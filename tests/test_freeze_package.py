"""Every SHA-256 listed in docs/OWNER-FREEZE-PACKAGE.md matches the working tree.

Run this before signing: a mismatch means the package no longer describes the files.
"""
from __future__ import annotations

import re
import sys
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from freeze_hashes import REPO, ref_sha256  # noqa: E402

PACKAGE = (REPO / "docs" / "OWNER-FREEZE-PACKAGE.md").read_text(encoding="utf-8")
# A table row naming `path` or `path#ID` and then a 64-hex SHA-256 in backticks.
ROW = re.compile(r"^\|.*?`((?:docs|design)/[^`#]+(?:#[A-Z]-[0-9]{3}[a-z]?)?)`.*?`([0-9a-f]{64})`", re.M)


class FreezePackageTests(unittest.TestCase):
    def test_hashes_match(self):
        rows = ROW.findall(PACKAGE)
        self.assertGreaterEqual(len(rows), 18)
        for ref, sha in rows:
            with self.subTest(ref=ref):
                self.assertEqual(ref_sha256(ref), sha)

    def test_every_listed_decision_present(self):
        for ident in ("D-004", "D-004a", "D-005", "D-006", "A-040", "A-041", "A-042", "A-043", "A-044"):
            self.assertIn(f"`docs/ambiguities.md#{ident}`", PACKAGE)


class FreezeRecordTests(unittest.TestCase):
    """design/fifo/freeze/freeze-record-2026-11-24.json against the signed package."""

    def setUp(self):
        sys.path.insert(0, str(REPO / "src"))
        from openvef import freeze, simulator_stages
        self.freeze, self.stages = freeze, simulator_stages
        self.record = freeze.load(REPO, simulator_stages.FREEZE_RECORD)

    def test_items_are_the_signed_lines(self):
        signed = re.findall(r"^\| ([A-F][0-9]) \|.*\| \[x\] Approve \[ \] Change \| \[ \] Approve \[ \] Change \|",
                            PACKAGE, re.M)
        self.assertEqual([i["id"] for i in self.record["items"]], signed)
        self.assertEqual(len(signed), 20)

    def test_record_hashes_are_the_package_hashes(self):
        listed = dict(ROW.findall(PACKAGE))
        for item in self.record["items"]:
            for r in item["refs"]:
                self.assertEqual(listed[r["ref"]], r["sha256"], (item["id"], r["ref"]))

    def test_verify_all_frozen(self):
        v = self.freeze.verify(REPO, self.record)
        self.assertEqual(v["changed"], [])
        self.assertEqual(len(v["frozen"]), 20)

    def test_changed_bytes_unfreeze(self):
        real = self.freeze.ref_sha256
        def fake(ref, repo=REPO):
            return "0" * 64 if ref == "design/fifo/rtl/ovf_fifo.v" else real(ref, repo)
        with unittest.mock.patch.object(self.freeze, "ref_sha256", fake):
            v = self.freeze.verify(REPO, self.record)
        self.assertEqual(v["changed"], ["C1"])

    def test_mask_never_settled_by_owner_freeze(self):
        self.assertNotIn("G", [i["id"] for i in self.record["items"]])
        done = {i["id"] for i in self.record["items"]}
        provisional, cleared = self.stages.open_reasons(done, None)
        self.assertEqual(len(provisional), 1)
        self.assertIn("independent human reviewer", provisional[0])
        self.assertEqual(cleared, [])

    def deviation(self):
        dev = self.freeze.load(REPO, self.stages.DEVIATION_RECORD)
        return dict(self.freeze.verify(REPO, dev), label=dev["label"])

    def test_dev001_clears_only_the_mask_reason_with_its_label(self):
        done = {i["id"] for i in self.record["items"]}
        provisional, cleared = self.stages.open_reasons(done, self.deviation())
        self.assertEqual(provisional, [])
        self.assertEqual([c["label"] for c in cleared], ["cleared under DEV-001 (non-independent mask review)"])
        provisional, cleared = self.stages.open_reasons(set(), self.deviation())
        self.assertEqual((len(provisional), len(cleared)), (5, 1))

    def test_dev001_hashes_are_package_section_g(self):
        g = dict(re.findall(r"^\| `(design/fifo/mask/[^`]+)` \| `([0-9a-f]{64})` \|", PACKAGE, re.M))
        dev = self.freeze.load(REPO, self.stages.DEVIATION_RECORD)
        self.assertEqual({r["ref"]: r["sha256"] for r in dev["items"][0]["refs"]}, g)

    def test_changed_mask_is_not_cleared(self):
        real = self.freeze.ref_sha256
        def fake(ref, repo=REPO):
            return "0" * 64 if ref.startswith("design/fifo/mask/") else real(ref, repo)
        with unittest.mock.patch.object(self.freeze, "ref_sha256", fake):
            provisional, cleared = self.stages.open_reasons({i["id"] for i in self.record["items"]}, self.deviation())
        self.assertEqual((len(provisional), cleared), (1, []))

    def test_d009_readings_match(self):
        v = self.freeze.verify(REPO, self.freeze.load(REPO, self.stages.READINGS_RECORD))
        self.assertEqual(v["changed"], [])
        self.assertEqual(len(v["frozen"]), 40)  # 7 + 23 + 1 + 8 readings and the F15 case table


if __name__ == "__main__":
    unittest.main()
