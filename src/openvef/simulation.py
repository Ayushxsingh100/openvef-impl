"""Simulator-backed stages, Protocol §3.4 L166 (7)-(8), through the D-002 sandbox.

Implements:
  L166 (7) — "Execute `create_driver(seed)` and `Driver.step` on original RTL, then on
            null netlist; within each cycle, exception wins over vector validation,
            which wins over watchdog when observed at the same checkpoint. Factory
            return type and runtime signatures are checked immediately after factory
            construction." (sandbox/sim.py, sandbox/sim_cocotb.py; precedence by
            stage_map.first_event, A-025.)
  L166 (8) — "Compare the two completed traces: compare raw outputs before that row's
            next-input decision; any next-input mismatch before first raw-output
            divergence is terminal driver nondeterminism; a same-input masked output
            divergence is a design halt."

Not implemented here, because the inputs are owner materials or TO FREEZE:
  - the design materials themselves (FIFO RTL, null netlist, port manifest, reset
    sequence, legal-input predicate, cycle cap, safe-idle vector; Protocol L61-L64,
    L229, L542);
  - the observation mask (owner-written; Scope section) — `compare_runs` takes the set
    of observed output ports as a parameter;
  - L166 (9)-(11) on a real null trace: the checker-facing trace schema and metadata
    (`spec_version_sha256`, `trace_schema_version`) are TO FREEZE (L543).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from openvef.envelope import Failure
from openvef.sandbox import run_harness
from openvef.stage_map import RTL_NULL_CONTROL_FAILURE, NotDetermined, first_event, paired_run_failure

# Trace-row field names given by Protocol §5.2 L217-L219 (A-040).
INPUTS = "inputs_consumed_at_edge_n"
OUTPUTS = "outputs_after_edge_n"
NEXT = "next_inputs_scheduled_for_edge_n_plus_1"

DESIGN_FIELDS = ("toplevel", "verilog_sources", "clock_port", "input_ports", "output_ports", "reset_sequence",
                 "cycle_cap", "safe_idle", "legal_input_predicate")
# Optional: "held_inputs" {port: bits} — harness-owned inputs that are not driver-vector
# keys (A-042). Reset-sequence vectors must give them; they are held after reset release.


class SimulationError(RuntimeError):
    """The sandbox produced no adjudicable result (evaluator-side; recorded as ERROR)."""


def driver_run(driver_source: str, design: Mapping[str, Any], target: str, seed: int, *,
               step_timeout_s: float, budget_s: float) -> dict:
    """One run on one target in a fresh container. Returns the harness result."""
    missing = [f for f in DESIGN_FIELDS if f not in design]
    if missing:
        raise ValueError(f"design materials lack {missing}")
    r = run_harness({"task": "simulate", "driver_source": driver_source, "seed": seed, "target": target,
                     "design": dict(design), "step_timeout_s": step_timeout_s, "budget_s": budget_s},
                    timeout_s=budget_s + 20.0)
    if r.timed_out or r.result is None:
        raise SimulationError(f"no result from the simulation container (timed_out={r.timed_out}, "
                              f"exit {r.returncode}): {r.stderr_tail[-300:]}")
    return r.result


def run_outcome(result: Mapping[str, Any]) -> Optional[Failure]:
    """The controlling failure of one run (None if it completed without events)."""
    if "error" in result:
        raise SimulationError(result["error"])
    if "not_determined" in result:
        raise NotDetermined(result["not_determined"])
    if "failure" in result and "events" not in result:  # factory/return-type/signature rejection
        f = result["failure"]
        return Failure(f["stage_id"], f["error_class"], f["diagnostic"], f["disposition"])
    events = [{k: v for k, v in e.items() if k not in ("cycle", "detail")} for e in result["events"]]
    return first_event(events) if events else None


def compare_runs(rtl_rows: list, null_rows: list, observed_outputs: Iterable[str]) -> Optional[Failure]:
    """L166 (8) on two completed runs."""
    if len(rtl_rows) != len(null_rows):
        raise SimulationError("completed runs have different lengths")
    observed = set(observed_outputs)
    raw_div = next_div = masked_same_input = None
    for i, (a, b) in enumerate(zip(rtl_rows, null_rows)):
        if raw_div is None and a[OUTPUTS] != b[OUTPUTS]:
            raw_div = i
        if next_div is None and a[NEXT] != b[NEXT]:
            next_div = i
        same_inputs_so_far = next_div is None
        if masked_same_input is None and same_inputs_so_far and any(a[OUTPUTS][p] != b[OUTPUTS][p] for p in observed):
            masked_same_input = i
    nondeterminism = paired_run_failure(raw_div, next_div)
    if nondeterminism is not None:
        return nondeterminism
    if masked_same_input is not None:
        return RTL_NULL_CONTROL_FAILURE
    return None


def driver_stages(driver_source: str, rtl: Mapping[str, Any], null: Mapping[str, Any],
                  observed_outputs: Iterable[str], seed: int, *, step_timeout_s: float,
                  budget_s: float) -> Optional[Failure]:
    """L166 (7) on RTL then null, then (8). None means both runs completed and agree."""
    runs = []
    for target, design in (("rtl", rtl), ("null", null)):
        result = driver_run(driver_source, design, target, seed, step_timeout_s=step_timeout_s, budget_s=budget_s)
        failure = run_outcome(result)
        if failure is not None:
            return failure
        runs.append(result["rows"])
    return compare_runs(runs[0], runs[1], observed_outputs)
