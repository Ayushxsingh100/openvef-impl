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

from openvef.import_policy import ALLOWED_ROOTS, classify_import, scan_identifiers  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
