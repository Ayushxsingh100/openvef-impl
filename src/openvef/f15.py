"""F15 — classifier, ledger and metric identities (Protocol L524, L529, L405-L411).

Case table: built by Claude as ledger inputs (plan §2, label (a)); approved under D-009.

The hand-built cases are ledger inputs, not executable artifacts. Each expected class is
fixed by the §12 rule text it cites, and each known-answer number is worked by hand from
the §13.2-§13.3 formulas (the worked values are in the comments beside them). The
inclusion table in openvef.pairs is compared with the pack's own lines L372-L384.

Readings this depends on: none of A-045..A-051 (those concern how observations are
measured, not how they are classified).
"""
from __future__ import annotations

import random
from fractions import Fraction
from pathlib import Path
from typing import Any

from openvef import metrics as MX
from openvef import pairs as P
from openvef import panel as PN

PACK_PROTOCOL = "02_OpenVEF_Experimental_Protocol_v1.3.6.md"
INCLUSION_LINES = range(372, 385)  # L372-L384


def _o(integrity=False, early=False, term=P.COMPLETE, raw=False, masked=False, checker=None):
    return P.PairObservation(integrity, early, term, raw, masked, checker)


# (case id, observation, expected class, expected NP subtype, rule cited)
PAIR_CASES = [
    ("C01", _o(early=True, checker=None), P.INVALID_PAIR, None,
     "L305 next-input schedules diverge before any raw output divergence"),
    ("C02", _o(integrity=True), P.INVALID_PAIR, None, "L305, L311 predeclared integrity rule violated"),
    ("C03", _o(early=True, term=P.DRIVER_SIM_ERROR, raw=True, masked=True), P.INVALID_PAIR, None,
     "L303-L306 precedence: rule 1 before rule 2"),
    ("C04", _o(term=P.DRIVER_SIM_ERROR, raw=True), P.DRIVER_SIM_NO_MASKED, None, "L306, L321"),
    ("C05", _o(term=P.DRIVER_SIM_ERROR, raw=True, masked=True), P.DRIVER_SIM_AFTER_MASKED, None, "L306, L322"),
    ("C06", _o(term=P.TIMEOUT), P.TIMEOUT_NO_MASKED, None, "L307, L325"),
    ("C07", _o(term=P.TIMEOUT, raw=True, masked=True), P.TIMEOUT_AFTER_MASKED, None, "L307, L326"),
    ("C08", _o(checker="ERROR"), P.CHECKER_ERROR_NO_MASKED, None, "L308, L323"),
    ("C09", _o(raw=True, masked=True, checker="ERROR"), P.CHECKER_ERROR_AFTER_MASKED, None, "L308, L324"),
    ("C10", _o(raw=True, masked=True, checker="FAIL"), P.DETECTED, None, "L314"),
    ("C11", _o(raw=True, masked=True, checker="PASS"), P.PND, None, "L315"),
    ("C12", _o(checker="PASS"), P.NP, P.NP_NO_RAW, "L316, L392"),
    ("C13", _o(raw=True, checker="PASS"), P.NP, P.NP_RAW_ONLY, "L316, L392"),
    ("C14", _o(checker="FAIL"), P.ANOMALY_PIPELINE, None, "L317; L311 checker-attributable, stays in T_i"),
    ("C15", _o(raw=True, checker="FAIL"), P.ANOMALY_STRICTER, None, "L318"),
    ("C16", _o(term=P.TIMEOUT, raw=True), P.TIMEOUT_NO_MASKED, None, "L307: raw-only before timeout is not masked"),
]

CANON: dict[str, P.PairObservation] = {}
for _cid, _obs, _exp, _sub, _rule in PAIR_CASES:  # first case of each class
    CANON.setdefault(_exp, _obs)


def _slot(arm, design, sid, classes):
    if classes is None:
        return MX.Slot(arm, design, sid, False)
    return MX.Slot(arm, design, sid, True, {f"m{i + 1}": CANON[c] for i, c in enumerate(classes)})


def ledger_scenario() -> tuple[list, dict]:
    slots = [
        _slot("A", "D1", "a1", [P.DETECTED, P.PND, P.NP, P.CHECKER_ERROR_AFTER_MASKED, P.DRIVER_SIM_AFTER_MASKED,
                                P.INVALID_PAIR]),
        _slot("A", "D1", "a2", [P.ANOMALY_PIPELINE, P.ANOMALY_STRICTER, P.CHECKER_ERROR_NO_MASKED, P.TIMEOUT_NO_MASKED,
                                P.TIMEOUT_AFTER_MASKED, P.DRIVER_SIM_NO_MASKED]),
        _slot("A", "D1", "a3", None),
        _slot("B", "D1", "b1", None),  # arm B, design D1: zero valid slots (L411)
        _slot("B", "D1", "b2", None),
        MX.Slot("A", "D2", "c1", True, {"m1": PAIR_CASES[12][1], "m2": PAIR_CASES[11][1]}),
        MX.Slot("B", "D2", "d1", True, {"m1": CANON[P.INVALID_PAIR], "m2": CANON[P.TIMEOUT_NO_MASKED]}),
    ]
    return slots, {"D1": [f"m{i}" for i in range(1, 7)], "D2": ["m1", "m2"]}


F = Fraction
# Known answers, worked by hand from L350-L411.
LEDGER_ARTIFACT_EXPECTED = {
    # a1: T = DET+PND+NP+CE_after = 4; X = 1+1+1 = 3; U = 1 (DRIVER_SIM_AFTER); |T|+|U|+INVALID = 6
    "a1": {"T": 4, "X": 3, "DET": 1, "U": 1, "U_X": 1, "E": F(3, 4), "S": F(1, 3), "S_optimistic": F(2, 3),
           "M": F(1, 2), "E_trunc": F(4, 5)},
    # a2: T = ANOM_P + ANOM_S + CE_no = 3; X = 0; U = 3, U_X = 1; E = 0; S, M = NA; E_trunc = 1/6
    "a2": {"T": 3, "X": 0, "DET": 0, "U": 3, "U_X": 1, "E": 0, "S": None, "S_optimistic": None, "M": None,
           "E_trunc": F(1, 6)},
    # c1: two NP; T = 2, X = 0, E = 0, S = NA, M = 0
    "c1": {"T": 2, "X": 0, "DET": 0, "U": 0, "U_X": 0, "E": 0, "S": None, "S_optimistic": None, "M": 0,
           "E_trunc": 0},
    # d1: INVALID_PAIR + TIMEOUT_NO; T = 0 → E = NA; U = 1; E_trunc = 0/1 = 0
    "d1": {"T": 0, "X": 0, "DET": 0, "U": 1, "U_X": 0, "E": None, "S": None, "S_optimistic": None, "M": None,
           "E_trunc": 0},
}
LEDGER_ARM_EXPECTED = {
    # A/D1: G = 3, valid 2, M_d = 6, denominator 18; ΣX = 3, ΣDET = 1, ΣCE_after = 1, ΣU_X = 2
    ("A", "D1"): {"V": F(2, 3), "J_exposure": F(1, 6), "J_detection": F(1, 18), "J_detection_optimistic": F(1, 9),
                  "J_exposure_trunc": F(5, 18), "E_ratio_of_sums": F(3, 7), "S_ratio_of_sums": F(1, 3)},
    # B/D1: zero valid slots → V = 0, J = 0, RHS not evaluated (L411)
    ("B", "D1"): {"V": 0, "J_exposure": 0, "J_detection": 0, "J_detection_optimistic": 0, "J_exposure_trunc": 0,
                  "E_ratio_of_sums": None, "S_ratio_of_sums": None},
    ("A", "D2"): {"V": 1, "J_exposure": 0, "J_detection": 0, "E_ratio_of_sums": 0, "S_ratio_of_sums": None},
    ("B", "D2"): {"V": 1, "J_exposure": 0, "J_detection": 0, "J_exposure_trunc": 0, "E_ratio_of_sums": None},
}

# Panel known answers (L417-L437), synthetic verdict pairs.
PANEL_BENIGN_CASES = [
    ("reference", [("PASS", "PASS")] * 4, PN.PANEL_COMPATIBLE, 0),
    ("always-FAIL", [("FAIL", "FAIL")] * 4, PN.PANEL_FALSE_ALARM, 4),
    ("crashing", [("ERROR", "ERROR")] * 4, PN.PANEL_ERROR, 0),
    ("nondeterministic", [("PASS", "PASS"), ("PASS", "FAIL"), ("PASS", "PASS"), ("PASS", "PASS")], PN.PANEL_ERROR, 1),
    ("error with false alarm", [("ERROR", "ERROR"), ("FAIL", "FAIL"), ("PASS", "PASS"), ("PASS", "PASS")],
     PN.PANEL_ERROR, 1),  # L423: the error does not hide the false alarm event
]
PANEL_MUTANT_CASES = [
    ({"kind": PN.EXPOSED, "evals": ("FAIL", "FAIL"), "identical_to_passed_benign": False}, "detections"),
    ({"kind": PN.EXPOSED, "evals": ("PASS", "PASS"), "identical_to_passed_benign": False}, "misses"),
    ({"kind": PN.EXPOSED, "evals": ("FAIL", "PASS"), "identical_to_passed_benign": False}, "PANEL_ERROR_EVENT"),
    ({"kind": PN.EXPOSED, "evals": ("ERROR", "ERROR"), "identical_to_passed_benign": False}, "PANEL_ERROR_EVENT"),
    ({"kind": PN.EXPOSED, "evals": ("FAIL", "FAIL"), "identical_to_passed_benign": True}, "PANEL_ERROR_EVENT"),
    ({"kind": PN.RAW_ONLY, "evals": ("FAIL", "FAIL"), "identical_to_passed_benign": False},
     "PANEL_STRICTER_THAN_MASK_EVENT"),
]
# ITT: G = 4 (compatible with 2 detections, false alarm with 3 events, error with 1 event,
# invalid); |Q| = 2, B = 4 → V = 3/4; each partition 1/4 (sum 3/4 = V); PanelSens_ITT =
# 2/(4×2) = 1/4; false-alarm event rate = (0+3+1)/(4×4) = 1/4; slots with a false alarm 2/4.
PANEL_ITT_SLOTS = [
    {"valid": True, "partition": PN.PANEL_COMPATIBLE, "detections": 2, "false_alarm_events": 0},
    {"valid": True, "partition": PN.PANEL_FALSE_ALARM, "detections": 0, "false_alarm_events": 3},
    {"valid": True, "partition": PN.PANEL_ERROR, "detections": 1, "false_alarm_events": 1},
    {"valid": False, "partition": None, "detections": 0, "false_alarm_events": 0},
]
PANEL_ITT_EXPECTED = {"V": F(3, 4), PN.PANEL_COMPATIBLE: F(1, 4), PN.PANEL_FALSE_ALARM: F(1, 4),
                      PN.PANEL_ERROR: F(1, 4), "PanelSens_ITT": F(1, 4), "false_alarm_event_rate": F(1, 4),
                      "slots_with_false_alarm": F(1, 2)}


def _eq(actual: Any, expected: Any) -> bool:
    if expected is None or actual is None:
        return actual is expected
    return abs(F(actual).limit_denominator(10 ** 6) - F(expected)) == 0


def inclusion_matches_pack(baseline_root: Path) -> list[str]:
    """The INCLUSION constant against the pack table, cell by cell."""
    lines = (baseline_root / PACK_PROTOCOL).read_text(encoding="utf-8").splitlines()
    problems, seen = [], set()
    for n in INCLUSION_LINES:
        cells = [c.strip() for c in lines[n - 1].strip().strip("|").split("|")]
        cls, rest = cells[0].strip("`"), tuple(cells[1:])
        seen.add(cls)
        if P.INCLUSION.get(cls) != rest:
            problems.append(f"L{n} {cls}: pack {rest} vs code {P.INCLUSION.get(cls)}")
    if seen != set(P.INCLUSION):
        problems.append(f"class sets differ: {sorted(seen ^ set(P.INCLUSION))}")
    return problems


def random_ledgers(seed: int, count: int) -> list[tuple[list, dict]]:
    """Property-style ledgers: random arms, designs, slot validity and pair classes."""
    rng = random.Random(seed)
    out = []
    observations = [obs for _, obs, _, _, _ in PAIR_CASES]
    for _ in range(count):
        mutants = {f"D{d}": [f"m{i}" for i in range(rng.randint(1, 6))] for d in range(rng.randint(1, 2))}
        slots = []
        for arm in ("A", "B"):
            for design, ms in mutants.items():
                for s in range(rng.randint(1, 5)):
                    sid = f"{arm}-{design}-{s}"
                    if rng.random() < 0.3:
                        slots.append(MX.Slot(arm, design, sid, False))
                    else:
                        slots.append(MX.Slot(arm, design, sid, True, {m: rng.choice(observations) for m in ms}))
        out.append((slots, mutants))
    return out


def run(baseline_root: Path, random_seed: int = 15, random_count: int = 300) -> dict:
    """Execute F15. PASS only if every case gives its expected answer and every identity holds."""
    results: dict[str, Any] = {}
    pair_results = []
    for cid, obs, exp, sub, rule in PAIR_CASES:
        got, got_sub = P.classify(obs), P.np_subtype(obs)
        pair_results.append({"case": cid, "rule": rule, "expected": exp, "actual": got, "expected_subtype": sub,
                             "actual_subtype": got_sub, "ok": got == exp and got_sub == sub})
    results["pair_cases"] = pair_results
    covered = {r["expected"] for r in pair_results}
    results["every_pair_class_covered"] = covered == set(P.PAIR_CLASSES)

    slots, mutants = ledger_scenario()
    rows = MX.build_ledger(slots, mutants)
    results["ledger_has_invalid_artifact_slot"] = any(r["class"] == P.INVALID_ARTIFACT_SLOT for r in rows)
    known = []
    for sid, exp in LEDGER_ARTIFACT_EXPECTED.items():
        got = MX.artifact_metrics([r["class"] for r in rows if r["slot"] == sid])
        for k, v in exp.items():
            known.append({"scope": sid, "metric": k, "expected": str(v), "actual": got[k], "ok": _eq(got[k], v)})
    for (arm, design), exp in LEDGER_ARM_EXPECTED.items():
        got = MX.arm_design_metrics(rows, slots, arm, design, len(mutants[design]))
        for k, v in exp.items():
            known.append({"scope": f"{arm}/{design}", "metric": k, "expected": str(v), "actual": got[k],
                          "ok": _eq(got[k], v)})
    results["ledger_known_answers"] = known
    identities = MX.check_identities(rows, slots, mutants)
    results["scenario_identities"] = identities

    failed_random = []
    n_assertions = 0
    for i, (s, m) in enumerate(random_ledgers(random_seed, random_count)):
        ids = MX.check_identities(MX.build_ledger(s, m), s, m)
        n_assertions += len(ids)
        failed_random += [dict(r, ledger=i) for r in ids if not r["holds"]]
    results["random_ledgers"] = {"seed": random_seed, "count": random_count, "assertions": n_assertions,
                                 "failed": failed_random}

    panel = []
    for name, evals, partition, fa_events in PANEL_BENIGN_CASES:
        got = PN.benign_classification(evals)
        panel.append({"case": name, "expected_partition": partition, "actual_partition": got["partition"],
                      "expected_false_alarm_events": fa_events, "actual_false_alarm_events": got["events"]["false_alarm"],
                      "ok": got["partition"] == partition and got["events"]["false_alarm"] == fa_events})
    for case, counter in PANEL_MUTANT_CASES:
        got = PN.mutant_events([case])
        panel.append({"case": f"mutant {case['kind']} {case['evals']} identical={case['identical_to_passed_benign']}",
                      "expected_counter": counter, "actual": got, "ok": got[counter] == 1 and sum(got.values()) == 1})
    itt = PN.itt(PANEL_ITT_SLOTS, q=2, b=4)
    for k, v in PANEL_ITT_EXPECTED.items():
        panel.append({"case": f"ITT {k}", "expected": str(v), "actual": itt[k], "ok": _eq(itt[k], v)})
    panel.append({"case": "(5) partition proportions sum to V_cd", "ok": PN.partition_identity(itt)})
    zero_q = PN.itt(PANEL_ITT_SLOTS, q=0, b=4)
    panel.append({"case": "|Q_ds| = 0: panel sensitivity NA, partitions reportable",
                  "ok": zero_q["PanelSens_ITT"] is None and PN.partition_identity(zero_q)
                  and PN.sensitivity(PN.PANEL_COMPATIBLE, 0, 0) is None})
    results["panel_cases"] = panel

    inclusion = inclusion_matches_pack(baseline_root)
    results["inclusion_table_vs_pack"] = {"lines": "L372-L384", "problems": inclusion}

    ok = (all(r["ok"] for r in pair_results) and results["every_pair_class_covered"]
          and results["ledger_has_invalid_artifact_slot"] and all(k["ok"] for k in known)
          and all(r["holds"] for r in identities) and not failed_random and all(p["ok"] for p in panel)
          and not inclusion)
    results["summary"] = {
        "pair_cases": len(pair_results), "known_answers": len(known) + len(panel),
        "scenario_identity_assertions": len(identities), "random_identity_assertions": n_assertions,
        "failures": sum(not r["ok"] for r in pair_results) + sum(not k["ok"] for k in known)
        + sum(not r["holds"] for r in identities) + len(failed_random) + sum(not p["ok"] for p in panel)
        + len(inclusion)}
    results["status"] = "PASS" if ok else "FAIL"
    return results
