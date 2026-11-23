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

Inputs the pack text does not settle raise `UnsettledSpec` naming the
docs/ambiguities.md item, instead of picking a reading:
  A-008 leading U+FEFF in a source string; A-009 a source string that cannot be
  encoded as UTF-8 (lone surrogates); A-010 whitespace characters beyond
  space/tab/LF/CR; A-011 SyntaxError without a positive line number, or a
  non-SyntaxError exception from `ast.parse`.

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

# Characters every reading treats as whitespace: they are whitespace in JSON
# (RFC 8259), for str.isspace() and for the Python tokenizer. Other str.isspace()
# characters (U+000B, U+000C, U+001C–U+001F, U+0085, U+00A0, U+2000–U+200A, ...) are
# not settled by the text: see A-010.
_AGREED_WHITESPACE = frozenset(" \t\n\r")


class UnsettledSpec(Exception):
    """The input reaches behaviour the pack text does not settle."""

    def __init__(self, ambiguity_id: str, detail: str):
        super().__init__(f"{ambiguity_id}: {detail}")
        self.ambiguity_id = ambiguity_id


def syntax_reject(file: str, lineno: int, offset: Optional[int]) -> Failure:
    """Build SOURCE_SYNTAX_REJECT from SyntaxError line and offset (Protocol §3.4)."""
    column = 1 if offset is None or offset < 1 else offset
    return Failure(STAGE, "SOURCE_SYNTAX_REJECT", f"SOURCE_SYNTAX_REJECT|file={file}|line={lineno}|column={column}")


def _empty(file: str) -> Failure:
    return Failure(STAGE, "SOURCE_EMPTY", f"SOURCE_EMPTY|file={file}")


def check_source(file: str, source: str) -> Failure | ast.Module:
    """Run the SOURCE_AST checks on one file (File 30 §3 L27 order)."""
    # 1. Strict UTF-8 with BOM rejection.
    try:
        source.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise UnsettledSpec("A-009", f"{file}: source not encodable as UTF-8") from exc
    if source.startswith(BOM_CHAR):
        raise UnsettledSpec("A-008", f"{file}: source starts with U+FEFF")

    # 2. Empty / whitespace-only.
    if all(c in _AGREED_WHITESPACE for c in source):
        return _empty(file)
    if all(c.isspace() for c in source):
        raise UnsettledSpec("A-010", f"{file}: whitespace-only under str.isspace() but not under every reading")

    # 3. ast.parse on the pinned interpreter.
    try:
        return ast.parse(source, filename=file, mode="exec")
    except SyntaxError as exc:  # includes IndentationError and TabError
        if not isinstance(exc.lineno, int) or exc.lineno < 1:
            raise UnsettledSpec("A-011", f"{file}: SyntaxError without a positive lineno") from exc
        return syntax_reject(file, exc.lineno, exc.offset)
    except Exception as exc:
        raise UnsettledSpec("A-011", f"{file}: ast.parse raised {type(exc).__name__}") from exc


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
