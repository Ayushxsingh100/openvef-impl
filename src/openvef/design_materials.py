"""Load DRAFT design materials (D-005) into the simulation stages' design dictionaries.

Generic over designs: everything comes from a materials JSON file and the files it
names. Nothing here depends on a fixture (CLAUDE.md rule 4).

The legal-input predicate is taken verbatim from the specification: the first
```python block after the clause named by `legal_input_predicate.spec_clause` (for the
FIFO, FIFO-042), so the specification text is the single source.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DESIGN_KEYS = ("toplevel", "clock_port", "input_ports", "held_inputs", "output_ports", "reset_sequence",
               "cycle_cap", "safe_idle")


def predicate_source(spec_text: str, clause_id: str) -> str:
    m = re.search(rf"^\*\*{re.escape(clause_id)}\*\*.*?```python\n(.*?)```", spec_text, re.S | re.M)
    if m is None:
        raise ValueError(f"no python block after {clause_id}")
    return m.group(1)


def load(repo: Path, materials_file: str) -> dict[str, Any]:
    materials = json.loads((repo / materials_file).read_text(encoding="utf-8"))
    spec_text = (repo / materials["spec"]).read_text(encoding="utf-8")
    pred = materials["legal_input_predicate"]
    rtl_name = Path(materials["rtl"]).name
    base = {k: materials[k] for k in DESIGN_KEYS}
    base["legal_input_predicate"] = {"language": pred["language"], "function": pred["function"],
                                     "source": predicate_source(spec_text, pred["spec_clause"])}
    rtl = dict(base, verilog_sources={rtl_name: (repo / materials["rtl"]).read_text(encoding="utf-8")})
    return {"materials": materials, "spec_text": spec_text, "base": base, "rtl": rtl}
