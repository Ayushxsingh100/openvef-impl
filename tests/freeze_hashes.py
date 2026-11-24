"""Hashes used by docs/OWNER-FREEZE-PACKAGE.md (imported by tests/test_freeze_package.py).

The rules live in src/openvef/freeze.py, so the runner and the tests use one definition.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.freeze import ref_sha256, section_text  # noqa: E402,F401
