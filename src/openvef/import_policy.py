"""Stage IMPORT_POLICY.

Implemented:
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
  File 30 §3 L29; Protocol §3.4 (file 02 L135) — module-body statements
                   (MODULE_STATEMENT_REJECT|file=<FILE>|line=<LINE>|reason=<REASON>).

  `check_import_policy` — the combined stage: Protocol §3.4 evaluation order (3) and
                   owner decision A-013/A-014 reading (c) (Ayush's confirmation pending).

Each sub-rule function returns every violation as a `Finding` keyed by the node's
`(lineno, col_offset, end_lineno, end_col_offset)` (File 30 §3 L27). The stage
applies reading (c): per file, after the identifier scan, the finding with the
smallest key wins, whatever its category.

Readings decided by Claude under the standing delegation (docs/ambiguities.md; approved
under D-009):
  A-013 tie: findings with the same smallest key are ordered by File 30 §3 L27's stage
        list -- module-level AST policy, then import, then prohibited-name policy (with
        `random` use after prohibited names, as in File 30 §2 L19-L20). A bare
        module-level `eval` is MODULE_EXECUTABLE.
  A-015 every module-scope statement is classified; see `classify_module_body`.
  A-016, A-017 as planned (only `Name` nodes and `builtins.<name>`; `random` matched
        syntactically).
  A-018 the rule as written: on CPython 3.11 an f-string is one STRING token, so a
        non-ASCII identifier inside an f-string replacement field is not scanned.
  A-019 lines are Python physical lines (LF, CRLF or a lone CR, Language Reference
        2.1.2), as `ast.parse` counts them; the tokenizer copy has lone CRs turned
        into LF, which changes no column.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize
from typing import NamedTuple, Optional

from openvef.envelope import Failure

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
_LONE_CR = re.compile(r"\r(?!\n)")


class Finding(NamedTuple):
    """One violation at a source position."""

    key: SourceKey
    outcome: Failure


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
    # A-019: a lone CR ends a physical line for `ast.parse` but not for `tokenize`.
    # Replacing it with LF (one character for one, at a line end) aligns the line
    # numbers and leaves every line prefix, and so every column, unchanged.
    lines_source = _LONE_CR.sub("\n", source)
    for tok in tokenize.generate_tokens(io.StringIO(lines_source).readline):
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

    A-016 (decided by Claude under standing delegation, approved under D-009): only `ast.Name` nodes (any context) and
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

    A-017 (decided by Claude under standing delegation, approved under D-009): the match is syntactic,
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


# --- Module-body statements (File 30 §3 L29; Protocol §3.4 file 02 L135) ----------------

# File 30 §3 L29: "`ast.Constant` values of type string, bytes, integer, float, complex,
# boolean or `None`". The list is exhaustive: Ellipsis is not in it (A-015 case 6).
_LITERAL_TYPES = frozenset({str, bytes, int, float, complex, bool, type(None)})
# "unary plus/minus applied to a numeric literal": the type list names boolean
# separately from integer, so `bool` is not numeric here (A-015 case 7).
_NUMERIC_TYPES = frozenset({int, float, complex})

_CONTROL_FLOW = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
                 ast.Try, ast.TryStar, ast.Match)


def is_literal_only(node: ast.expr) -> bool:
    """File 30 §3 L29: "Literal-only expressions are `ast.Constant` values of type string,
    bytes, integer, float, complex, boolean or `None`, and recursively nested
    tuple/list/set/dict literals containing only those values; unary plus/minus
    applied to a numeric literal is permitted. Names, calls, comprehensions,
    f-strings, attribute access, binary operations and other expressions are not
    literal-only."

    A-015 cases 6-8 (decided by Claude, approved under D-009): `...`, `-True` and
    `-(-1)` are not literal-only; the operand of a unary must itself be a numeric
    `ast.Constant`.
    """
    if isinstance(node, ast.Constant):
        return type(node.value) in _LITERAL_TYPES
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(is_literal_only(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        # A `None` key is `{**x}` unpacking.
        return all(k is not None and is_literal_only(k) for k in node.keys) and all(
            is_literal_only(v) for v in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return isinstance(node.operand, ast.Constant) and type(node.operand.value) in _NUMERIC_TYPES
    return False


def _is_name_target(target: ast.expr) -> bool:
    """True if the target binds plain names only (names, possibly unpacked/starred)."""
    if isinstance(target, ast.Name):
        return True
    if isinstance(target, (ast.Tuple, ast.List)):
        return all(_is_name_target(e) for e in target.elts)
    if isinstance(target, ast.Starred):
        return _is_name_target(target.value)
    return False


def _contains_call(node: Optional[ast.AST]) -> bool:
    return node is not None and any(isinstance(sub, ast.Call) for sub in ast.walk(node))


def classify_module_body(file: str, tree: ast.Module) -> list[Finding]:
    """Every module-scope violation, in source order.

    Protocol §3.4 (file 02 L135): "At module scope, allow only permitted imports, one
    optional docstring expression, synchronous undecorated function definitions
    (deferred to signature checks), the single permitted `Driver` class in
    `driver.py` (deferred to signature checks), and assignments/annotated assignments
    whose values are recursively literal-only. A non-literal assignment is
    `NON_LITERAL_CONSTANT`; module-level control-flow statements (`if`, `for`,
    `while`, `with`, `try`, `match`, `async` control flow) are `MODULE_CONTROL_FLOW`;
    other executable statements/calls/expressions are `MODULE_EXECUTABLE`."

    Imports are classified by `classify_import`/`classify_import_from`; function and
    class definitions are deferred to AST_SIGNATURE and never classified here.

    A-015 (decided by Claude under standing delegation, approved under D-009). The
    allowed list is exhaustive, `MODULE_CONTROL_FLOW` covers only the statements it
    names, and "assignments/annotated assignments" are `ast.Assign`/`ast.AnnAssign`:
      - `x += 1`, `pass`, `global`/`nonlocal`, `return`/`break`/`continue` and any
        other unlisted statement: MODULE_EXECUTABLE (cases 1, 4, 10, 11);
      - a string expression that is not the first statement: MODULE_EXECUTABLE (a
        docstring is the first statement; case 5);
      - a non-literal annotation is accepted unless it contains a call, which the
        text names as MODULE_EXECUTABLE (case 9); a non-literal value wins over it;
      - `x: int` (no value) is accepted: there is no value to fail (case 3).

    A-015 case 2 (owner decision by Krishika, revising Claude's first decision;
    Ayush's confirmation pending): a target that is not a plain name -- an attribute
    or subscript anywhere in it, e.g. `a.b = 1`, `math.pi = 3`, `d[0] = 1`,
    `a, b.c = 1, 2` -- is not a module constant but a side effect, so
    MODULE_EXECUTABLE whatever the value. File 30 L29: "attribute access ... are not
    literal-only", "other side effects are rejected"; File 30 L52/L64 and file 19
    L25/L40: "literal-only module constants", "side effects are prohibited".
    """
    findings = []

    def reject(stmt: ast.stmt, reason: str) -> None:
        findings.append(Finding(node_key(stmt), _reject(
            f"MODULE_STATEMENT_REJECT|file={file}|line={stmt.lineno}|reason={reason}")))

    def assignment(stmt: ast.stmt, value: Optional[ast.expr], targets: list[ast.expr],
                   annotation: Optional[ast.expr] = None) -> None:
        if not all(_is_name_target(t) for t in targets):
            reject(stmt, "MODULE_EXECUTABLE")  # A-015 case 2: a side effect, not a constant
        elif value is not None and not is_literal_only(value):
            reject(stmt, "NON_LITERAL_CONSTANT")
        elif _contains_call(annotation):
            reject(stmt, "MODULE_EXECUTABLE")

    for index, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(stmt, ast.Expr):
            is_docstring = index == 0 and isinstance(stmt.value, ast.Constant) and type(stmt.value.value) is str
            if not is_docstring:
                # File 30 §3 L29: "expressions other than a docstring ... are rejected".
                reject(stmt, "MODULE_EXECUTABLE")
        elif isinstance(stmt, ast.Assign):
            assignment(stmt, stmt.value, stmt.targets)
        elif isinstance(stmt, ast.AnnAssign):
            assignment(stmt, stmt.value, [stmt.target], stmt.annotation)
        elif isinstance(stmt, _CONTROL_FLOW):
            reject(stmt, "MODULE_CONTROL_FLOW")
        else:
            reject(stmt, "MODULE_EXECUTABLE")
    return sorted(findings, key=lambda f: f.key)


# --- Combined stage (Protocol §3.4 evaluation order (3); A-013/A-014 reading (c)) -------

def find_import_violations(file: str, tree: ast.Module) -> list[Finding]:
    """Every `ast.Import`/`ast.ImportFrom` node at any depth, classified per node."""
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result = classify_import(file, node)
        elif isinstance(node, ast.ImportFrom):
            result = classify_import_from(file, node)
        else:
            continue
        if result is not None:
            findings.append(Finding(node_key(node), result))
    return sorted(findings, key=lambda f: f.key)


def check_file(file: str, source: str, tree: ast.Module) -> Optional[Failure]:
    """IMPORT_POLICY for one file; None if the file passes.

    Protocol §3.4 evaluation order (3): "after successful `ast.parse`, scan ...;
    reject the first identifier lexeme containing a non-ASCII code point before
    classifying imports, prohibited names or module-body statements in that file."
    Then reading (c) (A-013/A-014, owner decision): one source-order pass, the first
    violation of any category wins.
    """
    rejected = scan_identifiers(file, source)
    if rejected is not None:
        return rejected
    # A-013 tie (decided by Claude, approved under D-009): equal keys fall back to
    # File 30 §3 L27's stage order -- module-level AST policy, import policy,
    # prohibited names -- then `random` use (File 30 §2 L20 follows L19).
    ranked = [(f.key, rank, f.outcome)
              for rank, group in enumerate((classify_module_body(file, tree), find_import_violations(file, tree),
                                            find_prohibited_names(tree), find_global_random_use(tree)))
              for f in group]
    if not ranked:
        return None
    first = min(ranked, key=lambda r: r[:2])
    # One node has one span and one category, so (key, rank) picks a single outcome.
    assert len({r[2] for r in ranked if r[:2] == first[:2]}) == 1, first
    return first[2]


def check_import_policy(sources: dict[str, str], trees: dict[str, ast.Module]) -> Optional[Failure]:
    """Run IMPORT_POLICY on driver.py, then checker.py; the first failing file wins.

    "If the identifier scan passes, complete that file's import, prohibited-name and
    module-body checks before advancing to the next file." (Protocol §3.4 (3).)
    """
    for file in ("driver.py", "checker.py"):
        result = check_file(file, sources[file], trees[file])
        if result is not None:
            return result
    return None
