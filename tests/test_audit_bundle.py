"""tools/build_audit_bundle.py guards (D-020).

D-020 (Krishika): the bundle builder must refuse to build on a dirty tree (any path, not
just the bundled ones) and must record `build_commit` = git HEAD at build time, keeping
`source_commit` as the last commit that touched the bundled paths.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "tools" / "build_audit_bundle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_audit_bundle_under_test", SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BundleGuardTests(unittest.TestCase):
    def test_refuses_dirty_tree(self):
        """A full-tree `git status --porcelain` that is non-empty stops the build before
        anything is written."""
        module = load_module()
        seen = []

        def fake_git(*args):
            seen.append(args)
            # Only the full-tree check has exactly these two arguments; the per-path check
            # carries "--" and the paths, and must stay clean so we reach the full-tree one.
            if args == ("status", "--porcelain"):
                return " M docs/some-other-file.md\n"
            return ""

        module.git = fake_git
        with self.assertRaises(SystemExit) as caught:
            module.main()
        self.assertIn("clean", str(caught.exception).lower())
        self.assertIn(("status", "--porcelain"), seen)

    def test_records_build_commit_and_keeps_source_commit(self):
        source = SRC.read_text()
        self.assertIn('"build_commit"', source)
        self.assertIn('"rev-parse", "HEAD"', source)
        self.assertIn('"source_commit"', source)


if __name__ == "__main__":
    unittest.main()
