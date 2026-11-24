"""DRAFT FIFO observation mask and File 24 traceability table (D-005).

The mask requires an independent human reviewer's signature (Protocol L271); these
checks are mechanical only:
- the table has exactly the File 24 template columns;
- every row maps to a defined clause ID, with an exact excerpt of that clause's text;
- the JSON mask and the table agree;
- each variant covers every output once, and the windows are over always-observed
  predicates (L274);
- the masked comparison ignores rd_data only in the null-trace rd_valid = 0 window, and
  the stricter variant compares it everywhere;
- in the pinned image, the null-netlist trace has no X/Z on always-observed outputs
  (L277), and RTL and null agree under both variants.
"""
from __future__ import annotations

import csv
import re
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

from openvef import design_materials  # noqa: E402
from openvef.simulation import compare_runs, driver_run, null_trace_xz, validate_mask  # noqa: E402

LOADED = design_materials.load(REPO, "design/fifo/design-materials-DRAFT.json")
MASK = LOADED["mask"]
MATERIALS = LOADED["materials"]
TABLE = REPO / MASK["traceability_table"]
TEMPLATE = REPO / "baseline/OpenVEF_Planning_v1_3_6/24_Mask_to_Specification_Traceability_Template.csv"
BODY = LOADED["spec_text"].split("<!-- PAYLOAD TEXT BELOW -->", 1)[1]
DOCKER = shutil.which("docker") is not None


def norm(s: str) -> str:
    return " ".join(s.split())


def clause_text(cid: str) -> str:
    m = re.search(rf"^\*\*{cid}\*\*(.*?)(?=^\*\*[A-Z]+-[0-9]+\*\*|^#|\Z)", BODY, re.S | re.M)
    assert m, cid
    return norm(m.group(1))


def rows() -> list[dict]:
    with open(TABLE, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class MaskTableTests(unittest.TestCase):
    def test_columns_equal_template(self):
        with open(TEMPLATE, encoding="utf-8", newline="") as f:
            template = next(csv.reader(f))
        with open(TABLE, encoding="utf-8", newline="") as f:
            self.assertEqual(next(csv.reader(f)), template)

    def test_every_row_has_exact_clause_excerpt(self):
        for r in rows():
            self.assertIn(norm(r["exact_supporting_clause_text"]), clause_text(r["specification_clause_id"]),
                          r["mask_entry_id"])
            self.assertIn(r["author_packet_block_heading"], BODY)

    def test_unsigned_and_unfrozen(self):
        for r in rows():
            self.assertEqual(r["review_status"], "DRAFT_UNSIGNED")
            self.assertIn("independent human reviewer signature", r["independent_reviewer"])
            self.assertEqual(r["spec_version_sha256"], "TO_FREEZE")
        self.assertIn("requires independent human reviewer signature", MASK["status"])

    def test_json_and_table_agree(self):
        table = {r["mask_entry_id"]: r for r in rows()}
        for variant, entries in MASK["variants"].items():
            for e in entries:
                self.assertEqual(table[e["entry"]]["mask_variant"], variant)
                self.assertEqual(table[e["entry"]]["output_or_predicate_signal"], e["signal"])

    def test_variants_valid(self):
        for entries in MASK["variants"].values():
            validate_mask(entries, MATERIALS["output_ports"])

    def test_validate_rejects_bad_masks(self):
        prim = MASK["variants"]["primary"]
        with self.assertRaises(ValueError):
            validate_mask(prim[:-1], MATERIALS["output_ports"])  # rd_data uncovered
        bad = [dict(e, when={"null_signal": "rd_data", "equals": "1"}) if e["signal"] == "full" else e for e in prim]
        with self.assertRaises(ValueError):
            validate_mask(bad, MATERIALS["output_ports"])  # predicate over a masked field


class MaskedCompareTests(unittest.TestCase):
    @staticmethod
    def row(valid: str, data: str) -> dict:
        return {"outputs_after_edge_n": {"rd_valid": valid, "rd_data": data, "full": "0", "almost_full": "0",
                                         "empty": "1"},
                "next_inputs_scheduled_for_edge_n_plus_1": {"wr_en": "0"}}

    def test_dont_care_window_and_stricter_variant(self):
        prim, strict = MASK["variants"]["primary"], MASK["variants"]["stricter"]
        null = [self.row("0", "00000000"), self.row("1", "00000001")]
        dc_only = [self.row("0", "11111111"), self.row("1", "00000001")]
        in_window = [self.row("0", "00000000"), self.row("1", "00000011")]
        self.assertIsNone(compare_runs(dc_only, null, mask=prim))             # F5-style: masked
        self.assertIsNotNone(compare_runs(dc_only, null, mask=strict))        # stricter catches it
        self.assertIsNotNone(compare_runs(in_window, null, mask=prim))


@unittest.skipUnless(DOCKER, "docker not available")
class MaskOnFifoTests(unittest.TestCase):
    def test_null_trace_no_xz_and_rtl_null_agree(self):
        from test_fifo_rtl import RANDOM_DRIVER, export_null
        null = dict(LOADED["base"], verilog_sources={"ovf_fifo_null.v": export_null()[1]})
        rtl_rows = driver_run(RANDOM_DRIVER, LOADED["rtl"], "rtl", 5, step_timeout_s=5.0, budget_s=120.0)["rows"]
        null_rows = driver_run(RANDOM_DRIVER, null, "null", 5, step_timeout_s=5.0, budget_s=120.0)["rows"]
        for entries in MASK["variants"].values():
            self.assertIsNone(null_trace_xz(null_rows, entries))
            self.assertIsNone(compare_runs(rtl_rows, null_rows, mask=entries))


if __name__ == "__main__":
    unittest.main()
