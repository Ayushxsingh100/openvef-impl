"""cocotb test module hosted by vvp: the per-cycle driver loop (see sim.py).

Runs inside the D-002 sandbox only. The artifact runs in its own confined process
(artifact_worker.py, D-015): this process, which owns the simulator, the recorder and the
trace, sends it the sampled outputs and receives one schema-checked plain value.

Per cycle (Protocol L166 (7); File 30 §4 (a)-(e)): call `step`; an exception is recorded
first; otherwise the vector is validated in order (a) key set (missing before extra),
(b) string values, (c) widths, (d) `0`/`1`, (e) legal-input predicate; an invalid vector
is not driven and ends the run. The watchdog is enforced from outside via the heartbeat.
"""
from __future__ import annotations

import json
import os
import time

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from cocotb.types import LogicArray
from cocotb.utils import get_sim_time

import harness
from artifact_proc import ArtifactFailed, ArtifactHostError, ArtifactProcess

ALL_INPUTS_LEGAL = "ALL_INPUTS_LEGAL"
# Field names given by Protocol §5.2 L217-L219, used verbatim (A-040).
INPUTS = "inputs_consumed_at_edge_n"
OUTPUTS = "outputs_after_edge_n"
NEXT = "next_inputs_scheduled_for_edge_n_plus_1"


def beat(phase: str) -> None:
    with open(os.environ["OPENVEF_SIM_HEARTBEAT"], "w", encoding="ascii") as f:
        f.write(f"{phase} {time.time()}\n")


def record_row(rows: list, row: dict) -> None:
    """Keep the row, and append it to the rows file at once, so the rows recorded before a
    watchdog kill survive it (Protocol L306-L307: masked divergence before termination)."""
    rows.append(row)
    with open(os.environ["OPENVEF_SIM_ROWS"], "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def now_ns() -> float:
    return get_sim_time(unit="ns")


def finish(result: dict) -> None:
    with open(os.environ["OPENVEF_SIM_RESULT"], "w", encoding="utf-8") as f:
        json.dump(result, f)


class PredicateError(RuntimeError):
    """The design pack's legal-input predicate failed (evaluator-side, not the driver's)."""


def load_predicate(spec):
    """Check (e)'s predicate from the design materials.

    - the test-only literal ALL_INPUTS_LEGAL;
    - or a design-pack Python 3.11 function, {"language": "python3.11", "function": <name>,
      "source": <text>}, called as f(vector, sampled) -> bool, where `sampled` is the
      outputs the driver was given in the same step (A-041; FIFO spec FIFO-042 form).
    Anything else is not executable: None, and (e) is NOT_DETERMINED (A-027, A-038)."""
    if spec == ALL_INPUTS_LEGAL:
        return spec
    if isinstance(spec, dict) and set(spec) == {"language", "function", "source"} and spec["language"] == "python3.11":
        namespace: dict = {}
        exec(compile(spec["source"], "<legal_input_predicate>", "exec"), namespace)  # noqa: S102 - design pack
        return namespace[spec["function"]]
    return None


def vector_reason(value, widths: dict, predicate, sampled: dict, key_names=None) -> str | None:
    """File 30 §4 (a)-(e) on a non-COMPLETE return; None if the vector may be driven.
    Returns "NOT_DETERMINED" when (e) cannot be run (A-027).

    `key_names` (A-044): a fixture-supplied port manifest with names only. It is the key
    set for (a); a vector that passes (a) and (b) under names that are not the design's
    ports cannot be width-checked or driven, so the result is NOT_DETERMINED."""
    if not isinstance(value, dict):
        return "RETURN_TYPE"
    keys, ports = set(value), set(widths) if key_names is None else set(key_names)
    if ports - keys:
        return "MISSING_KEYS"
    if keys - ports:
        return "EXTRA_KEYS"
    if not all(isinstance(v, str) for v in value.values()):
        return "NON_STRING_VALUE"
    if key_names is not None and set(key_names) != set(widths):
        return "NOT_DETERMINED"
    if any(len(value[k]) != widths[k] for k in value):
        return "WRONG_WIDTH"
    if any(c not in "01" for v in value.values() for c in v):
        return "ILLEGAL_SYMBOL"
    if predicate == ALL_INPUTS_LEGAL:
        return None
    if predicate is None:
        return "NOT_DETERMINED"
    try:
        verdict = predicate(dict(value), dict(sampled))
    except Exception as exc:  # noqa: BLE001 - a design-pack defect, reported as a harness error
        raise PredicateError(f"legal-input predicate raised {type(exc).__name__}") from exc
    if not isinstance(verdict, bool):
        raise PredicateError("legal-input predicate returned a non-bool")
    return None if verdict else "ILLEGAL_PROTOCOL_STATE"  # File 30 L83 (e); Protocol L125


def sample(dut, ports) -> dict:
    return {p: str(getattr(dut, p).value) for p in ports}


def drive(dut, vector: dict) -> None:
    for port, bits in vector.items():
        getattr(dut, port).value = LogicArray(bits)


@cocotb.test()
async def openvef_driver_run(dut):
    req = json.load(open(os.environ["OPENVEF_SIM_REQUEST"], encoding="utf-8"))
    design, target = req["design"], req["target"]
    widths = design["input_ports"]
    outputs = design["output_ports"]
    cap = design["cycle_cap"]
    safe_idle = design["safe_idle"]
    predicate = load_predicate(design.get("legal_input_predicate"))
    # A-042: harness-owned inputs (e.g. a reset port) that are not driver-vector keys. Each
    # reset-sequence vector gives them; from the reset-release drive phase onward they are
    # held at these values. They are still recorded as consumed top-level inputs (L217).
    held = dict(design.get("held_inputs") or {})
    all_inputs = sorted(set(widths) | set(held))

    def applied(vector: dict) -> dict:
        return {**vector, **held}

    beat("import")
    try:
        artifact = ArtifactProcess()
        failure = harness.construct(artifact, req["driver_source"], req["seed"])
    except ArtifactHostError as exc:
        finish({"error": f"artifact host error: {exc}"})
        return
    if failure is not None:
        artifact.close()
        finish(failure)
        return
    beat("sim")

    clk = getattr(dut, design["clock_port"])
    cocotb.start_soon(Clock(clk, 10, unit="ns").start(start_high=False))
    reset = design["reset_sequence"]
    if not reset:
        raise ValueError("design materials must give a non-empty reset_sequence")
    # Trace rows (Protocol §5.2 L216-L223; A-040). Row n belongs to active edge n, counted
    # from the first reset edge. reset[i] is driven before edge i ("the initial reset
    # inputs are defined in the design pack"); edge len(reset)-1 is the reset-release
    # edge, whose post-edge snapshot is the first `step` input (B5).
    release = len(reset) - 1
    rows, completed, events = [], False, []
    # Ordering probe (F2/F10, Protocol L223 "F2/F10 must prove the actual ordering"):
    # simulator time of each active edge, the ReadOnly sample, the driver call and the
    # drive phase, per row. Kept outside the trace rows (the trace schema is unchanged).
    ordering = []
    scheduled = dict(reset[0])
    n = 0
    drive(dut, scheduled)
    while True:
        await RisingEdge(clk)
        timing = {"row": n, "edge_ns": now_ns()}
        consumed = sample(dut, all_inputs)  # passive capture at the edge (L262)
        await ReadOnly()
        snapshot = sample(dut, outputs)
        timing.update(sample_ns=now_ns(), sample_phase="ReadOnly")
        ordering.append(timing)
        row = {"cycle_index": n, "reset": n < release, INPUTS: consumed, OUTPUTS: snapshot}
        if consumed != {k: scheduled[k] for k in all_inputs}:
            # L221: "The consumed-input field ... must agree with the prior row's scheduled
            # input"; a mismatch is a harness fault (stage map L155, reason ROW_ALIGNMENT).
            row.update({NEXT: None, "driver_completed": completed})
            record_row(rows, row)
            events.append({"kind": "trace_integrity", "reason": "ROW_ALIGNMENT", "cycle": n})
            break
        if n < release:
            vector = dict(reset[n + 1])
        elif n - release >= cap:
            # Cap reached (L227): this edge's outputs are recorded; no further decision.
            row.update({NEXT: None, "driver_completed": completed})
            record_row(rows, row)
            break
        elif completed:
            vector = applied(safe_idle)
        else:
            cycle_index = n - release
            beat("step")
            timing["driver_call_ns"] = now_ns()
            try:
                value = artifact.step(cycle_index, dict(snapshot))
            except ArtifactFailed as exc:
                events.append({"kind": "driver_runtime", "phase": "step", "exception_class": exc.exception_class,
                               "cycle": n})
                value = None
            except ArtifactHostError as exc:
                finish({"error": f"artifact host error: {exc}", "cycle": n})
                return
            finally:
                beat("sim")
            if events:
                row.update({NEXT: None, "driver_completed": completed})
                record_row(rows, row)
                break
            if isinstance(value, str) and value == "COMPLETE":
                completed = True
                vector = applied(safe_idle)
            else:
                try:
                    reason = vector_reason(value, widths, predicate, snapshot, design.get("driver_vector_keys"))
                except PredicateError as exc:
                    finish({"error": f"design materials: {exc}", "cycle": n})
                    return
                if reason == "NOT_DETERMINED":
                    finish({"not_determined": "vector checks not determinable: legal-input predicate not executable (A-027, A-038) or fixture port manifest without the design's ports/widths (A-044)",
                            "cycle": n, "rows": rows, "target": target})
                    return
                if reason is not None:  # an invalid vector is not driven (File 30 §4)
                    events.append({"kind": "driver_vector", "reason": reason, "cycle": n})
                    row.update({NEXT: None, "driver_completed": completed})
                    record_row(rows, row)
                    break
                vector = applied({k: value[k] for k in sorted(widths)})
        row.update({NEXT: vector, "driver_completed": completed})
        record_row(rows, row)
        scheduled = vector
        await FallingEdge(clk)  # designated drive phase: build default (L219; TO FREEZE, L542)
        drive(dut, vector)
        timing["drive_ns"] = now_ns()
        n += 1
    artifact.close()
    finish({"events": events, "rows": rows, "reset_release_cycle": release, "driver_completed": completed,
            "run_status": "TRUNCATED_TRACE" if events else "COMPLETE_TRACE", "target": target,
            "ordering": ordering})
