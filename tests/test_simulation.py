"""Simulator-backed stages (Protocol §3.4 L166 (7)-(8)) through the real sandbox.

Uses TEST-ONLY toy designs in tests/sim_designs/ (not a FIFO, not owner material). They
exercise the harness mechanics: reset/sampling, COMPLETE then safe-idle, per-cycle
precedence, vector validation, watchdog, simulator error, paired comparison.
Skipped only if Docker is absent; a skip is never counted as a pass.
"""
from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import sandbox  # noqa: E402
from openvef.simulation import SimulationError, driver_run, driver_stages, run_outcome  # noqa: E402
from openvef.stage_map import NotDetermined  # noqa: E402

DOCKER = shutil.which("docker") is not None


def design(src="toy.v", **over):
    d = {"toplevel": "toy", "verilog_sources": {"toy.v": (HERE / "sim_designs" / src).read_text()},
         "clock_port": "clk", "input_ports": {"rst": 1, "a": 2, "b": 1}, "output_ports": ["flag", "q"],
         "reset_sequence": [{"rst": "1", "a": "00", "b": "0"}, {"rst": "1", "a": "00", "b": "0"}],
         "cycle_cap": 6, "safe_idle": {"rst": "0", "a": "00", "b": "0"},
         "legal_input_predicate": "ALL_INPUTS_LEGAL"}
    d.update(over)
    return d


def driver(step_body: str) -> str:
    return ("import random\n\ndef create_driver(seed):\n    d = Driver()\n    d.rng = random.Random(seed)\n"
            "    return d\n\nclass Driver:\n    def step(self, cycle_index, outputs_after_edge):\n" + step_body)


COUNTER = driver("        if cycle_index == 3:\n            return 'COMPLETE'\n"
                 "        return {'rst': '0', 'a': format(cycle_index % 4, '02b'), 'b': '1'}\n")


def returns(expr: str) -> str:
    return driver(f"        return {expr}\n")


@unittest.skipUnless(DOCKER, "docker not available")
class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()

    def run1(self, src, d=None, target="rtl", step_timeout_s=3.0):
        return driver_run(src, d or design(), target, 0, step_timeout_s=step_timeout_s, budget_s=30.0)

    def diag(self, src, **kw):
        f = run_outcome(self.run1(src, **kw))
        return None if f is None else f.diagnostic

    def test_reset_sampling_complete_and_safe_idle(self):
        r = self.run1(COUNTER)
        rows = r["rows"]
        self.assertEqual(len(rows), 6)  # cycle cap
        self.assertEqual(rows[0]["outputs_after_edge"], {"flag": "0", "q": "00"})  # after reset-release edge
        self.assertEqual(rows[2]["outputs_after_edge"], {"flag": "1", "q": "01"})  # cycle 1's vector, one edge later
        self.assertEqual([row["driver_completed"] for row in rows], [False, False, False, True, True, True])
        self.assertEqual(rows[4]["next_inputs"], {"rst": "0", "a": "00", "b": "0"})  # safe idle
        self.assertTrue(r["driver_completed"])
        self.assertIsNone(run_outcome(r))

    def test_step_exception(self):
        self.assertEqual(self.diag(returns("{}['x']")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=KeyError")

    def test_vector_reasons_in_order(self):
        cases = {
            "'nope'": "RETURN_TYPE",
            "{'rst': '0', 'a': '00'}": "MISSING_KEYS",
            "{'rst': '0', 'a': '00', 'b': '0', 'zz': '1'}": "EXTRA_KEYS",
            "{'rst': '0', 'a': 0, 'b': '0'}": "NON_STRING_VALUE",
            "{'rst': '0', 'a': '0', 'b': '0'}": "WRONG_WIDTH",
            "{'rst': '0', 'a': 'x0', 'b': '0'}": "ILLEGAL_SYMBOL",
        }
        for expr, reason in cases.items():
            with self.subTest(expr=expr):
                self.assertEqual(self.diag(returns(expr)), f"DRIVER_VECTOR_INVALID|reason={reason}")

    def test_missing_keys_before_extra_keys(self):
        self.assertEqual(self.diag(returns("{'rst': '0', 'zz': '1'}")), "DRIVER_VECTOR_INVALID|reason=MISSING_KEYS")

    def test_unexecutable_predicate_is_not_determined(self):
        with self.assertRaises(NotDetermined):
            run_outcome(self.run1(COUNTER, design(legal_input_predicate="wr_en must be 0 when full is 1")))

    def test_watchdog(self):
        self.assertEqual(self.diag(driver("        while True:\n            pass\n"), step_timeout_s=2.0),
                         "WATCHDOG_TIMEOUT|phase=driver_step")

    def test_factory_checks_run_in_the_simulation(self):
        src = "def create_driver(seed):\n    return object()\n\nclass Driver:\n    def step(self, cycle_index, outputs_after_edge):\n        return 'COMPLETE'\n"
        self.assertEqual(self.diag(src), "ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE")

    def test_simulator_error_on_bad_design(self):
        self.assertEqual(self.diag(COUNTER, d=design(verilog_sources={"toy.v": "module toy(;"}), target="null"),
                         "SIMULATOR_ERROR|target=null|class=CalledProcessError")

    def test_artifact_cannot_reach_simulator(self):
        self.assertEqual(self.diag(driver("        import cocotb\n        return 'COMPLETE'\n")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=ImportError")

    def test_paired_runs_agree_on_equivalent_null(self):
        self.assertIsNone(driver_stages(COUNTER, design(), design("toy_null.v"), ["flag", "q"], 0,
                                        step_timeout_s=3.0, budget_s=30.0))

    def test_masked_divergence_is_a_design_halt(self):
        f = driver_stages(COUNTER, design(), design("toy_diverge.v"), ["flag", "q"], 0, step_timeout_s=3.0,
                          budget_s=30.0)
        self.assertEqual(f.diagnostic, "RTL_NULL_CONTROL_FAILURE|reason=MASKED_OUTPUT_DIVERGENCE")

    def test_reactive_divergence_is_not_nondeterminism(self):
        # The driver echoes `flag` into `b`. On toy_diverge.v raw outputs first differ at
        # cycle 1 (flag), and the next inputs differ at the same row, i.e. not *before*
        # the first raw-output divergence: no DRIVER_NONDETERMINISM. With only `q`
        # observed there is no masked divergence either.
        echo = driver("        return {'rst': '0', 'a': '01', 'b': outputs_after_edge['flag']}\n")
        self.assertIsNone(driver_stages(echo, design(), design("toy_diverge.v"), ["q"], 0, step_timeout_s=3.0,
                                        budget_s=30.0))

    def test_missing_design_field(self):
        d = design()
        del d["safe_idle"]
        with self.assertRaises(ValueError):
            self.run1(COUNTER, d)


class CompareRunsTests(unittest.TestCase):
    """L166 (8) on hand-made rows (no Docker)."""

    @staticmethod
    def rows(outputs, inputs):
        return [{"outputs_after_edge": {"o": o, "u": "0"}, "next_inputs": {"i": i}} for o, i in zip(outputs, inputs)]

    def test_next_input_mismatch_before_raw_divergence_is_terminal(self):
        from openvef.simulation import compare_runs
        f = compare_runs(self.rows("000", "011"), self.rows("001", "001"), ["o"])
        self.assertEqual(f.diagnostic, "DRIVER_NONDETERMINISM|reason=NEXT_INPUT_DIVERGENCE")

    def test_same_input_masked_divergence_is_halt(self):
        from openvef.simulation import compare_runs
        f = compare_runs(self.rows("010", "000"), self.rows("000", "000"), ["o"])
        self.assertEqual(f.diagnostic, "RTL_NULL_CONTROL_FAILURE|reason=MASKED_OUTPUT_DIVERGENCE")

    def test_unobserved_divergence_is_not_a_halt(self):
        from openvef.simulation import compare_runs
        a = self.rows("000", "000")
        b = [dict(r, outputs_after_edge={"o": "0", "u": "1"}) for r in self.rows("000", "000")]
        self.assertIsNone(compare_runs(a, b, ["o"]))


if __name__ == "__main__":
    unittest.main()
