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


# --- D-025 Phase B: C11-C16 -----------------------------------------------------------------------------------------
import hashlib  # noqa: E402
import json  # noqa: E402

import adapter_vectors as v136  # noqa: E402

SIGNATURE = BLOCKED + "outside the Protocol L185 domains"
ABORT = "DESIGN_ABORTED_NO_SLOTS_SCORED"
NON_NORMATIVE = rec("CONTROL_EXPECTATION", "FEEDBACK_SERIALIZER", "FEEDBACK_SERIALIZER_REJECT",
                    "FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC")


def repeated(inp):
    same = inp["first_halt_signature"] == inp["second_halt_signature"]
    reason = "EVALUATOR_FAILURE_REPRODUCED" if same else "SECOND_HALT_AFTER_RECOVERY"
    return rec(ABORT, "DESIGN_HALT", "DESIGN_HALT_REPEATED", f"DESIGN_HALT_REPEATED|reason={reason}")


def _from_v136(pairs):
    """The v1.3.6 recurrence pairs, with the edge now giving the candidate record instead of PD-26."""
    out = []
    for term, prop, edge, _, outside, outside_exp in pairs:
        out.append((term, prop, edge, repeated(edge), outside, SIGNATURE if "PD-01" in outside_exp else OUTSIDE))
    return out


T_SCOPE = "TRUNCATION_PRIMITIVE_ONLY_GRAMMAR_BYPASSED"
J_SCOPE = "JSON_ESCAPING_PRIMITIVE_ONLY_GRAMMAR_BYPASSED"


def trunc(raw, **over):
    base = {"raw_diagnostic": raw, "raw_diagnostic_utf8_bytes": len(raw.encode("utf-8")), "byte_cap": 2048,
            "marker": "...[TRUNCATED]", "truncate_on_utf8_boundary": True, "truncate_before_json_escape": True,
            "test_scope": T_SCOPE}
    base.update(over)
    return base


def trunc_rec(contains, n):
    return {"disposition": "CONTROL_EXPECTATION", "stage_id": "FEEDBACK_SERIALIZER", "error_class": "TRUNCATION",
            "contains_marker": contains, "valid_utf8": True, "output_diagnostic_bytes": n, "marker_utf8_bytes": 14}


FB = {"stage_id": "DRIVER_VECTOR", "error_class": "DRIVER_VECTOR_INVALID", "diagnostic": "x"}


def js(obj=None, **over):
    base = {"feedback_object": dict(obj or FB), "encoding": "UTF-8", "ensure_ascii": False, "indent": 2,
            "line_endings": "LF", "terminal_newline": True, "grammar_exempt_for_primitive_test": True,
            "test_scope": J_SCOPE}
    base.update(over)
    return base


def js_rec(obj):
    # An independent statement of L168 step (3): json.dumps with the stated options, key order stage_id, error_class,
    # diagnostic, one final LF.
    text = json.dumps({k: obj[k] for k in ("stage_id", "error_class", "diagnostic")}, ensure_ascii=False, indent=2) + "\n"
    data = text.encode("utf-8")
    return {"disposition": "CONTROL_EXPECTATION", "stage_id": "FEEDBACK_SERIALIZER", "error_class": "JSON_SERIALIZATION",
            "diagnostic_utf8": text, "diagnostic_sha256": hashlib.sha256(data).hexdigest(), "diagnostic_bytes": len(data)}


TI = {"kind": "trace_integrity", "reason": "REPLAY_HASH_MISMATCH"}


def life(event=None, **over):
    base = {"lifecycle": "MID_RUN", "event": dict(event or TI),
            "slots": {"scheduled": 6, "previously_evaluated": 2, "triggering_slot": 3, "remaining": 3},
            "evaluator_repair_attempt": 1}
    base.update(over)
    return base


HALT_TI = rec("DESIGN_HALT_NO_SLOT_SCORED", "DESIGN_HALT", "TRACE_INTEGRITY_FAILURE",
              "TRACE_INTEGRITY_FAILURE|reason=REPLAY_HASH_MISMATCH")
HALT_SIM = rec("DESIGN_HALT_NO_SLOT_SCORED", "DESIGN_HALT", "EVALUATOR_INFRASTRUCTURE_FAILURE",
               "SIMULATOR_ERROR|target=rtl|class=OSError")

VECTORS.update({
    "adapt_halt_recurrence_v137": [
        (v136.halt(v136.sig(), v136.sig()), repeated(v136.halt(v136.sig(), v136.sig()))),
        (v136.halt(v136.sig(), v136.sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="OSError")),
         repeated(v136.halt(v136.sig(), v136.sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="OSError")))),
        (v136.halt(v136.sig(comp="simulator"), v136.sig()), SIGNATURE),
        (dict(v136.halt(v136.sig(), v136.sig()), recovery_cycles_used=2), OUTSIDE),
    ],
    "adapt_serializer_grammar": [
        ({"diagnostic": "COMPILE_ERROR|file=checker.py|line=9"}, PASSED),
        ({"diagnostic": "COMPILE_ERROR|file=checker.py|line=9", "allowed_diagnostics": ["SOURCE_EMPTY|file=driver.py"]},
         NON_NORMATIVE),
        ({"diagnostic": "COMPILE_ERROR|file=checker.py|line=9",
          "allowed_diagnostics": ["COMPILE_ERROR|file=checker.py|line=9"]}, PASSED),
        ({"diagnostic": "SOURCE_EMPTY|file=driver.py /home/u"}, NON_NORMATIVE),
        ({"diagnostic": 7}, OUTSIDE),
    ],
    "adapt_truncation_primitive": [
        (trunc("abc"), trunc_rec(False, 3)),
        (trunc("x" * 2048), trunc_rec(False, 2048)),
        (trunc("x" * 2049), trunc_rec(True, 2048)),
        (trunc("é" * 1100), trunc_rec(True, 2048)),
        (trunc("abc", byte_cap=4096), OUTSIDE),
    ],
    "adapt_json_primitive": [
        (js(), js_rec(FB)),
        (js({"stage_id": "CHECKER_NULL", "error_class": "CHECKER_TIMEOUT", "diagnostic": "tab\tquote\" é"}),
         js_rec({"stage_id": "CHECKER_NULL", "error_class": "CHECKER_TIMEOUT", "diagnostic": "tab\tquote\" é"})),
        (js({"diagnostic": "x", "error_class": "E", "stage_id": "S"}),
         js_rec({"stage_id": "S", "error_class": "E", "diagnostic": "x"})),
        (js({"stage_id": "S", "error_class": "E"}), OUTSIDE),
    ],
    "adapt_lifecycle_halt_event": [
        (life(), HALT_TI),
        (life({"kind": "simulator_error", "target": "rtl", "exception_class": "OSError"}), HALT_SIM),
        (life({"kind": "driver_watchdog"}), OUTSIDE),
        (life(evaluator_repair_attempt=2), OUTSIDE),
    ],
    "adapt_design_preflight": [
        ({"design_preflight": {"rtl_null_masked_divergence": False}}, PASSED),
        ({"design_preflight": {"rtl_null_masked_divergence": 2}}, OUTSIDE),  # not 1: 1 == True in Python
        ({"design_preflight": {}}, OUTSIDE),
    ],
})

OUT_OF_DOMAIN.update({
    "adapt_halt_recurrence_v137": dict(v136.OUT_OF_DOMAIN["adapt_halt_recurrence"]),
    "adapt_serializer_grammar": {"diagnostic": {"diagnostic": None},
                                 "allowed_diagnostics": {"diagnostic": "x", "allowed_diagnostics": ["a", "a"]}},
    "adapt_truncation_primitive": {
        "raw_diagnostic": trunc("abc", raw_diagnostic=5), "raw_diagnostic_utf8_bytes": trunc("abc", raw_diagnostic_utf8_bytes=4),
        "byte_cap": trunc("abc", byte_cap="2048"), "marker": trunc("abc", marker="...[CUT]"),
        "truncate_on_utf8_boundary": trunc("abc", truncate_on_utf8_boundary=1),
        "truncate_before_json_escape": trunc("abc", truncate_before_json_escape=False),
        "test_scope": trunc("abc", test_scope=J_SCOPE)},
    "adapt_json_primitive": {
        "feedback_object": js({"stage_id": "S", "error_class": "E", "diagnostic": 3}), "encoding": js(encoding="utf-8"),
        "ensure_ascii": js(ensure_ascii=True), "indent": js(indent=True), "line_endings": js(line_endings="CRLF"),
        "terminal_newline": js(terminal_newline=False), "grammar_exempt_for_primitive_test": js(grammar_exempt_for_primitive_test=False),
        "test_scope": js(test_scope=T_SCOPE)},
    "adapt_lifecycle_halt_event": {
        "lifecycle": life(lifecycle="BASELINE"), "event": life({"kind": "simulator_error", "target": "both", "exception_class": "E"}),
        "slots": life(slots={"scheduled": 6, "previously_evaluated": 2, "triggering_slot": 7, "remaining": 3}),
        "evaluator_repair_attempt": life(evaluator_repair_attempt=0)},
    "adapt_design_preflight": {"design_preflight": {"design_preflight": {"rtl_null_masked_divergence": True, "note": ""}}},
})


def pair(term, prop, base, edge, edge_exp, outside, outside_exp):
    return (term, prop, {**base, prop: edge}, edge_exp, {**base, prop: outside}, outside_exp)


_SLOTS = {"scheduled": 6, "previously_evaluated": 2, "triggering_slot": 3, "remaining": 3}
BOUNDARIES.update({
    "adapt_halt_recurrence_v137": _from_v136(v136.BOUNDARIES["adapt_halt_recurrence"]),
    "adapt_serializer_grammar": [
        pair("`diagnostic` (a string)", "diagnostic", {}, "x", NON_NORMATIVE, "\ud800", OUTSIDE),
        pair("duplicate-free list of diagnostics the stage map emitted", "allowed_diagnostics", {"diagnostic": "a"},
             ["a", "b"], NON_NORMATIVE, ["a", "a"], OUTSIDE),
    ],
    "adapt_truncation_primitive": [
        pair("`raw_diagnostic` (a string)", "raw_diagnostic", trunc("ab"), "ab", trunc_rec(False, 2), "a\ud800", OUTSIDE),
        pair("(its UTF-8 byte length)", "raw_diagnostic_utf8_bytes", trunc("ab"), 2, trunc_rec(False, 2), 3, OUTSIDE),
        pair("`byte_cap` = `2048`", "byte_cap", trunc("ab"), 2048, trunc_rec(False, 2), 2047, OUTSIDE),
        pair("`marker` = `...[TRUNCATED]`", "marker", trunc("ab"), "...[TRUNCATED]", trunc_rec(False, 2), "...[TRUNCATED] ", OUTSIDE),
        pair("`truncate_on_utf8_boundary` = `true`", "truncate_on_utf8_boundary", trunc("ab"), True, trunc_rec(False, 2), False, OUTSIDE),
        pair("`truncate_before_json_escape` = `true`", "truncate_before_json_escape", trunc("ab"), True, trunc_rec(False, 2), False, OUTSIDE),
        pair(f"`test_scope` = `{T_SCOPE}`", "test_scope", trunc("ab"), T_SCOPE, trunc_rec(False, 2), T_SCOPE + "S", OUTSIDE),
    ],
    "adapt_json_primitive": [
        pair("exactly the string keys `stage_id`, `error_class`, `diagnostic`", "feedback_object", js(), FB, js_rec(FB),
             {**FB, "diagnostic": 1}, OUTSIDE),
        pair("`encoding` = `UTF-8`", "encoding", js(), "UTF-8", js_rec(FB), "UTF-16", OUTSIDE),
        pair("`ensure_ascii` = `false`", "ensure_ascii", js(), False, js_rec(FB), True, OUTSIDE),
        pair("`indent` = `2`", "indent", js(), 2, js_rec(FB), 3, OUTSIDE),
        pair("`line_endings` = `LF`", "line_endings", js(), "LF", js_rec(FB), "CR", OUTSIDE),
        pair("`terminal_newline` = `true`", "terminal_newline", js(), True, js_rec(FB), False, OUTSIDE),
        pair("`grammar_exempt_for_primitive_test` = `true`", "grammar_exempt_for_primitive_test", js(), True, js_rec(FB),
             False, OUTSIDE),
        pair(f"`test_scope` = `{J_SCOPE}`", "test_scope", js(), J_SCOPE, js_rec(FB), J_SCOPE + "S", OUTSIDE),
    ],
    "adapt_lifecycle_halt_event": [
        pair("`lifecycle` = `MID_RUN`", "lifecycle", life(), "MID_RUN", HALT_TI, "MID_RUNS", OUTSIDE),
        pair("or `trace_integrity` (`reason`)", "event", life(), TI, HALT_TI, {**TI, "kind": "trace_integrityx"}, OUTSIDE),
        pair("`previously_evaluated` + 1 + `remaining` = `scheduled`", "slots", life(), _SLOTS, HALT_TI,
             {**_SLOTS, "remaining": 4}, OUTSIDE),
        pair("`triggering_slot` (1 to `scheduled`)", "slots", life(), {**_SLOTS, "triggering_slot": 6}, HALT_TI,
             {**_SLOTS, "triggering_slot": 7}, OUTSIDE),
        pair("`evaluator_repair_attempt` = `1`", "evaluator_repair_attempt", life(), 1, HALT_TI, 2, OUTSIDE),
    ],
    "adapt_design_preflight": [
        pair("an object with exactly the Boolean `rtl_null_masked_divergence`", "design_preflight", {},
             {"rtl_null_masked_divergence": False}, PASSED, {"rtl_null_masked_divergence": "false"}, OUTSIDE),
    ],
})
