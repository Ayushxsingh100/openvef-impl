"""D-012 (audit finding A1-1): no runner adapter that only one fixture can reach.

1. Every ADAPTERS row's adapter is reached by at least two mandatory descriptors.
2. No descriptor fits two rows.
3. Only the ADAPTERS table selects code by input shape: the AST of dispatch, and of every
   function, is checked so that a shape branch cannot be added beside the table.

"Reachable" is decided per adapter, so two shapes handled by one rule count together.
Branches on VALUES inside one shape (event kinds, change classes) are outside this scan.
"""
from __future__ import annotations

import ast
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "runner"))

import run_f18  # noqa: E402

FIXTURES = REPO / "baseline/OpenVEF_Planning_v1_3_6/41_F18_Fixture_Inputs"
RUNNER = REPO / "runner/run_f18.py"


def single_fixture_adapters(adapters, inputs) -> list[str]:
    reach = Counter()
    for inp in inputs:
        keys = set(inp)
        for required, optional, fn in adapters:
            if required <= keys <= required | optional:
                reach[fn.__name__] += 1
    return sorted(n for n in {fn.__name__ for _, _, fn in adapters} if reach[n] < 2)


def shape_branches(tree: ast.Module) -> list[str]:
    """Functions, other than the two that may, that test an input's key set or `fixture_class`."""
    allowed = {"find_adapters", "response_stages", "response_object", "load_descriptor", "load_index", "main"}
    found = []
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name not in allowed):
        for node in ast.walk(fn):
            if isinstance(node, (ast.Compare, ast.If, ast.IfExp)):
                src = ast.unparse(node.test if not isinstance(node, ast.Compare) else node)
                if any(s in src for s in ("set(inp", "keys", "fixture_class", "fixture_id", "test_scope", "in inp",
                                          "in desc", "inp.get(")):
                    found.append(f"{fn.name}: {src}")
    return found


class DispatchShapeTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {p.stem: json.loads(p.read_text("utf-8"))["input"] for p in FIXTURES.glob("*.json")
                       if p.name != "fixture-index.json"}

    def test_no_single_fixture_adapter(self):
        self.assertEqual(len(self.inputs), 144)
        self.assertEqual(single_fixture_adapters(run_f18.ADAPTERS, self.inputs.values()), [])

    def test_no_ambiguous_shape(self):
        for fid, inp in self.inputs.items():
            self.assertLessEqual(len(run_f18.find_adapters(inp)), 1, fid)

    def test_scan_detects_a_single_fixture_adapter(self):
        def added(desc, validator):
            return None
        rows = run_f18.ADAPTERS + (({"source_file", "syntax_error"}, set(), added),)
        self.assertEqual(single_fixture_adapters(rows, self.inputs.values()), ["added"])

    def test_no_shape_branch_outside_the_table(self):
        self.assertEqual(shape_branches(ast.parse(RUNNER.read_text("utf-8"))), [])

    def test_scan_detects_a_shape_branch(self):
        src = "def dispatch(desc, v):\n    keys = set(desc['input'])\n    if keys == {'x'}:\n        return 1\n"
        self.assertTrue(shape_branches(ast.parse(src)))

    def test_dispatch_is_table_only(self):
        tree = ast.parse(RUNNER.read_text("utf-8"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "dispatch")
        self.assertEqual([ast.unparse(n.test) for n in ast.walk(fn) if isinstance(n, ast.If)], ["not rows"])


if __name__ == "__main__":
    unittest.main()
