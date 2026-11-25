"""D-013: every runner adapter has (a) an input contract cited to the pack and (b) at least
three synthetic non-fixture vectors, one of whose outcomes no fixture expects; and (c) boundary pairs
(an in-domain edge and a value just outside) for every property's cited domain (D-017).

Also checked:
- only the ADAPTERS table selects code by input shape, and no descriptor fits two rows;
- every value that selects code (event kinds, run-record forms, finish reasons, entry
  points) is cited; a value that a single fixture uses is flagged unless it is cited;
- no adapter names a fixture.

Limits: citations are checked to be verbatim, not to be the right reading; the value scan
covers the adapters and the selection functions in SELECTORS, not every callee.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
import unittest.mock
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for p in (HERE, REPO / "src", REPO / "runner"):
    sys.path.insert(0, str(p))

import run_f18  # noqa: E402
from adapter_contracts import CONTRACTS, DOMAINS  # noqa: E402
from adapter_vectors import BLOCKED, BOUNDARIES, JUDGED_BY_RULE, OUT_OF_DOMAIN, PASSED, VECTORS  # noqa: E402
from openvef import envelope, stage_map  # noqa: E402

PACK = REPO / "baseline/OpenVEF_Planning_v1_3_6"
FIXTURES = PACK / "41_F18_Fixture_Inputs"
RUNNER = REPO / "runner/run_f18.py"
# Functions outside the runner that choose a path from an input VALUE.
SELECTORS = {"adapt_events": [stage_map.first_event, stage_map._validate_event],
             "adapt_null_runs": [stage_map.outcome_from_record],
             "adapt_checker_runs": [stage_map.outcome_from_record],
             "adapt_response": [envelope.parse_envelope]}
OUT_OF_SCOPE = {"M13", "M14", "M15", "M17", "M27", "M36", "M37", "M41", "M48", "M50", "M53", "M54", "M58", "P17", "R07"}


def descriptors() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text("utf-8")) for p in FIXTURES.glob("*.json") if p.name != "fixture-index.json"}


def line(tag: str, n: int) -> str:
    return next(PACK.glob(f"{tag}_*")).read_text("utf-8").splitlines()[n - 1]


def citations(contract: dict) -> list[tuple]:
    return [*contract["inputs"].values(), *contract["values"].values(), *contract["outcome"]]


def contract_problems(adapters, contracts) -> list[str]:
    """Condition (a): contract present, every property of the shape cited, text verbatim."""
    out, shape = [], {}
    for required, optional, fn in adapters:
        shape.setdefault(fn.__name__, set()).update(required | optional)
    for name, keys in shape.items():
        if name not in contracts:
            out.append(f"{name}: no cited contract")
            continue
        if set(contracts[name]["inputs"]) != keys:
            out.append(f"{name}: properties without a citation {sorted(keys ^ set(contracts[name]['inputs']))}")
        out += [f"{name}: not verbatim at {t} L{n}: {s}" for t, n, s in citations(contracts[name]) if s not in line(t, n)]
    return out


def vector_problems(adapters, vectors, descs) -> list[str]:
    """Condition (b): three or more distinct non-fixture inputs; one outcome no fixture expects."""
    inputs = [d["input"] for d in descs.values()]
    expected = [d["expected"] for d in descs.values()]
    out = []
    for name in {fn.__name__ for _, _, fn in adapters}:
        vs = vectors.get(name, [])
        distinct = {json.dumps(i, sort_keys=True) for i, _ in vs}
        if len(distinct) < 3:
            out.append(f"{name}: {len(distinct)} synthetic inputs")
        if any(i in inputs for i, _ in vs):
            out.append(f"{name}: a vector is a fixture input")
        if not any(isinstance(e, str) or e not in expected for _, e in vs):
            out.append(f"{name}: no outcome differs from every fixture's")
    return out


def changed_span(a: object, b: object) -> int:
    """Length of the differing middle of two values' JSON texts (common ends removed)."""
    x, y = (json.dumps(v, sort_keys=True) for v in (a, b))
    i = 0
    while i < min(len(x), len(y)) and x[i] == y[i]:
        i += 1
    j = 0
    while j < min(len(x), len(y)) - i and x[-1 - j] == y[-1 - j]:
        j += 1
    return max(len(x), len(y)) - i - j


def boundary_problems(domains, boundaries, descs) -> list[str]:
    """Condition (c), D-017: per property, an in-domain edge and a value just outside it, each pair
    tied to a cited domain term, differing in that property only and by little, and with
    different outcomes. "Just outside" is approximated: same JSON type, integers one apart,
    other values at most 24 characters of JSON text apart."""
    inputs = [d["input"] for d in descs.values()]
    out = [f"{a}: no boundary tests" for a in domains if a not in boundaries]
    for adapter, pairs in boundaries.items():
        out += [f"{adapter}: {p} has no boundary pair" for p in set(domains[adapter]) - {p for _, p, *_ in pairs}]
        out += [f"{adapter}: {p}: no outside value is refused or rejected" for p in sorted({p for _, p, *_ in pairs})
                if all(o == PASSED for _, q, _, _, _, o in pairs if q == p)]
        for term, prop, edge, edge_exp, outside, outside_exp in pairs:
            where = f"{adapter}.{prop} ({term})"
            if prop not in domains[adapter] or term not in domains[adapter][prop]["terms"]:
                out.append(f"{where}: not a cited domain term")
            if {k: v for k, v in edge.items() if k != prop} != {k: v for k, v in outside.items() if k != prop}:
                out.append(f"{where}: more than the property differs")
            a, b = edge[prop], outside[prop]
            if type(a) is not type(b) or a == b or (abs(a - b) != 1 if type(a) is int else changed_span(a, b) > 24):
                out.append(f"{where}: not adjacent values")
            if edge_exp == outside_exp:
                out.append(f"{where}: the outcomes do not differ")
            if isinstance(edge_exp, str) and ("outside" in edge_exp or "PD-01" in edge_exp):
                out.append(f"{where}: the edge is refused")
            if edge in inputs or outside in inputs:
                out.append(f"{where}: a fixture input")
    return out


def compared_strings(fn_node: ast.AST) -> set[str]:
    """String constants an ==, != or `in` test compares against a value (not a key set)."""
    found: set[str] = set()
    for node in ast.walk(fn_node):
        if not isinstance(node, ast.Compare):
            continue
        for op, right in zip(node.ops, node.comparators):
            sides = [right, node.left] if isinstance(op, (ast.Eq, ast.NotEq)) else [right]
            for side in sides:
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    found.add(side.value)
                elif isinstance(side, (ast.Tuple, ast.List)) or (isinstance(side, ast.Set) and isinstance(op, (ast.In, ast.NotIn))):
                    found |= {e.value for e in side.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return found


def uncited_values(name: str, nodes: list[ast.AST], contracts) -> set[str]:
    cited = set(contracts[name]["values"]) | {""}
    return set().union(set(), *(compared_strings(n) for n in nodes)) - cited


def shape_branches(tree: ast.Module) -> list[str]:
    """Tests of an input's key set, labels or descriptor outside the ADAPTERS table."""
    allowed = {"find_adapters", "response_stages", "response_object", "load_descriptor", "load_index", "main"}
    found = []
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name not in allowed):
        for node in ast.walk(fn):
            if isinstance(node, (ast.If, ast.IfExp, ast.Compare)):
                src = ast.unparse(node if isinstance(node, ast.Compare) else node.test)
                if any(s in src for s in ("set(inp", "keys", "fixture_class", "fixture_id", "test_scope", "in inp",
                                          "in desc", "desc['expected']")):
                    # these two check the fields inside one property, not the input shape
                    if fn.name in ("adapt_runtime_signature", "adapt_paired_runs") and src.startswith(("set(sig)", "set(runs)")):
                        continue
                    found.append(f"{fn.name}: {src}")
    return found


def adapter_nodes() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(RUNNER.read_text("utf-8"))
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("adapt_")}


class DispatchShapeTests(unittest.TestCase):
    def setUp(self):
        self.descs = descriptors()
        self.assertEqual(len(self.descs), 144)

    # --- (a)
    def test_every_adapter_has_a_cited_contract(self):
        self.assertEqual(contract_problems(run_f18.ADAPTERS, CONTRACTS), [])
        self.assertEqual(set(CONTRACTS), {fn.__name__ for _, _, fn in run_f18.ADAPTERS})

    def test_scan_detects_missing_contract_property_and_false_quote(self):
        def added(desc, validator):
            return None
        rows = (({"x", "y"}, set(), added),)
        self.assertTrue(contract_problems(rows, {}))
        c = {"added": {"inputs": {"x": ("02", 139, "not in the pack")}, "values": {}, "outcome": []}}
        self.assertEqual(len(contract_problems(rows, c)), 2)

    # --- domains (D-015, audit A8-2)
    def test_cited_text_covers_every_property_domain(self):
        self.assertEqual({a: set(c["inputs"]) for a, c in CONTRACTS.items()}, {a: set(d) for a, d in DOMAINS.items()})
        for adapter, props in DOMAINS.items():
            for prop, d in props.items():
                text = "\n".join(line(t, n) for t, n in d["lines"])
                self.assertTrue(d["terms"])
                for term in d["terms"]:
                    with self.subTest(adapter=adapter, prop=prop, term=term):
                        self.assertIn(term, text)

    def test_every_property_is_checked_against_its_domain(self):
        self.assertEqual({a: set(d) for a, d in OUT_OF_DOMAIN.items()}, {a: set(d) for a, d in DOMAINS.items()})
        validator = run_f18.load_schema_validator(PACK)
        with unittest.mock.patch.object(run_f18, "SANDBOX", {}), \
                unittest.mock.patch.object(run_f18, "factory_checks", lambda source: None):
            for adapter, props in OUT_OF_DOMAIN.items():
                for prop, inp in props.items():
                    with self.subTest(adapter=adapter, prop=prop):
                        self.assertEqual([r[2].__name__ for r in run_f18.find_adapters(inp)], [adapter])
                        status, actual, note = run_f18.execute({"input": inp, "manifest_clause_ids": ["UART-001"]}, validator)
                        if (adapter, prop) in JUDGED_BY_RULE:
                            self.assertEqual((status, actual["disposition"]), ("EXECUTED", "REPAIR"))
                        else:
                            self.assertEqual(status, "NOT_IMPLEMENTED", (actual, note))

    def test_canonical_values_equal_the_pack(self):
        from openvef import assembler
        sidecar = json.loads(next(PACK.glob("33_*")).read_text("utf-8"))
        self.assertEqual(list(assembler.RESERVED_HEADINGS), [b["heading"] for b in sidecar["block_inventory"]])

    # --- (b)
    def test_every_adapter_has_synthetic_vectors(self):
        self.assertEqual(vector_problems(run_f18.ADAPTERS, VECTORS, self.descs), [])

    def test_scan_detects_weak_vectors(self):
        def added(desc, validator):
            return None
        m18 = self.descs["M18"]
        self.assertEqual(len(vector_problems((({"x"}, set(), added),), {"added": [(m18["input"], m18["expected"])]},
                                             self.descs)), 3)

    def test_vectors_give_the_expected_outcome(self):
        validator = run_f18.load_schema_validator(PACK)
        with unittest.mock.patch.object(run_f18, "SANDBOX", {}), \
                unittest.mock.patch.object(run_f18, "factory_checks", lambda source: None):
            for name, vectors in VECTORS.items():
                for inp, expected in vectors:
                    with self.subTest(adapter=name, inp=str(inp)[:120]):
                        rows = run_f18.find_adapters(inp)
                        self.assertEqual([r[2].__name__ for r in rows], [name])
                        status, actual, note = run_f18.execute({"input": inp, "manifest_clause_ids": ["UART-001"]}, validator)
                        if isinstance(expected, str):
                            self.assertEqual(status, "NOT_IMPLEMENTED")
                            self.assertIn(expected[len(BLOCKED):], note)
                        else:
                            self.assertEqual((status, actual), ("EXECUTED", expected))

    # --- (c) boundaries (D-017)
    def test_every_property_has_boundary_pairs(self):
        self.assertEqual(boundary_problems(DOMAINS, BOUNDARIES, self.descs), [])
        self.assertEqual(set(BOUNDARIES), {fn.__name__ for _, _, fn in run_f18.ADAPTERS})

    def test_scan_detects_weak_boundaries(self):
        domains = {"a": {"x": {"lines": [], "terms": ["t"]}, "y": {"lines": [], "terms": ["u"]}}}
        ok = ("t", "x", {"x": 1, "y": 0}, {}, {"x": 2, "y": 0}, "BLOCKED:outside")
        self.assertEqual(boundary_problems(domains, {}, {}), ["a: no boundary tests"])
        self.assertEqual(boundary_problems(domains, {"a": [ok]}, {}), ["a: y has no boundary pair"])
        domains["a"].pop("y")
        self.assertEqual(boundary_problems(domains, {"a": [ok]}, {}), [])
        for bad in (("z", *ok[1:]), (*ok[:4], {"x": 2, "y": 1}, ok[5]), (*ok[:4], {"x": 9, "y": 0}, ok[5]),
                    (*ok[:4], {"x": "2", "y": 0}, ok[5]), (*ok[:5], {}), (*ok[:3], "BLOCKED:outside x", *ok[4:]), (*ok[:5], PASSED)):
            with self.subTest(bad=bad):
                self.assertEqual(len(boundary_problems(domains, {"a": [bad]}, {})), 1)
        self.assertEqual(len(boundary_problems(domains, {"a": [ok]}, {"F": {"input": ok[2]}})), 1)

    def test_boundary_pairs_give_the_expected_outcomes(self):
        validator = run_f18.load_schema_validator(PACK)
        with unittest.mock.patch.object(run_f18, "SANDBOX", {}), \
                unittest.mock.patch.object(run_f18, "factory_checks", lambda source: None):
            for adapter, pairs in BOUNDARIES.items():
                for term, prop, edge, edge_exp, outside, outside_exp in pairs:
                    for inp, expected in ((edge, edge_exp), (outside, outside_exp)):
                        with self.subTest(adapter=adapter, prop=prop, term=term, inp=ascii(inp[prop])[:100]):
                            self.assertEqual([r[2].__name__ for r in run_f18.find_adapters(inp)], [adapter])
                            status, actual, note = run_f18.execute({"input": inp, "manifest_clause_ids": ["UART-001"]}, validator)
                            if isinstance(expected, str):
                                self.assertEqual(status, "NOT_IMPLEMENTED", actual)
                                self.assertIn(expected[len(BLOCKED):], note)
                            else:
                                self.assertEqual((status, actual), ("EXECUTED", expected))

    # --- value selection
    def test_every_selecting_value_is_cited(self):
        nodes = adapter_nodes()
        for name, node in nodes.items():
            extra = [ast.parse(inspect.getsource(f)) for f in SELECTORS.get(name, [])]
            if name in ("adapt_null_runs", "adapt_checker_runs"):
                extra.append(ast.parse(inspect.getsource(stage_map.outcome_from_record)))
            with self.subTest(name=name):
                self.assertEqual(uncited_values(name, [node, *extra], CONTRACTS), set())
        self.assertLessEqual(set(stage_map.EVENT_ROWS), set(CONTRACTS["adapt_events"]["values"]))
        self.assertEqual({s for _, s in run_f18.REQUIRED_PARAMETERS}, set(CONTRACTS["adapt_runtime_signature"]["values"]))

    def test_single_fixture_values_are_cited(self):
        kinds, reasons = Counter(), Counter()
        for d in self.descs.values():
            rows = run_f18.find_adapters(d["input"])
            for e in (d["input"]["events"] if rows and rows[0][2].__name__ == "adapt_events" else []):
                kinds[e["kind"]] += 1
            if "provider_finish_reason" in d["input"]:
                reasons[d["input"]["provider_finish_reason"]] += 1
        for value in (k for k, n in kinds.items() if n == 1):
            self.assertIn(value, CONTRACTS["adapt_events"]["values"])
        for value in (k for k, n in reasons.items() if n == 1):
            self.assertIn(value, CONTRACTS["adapt_response"]["values"])

    def test_scan_detects_an_uncited_value(self):
        node = ast.parse("def adapt_events(desc, v):\n    if desc['input']['mode'] == 'SPECIAL':\n        return 1\n")
        self.assertEqual(uncited_values("adapt_events", [node], CONTRACTS), {"SPECIAL"})

    # --- structure
    def test_no_ambiguous_shape(self):
        for fid, d in self.descs.items():
            self.assertLessEqual(len(run_f18.find_adapters(d["input"])), 1, fid)

    def test_shapes_left_out(self):
        self.assertEqual({f for f, d in self.descs.items() if not run_f18.find_adapters(d["input"])}, OUT_OF_SCOPE)

    def test_no_shape_branch_outside_the_table(self):
        self.assertEqual(shape_branches(ast.parse(RUNNER.read_text("utf-8"))), [])
        src = "def dispatch(desc, v):\n    keys = set(desc['input'])\n    if keys == {'x'}:\n        return 1\n"
        self.assertTrue(shape_branches(ast.parse(src)))

    def test_dispatch_is_table_only(self):
        fn = next(n for n in ast.parse(RUNNER.read_text("utf-8")).body
                  if isinstance(n, ast.FunctionDef) and n.name == "dispatch")
        self.assertEqual([ast.unparse(n.test) for n in ast.walk(fn) if isinstance(n, ast.If)], ["not rows"])

    def test_no_fixture_id_in_code(self):
        for path in [RUNNER, REPO / "runner/adapter_contracts.py", *(REPO / "src").rglob("*.py")]:
            for node in ast.walk(ast.parse(path.read_text("utf-8"))):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in self.descs:
                    self.fail(f"{path.name}: {node.value}")
        for fn in (n for n in ast.walk(ast.parse(RUNNER.read_text("utf-8"))) if isinstance(n, ast.FunctionDef)):
            if fn.name != "load_index" and fn.name != "load_descriptor":  # integrity checks on the index
                for node in (n for n in ast.walk(fn) if isinstance(n, ast.Compare)):
                    self.assertNotIn("fixture_id", ast.unparse(node), fn.name)


if __name__ == "__main__":
    unittest.main()
