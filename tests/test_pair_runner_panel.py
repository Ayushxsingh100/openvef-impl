"""H2 pair runner/comparator and H7 panel (Protocol §8, §12, §13.4), synthetic rows only."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import pairs as P  # noqa: E402
from openvef import panel as PN  # noqa: E402
from openvef.pair_runner import compare_pair, run_pair  # noqa: E402
from openvef.simulation import SimulationError  # noqa: E402

INP, OUT, NXT = "inputs_consumed_at_edge_n", "outputs_after_edge_n", "next_inputs_scheduled_for_edge_n_plus_1"
MASK = [{"entry": "K1", "signal": "v", "when": "always"},
        {"entry": "K2", "signal": "q", "when": {"null_signal": "v", "equals": "1"}}]


def rows(spec):
    """spec: list of (v, q, next_en) per row; next_en None means no decision."""
    out = []
    for n, (v, q, nx) in enumerate(spec):
        out.append({"cycle_index": n, "reset": False, INP: {"en": "0"}, OUT: {"v": v, "q": q},
                    NXT: None if nx is None else {"en": nx}, "driver_completed": False})
    return out


def result(spec, events=(), status=None):
    return {"rows": rows(spec), "events": list(events),
            "run_status": status or ("TRUNCATED_TRACE" if events else "COMPLETE_TRACE")}


BASE = [("0", "00", "1"), ("1", "01", "0"), ("0", "00", "1"), ("1", "10", None)]


class ComparePairTests(unittest.TestCase):
    def test_identical(self):
        p = compare_pair(result(BASE), result(BASE), MASK)
        self.assertEqual((p["raw_divergence"], p["masked_divergence"], p["next_input_before_raw"]),
                         (False, False, False))

    def test_dontcare_only_is_raw_not_masked(self):
        mut = list(BASE)
        mut[0] = ("0", "11", "1")  # q differs while null v = 0
        p = compare_pair(result(BASE), result(mut), MASK)
        self.assertTrue(p["raw_divergence"])
        self.assertFalse(p["masked_divergence"])
        self.assertEqual(p["first_raw_row"], 0)

    def test_window_evaluated_on_null_row(self):
        mut = list(BASE)
        mut[1] = ("1", "11", "0")  # null v = 1 there: masked
        mut2 = list(BASE)
        mut2[0] = ("1", "11", "1")  # mutant v = 1 but null v = 0: v differs (always), q not compared by window
        self.assertEqual(compare_pair(result(BASE), result(mut), MASK)["first_masked_row"], 1)
        self.assertEqual(compare_pair(result(BASE), result(mut2), MASK)["first_masked_row"], 0)

    def test_same_row_tie_is_output_first(self):
        mut = list(BASE)
        mut[1] = ("1", "11", "1")  # output and decision differ in the same row (F10 shape)
        p = compare_pair(result(BASE), result(mut), MASK)
        self.assertFalse(p["next_input_before_raw"])
        self.assertEqual(p["first_next_input_row"], 1)

    def test_earlier_next_input_is_invalid(self):
        mut = list(BASE)
        mut[0] = ("0", "00", "0")  # decision differs before any raw divergence (F9 shape)
        mut[2] = ("1", "00", "1")
        p = compare_pair(result(BASE), result(mut), MASK)
        self.assertTrue(p["next_input_before_raw"])

    def test_truncated_after_masked(self):
        mut = [BASE[0], ("0", "01", None)]  # v differs at row 1, then the driver raised
        p = compare_pair(result(BASE), result(mut, events=[{"kind": "driver_runtime", "cycle": 1}]), MASK)
        self.assertEqual(p["termination"], P.DRIVER_SIM_ERROR)
        self.assertTrue(p["masked_divergence"])

    def test_watchdog_without_masked(self):
        p = compare_pair(result(BASE), result(BASE[:2], events=[{"kind": "driver_watchdog"}]), MASK)
        self.assertEqual((p["termination"], p["masked_divergence"]), (P.TIMEOUT, False))

    def test_null_failure_is_integrity(self):
        p = compare_pair(result(BASE[:2], events=[{"kind": "driver_watchdog"}]), result(BASE), MASK)
        self.assertTrue(p["integrity_failure"])

    def test_row_alignment_is_integrity(self):
        p = compare_pair(result(BASE), result(BASE, events=[{"kind": "trace_integrity", "reason": "ROW_ALIGNMENT"}]),
                         MASK)
        self.assertTrue(p["integrity_failure"])

    def test_unequal_complete_lengths_is_integrity(self):
        self.assertTrue(compare_pair(result(BASE), result(BASE[:3]), MASK)["integrity_failure"])

    def test_harness_error_raises(self):
        with self.assertRaises(SimulationError):
            compare_pair(result(BASE), {"error": "x"}, MASK)


class RunPairTests(unittest.TestCase):
    def run_with(self, mut_spec, verdict, events=()):
        def run(src, design, target, seed, **kw):
            return result(BASE) if target == "null" else result(mut_spec, events=events)

        class Outcome:
            def __init__(self, v):
                self.verdict = v

        return run_pair("drv", {}, {}, "m1", 0, MASK, timeout_s=2.0, run=run, checker_source="chk",
                        metadata={}, invoke=lambda s, t, m: Outcome(verdict))

    def test_detected(self):
        mut = list(BASE)
        mut[1] = ("1", "11", "0")
        r = self.run_with(mut, "FAIL")
        self.assertEqual(r["class"], P.DETECTED)

    def test_pipeline_anomaly_on_identical_trace(self):
        r = self.run_with(BASE, "FAIL")
        self.assertEqual(r["class"], P.ANOMALY_PIPELINE)
        self.assertTrue(r["byte_identical_to_null"])

    def test_checker_error(self):
        r = self.run_with(BASE, None)
        self.assertEqual(r["class"], P.CHECKER_ERROR_NO_MASKED)

    def test_truncated_has_no_checker(self):
        r = self.run_with(BASE[:2], "FAIL", events=[{"kind": "driver_watchdog"}])
        self.assertEqual(r["class"], P.TIMEOUT_NO_MASKED)
        self.assertNotIn("checker", r)


class PanelTests(unittest.TestCase):
    def fake_run(self, outputs_by_target):
        def run(src, design, target, seed):
            return result(outputs_by_target[target.split(":")[-1]])
        return run

    def test_build_stream(self):
        dontcare = [("0", "11", "1")] + BASE[1:]
        exposed = list(BASE)
        exposed[1] = ("1", "11", "0")
        corpus = PN.build_stream("DIRECTED", [{"scenario_id": "s1", "driver_source": "d", "seed": 0}],
                                 {}, {}, {"A": {}, "B": {}, "C": {}}, MASK,
                                 self.fake_run({"rtl": BASE, "null": BASE, "A": exposed, "B": dontcare, "C": BASE}))
        self.assertEqual(corpus["B"], 2)
        self.assertEqual(corpus["Q"], 1)
        kinds = {c["mutant"]: c["kind"] for c in corpus["cases"]}
        self.assertEqual(kinds, {"A": PN.EXPOSED, "B": PN.RAW_ONLY, "C": PN.NOT_DIVERGENT})

    def test_scenario_excluded_when_rtl_null_masked_differ(self):
        bad = list(BASE)
        bad[1] = ("0", "01", "0")
        corpus = PN.build_stream("DIRECTED", [{"scenario_id": "s1", "driver_source": "d", "seed": 0}],
                                 {}, {}, {}, MASK, self.fake_run({"rtl": bad, "null": BASE}))
        self.assertEqual(corpus["B"], 0)
        self.assertEqual(len(corpus["excluded_scenarios"]), 1)

    def test_invalid_pair_excluded_from_q(self):
        early = list(BASE)
        early[0] = ("0", "00", "0")
        early[1] = ("1", "11", "0")
        corpus = PN.build_stream("REACTIVE_RANDOM", [{"scenario_id": "s1", "driver_source": "d", "seed": 0}],
                                 {}, {}, {"A": {}}, MASK, self.fake_run({"rtl": BASE, "null": BASE, "A": early}))
        self.assertEqual((corpus["Q"], corpus["excluded_pairs"]), (0, 1))

    def test_evaluate_checker(self):
        exposed = list(BASE)
        exposed[1] = ("1", "11", "0")
        corpus = PN.build_stream("DIRECTED", [{"scenario_id": "s1", "driver_source": "d", "seed": 0}],
                                 {}, {}, {"A": {}}, MASK, self.fake_run({"rtl": BASE, "null": BASE, "A": exposed}))
        null_bytes = corpus["benign"][1]["bytes"]
        ref = PN.evaluate_checker(corpus, lambda b: "PASS" if b == null_bytes else "FAIL")
        self.assertEqual(ref["benign"]["partition"], PN.PANEL_COMPATIBLE)
        self.assertEqual(ref["sensitivity"], 1.0)
        always_pass = PN.evaluate_checker(corpus, lambda b: "PASS")
        self.assertEqual((always_pass["benign"]["partition"], always_pass["sensitivity"]), (PN.PANEL_COMPATIBLE, 0.0))
        always_fail = PN.evaluate_checker(corpus, lambda b: "FAIL")
        self.assertEqual(always_fail["benign"]["partition"], PN.PANEL_FALSE_ALARM)
        self.assertIsNone(always_fail["sensitivity"])
        crash = PN.evaluate_checker(corpus, lambda b: "ERROR")
        self.assertEqual(crash["benign"]["partition"], PN.PANEL_ERROR)

    def test_partition_identity(self):
        itt = PN.itt([{"valid": True, "partition": PN.PANEL_COMPATIBLE, "detections": 1, "false_alarm_events": 0},
                      {"valid": False, "partition": None, "detections": 0, "false_alarm_events": 0}], q=1, b=2)
        self.assertTrue(PN.partition_identity(itt))
        itt[PN.PANEL_ERROR] = 0.5
        self.assertFalse(PN.partition_identity(itt))


if __name__ == "__main__":
    unittest.main()
