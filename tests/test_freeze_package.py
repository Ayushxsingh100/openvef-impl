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
        never = [r for r, items in self.stages.PROVISIONAL_REASONS if not items]
        self.assertEqual(len(never), 1)
        self.assertIn("independent human reviewer", never[0])


if __name__ == "__main__":
    unittest.main()
