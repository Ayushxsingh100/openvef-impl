"""Runner adapters that exist only under `--pack v1.3.7-candidate` (D-024; v1.3.7 CANDIDATE, not audited).

Each input contract is cited to the candidate pack (proposals/v1.3.7/pack, corrections C2, C5, C9), so these rows
are never in the v1.3.6 table: v1.3.6 has no text for these shapes (PD-02, PD-04, PD-06, PD-07, D-013).
Contracts: runner/adapter_contracts_v137.py. Vectors and boundary pairs: tests/adapter_vectors_v137.py, checked by
tests/test_dispatch_shapes_v137.py under the same rules as the v1.3.6 adapters (D-013, D-017).

A refusal raises NotDetermined, which the runner reports as NOT_IMPLEMENTED with the reason, exactly as its own
Blocked. This module does not import the runner.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from openvef.envelope import Failure
from openvef.ledger import lifecycle_expectation_candidate
from openvef.source_ast import syntax_reject
from openvef.stage_map import NotDetermined, validate_vector

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


# (required keys, optional keys, adapter): added to the runner's table for the candidate pack only.
ROWS = (
    ({"change_class"}, set(), adapt_change_class),
    ({"source_file", "syntax_error"}, set(), adapt_parser_unit_vector),
    ({"driver_return", "input_port_widths", "sampled_outputs", "legal_input_predicate"}, set(), adapt_legal_input),
)
