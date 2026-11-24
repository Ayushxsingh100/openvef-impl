"""Stage SOURCE_AST: source UTF-8/BOM, empty and syntax checks.

Implements:
  Protocol §3.4 stage map — "Invalid UTF-8/BOM or syntax parse error" →
                   SOURCE_AST / SOURCE_SYNTAX_REJECT; "Empty/whitespace-only source" →
                   SOURCE_AST / SOURCE_EMPTY|file=<FILE>.
  Protocol §3.4 "Deterministic evaluation order" (2) — source UTF-8/BOM/empty/syntax
                   checks in file order driver.py, then checker.py.
  File 30 §3 L27 (file-local stages) — per file: strict UTF-8 decode with BOM rejection;
                   empty/whitespace-only rejection; `ast.parse`.
  Protocol §3.4 SOURCE_SYNTAX_REJECT.column rule — from SyntaxError.offset; absent,
                   null or < 1 gives column=1; otherwise the one-based source-character
                   column CPython reports.

Readings decided by Claude under the standing delegation (docs/ambiguities.md;
approved under D-009):
  A-008 a leading U+FEFF is the BOM: SOURCE_SYNTAX_REJECT at line 1, column 1.
  A-009 a source that cannot be encoded as UTF-8 (lone surrogates) is invalid UTF-8:
        SOURCE_SYNTAX_REJECT with no position, so line 1, column 1 (A-011 fallback).
  A-010 whitespace is Python's (space, tab, form feed, CR, LF); any other character
        goes to `ast.parse`.
  A-011 a parse failure without a positive line number uses line=1, by the same
        fallback the column rule gives for a missing offset; any other exception from
        `ast.parse` is a parse error with line=1, column=1.

`ast.parse` must run on the pinned CPython 3.11.18 interpreter. Warnings that
`ast.parse` emits (e.g. invalid escape sequences) are not failures here; the runner
is started without `-W error`.
"""
from __future__ import annotations

import ast
from typing import Optional, Sequence

from openvef.envelope import Failure

STAGE = "SOURCE_AST"
FILE_ORDER = ("driver.py", "checker.py")
BOM_CHAR = "\ufeff"

# A-010 (decided by Claude, approved under D-009): Python source whitespace -- space,
# tab and form feed between tokens (Language Reference 2.1.9) plus the line terminators
# CR and LF (2.1.2). Other str.isspace() characters (U+000B, U+00A0, U+3000, ...) are
# not whitespace in Python source; `ast.parse` decides them.
PYTHON_WHITESPACE = frozenset(" \t\f\r\n")


class UnsettledSpec(Exception):
    """The input reaches behaviour the pack text does not settle."""

    def __init__(self, ambiguity_id: str, detail: str):
        super().__init__(f"{ambiguity_id}: {detail}")
        self.ambiguity_id = ambiguity_id


def syntax_reject(file: str, lineno: int, offset: Optional[int]) -> Failure:
    """Build SOURCE_SYNTAX_REJECT from SyntaxError line and offset (Protocol §3.4)."""
    column = 1 if not isinstance(offset, int) or offset < 1 else offset
    return Failure(STAGE, "SOURCE_SYNTAX_REJECT", f"SOURCE_SYNTAX_REJECT|file={file}|line={lineno}|column={column}")


def _empty(file: str) -> Failure:
    return Failure(STAGE, "SOURCE_EMPTY", f"SOURCE_EMPTY|file={file}")


def check_source(file: str, source: str) -> Failure | ast.Module:
    """Run the SOURCE_AST checks on one file (File 30 §3 L27 order)."""
    # 1. Strict UTF-8 with BOM rejection.
    try:
        source.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return syntax_reject(file, 1, None)  # A-009: no position, so line 1, column 1
    if source.startswith(BOM_CHAR):
        return syntax_reject(file, 1, 1)  # A-008: the BOM is at line 1, column 1

    # 2. Empty / whitespace-only (A-010: Python source whitespace).
    if all(c in PYTHON_WHITESPACE for c in source):
        return _empty(file)

    # 3. ast.parse on the pinned interpreter.
    try:
        return ast.parse(source, filename=file, mode="exec")
    except SyntaxError as exc:  # includes IndentationError and TabError
        # A-011: a missing or non-positive line number falls back to line 1.
        lineno = exc.lineno if isinstance(exc.lineno, int) and exc.lineno >= 1 else 1
        return syntax_reject(file, lineno, exc.offset)
    except Exception:  # e.g. MemoryError for very deep nesting: A-011, no position
        return syntax_reject(file, 1, None)


def check_sources(sources: Sequence[tuple[str, str]]) -> Failure | dict[str, ast.Module]:
    """Check (filename, source) pairs in file order; the first failure wins (Protocol §3.4 (2))."""
    names = [name for name, _ in sources]
    if names != list(FILE_ORDER):
        raise ValueError(f"sources must be given in order {FILE_ORDER}, got {names}")
    modules: dict[str, ast.Module] = {}
    for name, source in sources:
        result = check_source(name, source)
        if isinstance(result, Failure):
            return result
        modules[name] = result
    return modules
