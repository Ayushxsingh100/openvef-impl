"""Stage IMPORT_POLICY: building blocks (not yet connected to the runner).

Implemented so far:
  File 30 §2 L21; Protocol §3.4 (file 02 L133) and evaluation order (3) — non-ASCII
                   identifier scan over `tokenize.NAME` and identifier-relevant
                   `tokenize.ERRORTOKEN` tokens; diagnostic
                   NON_ASCII_IDENTIFIER|file=<FILE>|line=<LINE>|column=<COLUMN>, where
                   COLUMN is the one-based UTF-8 byte column of the lexeme start.

The order between categories inside one file (A-013, A-014) is not decided, so this
module exposes one function per sub-rule and no combined stage yet.

Unsettled inputs raise `UnsettledSpec` (docs/ambiguities.md):
  A-019 a lone CR in the source (`ast.parse` and `tokenize` disagree on line numbers).
Known limitation, as the text is written (A-018): on CPython 3.11 an f-string is a
single STRING token, so a non-ASCII identifier inside an f-string replacement field
is not scanned.
"""
from __future__ import annotations

import io
import tokenize
from typing import Optional

from openvef.envelope import Failure
from openvef.source_ast import UnsettledSpec

STAGE = "IMPORT_POLICY"
ERROR_CLASS = "IMPORT_POLICY_REJECT"


def _reject(diagnostic: str) -> Failure:
    return Failure(STAGE, ERROR_CLASS, diagnostic)


# --- Non-ASCII identifier scan (File 30 §2 L21; Protocol §3.4 file 02 L133) ---------

def _start(c: str) -> bool:
    # "define `START(c)` as `c.isidentifier()`"
    return c.isidentifier()


def _continue(c: str) -> bool:
    # "`CONTINUE(c)` as `("A" + c).isidentifier()`"
    return ("A" + c).isidentifier()


def _byte_column(line: str, char_index: int) -> int:
    # "one-based UTF-8 byte position at the start of the entire identifier lexeme,
    # calculated from the UTF-8 byte length of the source-line prefix"
    return len(line[:char_index].encode("utf-8")) + 1


def _non_ascii(file: str, lineno: int, line: str, char_index: int) -> Failure:
    # The offending lexeme is never echoed.
    return _reject(f"NON_ASCII_IDENTIFIER|file={file}|line={lineno}|column={_byte_column(line, char_index)}")


def _lexeme_start(line: str, index: int) -> Optional[int]:
    """Start of the identifier lexeme containing line[index], or None if the run is not one.

    "reconstruct the maximal same-line contiguous run containing the offending code
    point by extending left and right across `CONTINUE` characters; the run is an
    identifier lexeme only when its first character satisfies `START`."
    """
    start = index
    while start > 0 and _continue(line[start - 1]):
        start -= 1
    # Extending right does not move the start; the run's first character decides.
    return start if _start(line[start]) else None


def scan_identifiers(file: str, source: str) -> Optional[Failure]:
    """Return the first non-ASCII identifier rejection in `source`, or None.

    Call only after `ast.parse(source)` succeeded (Protocol §3.4 evaluation order (3)).
    """
    if "\r" in source.replace("\r\n", ""):
        raise UnsettledSpec("A-019", f"{file}: lone CR; ast.parse and tokenize disagree on line numbers")

    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.NAME:
            # "For a `NAME` token, reject it if any code point is above U+007F."
            if not tok.string.isascii():
                return _non_ascii(file, tok.start[0], tok.line, tok.start[1])
        elif tok.type == tokenize.ERRORTOKEN:
            # "For an `ERRORTOKEN`, inspect each non-ASCII code point in source order."
            for offset, ch in enumerate(tok.string):
                if ch.isascii():
                    continue
                start = _lexeme_start(tok.line, tok.start[1] + offset)
                if start is not None:
                    return _non_ascii(file, tok.start[0], tok.line, start)
        # STRING and COMMENT tokens are not scanned.
    return None
