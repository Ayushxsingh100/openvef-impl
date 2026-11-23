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
    classify_import,
    classify_import_from,
    find_global_random_use,
    find_prohibited_names,
    scan_identifiers,
)
from openvef.source_ast import UnsettledSpec  # noqa: E402


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

    def test_lone_cr_is_unsettled(self):
        with self.assertRaises(UnsettledSpec) as cm:
            scan("x = 1\ry = 2\n")
        self.assertEqual(cm.exception.ambiguity_id, "A-019")

    def test_fstring_identifier_not_scanned_on_311(self):
        # A-018: records CPython 3.11 behaviour of the rule as written; the AST does
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
        # Planned reading (A-016): definitions/parameters and __builtins__ are not Name nodes.
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
        # Planned reading (A-017): matched whether or not `random` is the imported module.
        self.assertEqual(self.uses("def f(random):\n    return random.choice\n"), ["GLOBAL_RANDOM_USE|name=random.choice"])

    def test_source_order(self):
        src = "import random\ndef f():\n    a = random.randint(0, 1)\n    return random.random()\n"
        found = find_global_random_use(ast.parse(src))
        self.assertEqual(diagnostics(found), ["GLOBAL_RANDOM_USE|name=random.randint", "GLOBAL_RANDOM_USE|name=random.random"])
        self.assertEqual([f.key for f in found], [(3, 8, 3, 22), (4, 11, 4, 24)])


if __name__ == "__main__":
    unittest.main()
