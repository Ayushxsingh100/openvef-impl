"""Hashes used by docs/OWNER-FREEZE-PACKAGE.md (imported by tests/test_freeze_package.py).

- A plain path: SHA-256 of the file's bytes.
- `path#ID` (a decision record in docs/ambiguities.md): SHA-256 of the UTF-8 bytes of
  that section, from its `## ID — ...` heading line up to, but not including, the next
  line starting with `## `, with trailing whitespace removed and one LF appended.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def section_text(path: Path, ident: str) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(ident)} — .*?(?=^## |\Z)", text, re.S | re.M)
    if m is None:
        raise KeyError(f"{ident} not found in {path}")
    return m.group(0).rstrip() + "\n"


def ref_sha256(ref: str) -> str:
    if "#" in ref:
        path, ident = ref.split("#", 1)
        return hashlib.sha256(section_text(REPO / path, ident).encode("utf-8")).hexdigest()
    return hashlib.sha256((REPO / ref).read_bytes()).hexdigest()
