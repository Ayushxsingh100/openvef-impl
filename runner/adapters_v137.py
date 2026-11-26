"""Runner adapters that exist only under `--pack v1.3.7-candidate` (D-024; v1.3.7 CANDIDATE, not audited).

Each input contract is cited to the candidate pack (proposals/v1.3.7/pack, corrections C2, C5, C9-C16), so these rows
are never in the v1.3.6 table: v1.3.6 has no text for these shapes (PD-02, PD-04, PD-06, PD-07, D-013).
Contracts: runner/adapter_contracts_v137.py. Vectors and boundary pairs: tests/adapter_vectors_v137.py, checked by
tests/test_dispatch_shapes_v137.py under the same rules as the v1.3.6 adapters (D-013, D-017).

A refusal raises NotDetermined, which the runner reports as NOT_IMPLEMENTED with the reason, exactly as its own
Blocked. This module does not import the runner.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable, Mapping

from openvef import serializer
from openvef.envelope import Failure
from openvef.ledger import (DESIGN_IDS, HaltSignature, SignatureDomainError, halt_after_recovery,
                            lifecycle_expectation_candidate)
from openvef.source_ast import syntax_reject
from openvef.stage_map import HALT, EventError, NotDetermined, first_event, validate_vector

# D-025 item 1: the C5 predicate runs only after the runner has verified every file of the candidate pack against its
# pinned SHA256SUMS. Set by runner/run_f18.py main(); nothing else sets it.
PACK_VERIFIED = False

# Candidate 02 L176 (C2): "The change classes are closed and have these cases: ..."
CHANGE_CLASSES = ("FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED",
                  "SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED",
                  "DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START",
                  "DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED",
                  "HALT_SIGNATURE_COMPONENT_ENUMERATION")
# Candidate 36 L27 (C9): "`source_file` is `driver.py` or `checker.py`".
SOURCE_FILES = ("driver.py", "checker.py")
# Candidate 30 L83 (C5): "`legal_input_predicate` (an object with `language` = `python3.11`, `function`, ..., `source`".
PREDICATE_LANGUAGE = "python3.11"
PREDICATE_KEYS = {"language", "function", "source"}


def _in_domain(ok: bool, name: str) -> None:
    if not ok:
        raise NotDetermined(f"{name} outside its cited domain")


def _bits(value: Any) -> bool:
    return isinstance(value, str) and value != "" and set(value) <= {"0", "1"}


def adapt_change_class(desc: dict, validator) -> dict:
    """Candidate 02 L175-L176, L181-L185 (C1-C3): the change-class control expectation, whole (C4)."""
    change_class = desc["input"]["change_class"]
    _in_domain(isinstance(change_class, str) and change_class in CHANGE_CLASSES, "change_class")
    record, missing = lifecycle_expectation_candidate(change_class)
    if missing:
        raise NotDetermined(f"candidate Protocol does not support: {sorted(missing)}")
    return record


def adapt_parser_unit_vector(desc: dict, validator) -> dict:
    """Candidate 36 L27 (C9): the Protocol §3.4 SOURCE_SYNTAX_REJECT column rule (02 L127) at a given position."""
    inp = desc["input"]
    source_file, error = inp["source_file"], inp["syntax_error"]
    _in_domain(isinstance(source_file, str) and source_file in SOURCE_FILES, "source_file")
    _in_domain(isinstance(error, dict) and {"lineno"} <= set(error) <= {"lineno", "offset"}
               and type(error["lineno"]) is int and error["lineno"] >= 1
               and (error.get("offset") is None or type(error.get("offset")) is int), "syntax_error")
    failure = syntax_reject(source_file, error["lineno"], error.get("offset"))
    return {"disposition": "CONTROL_EXPECTATION", "stage_id": failure.stage_id, "error_class": failure.error_class,
            "diagnostic": failure.diagnostic}


def _predicate(spec: Mapping[str, str], sampled: Mapping[str, str]) -> Callable[[Mapping[str, str]], bool]:
    """Candidate 30 L83 (C5): one Python 3.11 function of (vector, sampled) returning exactly True or False; any
    other outcome is an evaluator failure, never an artifact verdict. The source is pack text, verified by the
    fixture index's SHA-256 before loading; it is evaluator material, not artifact code (D-015)."""
    if not PACK_VERIFIED:
        raise NotDetermined("candidate pack SHA256SUMS not verified (D-025); predicate not run")
    namespace: dict = {}
    try:
        exec(compile(spec["source"], "<legal_input_predicate>", "exec", dont_inherit=True), namespace)
        function = namespace[spec["function"]]
    except Exception as exc:
        raise NotDetermined(f"evaluator failure (candidate 30 L83): predicate does not load: {type(exc).__name__}")

    def legal(vector: Mapping[str, str]) -> bool:
        try:
            result = function(dict(vector), dict(sampled))
        except Exception as exc:
            raise NotDetermined(f"evaluator failure (candidate 30 L83): predicate raised {type(exc).__name__}")
        if type(result) is not bool:
            raise NotDetermined("evaluator failure (candidate 30 L83): predicate did not return a Boolean")
        return result
    return legal


def adapt_legal_input(desc: dict, validator) -> Failure:
    """Candidate 30 L83 (C5): checks (a)-(e) in order on a driver vector, with the supplied widths, sampled
    outputs and predicate."""
    inp = desc["input"]
    widths, sampled, spec = inp["input_port_widths"], inp["sampled_outputs"], inp["legal_input_predicate"]
    _in_domain(isinstance(widths, dict) and len(widths) > 0
               and all(isinstance(k, str) and type(w) is int and w >= 1 for k, w in widths.items()),
               "input_port_widths")
    _in_domain(isinstance(sampled, dict) and all(isinstance(k, str) and _bits(v) for k, v in sampled.items()),
               "sampled_outputs")
    _in_domain(isinstance(spec, dict) and set(spec) == PREDICATE_KEYS and spec["language"] == PREDICATE_LANGUAGE
               and isinstance(spec["function"], str) and spec["function"].isidentifier()
               and isinstance(spec["source"], str), "legal_input_predicate")
    failure = validate_vector(inp["driver_return"], widths, widths, _predicate(spec, sampled))
    if failure is None:
        raise NotDetermined("check passed; nothing further to compare")
    return failure


def _utf8(value: Any) -> bool:
    try:
        return isinstance(value, str) and bool(value.encode("utf-8") or True)
    except UnicodeEncodeError:
        return False


def adapt_halt_recurrence_v137(desc: dict, validator) -> Failure:
    """Candidate 02 L185 (C10, C11): the v1.3.6 recurrence domains, then the termination record that v1.3.6 could not
    give (PD-26). Replaces the v1.3.6 row in the candidate table only."""
    inp = desc["input"]
    _in_domain(inp["design_id"] in DESIGN_IDS, "design_id")
    _in_domain(type(inp["recovery_cycles_used"]) is int and inp["recovery_cycles_used"] == 1, "recovery_cycles_used")
    _in_domain(type(inp["scheduled_slots"]) is int and inp["scheduled_slots"] >= 1, "scheduled_slots")
    _in_domain(all(isinstance(inp[k], dict) for k in ("first_halt_signature", "second_halt_signature")), "halt signature")
    try:
        first, second = (HaltSignature.given(inp[k]) for k in ("first_halt_signature", "second_halt_signature"))
    except SignatureDomainError as exc:  # candidate L185: an evaluator input error, never compared
        raise NotDetermined(f"supplied halt signature outside the Protocol L185 domains: {exc}") from exc
    return halt_after_recovery(first, second, inp["recovery_cycles_used"])


_ABSENT = object()


def adapt_serializer_grammar(desc: dict, validator) -> Failure:
    """Candidate 02 L168 step (1) with the emitted set (C12), 02 L174 record (C11); input 36 L195."""
    inp = desc["input"]
    diagnostic, emitted = inp["diagnostic"], inp.get("allowed_diagnostics", _ABSENT)
    _in_domain(_utf8(diagnostic), "diagnostic")
    _in_domain(emitted is _ABSENT or (isinstance(emitted, list) and all(_utf8(d) for d in emitted)
                                      and len(set(emitted)) == len(emitted)), "allowed_diagnostics")
    failure = serializer.check_diagnostic(diagnostic, None if emitted is _ABSENT else emitted)
    if failure is None:
        raise NotDetermined("check passed; nothing further to compare")
    return failure


# Candidate 36 L196, L197 (C13, C14): the test-scope tokens.
TRUNCATION_SCOPE = "TRUNCATION_PRIMITIVE_ONLY_GRAMMAR_BYPASSED"
JSON_SCOPE = "JSON_ESCAPING_PRIMITIVE_ONLY_GRAMMAR_BYPASSED"
FEEDBACK_KEYS = ("stage_id", "error_class", "diagnostic")


def adapt_truncation_primitive(desc: dict, validator) -> dict:
    """Candidate 02 L168 step (2) alone, L174 (C13); input 36 L196. Properties fixed by L168 must equal it."""
    inp = desc["input"]
    raw = inp["raw_diagnostic"]
    _in_domain(_utf8(raw), "raw_diagnostic")
    _in_domain(type(inp["raw_diagnostic_utf8_bytes"]) is int and inp["raw_diagnostic_utf8_bytes"] == len(raw.encode()),
               "raw_diagnostic_utf8_bytes")
    _in_domain(type(inp["byte_cap"]) is int and inp["byte_cap"] == serializer.BYTE_CAP, "byte_cap")
    _in_domain(inp["marker"] == serializer.MARKER, "marker")
    _in_domain(inp["truncate_on_utf8_boundary"] is True, "truncate_on_utf8_boundary")
    _in_domain(inp["truncate_before_json_escape"] is True, "truncate_before_json_escape")
    _in_domain(inp["test_scope"] == TRUNCATION_SCOPE, "test_scope")
    out = serializer.truncate(raw).encode("utf-8")
    try:
        valid = bool(out.decode("utf-8") or True)
    except UnicodeDecodeError:
        valid = False
    marker = serializer.MARKER.encode("utf-8")
    return {"disposition": "CONTROL_EXPECTATION", "stage_id": "FEEDBACK_SERIALIZER", "error_class": "TRUNCATION",
            "contains_marker": out.endswith(marker), "valid_utf8": valid, "output_diagnostic_bytes": len(out),
            "marker_utf8_bytes": len(marker)}


def adapt_json_primitive(desc: dict, validator) -> dict:
    """Candidate 02 L168 step (3) alone, L174 (C13, C14); input 36 L197. Properties fixed by L168 must equal it."""
    inp = desc["input"]
    obj = inp["feedback_object"]
    _in_domain(isinstance(obj, dict) and set(obj) == set(FEEDBACK_KEYS) and all(_utf8(obj[k]) for k in FEEDBACK_KEYS),
               "feedback_object")
    _in_domain(inp["encoding"] == "UTF-8", "encoding")
    _in_domain(inp["ensure_ascii"] is False, "ensure_ascii")
    _in_domain(type(inp["indent"]) is int and inp["indent"] == 2, "indent")
    _in_domain(inp["line_endings"] == "LF", "line_endings")
    _in_domain(inp["terminal_newline"] is True, "terminal_newline")
    _in_domain(inp["grammar_exempt_for_primitive_test"] is True, "grammar_exempt_for_primitive_test")
    _in_domain(inp["test_scope"] == JSON_SCOPE, "test_scope")
    data = serializer._serialize_object(*(obj[k] for k in FEEDBACK_KEYS))
    return {"disposition": "CONTROL_EXPECTATION", "stage_id": "FEEDBACK_SERIALIZER", "error_class": "JSON_SERIALIZATION",
            "diagnostic_utf8": data.decode("utf-8"), "diagnostic_sha256": hashlib.sha256(data).hexdigest(),
            "diagnostic_bytes": len(data)}


# Candidate 36 L198 (C15): "one stage-map event of kind `simulator_error` ... or `trace_integrity`".
HALT_EVENTS = ("simulator_error", "trace_integrity")
SLOT_KEYS = {"scheduled", "previously_evaluated", "triggering_slot", "remaining"}


def adapt_lifecycle_halt_event(desc: dict, validator) -> Failure:
    """Candidate 36 L198 (C15): a first mid-run design halt; the record is the event's stage-map row."""
    inp = desc["input"]
    event, slots = inp["event"], inp["slots"]
    _in_domain(inp["lifecycle"] == "MID_RUN", "lifecycle")
    _in_domain(isinstance(event, dict) and event.get("kind") in HALT_EVENTS, "event")
    _in_domain(isinstance(slots, dict) and set(slots) == SLOT_KEYS and all(type(v) is int and v >= 0 for v in slots.values())
               and slots["scheduled"] >= 1 and 1 <= slots["triggering_slot"] <= slots["scheduled"]
               and slots["previously_evaluated"] + 1 + slots["remaining"] == slots["scheduled"], "slots")
    _in_domain(type(inp["evaluator_repair_attempt"]) is int and inp["evaluator_repair_attempt"] == 1,
               "evaluator_repair_attempt")
    try:
        failure = first_event([event])
    except EventError as exc:
        raise NotDetermined(f"event outside its cited domain: {exc}") from exc
    assert failure.disposition == HALT
    return failure


def adapt_design_preflight(desc: dict, validator) -> Failure:
    """Candidate 02 L179 (C16): the §7a baseline record; input 36 L199."""
    gate = desc["input"]["design_preflight"]
    _in_domain(isinstance(gate, dict) and set(gate) == {"rtl_null_masked_divergence"}
               and type(gate["rtl_null_masked_divergence"]) is bool, "design_preflight")
    if not gate["rtl_null_masked_divergence"]:
        raise NotDetermined("check passed; nothing further to compare")
    return Failure("DESIGN_HALT", "RTL_NULL_CONTROL_FAILURE", "RTL_NULL_CONTROL_FAILURE|reason=MASKED_OUTPUT_DIVERGENCE", HALT)


# v1.3.6 rows whose adapter the candidate replaces (same input shape, outcome the candidate text now gives).
REPLACEMENTS = {"adapt_halt_recurrence": adapt_halt_recurrence_v137}

# (required keys, optional keys, adapter): added to the runner's table for the candidate pack only.
ROWS = (
    ({"change_class"}, set(), adapt_change_class),
    ({"source_file", "syntax_error"}, set(), adapt_parser_unit_vector),
    ({"driver_return", "input_port_widths", "sampled_outputs", "legal_input_predicate"}, set(), adapt_legal_input),
    ({"diagnostic"}, {"allowed_diagnostics"}, adapt_serializer_grammar),
    ({"raw_diagnostic", "raw_diagnostic_utf8_bytes", "byte_cap", "marker", "truncate_on_utf8_boundary",
      "truncate_before_json_escape", "test_scope"}, set(), adapt_truncation_primitive),
    ({"feedback_object", "encoding", "ensure_ascii", "indent", "line_endings", "terminal_newline",
      "grammar_exempt_for_primitive_test", "test_scope"}, set(), adapt_json_primitive),
    ({"lifecycle", "event", "slots", "evaluator_repair_attempt"}, set(), adapt_lifecycle_halt_event),
    ({"design_preflight"}, set(), adapt_design_preflight),
)
