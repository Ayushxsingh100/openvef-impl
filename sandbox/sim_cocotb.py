"""cocotb test module hosted by vvp: the per-cycle driver loop (see sim.py).

Runs inside the D-002 sandbox only. The artifact is imported with the same restricted
runtime import as the factory task (harness.guarded_import), its stdout/stderr are
discarded, and it never receives a simulator handle: `step` gets a plain dict of
strings.

Per cycle (Protocol L166 (7); File 30 §4 (a)-(e)): call `step`; an exception is recorded
first; otherwise the vector is validated in order (a) key set (missing before extra),
(b) string values, (c) widths, (d) `0`/`1`, (e) legal-input predicate; an invalid vector
is not driven and ends the run. The watchdog is enforced from outside via the heartbeat.
"""
from __future__ import annotations

import builtins
import io
import json
import os
import sys
import time

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from cocotb.types import LogicArray

import harness

ALL_INPUTS_LEGAL = "ALL_INPUTS_LEGAL"
# Field names given by Protocol §5.2 L217-L219, used verbatim (A-040).
INPUTS = "inputs_consumed_at_edge_n"
OUTPUTS = "outputs_after_edge_n"
NEXT = "next_inputs_scheduled_for_edge_n_plus_1"


def beat(phase: str) -> None:
    with open(os.environ["OPENVEF_SIM_HEARTBEAT"], "w", encoding="ascii") as f:
        f.write(f"{phase} {time.time()}\n")


def finish(result: dict) -> None:
    with open(os.environ["OPENVEF_SIM_RESULT"], "w", encoding="utf-8") as f:
        json.dump(result, f)


def vector_reason(value, widths: dict, predicate) -> str | None:
    """File 30 §4 (a)-(e) on a non-COMPLETE return; None if the vector may be driven.
    Returns "NOT_DETERMINED" when (e) cannot be run (A-027)."""
    if not isinstance(value, dict):
        return "RETURN_TYPE"
    keys, ports = set(value), set(widths)
    if ports - keys:
        return "MISSING_KEYS"
    if keys - ports:
        return "EXTRA_KEYS"
    if not all(isinstance(v, str) for v in value.values()):
        return "NON_STRING_VALUE"
    if any(len(value[k]) != widths[k] for k in value):
        return "WRONG_WIDTH"
    if any(c not in "01" for v in value.values() for c in v):
        return "ILLEGAL_SYMBOL"
    if predicate != ALL_INPUTS_LEGAL:
        return "NOT_DETERMINED"
    return None


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
    predicate = design.get("legal_input_predicate")

    sink = io.StringIO()
    real_out, real_err = sys.stdout, sys.stderr

    def guarded(fn, *args):
        sys.stdout, sys.stderr = sink, sink
        builtins.__import__ = harness.guarded_import
        try:
            return fn(*args)
        finally:
            builtins.__import__ = harness._real_import
            sys.stdout, sys.stderr = real_out, real_err

    beat("import")
    failure, driver = guarded(harness.construct, req["driver_source"], req["seed"])
    if failure is not None:
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
    scheduled = dict(reset[0])
    n = 0
    drive(dut, scheduled)
    while True:
        await RisingEdge(clk)
        consumed = sample(dut, sorted(widths))  # passive capture at the edge (L262)
        await ReadOnly()
        snapshot = sample(dut, outputs)
        row = {"cycle_index": n, "reset": n < release, INPUTS: consumed, OUTPUTS: snapshot}
        if consumed != {k: scheduled[k] for k in sorted(widths)}:
            # L221: "The consumed-input field ... must agree with the prior row's scheduled
            # input"; a mismatch is a harness fault (stage map L155, reason ROW_ALIGNMENT).
            row.update({NEXT: None, "driver_completed": completed})
            rows.append(row)
            events.append({"kind": "trace_integrity", "reason": "ROW_ALIGNMENT", "cycle": n})
            break
        if n < release:
            vector = dict(reset[n + 1])
        elif n - release >= cap:
            # Cap reached (L227): this edge's outputs are recorded; no further decision.
            row.update({NEXT: None, "driver_completed": completed})
            rows.append(row)
            break
        elif completed:
            vector = dict(safe_idle)
        else:
            cycle_index = n - release
            beat("step")
            try:
                value = guarded(driver.step, cycle_index, dict(snapshot))
            except BaseException as exc:  # includes SystemExit
                events.append({"kind": "driver_runtime", "phase": "step", "exception_class": harness.exc_class(exc),
                               "cycle": n})
                value = None
            finally:
                beat("sim")
            if events:
                row.update({NEXT: None, "driver_completed": completed})
                rows.append(row)
                break
            if value == "COMPLETE":
                completed = True
                vector = dict(safe_idle)
            else:
                reason = vector_reason(value, widths, predicate)
                if reason == "NOT_DETERMINED":
                    finish({"not_determined": "legal-input predicate not executable (A-027, A-038)",
                            "cycle": n, "rows": rows, "target": target})
                    return
                if reason is not None:  # an invalid vector is not driven (File 30 §4)
                    events.append({"kind": "driver_vector", "reason": reason, "cycle": n})
                    row.update({NEXT: None, "driver_completed": completed})
                    rows.append(row)
                    break
                vector = {k: value[k] for k in sorted(widths)}
        row.update({NEXT: vector, "driver_completed": completed})
        rows.append(row)
        scheduled = vector
        await FallingEdge(clk)  # designated drive phase: build default (L219; TO FREEZE, L542)
        drive(dut, vector)
        n += 1
    finish({"events": events, "rows": rows, "reset_release_cycle": release, "driver_completed": completed,
            "run_status": "TRUNCATED_TRACE" if events else "COMPLETE_TRACE", "target": target})
