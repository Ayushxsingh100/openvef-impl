"""Stage PARSE_SCHEMA, part 1b: response-schema and assumption clause-ID checks.

Implements:
  File 30 §1 L7  — reject unknown/missing fields, wrong constants, wrong filenames and
                   wrong field types, using the canonical Draft 2020-12 schema
                   34_OpenVEF_Response_Schema_v1.0.json.
  File 30 §1 L9  — every assumptions[].clause_id is an exact member of the frozen
                   manifest `clause_ids` array or the reserved literal `UNSPECIFIED`;
                   unknown IDs are rejected.
  File 30 §1 "JSON Pointer selection rule" / Protocol §3.4 "JSON Pointer selection"
                 — collect every validator error, convert `absolute_path` to RFC 6901
                   tokens, use the parent pointer for `required`/`additionalProperties`,
                   sort by the four-level key, emit the first error's instance pointer;
                   a clause-ID rejection emits /assumptions/<lowest index>/clause_id.

Validator: jsonschema 4.26.0 (owner decision D-001), pinned with hashes in
requirements.lock.

Not checked here: the File 30 §1 L9 requirement that `UNSPECIFIED` text "must identify
the missing behavior" — see docs/ambiguities.md A-004.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from openvef.envelope import STAGE, Failure

SCHEMA_REL = "34_OpenVEF_Response_Schema_v1.0.json"
UNSPECIFIED = "UNSPECIFIED"

# Protocol §3.4 sort level (2): these keywords first, in this order; all others after,
# alphabetically.
_KEYWORD_RANK = ("additionalProperties", "required", "const", "type", "minLength", "maxItems")


@dataclass(frozen=True)
class ValidatedResponse:
    """A response object that passed schema and clause-ID validation."""

    obj: Any


def load_validator(schema_path: Path) -> Draft202012Validator:
    """Load the canonical response schema and build a Draft 2020-12 validator."""
    schema = json.loads(schema_path.read_bytes())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _rfc6901_token(token: str | int) -> str:
    # Order matters: escape "~" before "/" (RFC 6901 §3).
    return str(token).replace("~", "~0").replace("/", "~1")


def _tokens(path: Iterable[str | int]) -> tuple[str, ...]:
    return tuple(_rfc6901_token(t) for t in path)


def _pointer(tokens: Sequence[str]) -> str:
    # Project display form for the root pointer is "/".
    return "/" + "/".join(tokens)


def _token_seq_key(tokens: Sequence[str]) -> tuple[tuple[int, ...], ...]:
    # Lexicographic by Unicode code point per token; Python tuple comparison puts a
    # shorter equal prefix first.
    return tuple(tuple(ord(c) for c in t) for t in tokens)


def _keyword_key(keyword: str) -> tuple[int, tuple[int, ...]]:
    if keyword in _KEYWORD_RANK:
        return (_KEYWORD_RANK.index(keyword), ())
    return (len(_KEYWORD_RANK), tuple(ord(c) for c in keyword))


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _instance_tokens(error: ValidationError) -> tuple[str, ...]:
    # For `required` and `additionalProperties` the report is the parent instance
    # pointer. jsonschema reports both keywords on the object that owns them, so
    # absolute_path already *is* the parent pointer: it never names the missing or
    # extra child.
    return _tokens(error.absolute_path)


def _sort_key(error: ValidationError) -> tuple:
    return (
        _token_seq_key(_instance_tokens(error)),
        _keyword_key(str(error.validator)),
        _token_seq_key(_tokens(error.absolute_schema_path)),
        _canonical_json(error.validator_value),
    )


def _reject(pointer: str) -> Failure:
    return Failure(STAGE, "SCHEMA_REJECT", f"SCHEMA_REJECT|pointer={pointer}")


def validate_schema(validator: Draft202012Validator, obj: Any) -> Failure | ValidatedResponse:
    """Validate a decoded envelope against the response schema (File 30 §1)."""
    errors = list(validator.iter_errors(obj))
    if not errors:
        return ValidatedResponse(obj)
    first = min(errors, key=_sort_key)
    return _reject(_pointer(_instance_tokens(first)))


def validate_clause_ids(response: ValidatedResponse, manifest_clause_ids: Sequence[str]) -> Failure | ValidatedResponse:
    """Check each assumptions[].clause_id against the frozen manifest (File 30 §1 L9).

    Must run only on a schema-valid response, so `assumptions` is a list of objects
    whose `clause_id` is a non-empty string.
    """
    allowed = set(manifest_clause_ids)
    if UNSPECIFIED in allowed:
        # File 31 L29: UNSPECIFIED "must never appear in clause_ids".
        raise ValueError("manifest clause_ids contains the reserved value UNSPECIFIED")
    for index, assumption in enumerate(response.obj["assumptions"]):
        clause_id = assumption["clause_id"]
        if clause_id != UNSPECIFIED and clause_id not in allowed:
            return _reject(f"/assumptions/{index}/clause_id")
    return response
