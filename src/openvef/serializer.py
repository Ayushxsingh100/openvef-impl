"""Feedback serializer: closed-grammar check, truncation, JSON serialization.

Implements:
  Protocol §3.4 "Normative diagnostic grammar" (file 02 L94-L123) and "Diagnostic value
                   enumerations" (L125-L127).
  Protocol §3.4 "Feedback serialization" (L168): (1) validate the complete diagnostic
                   against the closed grammar; (2) truncate to 2,048 UTF-8 bytes
                   including `...[TRUNCATED]`, on a code-point boundary; (3) serialize
                   `{stage_id, error_class, diagnostic}` as UTF-8, ensure_ascii=false,
                   two-space indent, LF, exactly one final LF.
  Catalog (file 36) L18 — `FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC`.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from openvef.envelope import Failure

BYTE_CAP = 2048
MARKER = "...[TRUNCATED]"
CHECKER_NULL_REJECT_SENTENCE = "The checker returned FAIL on a legal null-netlist trace."

# Value domains (file 02 L125-L127). Generic values: "ASCII, non-empty, and may not
# contain `|`, CR or LF" (L100).
_ANY = r"[\x20-\x7b\x7d\x7e]+"
_POS = r"[1-9][0-9]*"
_FILE = r"(?:driver\.py|checker\.py)"
_EXC = r"[A-Za-z_][A-Za-z0-9_]*"
_NAMES = r"(?:__import__|eval|exec|compile|open)"
_SYMBOL = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
_ROOT = r"[A-Za-z_][A-Za-z0-9_]*"


def _alt(*values: str) -> str:
    return "(?:" + "|".join(re.escape(v) for v in values) + ")"


_IMPORT_FORM = _alt("RELATIVE_IMPORT", "STAR_IMPORT", "FUTURE_FEATURE", "FROM_IMPORT_FORBIDDEN", "SUBMODULE_IMPORT",
                    "IMPORT_ALIAS", "MULTIPLE_NAMES")
_MODULE = _alt("MODULE_EXECUTABLE", "MODULE_CONTROL_FLOW", "NON_LITERAL_CONSTANT")
_ENTRY = _alt("MISSING_ENTRY_POINT", "PARAMETER_NAMES", "PARAMETER_KIND", "DEFAULT_OR_VARIADIC", "EXTRA_ENTRY_POINT",
              "WRONG_ENTRY_POINT_KIND", "CLASS_FORBIDDEN", "DRIVER_CLASS_FORM", "FORBIDDEN_METHOD",
              "NESTED_CLASS_FORBIDDEN", "ASYNC_DEFINITION", "ASYNC_COMPREHENSION", "RETURN_TYPE", "RUNTIME_SIGNATURE")
_VECTOR = _alt("RETURN_TYPE", "MISSING_KEYS", "EXTRA_KEYS", "NON_STRING_VALUE", "WRONG_WIDTH", "ILLEGAL_SYMBOL",
               "ILLEGAL_PROTOCOL_STATE")
_CHECKER_RETURN = _alt("NON_DICTIONARY", "TOP_LEVEL_KEYS", "INVALID_VERDICT", "MISSING_DIAGNOSTICS", "DIAGNOSTICS_NOT_LIST")
_TRACE = _alt("REPLAY_HASH_MISMATCH", "MALFORMED_RECORDER_OUTPUT", "ROW_ALIGNMENT", "UNTRUSTED_TRACE_SERIALIZATION")
# GLOBAL_RANDOM_USE.name: "a prohibited module-global attribute such as ..." -- any
# `random.<identifier>` other than `random.Random`.
_RANDOM_NAME = r"random\.(?!Random$)[A-Za-z_][A-Za-z0-9_]*"

GRAMMAR = [re.compile(p) for p in (
    rf"SCHEMA_REJECT\|pointer=/(?:{_ANY})?",
    r"OUTPUT_TRUNCATED",
    rf"SOURCE_EMPTY\|file={_FILE}",
    rf"SOURCE_SYNTAX_REJECT\|file={_FILE}\|line={_POS}\|column={_POS}",
    rf"IMPORT_NOT_ALLOWED\|module={_ROOT}",
    rf"IMPORT_FORM_REJECT\|file={_FILE}\|line={_POS}\|reason={_IMPORT_FORM}",
    rf"NON_ASCII_IDENTIFIER\|file={_FILE}\|line={_POS}\|column={_POS}",
    rf"PROHIBITED_BUILTIN\|name={_NAMES}",
    rf"GLOBAL_RANDOM_USE\|name={_RANDOM_NAME}",
    rf"MODULE_STATEMENT_REJECT\|file={_FILE}\|line={_POS}\|reason={_MODULE}",
    rf"DECORATOR_REJECT\|file={_FILE}\|symbol={_SYMBOL}",
    rf"ENTRY_POINT_REJECT\|file={_FILE}\|symbol={_SYMBOL}\|reason={_ENTRY}",
    rf"COMPILE_ERROR\|file=driver\.py\|line={_POS}",
    rf"COMPILE_ERROR\|file=checker\.py\|line={_POS}",
    rf"RUNTIME_EXCEPTION\|file=driver\.py\|phase=(?:factory|step)\|class={_EXC}",
    rf"DRIVER_VECTOR_INVALID\|reason={_VECTOR}",
    r"WATCHDOG_TIMEOUT\|phase=driver_step",
    r"DRIVER_NONDETERMINISM\|reason=NEXT_INPUT_DIVERGENCE",
    rf"TRACE_INTEGRITY_FAILURE\|reason={_TRACE}",
    r"RTL_NULL_CONTROL_FAILURE\|reason=MASKED_OUTPUT_DIVERGENCE",
    rf"SIMULATOR_ERROR\|target=(?:rtl|null)\|class={_EXC}",
    rf"CHECKER_RUNTIME_ERROR\|class={_EXC}",
    rf"CHECKER_RETURN_INVALID\|reason={_CHECKER_RETURN}",
    r"CHECKER_TIMEOUT\|phase=null_check",
    re.escape(CHECKER_NULL_REJECT_SENTENCE),
    r"CHECKER_NONDETERMINISM\|reason=RUN_DISAGREEMENT",
)]


# Authoritative stage map, file 02 L143-L162: (stage, error class, diagnostic codes). The
# fixed sentence and the bare token count as their own code.
STAGE_MAP: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("PARSE_SCHEMA", "SCHEMA_REJECT", ("SCHEMA_REJECT",)),                                              # L143
    ("PARSE_SCHEMA", "OUTPUT_TRUNCATED", ("OUTPUT_TRUNCATED",)),                                        # L144
    ("SOURCE_AST", "SOURCE_SYNTAX_REJECT", ("SOURCE_SYNTAX_REJECT",)),                                  # L145
    ("SOURCE_AST", "SOURCE_EMPTY", ("SOURCE_EMPTY",)),                                                  # L146
    ("IMPORT_POLICY", "IMPORT_POLICY_REJECT", ("IMPORT_NOT_ALLOWED", "IMPORT_FORM_REJECT", "NON_ASCII_IDENTIFIER",
                                               "PROHIBITED_BUILTIN", "GLOBAL_RANDOM_USE",
                                               "MODULE_STATEMENT_REJECT")),                             # L147
    ("AST_SIGNATURE", "ENTRY_POINT_REJECT", ("ENTRY_POINT_REJECT", "DECORATOR_REJECT")),                # L148
    ("COMPILE_DRIVER", "COMPILE_ERROR", ("COMPILE_ERROR|file=driver.py",)),                             # L149
    ("COMPILE_CHECKER", "COMPILE_ERROR", ("COMPILE_ERROR|file=checker.py",)),                           # L150
    ("DRIVER_RUNTIME", "RUNTIME_EXCEPTION", ("RUNTIME_EXCEPTION",)),                                    # L151
    ("DRIVER_VECTOR", "DRIVER_VECTOR_INVALID", ("DRIVER_VECTOR_INVALID",)),                             # L152
    ("DRIVER_WATCHDOG", "WATCHDOG_TIMEOUT", ("WATCHDOG_TIMEOUT",)),                                     # L153
    ("DESIGN_HALT", "EVALUATOR_INFRASTRUCTURE_FAILURE", ("SIMULATOR_ERROR",)),                          # L154
    ("DESIGN_HALT", "TRACE_INTEGRITY_FAILURE", ("TRACE_INTEGRITY_FAILURE",)),                           # L155
    ("TERMINAL", "DRIVER_NONDETERMINISM", ("DRIVER_NONDETERMINISM",)),                                  # L156
    ("DESIGN_HALT", "RTL_NULL_CONTROL_FAILURE", ("RTL_NULL_CONTROL_FAILURE",)),                         # L157
    ("CHECKER_NULL", "CHECKER_RUNTIME_ERROR", ("CHECKER_RUNTIME_ERROR",)),                              # L158
    ("CHECKER_NULL", "CHECKER_RETURN_INVALID", ("CHECKER_RETURN_INVALID",)),                            # L158
    ("CHECKER_NULL", "CHECKER_TIMEOUT", ("CHECKER_TIMEOUT",)),                                          # L158
    ("CHECKER_NULL_REJECT", "CHECKER_NULL_REJECT", (CHECKER_NULL_REJECT_SENTENCE,)),                    # L159
    ("TERMINAL", "CHECKER_NONDETERMINISM", ("CHECKER_NONDETERMINISM",)),                                # L161
)


def in_stage_map(stage_id: object, error_class: object, diagnostic: object) -> bool:
    """True only if one stage-map row emits exactly this (stage, error class, diagnostic)."""
    return in_grammar(diagnostic) and any(
        (stage_id, error_class) == (stage, cls) and any(diagnostic == c or diagnostic.startswith(c + "|") for c in codes)
        for stage, cls, codes in STAGE_MAP)


def in_grammar(diagnostic: str) -> bool:
    return isinstance(diagnostic, str) and any(p.fullmatch(diagnostic) for p in GRAMMAR)


NON_NORMATIVE = Failure("FEEDBACK_SERIALIZER", "FEEDBACK_SERIALIZER_REJECT",
                        "FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC", "CONTROL_EXPECTATION")


def check_diagnostic(diagnostic: str, emitted: Optional[list[str]] = None) -> Optional[Failure]:
    """Step (1). A-029 (decided by Claude, approved under D-009): when the set of
    diagnostics the stage map emitted is supplied, the diagnostic must also be one of
    them ("accepts only a complete diagnostic emitted by the authoritative stage map")."""
    if not in_grammar(diagnostic) or (emitted is not None and diagnostic not in emitted):
        return NON_NORMATIVE
    return None


def truncate(diagnostic: str, cap: int = BYTE_CAP, marker: str = MARKER) -> str:
    """Step (2): longest code-point prefix whose bytes plus the marker fit in `cap`."""
    data = diagnostic.encode("utf-8")
    if len(data) <= cap:
        return diagnostic
    budget = cap - len(marker.encode("utf-8"))
    out, used = [], 0
    for ch in diagnostic:
        n = len(ch.encode("utf-8"))
        if used + n > budget:
            break
        out.append(ch)
        used += n
    return "".join(out) + marker


def _serialize_object(stage_id: str, error_class: str, diagnostic: str) -> bytes:
    """Step (3) alone, for the primitive's own unit test: the three-key object, UTF-8, ensure_ascii=false, indent 2, LF, one final LF."""
    text = json.dumps({"stage_id": stage_id, "error_class": error_class, "diagnostic": diagnostic},
                      ensure_ascii=False, indent=2)
    return (text + "\n").encode("utf-8")


def feedback_bytes(failure: Failure) -> Optional[bytes]:
    """Steps (1)-(3) for one stage-map failure; None unless the authoritative stage map emits
    exactly this (stage, error class, diagnostic) (L168; D-015, audit A4-1)."""
    return serialize(failure.stage_id, failure.error_class, failure.diagnostic)


def serialize(stage_id: str, error_class: str, diagnostic: str) -> Optional[bytes]:
    """The only way to feedback bytes: validate the full tuple, truncate, serialize."""
    if not in_stage_map(stage_id, error_class, diagnostic):
        return None
    return _serialize_object(stage_id, error_class, truncate(diagnostic))
