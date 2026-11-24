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
# Scheduler and recorder parameters, each marked with its source. "specified" values are
# fixed by the pack; "build_default" values are this build's choices for items the pack
# leaves TO FREEZE (L229, L542). Recorded in every result.
SCHEDULER = {
    "sample_point": {"value": "Cocotb ReadOnly after the active (rising) edge settles",
                     "source": "specified: Protocol §5.2 L218"},
    "ordering": {"value": "sample outputs, invoke driver, record next-input vector, drive before next edge",
                 "source": "specified: Protocol §5.2 L221"},
    "consumed_inputs": {"value": "captured passively at the active edge; must equal the prior row's scheduled "
                                 "vector, else TRACE_INTEGRITY_FAILURE|reason=ROW_ALIGNMENT",
                        "source": "specified: Protocol L221, L262; failure row L155 (A-040)"},
    "drive_point": {"value": "falling edge before the next active edge",
                    "source": "build_default: 'designated drive phase' not given (L219, L542)"},
    "timescale": {"value": "1ns/1ps", "source": "build_default (L542)"},
    "clock_period_ns": {"value": 10, "source": "build_default (L542)"},
    "first_active_edge": {"value": "rising edge at half a period (clock starts low)", "source": "build_default (L542)"},
    "reset": {"value": "reset_sequence[i] is driven before active edge i; edge len-1 is the reset-release edge; "
                       "trace rows start at edge 0",
              "source": "build_default for the convention; reset inputs come from the design pack (L221; A-040)"},
    "waveform": {"value": "FST via $dumpfile/$dumpvars wrapper, vvp -fst",
                 "source": "specified: 'Preserve an FST/VCD waveform audit file where supported' (L223)"},
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
    # L223: "Preserve an FST/VCD waveform audit file where supported." Icarus supports FST
    # through a separate top-level dump module (the same technique cocotb's runner uses).
    wave_file = work / "waves.fst"
    dump = src_dir / "openvef_waveform_dump.v"
    dump.write_text(f'module openvef_waveform_dump();\n  initial begin\n    $dumpfile("{wave_file}");\n'
                    f'    $dumpvars(0, {design["toplevel"]});\n  end\nendmodule\n', encoding="ascii")
    files.append(str(dump))
    cmd_file = work / "cmds.f"
    cmd_file.write_text(f"+timescale+{SCHEDULER['timescale']['value']}\n", encoding="ascii")
    vvp_file = work / "sim.vvp"
    budget_s = float(request["budget_s"])
    started = time.monotonic()

    build = subprocess.run(["iverilog", "-g2012", "-c", str(cmd_file), "-s", design["toplevel"], "-s", "openvef_waveform_dump", "-o", str(vvp_file),
                            *files], capture_output=True, text=True, timeout=budget_s)
    if build.returncode != 0:
        # The design materials do not build: an evaluator-side simulator error (L154).
        return _events({"kind": "simulator_error", "target": target, "exception_class": "CalledProcessError",
                        "detail": build.stderr[-500:]})

    (work / "request.json").write_text(json.dumps(request), encoding="utf-8")
    heartbeat = work / "heartbeat"
    result_file = work / "result.json"
    rows_file = work / "rows.jsonl"  # rows as recorded, kept if the run is killed
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
        "OPENVEF_SIM_ROWS": str(rows_file),
    }
    log = open(work / "vvp.log", "wb")
    proc = subprocess.Popen(["vvp", "-m", vpi_entry, str(vvp_file), "-fst"], cwd=str(work), env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    step_timeout = float(request["step_timeout_s"])
    while proc.poll() is None:
        time.sleep(POLL_S)
        phase, since = _read_heartbeat(heartbeat)
        now = time.monotonic()
        if phase == "step" and since is not None and time.time() - since > step_timeout:
            proc.kill()
            proc.wait()
            return _truncated(rows_file, {"kind": "driver_watchdog"}, target)
        if now - started > budget_s:
            proc.kill()
            proc.wait()
            if phase in ("import", "factory"):
                # A-037: no stage-map row for a driver import/factory that never returns.
                return {"error": "A-037: driver import/factory exceeded the wall-clock limit", "scheduler": SCHEDULER}
            return _truncated(rows_file, {"kind": "simulator_error", "target": target,
                                          "exception_class": "TimeoutExpired"}, target)
    if not result_file.exists():
        # vvp ended without the loop's result: the simulator process failed.
        return _events({"kind": "simulator_error", "target": target, "exception_class": "CalledProcessError",
                        "detail": f"vvp exit {proc.returncode}: " +
                                  (work / "vvp.log").read_text("utf-8", "replace")[-1500:]})
    result = json.loads(result_file.read_text(encoding="utf-8"))
    result["scheduler"] = SCHEDULER
    result["waveform"] = _waveform(wave_file)
    return result


def _truncated(rows_file: Path, event: dict, target: str) -> dict:
    """A run killed from outside: the event plus every row recorded before the kill
    (Protocol L306-L307 need to know whether a masked divergence was recorded before
    termination). A partly written last line is discarded."""
    rows = []
    if rows_file.exists():
        for line in rows_file.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                break
    result = _events(event)
    result.update(rows=rows, run_status="TRUNCATED_TRACE", target=target)
    return result


def _waveform(path: Path) -> dict:
    """The waveform audit file, returned with its hash so the caller can preserve it."""
    import base64
    import hashlib
    if not path.exists():
        return {"format": "fst", "status": "NOT_PRODUCED"}
    data = path.read_bytes()
    return {"format": "fst", "status": "PRESERVED", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "base64": base64.b64encode(data).decode("ascii")}


def _read_heartbeat(path: Path):
    try:
        phase, ts = path.read_text(encoding="ascii").split()
        return phase, float(ts)
    except (OSError, ValueError):
        return None, None
