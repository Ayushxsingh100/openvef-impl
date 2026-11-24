"""F14 — export repeatability (Protocol L523, L233) — plan step 3.

Implements:
  L523 — "Export null netlist twice with same pinned scripts | Stable null hash, top module
         and ports".
  L233 — "Export must preserve top module name and public ports. Run the export twice and
         compare null-netlist hashes."

Records the two export hashes, the Yosys version line, and the interface (top module,
public ports with direction and width, in declaration order) of the original RTL and of
both exported netlists. PASS needs equal hashes, the top module present in both netlists,
and the same set of (name, direction, width) ports as the RTL in both netlists. Port
order is recorded and compared separately (A-052).

Provisional while the export script and RTL are DRAFT (D-005; the frozen L544 export
script is an owner item).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

from openvef import design_materials


def run(repo: Path, materials_file: str, export: Callable[[str, str], dict],
        interface: Callable[[str, str], dict]) -> dict:
    loaded = design_materials.load(repo, materials_file)
    m = loaded["materials"]
    rtl_text = (repo / m["rtl"]).read_text(encoding="utf-8")
    script_text = (repo / m["export_script"]).read_text(encoding="utf-8")
    top = m["toplevel"]
    first, second = export(rtl_text, script_text), export(rtl_text, script_text)
    i_rtl = interface(rtl_text, top)
    i_1, i_2 = interface(first["netlist"], top), interface(second["netlist"], top)

    def port_set(i: dict) -> list:
        return sorted(tuple(p) for p in i["ports"])

    checks = {
        "hashes_equal": first["sha256"] == second["sha256"],
        "top_module_preserved": i_1["top"] == top and i_2["top"] == top and top in i_1["modules"]
        and top in i_2["modules"],
        "ports_preserved": port_set(i_rtl) == port_set(i_1) == port_set(i_2),
        "netlists_identical_interface": i_1["ports"] == i_2["ports"],
    }
    record: dict[str, Any] = {
        "materials_file": materials_file, "materials_status": m["status"],
        "rtl": m["rtl"], "rtl_sha256": hashlib.sha256(rtl_text.encode("utf-8")).hexdigest(),
        "export_script": m["export_script"],
        "export_script_sha256": hashlib.sha256(script_text.encode("utf-8")).hexdigest(),
        "yosys_version": [first["yosys_version"], second["yosys_version"]],
        "null_netlist_sha256": [first["sha256"], second["sha256"]],
        "top_module": top, "rtl_interface": i_rtl, "netlist_interface": [i_1, i_2],
        "port_order_same_as_rtl": i_rtl["ports"] == i_1["ports"],
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "provisional": ["export script and RTL are DRAFT under D-005; the frozen L544 export script is an "
                        "owner item", "A-052 (port comparison) approved under D-009"],
    }
    return record
