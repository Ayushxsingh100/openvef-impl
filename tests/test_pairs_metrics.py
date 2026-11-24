"""H3 pair classifier, H4 ledger/metrics and F15 (Protocol §12, §13.1-§13.3, L524, L529).

Synthetic inputs only. Shows both that the F15 case table passes and that the identity
checks fail when the ledger or the inclusion map is wrong.
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import f15  # noqa: E402
from openvef import metrics as MX  # noqa: E402
from openvef import pairs as P  # noqa: E402

BASE = HERE.parent / "baseline" / "OpenVEF_Planning_v1_3_6"


class ClassifierTests(unittest.TestCase):
    def test_every_case(self):
        for cid, obs, exp, sub, _ in f15.PAIR_CASES:
            with self.subTest(cid):
                self.assertEqual(P.classify(obs), exp)
                self.assertEqual(P.np_subtype(obs), sub)

    def test_precedence_invalid_over_everything(self):
        for term in P.TERMINATIONS:
            o = P.PairObservation(True, False, term, True, True, None)
            self.assertEqual(P.classify(o), P.INVALID_PAIR)

    def test_driver_error_before_timeout_rules(self):
        # a truncated trace never gets a checker result (L328)
        with self.assertRaises(ValueError):
            P.PairObservation(False, False, P.TIMEOUT, False, False, "PASS")

    def test_masked_implies_raw(self):
        with self.assertRaises(ValueError):
            P.PairObservation(False, False, P.COMPLETE, False, True, "PASS")

    def test_complete_valid_needs_checker(self):
        with self.assertRaises(ValueError):
            P.PairObservation(False, False, P.COMPLETE, False, False, None)

    def test_inclusion_table_is_the_packs(self):
        self.assertEqual(f15.inclusion_matches_pack(BASE), [])

    def test_inclusion_check_detects_a_wrong_cell(self):
        bad = dict(P.INCLUSION)
        bad[P.PND] = ("Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No")
        with mock.patch.object(P, "INCLUSION", bad):
            self.assertTrue(f15.inclusion_matches_pack(BASE))


class F15Tests(unittest.TestCase):
    def test_f15_passes(self):
        r = f15.run(BASE, random_count=60)
        self.assertEqual(r["status"], "PASS", r["summary"])
        self.assertTrue(r["every_pair_class_covered"])
        self.assertEqual(r["summary"]["failures"], 0)

    def test_zero_valid_slot_rhs_not_evaluated(self):
        slots, mutants = f15.ledger_scenario()
        rows = MX.build_ledger(slots, mutants)
        m = MX.arm_design_metrics(rows, slots, "B", "D1", 6)
        self.assertEqual((m["J_exposure"], m["J_detection"]), (0, 0))
        self.assertNotIn("J_exposure_rhs", m)
        self.assertTrue(m["no_valid_artifacts_observed"])


class IdentitiesDetectErrors(unittest.TestCase):
    def setUp(self):
        self.slots, self.mutants = f15.ledger_scenario()
        self.rows = MX.build_ledger(self.slots, self.mutants)

    def failing(self, rows):
        return {r["identity"] for r in MX.check_identities(rows, self.slots, self.mutants) if not r["holds"]}

    def test_clean(self):
        self.assertEqual(self.failing(self.rows), set())

    def test_dropped_row(self):
        self.assertIn("total = |G_cd|×|M_d|", self.failing(self.rows[1:]))

    def test_duplicated_row(self):
        self.assertIn("one class per scheduled slot × mutant", self.failing(self.rows + [self.rows[0]]))

    def test_wrong_x_definition(self):
        orig = MX.artifact_metrics

        def wrong(classes):
            a = orig(classes)
            a["X"] = a["DET"] + a["PND"]  # forgets CHECKER_ERROR_AFTER_MASKED
            return a
        with mock.patch.object(MX, "artifact_metrics", wrong):
            self.assertIn("X_i includes only DET+PND+checker-error-after-exposure", self.failing(self.rows))

    def test_wrong_inclusion_flag(self):
        bad = dict(P.INCLUSION)
        bad[P.CHECKER_ERROR_AFTER_MASKED] = ("Yes", "Yes", "Yes", "No", "No", "No", "No")
        with mock.patch.object(P, "INCLUSION", bad):
            self.assertIn("X_i includes only DET+PND+checker-error-after-exposure", self.failing(self.rows))

    def test_invalid_slot_with_pair_rows(self):
        rows = [dict(r, **{"class": P.NP}) if r["slot"] == "a3" else r for r in self.rows]
        self.assertIn("invalid slot: only INVALID_ARTIFACT_SLOT rows", self.failing(rows))

    def test_ledger_rejects_missing_observation(self):
        s = replace(self.slots[0], pairs={k: v for k, v in self.slots[0].pairs.items() if k != "m1"})
        with self.assertRaises(ValueError):
            MX.build_ledger([s], self.mutants)


if __name__ == "__main__":
    unittest.main()
