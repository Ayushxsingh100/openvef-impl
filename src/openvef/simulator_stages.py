"""Protocol §3.4 L166 (7)-(11) for one response, on DRAFT design materials (D-005).

Generic over designs and fixtures (CLAUDE.md rule 4): everything comes from a materials
file. Every result produced here depends on DRAFT, unfrozen or unsigned items, so
`prepare` lists them in `provisional` and callers must report results as provisional.

Order for one response, after the factory checks have passed:
  (7)  L334 timeout from three null runs; driver on RTL, then on the null netlist
       (simulation.simulate_pair);
  (8)  masked comparison, primary mask variant, windows on the null rows (L273);
  (9)  checker null invocation 1, on the frozen serialized null trace (trace.freeze);
  (10) checker null invocation 2, in a separate process, on the same bytes;
  (11) adjudication (stage_map.adjudicate_checker).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Optional

from openvef import design_materials, trace
from openvef.envelope import Failure
from openvef.runtime import checker_invocation
from openvef.sandbox import run_harness
from openvef.simulation import (SimulationError, compare_runs, l334_timeout, null_trace_xz, simulate_pair,
                                validate_mask)
from openvef.stage_map import adjudicate_checker

SEED = 0  # A-037: no F18 fixture supplies a slot seed
EXPORT_TIMEOUT_S = 300.0  # build default


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_null(rtl_text: str, script: str) -> dict:
    r = run_harness({"task": "export", "verilog": rtl_text, "script": script}, EXPORT_TIMEOUT_S)
    if r.timed_out or r.result is None or "error" in r.result:
        raise SimulationError(f"null-netlist export failed: {r.result!r} {r.stderr_tail[-300:]}")
    return r.result


def prepare(repo: Path, materials_file: str) -> dict[str, Any]:
    """Load the materials, export the null netlist twice and compare hashes (L233, F14)."""
    loaded = design_materials.load(repo, materials_file)
    m = loaded["materials"]
    mask = loaded["mask"]["variants"]["primary"]
    validate_mask(mask, m["output_ports"])
    rtl_text = (repo / m["rtl"]).read_text(encoding="utf-8")
    script = (repo / m["export_script"]).read_text(encoding="utf-8")
    first, second = export_null(rtl_text, script), export_null(rtl_text, script)
    if first["sha256"] != second["sha256"]:
        raise SimulationError("null-netlist export is not repeatable (L233)")
    if not re.search(rf"\bmodule\s+{re.escape(m['toplevel'])}\b", first["netlist"]):
        raise SimulationError("null netlist lost the top module name (L233)")
    null = dict(loaded["base"], verilog_sources={f"{m['toplevel']}_null.v": first["netlist"]})
    files = [materials_file, m["spec"], m["rtl"], m["export_script"], m["mask"],
             loaded["mask"]["traceability_table"]]
    spec_sha = _sha((repo / m["spec"]).read_bytes())
    provisional = [
        "FIFO specification, port manifest, reset/legal-input rules: DRAFT, not frozen (D-005, D-006)",
        "cycle cap, safe idle, watchdog, scheduler, trace schema, metadata: DRAFT proposals, not frozen (items 7-12)",
        "FIFO RTL and export script: DRAFT; export script is not the frozen L544 script",
        "observation mask and File 24 table: DRAFT, unsigned; require an independent human reviewer (L271)",
        "spec_version_sha256 in checker metadata is the SHA-256 of the DRAFT spec file, not a frozen value",
        "Claude-decided readings, owner review pending: A-040, A-041, A-043, A-044",
    ]
    metadata = {"design_id": m["design_id"], "spec_version_sha256": spec_sha,
                "trace_schema_version": m["trace_schema_version"], "cycle_cap": m["cycle_cap"],
                "reset_release_cycle": m["reset_release_cycle"], "trace_integrity_status": "VALID"}
    return {"rtl": loaded["rtl"], "null": null, "mask": mask, "metadata": metadata, "provisional": provisional,
            "record": {"materials_file": materials_file, "status": m["status"],
                       "file_sha256": {f: _sha((repo / f).read_bytes()) for f in files},
                       "null_netlist_sha256": [first["sha256"], second["sha256"]],
                       "yosys_version": first["yosys_version"], "checker_metadata": metadata,
                       "mask_variant": "primary", "provisional": provisional}}


def run_response(ctx: dict[str, Any], driver_source: str, checker_source: str,
                 port_names: Optional[list] = None) -> tuple[Optional[Failure], dict]:
    """L166 (7)-(11) for one response. Returns (failure or None, details)."""
    rtl, null = ctx["rtl"], ctx["null"]
    if port_names is not None:  # A-044: fixture-supplied port manifest (names only)
        rtl = dict(rtl, driver_vector_keys=list(port_names))
        null = dict(null, driver_vector_keys=list(port_names))
    timeout = l334_timeout(driver_source, null, SEED)
    details: dict[str, Any] = {"l334": timeout}
    out = simulate_pair(driver_source, rtl, null, SEED, lambda a, b: compare_runs(a, b, mask=ctx["mask"]),
                        timeout_s=timeout["t_timeout_s"])
    if out["failure"] is not None:
        details["failed_target"] = out["failed_target"]
        return out["failure"], details
    xz = null_trace_xz(out["null_rows"], ctx["mask"])
    if xz is not None:  # L277: a design-validation failure, not an artifact verdict
        raise SimulationError(f"X/Z on an always-observable output in the null trace at row {xz} (L277)")
    frozen = trace.freeze(out["null_rows"])
    details.update(null_trace_sha256=frozen.sha256, null_trace_rows=len(out["null_rows"]))
    outcomes = []
    for _ in range(2):  # L166 (9)-(10): separate processes, same bytes
        o = checker_invocation(checker_source, frozen.decoded(), dict(ctx["metadata"]))
        if isinstance(o, Failure):
            return o, details
        outcomes.append(o)
    if not frozen.verify():
        raise SimulationError("serialized null trace changed during checker invocations")
    return adjudicate_checker(*outcomes), details
