"""Simulator-backed driver run (outer process), inside the D-002 sandbox only.

Implements, for one target (`rtl` or `null`):
  Protocol §3.4 L166 (7) — "Execute `create_driver(seed)` and `Driver.step` on original
                   RTL, then on null netlist; within each cycle, exception wins over
                   vector validation, which wins over watchdog when observed at the same
                   checkpoint. Factory return type and runtime signatures are checked
                   immediately after factory construction."
  File 30 B5 / §4 — harness owns clock and scheduler; `create_driver(seed)` once; first
                   `step` after reset release with `cycle_index=0` and the post-edge
                   output snapshot; each vector validated before driving; invalid
                   vectors are not driven.
  Protocol L210, L227 — after `COMPLETE` the harness drives the safe-idle vector to the
                   fixed cycle cap and records `driver_completed`.

Toolchain (D-003): Icarus Verilog compiles the design; `vvp` runs it with the cocotb VPI
library, which hosts `sim_cocotb.py` (the per-cycle loop). This process watches a
heartbeat file and enforces the per-step watchdog and the overall budget.

The design materials (RTL/netlist sources, ports, reset sequence, cycle cap, safe-idle
vector, legal-input predicate) come in the request. They are owner-written or still TO
FREEZE (Protocol L229, L542-L543); nothing here supplies defaults for them. Scheduler
choices that the pack leaves TO FREEZE are build defaults, recorded in every result
(`SCHEDULER`), and listed in docs/simulation.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Build defaults for choices the pack leaves TO FREEZE (L229, L542). Not frozen values.
SCHEDULER = {
    "timescale": "1ns/1ps",
    "clock_period_ns": 10,
    "first_active_edge": "rising edge at half a period (clock starts low)",
    "sample_point": "ReadOnly phase after the active (rising) edge",
    "drive_point": "falling edge before the next active edge",
    "reset": "reset_sequence[i] is driven before active edge i; the edge after the last vector is the "
             "reset-release edge",
}
POLL_S = 0.02


def _events(*events: dict) -> dict:
    return {"events": list(events), "scheduler": SCHEDULER}


def run(request: dict) -> dict:
    design, target = request["design"], request["target"]
    work = Path(tempfile.mkdtemp(prefix="sim-", dir="/tmp"))
    src_dir = work / "src"
    src_dir.mkdir()
    files = []
    for name, text in sorted(design["verilog_sources"].items()):
        if "/" in name or name.startswith("."):
            raise ValueError("verilog source names must be plain file names")
        (src_dir / name).write_text(text, encoding="utf-8")
        files.append(str(src_dir / name))
    cmd_file = work / "cmds.f"
    cmd_file.write_text(f"+timescale+{SCHEDULER['timescale']}\n", encoding="ascii")
    vvp_file = work / "sim.vvp"
    budget_s = float(request["budget_s"])
    started = time.monotonic()

    build = subprocess.run(["iverilog", "-g2012", "-c", str(cmd_file), "-s", design["toplevel"], "-o", str(vvp_file),
                            *files], capture_output=True, text=True, timeout=budget_s)
    if build.returncode != 0:
        # The design materials do not build: an evaluator-side simulator error (L154).
        return _events({"kind": "simulator_error", "target": target, "exception_class": "CalledProcessError",
                        "detail": build.stderr[-500:]})

    (work / "request.json").write_text(json.dumps(request), encoding="utf-8")
    heartbeat = work / "heartbeat"
    result_file = work / "result.json"
    from cocotb_tools import config as cocotb_config  # harness-side only; same env as cocotb's Icarus runner
    import find_libpython
    libdir = str(cocotb_config.libs_dir)
    vpi_entry = str(cocotb_config.lib_entry("vpi", "icarus"))
    libpython = find_libpython.find_libpython()
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin") + os.pathsep + libdir,
        "GPI_USERS": f"{libpython};{cocotb_config.pygpi_entry_point()}",
        "HOME": "/tmp",
        "PYTHONPATH": str(HERE),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYGPI_PYTHON_BIN": sys.executable,
        "LIBPYTHON_LOC": libpython,
        "COCOTB_TEST_MODULES": "sim_cocotb",
        "COCOTB_TOPLEVEL": design["toplevel"],
        "TOPLEVEL_LANG": "verilog",
        "COCOTB_RANDOM_SEED": "0",
        "COCOTB_RESULTS_FILE": str(work / "results.xml"),
        "OPENVEF_SIM_REQUEST": str(work / "request.json"),
        "OPENVEF_SIM_HEARTBEAT": str(heartbeat),
        "OPENVEF_SIM_RESULT": str(result_file),
    }
    log = open(work / "vvp.log", "wb")
    proc = subprocess.Popen(["vvp", "-m", vpi_entry, str(vvp_file), "-none"], cwd=str(work), env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    step_timeout = float(request["step_timeout_s"])
    while proc.poll() is None:
        time.sleep(POLL_S)
        phase, since = _read_heartbeat(heartbeat)
        now = time.monotonic()
        if phase == "step" and since is not None and time.time() - since > step_timeout:
            proc.kill()
            proc.wait()
            return _events({"kind": "driver_watchdog"})
        if now - started > budget_s:
            proc.kill()
            proc.wait()
            if phase in ("import", "factory"):
                # A-037: no stage-map row for a driver import/factory that never returns.
                return {"error": "A-037: driver import/factory exceeded the wall-clock limit", "scheduler": SCHEDULER}
            return _events({"kind": "simulator_error", "target": target, "exception_class": "TimeoutExpired"})
    if not result_file.exists():
        # vvp ended without the loop's result: the simulator process failed.
        return _events({"kind": "simulator_error", "target": target, "exception_class": "CalledProcessError",
                        "detail": f"vvp exit {proc.returncode}: " +
                                  (work / "vvp.log").read_text("utf-8", "replace")[-1500:]})
    result = json.loads(result_file.read_text(encoding="utf-8"))
    result["scheduler"] = SCHEDULER
    return result


def _read_heartbeat(path: Path):
    try:
        phase, ts = path.read_text(encoding="ascii").split()
        return phase, float(ts)
    except (OSError, ValueError):
        return None, None
