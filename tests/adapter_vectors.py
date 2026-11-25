"""Synthetic, non-fixture inputs for every runner adapter (D-013 (b)).

Each entry: (input, expected). Expected is the four-field record, or BLOCKED + a substring
of the reason when the cited rule gives no rejection or the input is outside the contract.
No input or expectation is copied from a fixture descriptor; the test checks this.
"""
from __future__ import annotations

import base64
import json

BLOCKED = "BLOCKED:"
DRIVER = ("import random\n\nclass Driver:\n    def step(self, cycle_index, outputs_after_edge):\n"
          "        return 'COMPLETE'\n\ndef create_driver(seed):\n    d = Driver()\n    d.r = random.Random(seed)\n"
          "    return d\n")
CHECKER = "def check_trace(trace, metadata):\n    return {'verdict': 'PASS', 'diagnostics': []}\n"


def rec(disposition, stage_id, error_class, diagnostic):
    return {"disposition": disposition, "stage_id": stage_id, "error_class": error_class, "diagnostic": diagnostic}


def repair(stage, cls, diagnostic):
    return rec("REPAIR", stage, cls, diagnostic)


def response(driver=DRIVER, checker=CHECKER, **over):
    obj = {"schema_version": "1.0", "language": "python", "language_version": "3.11",
           "driver": {"filename": "driver.py", "factory": "create_driver(seed: int) -> Driver", "class_name": "Driver",
                      "method": "step(cycle_index: int, outputs_after_edge: dict[str, str]) -> dict[str, str] | str",
                      "source": driver},
           "checker": {"filename": "checker.py",
                       "entry_point": "check_trace(trace: dict[str, object], metadata: dict[str, object]) -> "
                                      "dict[str, object]",
                       "source": checker},
           "dependencies": [], "assumptions": []}
    obj.update(over)
    return obj


def b64(text: bytes) -> str:
    return base64.b64encode(text).decode("ascii")


def sig(design="UART", code="RTL_NULL_CONTROL_FAILURE", comp="RTL_NULL_COMPARATOR", cls="NONE", diag=None):
    return {"design_id": design, "halt_code": code, "evaluator_component": comp, "stable_error_class": cls,
            "stable_diagnostic_code": diag or code}


def halt(a, b):
    return {"design_id": "UART", "recovery_cycles_used": 1, "first_halt_signature": a, "second_halt_signature": b,
            "scheduled_slots": 6}


SCHEMA = lambda p: repair("PARSE_SCHEMA", "SCHEMA_REJECT", f"SCHEMA_REJECT|pointer={p}")  # noqa: E731
F18 = lambda d: rec("F18_REJECT", "F18", "ASSEMBLY_OR_MANIFEST_FAILURE", d)  # noqa: E731
DISAGREE = rec("TERMINAL_INVALID_NO_REPAIR", "TERMINAL", "CHECKER_NONDETERMINISM",
               "CHECKER_NONDETERMINISM|reason=RUN_DISAGREEMENT")
NEXT_INPUT = rec("TERMINAL_INVALID_NO_REPAIR", "TERMINAL", "DRIVER_NONDETERMINISM",
                 "DRIVER_NONDETERMINISM|reason=NEXT_INPUT_DIVERGENCE")
CLAUSE = "^[A-Z]{2,6}-[0-9]{3}$"


def crash(name):
    return {"error_code": "CHECKER_RUNTIME_ERROR", "exception_class": name}


def invalid(reason):
    return {"type": "return_invalid", "reason": reason}


VECTORS = {
    "adapt_response": [
        ({"response_object": response(language="ruby")}, SCHEMA("/language")),
        ({"raw_response_utf8": json.dumps(response(language_version="3.9"))}, SCHEMA("/language_version")),
        ({"raw_response_base64": b64(b"\xff\xfe{}")}, SCHEMA("/")),
        ({"raw_response_utf8": "{}", "provider_finish_reason": "length"},
         repair("PARSE_SCHEMA", "OUTPUT_TRUNCATED", "OUTPUT_TRUNCATED")),
        ({"raw_response_utf8": "{", "provider_finish_reason": "stop"}, SCHEMA("/")),
        ({"raw_response_utf8": "{}", "provider_finish_reason": "other"}, BLOCKED + "finish reason"),
        ({"response_object": response(driver="import socket\n" + DRIVER)},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=socket")),
    ],
    "adapt_source_pair": [
        ({"driver_source": DRIVER, "checker_source": "import socket\n"},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=socket")),
        ({"driver_source": DRIVER, "checker_source": "\t"},
         repair("SOURCE_AST", "SOURCE_EMPTY", "SOURCE_EMPTY|file=checker.py")),
        ({"driver_source": "import ctypes\n", "checker_source": "import socket\n"},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=ctypes")),
    ],
    "adapt_null_runs": [
        ({"response_object": response(), "null_runs": [invalid("TOP_LEVEL_KEYS")] * 2},
         repair("CHECKER_NULL", "CHECKER_RETURN_INVALID", "CHECKER_RETURN_INVALID|reason=TOP_LEVEL_KEYS")),
        ({"response_object": response(), "null_runs": [{"timeout": True}, {"verdict": "PASS"}]}, DISAGREE),
        ({"response_object": response(), "null_runs": [crash("OverflowError")] * 2},
         repair("CHECKER_NULL", "CHECKER_RUNTIME_ERROR", "CHECKER_RUNTIME_ERROR|class=OverflowError")),
        ({"response_object": response(language="ruby"), "null_runs": [{"timeout": True}] * 2}, SCHEMA("/language")),
    ],
    "adapt_checker_runs": [
        ({"checker_runs": [crash("OverflowError")] * 2},
         repair("CHECKER_NULL", "CHECKER_RUNTIME_ERROR", "CHECKER_RUNTIME_ERROR|class=OverflowError")),
        ({"checker_runs": [invalid("INVALID_VERDICT")] * 2},
         repair("CHECKER_NULL", "CHECKER_RETURN_INVALID", "CHECKER_RETURN_INVALID|reason=INVALID_VERDICT")),
        ({"checker_runs": [{"verdict": "FAIL"}, {"timeout": True}]}, DISAGREE),
        ({"checker_runs": [{"verdict": "PASS"}]}, BLOCKED + "two run records"),
    ],
    "adapt_events": [
        ({"events": [{"kind": "schema_reject", "pointer": "/checker/source"}]}, SCHEMA("/checker/source")),
        ({"events": [{"kind": "driver_watchdog"}, {"kind": "output_truncated"}]},
         repair("PARSE_SCHEMA", "OUTPUT_TRUNCATED", "OUTPUT_TRUNCATED")),
        ({"events": [{"kind": "compile_error", "file": "driver.py", "line": 7},
                     {"kind": "import_not_allowed", "module": "ssl"}]},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=ssl")),
        ({"events": [{"kind": "compile_error", "file": "checker.py", "line": 8}]},
         repair("COMPILE_CHECKER", "COMPILE_ERROR", "COMPILE_ERROR|file=checker.py|line=8")),
        ({"events": [{"kind": "driver_runtime", "phase": "factory", "exception_class": "OverflowError"}]},
         repair("DRIVER_RUNTIME", "RUNTIME_EXCEPTION", "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=OverflowError")),
        ({"events": [{"kind": "driver_vector", "reason": "NON_STRING_VALUE"}]},
         repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=NON_STRING_VALUE")),
        ({"events": [{"kind": "driver_watchdog"}, {"kind": "trace_integrity", "reason": "REPLAY_HASH_MISMATCH"}]},
         repair("DRIVER_WATCHDOG", "WATCHDOG_TIMEOUT", "WATCHDOG_TIMEOUT|phase=driver_step")),
        ({"events": [{"kind": "simulator_error", "target": "rtl", "exception_class": "OSError"}]},
         rec("DESIGN_HALT_NO_SLOT_SCORED", "DESIGN_HALT", "EVALUATOR_INFRASTRUCTURE_FAILURE",
             "SIMULATOR_ERROR|target=rtl|class=OSError")),
        ({"events": [{"kind": "trace_integrity", "reason": "MALFORMED_RECORDER_OUTPUT"}]},
         rec("DESIGN_HALT_NO_SLOT_SCORED", "DESIGN_HALT", "TRACE_INTEGRITY_FAILURE",
             "TRACE_INTEGRITY_FAILURE|reason=MALFORMED_RECORDER_OUTPUT")),
        ({"events": [{"kind": "something_else"}]}, BLOCKED + "unknown event kind"),
    ],
    "adapt_halt_recurrence": [
        (halt(sig(), sig()), BLOCKED + "identical: True"),
        (halt(sig(), sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="OSError")), BLOCKED + "identical: False"),
        (halt(sig(design="SPI"), sig()), BLOCKED + "design_id='SPI'"),
    ],
    "adapt_clause_ids": [
        ({"visible_payload": "UART-001 and UART-002", "manifest_clause_ids": ["UART-001"], "clause_id_regex": CLAUSE},
         F18("F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH")),
        ({"visible_payload": "see uart-7", "manifest_clause_ids": ["UART-001"], "clause_id_regex": CLAUSE},
         F18("F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN")),
        ({"visible_payload": "UART-001", "manifest_clause_ids": ["UART-001"], "clause_id_regex": CLAUSE},
         BLOCKED + "check passed"),
    ],
    "adapt_reserved_headings": [
        ({"payload": "a\r\n[Port manifest]\r\nb", "reserved_headings": ["[Checker contract]", "[Port manifest]"]},
         F18("PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE")),
        ({"payload": "x [Port manifest]", "reserved_headings": ["[Port manifest]"]}, BLOCKED + "check passed"),
        ({"payload": "[Port manifest] ", "reserved_headings": ["[Port manifest]"]}, BLOCKED + "check passed"),
        ({"payload": "", "reserved_headings": []}, BLOCKED + "check passed"),
        # the canonical list decides, not the supplied one
        ({"payload": "[Driver API]", "reserved_headings": []}, F18("PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE")),
        ({"payload": "[My heading]", "reserved_headings": ["[My heading]"]}, BLOCKED + "outside its cited domain"),
    ],
    "adapt_rendered": [
        ({"rendered": "x {{A_1}} y"}, F18("ASSEMBLY_REJECT|reason=UNRESOLVED_PLACEHOLDER")),
        ({"rendered": "x {{lower}} y"}, BLOCKED + "check passed"),
        ({"rendered": "x {A_1} y"}, BLOCKED + "check passed"),
    ],
    "adapt_runtime_signature": [
        ({"runtime_signature": {"file": "checker.py", "symbol": "check_trace", "actual": ["trace"],
                                "expected": ["trace", "metadata"]}},
         repair("AST_SIGNATURE", "ENTRY_POINT_REJECT",
                "ENTRY_POINT_REJECT|file=checker.py|symbol=check_trace|reason=RUNTIME_SIGNATURE")),
        ({"runtime_signature": {"file": "driver.py", "symbol": "create_driver", "actual": ["s"], "expected": ["seed"]}},
         repair("AST_SIGNATURE", "ENTRY_POINT_REJECT",
                "ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RUNTIME_SIGNATURE")),
        ({"runtime_signature": {"file": "driver.py", "symbol": "create_driver", "actual": ["seed"], "expected": ["seed"]}},
         BLOCKED + "check passed"),
        ({"runtime_signature": {"file": "driver.py", "symbol": "helper", "actual": [], "expected": ["x"]}},
         BLOCKED + "not a File 30"),
    ],
    "adapt_vector_keys": [
        ({"driver_return": 7, "expected_keys": ["a"]},
         repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=RETURN_TYPE")),
        ({"driver_return": {"a": 1, "b": "0"}, "expected_keys": ["a", "b"]},
         repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=NON_STRING_VALUE")),
        ({"driver_return": {"a": "0"}, "expected_keys": ["a", "b"]},
         repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=MISSING_KEYS")),
        ({"driver_return": {"a": "0"}, "expected_keys": ["a"]}, BLOCKED + "widths not supplied"),
    ],
    "adapt_paired_runs": [
        ({"paired_runs": {"first_raw_output_divergence_cycle": 9, "first_next_input_divergence_cycle": 8}}, NEXT_INPUT),
        ({"paired_runs": {"first_raw_output_divergence_cycle": 8, "first_next_input_divergence_cycle": 8}},
         BLOCKED + "check passed"),
        ({"paired_runs": {"first_raw_output_divergence_cycle": None, "first_next_input_divergence_cycle": None}},
         BLOCKED + "check passed"),
        ({"paired_runs": {"first_raw_output_divergence_cycle": "8", "first_next_input_divergence_cycle": 1}},
         BLOCKED + "outside the contract"),
    ],
}


# One out-of-domain input per property (D-015): the adapter must refuse it (BLOCKED), or reject it
# by a cited rule where the property's domain is "anything, judged by the rule".
OUT_OF_DOMAIN = {
    "adapt_response": {"raw_response_utf8": {"raw_response_utf8": 7}, "raw_response_base64": {"raw_response_base64": 7},
                       "response_object": {"response_object": 7},
                       "provider_finish_reason": {"raw_response_utf8": "{}", "provider_finish_reason": "max_tokens"}},
    "adapt_source_pair": {"driver_source": {"driver_source": 7, "checker_source": CHECKER},
                          "checker_source": {"driver_source": DRIVER, "checker_source": None}},
    "adapt_null_runs": {"response_object": {"response_object": [], "null_runs": [{"timeout": True}] * 2},
                        "null_runs": {"response_object": response(), "null_runs": ["PASS", "PASS"]}},
    "adapt_checker_runs": {"checker_runs": {"checker_runs": [{"verdict": "MAYBE"}] * 2}},
    "adapt_events": {"events": {"events": "driver_watchdog"}},
    "adapt_halt_recurrence": {"design_id": dict(halt(sig(), sig()), design_id="SPI"),
                              "recovery_cycles_used": dict(halt(sig(), sig()), recovery_cycles_used=2),
                              "scheduled_slots": dict(halt(sig(), sig()), scheduled_slots="6"),
                              "first_halt_signature": halt(sig(comp="rtl_null_comparator"), sig()),
                              "second_halt_signature": halt(sig(), [])},
    "adapt_clause_ids": {
        p: dict({"visible_payload": "UART-001", "manifest_clause_ids": ["UART-001"], "clause_id_regex": CLAUSE}, **{p: v})
        for p, v in (("visible_payload", 7), ("manifest_clause_ids", ["UART-002", "UART-001"]), ("clause_id_regex", ".*"),
                     ("clause_id_search_regex", ".*"), ("clause_id_near_match_regex", "x^"))},
    "adapt_reserved_headings": {"payload": {"payload": 7, "reserved_headings": []},
                                "reserved_headings": {"payload": "a\n[X]", "reserved_headings": ["[X]"]}},
    "adapt_rendered": {"rendered": {"rendered": ["{{A}}"]}},
    "adapt_runtime_signature": {"runtime_signature": {"runtime_signature": {
        "file": "driver.py", "symbol": "create_driver", "actual": ["x"], "expected": ["x", "y"]}}},
    "adapt_vector_keys": {"driver_return": {"driver_return": [], "expected_keys": ["a"]},
                          "expected_keys": {"driver_return": {"a": "0"}, "expected_keys": ["a", "a"]}},
    "adapt_paired_runs": {"paired_runs": {"paired_runs": {"first_raw_output_divergence_cycle": -1,
                                                          "first_next_input_divergence_cycle": 1}}},
}
# Properties whose out-of-domain value is rejected by a rule rather than refused.
JUDGED_BY_RULE = {("adapt_response", "response_object"), ("adapt_null_runs", "response_object"),
                  ("adapt_vector_keys", "driver_return")}


# D-017: boundary pairs. (cited domain term, property, in-domain edge, expected, just outside, expected);
# the two inputs differ in that property only. Surrogates start at U+D800, so U+D7FF is the last
# code point before the gap in what UTF-8 can encode; U+FEFF is the BOM.
SOCKET = repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=socket")
OUTSIDE = BLOCKED + "outside its cited domain"
VOCAB = BLOCKED + "outside the adapter vocabulary"
MISMATCH = F18("F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH")
HEADING = F18("PACKET_FREEZE_REJECT|reason=RESERVED_HEADING_LINE")
PLACEHOLDER = F18("ASSEMBLY_REJECT|reason=UNRESOLVED_PLACEHOLDER")
PASSED = BLOCKED + "check passed"
VALID = BLOCKED + "PD-26"
SIGNATURE = BLOCKED + "PD-01"
BAD_IMPORT = "import socket\n" + DRIVER
RUBY = json.dumps(response(language="ruby"))


def replaced(base, prop, term, edge, edge_expected, outside, outside_expected):
    return (term, prop, {**base, prop: edge}, edge_expected, {**base, prop: outside}, outside_expected)


def more(event):
    """A second event that never controls: the watchdog for earlier rows, a repeat for later ones."""
    return [dict(event) if event["kind"] in ("simulator_error", "trace_integrity") else {"kind": "driver_watchdog"}]


def halted(diag, cls):
    return rec("DESIGN_HALT_NO_SLOT_SCORED", "DESIGN_HALT", cls, diag)


def run_pairs(base, prop):
    terms = [("checker null invocation 2", [{"verdict": "FAIL"}, {"verdict": "PASS"}], DISAGREE,
              [{"verdict": "FAIL"}, {"verdict": "PASS"}, {"verdict": "PASS"}], BLOCKED + "exactly two run records"),
             ("`PASS` or `FAIL`", [{"verdict": "FAIL"}, {"verdict": "PASS"}], DISAGREE,
              [{"verdict": "FAIL"}, {"verdict": "pASS"}], VOCAB),
             ("CHECKER_TIMEOUT|phase=null_check", [{"timeout": True}] * 2,
              repair("CHECKER_NULL", "CHECKER_TIMEOUT", "CHECKER_TIMEOUT|phase=null_check"),
              [{"timeout": True}, {"timeout": False}], VOCAB)]
    for reason in ("NON_DICTIONARY", "MISSING_DIAGNOSTICS", "TOP_LEVEL_KEYS", "INVALID_VERDICT", "DIAGNOSTICS_NOT_LIST"):
        terms.append((reason, [invalid(reason)] * 2,
                      repair("CHECKER_NULL", "CHECKER_RETURN_INVALID", "CHECKER_RETURN_INVALID|reason=" + reason),
                      [invalid(reason), invalid(reason + "S")], VOCAB))
    return [replaced(base, prop, *t) for t in terms]


def paired(a, b):
    return {"first_raw_output_divergence_cycle": a, "first_next_input_divergence_cycle": b}


def runtime_sig(file="driver.py", symbol="create_driver", actual=(), expected=("seed",)):
    return {"file": file, "symbol": symbol, "actual": list(actual), "expected": list(expected)}


def sig_fail(file, symbol):
    return repair("AST_SIGNATURE", "ENTRY_POINT_REJECT", f"ENTRY_POINT_REJECT|file={file}|symbol={symbol}|reason=RUNTIME_SIGNATURE")


def clause_base(payload="UART-001", ids=("UART-002",)):
    return {"visible_payload": payload, "manifest_clause_ids": list(ids), "clause_id_regex": CLAUSE}


SEARCH = r"(?<![A-Za-z0-9_-])[A-Z]{2,6}-[0-9]{3}(?![A-Za-z0-9_-])"
NEAR = r"(?<![A-Za-z0-9_-])[A-Za-z]{2,6}-[0-9]{1,3}(?![A-Za-z0-9_-])"
NINE = ["[Task instruction]", "[Design specification]", "[Port manifest]", "[Reset and legal-input rules]",
        "[Execution envelope]", "[Driver API]", "[Trace schema]", "[Checker contract]", "[Response schema]"]
_OBJECT = response(driver=BAD_IMPORT)
_RAW_BASE = response(driver="# \ud7ff\n" + BAD_IMPORT)
_RUN_BASE = {"response_object": response(), "null_runs": [{"timeout": True}] * 2}
_HALT = halt(sig(), sig())
_HALT_SIM = sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="_")


def halt_pairs(prop):
    return [replaced(_HALT, prop, "`halt_code` is `SIMULATOR_ERROR`, `TRACE_INTEGRITY_FAILURE` or `RTL_NULL_CONTROL_FAILURE`"
                     if prop == "first_halt_signature" else "Its components have these exact domains", edge, VALID, out, SIGNATURE)
            for edge, out in ((_HALT_SIM, sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="")),
                              (_HALT_SIM, sig(code="SIMULATOR_ERROR", comp="SIMULATOR", cls="_\n")),
                              (sig(), sig(cls="NONE_")), (sig(), sig(comp="RTL_NULL_COMPARATORS")),
                              (sig(), sig(code="RTL_NULL_CONTROL_FAILURES", diag="RTL_NULL_CONTROL_FAILURE")), (sig(), sig(diag="RTL_NULL_CONTROL_FAILUR")))]


BOUNDARIES = {
    "adapt_response": [
        replaced({}, "raw_response_utf8", "one UTF-8 JSON object", RUBY, SCHEMA("/language"), RUBY + "{}", SCHEMA("/")),
        replaced({}, "raw_response_utf8", "one UTF-8 JSON object", json.dumps(_RAW_BASE, ensure_ascii=False), SOCKET,
                 json.dumps(_RAW_BASE, ensure_ascii=False).replace("\ud7ff", "\ud800"), OUTSIDE),
        replaced({}, "raw_response_base64", "one UTF-8 JSON object", b64(RUBY.encode()), SCHEMA("/language"),
                 b64(RUBY.encode() + b"\xff"), SCHEMA("/")),
        replaced({}, "raw_response_base64", "one UTF-8 JSON object", b64(RUBY.encode()), SCHEMA("/language"),
                 b64(RUBY.encode()) + "=", OUTSIDE),
        replaced({}, "response_object", "34_OpenVEF_Response_Schema_v1.0.json", _OBJECT, SOCKET,
                 dict(_OBJECT, schema_version="1.00"), SCHEMA("/schema_version")),
        replaced({"raw_response_utf8": "{"}, "provider_finish_reason", "explicitly reports max-token truncation", "length",
                 repair("PARSE_SCHEMA", "OUTPUT_TRUNCATED", "OUTPUT_TRUNCATED"), "lengths", BLOCKED + "finish reason")],
    "adapt_source_pair": [
        replaced({"checker_source": CHECKER}, "driver_source", "strict UTF-8 decode", "# \ud7ff\nimport socket\n", SOCKET,
                 "# \ud800\nimport socket\n",
                 repair("SOURCE_AST", "SOURCE_SYNTAX_REJECT", "SOURCE_SYNTAX_REJECT|file=driver.py|line=1|column=1")),
        replaced({"driver_source": DRIVER}, "checker_source", "strict UTF-8 decode", "# \ud7ff\nimport socket\n", SOCKET,
                 "# \ud800\nimport socket\n",
                 repair("SOURCE_AST", "SOURCE_SYNTAX_REJECT", "SOURCE_SYNTAX_REJECT|file=checker.py|line=1|column=1"))],
    "adapt_null_runs": [
        replaced(_RUN_BASE, "response_object", "34_OpenVEF_Response_Schema_v1.0.json", response(),
                 repair("CHECKER_NULL", "CHECKER_TIMEOUT", "CHECKER_TIMEOUT|phase=null_check"),
                 response(schema_version="1.00"), SCHEMA("/schema_version")),
        *run_pairs(_RUN_BASE, "null_runs")],
    "adapt_checker_runs": run_pairs({}, "checker_runs"),
    "adapt_events": [replaced({}, "events", term, [edge, *more(edge)], exp, [out, *more(edge)], VOCAB) for term, edge, exp, out in (
        ("escape `~` as `~0` and `/` as `~1`", {"kind": "schema_reject", "pointer": "/~1"}, SCHEMA("/~1"), {"kind": "schema_reject", "pointer": "/~2"}),
        ("show root as `/`", {"kind": "schema_reject", "pointer": "/"}, SCHEMA("/"), {"kind": "schema_reject", "pointer": ""}),
        ("the offending root as written", {"kind": "import_not_allowed", "module": "maths"},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=maths"),
         {"kind": "import_not_allowed", "module": "math"}),
        ("the offending root as written", {"kind": "import_not_allowed", "module": "os"},
         repair("IMPORT_POLICY", "IMPORT_POLICY_REJECT", "IMPORT_NOT_ALLOWED|module=os"),
         {"kind": "import_not_allowed", "module": "os."}),
        ("`LINE` and `COLUMN` are positive decimal integers", {"kind": "compile_error", "file": "checker.py", "line": 1},
         repair("COMPILE_CHECKER", "COMPILE_ERROR", "COMPILE_ERROR|file=checker.py|line=1"),
         {"kind": "compile_error", "file": "checker.py", "line": 0}),
        ("`FILE` is `driver.py` or `checker.py`", {"kind": "compile_error", "file": "driver.py", "line": 1},
         repair("COMPILE_DRIVER", "COMPILE_ERROR", "COMPILE_ERROR|file=driver.py|line=1"),
         {"kind": "compile_error", "file": "drivers.py", "line": 1}),
        ("`PHASE` is `factory` or `step`", {"kind": "driver_runtime", "phase": "step", "exception_class": "OverflowError"},
         repair("DRIVER_RUNTIME", "RUNTIME_EXCEPTION", "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=OverflowError"),
         {"kind": "driver_runtime", "phase": "steps", "exception_class": "OverflowError"}),
        ("`RTL_OR_NULL` is `rtl` or `null`", {"kind": "simulator_error", "target": "null", "exception_class": "OSError"},
         halted("SIMULATOR_ERROR|target=null|class=OSError", "EVALUATOR_INFRASTRUCTURE_FAILURE"),
         {"kind": "simulator_error", "target": "nul", "exception_class": "OSError"}),
        ("`DRIVER_VECTOR_INVALID.reason` is one of", {"kind": "driver_vector", "reason": "ILLEGAL_PROTOCOL_STATE"},
         repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"),
         {"kind": "driver_vector", "reason": "ILLEGAL_PROTOCOL_STATES"}),
        ("`TRACE_INTEGRITY_FAILURE.reason` is one of", {"kind": "trace_integrity", "reason": "UNTRUSTED_TRACE_SERIALIZATION"},
         halted("TRACE_INTEGRITY_FAILURE|reason=UNTRUSTED_TRACE_SERIALIZATION", "TRACE_INTEGRITY_FAILURE"),
         {"kind": "trace_integrity", "reason": "UNTRUSTED_TRACE_SERIALIZATIO"}),
        ("WATCHDOG_TIMEOUT", {"kind": "driver_watchdog"},
         repair("DRIVER_WATCHDOG", "WATCHDOG_TIMEOUT", "WATCHDOG_TIMEOUT|phase=driver_step"), {"kind": "driver_watchdogs"}),
        ("OUTPUT_TRUNCATED", {"kind": "output_truncated"}, repair("PARSE_SCHEMA", "OUTPUT_TRUNCATED", "OUTPUT_TRUNCATED"),
         {"kind": "output_truncate"}))],
    "adapt_halt_recurrence": [
        replaced(_HALT, "design_id", "`design_id` is `FIFO` or `UART`", "FIFO", VALID, "FIFOS", OUTSIDE),
        replaced(_HALT, "recovery_cycles_used", "one permitted recovery cycle", 1, VALID, 2, OUTSIDE),
        replaced(_HALT, "recovery_cycles_used", "one permitted recovery cycle", 1, VALID, 0, OUTSIDE),
        replaced(_HALT, "scheduled_slots", "every scheduled slot", 1, VALID, 0, OUTSIDE),
        *halt_pairs("first_halt_signature"), *halt_pairs("second_halt_signature")],
    "adapt_clause_ids": [
        replaced(clause_base(), "visible_payload", "reject invalid UTF-8 and BOM", "\ud7ff", MISMATCH, "\ud800", OUTSIDE),
        replaced(clause_base(), "visible_payload", "reject invalid UTF-8 and BOM", "\ufefe UART-001", MISMATCH,
                 "\ufeff UART-001", OUTSIDE),
        *(replaced(clause_base(), "manifest_clause_ids", "fully matches that pattern", [edge], MISMATCH, [out], OUTSIDE)
          for edge, out in (("AB-000", "A-000"), ("ABCDEF-999", "ABCDEFG-999"), ("AB-000", "AB-00"), ("AB-000", "AB-0000"),
                            ("AB-000", "AB-000\n"))),
        replaced(clause_base(), "manifest_clause_ids", "duplicate-free, lexicographically sorted array of strings",
                 ["AB-000", "AB-001"], MISMATCH, ["AB-001", "AB-001"], OUTSIDE),
        replaced(clause_base(), "manifest_clause_ids", "duplicate-free, lexicographically sorted array of strings",
                 ["AB-001", "AB-002"], MISMATCH, ["AB-001", "AB-000"], OUTSIDE),
        *(replaced(clause_base(), p, pat, pat, MISMATCH, out, OUTSIDE)
          for p, pat in (("clause_id_regex", CLAUSE), ("clause_id_search_regex", SEARCH), ("clause_id_near_match_regex", NEAR))
          for out in (pat[:-1], pat.replace("2,6", "2,7")))],
    "adapt_reserved_headings": [
        replaced({"reserved_headings": []}, "payload", "reject invalid UTF-8 and BOM", "\ud7ff\n[Driver API]", HEADING,
                 "\ud800\n[Driver API]", OUTSIDE),
        replaced({"reserved_headings": []}, "payload", "reject invalid UTF-8 and BOM", "\ufefe\n[Driver API]", HEADING,
                 "\ufeff\n[Driver API]", OUTSIDE),
        replaced({"reserved_headings": []}, "payload", "any payload line", "[Driver API]", HEADING, "[Driver API] ", PASSED),
        replaced({"payload": "[Driver API]"}, "reserved_headings", "one of the nine reserved headings in the sidecar", NINE,
                 HEADING, [*NINE[:-1], "[Response schemas]"], OUTSIDE)],
    "adapt_rendered": [
        replaced({}, "rendered", "reject BOM and invalid sequences", "\ud7ff{{A}}", PLACEHOLDER, "\ud800{{A}}", OUTSIDE),
        replaced({}, "rendered", "reject BOM and invalid sequences", "\ufefe{{A}}", PLACEHOLDER, "\ufeff{{A}}", OUTSIDE),
        replaced({}, "rendered", "\\{\\{[A-Z0-9_]+\\}\\}", "{{A}}", PLACEHOLDER, "{{}}", PASSED),
        replaced({}, "rendered", "\\{\\{[A-Z0-9_]+\\}\\}", "{{_}}", PLACEHOLDER, "{{`}}", PASSED)],
    "adapt_runtime_signature": [replaced({}, "runtime_signature", term, edge, exp, out, BLOCKED + "not a File 30")
                                for term, edge, exp, out in (
        ("named `seed`", runtime_sig(), sig_fail("driver.py", "create_driver"), runtime_sig(expected=["seeds"])),
        ("`create_driver`", runtime_sig(), sig_fail("driver.py", "create_driver"), runtime_sig(symbol="create_drivers")),
        ("`driver.py`", runtime_sig(), sig_fail("driver.py", "create_driver"), runtime_sig(file="driver.p")),
        ("`self`, `cycle_index`, `outputs_after_edge`",
         runtime_sig(symbol="Driver.step", expected=["self", "cycle_index", "outputs_after_edge"]),
         sig_fail("driver.py", "Driver.step"),
         runtime_sig(symbol="Driver.step", expected=["self", "cycle_index", "outputs_after_edges"])),
        ("`trace` and `metadata`", runtime_sig("checker.py", "check_trace", ["trace"], ["trace", "metadata"]),
         sig_fail("checker.py", "check_trace"),
         runtime_sig("checker.py", "check_trace", ["trace"], ["trace", "metadatas"])))],
    "adapt_vector_keys": [
        replaced({"expected_keys": ["a"]}, "driver_return", "exact string `COMPLETE` or a dictionary", "COMPLETE", PASSED,
                 "COMPLETE ", repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=RETURN_TYPE")),
        replaced({"expected_keys": ["a"]}, "driver_return", "each value is a string", {"a": ""}, BLOCKED + "widths not supplied",
                 {"a": 0}, repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=NON_STRING_VALUE")),
        replaced({"driver_return": 7}, "expected_keys", "frozen top-level input-port set", ["p"],
                 repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=RETURN_TYPE"), [], OUTSIDE),
        replaced({"driver_return": 7}, "expected_keys", "frozen top-level input-port set", ["p", "q"],
                 repair("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", "DRIVER_VECTOR_INVALID|reason=RETURN_TYPE"), ["p", "p"], OUTSIDE)],
    "adapt_paired_runs": [
        replaced({}, "paired_runs", "next-input schedules", paired(1, 0), NEXT_INPUT, paired(1, -1), BLOCKED + "outside the contract"),
        replaced({}, "paired_runs", "first raw-output divergence", paired(0, 0), PASSED, paired(-1, 0),
                 BLOCKED + "outside the contract"),
        replaced({}, "paired_runs", "first raw output divergence", paired(1, 0), NEXT_INPUT, paired(0, 0), PASSED)],
}
