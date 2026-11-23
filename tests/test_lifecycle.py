"""Change-class lifecycle expectations (Protocol L175-L176, L181-L185; A-033 revised).

The key property: every string value the ledger produces appears verbatim in the
Protocol text, so nothing is taken from a fixture descriptor.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.ledger import LIFECYCLE_CASES, Unsupported, lifecycle_expectation  # noqa: E402

PROTOCOL = (REPO / "baseline/OpenVEF_Planning_v1_3_6/02_OpenVEF_Experimental_Protocol_v1.3.6.md").read_text("utf-8")


class LifecycleTests(unittest.TestCase):
    def test_every_string_value_is_verbatim_in_the_protocol(self):
        for change_class, case in LIFECYCLE_CASES.items():
            for name, entry in case.items():
                if isinstance(entry, Unsupported):
                    continue
                values = entry[0] if isinstance(entry[0], list) else [entry[0]]
                for v in values:
                    if isinstance(v, str):
                        self.assertIn(f"`{v}`", PROTOCOL, f"{change_class}.{name}")

    def test_every_supported_field_has_a_citation(self):
        for case in LIFECYCLE_CASES.values():
            for entry in case.values():
                if not isinstance(entry, Unsupported):
                    self.assertTrue(entry[1].startswith("L"), entry)

    def test_unsupported_fields_are_reported_not_filled(self):
        record, missing = lifecycle_expectation("FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED")
        self.assertEqual(set(missing), {"error_class", "rerun_scope_rule"})
        self.assertNotIn("error_class", record)

    def test_study_reset_is_fully_supported(self):
        record, missing = lifecycle_expectation(
            "DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START")
        self.assertEqual(missing, {})
        self.assertEqual(record["error_class"], "AUTHORING_REVISION_REQUIRED")

    def test_unknown_change_class(self):
        with self.assertRaises(ValueError):
            lifecycle_expectation("SOMETHING_ELSE")


if __name__ == "__main__":
    unittest.main()
