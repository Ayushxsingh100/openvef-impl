"""Every SHA-256 listed in docs/OWNER-FREEZE-PACKAGE.md matches the working tree.

Run this before signing: a mismatch means the package no longer describes the files.
"""
from __future__ import annotations

import re
import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
