"""Unit tests for IMPORT_POLICY building blocks (src/openvef/import_policy.py).

Hand-constructed inputs, not F18 fixtures. Run on the pinned interpreter:
    .venv/bin/python -I -m unittest discover -s tests
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.import_policy import (  # noqa: E402
    ALLOWED_ROOTS,
    check_import_policy,
    classify_import,
    classify_import_from,
    classify_module_body,
    find_global_random_use,
    find_prohibited_names,
    scan_identifiers,
)


def scan(source, file="checker.py"):
    ast.parse(source)  # the scan runs only after a successful parse
    result = scan_identifiers(file, source)
    if result is None:
        return None
    assert (result.stage_id, result.error_class, result.disposition) == ("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "REPAIR")
    return result.diagnostic


class IdentifierScanTests(unittest.TestCase):
    def test_name_token_in_function_body(self):
        self.assertEqual(scan("def check_trace(trace, metadata):\n    café = 1\n"),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=5")

    def test_column_is_utf8_bytes_after_multibyte_string(self):
        # '    label = "é"; ' is 17 characters but 18 UTF-8 bytes.
        self.assertEqual(scan('def f():\n    label = "é"; café = 1\n'),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=19")

    def test_import_name(self):
        self.assertEqual(scan("import módulo\n", "driver.py"),
                         "NON_ASCII_IDENTIFIER|file=driver.py|line=1|column=8")

    def test_attribute_name(self):
        self.assertEqual(scan("def f(obj):\n    value = obj.café\n"),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=17")

    def test_function_name(self):
        self.assertEqual(scan("def café():\n    return None\n"),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=1|column=5")

    def test_errortoken_start_character(self):
        # U+2118 is emitted as ERRORTOKEN on 3.11.
        self.assertEqual(scan("℘ = 1\n", "driver.py"), "NON_ASCII_IDENTIFIER|file=driver.py|line=1|column=1")

    def test_errortoken_after_ascii_prefix_reports_lexeme_start(self):
        self.assertEqual(scan("def f():\n    a℘ = 1\n"), "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=5")

    def test_errortoken_continuation_only_character(self):
        # U+00B7 is CONTINUE but not START; the lexeme x·y starts at x.
        self.assertEqual(scan("x·y = 1\n", "driver.py"), "NON_ASCII_IDENTIFIER|file=driver.py|line=1|column=1")

    def test_errortoken_in_def_name(self):
        self.assertEqual(scan("def ℘f():\n    return None\n", "driver.py"),
                         "NON_ASCII_IDENTIFIER|file=driver.py|line=1|column=5")

    def test_errortoken_after_multibyte_string(self):
        # '    s = "é"; ' is 13 characters, 14 bytes; lexeme a℘ starts at byte 15.
        self.assertEqual(scan('def f():\n    s = "é"; a℘ = 1\n'),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=15")

    def test_first_lexeme_in_source_order_wins(self):
        self.assertEqual(scan("a = 1\nb℘ = 2\ncafé = 3\n"), "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=1")

    def test_unicode_in_docstring_comment_and_string_is_allowed(self):
        src = '"""Café and ℘ in a docstring."""\n# café ℘ in a comment\nlabel = "naïve ℘"\nb = b"x"\n'
        self.assertIsNone(scan(src, "driver.py"))

    def test_ascii_source_passes(self):
        self.assertIsNone(scan("import random\n\ndef f(x):\n    return random.Random(x)\n"))

    def test_crlf_line_endings_keep_line_numbers(self):
        self.assertEqual(scan("x = 1\r\ncafé = 2\r\n"), "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=1")

    def test_lone_cr_ends_a_line_as_for_ast_parse(self):
        # A-019, decided by Claude (approved under D-009): Python physical lines.
        src = "x = 1\rcafé = 2\n"
        self.assertEqual(ast.parse(src).body[1].lineno, 2)
        self.assertEqual(scan(src), "NON_ASCII_IDENTIFIER|file=checker.py|line=2|column=1")
        self.assertEqual(scan("x = 1\ry = 2\r  # é\rz = 1; ab℘ = 3\n"),
                         "NON_ASCII_IDENTIFIER|file=checker.py|line=4|column=8")

    @unittest.skipUnless(sys.version_info[:2] == (3, 11), "A-018 is specific to CPython 3.11 f-string tokens")
    def test_fstring_identifier_not_scanned_on_311(self):
        # A-018 (decided by Claude, approved under D-009): the rule as written; the AST does
        # contain the non-ASCII Name.
        src = 'x = f"{café}"\n'
        self.assertIn("café", [n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)])
        self.assertIsNone(scan(src))


def first_stmt(source):
    return ast.parse(source).body[0]


def classify(source, file="driver.py"):
    node = first_stmt(source)
    assert isinstance(node, ast.Import)
    result = classify_import(file, node)
    if result is None:
        return None
    assert (result.stage_id, result.error_class, result.disposition) == ("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "REPAIR")
    return result.diagnostic


class ImportClassificationTests(unittest.TestCase):
    def test_allowed_roots_exact(self):
        self.assertEqual(ALLOWED_ROOTS, {"__future__", "collections", "copy", "functools", "itertools", "json",
                                         "math", "operator", "random", "re", "statistics", "typing"})

    def test_spec_examples(self):
        # File 30 §2 L17 / Protocol §3.4 L129: "Thus `import math, json` is MULTIPLE_NAMES; ..."
        self.assertEqual(classify("import math, json\n"), "IMPORT_FORM_REJECT|file=driver.py|line=1|reason=MULTIPLE_NAMES")
        self.assertEqual(classify("import os.path\n"), "IMPORT_NOT_ALLOWED|module=os")
        self.assertEqual(classify("import collections.abc\n"), "IMPORT_FORM_REJECT|file=driver.py|line=1|reason=SUBMODULE_IMPORT")
        self.assertEqual(classify("import math as m\n"), "IMPORT_FORM_REJECT|file=driver.py|line=1|reason=IMPORT_ALIAS")

    def test_every_allowed_root_accepted(self):
        for root in sorted(ALLOWED_ROOTS):
            with self.subTest(root=root):
                self.assertIsNone(classify(f"import {root}\n"))

    def test_disallowed_root(self):
        self.assertEqual(classify("import os\n"), "IMPORT_NOT_ALLOWED|module=os")
        self.assertEqual(classify("import builtins\n"), "IMPORT_NOT_ALLOWED|module=builtins")
        # abc, dataclasses, enum are "intentionally not allowed" (File 30 §2 L16).
        for root in ("abc", "dataclasses", "enum"):
            self.assertEqual(classify(f"import {root}\n"), f"IMPORT_NOT_ALLOWED|module={root}")

    def test_multiple_names_wins_over_root(self):
        self.assertEqual(classify("import os, json\n"), "IMPORT_FORM_REJECT|file=driver.py|line=1|reason=MULTIPLE_NAMES")

    def test_root_wins_over_alias(self):
        self.assertEqual(classify("import os as operating_system\n"), "IMPORT_NOT_ALLOWED|module=os")

    def test_submodule_wins_over_alias(self):
        self.assertEqual(classify("import collections.abc as c\n"),
                         "IMPORT_FORM_REJECT|file=driver.py|line=1|reason=SUBMODULE_IMPORT")

    def test_line_is_node_line_and_file_is_passed_through(self):
        node = ast.parse("x = 1\n\nimport math as m\n").body[1]
        self.assertEqual(classify_import("checker.py", node).diagnostic,
                         "IMPORT_FORM_REJECT|file=checker.py|line=3|reason=IMPORT_ALIAS")


def classify_from(source, file="driver.py"):
    node = first_stmt(source)
    assert isinstance(node, ast.ImportFrom)
    result = classify_import_from(file, node)
    if result is None:
        return None
    assert (result.stage_id, result.error_class, result.disposition) == ("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "REPAIR")
    return result.diagnostic


def form(reason, line=1, file="driver.py"):
    return f"IMPORT_FORM_REJECT|file={file}|line={line}|reason={reason}"


class ImportFromClassificationTests(unittest.TestCase):
    def test_spec_examples(self):
        # Protocol §3.4 L131 "Consequently ..." and File 30 §2 L18 examples.
        self.assertEqual(classify_from("from collections import abc\n"), form("FROM_IMPORT_FORBIDDEN"))
        self.assertEqual(classify_from("from collections.abc import Iterable\n"), form("FROM_IMPORT_FORBIDDEN"))
        self.assertEqual(classify_from("from os import path\n"), "IMPORT_NOT_ALLOWED|module=os")
        self.assertEqual(classify_from("from os import path as p\n"), "IMPORT_NOT_ALLOWED|module=os")
        self.assertEqual(classify_from("from . import x\n"), form("RELATIVE_IMPORT"))
        self.assertEqual(classify_from("from math import *\n"), form("STAR_IMPORT"))
        self.assertEqual(classify_from("from __future__ import annotations, annotations\n"), form("MULTIPLE_NAMES"))
        self.assertEqual(classify_from("from __future__ import annotations, division\n"), form("MULTIPLE_NAMES"))

    def test_only_accepted_form(self):
        # File 30 §2 L18: "The only accepted form is exactly `from __future__ import annotations` without alias."
        self.assertIsNone(classify_from("from __future__ import annotations\n"))

    def test_future_feature_and_alias(self):
        self.assertEqual(classify_from("from __future__ import division\n"), form("FUTURE_FEATURE"))
        self.assertEqual(classify_from("from __future__ import annotations as future_annotations\n"), form("IMPORT_ALIAS"))
        # Unsupported feature precedes the alias rule.
        self.assertEqual(classify_from("from __future__ import division as d\n"), form("FUTURE_FEATURE"))

    def test_relative_wins_over_star_and_root(self):
        self.assertEqual(classify_from("from . import *\n"), form("RELATIVE_IMPORT"))
        self.assertEqual(classify_from("from .os import x\n"), form("RELATIVE_IMPORT"))
        self.assertEqual(classify_from("from ..math import a, b\n"), form("RELATIVE_IMPORT"))

    def test_star_wins_over_future_and_root(self):
        self.assertEqual(classify_from("from __future__ import *\n"), form("STAR_IMPORT"))
        self.assertEqual(classify_from("from os import *\n"), form("STAR_IMPORT"))

    def test_multiple_names_wins_over_root(self):
        self.assertEqual(classify_from("from os import path, sep\n"), form("MULTIPLE_NAMES"))

    def test_allowed_root_still_forbidden_with_or_without_alias(self):
        self.assertEqual(classify_from("from math import ceil\n"), form("FROM_IMPORT_FORBIDDEN"))
        self.assertEqual(classify_from("from math import ceil as c\n"), form("FROM_IMPORT_FORBIDDEN"))
        # File 30 §2 L20: "`from random import ...` is not permitted by the general from-import rule."
        self.assertEqual(classify_from("from random import Random\n"), form("FROM_IMPORT_FORBIDDEN"))

    def test_disallowed_dotted_root_reports_first_component(self):
        self.assertEqual(classify_from("from os.path import join\n"), "IMPORT_NOT_ALLOWED|module=os")

    def test_line_and_file(self):
        node = ast.parse("x = 1\nfrom math import ceil\n").body[1]
        self.assertEqual(classify_import_from("checker.py", node).diagnostic,
                         form("FROM_IMPORT_FORBIDDEN", line=2, file="checker.py"))


def diagnostics(findings):
    out = []
    for f in findings:
        assert (f.outcome.stage_id, f.outcome.error_class, f.outcome.disposition) == \
            ("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "REPAIR")
        out.append(f.outcome.diagnostic)
    return out


class ProhibitedNameTests(unittest.TestCase):
    def names(self, source):
        return diagnostics(find_prohibited_names(ast.parse(source)))

    def test_each_prohibited_name_called_in_a_method(self):
        for name in ("exec", "eval", "compile", "open", "__import__"):
            src = f"class Driver:\n    def step(self, c, o):\n        {name}('x')\n        return 'COMPLETE'\n"
            with self.subTest(name=name):
                self.assertEqual(self.names(src), [f"PROHIBITED_BUILTIN|name={name}"])

    def test_inside_checker_function(self):
        self.assertEqual(self.names('def check_trace(trace, metadata):\n    return __import__("os")\n'),
                         ["PROHIBITED_BUILTIN|name=__import__"])

    def test_regardless_of_call_context(self):
        # Store, Load without call, and Del contexts all count.
        self.assertEqual(self.names("def f():\n    g = eval\n    open = 1\n    del exec\n"),
                         ["PROHIBITED_BUILTIN|name=eval", "PROHIBITED_BUILTIN|name=open", "PROHIBITED_BUILTIN|name=exec"])

    def test_builtins_attribute_without_import(self):
        self.assertEqual(self.names('def f():\n    builtins.open("x")\n'), ["PROHIBITED_BUILTIN|name=open"])

    def test_re_compile_and_other_attributes_allowed(self):
        self.assertEqual(self.names("import re\ndef f():\n    return re.compile('a'), obj.open, obj.eval\n"), [])

    def test_builtins_other_attribute_allowed(self):
        self.assertEqual(self.names("def f():\n    return builtins.len\n"), [])

    def test_a016_not_matched(self):
        # A-016 (decided by Claude, approved under D-009): definitions/parameters and __builtins__ are not Name nodes.
        self.assertEqual(self.names("def open():\n    pass\ndef f(eval):\n    return __builtins__.open\n"), [])

    def test_source_order_with_keys(self):
        found = find_prohibited_names(ast.parse("def f():\n    return eval(exec)\ndef g():\n    open\n"))
        self.assertEqual(diagnostics(found),
                         ["PROHIBITED_BUILTIN|name=eval", "PROHIBITED_BUILTIN|name=exec", "PROHIBITED_BUILTIN|name=open"])
        self.assertEqual([f.key for f in found], [(2, 11, 2, 15), (2, 16, 2, 20), (4, 4, 4, 8)])

    def test_name_inside_fstring_is_found(self):
        # The AST walk sees names inside f-string replacement fields.
        self.assertEqual(self.names('def f():\n    return f"{eval}"\n'), ["PROHIBITED_BUILTIN|name=eval"])


class GlobalRandomTests(unittest.TestCase):
    def uses(self, source):
        return diagnostics(find_global_random_use(ast.parse(source)))

    def method(self, line):
        return f"import random\ndef create_driver(seed):\n    return Driver()\nclass Driver:\n    def step(self, c, o):\n        {line}\n        return 'COMPLETE'\n"

    def test_module_global_calls(self):
        for attr, line in (("random", "value = random.random()"), ("randint", "value = random.randint(0, 1)"),
                           ("SystemRandom", "value = random.SystemRandom()"), ("seed", "random.seed(1)")):
            with self.subTest(attr=attr):
                self.assertEqual(self.uses(self.method(line)), [f"GLOBAL_RANDOM_USE|name=random.{attr}"])

    def test_random_Random_allowed(self):
        src = "import random\ndef create_driver(seed):\n    driver = Driver()\n    driver.rng = random.Random(seed)\n    return driver\n"
        self.assertEqual(self.uses(src), [])

    def test_attribute_access_without_call(self):
        self.assertEqual(self.uses("import random\ndef f():\n    return random.choice\n"),
                         ["GLOBAL_RANDOM_USE|name=random.choice"])

    def test_methods_of_a_local_generator_allowed(self):
        self.assertEqual(self.uses("import random\ndef f(seed):\n    rng = random.Random(seed)\n    return rng.random()\n"), [])

    def test_aliases_not_detected(self):
        # File 30 §2 L20: aliasing and getattr bypass static detection by design.
        self.assertEqual(self.uses('import random\ndef f():\n    r = random\n    return r.random(), getattr(random, "random")\n'), [])

    def test_a017_syntactic_without_import(self):
        # A-017 (decided by Claude, approved under D-009): matched whether or not `random` is the imported module.
        self.assertEqual(self.uses("def f(random):\n    return random.choice\n"), ["GLOBAL_RANDOM_USE|name=random.choice"])

    def test_source_order(self):
        src = "import random\ndef f():\n    a = random.randint(0, 1)\n    return random.random()\n"
        found = find_global_random_use(ast.parse(src))
        self.assertEqual(diagnostics(found), ["GLOBAL_RANDOM_USE|name=random.randint", "GLOBAL_RANDOM_USE|name=random.random"])
        self.assertEqual([f.key for f in found], [(3, 8, 3, 22), (4, 11, 4, 24)])


class ModuleBodyTests(unittest.TestCase):
    def body(self, source, file="driver.py"):
        out = []
        for f in classify_module_body(file, ast.parse(source)):
            assert (f.outcome.stage_id, f.outcome.error_class) == ("IMPORT_POLICY", "IMPORT_POLICY_REJECT")
            out.append(f.outcome.diagnostic)
        return out

    def reason(self, source, line=1):
        return [f"MODULE_STATEMENT_REJECT|file=driver.py|line={line}|reason={r}" for r in source]

    def test_executable_call_before_definitions(self):
        self.assertEqual(self.body("print(1)\nimport random\n\ndef create_driver(seed):\n    return None\n"),
                         self.reason(["MODULE_EXECUTABLE"]))

    def test_non_literal_constant(self):
        self.assertEqual(self.body("MASK = (1 << 8) - 1\nimport random\n"), self.reason(["NON_LITERAL_CONSTANT"]))

    def test_if_main_guard_is_control_flow_once(self):
        self.assertEqual(self.body('if __name__ == "__main__":\n    print(1)\nimport random\n'),
                         self.reason(["MODULE_CONTROL_FLOW"]))

    def test_every_control_flow_statement(self):
        for src in ("if x:\n    pass\n", "for a in b:\n    pass\n", "while x:\n    pass\n", "with a:\n    pass\n",
                    "try:\n    pass\nexcept E:\n    pass\n", "try:\n    pass\nexcept* E:\n    pass\n",
                    "match x:\n    case 1:\n        pass\n", "async for a in b:\n    pass\n", "async with a:\n    pass\n"):
            with self.subTest(src=src):
                self.assertEqual(self.body(src), self.reason(["MODULE_CONTROL_FLOW"]))

    def test_other_executable_statements_and_expressions(self):
        for src in ("del x\n", "assert x\n", "raise E\n", "x\n", "1\n", "f()\n", "await f()\n", "yield 1\n",
                    "[n for n in ()]\n", 'b"bytes first"\n', 'f"fstring first"\n'):
            with self.subTest(src=src):
                self.assertEqual(self.body(src), self.reason(["MODULE_EXECUTABLE"]))

    def test_allowed_module_shape(self):
        src = ('"""Café and ℘ appear only in the module docstring."""\n# café ℘ in a comment\n'
               'label = "naïve ℘"\nimport random\nfrom __future__ import annotations\n\n'
               'def create_driver(seed):\n    print(1)\n    return Driver()\n\n'
               '@decorated\nclass Driver:\n    def step(self, c, o):\n        return "COMPLETE"\n'
               'async def deferred():\n    pass\n')
        self.assertEqual(self.body(src), [])

    def test_literal_values_accepted(self):
        for value in ("'s'", "b'b'", "1", "1.5", "2j", "True", "None", "-1", "+1.5", "-2j",
                      "(1, 'a', None)", "[1, [2, (3,)]]", "{1, 2}", "{'a': [1, {'b': -2}]}", "()", "[]", "{}"):
            with self.subTest(value=value):
                self.assertEqual(self.body(f"X = {value}\n"), [])
        self.assertEqual(self.body("A = B = 1\na, *b = (1, 2)\n[c, d] = [3, 4]\nX: int = 1\nY: dict[str, int] | None = None\n"), [])

    def test_non_literal_values(self):
        for value in ("name", "f()", "a.b", "1 + 2", "1 + 2j", "not 1", "~1", "-'s'", "-x", "-(-x)", "[*a]", "{**d}",
                      "[n for n in ()]", 'f"x{1}"', "lambda: 1", "(..., f())", "(-True, g())"):
            with self.subTest(value=value):
                self.assertEqual(self.body(f"X = {value}\n"), self.reason(["NON_LITERAL_CONSTANT"]))

    def test_annotated_non_literal(self):
        self.assertEqual(self.body("X: int = f()\n"), self.reason(["NON_LITERAL_CONSTANT"]))

    def test_a015_decided_cases(self):
        # A-015, decided by Claude under standing delegation (approved under D-009).
        cases = {
            "MODULE_EXECUTABLE": ("x += 1\n", "pass\n", 'X = 1\n"late string"\n', '"""doc"""\n"""second"""\n',
                                  "global x\n", "nonlocal x\n", "return 1\n", "break\n", "continue\n",
                                  "a[f()] = 1\n", "a.b(1).c = 1\n", "X: foo() = 1\n",
                                  # case 2, owner revision: non-name targets are side effects
                                  "a.b = 1\n", "math.pi = 3\n", "d[0] = 1\n", "a, b.c = 1, 2\n",
                                  "[a, *b[0]] = 1, 2\n", "a.b: int = 1\n", "d[0]: int\n",
                                  "a[f()] = g()\n", "a.b = f()\n", "X = a.b = 1\n"),
            "NON_LITERAL_CONSTANT": ("X = ...\n", "X = (1, ...)\n", "X = -True\n", "X = +False\n",
                                     "X = -(-1)\n", "X = +-1\n", "X: foo() = g()\n"),
            None: ("x: int\n", "X: int + 1 = 1\n", "X: foo = 1\n", "a, *b = 1, 2\n", "(a, [b, c]) = 1, (2, 3)\n"),
        }
        for reason, sources in cases.items():
            for src in sources:
                with self.subTest(src=src):
                    line = src.count("\n") if "late" in src or "second" in src else 1
                    self.assertEqual(self.body(src), [] if reason is None else self.reason([reason], line))

    def test_all_findings_in_source_order(self):
        found = classify_module_body("checker.py", ast.parse("print(1)\npass\nX = f()\n"))
        self.assertEqual([f.outcome.diagnostic for f in found], [
            "MODULE_STATEMENT_REJECT|file=checker.py|line=1|reason=MODULE_EXECUTABLE",
            "MODULE_STATEMENT_REJECT|file=checker.py|line=2|reason=MODULE_EXECUTABLE",
            "MODULE_STATEMENT_REJECT|file=checker.py|line=3|reason=NON_LITERAL_CONSTANT"])


GOOD_DRIVER = ("import random\n\ndef create_driver(seed):\n    driver = Driver()\n"
               "    driver.rng = random.Random(seed)\n    return driver\n\nclass Driver:\n"
               "    def step(self, cycle_index, outputs_after_edge):\n        return \"COMPLETE\"\n")
GOOD_CHECKER = 'def check_trace(trace, metadata):\n    return {"verdict": "PASS", "diagnostics": []}\n'


class CombinedStageTests(unittest.TestCase):
    def stage(self, driver=GOOD_DRIVER, checker=GOOD_CHECKER):
        sources = {"driver.py": driver, "checker.py": checker}
        result = check_import_policy(sources, {k: ast.parse(v) for k, v in sources.items()})
        return None if result is None else result.diagnostic

    def test_valid_pair_passes(self):
        self.assertIsNone(self.stage())

    def test_driver_before_checker(self):
        self.assertEqual(self.stage("import os\n", "import sys\n"), "IMPORT_NOT_ALLOWED|module=os")

    def test_driver_import_beats_checker_identifier(self):
        self.assertEqual(self.stage("import os\n", "def f():\n    café = 1\n"), "IMPORT_NOT_ALLOWED|module=os")

    def test_identifier_scan_beats_earlier_import_in_same_file(self):
        self.assertEqual(self.stage("import os\nimport módulo\n"), "NON_ASCII_IDENTIFIER|file=driver.py|line=2|column=8")

    def test_reading_c_examples_from_a013(self):
        self.assertEqual(self.stage("import os\nprint(1)\n"), "IMPORT_NOT_ALLOWED|module=os")
        self.assertEqual(self.stage("print(1)\nimport os\n"), "MODULE_STATEMENT_REJECT|file=driver.py|line=1|reason=MODULE_EXECUTABLE")
        self.assertEqual(self.stage("def f():\n    return eval('1')\nX = [n for n in ()]\n"), "PROHIBITED_BUILTIN|name=eval")

    def test_reading_c_example_from_a014(self):
        src = "import random\ndef f():\n    v = random.random()\n    exec('x')\n"
        self.assertEqual(self.stage(src), "GLOBAL_RANDOM_USE|name=random.random")

    def test_nested_node_with_same_start_ends_first(self):
        self.assertEqual(self.stage("eval('1')\n"), "PROHIBITED_BUILTIN|name=eval")
        self.assertEqual(self.stage("x = eval('1')\n"), "MODULE_STATEMENT_REJECT|file=driver.py|line=1|reason=NON_LITERAL_CONSTANT")

    def test_equal_key_tie_uses_file30_stage_order(self):
        # A-013 tie, decided by Claude (approved under D-009): module-level policy first.
        for src in ("eval\n", "random.seed\n", "builtins.open\n"):
            with self.subTest(src=src):
                self.assertEqual(self.stage(src), "MODULE_STATEMENT_REJECT|file=driver.py|line=1|reason=MODULE_EXECUTABLE")

    def test_attribute_target_is_executable_in_stage(self):
        # A-015 case 2 (owner revision): checked in the combined stage too.
        self.assertEqual(self.stage("import math\nmath.pi = 3\n"),
                         "MODULE_STATEMENT_REJECT|file=driver.py|line=2|reason=MODULE_EXECUTABLE")

    def test_a015_cases_take_part_in_source_order(self):
        self.assertEqual(self.stage("pass\nimport os\n"), "MODULE_STATEMENT_REJECT|file=driver.py|line=1|reason=MODULE_EXECUTABLE")
        self.assertEqual(self.stage("import os\npass\n"), "IMPORT_NOT_ALLOWED|module=os")

    def test_import_inside_function_is_classified(self):
        self.assertEqual(self.stage("def f():\n    import os\n"), "IMPORT_NOT_ALLOWED|module=os")


if __name__ == "__main__":
    unittest.main()
