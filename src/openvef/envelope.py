"""Stage PARSE_SCHEMA, part 1a: response-envelope checks.

Implements:
  File 30 §1 L7  — one UTF-8 JSON object; reject invalid UTF-8, BOM, prose, fences,
                   trailing non-whitespace, truncated JSON, duplicate object keys;
                   never strip, coerce, recover or normalize.
  Protocol §3.4 (JSON Pointer selection) — duplicate keys, invalid UTF-8, BOM,
                   malformed envelope or JSON syntax emit SCHEMA_REJECT|pointer=/.
  Protocol §3.4 stage map — provider max-token truncation is OUTPUT_TRUNCATED at
                   PARSE_SCHEMA. Precedence versus envelope checks: see
                   docs/ambiguities.md A-001 (provisional, owner confirmation pending).

Not implemented here: Draft 2020-12 schema validation and clause-ID checks (part 1b),
which need the pinned `jsonschema` validator (docs/ambiguities.md D-001).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

STAGE = "PARSE_SCHEMA"
BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class Failure:
    """One deterministic repair outcome (Protocol §3.4 stage map)."""

    stage_id: str
    error_class: str
    diagnostic: str
    disposition: str = "REPAIR"


@dataclass(frozen=True)
class Envelope:
    """A successfully decoded response object, ready for schema validation."""

    obj: Any


class _DuplicateKey(Exception):
    pass


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen[key] = value
    return seen


def _reject_nonstandard_constant(token: str) -> Any:
    # Python's json module accepts NaN/Infinity/-Infinity, which are not JSON
    # (RFC 8259). See docs/ambiguities.md A-003.
    raise ValueError(f"non-standard JSON constant {token}")


def _root_reject() -> Failure:
    return Failure(STAGE, "SCHEMA_REJECT", "SCHEMA_REJECT|pointer=/")


def parse_envelope(raw: bytes, provider_finish_reason: Optional[str] = None) -> Failure | Envelope:
    """Decode the raw provider response bytes into one JSON value, or fail."""
    # A-001 (provisional): explicit provider max-token truncation is reported
    # before envelope decoding, so it is "reported separately" (File 30 §1).
    if provider_finish_reason == "length":
        return Failure(STAGE, "OUTPUT_TRUNCATED", "OUTPUT_TRUNCATED")

    if raw.startswith(BOM):
        return _root_reject()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _root_reject()

    try:
        obj = json.loads(
            text,
            object_pairs_hook=_reject_duplicates,
            parse_constant=_reject_nonstandard_constant,
        )
    except (_DuplicateKey, ValueError):
        # json.JSONDecodeError is a ValueError subclass: covers prose, fences,
        # trailing non-whitespace and truncated JSON without any recovery.
        return _root_reject()
    return Envelope(obj)
