"""Unit tests for PARSE_SCHEMA part 1b (src/openvef/schema.py).

These are hand-constructed inputs, not F18 fixtures. Run:
    .venv/bin/python -I -m unittest discover -s tests
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.envelope import Failure  # noqa: E402
from openvef.schema import (  # noqa: E402
    SCHEMA_REL,
    ValidatedResponse,
    load_validator,
    validate_clause_ids,
    validate_schema,
)

VALIDATOR = load_validator(REPO / "baseline" / "OpenVEF_Planning_v1_3_6" / SCHEMA_REL)

VALID = {
    "schema_version": "1.0",
    "language": "python",
    "language_version": "3.11",
    "driver": {
        "filename": "driver.py",
        "factory": "create_driver(seed: int) -> Driver",
        "class_name": "Driver",
        "method": "step(cycle_index: int, outputs_after_edge: dict[str, str]) -> dict[str, str] | str",
        "source": "x = 1\n",
    },
    "checker": {
        "filename": "checker.py",
        "entry_point": "check_trace(trace: dict[str, object], metadata: dict[str, object]) -> dict[str, object]",
        "source": "x = 1\n",
    },
    "dependencies": [],
    "assumptions": [],
}


def pointer(obj) -> str | None:
    result = validate_schema(VALIDATOR, obj)
    if isinstance(result, ValidatedResponse):
        return None
    return result.diagnostic


class SchemaPointerTests(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(pointer(VALID))

    def test_non_object_root(self):
        self.assertEqual(pointer([]), "SCHEMA_REJECT|pointer=/")

    def test_root_prefix_sorts_first(self):
        obj = copy.deepcopy(VALID)
        obj["schema_version"] = "2.0"
        del obj["checker"]
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/")

    def test_code_point_order_between_siblings(self):
        obj = copy.deepcopy(VALID)
        obj["schema_version"] = "2.0"
        obj["language"] = "rust"
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/language")

    def test_parent_pointer_for_additional_properties(self):
        obj = copy.deepcopy(VALID)
        obj["driver"]["extra"] = 1
        obj["driver"]["filename"] = "x.py"
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/driver")

    def test_parent_pointer_for_required(self):
        obj = copy.deepcopy(VALID)
        del obj["checker"]["source"]
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/checker")

    def test_type_and_min_length_paths(self):
        obj = copy.deepcopy(VALID)
        obj["driver"]["source"] = ""
        obj["checker"]["source"] = 7
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/checker/source")

    def test_array_index_tokens_compare_as_strings(self):
        # Provisional reading A-006: token "10" sorts before token "2".
        obj = copy.deepcopy(VALID)
        obj["assumptions"] = [{"clause_id": "FIFO-001", "text": "t"} for _ in range(11)]
        obj["assumptions"][2]["text"] = ""
        obj["assumptions"][10]["text"] = ""
        self.assertEqual(pointer(obj), "SCHEMA_REJECT|pointer=/assumptions/10/text")


class ClauseIdTests(unittest.TestCase):
    def check(self, clause_ids, manifest=("FIFO-001", "FIFO-002")):
        obj = copy.deepcopy(VALID)
        obj["assumptions"] = [{"clause_id": c, "text": "t"} for c in clause_ids]
        validated = validate_schema(VALIDATOR, obj)
        self.assertIsInstance(validated, ValidatedResponse)
        return validate_clause_ids(validated, list(manifest))

    def test_members_and_unspecified_accepted(self):
        self.assertIsInstance(self.check(["FIFO-002", "UNSPECIFIED", "FIFO-001"]), ValidatedResponse)

    def test_lowest_failing_index(self):
        result = self.check(["FIFO-001", "FIFO-999", "BAD"])
        self.assertIsInstance(result, Failure)
        self.assertEqual(result.diagnostic, "SCHEMA_REJECT|pointer=/assumptions/1/clause_id")

    def test_exact_match_only(self):
        result = self.check(["fifo-001"])
        self.assertEqual(result.diagnostic, "SCHEMA_REJECT|pointer=/assumptions/0/clause_id")

    def test_reserved_value_in_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check([], manifest=("UNSPECIFIED",))


if __name__ == "__main__":
    unittest.main()
