"""Pair outcome partition and classification precedence (Protocol §12, §13.2) — H3.

Implements:
  L303-L309 — "Every scheduled slot × primary-mutant combination receives exactly one
              ledger outcome. For valid artifacts, apply this precedence: 1. INVALID_PAIR
              ... 2. Driver/simulator error ... 3. Wall-clock timeout ... 4. Offline
              checker error ... 5. Normal-completion outcomes and anomalies."
  L311      — integrity adjudication: a predeclared harness/trace-integrity failure is
              INVALID_PAIR; a checker-attributable failure stays in T_i as an anomaly;
              an undetermined cause is INVALID_PAIR.
  L313-L326 — the normal, anomaly and error/timeout classes.
  L328      — INVALID_ARTIFACT_SLOT for every scheduled mutant of an invalid slot.
  L370-L384 — the outcome-class inclusion table (INCLUSION, checked verbatim against the
              pack by tests/test_pairs.py).
  L392      — NP subtypes NP_NO_RAW_DIVERGENCE and NP_RAW_ONLY_UNMASKED.

An observation is what the pair runner (openvef.pair_runner) measured; this module only
classifies it. Nothing here depends on a design, fixture or control.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DETECTED = "DETECTED"
PND = "PND"
NP = "NP"
ANOMALY_PIPELINE = "ANOMALY_PIPELINE_OR_NONDETERMINISM"
ANOMALY_STRICTER = "ANOMALY_CHECKER_STRICTER_THAN_MASK"
CHECKER_ERROR_NO_MASKED = "CHECKER_ERROR_NO_MASKED_DIVERGENCE"
CHECKER_ERROR_AFTER_MASKED = "CHECKER_ERROR_AFTER_MASKED_DIVERGENCE"
INVALID_PAIR = "INVALID_PAIR"
DRIVER_SIM_NO_MASKED = "DRIVER_SIM_ERROR_NO_MASKED_DIVERGENCE"
DRIVER_SIM_AFTER_MASKED = "DRIVER_SIM_ERROR_AFTER_MASKED_DIVERGENCE"
TIMEOUT_NO_MASKED = "TIMEOUT_WITHOUT_MASKED_DIVERGENCE"
TIMEOUT_AFTER_MASKED = "TIMEOUT_AFTER_MASKED_DIVERGENCE"
INVALID_ARTIFACT_SLOT = "INVALID_ARTIFACT_SLOT"

NP_NO_RAW = "NP_NO_RAW_DIVERGENCE"
NP_RAW_ONLY = "NP_RAW_ONLY_UNMASKED"

# Protocol L370-L384, one row per class, columns in table order:
# (complete trace / valid pair, in T_i, masked exposure known, in X_i, in DET_i,
#  in primary J_exposure, in primary J_detection). Cell text is kept verbatim so the
# test can compare it with the pack line by line.
INCLUSION = {
    DETECTED: ("Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"),
    PND: ("Yes", "Yes", "Yes", "Yes", "No", "Yes", "No"),
    NP: ("Yes", "Yes", "No", "No", "No", "No", "No"),
    ANOMALY_PIPELINE: ("Yes", "Yes", "No", "No", "No", "No", "No"),
    ANOMALY_STRICTER: ("Yes", "Yes", "No (raw-only divergence)", "No", "No", "No", "No"),
    CHECKER_ERROR_NO_MASKED: ("Yes", "Yes", "No", "No", "No", "No", "No"),
    CHECKER_ERROR_AFTER_MASKED: ("Yes", "Yes", "Yes", "Yes", "No", "Yes", "No"),
    INVALID_PAIR: ("Not an eligible paired observation", "No", "Not scored", "No", "No", "No", "No"),
    DRIVER_SIM_NO_MASKED: ("No (truncated)", "No", "No", "No", "No", "No", "No"),
    DRIVER_SIM_AFTER_MASKED: ("No (truncated)", "No", "Known before termination", "No (primary)", "No",
                              "No (primary)", "No"),
    TIMEOUT_NO_MASKED: ("No (truncated)", "No", "No", "No", "No", "No", "No"),
    TIMEOUT_AFTER_MASKED: ("No (truncated)", "No", "Known before timeout", "No (primary)", "No", "No (primary)",
                           "No"),
    INVALID_ARTIFACT_SLOT: ("No artifact / no valid pair", "No", "Not scored", "No", "No", "No", "No"),
}
PAIR_CLASSES = tuple(c for c in INCLUSION if c != INVALID_ARTIFACT_SLOT)
TRUNCATED = (DRIVER_SIM_NO_MASKED, DRIVER_SIM_AFTER_MASKED, TIMEOUT_NO_MASKED, TIMEOUT_AFTER_MASKED)
TRUNCATED_AFTER_MASKED = (DRIVER_SIM_AFTER_MASKED, TIMEOUT_AFTER_MASKED)

COMPLETE = "COMPLETE"
DRIVER_SIM_ERROR = "DRIVER_SIM_ERROR"
TIMEOUT = "TIMEOUT"
TERMINATIONS = (COMPLETE, DRIVER_SIM_ERROR, TIMEOUT)
CHECKER_RESULTS = ("PASS", "FAIL", "ERROR")


def flag(cls: str, column: int) -> bool:
    """True when the inclusion-table cell starts with "Yes" (column index as in INCLUSION)."""
    return INCLUSION[cls][column].startswith("Yes")


IN_T, IN_X, IN_DET, IN_J_EXPOSURE, IN_J_DETECTION = 1, 3, 4, 5, 6


@dataclass(frozen=True)
class PairObservation:
    """What was measured for one valid artifact × mutant pair.

    integrity_failure: a predeclared harness/trace-integrity rule was violated (L311),
        or the cause of a failure could not be determined from predeclared evidence;
    next_input_before_raw: the paired next-input schedules diverged in a row before the
        first raw output divergence (L265);
    termination: COMPLETE (cycle cap reached), DRIVER_SIM_ERROR or TIMEOUT;
    raw_divergence / masked_divergence: over the complete trace, or over the rows
        recorded before termination for a truncated run (L306-L307);
    checker: the verdict on the complete mutant trace — PASS, FAIL or ERROR; None for a
        truncated trace ("Checkers are never run on truncated traces", L328).
    """
    integrity_failure: bool
    next_input_before_raw: bool
    termination: str
    raw_divergence: bool
    masked_divergence: bool
    checker: Optional[str]

    def __post_init__(self) -> None:
        if self.termination not in TERMINATIONS:
            raise ValueError(f"termination {self.termination!r}")
        if self.masked_divergence and not self.raw_divergence:
            raise ValueError("a masked divergence is also a raw divergence")
        if self.termination == COMPLETE and not self.integrity_failure and not self.next_input_before_raw:
            if self.checker not in CHECKER_RESULTS:
                raise ValueError("a complete valid trace needs a checker result")
        if self.termination != COMPLETE and self.checker is not None:
            raise ValueError("checkers are never run on truncated traces (L328)")


def classify(o: PairObservation) -> str:
    """Exactly one class, by the L303-L309 precedence."""
    if o.integrity_failure or o.next_input_before_raw:  # 1
        return INVALID_PAIR
    if o.termination == DRIVER_SIM_ERROR:  # 2
        return DRIVER_SIM_AFTER_MASKED if o.masked_divergence else DRIVER_SIM_NO_MASKED
    if o.termination == TIMEOUT:  # 3
        return TIMEOUT_AFTER_MASKED if o.masked_divergence else TIMEOUT_NO_MASKED
    if o.checker == "ERROR":  # 4
        return CHECKER_ERROR_AFTER_MASKED if o.masked_divergence else CHECKER_ERROR_NO_MASKED
    # 5: normal outcomes (L314-L318)
    if o.checker == "FAIL":
        if o.masked_divergence:
            return DETECTED
        return ANOMALY_STRICTER if o.raw_divergence else ANOMALY_PIPELINE
    return PND if o.masked_divergence else NP


def np_subtype(o: PairObservation) -> Optional[str]:
    """L392: NP_NO_RAW_DIVERGENCE or NP_RAW_ONLY_UNMASKED for an NP pair, else None."""
    if classify(o) != NP:
        return None
    return NP_RAW_ONLY if o.raw_divergence else NP_NO_RAW
