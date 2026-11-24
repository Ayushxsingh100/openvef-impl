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
