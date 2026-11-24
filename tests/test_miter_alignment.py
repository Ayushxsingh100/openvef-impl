"""H5 miter, H6 replay, H9 ordering probe, H10 determinism, H1 mutants, F14 — synthetic
inputs and the TEST-ONLY toy designs in tests/sim_designs/ (toy_hs*.v are not FIFO
control mutants and are not owner material).

The Docker-backed classes run the real sandbox and are skipped only if Docker is absent;
a skip is never counted as a pass.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "runner"))

from openvef import alignment as AL  # noqa: E402
from openvef import eda, f14, miter, mutants  # noqa: E402
from openvef.pair_runner import compare_pair  # noqa: E402
from openvef.simulation import driver_run  # noqa: E402

DOCKER = shutil.which("docker") is not None
INP, OUT, NXT = "inputs_consumed_at_edge_n", "outputs_after_edge_n", "next_inputs_scheduled_for_edge_n_plus_1"
TOY_PRED_SRC = ("def legal(vector, sampled):\n"
                "    return not (sampled['v'] == '1' and vector['en'] == '1' and vector['d'] == '11')\n")
MASK = [{"entry": "K1", "signal": "v", "when": "always"},
        {"entry": "K2", "signal": "q", "when": {"null_signal": "v", "equals": "1"}}]


def toy_pred():
    ns: dict = {}
    exec(TOY_PRED_SRC, ns)
    return ns["legal"]


def toy_design(src: str) -> dict:
    return {"toplevel": "toy_hs", "verilog_sources": {"toy_hs.v": (HERE / "sim_designs" / src).read_text()},
            "clock_port": "clk", "input_ports": {"en": 1, "d": 2}, "held_inputs": {"rst": "0"},
            "output_ports": ["q", "v"], "output_widths": {"q": 2, "v": 1},
            "reset_sequence": [{"rst": "1", "en": "0", "d": "00"}, {"rst": "1", "en": "0", "d": "00"}],
            "cycle_cap": 8, "safe_idle": {"en": "0", "d": "00"},
            "legal_input_predicate": {"language": "python3.11", "function": "legal", "source": TOY_PRED_SRC}}


def eval_expr(expr: str, inputs: dict, outputs: dict) -> int:
    """Evaluate the generated sum-of-products in Python (test oracle)."""
    def bit(name: str, k: int) -> int:
        if name.startswith("gold_"):
            s = outputs[name[5:]]
        else:
            s = inputs[name]
        return int(s[len(s) - 1 - k])
    py = expr.replace("1'b0", "0").replace("1'b1", "1")
    py = re.sub(r"~([A-Za-z_]\w*)\[(\d+)\]", r"(1-bit('\1',\2))", py)
    py = re.sub(r"(?<![\w'])([A-Za-z_]\w*)\[(\d+)\]", r"bit('\1',\2)", py)
    py = py.replace("~(", "1-(")
    return eval(py, {"bit": bit})  # noqa: S307 - test oracle on generated text


class PredicateCompileTests(unittest.TestCase):
    def test_exact_on_whole_domain(self):
        fn = toy_pred()
        c = miter.compile_predicate(fn, {"en": 1, "d": 2}, {"v": 1, "q": 2})
        self.assertEqual(sorted(c["support"]), sorted(["en[0]", "d[0]", "d[1]", "gold_v[0]"]))
        for en in "01":
            for d in ("00", "01", "10", "11"):
                for v in "01":
                    for q in ("00", "01", "10", "11"):
                        want = fn({"en": en, "d": d}, {"v": v, "q": q})
                        got = eval_expr(c["expression"], {"en": en, "d": d}, {"v": v, "q": q})
                        self.assertEqual(bool(got), want, (en, d, v, q))

    def test_constant_predicates(self):
        self.assertEqual(miter.compile_predicate(lambda v, s: True, {"a": 2}, {"b": 1})["expression"], "1'b1")
        self.assertEqual(miter.compile_predicate(lambda v, s: False, {"a": 2}, {"b": 1})["expression"], "1'b0")

    def test_cap(self):
        with self.assertRaises(miter.MiterError):
            miter.compile_predicate(lambda v, s: True, {"a": 20}, {"b": 8})

    def test_non_bool(self):
        with self.assertRaises(miter.MiterError):
            miter.compile_predicate(lambda v, s: 1, {"a": 1}, {"b": 1})

    def test_wrapper_text(self):
        w = miter.wrapper("toy_hs", {"en": 1, "d": 2, "rst": 1}, {"v": 1, "q": 2}, MASK, "1'b1")
        self.assertIn("assign trigger = (gold_v != gate_v) | ((gold_v == 1'b1) & (gold_q != gate_q));", w)
        self.assertIn("toy_hs_gold gold_inst(", w)

    def test_parse_log(self):
        log = ("SAT proof finished - model found: FAIL!\n"
               "     3 \\en                        1         1             1\n"
               "     3 \\trigger                   0         0             0\n"
               "     4 \\trigger                   1         1             1\n")
        p = miter.parse_log(log)
        self.assertEqual(p["steps"][4]["trigger"], "1")
        self.assertEqual(miter.parse_log("SAT proof finished - no model found: SUCCESS!")["result"], "PROVED")


def run_result(spec_rows, ordering=None):
    return {"rows": spec_rows, "ordering": ordering}


class AlignmentSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.design = toy_design("toy_hs.v")
        r0, r1 = self.design["reset_sequence"]
        a = {"rst": "0", "en": "1", "d": "01"}
        self.rows = [
            {"cycle_index": 0, "reset": True, INP: r0, OUT: {"v": "0", "q": "00"}, NXT: r1, "driver_completed": False},
            {"cycle_index": 1, "reset": False, INP: r1, OUT: {"v": "0", "q": "00"}, NXT: a, "driver_completed": False},
            {"cycle_index": 2, "reset": False, INP: a, OUT: {"v": "1", "q": "01"}, NXT: None, "driver_completed": False},
        ]
        self.ordering = [{"row": 0, "edge_ns": 5, "sample_ns": 5, "sample_phase": "ReadOnly", "drive_ns": 10},
                         {"row": 1, "edge_ns": 15, "sample_ns": 15, "sample_phase": "ReadOnly",
                          "driver_call_ns": 15, "drive_ns": 20},
                         {"row": 2, "edge_ns": 25, "sample_ns": 25, "sample_phase": "ReadOnly"}]

    def test_aligned(self):
        self.assertEqual(AL.check_alignment(run_result(self.rows, self.ordering), self.design), [])

    def test_consumed_mismatch(self):
        self.rows[2][INP] = {"rst": "0", "en": "0", "d": "01"}
        self.assertTrue(AL.check_alignment(run_result(self.rows, self.ordering), self.design))

    def test_drive_after_next_edge(self):
        self.ordering[1]["drive_ns"] = 26
        self.assertTrue(any("before edge" in p for p in AL.check_alignment(run_result(self.rows, self.ordering),
                                                                            self.design)))

    def test_sample_not_readonly(self):
        self.ordering[1]["sample_phase"] = "ReadWrite"
        self.assertTrue(AL.check_alignment(run_result(self.rows, self.ordering), self.design))

    def test_echo(self):
        e = AL.check_echo(run_result(self.rows), self.design, "v", "en")
        self.assertEqual(e["rows_checked"], 1)
        self.assertEqual(e["mismatch_rows"], [1])  # row 1 sampled v=0 but scheduled en=1

    def test_compare_repeats(self):
        a = {"rows": self.rows, "events": [], "waveform": {"sha256": "x"}}
        b = {"rows": self.rows, "events": [], "waveform": {"sha256": "y"}}
        c = AL.compare_repeats([a, b])
        self.assertTrue(c["traces_identical"] and c["records_identical"])
        d = dict(b, events=[{"kind": "driver_watchdog"}])
        self.assertFalse(AL.compare_repeats([a, d])["records_identical"])


class MutantManifestTests(unittest.TestCase):
    def write(self, d: Path, manifest: dict, files: dict):
        (d / "mutants").mkdir()
        for k, v in files.items():
            (d / "mutants" / k).write_text(v)
        (d / "mutants" / "manifest.json").write_text(json.dumps(manifest))
        return d / "mutants" / "manifest.json"

    def test_load_and_export(self):
        orig = (HERE / "sim_designs" / "toy_hs.v").read_text()
        with tempfile.TemporaryDirectory() as t:
            m = self.write(Path(t), {"mutants": [{"id": "a", "file": "a.v", "roles": ["M-exposed"], "description": "x"}]},
                           {"a.v": (HERE / "sim_designs" / "toy_hs_late.v").read_text()})
            entries = mutants.load_manifest(m, "toy_hs", orig)
            self.assertTrue(entries[0]["diff_vs_original"].startswith("---"))
            exp = mutants.export_all(entries, "s", "nullsha", [["clk", "input", 1]],
                                     lambda text, s: {"netlist": "N" + text, "sha256": str(hash(text))},
                                     lambda v, top: {"ports": [["clk", "input", 1]]}, "toy_hs", {"toplevel": "toy_hs"})
            self.assertEqual(mutants.by_role(exp, "M-exposed"), ["a"])
            self.assertIn("toy_hs_mutant_a.v", exp["a"]["design"]["verilog_sources"])

    def test_rejections(self):
        orig = (HERE / "sim_designs" / "toy_hs.v").read_text()
        cases = [({"mutants": [{"id": "a", "file": "a.v", "roles": [], "description": ""}]}, {"a.v": orig}),
                 ({"mutants": [{"id": "a", "file": "../a.v", "roles": [], "description": ""}]}, {}),
                 ({"mutants": [{"id": "a", "file": "a.v", "roles": [], "description": "", "x": 1}]}, {"a.v": "m"}),
                 ({"mutants": []}, {})]
        for manifest, files in cases:
            with self.subTest(manifest=manifest), tempfile.TemporaryDirectory() as t:
                m = self.write(Path(t), manifest, files)
                with self.assertRaises((mutants.MutantError, FileNotFoundError)):
                    mutants.load_manifest(m, "toy_hs", orig)

    def test_identical_netlist_rejected(self):
        e = [{"id": "a", "source": "x", "roles": [], "description": "", "file": "a.v", "source_sha256": "",
              "diff_sha256": ""}]
        with self.assertRaises(mutants.MutantError):
            mutants.export_all(e, "s", "same", [], lambda t, s: {"netlist": "n", "sha256": "same"},
                               lambda v, top: {"ports": []}, "t", {})


class F14FakeTests(unittest.TestCase):
    def test_pass_and_fail(self):
        ports = [["clk", "input", 1], ["q", "output", 2]]

        def iface(v, top):
            return {"top": top, "modules": [top], "ports": ports}
        ok = f14.run(REPO, "design/fifo/design-materials-DRAFT.json",
                     lambda t, s: {"netlist": "n", "sha256": "h", "yosys_version": "y"}, iface)
        self.assertEqual(ok["status"], "PASS")
        counter = iter(["h1", "h2"])
        bad = f14.run(REPO, "design/fifo/design-materials-DRAFT.json",
                      lambda t, s: {"netlist": "n", "sha256": next(counter), "yosys_version": "y"}, iface)
        self.assertEqual(bad["status"], "FAIL")
        self.assertFalse(bad["checks"]["hashes_equal"])


@unittest.skipUnless(DOCKER, "docker not available")
class MiterDockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = toy_design("toy_hs.v")
        cls.legal = miter.compile_predicate(toy_pred(), {"en": 1, "d": 2}, {"v": 1, "q": 2})["expression"]
        cls.gold = (HERE / "sim_designs" / "toy_hs.v").read_text()

    def check(self, src, n=6):
        return miter.bounded_check(self.gold, (HERE / "sim_designs" / src).read_text(), self.design, MASK,
                                   self.legal, n, run_yosys=eda.run_yosys, solver_timeout_s=60, wall_timeout_s=120)

    def test_dontcare_bounded_equivalent(self):
        self.assertEqual(self.check("toy_hs_dontcare.v")["label"], miter.BOUNDED_EQUIVALENT)

    def test_late_shortest_counterexample_and_replay(self):
        r = self.check("toy_hs_late.v")
        self.assertEqual(r["label"], miter.NON_EQUIVALENT)
        cex = r["counterexample"]
        # two consecutive enables right after reset release: divergence visible after edge 3
        self.assertEqual(cex["trigger_step"], 5)
        self.assertEqual(cex["predicted_masked_divergence_row"], 3)
        drv = miter.replay_driver(cex, self.design)
        null = driver_run(drv, self.design, "null", 0, step_timeout_s=30, budget_s=60)
        mut = driver_run(drv, toy_design("toy_hs_late.v"), "mutant", 0, step_timeout_s=30, budget_s=60)
        pair = compare_pair(null, mut, MASK)
        self.assertTrue(miter.replay_agrees(cex, pair)["agrees"], (cex, pair))

    def test_bound_over_cap_rejected(self):
        with self.assertRaises(miter.MiterError):
            self.check("toy_hs_late.v", n=9)

    def test_identical_proved(self):
        self.assertEqual(self.check("toy_hs.v")["label"], miter.BOUNDED_EQUIVALENT)


ECHO = ("class Driver:\n    def step(self, cycle_index, outputs_after_edge):\n"
        "        if cycle_index >= 5:\n            return 'COMPLETE'\n"
        "        return {'en': '1' if outputs_after_edge['v'] == '0' else '0', 'd': '01'}\n\n\n"
        "def create_driver(seed):\n    return Driver()\n")
LOOPS = ("class Driver:\n    def step(self, cycle_index, outputs_after_edge):\n"
         "        while cycle_index >= 3:\n            pass\n        return {'en': '1', 'd': '10'}\n\n\n"
         "def create_driver(seed):\n    return Driver()\n")


@unittest.skipUnless(DOCKER, "docker not available")
class HarnessProbeDockerTests(unittest.TestCase):
    """Test-only drivers exercising the harness mechanics on the toy design (not F-controls)."""

    def test_ordering_and_alignment_on_a_real_run(self):
        d = toy_design("toy_hs.v")
        r = driver_run(ECHO, d, "null", 0, step_timeout_s=30, budget_s=60)
        self.assertEqual(r["run_status"], "COMPLETE_TRACE")
        self.assertEqual(AL.check_alignment(r, d), [])
        # The echo driver inverts v into en, so en(n+1) = not v(n): the probe must see every row
        rows = r["rows"]
        release = len(d["reset_sequence"]) - 1
        for n in range(release, release + 5):
            self.assertEqual(rows[n + 1][INP]["en"], "1" if rows[n][OUT]["v"] == "0" else "0")

    def test_watchdog_keeps_rows(self):
        r = driver_run(LOOPS, toy_design("toy_hs.v"), "null", 0, step_timeout_s=2, budget_s=60)
        self.assertEqual(r["events"][0]["kind"], "driver_watchdog")
        self.assertEqual(r["run_status"], "TRUNCATED_TRACE")
        self.assertGreaterEqual(len(r["rows"]), 4)  # reset rows + cycles 0-2 recorded before the loop

    def test_repeat_determinism(self):
        d = toy_design("toy_hs.v")
        runs = [driver_run(ECHO, d, "null", 0, step_timeout_s=30, budget_s=60) for _ in range(2)]
        c = AL.compare_repeats(runs)
        self.assertTrue(c["traces_identical"], c)
        self.assertTrue(c["records_identical"], c)


if __name__ == "__main__":
    unittest.main()
