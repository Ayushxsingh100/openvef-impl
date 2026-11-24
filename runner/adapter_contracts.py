"""Pack citations for every runner adapter (owner decision D-013).

Data only: nothing here selects code. tests/test_dispatch_shapes.py checks that every
adapter has a contract, that `inputs` names every property of its shape, that every quoted
text is verbatim at that line, that every value that selects code is cited in `values`, and
that `DOMAINS` gives, for every property, the cited lines and the domain terms they state
(D-015, A8-2), with an out-of-domain vector per property that the adapter must refuse.

Reading A-053 (docs/ambiguities.md): the pack does not spell descriptor JSON keys, so a key
or label spelling is only a carrier. What the pack must state is each property's meaning and
domain, the row or rule each selecting value names, and the whole outcome.
Citation: (pack file number, line, verbatim text).
"""
from __future__ import annotations

_RESP = ("30", 7, "The model must return one UTF-8 JSON object")
_NULL_RUNS = ("02", 166, "(9) Run checker null invocation 1 on the immutable null trace. (10) Run checker null "
                         "invocation 2 in a separate process on the same immutable trace")
_RUN_VALUES = {
    "timeout": ("30", 97, "a wall-clock watchdog is `CHECKER_TIMEOUT|phase=null_check`"),
    "CHECKER_RUNTIME_ERROR": ("30", 97, "A process crash is `CHECKER_RUNTIME_ERROR|class=<EXCEPTION_CLASS>`"),
    "return_invalid": ("30", 97, "A checker return error is classified in this exact order"),
    "PASS": ("30", 97, "`verdict` must be exactly `PASS` or `FAIL`"),
    "FAIL": ("30", 97, "`verdict` must be exactly `PASS` or `FAIL`"),
}
_RUN_OUTCOME = [("02", 158, "Both checker null runs have the same runtime exception, invalid-return code or timeout"),
                ("02", 159, "Both checker null runs return `FAIL`"),
                ("02", 161, "Checker results differ in verdict, valid/error status, error code or exception class"),
                ("02", 162, "Malformed diagnostic item with otherwise valid top-level return and verdict")]
_MAP = [("02", 139, "**Authoritative failure-to-stage map.** The first applicable row")]
_F18 = [("02", 174, "`F18_REJECT` fixtures use error class `ASSEMBLY_OR_MANIFEST_FAILURE`"),
        ("36", 16, "`F18_REJECT`: a packet-freeze, assembly, manifest or fixture-integrity gate rejects")]

CONTRACTS = {
    "adapt_response": {
        "inputs": {"raw_response_utf8": _RESP, "raw_response_base64": _RESP,
                   "response_object": ("30", 7, "The canonical JSON Schema is `34_OpenVEF_Response_Schema_v1.0.json`"),
                   "provider_finish_reason": ("02", 144, "Provider finish reason explicitly reports max-token truncation")},
        "values": {"length": ("02", 144, "Provider finish reason explicitly reports max-token truncation"),
                   "stop": ("02", 143, "Envelope, schema or clause manifest rejection")},
        "outcome": _MAP},
    "adapt_source_pair": {
        "inputs": {"driver_source": ("30", 27, "For file-local stages, process each source file in this order"),
                   "checker_source": ("30", 27, "process `driver.py` before `checker.py`")},
        "values": {}, "outcome": _MAP},
    "adapt_null_runs": {
        "inputs": {"response_object": ("30", 7, "The canonical JSON Schema is `34_OpenVEF_Response_Schema_v1.0.json`"),
                   "null_runs": _NULL_RUNS},
        "values": _RUN_VALUES, "outcome": _MAP + _RUN_OUTCOME},
    "adapt_checker_runs": {"inputs": {"checker_runs": _NULL_RUNS}, "values": _RUN_VALUES, "outcome": _RUN_OUTCOME},
    "adapt_events": {
        "inputs": {"events": ("02", 139, "The first applicable row after the exact evaluation order below controls")},
        "values": {
            "schema_reject": ("02", 143, "`SCHEMA_REJECT|pointer=<JSON_POINTER>`"),
            "output_truncated": ("02", 144, "Provider finish reason explicitly reports max-token truncation"),
            "import_not_allowed": ("02", 147, "Disallowed import form/root"),
            "compile_error": ("02", 149, "Driver compile error"),
            "driver_runtime": ("02", 151, "Driver factory or `step` raises"),
            "driver_vector": ("02", 152, "Driver return value/vector is invalid"),
            "driver_watchdog": ("02", 153, "Driver step watchdog expires"),
            "simulator_error": ("02", 154, "Simulator error on RTL or null run"),
            "trace_integrity": ("02", 155, "Harness trace-integrity fault"),
            "driver.py": ("02", 125, "`FILE` is `driver.py` or `checker.py`"),
            "checker.py": ("02", 125, "`FILE` is `driver.py` or `checker.py`")},
        "outcome": _MAP},
    "adapt_halt_recurrence": {  # input contract only: no outcome (the error class is unstated, PD-26)
        "inputs": {"design_id": ("02", 185, "`design_id` is `FIFO` or `UART`"),
                   "recovery_cycles_used": ("02", 185, "After one permitted recovery cycle succeeds"),
                   "first_halt_signature": ("02", 185, "Define the **halt signature** as"),
                   "second_halt_signature": ("02", 185, "If the identical halt signature recurs after recovery"),
                   "scheduled_slots": ("02", 185, "re-evaluate every scheduled slot in the affected scope")},
        "values": {"FIFO": ("02", 185, "`design_id` is `FIFO` or `UART`"),
                   "UART": ("02", 185, "`design_id` is `FIFO` or `UART`")}, "outcome": []},
    "adapt_clause_ids": {
        "inputs": {"visible_payload": ("31", 30, "Search those payload bytes using"),
                   "manifest_clause_ids": ("31", 30, "requires equality with manifest `clause_ids`"),
                   "clause_id_regex": ("31", 29, "`clause_id_regex` is a fully anchored regular expression"),
                   "clause_id_search_regex": ("31", 30, "`clause_id_search_regex = "),
                   "clause_id_near_match_regex": ("31", 30, "`clause_id_near_match_regex = ")},
        "values": {}, "outcome": [("02", 173, "`F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH`"),
                                  ("02", 173, "`F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN`"), *_F18]},
    "adapt_reserved_headings": {
        "inputs": {"payload": ("31", 27, "If any payload line equals one of the reserved headings after LF normalization"),
                   "reserved_headings": ("31", 9, "one of the nine reserved headings in the sidecar")},
        "values": {}, "outcome": [("02", 173, "`PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE`"), *_F18]},
    "adapt_rendered": {
        "inputs": {"rendered": ("31", 28, "Missing, duplicate or unresolved matches of `\\{\\{[A-Z0-9_]+\\}\\}` are hard errors")},
        "values": {}, "outcome": [("02", 173, "`ASSEMBLY_REJECT|reason=UNRESOLVED_PLACEHOLDER`"), *_F18]},
    "adapt_runtime_signature": {
        "inputs": {"runtime_signature": ("30", 35, "Runtime `inspect.signature` must confirm the same parameter "
                                                   "names/kinds/counts")},
        "values": {"create_driver": ("30", 35, "It has exactly one required positional-or-keyword parameter named `seed`"),
                   "Driver.step": ("30", 35, "named `self`, `cycle_index`, `outputs_after_edge`"),
                   "check_trace": ("30", 37, "parameters named `trace` and `metadata`")},
        "outcome": [("02", 148, "inspect-signature mismatch")]},
    "adapt_vector_keys": {
        "inputs": {"driver_return": ("30", 83, "A return value is either the exact string `COMPLETE` or a dictionary"),
                   "expected_keys": ("30", 83, "its key set equals the frozen top-level input-port set exactly")},
        "values": {}, "outcome": [("02", 152, "Driver return value/vector is invalid")]},
    "adapt_paired_runs": {
        "inputs": {"paired_runs": ("02", 166, "compare raw outputs before that row's next-input decision; any next-input "
                                              "mismatch before first raw-output divergence is terminal driver "
                                              "nondeterminism")},
        "values": {}, "outcome": [("02", 156, "Before first raw output divergence, paired next-input schedules differ")]},
}

_HEADINGS = {10: "[Task instruction]", 15: "[Design specification]", 20: "[Port manifest]",
             25: "[Reset and legal-input rules]", 30: "[Execution envelope]", 35: "[Driver API]",
             40: "[Trace schema]", 45: "[Checker contract]", 50: "[Response schema]"}
_RUN_DOMAIN = {"lines": [("02", 166), ("30", 97)],
               "terms": ["checker null invocation 1", "checker null invocation 2", "`PASS` or `FAIL`", "NON_DICTIONARY",
                         "MISSING_DIAGNOSTICS", "TOP_LEVEL_KEYS", "INVALID_VERDICT", "DIAGNOSTICS_NOT_LIST",
                         "CHECKER_RUNTIME_ERROR|class=", "CHECKER_TIMEOUT|phase=null_check"]}
_RESP_DOMAIN = {"lines": [("30", 7)], "terms": ["one UTF-8 JSON object", "34_OpenVEF_Response_Schema_v1.0.json"]}

# property -> cited lines, and the terms of its domain that those lines must state verbatim.
DOMAINS = {
    "adapt_response": {
        "raw_response_utf8": _RESP_DOMAIN, "raw_response_base64": _RESP_DOMAIN, "response_object": _RESP_DOMAIN,
        "provider_finish_reason": {"lines": [("02", 144)], "terms": ["explicitly reports max-token truncation"]}},
    "adapt_source_pair": {
        "driver_source": {"lines": [("30", 27)], "terms": ["strict UTF-8 decode", "`driver.py`"]},
        "checker_source": {"lines": [("30", 27)], "terms": ["strict UTF-8 decode", "`checker.py`"]}},
    "adapt_null_runs": {"response_object": _RESP_DOMAIN, "null_runs": _RUN_DOMAIN},
    "adapt_checker_runs": {"checker_runs": _RUN_DOMAIN},
    "adapt_events": {"events": {
        "lines": [("02", n) for n in (125, 139, 143, 144, 147, 149, 150, 151, 152, 153, 154, 155)],
        "terms": ["SCHEMA_REJECT", "OUTPUT_TRUNCATED", "IMPORT_NOT_ALLOWED", "COMPILE_ERROR", "RUNTIME_EXCEPTION",
                  "DRIVER_VECTOR_INVALID", "WATCHDOG_TIMEOUT", "SIMULATOR_ERROR", "TRACE_INTEGRITY_FAILURE",
                  "`FILE` is `driver.py` or `checker.py`", "`PHASE` is `factory` or `step`",
                  "`RTL_OR_NULL` is `rtl` or `null`", "`LINE` and `COLUMN` are positive decimal integers"]}},
    "adapt_halt_recurrence": {
        "design_id": {"lines": [("02", 185)], "terms": ["`design_id` is `FIFO` or `UART`"]},
        "recovery_cycles_used": {"lines": [("02", 185)], "terms": ["one permitted recovery cycle"]},
        "scheduled_slots": {"lines": [("02", 181), ("02", 185)],
                            "terms": ["a *slot* is exactly one arm × design combination", "every scheduled slot"]},
        "first_halt_signature": {"lines": [("02", 185)], "terms": [
            "`halt_code` is `SIMULATOR_ERROR`, `TRACE_INTEGRITY_FAILURE` or `RTL_NULL_CONTROL_FAILURE`",
            "`evaluator_component` is `SIMULATOR`", "`stable_error_class` is", "`stable_diagnostic_code` is exactly"]},
        "second_halt_signature": {"lines": [("02", 185)], "terms": ["Its components have these exact domains"]}},
    "adapt_clause_ids": {
        "visible_payload": {"lines": [("31", 30)], "terms": ["those payload bytes"]},
        "manifest_clause_ids": {"lines": [("31", 29)], "terms": ["duplicate-free, lexicographically sorted array of strings",
                                                                 "fully matches that pattern"]},
        "clause_id_regex": {"lines": [("31", 91)], "terms": ["^[A-Z]{2,6}-[0-9]{3}$"]},
        "clause_id_search_regex": {"lines": [("31", 92)], "terms": ["(?<![A-Za-z0-9_-])[A-Z]{2,6}-[0-9]{3}(?![A-Za-z0-9_-])"]},
        "clause_id_near_match_regex": {"lines": [("31", 93)],
                                       "terms": ["(?<![A-Za-z0-9_-])[A-Za-z]{2,6}-[0-9]{1,3}(?![A-Za-z0-9_-])"]}},
    "adapt_reserved_headings": {
        "payload": {"lines": [("31", 27)], "terms": ["any payload line", "after LF normalization"]},
        "reserved_headings": {"lines": [("31", 9), *(("33", n) for n in _HEADINGS)],
                              "terms": ["one of the nine reserved headings in the sidecar", *_HEADINGS.values()]}},
    "adapt_rendered": {"rendered": {"lines": [("31", 28)], "terms": ["\\{\\{[A-Z0-9_]+\\}\\}"]}},
    "adapt_runtime_signature": {"runtime_signature": {
        "lines": [("30", 35), ("30", 37)],
        "terms": ["named `seed`", "`self`, `cycle_index`, `outputs_after_edge`", "`trace` and `metadata`",
                  "`driver.py`", "`checker.py`", "`create_driver`", "`Driver.step`", "`check_trace`"]}},
    "adapt_vector_keys": {
        "driver_return": {"lines": [("30", 83)], "terms": ["exact string `COMPLETE` or a dictionary", "each value is a string"]},
        "expected_keys": {"lines": [("30", 83)], "terms": ["frozen top-level input-port set"]}},
    "adapt_paired_runs": {"paired_runs": {
        "lines": [("02", 156), ("02", 166)],
        "terms": ["first raw output divergence", "next-input schedules", "first raw-output divergence"]}},
}
