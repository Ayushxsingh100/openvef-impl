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

# --- D-025 Phase B: C11-C16 -----------------------------------------------------------------------------------------
from adapter_contracts import CONTRACTS as _V136, DOMAINS as _V136_DOMAINS, VALUE_SUPPORT as _V136_SUPPORT  # noqa: E402
from adapters_v137 import JSON_SCOPE, TRUNCATION_SCOPE  # noqa: E402

_L195 = ("36", 195)
_L196, _L197, _L198, _L199 = ("36", 196), ("36", 197), ("36", 198), ("36", 199)


def _q(at, text):
    return (*at, text)


CONTRACTS.update({
    "adapt_halt_recurrence_v137": {
        "inputs": dict(_V136["adapt_halt_recurrence"]["inputs"]),
        "values": dict(_V136["adapt_halt_recurrence"]["values"]),
        "outcome": [("02", 185, "Both terminations are recorded at stage `DESIGN_HALT` with error class `DESIGN_HALT_REPEATED`."),
                    ("02", 185, "mark every scheduled slot in the affected scope `DESIGN_ABORTED_NO_SLOTS_SCORED`"),
                    ("02", 185, "A supplied halt signature with any component outside these domains is an evaluator input "
                                "error; it is never compared for recurrence.")]},
    "adapt_serializer_grammar": {
        "inputs": {"diagnostic": _q(_L195, "`diagnostic` (a string)"),
                   "allowed_diagnostics": _q(_L195, "`allowed_diagnostics` (the duplicate-free list of diagnostics the "
                                                    "stage map emitted)")},
        "values": {},
        "outcome": [("02", 168, "When the set of diagnostics the stage map emitted is given, a diagnostic that passes the "
                                "grammar but is not in that set is also rejected at step (1)"),
                    ("02", 174, "is recorded at stage `FEEDBACK_SERIALIZER` with error class `FEEDBACK_SERIALIZER_REJECT` "
                                "and disposition `CONTROL_EXPECTATION`.")]},
    "adapt_truncation_primitive": {
        "inputs": {"raw_diagnostic": _q(_L196, "`raw_diagnostic` (a string)"),
                   "raw_diagnostic_utf8_bytes": _q(_L196, "`raw_diagnostic_utf8_bytes` (its UTF-8 byte length)"),
                   "byte_cap": _q(_L196, "`byte_cap` = `2048`"),
                   "marker": _q(_L196, "`marker` = `...[TRUNCATED]`"),
                   "truncate_on_utf8_boundary": _q(_L196, "`truncate_on_utf8_boundary` = `true`"),
                   "truncate_before_json_escape": _q(_L196, "`truncate_before_json_escape` = `true`"),
                   "test_scope": _q(_L196, f"`test_scope` = `{TRUNCATION_SCOPE}`")},
        "values": {TRUNCATION_SCOPE: _q(_L196, f"`test_scope` = `{TRUNCATION_SCOPE}`")},
        "outcome": [("02", 168, "A truncation-primitive vector applies step (2) alone to its input string and reports"),
                    ("02", 174, "A truncation-primitive vector uses error class `TRUNCATION`")]},
    "adapt_json_primitive": {
        "inputs": {"feedback_object": _q(_L197, "`feedback_object` (exactly the string keys `stage_id`, `error_class`, "
                                                "`diagnostic`)"),
                   "encoding": _q(_L197, "`encoding` = `UTF-8`"), "ensure_ascii": _q(_L197, "`ensure_ascii` = `false`"),
                   "indent": _q(_L197, "`indent` = `2`"), "line_endings": _q(_L197, "`line_endings` = `LF`"),
                   "terminal_newline": _q(_L197, "`terminal_newline` = `true`"),
                   "grammar_exempt_for_primitive_test": _q(_L197, "`grammar_exempt_for_primitive_test` = `true`"),
                   "test_scope": _q(_L197, f"`test_scope` = `{JSON_SCOPE}`")},
        "values": {"UTF-8": _q(_L197, "`encoding` = `UTF-8`"), "LF": _q(_L197, "`line_endings` = `LF`"),
                   JSON_SCOPE: _q(_L197, f"`test_scope` = `{JSON_SCOPE}`")},
        "outcome": [("02", 168, "A JSON-escaping-primitive vector applies step (3) alone to its three-key object and reports"),
                    ("02", 174, "a JSON-escaping-primitive vector uses error class `JSON_SERIALIZATION`")]},
    "adapt_lifecycle_halt_event": {
        "inputs": {"lifecycle": _q(_L198, "`lifecycle` = `MID_RUN` (the halt occurs after slots have begun, §7b)"),
                   "event": _q(_L198, "one stage-map event of kind `simulator_error`"),
                   "slots": _q(_L198, "`previously_evaluated` + 1 + `remaining` = `scheduled`"),
                   "evaluator_repair_attempt": _q(_L198, "`evaluator_repair_attempt` = `1`, the ordinal of the recovery "
                                                         "cycle this halt opens")},
        "values": {"MID_RUN": _q(_L198, "`lifecycle` = `MID_RUN`"),
                   "simulator_error": _q(_L198, "one stage-map event of kind `simulator_error`"),
                   "trace_integrity": _q(_L198, "or `trace_integrity` (`reason`)")},
        "outcome": [_q(_L198, "The result is the event's stage-map row with disposition `DESIGN_HALT_NO_SLOT_SCORED`"),
                    ("02", 154, "| Simulator error on RTL or null run | `DESIGN_HALT` | `EVALUATOR_INFRASTRUCTURE_FAILURE` |"),
                    ("02", 155, "| Harness trace-integrity fault | `DESIGN_HALT` | `TRACE_INTEGRITY_FAILURE` |")]},
    "adapt_design_preflight": {
        "inputs": {"design_preflight": _q(_L199, "`design_preflight`, an object with exactly the Boolean "
                                                 "`rtl_null_masked_divergence`")},
        "values": {},
        "outcome": [("02", 179, "It is recorded at stage `DESIGN_HALT` with error class `RTL_NULL_CONTROL_FAILURE`"),
                    _q(_L199, "`true` is the §7a baseline mismatch record")]},
})

VALUE_SUPPORT.update({
    "adapt_halt_recurrence_v137": dict(_V136_SUPPORT["adapt_halt_recurrence"]),
    "adapt_serializer_grammar": {},
    "adapt_truncation_primitive": {TRUNCATION_SCOPE: (LITERAL, f"`{TRUNCATION_SCOPE}`")},
    "adapt_json_primitive": {"UTF-8": (LITERAL, "`UTF-8`"), "LF": (LITERAL, "`LF`"), JSON_SCOPE: (LITERAL, f"`{JSON_SCOPE}`")},
    "adapt_lifecycle_halt_event": {"MID_RUN": (LITERAL, "`MID_RUN`"), "simulator_error": (LITERAL, "`simulator_error`"),
                                   "trace_integrity": (LITERAL, "`trace_integrity`")},
    "adapt_design_preflight": {},
})


def _d(at, *terms):
    return {"lines": [at], "terms": list(terms)}


DOMAINS.update({
    "adapt_halt_recurrence_v137": {k: dict(v) for k, v in _V136_DOMAINS["adapt_halt_recurrence"].items()},
    "adapt_serializer_grammar": {"diagnostic": _d(_L195, "`diagnostic` (a string)"),
                                 "allowed_diagnostics": _d(_L195, "duplicate-free list of diagnostics the stage map emitted")},
    "adapt_truncation_primitive": {
        "raw_diagnostic": _d(_L196, "`raw_diagnostic` (a string)"),
        "raw_diagnostic_utf8_bytes": _d(_L196, "(its UTF-8 byte length)"),
        "byte_cap": _d(_L196, "`byte_cap` = `2048`"), "marker": _d(_L196, "`marker` = `...[TRUNCATED]`"),
        "truncate_on_utf8_boundary": _d(_L196, "`truncate_on_utf8_boundary` = `true`"),
        "truncate_before_json_escape": _d(_L196, "`truncate_before_json_escape` = `true`"),
        "test_scope": _d(_L196, f"`test_scope` = `{TRUNCATION_SCOPE}`")},
    "adapt_json_primitive": {
        "feedback_object": _d(_L197, "exactly the string keys `stage_id`, `error_class`, `diagnostic`"),
        "encoding": _d(_L197, "`encoding` = `UTF-8`"), "ensure_ascii": _d(_L197, "`ensure_ascii` = `false`"),
        "indent": _d(_L197, "`indent` = `2`"), "line_endings": _d(_L197, "`line_endings` = `LF`"),
        "terminal_newline": _d(_L197, "`terminal_newline` = `true`"),
        "grammar_exempt_for_primitive_test": _d(_L197, "`grammar_exempt_for_primitive_test` = `true`"),
        "test_scope": _d(_L197, f"`test_scope` = `{JSON_SCOPE}`")},
    "adapt_lifecycle_halt_event": {
        "lifecycle": _d(_L198, "`lifecycle` = `MID_RUN`"),
        "event": _d(_L198, "one stage-map event of kind `simulator_error`", "or `trace_integrity` (`reason`)"),
        "slots": _d(_L198, "`scheduled` (at least 1)", "`triggering_slot` (1 to `scheduled`)",
                    "`previously_evaluated` + 1 + `remaining` = `scheduled`"),
        "evaluator_repair_attempt": _d(_L198, "`evaluator_repair_attempt` = `1`")},
    "adapt_design_preflight": {"design_preflight": _d(_L199, "an object with exactly the Boolean `rtl_null_masked_divergence`")},
})
