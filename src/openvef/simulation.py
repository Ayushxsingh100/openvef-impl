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

Also implemented (DRAFT materials under D-005; frozen values pending):
  - check (e) with an executable design-pack predicate (sandbox/sim_cocotb.py, A-041);
  - the L334 timeout, per run and per step (`l334_timeout`, A-043, D-006);
  - `simulate_pair`, which keeps the null trace for L166 (9)-(10).
The design materials themselves come from openvef.design_materials; the observation mask
is passed in as the comparison.
"""
from __future__ import annotations

import statistics
import time
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


# Protocol L334: "Proposed timeout: `T_timeout = max(5 × median(null-netlist wall time over
# 3 runs for the same artifact/design), 2 seconds)`." Applied per run, and as the per-step
# watchdog bound (proposal item 9, approved under D-006; frozen values pending).
L334_FACTOR = 5.0
L334_FLOOR_S = 2.0
# Build default, not from the pack: the limit for the three calibration runs themselves.
CALIBRATION_CEILING_S = 120.0


def l334_timeout(driver_source: str, null: Mapping[str, Any], seed: int) -> dict:
    """Three null-netlist runs of this artifact; T_timeout from their wall times (A-043).

    Wall time is the evaluator's elapsed time for one complete null-netlist driver run
    (one sandbox container). The calibration runs' outcomes are not used, only their
    wall times; a calibration run that hits the ceiling counts as the ceiling."""
    walls = []
    for _ in range(3):
        start = time.monotonic()
        driver_run(driver_source, null, "null", seed, step_timeout_s=CALIBRATION_CEILING_S,
                   budget_s=CALIBRATION_CEILING_S)
        walls.append(round(time.monotonic() - start, 3))
    median = statistics.median(walls)
    return {"wall_times_s": walls, "median_s": median,
            "t_timeout_s": round(max(L334_FACTOR * median, L334_FLOOR_S), 3),
            "rule": "Protocol L334, per run and per step (D-006); wall time per A-043"}


def simulate_pair(driver_source: str, rtl: Mapping[str, Any], null: Mapping[str, Any], seed: int,
                  compare, *, timeout_s: float) -> dict:
    """L166 (7) on RTL then null, then (8) through `compare(rtl_rows, null_rows)`.

    Returns {"failure": Failure | None, "null_rows": ..., "null_result": ...}; the null rows
    are kept for the checker's null invocations (L166 (9)-(10))."""
    runs = []
    for target, design in (("rtl", rtl), ("null", null)):
        result = driver_run(driver_source, design, target, seed, step_timeout_s=timeout_s, budget_s=timeout_s)
        failure = run_outcome(result)
        if failure is not None:
            return {"failure": failure, "failed_target": target, "null_rows": None, "null_result": None}
        runs.append(result)
    return {"failure": compare(runs[0]["rows"], runs[1]["rows"]), "failed_target": None,
            "null_rows": runs[1]["rows"], "null_result": runs[1]}
