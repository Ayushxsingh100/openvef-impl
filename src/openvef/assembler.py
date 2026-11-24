"""Packet-freeze and assembly checks used by F18.

Implements:
  File 31 L11, L27 — a payload line exactly equal to a reserved heading after LF
                   normalization fails packet freeze
                   (`PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE`).
  File 31 L28, L57 — an unresolved `\\{\\{[A-Z0-9_]+\\}\\}` placeholder in rendered text is a
                   hard error (`ASSEMBLY_REJECT|reason=UNRESOLVED_PLACEHOLDER`).
  File 31 L30, §8 (L87-L95) — near-match candidates that are not a full
                   `clause_id_regex` match (`F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN`);
                   extracted exact-ID set must equal manifest `clause_ids`
                   (`F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH`).
  Catalog (file 36) L18 — error class `ASSEMBLY_OR_MANIFEST_FAILURE`, disposition
                   `F18_REJECT`, stage `F18`.

A-030 (decided by Claude, approved under D-009): the near-match check runs before the
set-equality check (File 31 L30 order), and when a descriptor omits a regex the value
fixed by File 31 §8 is used.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from openvef.envelope import Failure

CLAUSE_ID_REGEX_DEFAULT = r"^[A-Z]{2,6}-[0-9]{3}$"
SEARCH_REGEX_DEFAULT = r"(?<![A-Za-z0-9_-])[A-Z]{2,6}-[0-9]{3}(?![A-Za-z0-9_-])"
NEAR_MATCH_REGEX_DEFAULT = r"(?<![A-Za-z0-9_-])[A-Za-z]{2,6}-[0-9]{1,3}(?![A-Za-z0-9_-])"
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _reject(diagnostic: str) -> Failure:
    return Failure("F18", "ASSEMBLY_OR_MANIFEST_FAILURE", diagnostic, "F18_REJECT")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_reserved_heading_lines(payload: str, reserved_headings: Iterable[str]) -> Optional[Failure]:
    headings = set(reserved_headings)
    if any(line in headings for line in _lf(payload).split("\n")):
        return _reject("PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE")
    return None


def check_unresolved_placeholders(rendered: str) -> Optional[Failure]:
    if PLACEHOLDER.search(rendered):
        return _reject("ASSEMBLY_REJECT|reason=UNRESOLVED_PLACEHOLDER")
    return None


def check_visible_clause_ids(visible_payload: str, manifest_clause_ids: Iterable[str],
                             clause_id_regex: str = CLAUSE_ID_REGEX_DEFAULT,
                             search_regex: str = SEARCH_REGEX_DEFAULT,
                             near_match_regex: str = NEAR_MATCH_REGEX_DEFAULT) -> Optional[Failure]:
    full = re.compile(clause_id_regex)
    for candidate in re.findall(near_match_regex, visible_payload):
        if not full.fullmatch(candidate):
            return _reject("F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN")
    if set(re.findall(search_regex, visible_payload)) != set(manifest_clause_ids):
        return _reject("F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH")
    return None
