"""Design-lifecycle ledger: halt signatures and the single recovery cycle (Protocol §7b).

Implements:
  Protocol L183-L185 — design-local halt after slots have begun; one recovery cycle per
                   affected design (operational recovery or evaluator revision); halt
                   signature `(design_id, halt_code, evaluator_component,
                   stable_error_class, stable_diagnostic_code)` with exact component
                   domains and the reason-to-component mapping; termination with
                   `DESIGN_HALT_REPEATED|reason=EVALUATOR_FAILURE_REPRODUCED` or
                   `|reason=SECOND_HALT_AFTER_RECOVERY`; every scheduled slot in scope is
                   `DESIGN_ABORTED_NO_SLOTS_SCORED`.
  Protocol L175 (closed lifecycle vocabulary) — `RERUN_ALL_SCHEDULED_SLOTS_WITH_SAME_
                   FROZEN_ARTIFACTS` (error class `MID_RUN_REEVALUATION`) for a successful
                   operational recovery.

A-031 (decided by Claude, owner review pending): `HaltSignature.build` enforces the
L185 domains for signatures the ledger constructs from halt events. Signatures supplied
ready-made (as in a descriptor) are compared for identity as given, because recurrence
detection needs only tuple equality.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, NamedTuple, Optional

from openvef.envelope import Failure

DESIGN_IDS = ("FIFO", "UART")
HALT_CODES = ("SIMULATOR_ERROR", "TRACE_INTEGRITY_FAILURE", "RTL_NULL_CONTROL_FAILURE")
EVALUATOR_COMPONENTS = ("SIMULATOR", "REPLAY_VERIFIER", "RECORDER", "TRACE_ALIGNMENT_CHECKER", "TRACE_SERIALIZER",
                        "RTL_NULL_COMPARATOR")
TRACE_REASON_COMPONENT = {
    "REPLAY_HASH_MISMATCH": "REPLAY_VERIFIER",
    "MALFORMED_RECORDER_OUTPUT": "RECORDER",
    "ROW_ALIGNMENT": "TRACE_ALIGNMENT_CHECKER",
    "UNTRUSTED_TRACE_SERIALIZATION": "TRACE_SERIALIZER",
}
_EXC = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SIGNATURE_FIELDS = ("design_id", "halt_code", "evaluator_component", "stable_error_class", "stable_diagnostic_code")

ABORTED = "DESIGN_ABORTED_NO_SLOTS_SCORED"


class HaltSignature(NamedTuple):
    design_id: str
    halt_code: str
    evaluator_component: str
    stable_error_class: str
    stable_diagnostic_code: str

    @classmethod
    def build(cls, design_id: str, halt_code: str, *, exception_class: Optional[str] = None,
              trace_reason: Optional[str] = None) -> "HaltSignature":
        """Construct a signature from a halt event, enforcing the L185 domains."""
        if design_id not in DESIGN_IDS or halt_code not in HALT_CODES:
            raise ValueError("design_id or halt_code outside its domain")
        if halt_code == "SIMULATOR_ERROR":
            if not (isinstance(exception_class, str) and _EXC.fullmatch(exception_class)):
                raise ValueError("SIMULATOR_ERROR needs a simple exception class name")
            return cls(design_id, halt_code, "SIMULATOR", exception_class, halt_code)
        if halt_code == "TRACE_INTEGRITY_FAILURE":
            return cls(design_id, halt_code, TRACE_REASON_COMPONENT[trace_reason], "NONE", halt_code)
        return cls(design_id, halt_code, "RTL_NULL_COMPARATOR", "NONE", halt_code)

    @classmethod
    def given(cls, record: Mapping[str, Any]) -> "HaltSignature":
        """A ready-made signature: exactly the five components, compared as given."""
        if set(record) != set(SIGNATURE_FIELDS):
            raise ValueError(f"halt signature must have exactly {SIGNATURE_FIELDS}")
        return cls(*(record[f] for f in SIGNATURE_FIELDS))


def halt_after_recovery(first: HaltSignature, second: HaltSignature, recovery_cycles_used: int) -> Failure:
    """A design halt after the single recovery cycle terminates the design (L185)."""
    if recovery_cycles_used != 1:
        raise ValueError("this rule applies to a halt after the one recovery cycle")
    reason = "EVALUATOR_FAILURE_REPRODUCED" if first == second else "SECOND_HALT_AFTER_RECOVERY"
    return Failure("DESIGN_HALT", "DESIGN_HALT_REPEATED", f"DESIGN_HALT_REPEATED|reason={reason}", ABORTED)


class OperationalRecovery(NamedTuple):
    """The control expectation of a successful operational recovery (L175, L183-L185)."""
    failure: Failure
    discard_pre_halt_scores: bool      # "Discard all pre-halt partial scores"
    rerun_slots: int                   # "re-evaluate every scheduled slot in the affected scope"
    reuse_same_artifact_bytes: bool    # "with the same frozen artifact bytes and slot seeds"
    new_confirmatory_generation_calls: int  # "no confirmatory generation call is made"


def operational_recovery(*, scheduled_slots: int, frozen_evaluator_hashes_unchanged: bool, same_artifact_bytes: bool,
                         same_slot_seeds: bool, author_visible_materials_changed: bool,
                         new_generation_calls: int, f16_required: bool) -> Optional[OperationalRecovery]:
    """None unless every operational-recovery condition of L183 holds.

    Operational recovery uses "the exact same frozen source, binaries, ... configuration";
    "it creates no new hashes, requires no new F16 and changes no artifact".
    """
    if not (frozen_evaluator_hashes_unchanged and same_artifact_bytes and same_slot_seeds
            and not author_visible_materials_changed and new_generation_calls == 0 and not f16_required):
        return None
    failure = Failure("DESIGN_HALT", "MID_RUN_REEVALUATION", "RERUN_ALL_SCHEDULED_SLOTS_WITH_SAME_FROZEN_ARTIFACTS",
                      "CONTROL_EXPECTATION")
    return OperationalRecovery(failure, True, scheduled_slots, True, 0)
