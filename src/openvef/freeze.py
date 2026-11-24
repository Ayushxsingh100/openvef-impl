"""Freeze records: verify that frozen items still match their signed hashes.

Hash rules (moved here from tests/freeze_hashes.py, which re-exports them):
- a plain path: SHA-256 of the file's bytes;
- `path#ID` (a decision record in docs/ambiguities.md): SHA-256 of the UTF-8 bytes of
  that section, from its `## ID — ...` heading line up to, but not including, the next
  line starting with `## `, with trailing whitespace removed and one LF appended.

A freeze record (design/fifo/freeze/*.json) lists the items an owner signature froze,
each with its reference and signed SHA-256. `verify` recomputes every hash; a frozen item
whose bytes changed is reported, and the caller must then treat it as not frozen.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def section_text(path: Path, ident: str) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(ident)} — .*?(?=^## |\Z)", text, re.S | re.M)
    if m is None:
        raise KeyError(f"{ident} not found in {path}")
    return m.group(0).rstrip() + "\n"


def ref_sha256(ref: str, repo: Path = REPO) -> str:
    if "#" in ref:
        path, ident = ref.split("#", 1)
        return hashlib.sha256(section_text(repo / path, ident).encode("utf-8")).hexdigest()
    return hashlib.sha256((repo / ref).read_bytes()).hexdigest()


def load(repo: Path, record_file: str) -> dict:
    return json.loads((repo / record_file).read_text(encoding="utf-8"))


def verify(repo: Path, record: dict) -> dict:
    """{"frozen": [ids whose bytes match], "changed": [ids whose bytes differ], ...}."""
    frozen, changed = [], []
    for item in record["items"]:
        refs = item["refs"]
        ok = all(ref_sha256(r["ref"], repo) == r["sha256"] for r in refs)
        (frozen if ok else changed).append(item["id"])
    return {"record": record["record_id"], "basis": record["basis"], "frozen": frozen, "changed": changed,
            "not_frozen": record.get("not_frozen", [])}
