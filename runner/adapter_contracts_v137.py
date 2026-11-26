"""Pack citations for the candidate-only adapters (D-024; v1.3.7 CANDIDATE, not audited).

Data only, in the format of runner/adapter_contracts.py (D-013, D-015, D-017, D-022). Every citation is to the
candidate pack, proposals/v1.3.7/pack; its lines are numbered as in v1.3.6. tests/test_dispatch_shapes_v137.py
checks these against the candidate text with the same functions that check the v1.3.6 contracts.
"""
from __future__ import annotations

from adapter_contracts import LITERAL
from adapters_v137 import CHANGE_CLASSES

_CC_SENTENCE = {
    CHANGE_CLASSES[0]: "is the evaluator revision of §7b path (b)",
    CHANGE_CLASSES[1]: "is a shared-item revision",
    CHANGE_CLASSES[2]: "is a study reset",
    CHANGE_CLASSES[3]: "is a design-specific revision while membership, estimand and weights remain unchanged",
    CHANGE_CLASSES[4]: "is the halt-signature domain check",
}

CONTRACTS = {
    "adapt_change_class": {
        "inputs": {"change_class": ("02", 176, "The change classes are closed and have these cases:")},
        "values": {cc: ("02", 176, f"`{cc}` {words}") for cc, words in _CC_SENTENCE.items()},
        "outcome": [("02", 175, "Error classes of change-class control expectations are stated by rule, not by fixture"),
                    ("02", 176, "Closed scope tokens:"),
                    ("02", 185, "(rule token `stable_error_class_rule` = `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`)"),
                    ("36", 176, "Any other expected object is a control-vector expectation")]},
    "adapt_parser_unit_vector": {
        "inputs": {"source_file": ("36", 27, "`source_file` is `driver.py` or `checker.py`."),
                   "syntax_error": ("36", 27, "`syntax_error` has the key `lineno`, a positive integer, and may have the "
                                              "key `offset`, an integer or null.")},
        "values": {"driver.py": ("36", 27, "`source_file` is `driver.py` or `checker.py`."),
                   "checker.py": ("36", 27, "`source_file` is `driver.py` or `checker.py`.")},
        "outcome": [("36", 27, "Its result has stage `SOURCE_AST`, error class `SOURCE_SYNTAX_REJECT`, the diagnostic "
                               "given by the rule, and disposition `CONTROL_EXPECTATION`."),
                    ("02", 127, "If `offset` is absent, null or less than 1, emit `column=1`")]},
    "adapt_legal_input": {
        "inputs": {"driver_return": ("30", 83, "A return value is either the exact string `COMPLETE` or a dictionary"),
                   "input_port_widths": ("30", 83, "`input_port_widths` (each input port name mapped to its width)"),
                   "sampled_outputs": ("30", 83, "`sampled_outputs` (the outputs sampled in the same row)"),
                   "legal_input_predicate": ("30", 83, "`legal_input_predicate` (an object with `language` = `python3.11`, "
                                                       "`function`, the function's name, and `source`, its Python source)")},
        "values": {"python3.11": ("30", 83, "an object with `language` = `python3.11`")},
        "outcome": [("30", 83, "Checks (a) to (e) run in that order and the first failure is reported."),
                    ("30", 83, "Any other outcome, including an exception, is an evaluator failure and is never an "
                               "artifact verdict."),
                    ("02", 152, "Driver return value/vector is invalid")]},
}

VALUE_SUPPORT = {
    "adapt_change_class": {cc: (LITERAL, f"`{cc}`") for cc in CHANGE_CLASSES},
    "adapt_parser_unit_vector": {"driver.py": (LITERAL, "`driver.py`"), "checker.py": (LITERAL, "`checker.py`")},
    "adapt_legal_input": {"python3.11": (LITERAL, "`python3.11`")},
}

DOMAINS = {
    "adapt_change_class": {"change_class": {
        "lines": [("02", 176)],
        "terms": ["The change classes are closed and have these cases", *(f"`{cc}`" for cc in CHANGE_CLASSES)]}},
    "adapt_parser_unit_vector": {
        "source_file": {"lines": [("36", 27)], "terms": ["`source_file` is `driver.py` or `checker.py`"]},
        "syntax_error": {"lines": [("36", 27)], "terms": ["`syntax_error` has the key `lineno`, a positive integer",
                                                          "may have the key `offset`, an integer or null"]}},
    "adapt_legal_input": {
        "driver_return": {"lines": [("30", 83)], "terms": ["exact string `COMPLETE` or a dictionary",
                                                           "each value is a string"]},
        "input_port_widths": {"lines": [("30", 83)], "terms": ["each input port name mapped to its width",
                                                               "the value length equals the port width"]},
        "sampled_outputs": {"lines": [("30", 83)], "terms": ["each mapping a port name to its bit string"]},
        "legal_input_predicate": {"lines": [("30", 83)], "terms": [
            "one Python 3.11 function of two dictionaries", "`language` = `python3.11`",
            "returns the exact Boolean `True` for a legal vector and `False` otherwise"]}},
}
