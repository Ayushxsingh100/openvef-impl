"""Paired null/mutant runs and their comparison (Protocol §8, §12) — H2.

Implements:
  L257-L263 — the same deterministic driver on the null netlist and, independently, on the
              mutant, with identical seed, reset, simulator, cap, safe-idle, driver API
              and watchdog; the driver reacts to the implementation it runs on.
  L265      — "Before the first raw output divergence, paired next-input decisions must
              match ... Within each row, raw outputs are compared before the next-input
              decision; a same-row divergence is output-first. A next-input divergence in
              an earlier row is INVALID_PAIR."
  L273      — mask windows are evaluated on the null-netlist row for both members.
  L306-L307, L328 — for a truncated run, whether a masked divergence was recorded before
              termination; checkers never run on truncated traces.
  L311      — predeclared integrity failures (row alignment, unequal complete lengths,
              a null run that did not complete) make the pair INVALID_PAIR.
  L336      — "A null run must complete within its watchdog for a mutant-run timeout to
              be interpreted."

Readings decided under the standing delegation (approved under D-009): A-046 (event
mapping), A-047 (null-run failure in a pair), A-048 (one checker invocation per pair).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from openvef import pairs as P
from openvef import trace as trace_mod
from openvef.simulation import NEXT, OUTPUTS, SimulationError, mask_comparator

# A-046: mutant-run harness events → §12 termination.
DRIVER_SIM_EVENTS = ("driver_runtime", "driver_vector", "simulator_error")
TIMEOUT_EVENTS = ("driver_watchdog",)
INTEGRITY_EVENTS = ("trace_integrity",)


def _status(result: dict) -> tuple[str, Optional[str]]:
    """(termination, integrity reason) for one harness simulation result."""
    if "error" in result or "not_determined" in result:
        raise SimulationError(f"evaluator-side failure, not a pair outcome: {result.get('error') or result.get('not_determined')}")
    if "failure" in result and "events" not in result:
        raise SimulationError("factory/signature rejection in a pair run: the artifact is not valid")
    kinds = [e["kind"] for e in result.get("events", [])]
    if any(k in INTEGRITY_EVENTS for k in kinds):
        return "INTEGRITY", "trace_integrity event: " + ",".join(e.get("reason", "") for e in result["events"])
    if any(k in DRIVER_SIM_EVENTS for k in kinds):
        return P.DRIVER_SIM_ERROR, None
    if any(k in TIMEOUT_EVENTS for k in kinds):
        return P.TIMEOUT, None
    if kinds:
        raise SimulationError(f"unknown harness events {kinds}")
    if result.get("run_status") != "COMPLETE_TRACE":
        return "INTEGRITY", f"run_status {result.get('run_status')!r} without an event"
    return P.COMPLETE, None


def compare_pair(null_result: dict, mutant_result: dict, mask: list) -> dict:
    """Row-by-row comparison of a null run and a mutant run (L265, L273)."""
    null_term, null_reason = _status(null_result)
    mut_term, mut_reason = _status(mutant_result)
    out: dict[str, Any] = {"termination": mut_term if mut_term != "INTEGRITY" else P.COMPLETE,
                           "integrity_failure": False, "integrity_reason": None}
    if null_term != P.COMPLETE:  # A-047, L311, L336
        out.update(integrity_failure=True, integrity_reason=f"null run did not complete: {null_term} {null_reason or ''}".strip())
    elif mut_term == "INTEGRITY":
        out.update(integrity_failure=True, integrity_reason=mut_reason)
    null_rows, mut_rows = null_result.get("rows") or [], mutant_result.get("rows") or []
    if not out["integrity_failure"] and mut_term == P.COMPLETE and len(null_rows) != len(mut_rows):
        out.update(integrity_failure=True, integrity_reason="complete traces of different lengths")
    differs = mask_comparator(mask)
    raw = masked = nxt = None
    for i, (a, b) in enumerate(zip(null_rows, mut_rows)):
        if raw is None and a[OUTPUTS] != b[OUTPUTS]:
            raw = i
        if masked is None and differs(a[OUTPUTS], b[OUTPUTS], a[OUTPUTS]):
            masked = i
        # A failure or cap row has no next-input decision (null); only decisions are compared.
        if nxt is None and a[NEXT] is not None and b[NEXT] is not None and a[NEXT] != b[NEXT]:
            nxt = i
    out.update(first_raw_row=raw, first_masked_row=masked, first_next_input_row=nxt,
               raw_divergence=raw is not None, masked_divergence=masked is not None,
               next_input_before_raw=nxt is not None and (raw is None or nxt < raw),
               rows_compared=min(len(null_rows), len(mut_rows)), null_rows=len(null_rows), mutant_rows=len(mut_rows),
               mutant_events=mutant_result.get("events", []))
    return out


def observation(pair: dict, checker: Optional[str]) -> P.PairObservation:
    complete_valid = (pair["termination"] == P.COMPLETE and not pair["integrity_failure"]
                      and not pair["next_input_before_raw"])
    return P.PairObservation(integrity_failure=pair["integrity_failure"],
                             next_input_before_raw=pair["next_input_before_raw"],
                             termination=pair["termination"], raw_divergence=pair["raw_divergence"],
                             masked_divergence=pair["masked_divergence"],
                             checker=checker if complete_valid else None)


def checker_result(outcome: Any) -> str:
    """PASS, FAIL or ERROR from a runtime.checker_invocation result."""
    verdict = getattr(outcome, "verdict", None)
    return verdict if verdict in ("PASS", "FAIL") else "ERROR"


def run_pair(driver_source: str, null: dict, mutant: dict, mutant_id: str, seed: int, mask: list, *,
             timeout_s: float, run: Callable, checker_source: Optional[str] = None,
             metadata: Optional[dict] = None, invoke: Optional[Callable] = None) -> dict:
    """One valid artifact × mutant pair. `run(driver_source, design, target, seed, step_timeout_s=,
    budget_s=)` is openvef.simulation.driver_run; `invoke(checker_source, trace, metadata)` is
    openvef.runtime.checker_invocation. Returns the comparison, the class and hashes."""
    r_null = run(driver_source, null, "null", seed, step_timeout_s=timeout_s, budget_s=timeout_s)
    r_mut = run(driver_source, mutant, f"mutant:{mutant_id}", seed, step_timeout_s=timeout_s, budget_s=timeout_s)
    pair = compare_pair(r_null, r_mut, mask)
    record: dict[str, Any] = {"mutant": mutant_id, "seed": seed, "timeout_s": timeout_s,
                              "comparison": {k: v for k, v in pair.items() if k != "mutant_events"},
                              "mutant_events": pair["mutant_events"]}
    checker = None
    complete_valid = (pair["termination"] == P.COMPLETE and not pair["integrity_failure"]
                      and not pair["next_input_before_raw"])
    if complete_valid:
        frozen_null, frozen_mut = trace_mod.freeze(r_null["rows"]), trace_mod.freeze(r_mut["rows"])
        record.update(null_trace_sha256=frozen_null.sha256, mutant_trace_sha256=frozen_mut.sha256,
                      byte_identical_to_null=frozen_null.data == frozen_mut.data)
        if checker_source is not None:
            outcome = invoke(checker_source, frozen_mut.decoded(), dict(metadata or {}))  # A-048: once
            if not frozen_mut.verify():
                raise SimulationError("mutant trace bytes changed during the checker invocation")
            checker = checker_result(outcome)
            record["checker"] = checker
    if checker_source is not None or not complete_valid:
        obs = observation(pair, checker)
        record["class"] = P.classify(obs)
        record["np_subtype"] = P.np_subtype(obs)
    return record
