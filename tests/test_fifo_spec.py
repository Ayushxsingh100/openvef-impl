"""Mechanical checks on the DRAFT FIFO specification v0.2 (D-005; docs/fifo-spec-v0.2.md).

These checks do not approve the draft; only the owners can. They check that:
- the File 31 clause-ID extraction, using the regexes from the File 38 template, finds
  exactly the clause IDs the payload text defines, with no near-match tokens (File 31
  L29-L30, L91-L95);
- the FIFO-042 executable predicate runs under Python 3.11 and agrees with FIFO-041;
- the worked example agrees with a model of the read/write and status clauses
  (FIFO-020 to FIFO-035).
"""
from __future__ import annotations

import itertools
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPEC = (REPO / "docs" / "fifo-spec-v0.2.md").read_text(encoding="utf-8")
TEMPLATE = json.loads((REPO / "baseline/OpenVEF_Planning_v1_3_6/38_Authoring_Packet_Manifest_Template_v1.3.6.json")
                      .read_text(encoding="utf-8"))
MARKER = "<!-- PAYLOAD TEXT BELOW -->"
FRONT, BODY = SPEC.split(MARKER, 1)
BLOCKS = ("## [Design specification]", "## [Port manifest]", "## [Reset and legal-input rules]")


def defined_ids() -> list[str]:
    return re.findall(r"^\*\*([A-Z]+-[0-9]+)\*\*", BODY, re.M)


def predicate():
    code = re.search(r"```python\n(.*?)```", BODY, re.S).group(1)
    namespace: dict = {}
    exec(compile(code, "FIFO-042", "exec"), namespace)  # noqa: S102 - the spec's own code
    return namespace["legal_input"]


class ClauseIdTests(unittest.TestCase):
    def test_status_is_draft(self):
        self.assertIn("**Status: DRAFT. Not approved, not frozen.**", FRONT)

    def test_payload_blocks_present_in_order(self):
        positions = [BODY.index(b) for b in BLOCKS]
        self.assertEqual(positions, sorted(positions))

    def test_defined_ids_unique_and_match_regex(self):
        ids = defined_ids()
        self.assertEqual(len(ids), len(set(ids)))
        full = re.compile(TEMPLATE["clause_id_regex"])
        for cid in ids:
            self.assertIsNotNone(full.fullmatch(cid), cid)

    def test_extraction_equals_defined_set(self):
        visible = set(re.findall(TEMPLATE["clause_id_search_regex"], BODY))
        self.assertEqual(visible, set(defined_ids()))

    def test_no_near_match_errors(self):
        full = re.compile(TEMPLATE["clause_id_regex"])
        bad = [t for t in re.findall(TEMPLATE["clause_id_near_match_regex"], BODY) if not full.fullmatch(t)]
        self.assertEqual(bad, [])

    def test_every_reference_is_defined(self):
        refs = set(re.findall(TEMPLATE["clause_id_search_regex"], FRONT))
        self.assertLessEqual(refs, set(defined_ids()))


class PredicateTests(unittest.TestCase):
    def test_matches_fifo_041(self):
        legal = predicate()
        for wr, rd, full, af, empty, valid in itertools.product("01", repeat=6):
            for data in ("00000000", "10100101", "11111111"):
                vector = {"wr_en": wr, "wr_data": data, "rd_en": rd}
                sampled = {"rd_valid": valid, "rd_data": data, "full": full, "almost_full": af, "empty": empty}
                expected = not (full == "1" and wr == "1" and rd == "0")
                self.assertEqual(legal(vector, sampled), expected, (vector, sampled))

    def test_all_zero_vector_is_legal_in_every_state(self):
        legal = predicate()
        zero = {"wr_en": "0", "wr_data": "00000000", "rd_en": "0"}
        for full, af, empty in itertools.product("01", repeat=3):
            self.assertTrue(legal(zero, {"rd_valid": "0", "rd_data": "00000000", "full": full, "almost_full": af,
                                         "empty": empty}))

    def test_driver_vector_keys(self):
        self.assertIn("Every driver vector has exactly the keys `wr_en`, `wr_data` and `rd_en`.", BODY)


class WorkedExampleTests(unittest.TestCase):
    def test_example_follows_clauses(self):
        table = BODY.split("### Worked example", 1)[1].split("## [Port manifest]", 1)[0]
        rows = [[cell.strip() for cell in line.strip("|").split("|")]
                for line in table.splitlines() if re.match(r"^\| [0-9]+ \|", line)]
        self.assertGreater(len(rows), 10)
        words: list[str] = []  # after reset: c = 0 (FIFO-010)
        for edge, wr, data, rd, c, valid, rdata, full, af, empty in rows:
            read = rd == "1" and len(words) > 0                    # FIFO-020, FIFO-023
            write = wr == "1" and (len(words) < 4 or read)        # FIFO-024, FIFO-030
            self.assertFalse(wr == "1" and rd == "0" and len(words) == 4, f"edge {edge}: illegal (FIFO-031)")
            popped = words.pop(0) if read else None               # FIFO-025: oldest first
            if write:
                words.append(data)                                # FIFO-026: no bypass
            self.assertEqual(int(c), len(words), f"edge {edge}: c")               # FIFO-027
            self.assertEqual(valid, "1" if read else "0", f"edge {edge}: rd_valid")  # FIFO-021
            self.assertEqual(rdata, popped if read else "-", f"edge {edge}: rd_data")  # FIFO-021/022
            self.assertEqual(full, "1" if len(words) == 4 else "0", f"edge {edge}: full")   # FIFO-028
            self.assertEqual(empty, "1" if not words else "0", f"edge {edge}: empty")       # FIFO-028
            self.assertEqual(af, "1" if len(words) >= 3 else "0", f"edge {edge}: almost_full")  # FIFO-029


if __name__ == "__main__":
    unittest.main()
