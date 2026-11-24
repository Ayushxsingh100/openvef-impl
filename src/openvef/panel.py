"""Common-trace checker panel (Protocol §13.4) for pre-freeze F17 — H7.

Implements:
  L415 — corpus built through the production harness; separate `REACTIVE_RANDOM` and
         `DIRECTED` streams; benign original-RTL and null-netlist traces per scenario,
         admitted only when the RTL-versus-null masked-equivalence and legal-input
         controls pass; null plus each mutant for the mutant panel.
  L417-L423 — each checker twice in separate processes on each byte-identical benign
         trace; flags for crash/schema error, nondeterminism and false alarm; partition
         PANEL_ERROR > PANEL_FALSE_ALARM > PANEL_COMPATIBLE; event counts kept.
  L425-L427 — Q_ds (checker-independent masked divergence); |Q_ds| = 0 gives NA; Sens
         only for PANEL_COMPATIBLE; PANEL_STRICTER_THAN_MASK_EVENT on raw-only traces.
  L429 — the ITT panel proportions, which must sum to V_cd; false-alarm event rate over
         |G_cd| × B_ds; the share of slots with at least one false alarm.
  L435, L437 — mutant-trace repeat rule; PANEL_ERROR_EVENT; corpus pairs violating the
         paired-input or trace-integrity rule are excluded from Q_ds and counted; a FAIL
         on a mutant trace byte-identical to a benign null trace the checker passed is a
         PANEL_ERROR_EVENT.

Readings decided under the standing delegation (approved under D-009) are A-049 and
A-050 in docs/ambiguities.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from openvef import trace as trace_mod
from openvef.pair_runner import compare_pair

PANEL_ERROR = "PANEL_ERROR"
PANEL_FALSE_ALARM = "PANEL_FALSE_ALARM"
PANEL_COMPATIBLE = "PANEL_COMPATIBLE"
PARTITIONS = (PANEL_ERROR, PANEL_FALSE_ALARM, PANEL_COMPATIBLE)
STREAMS = ("REACTIVE_RANDOM", "DIRECTED")

EXPOSED = "EXPOSED"          # in Q_ds
RAW_ONLY = "RAW_ONLY"        # raw-only unmasked divergence (stricter-than-mask events)
NOT_DIVERGENT = "NOT_DIVERGENT"
EXCLUDED = "EXCLUDED"        # paired-input / integrity / truncation: not in Q_ds (L437)


# --- corpus ------------------------------------------------------------------------

def build_stream(stream: str, scenarios: list[dict], rtl: dict, null: dict, mutants: dict[str, dict],
                 mask: list, run: Callable[[str, dict, str, int], dict]) -> dict:
    """Build one stream's corpus.

    scenarios: [{"scenario_id", "driver_source", "seed"}]; `run(driver_source, design,
    target, seed)` returns a harness simulation result (openvef.simulation.driver_run).
    Returns benign traces (bytes), excluded scenarios with reasons, and mutant cases."""
    if stream not in STREAMS:
        raise ValueError(f"unknown stream {stream!r}")
    benign, excluded, cases = [], [], []
    for sc in scenarios:
        sid, src, seed = sc["scenario_id"], sc["driver_source"], sc["seed"]
        r_rtl = run(src, rtl, "rtl", seed)
        r_null = run(src, null, "null", seed)
        reason = _benign_reason(r_rtl, r_null, mask)
        if reason is not None:
            excluded.append({"scenario_id": sid, "reason": reason})
            continue
        t_rtl, t_null = trace_mod.freeze(r_rtl["rows"]), trace_mod.freeze(r_null["rows"])
        benign.append({"scenario_id": sid, "target": "rtl", "bytes": t_rtl.data, "sha256": t_rtl.sha256})
        benign.append({"scenario_id": sid, "target": "null", "bytes": t_null.data, "sha256": t_null.sha256})
        for mid, design in sorted(mutants.items()):
            r_mut = run(src, design, f"mutant:{mid}", seed)
            pair = compare_pair(r_null, r_mut, mask)
            kind = case_kind(pair)
            case = {"scenario_id": sid, "mutant": mid, "kind": kind, "pair": pair}
            if kind in (EXPOSED, RAW_ONLY, NOT_DIVERGENT):
                frozen = trace_mod.freeze(r_mut["rows"])
                case.update(bytes=frozen.data, sha256=frozen.sha256, null_sha256=t_null.sha256)
            cases.append(case)
    return {"stream": stream, "benign": benign, "excluded_scenarios": excluded, "cases": cases,
            "B": len(benign), "Q": sum(c["kind"] == EXPOSED for c in cases),
            "excluded_pairs": sum(c["kind"] == EXCLUDED for c in cases)}


def _benign_reason(r_rtl: dict, r_null: dict, mask: list) -> Optional[str]:
    for name, r in (("rtl", r_rtl), ("null", r_null)):
        if "rows" not in r or r.get("run_status") != "COMPLETE_TRACE" or r.get("events"):
            return f"{name} run not complete (events {r.get('events')}; legal-input or harness control failed)"
    pair = compare_pair(r_null, r_rtl, mask)
    if pair["integrity_failure"] or pair["next_input_before_raw"]:
        return "RTL-versus-null paired-input or integrity rule violated"
    if pair["masked_divergence"]:
        return "RTL-versus-null masked divergence (control failed)"
    return None


def case_kind(pair: dict) -> str:
    """L425, L437: a corpus null/mutant pair's place in the panel."""
    if pair["integrity_failure"] or pair["next_input_before_raw"] or pair["termination"] != "COMPLETE":
        return EXCLUDED
    if pair["masked_divergence"]:
        return EXPOSED
    return RAW_ONLY if pair["raw_divergence"] else NOT_DIVERGENT


# --- one checker on one stream -------------------------------------------------------

def benign_classification(evals: list[tuple[str, str]]) -> dict:
    """L417-L423 for one checker and stream. `evals` holds the two outcomes (PASS, FAIL or
    ERROR) for each benign trace. Returns flags, event counts and the partition."""
    crash = sum("ERROR" in e for e in evals)
    nondet = sum("ERROR" not in e and e[0] != e[1] for e in evals)
    # A-049: a benign trace carries a false-alarm event when either evaluation returned FAIL.
    false_alarm_events = sum("FAIL" in e for e in evals)
    if crash or nondet:
        partition = PANEL_ERROR
    elif false_alarm_events:
        partition = PANEL_FALSE_ALARM
    else:
        partition = PANEL_COMPATIBLE
    return {"partition": partition, "flags": {"crash_or_schema_error": crash > 0, "nondeterminism": nondet > 0,
                                              "false_alarm": false_alarm_events > 0},
            "events": {"crash_or_schema_error": crash, "nondeterminism": nondet,
                       "false_alarm": false_alarm_events}, "B": len(evals)}


def mutant_events(cases: list[dict]) -> dict:
    """L427, L435, L437 for one checker on one stream's evaluated mutant traces.

    Each case: {"kind": EXPOSED|RAW_ONLY, "evals": (a, b), "identical_to_passed_benign": bool}."""
    detections = misses = error_events = stricter = 0
    for c in cases:
        a, b = c["evals"]
        consistent = "ERROR" not in (a, b) and a == b
        if not consistent:
            error_events += 1
            continue
        if a == "FAIL" and c["identical_to_passed_benign"]:
            error_events += 1  # L437
            continue
        if c["kind"] == EXPOSED:
            if a == "FAIL":
                detections += 1
            else:
                misses += 1
        elif c["kind"] == RAW_ONLY and a == "FAIL":
            stricter += 1  # PANEL_STRICTER_THAN_MASK_EVENT, not a detection (L427)
    return {"detections": detections, "misses": misses, "PANEL_ERROR_EVENT": error_events,
            "PANEL_STRICTER_THAN_MASK_EVENT": stricter}


def sensitivity(partition: str, detections: int, q: int) -> Optional[float]:
    """Sens_i,ds (L427): defined only for PANEL_COMPATIBLE and |Q_ds| > 0."""
    if q == 0 or partition != PANEL_COMPATIBLE:
        return None
    return detections / q


# --- ITT over scheduled slots (L429) -------------------------------------------------

def itt(slots: list[dict], q: int, b: int) -> dict:
    """slots: one per scheduled slot of an arm/design/stream:
    {"valid": bool, "partition": str|None, "detections": int, "false_alarm_events": int}."""
    g = len(slots)
    valid = [s for s in slots if s["valid"]]
    out = {"G": g, "V": None if g == 0 else len(valid) / g, "Q": q, "B": b}
    for p in PARTITIONS:
        out[p] = None if g == 0 else sum(s["partition"] == p for s in valid) / g
    out["PanelSens_ITT"] = None if q == 0 or g == 0 else (
        sum(s["detections"] for s in valid if s["partition"] == PANEL_COMPATIBLE) / (g * q))
    out["false_alarm_event_rate"] = None if g == 0 or b == 0 else sum(s["false_alarm_events"] for s in valid) / (g * b)
    out["slots_with_false_alarm"] = None if g == 0 else sum(s["false_alarm_events"] > 0 for s in valid) / g
    return out


def partition_identity(itt_record: dict) -> bool:
    """L429, L529 (5): the three ITT partition proportions sum to V_cd."""
    if itt_record["G"] == 0:
        return False
    total = sum(itt_record[p] for p in PARTITIONS)
    return abs(total - itt_record["V"]) <= 1e-12


def evaluate_checker(corpus: dict, invoke: Callable[[bytes], str]) -> dict:
    """One checker on one stream's corpus. `invoke(trace_bytes)` runs the checker once in a
    separate process on the decoded bytes and returns PASS, FAIL or ERROR; it is called
    twice per trace (L417, L435). Mutant traces evaluated: EXPOSED (Q_ds) and RAW_ONLY
    (stricter-than-mask events) — A-050."""
    benign_evals = [(invoke(t["bytes"]), invoke(t["bytes"])) for t in corpus["benign"]]
    passed = {t["bytes"] for t, e in zip(corpus["benign"], benign_evals) if e == ("PASS", "PASS")}
    benign = benign_classification(benign_evals)
    cases = []
    for c in corpus["cases"]:
        if c["kind"] not in (EXPOSED, RAW_ONLY):
            continue
        cases.append({"scenario_id": c["scenario_id"], "mutant": c["mutant"], "kind": c["kind"],
                      "evals": (invoke(c["bytes"]), invoke(c["bytes"])),
                      "identical_to_passed_benign": c["bytes"] in passed})
    events = mutant_events(cases)
    return {"stream": corpus["stream"], "benign": benign, "benign_evals": benign_evals, "mutant_cases": cases,
            "mutant_events": events, "Q": corpus["Q"], "B": corpus["B"],
            "sensitivity": sensitivity(benign["partition"], events["detections"], corpus["Q"])}
