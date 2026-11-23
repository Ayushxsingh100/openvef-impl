"""Unit tests for static AST_SIGNATURE and compilation (not F18 fixtures)."""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef.ast_signature import check_ast_signature, check_compile  # noqa: E402

DRIVER = ("import random\n\ndef create_driver(seed):\n    driver = Driver()\n"
          "    driver.rng = random.Random(seed)\n    return driver\n\nclass Driver:\n"
          "    def step(self, cycle_index, outputs_after_edge):\n        return 'COMPLETE'\n")
CHECKER = "def check_trace(trace, metadata):\n    return {'verdict': 'PASS', 'diagnostics': []}\n"


def run(driver=DRIVER, checker=CHECKER):
    trees = {"driver.py": ast.parse(driver), "checker.py": ast.parse(checker)}
    result = check_ast_signature(trees)
    if result is None:
        return None
    assert (result.stage_id, result.error_class) == ("AST_SIGNATURE", "ENTRY_POINT_REJECT")
    return result.diagnostic


def ep(file, symbol, reason):
    return f"ENTRY_POINT_REJECT|file={file}|symbol={symbol}|reason={reason}"


def driver_with(extra="", step="def step(self, cycle_index, outputs_after_edge):", factory="def create_driver(seed):",
                class_line="class Driver:", class_extra=""):
    return (f"{factory}\n    return Driver()\n\n{class_line}\n{class_extra}    {step}\n        return 'COMPLETE'\n{extra}")


class RequiredSymbolTests(unittest.TestCase):
    def test_valid_pair(self):
        self.assertIsNone(run())

    def test_missing_extra_wrong_kind(self):
        self.assertEqual(run(driver_with().replace("create_driver", "make_driver")),
                         ep("driver.py", "create_driver", "MISSING_ENTRY_POINT"))
        self.assertEqual(run(driver_with(extra="def create_driver(seed):\n    return None\n")),
                         ep("driver.py", "create_driver", "EXTRA_ENTRY_POINT"))
        self.assertEqual(run(driver_with(factory="async def create_driver(seed):")),
                         ep("driver.py", "create_driver", "WRONG_ENTRY_POINT_KIND"))
        self.assertEqual(run(driver_with(extra="create_driver = None\n").replace(
            "def create_driver(seed):\n    return Driver()\n", "")),
            ep("driver.py", "create_driver", "WRONG_ENTRY_POINT_KIND"))

    def test_any_binding_kind_counts_as_extra(self):
        self.assertEqual(run(driver_with(extra="create_driver = None\n")),
                         ep("driver.py", "create_driver", "EXTRA_ENTRY_POINT"))
        self.assertEqual(run(driver_with(extra="Driver = None\n")), ep("driver.py", "Driver", "EXTRA_ENTRY_POINT"))

    def test_annotation_without_value_is_not_a_binding(self):
        # A-021 (decided by Claude, owner review pending).
        self.assertIsNone(run(driver_with(extra="create_driver: int\n")))

    def test_nested_definition_is_not_at_the_required_scope(self):
        self.assertIsNone(run(driver_with(extra="def helper():\n    def create_driver(seed):\n        return 1\n    return create_driver\n")))

    def test_driver_kind_and_step(self):
        self.assertEqual(run("def create_driver(seed):\n    return Driver()\nDriver = 1\n"),
                         ep("driver.py", "Driver", "DRIVER_CLASS_FORM"))
        self.assertEqual(run(driver_with(step="def stop(self, cycle_index, outputs_after_edge):")),
                         ep("driver.py", "Driver.step", "MISSING_ENTRY_POINT"))
        self.assertEqual(run(driver_with(step="async def step(self, cycle_index, outputs_after_edge):")),
                         ep("driver.py", "Driver.step", "WRONG_ENTRY_POINT_KIND"))
        self.assertEqual(run(driver_with(class_extra="    step = 1\n")), ep("driver.py", "Driver.step", "EXTRA_ENTRY_POINT"))

    def test_checker_symbol(self):
        self.assertEqual(run(checker="def check(trace, metadata):\n    return None\n"),
                         ep("checker.py", "check_trace", "MISSING_ENTRY_POINT"))
        self.assertEqual(run(checker="async def check_trace(trace, metadata):\n    return None\n"),
                         ep("checker.py", "check_trace", "WRONG_ENTRY_POINT_KIND"))

    def test_fixed_sequence(self):
        # create_driver before Driver before Driver.step before check_trace.
        bad_checker = "def check(trace, metadata):\n    return None\n"
        self.assertEqual(run(driver_with(step="def step(self):"), bad_checker), ep("driver.py", "Driver.step", "PARAMETER_NAMES"))
        self.assertEqual(run("class Driver:\n    pass\n", bad_checker), ep("driver.py", "create_driver", "MISSING_ENTRY_POINT"))

    def test_required_pass_before_categories(self):
        self.assertEqual(run(driver_with(extra="class Helper:\n    pass\n"), "def check(trace, metadata):\n    return 1\n"),
                         ep("checker.py", "check_trace", "MISSING_ENTRY_POINT"))


class ParameterTests(unittest.TestCase):
    """A-020 (decided by Claude, owner review pending)."""

    def factory(self, params):
        return run(driver_with(factory=f"def create_driver({params}):"))

    def test_names(self):
        for params in ("s", "", "seed, extra", "*, seed", "self, seed"):
            with self.subTest(params=params):
                self.assertEqual(self.factory(params), ep("driver.py", "create_driver", "PARAMETER_NAMES"))

    def test_kind(self):
        self.assertEqual(self.factory("seed, /"), ep("driver.py", "create_driver", "PARAMETER_KIND"))

    def test_default_or_variadic(self):
        for params in ("seed=1", "seed, *args", "seed, **kw", "seed, *, extra", "seed, *, extra=1"):
            with self.subTest(params=params):
                self.assertEqual(self.factory(params), ep("driver.py", "create_driver", "DEFAULT_OR_VARIADIC"))

    def test_names_before_kind_before_shape(self):
        self.assertEqual(self.factory("s, /, *args"), ep("driver.py", "create_driver", "PARAMETER_NAMES"))
        self.assertEqual(self.factory("seed, /, *args"), ep("driver.py", "create_driver", "PARAMETER_KIND"))

    def test_annotations_ignored(self):
        self.assertIsNone(run(driver_with(factory="def create_driver(seed: int) -> 'Driver':")))

    def test_step_and_check_trace(self):
        self.assertEqual(run(driver_with(step="def step(self, cycle_index, outputs):")),
                         ep("driver.py", "Driver.step", "PARAMETER_NAMES"))
        self.assertEqual(run(checker="def check_trace(trace, metadata=None):\n    return 1\n"),
                         ep("checker.py", "check_trace", "DEFAULT_OR_VARIADIC"))


class CategoryTests(unittest.TestCase):
    def test_each_category(self):
        cases = [
            (driver_with(extra="def helper():\n    class Nested:\n        pass\n    return Nested\n"),
             CHECKER, ep("driver.py", "helper.Nested", "NESTED_CLASS_FORBIDDEN")),
            (driver_with(class_extra="    class Inner:\n        pass\n"), CHECKER,
             ep("driver.py", "Driver.Inner", "NESTED_CLASS_FORBIDDEN")),
            (driver_with(extra="class Helper:\n    pass\n"), CHECKER, ep("driver.py", "Helper", "CLASS_FORBIDDEN")),
            (DRIVER, CHECKER + "class Result:\n    pass\n", ep("checker.py", "Result", "CLASS_FORBIDDEN")),
            (driver_with(class_extra="    def __init__(self):\n        pass\n"), CHECKER,
             ep("driver.py", "Driver.__init__", "FORBIDDEN_METHOD")),
            (driver_with(class_extra="    async def helper(self):\n        pass\n"), CHECKER,
             ep("driver.py", "Driver.helper", "FORBIDDEN_METHOD")),
            (driver_with(class_line="class Driver(Base):"), CHECKER, ep("driver.py", "Driver", "DRIVER_CLASS_FORM")),
            (driver_with(class_line="class Driver(object, metaclass=M):"), CHECKER,
             ep("driver.py", "Driver", "DRIVER_CLASS_FORM")),
            (driver_with(extra="@wrap\ndef helper():\n    return 1\n"), CHECKER, "DECORATOR_REJECT|file=driver.py|symbol=helper"),
            (driver_with(extra="@wrap\nasync def helper():\n    return 1\n"), CHECKER,
             "DECORATOR_REJECT|file=driver.py|symbol=helper"),
            (driver_with(step="@staticmethod\n    def step(self, cycle_index, outputs_after_edge):"), CHECKER,
             "DECORATOR_REJECT|file=driver.py|symbol=Driver.step"),
            (driver_with(extra="def helper():\n    async def nested_async():\n        return 1\n    return 2\n"), CHECKER,
             ep("driver.py", "helper.nested_async", "ASYNC_DEFINITION")),
            (DRIVER, CHECKER + "def helper(stream):\n    return (item async for item in stream)\n",
             ep("checker.py", "helper", "ASYNC_COMPREHENSION")),
            (DRIVER, CHECKER + "def helper(xs):\n    return [x for x in xs if (lambda: await_)()]\n", None),
        ]
        for driver, checker, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(run(driver, checker), expected)

    def test_explicit_object_base_allowed(self):
        self.assertIsNone(run(driver_with(class_line="class Driver(object):")))

    def test_await_in_comprehension_is_async(self):
        # is_async is 0 everywhere; the ast.Await node decides.
        src = CHECKER + "def helper(xs):\n    return [await x for x in xs]\n"
        self.assertEqual(run(DRIVER, src), ep("checker.py", "helper", "ASYNC_COMPREHENSION"))
        src = CHECKER + "def helper(xs):\n    return {k: v for k, v in xs if (lambda: (await v))}\n"
        self.assertEqual(run(DRIVER, src), ep("checker.py", "helper", "ASYNC_COMPREHENSION"))

    def test_comprehension_in_default_uses_enclosing_definition(self):
        src = CHECKER + "def helper(xs=[await y for y in ()]):\n    return xs\n"
        self.assertEqual(run(DRIVER, src), ep("checker.py", "helper", "ASYNC_COMPREHENSION"))

    def test_async_comprehension_inside_async_def_is_rank_6(self):
        src = CHECKER + "def helper():\n    async def inner(s):\n        return [i async for i in s]\n    return inner\n"
        self.assertEqual(run(DRIVER, src), ep("checker.py", "helper.inner", "ASYNC_DEFINITION"))

    def test_global_category_order_across_files(self):
        driver = driver_with(extra="@wrap\ndef helper():\n    return 1\n")
        checker = CHECKER + "class Result:\n    pass\n"
        self.assertEqual(run(driver, checker), ep("checker.py", "Result", "CLASS_FORBIDDEN"))
        # Rank 1 in checker beats rank 2 in driver.
        driver = driver_with(extra="class Helper:\n    pass\n")
        checker = CHECKER + "def helper():\n    class N:\n        pass\n    return N\n"
        self.assertEqual(run(driver, checker), ep("checker.py", "helper.N", "NESTED_CLASS_FORBIDDEN"))

    def test_within_category_driver_first_then_position(self):
        driver = driver_with(extra="class B:\n    pass\nclass A:\n    pass\n")
        self.assertEqual(run(driver, CHECKER + "class C:\n    pass\n"), ep("driver.py", "B", "CLASS_FORBIDDEN"))

    def test_driver_body_statements(self):
        # A-022 (decided by Claude, owner review pending).
        self.assertIsNone(run(driver_with(class_extra='    """doc"""\n    WIDTH = 8\n    MASKS: tuple = (1, -2)\n')))
        for body in ("    X = f()\n", "    X = Y = [n for n in ()]\n", "    pass\n", "    if True:\n        X = 1\n",
                     "    self.x = 1\n", '    X = 1\n    """late"""\n'):
            with self.subTest(body=body):
                self.assertEqual(run(driver_with(class_extra=body)), ep("driver.py", "Driver", "DRIVER_CLASS_FORM"))


class CompileTests(unittest.TestCase):
    def test_compile_passes(self):
        self.assertIsNone(check_compile({"driver.py": DRIVER, "checker.py": CHECKER}))

    def test_await_outside_async_function(self):
        bad = CHECKER + "def helper(x):\n    y = 1\n    return await x\n"
        r = check_compile({"driver.py": DRIVER, "checker.py": bad})
        self.assertEqual((r.stage_id, r.error_class, r.diagnostic),
                         ("COMPILE_CHECKER", "COMPILE_ERROR", "COMPILE_ERROR|file=checker.py|line=5"))

    def test_driver_before_checker(self):
        bad = "def f():\n    return 1\nreturn 2\n"
        r = check_compile({"driver.py": bad, "checker.py": bad})
        self.assertEqual((r.stage_id, r.diagnostic), ("COMPILE_DRIVER", "COMPILE_ERROR|file=driver.py|line=3"))


if __name__ == "__main__":
    unittest.main()
