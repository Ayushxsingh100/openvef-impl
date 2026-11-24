"""Alignment/ordering assertions (F2, F10) — H9; determinism comparison (F1) — H10.

H9 implements:
  L216-L219 — row n records inputs consumed at edge n, outputs sampled in ReadOnly after
              edge n, and the driver's vector for edge n+1.
  L221      — "sample outputs first, invoke the driver second, record its next-input
              vector third, drive it before the next active edge"; the consumed-input
              field "must agree with the prior row's scheduled input; the initial reset
              inputs are defined in the design pack".
  L223      — "F2/F10 must prove the actual ordering before any research run." The proof
              uses the simulator times the harness records per row (`ordering`, from
              sandbox/sim_cocotb.py), not only the recorded fields.
  L511 (F2) — with a driver that echoes a registered output into its next input, the
              consumed input at edge n+1 equals the output sampled after edge n.

H10 implements:
  L510 (F1) — "Traces match excluding explicitly non-deterministic metadata"; L551.
  The checker-facing trace rows (DRAFT schema, item 11) contain no non-deterministic
  field, so trace bytes are compared exactly. In a run record, the fields listed in
  NONDETERMINISTIC_RESULT_FIELDS are excluded, each with its reason (A-051).
"""
from __future__ import annotations

from typing import Any, Optional

from openvef import trace as trace_mod
from openvef.simulation import INPUTS, NEXT, OUTPUTS

# A-051 (decided by Claude under the standing delegation, approved under D-009).
NONDETERMINISTIC_RESULT_FIELDS = {
    "waveform": "the FST file header records its creation date and time",
}


def check_alignment(result: dict, design: dict) -> list[str]:
    """Every L216-L221 violation in one simulation result (empty list = aligned)."""
    problems = []
    rows, ordering = result.get("rows") or [], result.get("ordering")
    if not rows:
        return ["no rows"]
    held = design.get("held_inputs") or {}
    first = design["reset_sequence"][0]
    if rows[0][INPUTS] != first:
        problems.append("row 0: consumed inputs differ from the design pack's first reset vector")
    for n in range(1, len(rows)):
        prev = rows[n - 1][NEXT]
        if prev is None:
            problems.append(f"row {n}: follows a row without a scheduled vector")
        elif rows[n][INPUTS] != prev:
            problems.append(f"row {n}: consumed inputs differ from row {n - 1}'s scheduled vector")
    for n, row in enumerate(rows):
        if row["cycle_index"] != n:
            problems.append(f"row {n}: cycle_index {row['cycle_index']}")
        if row[NEXT] is not None:
            for k, v in held.items():
                if n >= len(design["reset_sequence"]) - 1 and row[NEXT].get(k) != v:
                    problems.append(f"row {n}: held input {k} not held")
    if ordering is None:
        problems.append("no ordering record (harness without the H9 probe)")
        return problems
    if [t["row"] for t in ordering] != list(range(len(rows))):
        problems.append("ordering records do not cover the rows one to one")
        return problems
    for n, t in enumerate(ordering):
        if t.get("sample_phase") != "ReadOnly":
            problems.append(f"row {n}: outputs not sampled in ReadOnly")
        if t["sample_ns"] != t["edge_ns"]:
            problems.append(f"row {n}: sample not in the timestep of edge {n}")
        if "driver_call_ns" in t and not t["sample_ns"] <= t["driver_call_ns"]:
            problems.append(f"row {n}: driver called before the outputs were sampled")
        if rows[n][NEXT] is not None:
            if "drive_ns" not in t:
                problems.append(f"row {n}: scheduled vector without a drive time")
                continue
            after = t.get("driver_call_ns", t["sample_ns"])
            if not t["drive_ns"] > after:
                problems.append(f"row {n}: drive not after the decision")
            if n + 1 < len(ordering) and not t["drive_ns"] < ordering[n + 1]["edge_ns"]:
                problems.append(f"row {n}: drive not before edge {n + 1}")
    return problems


def check_echo(result: dict, design: dict, output_port: str, input_port: str) -> dict:
    """F2: for every row where the driver made a decision, the consumed `input_port` at
    edge n+1 equals `output_port` sampled after edge n. Returns the rows checked and any
    mismatches."""
    rows = result.get("rows") or []
    release = len(design["reset_sequence"]) - 1
    checked, mismatches = [], []
    for n in range(release, len(rows) - 1):
        if rows[n]["driver_completed"] or rows[n][NEXT] is None:
            continue
        checked.append(n)
        if rows[n + 1][INPUTS].get(input_port) != rows[n][OUTPUTS].get(output_port):
            mismatches.append(n)
    return {"output": output_port, "input": input_port, "rows_checked": len(checked), "mismatch_rows": mismatches}


def comparable(result: dict) -> dict:
    return {k: v for k, v in result.items() if k not in NONDETERMINISTIC_RESULT_FIELDS}


def compare_repeats(results: list[dict]) -> dict:
    """F1: the trace bytes of every repeat are identical; the run records are identical
    after removing the explicitly non-deterministic fields."""
    if len(results) < 2:
        raise ValueError("need at least two runs")
    hashes = []
    for r in results:
        if not r.get("rows"):
            hashes.append(None)
            continue
        hashes.append(trace_mod.freeze(r["rows"]).sha256)
    base = comparable(results[0])
    differing: list[Optional[list]] = []
    for r in results[1:]:
        other = comparable(r)
        differing.append(sorted(k for k in set(base) | set(other) if base.get(k) != other.get(k)))
    return {"trace_sha256": hashes, "traces_identical": None not in hashes and len(set(hashes)) == 1,
            "records_identical_excluding": sorted(NONDETERMINISTIC_RESULT_FIELDS),
            "differing_fields": differing, "records_identical": all(not d for d in differing)}


def null_checker_repeat(outcomes: list[Any]) -> dict:
    """F1: both checker invocations on the same immutable null trace return PASS."""
    verdicts = [getattr(o, "verdict", None) for o in outcomes]
    return {"verdicts": verdicts, "identical_pass": len(verdicts) == 2 and verdicts == ["PASS", "PASS"]}
