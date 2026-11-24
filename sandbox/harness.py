"""In-container harness: restricted import, factory and signature checks, checker calls.

Runs inside the D-002 sandbox only (`python -I /opt/openvef/harness.py`), standard
library only. Reads one JSON request on stdin and writes one result line
`OPENVEF_SANDBOX_RESULT <json>` to the original stdout. Artifact output is captured and
discarded, so artifact code cannot forge a result line.

Implements:
  File 30 §3 L27 — "compilation; restricted-runtime import; runtime `inspect.signature`
                   and factory-return checks".
  File 30 §6 — "Enforce the same import allow-list statically and at runtime."
  File 30 §3 L35/L37 — `create_driver(seed)` must return an instance of the module's
                   `Driver` class; runtime `inspect.signature` must confirm the same
                   parameter names/kinds/counts for create_driver, Driver.step and
                   check_trace.
  Protocol §3.4 L166 (7) — "Factory return type and runtime signatures are checked
                   immediately after factory construction."
  Protocol stage map — RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=<C>;
                   ENTRY_POINT_REJECT|...|reason=RETURN_TYPE / RUNTIME_SIGNATURE;
                   CHECKER_RUNTIME_ERROR|class=<C>; File 30 L97 return classification.

Readings decided by Claude under the standing delegation (docs/ambiguities.md; owner
review pending): A-034 an exception while importing a module; A-035 order of the
post-construction checks and when check_trace's signature is checked.
"""
from __future__ import annotations

import builtins
import inspect
import io
import json
import os
import re
import sys
import types

ALLOWED_ROOTS = frozenset({"__future__", "collections", "copy", "functools", "itertools", "json", "math",
                           "operator", "random", "re", "statistics", "typing"})
ARTIFACT_MODULES = frozenset({"driver", "checker"})
RESULT_MARKER = "OPENVEF_SANDBOX_RESULT "
_EXC = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
P = inspect.Parameter
REQUIRED_SIGNATURES = {
    "create_driver": ("seed",),
    "Driver.step": ("self", "cycle_index", "outputs_after_edge"),
    "check_trace": ("trace", "metadata"),
}

_real_stdout_fd = os.dup(1)
_real_import = builtins.__import__


def emit(result: dict) -> None:
    os.write(_real_stdout_fd, (RESULT_MARKER + json.dumps(result, sort_keys=True) + "\n").encode("utf-8"))


def exc_class(exc: BaseException) -> str:
    name = type(exc).__name__
    return name if _EXC.fullmatch(name) else "Exception"


def failure(stage: str, error_class: str, diagnostic: str, disposition: str = "REPAIR") -> dict:
    return {"failure": {"stage_id": stage, "error_class": error_class, "diagnostic": diagnostic,
                        "disposition": disposition}}


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    """The static allow-list, applied again to imports made by artifact code."""
    importer = (globals or {}).get("__name__")
    if importer in ARTIFACT_MODULES:
        if level != 0 or name.split(".", 1)[0] not in ALLOWED_ROOTS:
            raise ImportError(f"import of {name!r} is not allowed")
    return _real_import(name, globals, locals, fromlist, level)


def load(name: str, filename: str, source: str) -> types.ModuleType:
    """Restricted-runtime import of one artifact file as module `name`."""
    module = types.ModuleType(name)
    module.__file__ = filename
    sys.modules[name] = module
    exec(compile(source, filename, "exec", dont_inherit=True), module.__dict__)
    return module


def signature_ok(func, expected: tuple[str, ...]) -> bool:
    try:
        params = list(inspect.signature(func).parameters.values())
    except (TypeError, ValueError):
        return False
    return ([p.name for p in params] == list(expected)
            and all(p.kind is P.POSITIONAL_OR_KEYWORD and p.default is P.empty for p in params))


def entry_reject(file: str, symbol: str, reason: str) -> dict:
    return failure("AST_SIGNATURE", "ENTRY_POINT_REJECT", f"ENTRY_POINT_REJECT|file={file}|symbol={symbol}|reason={reason}")


def construct(driver_source: str, seed: int):
    """Import driver.py, call create_driver(seed) once, then the return-type and signature
    checks. Returns (failure_record_or_None, instance_or_None)."""
    try:
        driver = load("driver", "driver.py", driver_source)
    except BaseException as exc:  # A-034: import is the first execution of driver code; includes SystemExit
        return failure("DRIVER_RUNTIME", "RUNTIME_EXCEPTION",
                       f"RUNTIME_EXCEPTION|file=driver.py|phase=factory|class={exc_class(exc)}"), None
    try:
        instance = driver.create_driver(seed)
    except BaseException as exc:  # includes SystemExit from exit()
        return failure("DRIVER_RUNTIME", "RUNTIME_EXCEPTION",
                       f"RUNTIME_EXCEPTION|file=driver.py|phase=factory|class={exc_class(exc)}"), None
    # A-035: return type, then create_driver's signature, then Driver.step's.
    driver_class = getattr(driver, "Driver", None)
    if not (isinstance(driver_class, type) and isinstance(instance, driver_class)):
        return entry_reject("driver.py", "create_driver", "RETURN_TYPE"), None
    if not signature_ok(driver.create_driver, REQUIRED_SIGNATURES["create_driver"]):
        return entry_reject("driver.py", "create_driver", "RUNTIME_SIGNATURE"), None
    if not signature_ok(driver_class.__dict__.get("step"), REQUIRED_SIGNATURES["Driver.step"]):
        return entry_reject("driver.py", "Driver.step", "RUNTIME_SIGNATURE"), None
    return None, instance


def task_factory(request: dict) -> dict:
    """Import driver.py, construct the driver, then return-type and signature checks."""
    fail, _ = construct(request["driver_source"], request["seed"])
    return fail or {"failure": None}


def classify_return(value) -> dict:
    """File 30 L97 exact order; malformed items counted, not errors."""
    def invalid(reason):
        return {"error": ["CHECKER_RETURN_INVALID", f"CHECKER_RETURN_INVALID|reason={reason}"]}
    if not isinstance(value, dict):
        return invalid("NON_DICTIONARY")
    if "diagnostics" not in value:
        return invalid("MISSING_DIAGNOSTICS")
    if set(value) != {"verdict", "diagnostics"}:
        return invalid("TOP_LEVEL_KEYS")
    if not (isinstance(value["verdict"], str) and value["verdict"] in ("PASS", "FAIL")):
        return invalid("INVALID_VERDICT")
    if not isinstance(value["diagnostics"], list):
        return invalid("DIAGNOSTICS_NOT_LIST")

    def item_ok(item):
        return (isinstance(item, dict) and set(item) == {"code", "message", "cycle", "clause_id"}
                and isinstance(item["code"], str) and isinstance(item["message"], str)
                and (item["cycle"] is None or type(item["cycle"]) is int)
                and (item["clause_id"] is None or isinstance(item["clause_id"], str)))
    return {"verdict": value["verdict"], "malformed_items": sum(not item_ok(i) for i in value["diagnostics"])}


def task_checker(request: dict) -> dict:
    """One checker null invocation on an immutable trace (its own container = process)."""
    try:
        checker = load("checker", "checker.py", request["checker_source"])
    except BaseException as exc:  # A-034; includes SystemExit
        return {"error": ["CHECKER_RUNTIME_ERROR", f"CHECKER_RUNTIME_ERROR|class={exc_class(exc)}"]}
    # A-035: check_trace's runtime signature is checked in the checker process, before
    # the first call.
    if not signature_ok(getattr(checker, "check_trace", None), REQUIRED_SIGNATURES["check_trace"]):
        return entry_reject("checker.py", "check_trace", "RUNTIME_SIGNATURE")
    try:
        value = checker.check_trace(request["trace"], request["metadata"])
    except BaseException as exc:  # includes SystemExit from exit()
        return {"error": ["CHECKER_RUNTIME_ERROR", f"CHECKER_RUNTIME_ERROR|class={exc_class(exc)}"]}
    return classify_return(value)


def task_simulate(request: dict) -> dict:
    """One driver run on one target (rtl or null) through Icarus + cocotb (sim.py)."""
    # `python -I` leaves the script directory off sys.path; sim.py sits next to this file.
    # Artifacts still cannot import it: guarded_import admits only the allow-list roots.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sim
    return sim.run(request)


def task_export(request: dict) -> dict:
    """Null-netlist export (Protocol L233) with the design pack's Yosys script.

    The script reads /tmp/in.v and writes /tmp/net.v (design/fifo/export_null.ys). Evaluator
    material only: no artifact code is involved. Returns the netlist text and its SHA-256."""
    import hashlib
    import subprocess
    with open("/tmp/in.v", "w", encoding="utf-8") as f:
        f.write(request["verilog"])
    with open("/tmp/export.ys", "w", encoding="utf-8") as f:
        f.write(request["script"])
    p = subprocess.run(["yosys", "-q", "-s", "/tmp/export.ys"], capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": f"yosys exit {p.returncode}: {(p.stderr or p.stdout)[-800:]}"}
    data = open("/tmp/net.v", "rb").read()
    version = subprocess.run(["yosys", "-V"], capture_output=True, text=True).stdout.strip()
    return {"netlist": data.decode("utf-8"), "sha256": hashlib.sha256(data).hexdigest(), "yosys_version": version}


def task_interface(request: dict) -> dict:
    """Top module and public ports of a Verilog text, from Yosys `write_json` (F14; H1).

    Evaluator material only. Returns {"modules", "top", "ports": [[name, direction, width],
    ...] in declaration order}."""
    import subprocess
    with open("/tmp/iface.v", "w", encoding="utf-8") as f:
        f.write(request["verilog"])
    top = request["top"]
    script = f"read_verilog -sv /tmp/iface.v\nhierarchy -check -top {top}\nproc\nwrite_json /tmp/iface.json\n"
    p = subprocess.run(["yosys", "-q", "-p", script], capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": f"yosys exit {p.returncode}: {(p.stderr or p.stdout)[-800:]}"}
    data = json.load(open("/tmp/iface.json", encoding="utf-8"))
    mod = data["modules"][top]
    ports = [[name, spec["direction"], len(spec["bits"])] for name, spec in mod["ports"].items()]
    return {"modules": sorted(data["modules"]), "top": top, "ports": ports}


def task_yosys(request: dict) -> dict:
    """Run evaluator-built Yosys scripts on evaluator-supplied files (H5 bounded check).

    `files` maps plain names to text, written under /tmp/y; each of `scripts` runs as one
    `yosys -s` invocation with its own wall-clock limit. Returns each log and exit code.
    No artifact code is involved."""
    import subprocess
    os.makedirs("/tmp/y", exist_ok=True)
    for name, text in request["files"].items():
        if "/" in name or name.startswith("."):
            return {"error": "file names must be plain"}
        with open(f"/tmp/y/{name}", "w", encoding="utf-8") as f:
            f.write(text)
    runs = []
    for i, script in enumerate(request["scripts"]):
        path = f"/tmp/y/script{i}.ys"
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        try:
            p = subprocess.run(["yosys", "-q", "-l", f"/tmp/y/log{i}.txt", "-s", path], capture_output=True,
                               text=True, timeout=float(request["timeout_s"]), cwd="/tmp/y")
            log = open(f"/tmp/y/log{i}.txt", encoding="utf-8", errors="replace").read()
            runs.append({"returncode": p.returncode, "log": log[-int(request.get("log_tail", 200000)):],
                         "stderr": (p.stderr or "")[-800:]})
        except subprocess.TimeoutExpired:
            runs.append({"returncode": None, "timed_out": True, "log": ""})
            break
    version = subprocess.run(["yosys", "-V"], capture_output=True, text=True).stdout.strip()
    return {"runs": runs, "yosys_version": version}


TASKS = {"factory": task_factory, "checker": task_checker, "simulate": task_simulate, "export": task_export,
         "interface": task_interface, "yosys": task_yosys}


def main() -> None:
    request = json.loads(sys.stdin.read())
    task = TASKS[request["task"]]
    for root in sorted(ALLOWED_ROOTS):  # initialize allowed modules before artifact code runs
        _real_import(root)
    sink = io.StringIO()
    sys.stdout, sys.stderr = sink, sink
    builtins.__import__ = guarded_import
    try:
        result = task(request)
    finally:
        builtins.__import__ = _real_import
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    emit(result)


if __name__ == "__main__":
    main()
