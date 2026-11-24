"""Hand-built control mutants: manifest, export and the mutant simulation target — H1.

Implements:
  Charter L74 — "One null reference and a hand-built set of distinct control mutants
                sufficient to exercise the F1–F15 cases".
  Protocol L233 — "The null-mutant netlist is generated from the original RTL by exactly
                the same synthesis/export script, tool versions and top-level interface
                as the mutant netlists, with no mutation applied. Export must preserve top
                module name and public ports."
  Protocol L506 — "F17 feasibility uses only hand-built FIFO control mutants."
  Owner decision D-007 (2) — control mutants are RTL edits of design/fifo/rtl/ovf_fifo.v.

The mutants themselves are owner-written (CLAUDE.md; D-007). This module only loads the
manifest the owners write (design/fifo/controls/mutants/manifest.json; format in the
controls README), exports each mutant with the same script as the null netlist, checks
that it keeps the top module and public ports and is distinct from the null netlist and
from every other mutant, and returns the design dictionaries for simulation.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Callable

MANIFEST_KEYS = {"mutants"}
MUTANT_KEYS = {"id", "file", "roles", "description"}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


class MutantError(ValueError):
    """The owner-written mutant set does not meet the stated form."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(manifest_path: Path, toplevel: str, original_rtl: str) -> list[dict]:
    """Read and check the manifest. Each entry: {"id", "file" (relative to the manifest's
    directory), "roles" (list of role names from the controls README), "description"}."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != MANIFEST_KEYS or not isinstance(data["mutants"], list):
        raise MutantError('manifest must be {"mutants": [...]}')
    out, seen = [], set()
    for e in data["mutants"]:
        if not isinstance(e, dict) or set(e) != MUTANT_KEYS:
            raise MutantError(f"mutant entry keys must be {sorted(MUTANT_KEYS)}: {e!r}")
        if not isinstance(e["id"], str) or not ID_RE.match(e["id"]) or e["id"] in seen:
            raise MutantError(f"bad or duplicate mutant id {e['id']!r}")
        seen.add(e["id"])
        if not (isinstance(e["roles"], list) and all(isinstance(r, str) for r in e["roles"])):
            raise MutantError(f"{e['id']}: roles must be a list of strings")
        rel = Path(e["file"])
        if rel.is_absolute() or ".." in rel.parts:
            raise MutantError(f"{e['id']}: file must be relative and inside the mutants directory")
        path = manifest_path.parent / rel
        text = path.read_text(encoding="utf-8")
        if not re.search(rf"\bmodule\s+{re.escape(toplevel)}\b", text):
            raise MutantError(f"{e['id']}: does not define module {toplevel} (D-007: an RTL edit of the original)")
        if text == original_rtl:
            raise MutantError(f"{e['id']}: identical to the original RTL")
        diff = "".join(difflib.unified_diff(original_rtl.splitlines(True), text.splitlines(True),
                                            "ovf_fifo.v", e["file"]))
        out.append({**e, "path": str(path), "source": text, "source_sha256": _sha(text.encode("utf-8")),
                    "diff_vs_original": diff, "diff_sha256": _sha(diff.encode("utf-8"))})
    if not out:
        raise MutantError("manifest lists no mutants")
    return out


def export_all(entries: list[dict], script: str, null_netlist_sha256: str, null_ports: list,
               export: Callable[[str, str], dict], interface: Callable[[str, str], dict], toplevel: str,
               null_base: dict) -> dict[str, dict]:
    """Export every mutant twice with the null netlist's script (L233), and check it.

    `export(rtl_text, script)` is simulator_stages.export_null; `interface(verilog, top)`
    returns {"ports": [...]} (harness task `interface`). Returns {id: record} where each
    record holds the hashes, the interface and the `design` dictionary for simulation."""
    out: dict[str, dict] = {}
    by_hash: dict[str, str] = {}
    for e in entries:
        first, second = export(e["source"], script), export(e["source"], script)
        if first["sha256"] != second["sha256"]:
            raise MutantError(f"{e['id']}: export is not repeatable")
        if first["sha256"] == null_netlist_sha256:
            raise MutantError(f"{e['id']}: exported netlist is identical to the null netlist (not distinct)")
        if first["sha256"] in by_hash:
            raise MutantError(f"{e['id']}: exported netlist identical to mutant {by_hash[first['sha256']]}")
        by_hash[first["sha256"]] = e["id"]
        ports = interface(first["netlist"], toplevel)["ports"]
        if ports != null_ports:
            raise MutantError(f"{e['id']}: public ports {ports} differ from the null netlist's {null_ports} (L233)")
        design = dict(null_base, verilog_sources={f"{toplevel}_mutant_{e['id']}.v": first["netlist"]})
        out[e["id"]] = {"id": e["id"], "roles": e["roles"], "description": e["description"], "file": e["file"],
                        "source_sha256": e["source_sha256"], "diff_sha256": e["diff_sha256"],
                        "netlist_sha256": [first["sha256"], second["sha256"]], "ports": ports,
                        "netlist": first["netlist"], "design": design}
    return out


def by_role(exported: dict[str, dict], role: str) -> list[str]:
    return sorted(m for m, r in exported.items() if role in r["roles"])
