"""D-019 (audit A9-2): can an artifact forge what the runtime checks see?

File 30 §3 L35, L37, L39 require run-time signature checks and "`create_driver(seed)` must return
an instance of the module's `Driver` class". After artifact code has run, its process can report
anything, so neither the state of its objects nor the type of a returned object can be measured
there reliably. This module decides, from the source text alone and without running it, whether
the source stays inside a closed fragment in which it has no means to reach or change the
interpreter's internals, the `Driver` class or its own functions, and in which every return
of `create_driver` is a `Driver()` object. Assumes CPython itself behaves as documented.

PROVEN: in the fragment; what the runtime checks require follows from the source.
SELF_REPORTED: not shown; the artifact could have forged a passing run-time report. This is
not a rejection: the pack allows code outside the fragment (docs/sandbox.md "Runtime checks").
Anything not recognised is SELF_REPORTED. Call it only on sources that passed the static stages.
"""
from __future__ import annotations

import ast
import builtins

from openvef.import_policy import ALLOWED_ROOTS

PROVEN, SELF_REPORTED = "PROVEN", "SELF_REPORTED"

# Builtins that give no access to attributes by name, namespaces, frames or types.
_BUILTINS = frozenset(
    "abs all any ascii bin bool bytearray bytes chr complex dict divmod enumerate filter float format frozenset hash hex "
    "int isinstance iter len list map max min next object oct ord pow print range repr reversed round set slice sorted "
    "str sum tuple zip True False None NotImplemented Ellipsis".split()) | {
    n for n, v in vars(builtins).items() if isinstance(v, type) and issubclass(v, BaseException)}
# The only use of an imported module is `module.name` with a name listed here.
_MODULE_NAMES = {
    "math": frozenset("acos acosh asin asinh atan atan2 atanh ceil comb copysign cos cosh degrees dist e erf exp expm1 "
                      "fabs factorial floor fmod frexp fsum gamma gcd hypot inf isclose isfinite isinf isnan isqrt lcm "
                      "ldexp lgamma log log10 log1p log2 modf nan perm pi pow prod radians remainder sin sinh sqrt tan "
                      "tanh tau trunc ulp".split()),
    "itertools": frozenset("accumulate chain combinations combinations_with_replacement compress count cycle dropwhile "
                           "filterfalse groupby islice pairwise permutations product repeat starmap takewhile tee "
                           "zip_longest".split()),
    "random": frozenset({"Random"}),
    "collections": frozenset({"deque", "Counter", "OrderedDict", "defaultdict"}),
    "copy": frozenset({"copy", "deepcopy"}),
    "functools": frozenset({"reduce"}),
    "json": frozenset({"dumps", "loads"}),
    "operator": frozenset("add sub mul floordiv mod xor and_ or_ invert lshift rshift eq ne lt le gt ge itemgetter".split()),
    "re": frozenset({"compile", "match", "fullmatch", "search", "findall", "sub", "split"}),
    "statistics": frozenset({"mean", "median", "mode", "pstdev", "stdev"}),
    "typing": frozenset({"Any", "Dict", "List", "Optional", "Tuple", "Union"}),
}
_FRAME_ATTRIBUTES = ("gi_", "cr_", "ag_", "tb_", "f_back", "f_builtins", "f_code", "f_globals", "f_locals", "f_trace")


class _Outside(Exception):
    pass


def _bindings(node: ast.AST) -> list[str]:
    """Names a node binds other than through ast.Name."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        return [node.name] if node.name else []
    if isinstance(node, ast.MatchMapping):
        return [node.rest] if node.rest else []
    return []


def _is_driver_call(node: ast.AST | None) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Driver"
            and not node.args and not node.keywords)


def _check_fragment(tree: ast.Module, entry_points: tuple[str, ...]) -> None:
    modules = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    if any(a.asname for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names) or \
            not modules <= ALLOWED_ROOTS:
        raise _Outside("import form")
    parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    top = {id(n) for n in tree.body}
    for n in ast.walk(tree):
        line = f"line {getattr(n, 'lineno', 0)}"
        if isinstance(n, (ast.Global, ast.Nonlocal, ast.MatchClass, ast.AsyncFunctionDef, ast.Await)):
            raise _Outside(f"{type(n).__name__} at {line}")
        if isinstance(n, ast.ImportFrom) and n.module != "__future__":
            raise _Outside(f"import form at {line}")
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.decorator_list:
            raise _Outside(f"decorator at {line}")
        for name in _bindings(n):
            if name.startswith("__") or name in modules or (name in entry_points and id(n) not in top):
                raise _Outside(f"binding of {name} at {line}")
        if isinstance(n, ast.Name):
            use = parent[n]
            if n.id.startswith("__"):
                raise _Outside(f"name {n.id} at {line}")
            if n.id in modules:
                if not (isinstance(n.ctx, ast.Load) and isinstance(use, ast.Attribute)
                        and use.attr in _MODULE_NAMES.get(n.id, ())):
                    raise _Outside(f"use of module {n.id} at {line}")
            elif n.id in entry_points:
                if not (n.id == "Driver" and _is_driver_call(use) and use.func is n):
                    raise _Outside(f"use of {n.id} at {line}")
            elif hasattr(builtins, n.id) and n.id not in _BUILTINS:
                raise _Outside(f"builtin {n.id} at {line}")
        if isinstance(n, ast.Attribute):
            if n.attr.startswith("__") or n.attr.startswith(_FRAME_ATTRIBUTES):
                raise _Outside(f"attribute {n.attr} at {line}")
            if not isinstance(n.ctx, ast.Load) and (n.attr == "step" or n.attr == "check_trace"):
                raise _Outside(f"assignment to {n.attr} at {line}")
    for name in entry_points:
        if sum(name in _bindings(n) for n in tree.body) != 1:
            raise _Outside(f"{name} is not defined exactly once")


def _check_driver(tree: ast.Module) -> None:
    cls = next(n for n in tree.body if getattr(n, "name", None) == "Driver")
    fn = next(n for n in tree.body if getattr(n, "name", None) == "create_driver")
    if not isinstance(cls, ast.ClassDef) or not isinstance(fn, ast.FunctionDef):
        raise _Outside("entry-point kind")
    if cls.keywords or any(not (isinstance(b, ast.Name) and b.id == "object") for b in cls.bases):
        raise _Outside("Driver bases")
    if [n.name for n in cls.body if isinstance(n, ast.FunctionDef)] != ["step"] or \
            any(isinstance(n, ast.Name) and n.id == "step" and not isinstance(n.ctx, ast.Load) for n in ast.walk(cls)) or \
            any(isinstance(n, ast.ClassDef) and n is not cls for n in ast.walk(tree)):
        raise _Outside("Driver body")
    returns, nodes = [], []

    def own(node: ast.AST) -> None:
        for c in ast.iter_child_nodes(node):
            nodes.append(c)
            if not isinstance(c, (ast.FunctionDef, ast.Lambda)):
                own(c)
    own(fn)
    returns = [n for n in nodes if isinstance(n, ast.Return)]
    if any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in nodes) or not isinstance(fn.body[-1], ast.Return):
        raise _Outside("create_driver may not end in a return")
    good = {id(t) for n in ast.walk(fn) if isinstance(n, (ast.Assign, ast.AnnAssign)) and _is_driver_call(n.value)
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)}
    for r in returns:
        if _is_driver_call(r.value):
            continue
        if not isinstance(r.value, ast.Name):
            raise _Outside(f"return value at line {r.lineno}")
        var = r.value.id
        stores = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == var and not isinstance(n.ctx, ast.Load)]
        if not stores or any(id(s) not in good for s in stores) or any(var in _bindings(n) for n in ast.walk(fn)):
            raise _Outside(f"return value at line {r.lineno}")


def basis(file: str, source: str) -> dict:
    """{"basis": PROVEN | SELF_REPORTED, "reason": ...} for driver.py or checker.py."""
    try:
        tree = ast.parse(source)
        if file == "driver.py":
            _check_fragment(tree, ("create_driver", "Driver"))
            _check_driver(tree)
        else:
            _check_fragment(tree, ("check_trace",))
    except _Outside as exc:
        return {"basis": SELF_REPORTED, "reason": str(exc)}
    except (SyntaxError, ValueError, RecursionError) as exc:
        return {"basis": SELF_REPORTED, "reason": type(exc).__name__}
    return {"basis": PROVEN, "reason": "closed fragment"}
