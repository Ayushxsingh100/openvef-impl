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
    # reset[i] is driven before active edge i; the active edge after the last vector is
    # the reset-release edge, after which the first snapshot is sampled (B5).
    for i, vector in enumerate(reset):
        if i:
            await FallingEdge(clk)
        drive(dut, vector)
        await RisingEdge(clk)
    await ReadOnly()
    snapshot = sample(dut, outputs)

    rows, completed, events = [], False, []
    for cycle_index in range(cap):
        if completed:
            vector = dict(safe_idle)
        else:
            beat("step")
            try:
                value = guarded(driver.step, cycle_index, dict(snapshot))
            except BaseException as exc:  # includes SystemExit
                events.append({"kind": "driver_runtime", "phase": "step", "exception_class": harness.exc_class(exc),
                               "cycle": cycle_index})
                break
            finally:
                beat("sim")
            if value == "COMPLETE":
                completed = True
                vector = dict(safe_idle)
            else:
                reason = vector_reason(value, widths, predicate)
                if reason == "NOT_DETERMINED":
                    finish({"not_determined": "legal-input predicate not executable (A-027, A-038)",
                            "cycle": cycle_index, "rows": rows, "target": target})
                    return
                if reason is not None:
                    events.append({"kind": "driver_vector", "reason": reason, "cycle": cycle_index})
                    break
                vector = {k: value[k] for k in sorted(widths)}
        rows.append({"cycle": cycle_index, "outputs_after_edge": snapshot, "next_inputs": vector,
                     "driver_completed": completed})
        await FallingEdge(clk)
        drive(dut, vector)
        await RisingEdge(clk)
        await ReadOnly()
        snapshot = sample(dut, outputs)
    finish({"events": events, "rows": rows, "final_outputs": snapshot, "driver_completed": completed,
            "target": target})
