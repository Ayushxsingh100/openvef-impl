"""Stage-map rows after compilation, and multi-failure precedence.

Implements:
  Protocol §3.4 "Authoritative failure-to-stage map" (file 02 L141-L162) — rows,
                   error classes, diagnostics and dispositions; "The first applicable
                   row after the exact evaluation order below controls" (L139).
  Protocol §3.4 "Deterministic evaluation order" (L166) — steps (1)-(11); within a
                   cycle "exception wins over vector validation, which wins over
                   watchdog"; step (8) paired-run comparison; step (11) checker
                   adjudication.
  File 30 §3 L83 — driver vector checks (a)-(e) and their reason codes.
  File 30 §3 L97 — checker return classification order and diagnostic-item form.
  Catalog (file 36) L5-L16 — local dispositions.

Readings decided by Claude under the standing delegation (docs/ambiguities.md; approved
under D-009): A-025 the `events` vocabulary and precedence key; A-026 the checker
run-outcome records; A-027 driver-vector checks whose parameters are not supplied.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Iterable, Mapping, NamedTuple, Optional, Sequence

from openvef.envelope import Failure

REPAIR = "REPAIR"
TERMINAL = "TERMINAL_INVALID_NO_REPAIR"
HALT = "DESIGN_HALT_NO_SLOT_SCORED"
ACCEPT_WITH_WARNING = "ACCEPT_WITH_WARNING"

_EXCEPTION_CLASS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FILE_ORDER = ("driver.py", "checker.py")


def exception_class(name: Any) -> str:
    """`EXCEPTION_CLASS` (file 02 L125): the simple class name, else `Exception`."""
    return name if isinstance(name, str) and _EXCEPTION_CLASS.fullmatch(name) else "Exception"


# --- Events and precedence (A-025) ------------------------------------------------------

class Row(NamedTuple):
    step: int        # evaluation-order step (Protocol §3.4 L166)
    row: int         # stage-map row index (L141-L162): the first applicable row wins
    build: Callable[[Mapping[str, Any]], Failure]


def _f(stage: str, error_class: str, disposition: str = REPAIR):
    return lambda diagnostic: Failure(stage, error_class, diagnostic, disposition)


def _compile_error(e: Mapping[str, Any]) -> Failure:
    stage = {"driver.py": "COMPILE_DRIVER", "checker.py": "COMPILE_CHECKER"}[e["file"]]
    return Failure(stage, "COMPILE_ERROR", f"COMPILE_ERROR|file={e['file']}|line={int(e['line'])}")


# A-025: each event kind names one stage-map row. The step is the evaluation-order step
# in which that row's check runs; compile errors take step 5 (driver) or 6 (checker).
EVENT_ROWS: dict[str, Row] = {
    "schema_reject": Row(1, 0, lambda e: _f("PARSE_SCHEMA", "SCHEMA_REJECT")(f"SCHEMA_REJECT|pointer={e['pointer']}")),
    "output_truncated": Row(1, 1, lambda e: _f("PARSE_SCHEMA", "OUTPUT_TRUNCATED")("OUTPUT_TRUNCATED")),
    "import_not_allowed": Row(3, 4, lambda e: _f("IMPORT_POLICY", "IMPORT_POLICY_REJECT")(
        f"IMPORT_NOT_ALLOWED|module={e['module']}")),
    "compile_error": Row(5, 6, _compile_error),
    "driver_runtime": Row(7, 8, lambda e: _f("DRIVER_RUNTIME", "RUNTIME_EXCEPTION")(
        f"RUNTIME_EXCEPTION|file=driver.py|phase={e['phase']}|class={exception_class(e['exception_class'])}")),
    "driver_vector": Row(7, 9, lambda e: _f("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID")(
        f"DRIVER_VECTOR_INVALID|reason={e['reason']}")),
    "driver_watchdog": Row(7, 10, lambda e: _f("DRIVER_WATCHDOG", "WATCHDOG_TIMEOUT")("WATCHDOG_TIMEOUT|phase=driver_step")),
    "simulator_error": Row(7, 11, lambda e: _f("DESIGN_HALT", "EVALUATOR_INFRASTRUCTURE_FAILURE", HALT)(
        f"SIMULATOR_ERROR|target={e['target']}|class={exception_class(e['exception_class'])}")),
    "trace_integrity": Row(7, 12, lambda e: _f("DESIGN_HALT", "TRACE_INTEGRITY_FAILURE", HALT)(
        f"TRACE_INTEGRITY_FAILURE|reason={e['reason']}")),
}

_PHASES = {"factory", "step"}
_TARGETS = {"rtl", "null"}
_VECTOR_REASONS = ("RETURN_TYPE", "MISSING_KEYS", "EXTRA_KEYS", "NON_STRING_VALUE", "WRONG_WIDTH", "ILLEGAL_SYMBOL",
                   "ILLEGAL_PROTOCOL_STATE")
_TRACE_REASONS = {"REPLAY_HASH_MISMATCH", "MALFORMED_RECORDER_OUTPUT", "ROW_ALIGNMENT", "UNTRUSTED_TRACE_SERIALIZATION"}


class EventError(ValueError):
    """An event outside the vocabulary or with fields outside the enumerated domains."""


def _validate_event(e: Mapping[str, Any]) -> None:
    kind = e.get("kind")
    if kind not in EVENT_ROWS:
        raise EventError(f"unknown event kind {kind!r}")
    checks = {
        "compile_error": lambda: e["file"] in FILE_ORDER and type(e["line"]) is int and e["line"] >= 1,
        "driver_runtime": lambda: e["phase"] in _PHASES,
        "driver_vector": lambda: e["reason"] in _VECTOR_REASONS,
        "simulator_error": lambda: e["target"] in _TARGETS,
        "trace_integrity": lambda: e["reason"] in _TRACE_REASONS,
        "import_not_allowed": lambda: isinstance(e["module"], str) and e["module"] != "",
        "schema_reject": lambda: isinstance(e["pointer"], str) and e["pointer"].startswith("/"),
    }
    try:
        ok = checks.get(kind, lambda: True)()
    except (KeyError, TypeError) as exc:
        raise EventError(f"event {kind!r} lacks a field: {exc}") from exc
    if not ok:
        raise EventError(f"event {kind!r} has a field outside its domain")


def first_event(events: Sequence[Mapping[str, Any]]) -> Failure:
    """The controlling failure among several observed events (A-025).

    Key: (evaluation step, stage-map row, file order, line). Step decides first (the
    evaluation order is "exact"); within a step the first applicable row controls
    (L139), which gives exception > vector > watchdog within a cycle (L166 (7)).
    """
    if not events:
        raise EventError("no events")
    for e in events:
        _validate_event(e)

    def key(e: Mapping[str, Any]) -> tuple:
        row = EVENT_ROWS[e["kind"]]
        step = row.step + (1 if e["kind"] == "compile_error" and e["file"] == "checker.py" else 0)
        file = FILE_ORDER.index(e["file"]) if e.get("file") in FILE_ORDER else 0
        line = e["line"] if type(e.get("line")) is int else 0
        return (step, row.row, file, line)

    ranked = sorted(events, key=key)
    if len(ranked) > 1 and key(ranked[0]) == key(ranked[1]) and \
            EVENT_ROWS[ranked[0]["kind"]].build(ranked[0]) != EVENT_ROWS[ranked[1]["kind"]].build(ranked[1]):
        raise EventError("two different events share the first precedence key")
    return EVENT_ROWS[ranked[0]["kind"]].build(ranked[0])


# --- Paired-run comparison (L166 step (8)) ----------------------------------------------

def paired_run_failure(first_raw_output_divergence: Optional[int],
                       first_next_input_divergence: Optional[int]) -> Optional[Failure]:
    """"compare raw outputs before that row's next-input decision; any next-input
    mismatch before first raw-output divergence is terminal driver nondeterminism"."""
    if first_next_input_divergence is None:
        return None
    if first_raw_output_divergence is None or first_next_input_divergence < first_raw_output_divergence:
        return Failure("TERMINAL", "DRIVER_NONDETERMINISM", "DRIVER_NONDETERMINISM|reason=NEXT_INPUT_DIVERGENCE", TERMINAL)
    return None


RTL_NULL_CONTROL_FAILURE = Failure("DESIGN_HALT", "RTL_NULL_CONTROL_FAILURE",
                                   "RTL_NULL_CONTROL_FAILURE|reason=MASKED_OUTPUT_DIVERGENCE", HALT)


# --- Driver vector validation (File 30 §3 L83) ------------------------------------------

class NotDetermined(Exception):
    """A check that could decide the outcome lacks its parameters (A-027)."""


def _vector_reject(reason: str) -> Failure:
    return Failure("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", f"DRIVER_VECTOR_INVALID|reason={reason}")


def validate_vector(value: Any, ports: Iterable[str], widths: Optional[Mapping[str, int]] = None,
                    legal: Optional[Callable[[Mapping[str, str]], bool]] = None) -> Optional[Failure]:
    """None if `value` is `COMPLETE` or a valid vector.

    Order (File 30 L83 (a)-(e)): key set (missing keys before extra keys, the order of
    the reason enumeration), string values, width, `0`/`1` symbols, legal-input
    predicate. A-027: when `widths` or `legal` is not supplied, that check cannot be
    run; if every supplied check passes, the outcome is not determined.
    """
    if value == "COMPLETE":
        return None
    if not isinstance(value, dict):
        return _vector_reject("RETURN_TYPE")
    ports = set(ports)
    keys = set(value)
    if ports - keys:
        return _vector_reject("MISSING_KEYS")
    if keys - ports:
        return _vector_reject("EXTRA_KEYS")
    if not all(isinstance(v, str) for v in value.values()):
        return _vector_reject("NON_STRING_VALUE")
    if widths is None:
        raise NotDetermined("port widths not supplied")
    if any(len(value[k]) != widths[k] for k in value):
        return _vector_reject("WRONG_WIDTH")
    if any(c not in "01" for v in value.values() for c in v):
        return _vector_reject("ILLEGAL_SYMBOL")
    if legal is None:
        raise NotDetermined("legal-input predicate not supplied")
    return None if legal(value) else _vector_reject("ILLEGAL_PROTOCOL_STATE")


# --- Runtime signature (File 30 §3 L35/L37: "Runtime `inspect.signature` must confirm") --

def runtime_signature_failure(file: str, symbol: str, actual: Sequence[str], expected: Sequence[str]) -> Optional[Failure]:
    if list(actual) == list(expected):
        return None
    return Failure("AST_SIGNATURE", "ENTRY_POINT_REJECT", f"ENTRY_POINT_REJECT|file={file}|symbol={symbol}|reason=RUNTIME_SIGNATURE")


# --- Checker null runs (L166 steps (9)-(11); File 30 §3 L97) ----------------------------

class CheckerOutcome(NamedTuple):
    verdict: Optional[str]                 # "PASS"/"FAIL" for a valid return, else None
    error: Optional[tuple[str, str]]       # (error_class, diagnostic) for a checker error
    malformed_items: int = 0


def diagnostic_item_ok(item: Any) -> bool:
    """B7 (File 30 L74): exactly `code` (string), `message` (string), `cycle` (integer or
    null) and `clause_id` (string or null)."""
    return (isinstance(item, dict) and set(item) == {"code", "message", "cycle", "clause_id"}
            and isinstance(item["code"], str) and isinstance(item["message"], str)
            and (item["cycle"] is None or type(item["cycle"]) is int)
            and (item["clause_id"] is None or isinstance(item["clause_id"], str)))


def classify_return(value: Any) -> CheckerOutcome:
    """A real checker return, classified in File 30 L97's exact order."""
    def invalid(reason: str) -> CheckerOutcome:
        return CheckerOutcome(None, ("CHECKER_RETURN_INVALID", f"CHECKER_RETURN_INVALID|reason={reason}"))
    if not isinstance(value, dict):
        return invalid("NON_DICTIONARY")
    if "diagnostics" not in value:
        return invalid("MISSING_DIAGNOSTICS")
    if set(value) != {"verdict", "diagnostics"}:
        return invalid("TOP_LEVEL_KEYS")
    if value["verdict"] not in ("PASS", "FAIL") or not isinstance(value["verdict"], str):
        return invalid("INVALID_VERDICT")
    if not isinstance(value["diagnostics"], list):
        return invalid("DIAGNOSTICS_NOT_LIST")
    return CheckerOutcome(value["verdict"], None, sum(not diagnostic_item_ok(i) for i in value["diagnostics"]))


def checker_runtime_error(exc_class: Any) -> CheckerOutcome:
    return CheckerOutcome(None, ("CHECKER_RUNTIME_ERROR", f"CHECKER_RUNTIME_ERROR|class={exception_class(exc_class)}"))


CHECKER_TIMEOUT = CheckerOutcome(None, ("CHECKER_TIMEOUT", "CHECKER_TIMEOUT|phase=null_check"))
_RETURN_REASONS = {"NON_DICTIONARY", "TOP_LEVEL_KEYS", "INVALID_VERDICT", "MISSING_DIAGNOSTICS", "DIAGNOSTICS_NOT_LIST"}


def outcome_from_record(record: Mapping[str, Any]) -> CheckerOutcome:
    """A-026: a descriptor's checker run-outcome record.

    `{"timeout": true}` → timeout; `{"error_code": "CHECKER_RUNTIME_ERROR",
    "exception_class": C}` → runtime error; `{"type": "return_invalid", "reason": R}` →
    `CHECKER_RETURN_INVALID|reason=R`; `{"verdict": V[, "diagnostics": [...]]}` → a valid
    return with verdict V whose diagnostic items are checked for form.
    """
    keys = set(record)
    if keys == {"timeout"} and record["timeout"] is True:
        return CHECKER_TIMEOUT
    if keys == {"error_code", "exception_class"} and record["error_code"] == "CHECKER_RUNTIME_ERROR":
        return checker_runtime_error(record["exception_class"])
    if keys == {"type", "reason"} and record["type"] == "return_invalid" and record["reason"] in _RETURN_REASONS:
        return CheckerOutcome(None, ("CHECKER_RETURN_INVALID", f"CHECKER_RETURN_INVALID|reason={record['reason']}"))
    if keys in ({"verdict"}, {"verdict", "diagnostics"}) and record["verdict"] in ("PASS", "FAIL"):
        items = record.get("diagnostics", [])
        if not isinstance(items, list):
            raise EventError("diagnostics in a verdict record must be a list")
        return CheckerOutcome(record["verdict"], None, sum(not diagnostic_item_ok(i) for i in items))
    raise EventError(f"checker run record outside the A-026 vocabulary: {sorted(keys)}")


def adjudicate_checker(first: CheckerOutcome, second: CheckerOutcome) -> Optional[Failure]:
    """Step (11) and the CHECKER rows of the stage map. None means "validity continues".

    "both PASS continues; both FAIL triggers repair; identical error code and exact
    diagnostic bytes triggers checker repair; any disagreement is terminal." A
    malformed item with both verdicts PASS gives ACCEPT_WITH_WARNING (stage and error
    class null, diagnostic `DIAGNOSTIC_FORMAT_WARNING`, Catalog L10).
    """
    if first.error and second.error and first.error == second.error:
        error_class, diagnostic = first.error
        return Failure("CHECKER_NULL", error_class, diagnostic)
    if first.verdict == second.verdict == "FAIL":
        return Failure("CHECKER_NULL_REJECT", "CHECKER_NULL_REJECT",
                       "The checker returned FAIL on a legal null-netlist trace.")
    if first.verdict == second.verdict == "PASS":
        if first.malformed_items or second.malformed_items:
            return Failure(None, None, "DIAGNOSTIC_FORMAT_WARNING", ACCEPT_WITH_WARNING)
        return None
    return Failure("TERMINAL", "CHECKER_NONDETERMINISM", "CHECKER_NONDETERMINISM|reason=RUN_DISAGREEMENT", TERMINAL)
