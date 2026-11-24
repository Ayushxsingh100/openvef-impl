"""DRAFT checker-facing trace serialization and hashing (openvef.trace; item 11)."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef import trace  # noqa: E402

ROW = {"cycle_index": 0, "reset": True, "inputs_consumed_at_edge_n": {"rst": "1", "b": "0"},
       "outputs_after_edge_n": {"q": "X"}, "next_inputs_scheduled_for_edge_n_plus_1": None,
       "driver_completed": False}


class TraceTests(unittest.TestCase):
    def test_canonical_bytes_and_hash(self):
        f = trace.freeze([ROW])
        self.assertEqual(f.data, b'[{"cycle_index":0,"driver_completed":false,"inputs_consumed_at_edge_n":'
                                 b'{"b":"0","rst":"1"},"next_inputs_scheduled_for_edge_n_plus_1":null,'
                                 b'"outputs_after_edge_n":{"q":"X"},"reset":true}]')
        self.assertEqual(f.sha256, hashlib.sha256(f.data).hexdigest())
        self.assertEqual(trace.freeze([dict(reversed(list(ROW.items())))]).sha256, f.sha256)  # key order irrelevant

    def test_each_invocation_gets_an_independent_value(self):
        f = trace.freeze([ROW])
        a = f.decoded()
        a[0]["reset"] = False
        self.assertTrue(f.decoded()[0]["reset"])
        self.assertTrue(f.verify())

    def test_rows_outside_schema_rejected(self):
        with self.assertRaises(ValueError):
            trace.freeze([{k: v for k, v in ROW.items() if k != "reset"}])
        with self.assertRaises(ValueError):
            trace.freeze([dict(ROW, extra=1)])

    def test_non_json_values_rejected(self):
        with self.assertRaises(ValueError):
            trace.freeze([dict(ROW, cycle_index=float("nan"))])


if __name__ == "__main__":
    unittest.main()
