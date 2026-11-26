"""Synthetic, non-fixture inputs for the candidate-only adapters (D-024; D-013 (b), D-017), in the format of
tests/adapter_vectors.py. No input is copied from a fixture descriptor; the test checks this. Expected records of
the change-class adapter are computed by the ledger, never copied from a descriptor.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef.ledger import lifecycle_expectation_candidate  # noqa: E402

BLOCKED = "BLOCKED:"
OUTSIDE = BLOCKED + "outside its cited domain"
PASSED = BLOCKED + "check passed"
EVALUATOR = BLOCKED + "evaluator failure"


def rec(disposition, stage_id, error_class, diagnostic):
    return {"disposition": disposition, "stage_id": stage_id, "error_class": error_class, "diagnostic": diagnostic}


def invalid(reason):
    return rec("REPAIR", "DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", f"DRIVER_VECTOR_INVALID|reason={reason}")


def syntax(file, line, column):
    return rec("CONTROL_EXPECTATION", "SOURCE_AST", "SOURCE_SYNTAX_REJECT",
               f"SOURCE_SYNTAX_REJECT|file={file}|line={line}|column={column}")


def unit(file="driver.py", **error):
    return {"source_file": file, "syntax_error": error}


# A toy design (not the FIFO): input ports `a` (1 bit) and `b` (2 bits); `a` = 1 is illegal while `busy` = 1.
TOY_SOURCE = "def ok(vector, sampled):\n    return not (sampled['busy'] == '1' and vector['a'] == '1')\n"
TOY = {"language": "python3.11", "function": "ok", "source": TOY_SOURCE}


def vec(driver_return, widths=None, sampled=None, predicate=None):
    return {"driver_return": driver_return, "input_port_widths": widths or {"a": 1, "b": 2},
            "sampled_outputs": sampled or {"busy": "1"}, "legal_input_predicate": predicate or TOY}


def pred(source, function="ok", language="python3.11"):
    return {"language": language, "function": function, "source": source}


HALT_ENUM = "HALT_SIGNATURE_COMPONENT_ENUMERATION"

VECTORS = {
    "adapt_change_class": [
        ({"change_class": "OPERATIONAL_RECOVERY"}, OUTSIDE),           # a §7b path, not a change class
        ({"change_class": HALT_ENUM.lower()}, OUTSIDE),
        ({"change_class": 5}, OUTSIDE),
    ],
    "adapt_parser_unit_vector": [
        (unit("checker.py", lineno=7, offset=3), syntax("checker.py", 7, 3)),
        (unit(lineno=2), syntax("driver.py", 2, 1)),                    # offset absent
        (unit(lineno=1, offset=0), syntax("driver.py", 1, 1)),          # less than 1
        (unit(lineno=9, offset=-4), syntax("driver.py", 9, 1)),
        (unit("setup.py", lineno=1), OUTSIDE),
    ],
    "adapt_legal_input": [
        (vec({"a": "1", "b": "00"}), invalid("ILLEGAL_PROTOCOL_STATE")),
        (vec({"a": "0", "b": "01"}), PASSED),
        (vec({"a": "1", "b": "00"}, sampled={"busy": "0"}), PASSED),
        (vec({"a": "0"}), invalid("MISSING_KEYS")),
        (vec({"a": "0", "b": "01", "c": "1"}), invalid("EXTRA_KEYS")),
        (vec({"a": "0", "b": "0"}), invalid("WRONG_WIDTH")),
        (vec({"a": "0", "b": "0z"}), invalid("ILLEGAL_SYMBOL")),
        (vec("COMPLETE"), PASSED),
        (vec({"a": "0", "b": "01"}, predicate=pred("def ok(vector, sampled):\n    return 1\n")), EVALUATOR),
        (vec({"a": "0", "b": "01"}, predicate=pred("def ok(vector, sampled):\n    return sampled['idle'] == '1'\n")),
         EVALUATOR),
        (vec({"a": "0", "b": "01"}, predicate=pred(TOY_SOURCE, function="missing")), EVALUATOR),
    ],
}

OUT_OF_DOMAIN = {
    "adapt_change_class": {"change_class": {"change_class": None}},
    "adapt_parser_unit_vector": {"source_file": unit(None, lineno=3),
                                 "syntax_error": unit(lineno=3, column=1)},
    "adapt_legal_input": {"driver_return": vec([]),
                          "input_port_widths": vec({"a": "0", "b": "01"}, widths={"a": 1, "b": "2"}),
                          "sampled_outputs": vec({"a": "0", "b": "01"}, sampled={"busy": 1}),
                          "legal_input_predicate": vec({"a": "0", "b": "01"}, predicate={"source": TOY_SOURCE})},
}
JUDGED_BY_RULE = {("adapt_legal_input", "driver_return")}  # a non-dictionary is RETURN_TYPE (30 L83)

# The change-class domain is a closed list of five labels, and every label is a fixture input, so an in-domain edge
# cannot avoid being one. The test allows exactly this, and checks that each value of the list is in a fixture.
EDGE_MAY_BE_A_FIXTURE_INPUT = {("adapt_change_class", "change_class")}

BOUNDARIES = {
    "adapt_change_class": [
        ("`HALT_SIGNATURE_COMPONENT_ENUMERATION`", "change_class", {"change_class": HALT_ENUM},
         lifecycle_expectation_candidate(HALT_ENUM)[0], {"change_class": HALT_ENUM + "S"}, OUTSIDE),
        ("The change classes are closed and have these cases", "change_class",
         {"change_class": "DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED"},
         lifecycle_expectation_candidate("DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED")[0],
         {"change_class": "DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEMS_CHANGED"}, OUTSIDE),
    ],
    "adapt_parser_unit_vector": [
        ("`source_file` is `driver.py` or `checker.py`", "source_file", unit("checker.py", lineno=5, offset=2),
         syntax("checker.py", 5, 2), unit("checker.pyc", lineno=5, offset=2), OUTSIDE),
        ("`syntax_error` has the key `lineno`, a positive integer", "syntax_error", unit(lineno=1, offset=6),
         syntax("driver.py", 1, 6), unit(lineno=0, offset=6), OUTSIDE),
        ("may have the key `offset`, an integer or null", "syntax_error", unit(lineno=8, offset=None),
         syntax("driver.py", 8, 1), unit(lineno=8, offset="1"), OUTSIDE),
    ],
    "adapt_legal_input": [
        ("each value is a string", "driver_return", vec({"a": "0", "b": "11"}), PASSED,
         vec({"a": 0, "b": "11"}), invalid("NON_STRING_VALUE")),
        ("each input port name mapped to its width", "input_port_widths", vec({"a": "0", "b": "11"}, widths={"a": 1, "b": 2}),
         PASSED, vec({"a": "0", "b": "11"}, widths={"a": 1, "b": 0}), OUTSIDE),
        ("each mapping a port name to its bit string", "sampled_outputs", vec({"a": "1", "b": "11"}, sampled={"busy": "0"}),
         PASSED, vec({"a": "1", "b": "11"}, sampled={"busy": "2"}), OUTSIDE),
        ("`language` = `python3.11`", "legal_input_predicate", vec({"a": "0", "b": "10"}, predicate=pred(TOY_SOURCE)),
         PASSED, vec({"a": "0", "b": "10"}, predicate=pred(TOY_SOURCE, language="python3.12")), OUTSIDE),
    ],
}
