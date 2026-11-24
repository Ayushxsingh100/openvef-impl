"""Simulator-backed stages (Protocol §3.4 L166 (7)-(8)) through the real sandbox.

Uses TEST-ONLY toy designs in tests/sim_designs/ (not a FIFO, not owner material). They
exercise the harness mechanics: reset/sampling, COMPLETE then safe-idle, per-cycle
precedence, vector validation, watchdog, simulator error, paired comparison.
Skipped only if Docker is absent; a skip is never counted as a pass.
"""
from __future__ import annotations

import base64
import hashlib
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import sandbox  # noqa: E402
from openvef.simulation import (SimulationError, compare_runs, driver_run, driver_stages, l334_timeout,  # noqa: E402
                                 run_outcome, simulate_pair)
from openvef.stage_map import NotDetermined  # noqa: E402

INP, OUT, NXT = "inputs_consumed_at_edge_n", "outputs_after_edge_n", "next_inputs_scheduled_for_edge_n_plus_1"

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

    def test_check_e_executable_predicate(self):
        # File 30 L83 (e) with a design-pack predicate over (vector, sampled outputs) (A-041).
        pred = {"language": "python3.11", "function": "legal",
                "source": "def legal(vector, sampled):\n    return not (sampled['flag'] == '1' and vector['b'] == '1')\n"}
        r = self.run1(COUNTER, design(legal_input_predicate=pred))
        # Cycle 0 is legal (flag 0 after reset) and drives b = 1; cycle 1 sees flag = 1 and
        # returns b = 1 again: illegal, not driven.
        self.assertEqual(run_outcome(r).diagnostic, "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE")
        self.assertEqual(r["events"][0]["cycle"], r["reset_release_cycle"] + 1)
        self.assertIsNone(r["rows"][-1][NXT])

    def test_check_e_predicate_failure_is_a_harness_error(self):
        for body in ("    raise KeyError('x')\n", "    return 1\n"):
            pred = {"language": "python3.11", "function": "legal", "source": "def legal(vector, sampled):\n" + body}
            with self.assertRaises(SimulationError):
                run_outcome(self.run1(COUNTER, design(legal_input_predicate=pred)))

    def test_check_e_non_executable_predicate_is_not_determined(self):
        with self.assertRaises(NotDetermined):
            run_outcome(self.run1(COUNTER, design(legal_input_predicate="b must be 0 when flag is 1")))

    def test_l334_timeout_and_simulate_pair(self):
        t = l334_timeout(COUNTER, design(), 0)
        self.assertEqual(len(t["wall_times_s"]), 3)
        self.assertGreaterEqual(t["t_timeout_s"], 2.0)
        self.assertAlmostEqual(t["t_timeout_s"], max(5 * t["median_s"], 2.0), places=2)
        out = simulate_pair(COUNTER, design(), design(), 0,
                            lambda a, b: compare_runs(a, b, ["flag", "q"]), timeout_s=t["t_timeout_s"])
        self.assertIsNone(out["failure"])
        self.assertEqual(len(out["null_rows"]), 8)

    def test_fixture_port_names_override_key_set(self):
        # A-044: a fixture-supplied names-only port manifest is the key set for (a); a
        # vector that passes (a)-(b) under names that are not the design's ports is not
        # determined (no widths, cannot be driven).
        d = design(driver_vector_keys=["data", "valid"])
        self.assertEqual(self.diag(returns("{'data': '0'}"), d=d), "DRIVER_VECTOR_INVALID|reason=MISSING_KEYS")
        self.assertEqual(self.diag(returns("{'data': '0', 'valid': 1}"), d=d),
                         "DRIVER_VECTOR_INVALID|reason=NON_STRING_VALUE")
        with self.assertRaises(NotDetermined):
            run_outcome(self.run1(returns("{'data': '0', 'valid': '1'}"), d))

    def test_held_inputs_are_not_driver_keys(self):
        # A-042: rst is harness-owned; driver vectors omit it, the harness holds it at 0
        # after reset and records it as a consumed top-level input (L217).
        held = design(input_ports={"a": 2, "b": 1}, held_inputs={"rst": "0"},
                      safe_idle={"a": "00", "b": "0"})
        no_rst = driver("        if cycle_index == 3:\n            return 'COMPLETE'\n"
                        "        return {'a': format(cycle_index % 4, '02b'), 'b': '1'}\n")
        r = self.run1(no_rst, held)
        self.assertEqual(r["events"], [])
        rows = r["rows"]
        self.assertEqual(rows[0][INP], {"rst": "1", "a": "00", "b": "0"})
        self.assertEqual(rows[2][INP], {"rst": "0", "a": "00", "b": "1"})
        self.assertEqual(rows[1][NXT], {"rst": "0", "a": "00", "b": "1"})
        self.assertEqual(rows[3][OUT], {"flag": "1", "q": "01"})
        self.assertEqual(rows[-2][NXT], {"rst": "0", "a": "00", "b": "0"})  # safe idle, rst held
        # A driver that still returns rst gets EXTRA_KEYS: rst is not a driver key.
        self.assertEqual(self.diag(COUNTER, d=held), "DRIVER_VECTOR_INVALID|reason=EXTRA_KEYS")

    def test_reset_sampling_complete_and_safe_idle(self):
        r = self.run1(COUNTER)
        rows = r["rows"]
        # Row n = active edge n from the first reset edge; one reset row, then the
        # reset-release row (driver cycle_index 0), 6 driver rows (cap), and the cap row.
        self.assertEqual(r["reset_release_cycle"], 1)
        self.assertEqual(len(rows), 1 + 6 + 1)
        self.assertEqual([row["cycle_index"] for row in rows], list(range(8)))
        self.assertEqual([row["reset"] for row in rows], [True] + [False] * 7)
        self.assertEqual(rows[1][OUT], {"flag": "0", "q": "00"})  # after the reset-release edge
        self.assertEqual(rows[3][OUT], {"flag": "1", "q": "01"})  # driver cycle 1's vector, one edge later
        self.assertEqual([row["driver_completed"] for row in rows[1:7]], [False, False, False, True, True, True])
        self.assertEqual(rows[5][NXT], {"rst": "0", "a": "00", "b": "0"})  # safe idle
        self.assertIsNone(rows[7][NXT])  # cap row: no further decision
        self.assertEqual(r["run_status"], "COMPLETE_TRACE")
        self.assertTrue(r["driver_completed"])
        self.assertIsNone(run_outcome(r))

    def test_consumed_inputs_are_captured_and_agree_with_prior_schedule(self):
        rows = self.run1(COUNTER)["rows"]
        self.assertEqual(rows[0][INP], {"rst": "1", "a": "00", "b": "0"})  # reset inputs from the design pack
        for prev, row in zip(rows, rows[1:]):
            self.assertEqual(row[INP], prev[NXT])  # L221

    def test_row_field_names_are_the_pack_names(self):
        row = self.run1(COUNTER)["rows"][2]
        self.assertEqual(set(row), {"cycle_index", "reset", "inputs_consumed_at_edge_n", "outputs_after_edge_n",
                                    "next_inputs_scheduled_for_edge_n_plus_1", "driver_completed"})

    def test_four_state_values_preserved(self):
        src = ("module toy(input clk, input rst, input [1:0] a, input b, output [1:0] q, output flag);\n"
               "  assign q = 2'bxz;\n  assign flag = 1'bz;\nendmodule\n")
        rows = self.run1(COUNTER, design(verilog_sources={"toy.v": src}))["rows"]
        self.assertEqual(rows[1][OUT], {"flag": "Z", "q": "XZ"})

    def test_waveform_audit_file(self):
        w = self.run1(COUNTER)["waveform"]
        self.assertEqual((w["format"], w["status"]), ("fst", "PRESERVED"))
        data = base64.b64decode(w["base64"])
        self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (w["bytes"], w["sha256"]))
        self.assertGreater(len(data), 0)

    def test_truncated_trace_status(self):
        r = self.run1(driver("        if cycle_index == 2:\n            return {}['x']\n"
                             "        return {'rst': '0', 'a': '00', 'b': '0'}\n"))
        self.assertEqual(r["run_status"], "TRUNCATED_TRACE")
        self.assertIsNone(r["rows"][-1][NXT])
        self.assertEqual(r["rows"][-1]["cycle_index"], 3)  # driver cycle_index 2 = row 1 + 2

    def test_scheduler_marks_sources(self):
        sched = self.run1(COUNTER)["scheduler"]
        self.assertTrue(sched["sample_point"]["source"].startswith("specified: Protocol §5.2 L218"))
        self.assertTrue(sched["drive_point"]["source"].startswith("build_default"))

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
        return [{OUT: {"o": o, "u": "0"}, NXT: {"i": i}} for o, i in zip(outputs, inputs)]

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
        b = [{**r, OUT: {"o": "0", "u": "1"}} for r in self.rows("000", "000")]
        self.assertIsNone(compare_runs(a, b, ["o"]))


if __name__ == "__main__":
    unittest.main()
