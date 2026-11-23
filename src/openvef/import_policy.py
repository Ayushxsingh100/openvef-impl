"""Stage IMPORT_POLICY: building blocks (not yet connected to the runner).

Implemented so far:
  File 30 §2 L21; Protocol §3.4 (file 02 L133) and evaluation order (3) — non-ASCII
                   identifier scan over `tokenize.NAME` and identifier-relevant
                   `tokenize.ERRORTOKEN` tokens; diagnostic
                   NON_ASCII_IDENTIFIER|file=<FILE>|line=<LINE>|column=<COLUMN>, where
                   COLUMN is the one-based UTF-8 byte column of the lexeme start.
  File 30 §2 L16-L17; Protocol §3.4 (file 02 L129) — per-node `ast.Import`
                   classification and its total precedence.
  File 30 §2 L18; Protocol §3.4 (file 02 L131) — per-node `ast.ImportFrom`
                   classification and its total precedence.
  File 30 §2 L19; Protocol §3.4 (file 02 L133) — prohibited built-in names and
                   `builtins.<name>` (PROHIBITED_BUILTIN|name=<NAME>).
  File 30 §2 L20; Protocol §3.4 (file 02 L133) — direct `random.<attribute>` use
                   other than `random.Random` (GLOBAL_RANDOM_USE|name=random.<attr>).

The order between categories inside one file (A-013, A-014) is not decided, so this
module exposes one function per sub-rule and no combined stage yet. The `find_*`
functions return every violation as a `Finding` keyed by the node's
`(lineno, col_offset, end_lineno, end_col_offset)` (File 30 §3 L27), sorted by that
key, so any of the A-013/A-014 readings can be applied when the stage is assembled.

Unsettled inputs raise `UnsettledSpec` (docs/ambiguities.md):
  A-019 a lone CR in the source (`ast.parse` and `tokenize` disagree on line numbers).
Known limitation, as the text is written (A-018): on CPython 3.11 an f-string is a
single STRING token, so a non-ASCII identifier inside an f-string replacement field
is not scanned.
"""
from __future__ import annotations

import ast
import io
import tokenize
from typing import NamedTuple, Optional, Union

from openvef.envelope import Failure
from openvef.source_ast import UnsettledSpec

STAGE = "IMPORT_POLICY"
ERROR_CLASS = "IMPORT_POLICY_REJECT"

# File 30 §2 L16: "Permitted import roots are exactly: ..."
ALLOWED_ROOTS = frozenset({
    "__future__", "collections", "copy", "functools", "itertools", "json", "math",
    "operator", "random", "re", "statistics", "typing",
})


def _reject(diagnostic: str) -> Failure:
    return Failure(STAGE, ERROR_CLASS, diagnostic)


SourceKey = tuple[int, int, int, int]


class Finding(NamedTuple):
    """One violation (or one unsettled case) at a source position."""

    key: SourceKey
    outcome: Union[Failure, UnsettledSpec]


def node_key(node: ast.AST) -> SourceKey:
    # File 30 §3 L27: "source nodes use ascending (lineno, col_offset, end_lineno,
    # end_col_offset)".
    return (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)


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


# --- Import classification (File 30 §2 L17; Protocol §3.4 file 02 L129) ----------------

def _form_reject(file: str, node: ast.stmt, reason: str) -> Failure:
    return _reject(f"IMPORT_FORM_REJECT|file={file}|line={node.lineno}|reason={reason}")


def _not_allowed(root: str) -> Failure:
    # "`IMPORT_NOT_ALLOWED.module` is the offending root as written"
    return _reject(f"IMPORT_NOT_ALLOWED|module={root}")


def classify_import(file: str, node: ast.Import) -> Optional[Failure]:
    """Classify one `ast.Import` node; None means the exact single root is accepted.

    Total order: "(1) if `len(names) != 1`, ... MULTIPLE_NAMES; (2) if the first
    component of the imported name is not an allowed root, `IMPORT_NOT_ALLOWED|
    module=<root>`; (3) if the imported name is dotted, ... SUBMODULE_IMPORT; (4) if
    `asname` is present, ... IMPORT_ALIAS; otherwise accept the exact single root."
    """
    if len(node.names) != 1:
        return _form_reject(file, node, "MULTIPLE_NAMES")
    alias = node.names[0]
    root = alias.name.split(".", 1)[0]
    if root not in ALLOWED_ROOTS:
        return _not_allowed(root)
    if "." in alias.name:
        return _form_reject(file, node, "SUBMODULE_IMPORT")
    if alias.asname is not None:
        return _form_reject(file, node, "IMPORT_ALIAS")
    return None


def classify_import_from(file: str, node: ast.ImportFrom) -> Optional[Failure]:
    """Classify one `ast.ImportFrom` node; None means it is accepted.

    Total order (Protocol §3.4 file 02 L131): "(1) `level > 0` -> `RELATIVE_IMPORT`;
    (2) any `*` alias -> `STAR_IMPORT`; (3) if `len(names) != 1` -> `MULTIPLE_NAMES`;
    (4) if `module == "__future__"`, accept only exactly one unaliased `annotations`
    name; any other future feature -> `FUTURE_FEATURE`, while `annotations as alias`
    -> `IMPORT_ALIAS`; (5) if the first module component is not an allowed root, emit
    `IMPORT_NOT_ALLOWED|module=<root>`; (6) every remaining non-future `from` import
    emits `FROM_IMPORT_FORBIDDEN`."
    """
    if node.level > 0:
        return _form_reject(file, node, "RELATIVE_IMPORT")
    if any(alias.name == "*" for alias in node.names):
        return _form_reject(file, node, "STAR_IMPORT")
    if len(node.names) != 1:
        return _form_reject(file, node, "MULTIPLE_NAMES")
    alias = node.names[0]
    # level == 0 here, so `module` is a non-empty string.
    if node.module == "__future__":
        if alias.name != "annotations":
            return _form_reject(file, node, "FUTURE_FEATURE")
        if alias.asname is not None:
            return _form_reject(file, node, "IMPORT_ALIAS")
        return None
    root = node.module.split(".", 1)[0]
    if root not in ALLOWED_ROOTS:
        return _not_allowed(root)
    return _form_reject(file, node, "FROM_IMPORT_FORBIDDEN")


# --- Prohibited built-in names (File 30 §2 L19; Protocol §3.4 file 02 L133) -------------

PROHIBITED_NAMES = frozenset({"__import__", "eval", "exec", "compile", "open"})


def find_prohibited_names(tree: ast.Module) -> list[Finding]:
    """Every prohibited-name violation in the file, in source order.

    "AST `Name` nodes whose `id` is `__import__`, `eval`, `exec`, `compile` or `open`
    are rejected, regardless of call context. A `builtins` attribute whose attribute is
    one of those names is also rejected." (File 30 §2 L19.) `re.compile` is an
    attribute of `re`, not a `Name`, so it is not matched.

    A-016 (owner confirmation pending): only `ast.Name` nodes (any context) and
    `Attribute(value=Name(id="builtins"))` are matched; a function or parameter named
    e.g. `open`, and `__builtins__.<name>`, are not.
    """
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in PROHIBITED_NAMES:
            name = node.id
        elif (isinstance(node, ast.Attribute) and node.attr in PROHIBITED_NAMES
              and isinstance(node.value, ast.Name) and node.value.id == "builtins"):
            name = node.attr
        else:
            continue
        findings.append(Finding(node_key(node), _reject(f"PROHIBITED_BUILTIN|name={name}")))
    return sorted(findings, key=lambda f: f.key)


# --- Module-global random use (File 30 §2 L20; Protocol §3.4 file 02 L133) --------------

def find_global_random_use(tree: ast.Module) -> list[Finding]:
    """Every direct `random.<attribute>` other than `random.Random`, in source order.

    "Any direct attribute access on the module name `random` other than
    `random.Random` is rejected, including module-global PRNG calls and
    `random.SystemRandom`." (File 30 §2 L20.) `GLOBAL_RANDOM_USE.name` is the
    qualified name, e.g. `random.random` (Protocol §3.4 file 02 L125).

    A-017 (owner confirmation pending): the match is syntactic,
    `Attribute(value=Name(id="random"))`, whether or not `random` is the imported
    module. Aliases such as `r = random; r.random()` and `getattr(random, "random")`
    are not statically detected, as the text says.
    """
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "random" and node.attr != "Random"):
            findings.append(Finding(node_key(node), _reject(f"GLOBAL_RANDOM_USE|name=random.{node.attr}")))
    return sorted(findings, key=lambda f: f.key)
