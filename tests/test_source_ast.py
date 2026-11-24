"""Unit tests for stage SOURCE_AST (src/openvef/source_ast.py).

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

from openvef.envelope import Failure  # noqa: E402
from openvef.source_ast import UnsettledSpec, check_source, check_sources, syntax_reject  # noqa: E402

GOOD = "def f():\n    return 1\n"


def diag(result):
    assert isinstance(result, Failure), result
    return (result.stage_id, result.error_class, result.diagnostic, result.disposition)


class ColumnRuleTests(unittest.TestCase):
    def test_offset_none_absent_or_below_one_gives_column_1(self):
        for offset in (None, 0, -3):
            self.assertEqual(syntax_reject("driver.py", 4, offset).diagnostic,
                             "SOURCE_SYNTAX_REJECT|file=driver.py|line=4|column=1")

    def test_positive_offset_used_as_is(self):
        self.assertEqual(syntax_reject("checker.py", 2, 7).diagnostic,
                         "SOURCE_SYNTAX_REJECT|file=checker.py|line=2|column=7")

    def test_column_counts_characters_not_utf8_bytes(self):
        # "é" is two UTF-8 bytes; ")" is the 12th character, the 13th byte.
        self.assertEqual(check_source("driver.py", "é = 1; y = )\n").diagnostic,
                         "SOURCE_SYNTAX_REJECT|file=driver.py|line=1|column=12")


class SingleFileTests(unittest.TestCase):
    def test_valid_source_returns_module(self):
        self.assertIsInstance(check_source("driver.py", GOOD), ast.Module)

    def test_agreed_whitespace_is_empty(self):
        for src in ("", " ", "\n", "   \n\t", "\r\n"):
            self.assertEqual(diag(check_source("checker.py", src)),
                             ("SOURCE_AST", "SOURCE_EMPTY", "SOURCE_EMPTY|file=checker.py", "REPAIR"))

    def test_comment_only_is_not_empty(self):
        self.assertIsInstance(check_source("driver.py", "# note\n"), ast.Module)

    def test_indentation_error_is_syntax_reject(self):
        self.assertEqual(check_source("driver.py", "  x = 1\n").error_class, "SOURCE_SYNTAX_REJECT")

    def test_claude_decided_cases(self):
        # A-008..A-011, decided by Claude under standing delegation (approved under D-009).
        rej = "SOURCE_SYNTAX_REJECT|file=driver.py|line={}|column={}"
        cases = {
            "\ufeffx = 1\n": rej.format(1, 1),          # A-008: BOM at line 1, column 1
            "x = 1\ny = '\ud800'\n": rej.format(1, 1),  # A-009: no position given
            "\x0c": "SOURCE_EMPTY|file=driver.py",       # A-010: form feed is Python whitespace
            " \f\r\n\t": "SOURCE_EMPTY|file=driver.py",
            "\x0b": rej.format(1, 1),                    # A-010: not Python whitespace
            " \xa0\n": rej.format(1, 1),                 # CPython: unexpected indent, offset 1
            "x = 1\x00\n": rej.format(1, 1),            # A-011: SyntaxError without lineno
        }
        for src, diagnostic in cases.items():
            with self.subTest(src=repr(src)):
                self.assertEqual(check_source("driver.py", src).diagnostic, diagnostic)

    def test_non_syntax_error_from_parse_is_line_1_column_1(self):
        # A-011: CPython 3.11.18 raises MemoryError (no position) for very deep nesting.
        r = check_source("checker.py", "-" * 200000 + "1\n")
        self.assertEqual(r.diagnostic, "SOURCE_SYNTAX_REJECT|file=checker.py|line=1|column=1")


class FileOrderTests(unittest.TestCase):
    def test_driver_checked_before_checker(self):
        r = check_sources([("driver.py", " "), ("checker.py", "x = )\n")])
        self.assertEqual(r.diagnostic, "SOURCE_EMPTY|file=driver.py")

    def test_checker_failure_after_valid_driver(self):
        r = check_sources([("driver.py", GOOD), ("checker.py", "x = )\n")])
        self.assertEqual(r.diagnostic, "SOURCE_SYNTAX_REJECT|file=checker.py|line=1|column=5")

    def test_both_valid(self):
        r = check_sources([("driver.py", GOOD), ("checker.py", GOOD)])
        self.assertEqual(sorted(r), ["checker.py", "driver.py"])

    def test_wrong_order_is_a_caller_error(self):
        with self.assertRaises(ValueError):
            check_sources([("checker.py", GOOD), ("driver.py", GOOD)])


if __name__ == "__main__":
    unittest.main()
