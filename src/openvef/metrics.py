"""Ledger, denominators and metrics (Protocol §13.1-§13.3) and the F15 identities — H4.

Implements:
  L342-L346 — slots G_cd, V_cd = valid artifact slots / |G_cd|.
  L350-L366 — T_i, X_i = DET_i + PND_i + CHECKER_ERROR_AFTER_MASKED_DIVERGENCE_i,
              E_i, S_i, S_i^optimistic, M_i and the NA rules.
  L386      — U_i, U_i^X, E_i^trunc; INVALID_ARTIFACT_SLOT for every scheduled mutant
              combination of a missing/invalid slot.
  L388      — ratio-of-sums aggregation; equal-weight means with NA counts.
  L390      — the miss-composition identity, tested on C_i = NP_i + PND_i + DET_i only.
  L396-L411 — J_exposure, J_detection, the optimistic and truncated sensitivities, the
              V_cd identities, and the zero-valid-slot rule.
  L524, L529 — the F15 ledger assertions (`check_identities`).

Each count is computed twice — from class names by the §13.2 formulas, and from the
L370-L384 inclusion flags (openvef.pairs.INCLUSION) — and `check_identities` requires
both to agree, so a wrong formula and a wrong table cannot both pass silently.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from openvef import pairs as P

NA = None  # "Do not replace NA with zero" (L445)


@dataclass(frozen=True)
class Slot:
    """One scheduled generation slot (L342). `pairs` maps each mutant of the design to
    its observation; it is empty for an invalid or missing artifact slot."""
    arm: str
    design: str
    slot_id: str
    valid: bool
    pairs: dict = field(default_factory=dict)


def build_ledger(slots: list[Slot], mutants: dict[str, list[str]]) -> list[dict]:
    """One row per scheduled slot × mutant (L303). Raises if a valid slot does not have
    exactly one observation per mutant of its design."""
    rows = []
    for s in slots:
        m_d = mutants[s.design]
        if len(set(m_d)) != len(m_d):
            raise ValueError(f"duplicate mutant IDs for design {s.design}")
        if s.valid:
            if sorted(s.pairs) != sorted(m_d):
                raise ValueError(f"slot {s.slot_id}: observations {sorted(s.pairs)} != mutants {sorted(m_d)}")
            for m in m_d:
                o = s.pairs[m]
                rows.append({"arm": s.arm, "design": s.design, "slot": s.slot_id, "mutant": m,
                             "class": P.classify(o), "np_subtype": P.np_subtype(o)})
        else:
            if s.pairs:
                raise ValueError(f"slot {s.slot_id}: an invalid slot has no pair observations")
            rows.extend({"arm": s.arm, "design": s.design, "slot": s.slot_id, "mutant": m,
                         "class": P.INVALID_ARTIFACT_SLOT, "np_subtype": None} for m in m_d)
    return rows


def _div(a: float, b: float) -> Optional[float]:
    return NA if b == 0 else a / b


def artifact_metrics(classes: list[str]) -> dict:
    """§13.2 for one valid artifact, from its pair classes (one per mutant)."""
    c = Counter(classes)
    det, pnd, np_, ce_after = c[P.DETECTED], c[P.PND], c[P.NP], c[P.CHECKER_ERROR_AFTER_MASKED]
    t = sum(c[k] for k in (P.DETECTED, P.PND, P.NP, P.ANOMALY_PIPELINE, P.ANOMALY_STRICTER,
                           P.CHECKER_ERROR_NO_MASKED, P.CHECKER_ERROR_AFTER_MASKED))
    x = det + pnd + ce_after
    u = sum(c[k] for k in P.TRUNCATED)
    u_x = sum(c[k] for k in P.TRUNCATED_AFTER_MASKED)
    c_i = np_ + pnd + det
    e_c = _div(pnd + det, c_i)
    s_c = _div(det, det + pnd)
    return {
        "counts": dict(sorted(c.items())), "T": t, "X": x, "DET": det, "PND": pnd, "NP": np_,
        "CHECKER_ERROR_AFTER_MASKED": ce_after, "INVALID_PAIR": c[P.INVALID_PAIR], "U": u, "U_X": u_x,
        "E": _div(x, t), "S": _div(det, x), "S_optimistic": _div(det + ce_after, x), "M": _div(pnd, np_ + pnd),
        "E_trunc": _div(x + u_x, t + u), "C": c_i, "E_C": e_c, "S_C": s_c,
    }


def artifact_metrics_from_flags(classes: list[str]) -> dict:
    """The same counts from the L370-L384 inclusion flags only (independent path)."""
    return {"T": sum(P.flag(k, P.IN_T) for k in classes), "X": sum(P.flag(k, P.IN_X) for k in classes),
            "DET": sum(P.flag(k, P.IN_DET) for k in classes),
            "J_exposure_numerator": sum(P.flag(k, P.IN_J_EXPOSURE) for k in classes),
            "J_detection_numerator": sum(P.flag(k, P.IN_J_DETECTION) for k in classes)}


def _mean(values: list) -> Optional[float]:
    defined = [v for v in values if v is not None]
    return NA if not defined else sum(defined) / len(defined)


def arm_design_metrics(rows: list[dict], slots: list[Slot], arm: str, design: str, m_d: int) -> dict:
    """§13.1-§13.3 for one arm × design."""
    mine = [s for s in slots if s.arm == arm and s.design == design]
    g = len(mine)
    valid = [s for s in mine if s.valid]
    per = {s.slot_id: artifact_metrics([r["class"] for r in rows if r["slot"] == s.slot_id]) for s in valid}
    sx = sum(a["X"] for a in per.values())
    sdet = sum(a["DET"] for a in per.values())
    sce = sum(a["CHECKER_ERROR_AFTER_MASKED"] for a in per.values())
    sux = sum(a["U_X"] for a in per.values())
    st = sum(a["T"] for a in per.values())
    denom = g * m_d
    out = {
        "G": g, "valid_slots": len(valid), "M_d": m_d, "V": _div(len(valid), g),
        "J_exposure": _div(sx, denom), "J_detection": _div(sdet, denom),
        "J_detection_optimistic": _div(sdet + sce, denom), "J_exposure_trunc": _div(sx + sux, denom),
        "E_ratio_of_sums": _div(sx, st), "S_ratio_of_sums": _div(sdet, sx),
        "E_equal_weight": _mean([a["E"] for a in per.values()]),
        "S_equal_weight": _mean([a["S"] for a in per.values()]),
        "NA_counts": {"E": sum(a["E"] is None for a in per.values()), "S": sum(a["S"] is None for a in per.values()),
                      "M": sum(a["M"] is None for a in per.values())},
        "per_artifact": per,
        "no_valid_artifacts_observed": not valid,
    }
    if valid:  # L405-L409; "do not evaluate the right-hand conditional-mean expressions" otherwise (L411)
        k = len(valid) * m_d
        out["J_exposure_rhs"] = out["V"] * (sx / k)
        out["J_detection_rhs"] = out["V"] * (sdet / k)
        out["J_detection_optimistic_rhs"] = out["V"] * ((sdet + sce) / k)
    return out


def check_identities(rows: list[dict], slots: list[Slot], mutants: dict[str, list[str]]) -> list[dict]:
    """Every F15 assertion (L524, L529, L405-L411) on one ledger. Returns one record per
    assertion instance: {"identity", "scope", "holds", "detail"}."""
    out: list[dict] = []

    def check(identity: str, scope: str, holds: bool, detail: str = "") -> None:
        out.append({"identity": identity, "scope": scope, "holds": bool(holds), "detail": detail})

    def close(a: Optional[float], b: Optional[float]) -> bool:
        return a is not None and b is not None and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)

    # Exactly one ledger class for every scheduled slot × mutant; total = |G_cd|×|M_d|.
    keys = Counter((r["slot"], r["mutant"]) for r in rows)
    check("one class per scheduled slot × mutant", "ledger", all(v == 1 for v in keys.values()),
          f"{sum(v > 1 for v in keys.values())} duplicated")
    check("every class is a defined ledger class", "ledger", all(r["class"] in P.INCLUSION for r in rows))
    for arm, design in sorted({(s.arm, s.design) for s in slots}):
        scope = f"{arm}/{design}"
        mine = [s for s in slots if s.arm == arm and s.design == design]
        m_d = len(mutants[design])
        my_rows = [r for r in rows if r["arm"] == arm and r["design"] == design]
        check("total = |G_cd|×|M_d|", scope, len(my_rows) == len(mine) * m_d, f"{len(my_rows)} vs {len(mine)}×{m_d}")
        valid_pair_rows = sum(r["class"] != P.INVALID_ARTIFACT_SLOT for r in my_rows)
        invalid_rows = sum(r["class"] == P.INVALID_ARTIFACT_SLOT for r in my_rows)
        check("(2) valid pair rows + INVALID_ARTIFACT_SLOT rows = |G_cd|×|M_d|", scope,
              valid_pair_rows + invalid_rows == len(mine) * m_d)
        for s in mine:
            classes = [r["class"] for r in rows if r["slot"] == s.slot_id]
            sc = f"{scope}/{s.slot_id}"
            if not s.valid:
                check("invalid slot: only INVALID_ARTIFACT_SLOT rows", sc,
                      classes == [P.INVALID_ARTIFACT_SLOT] * m_d)
                continue
            a, f = artifact_metrics(classes), artifact_metrics_from_flags(classes)
            check("(1) |T_i|+|U_i|+|INVALID_PAIR_i| = |M_d|", sc, a["T"] + a["U"] + a["INVALID_PAIR"] == m_d,
                  f"{a['T']}+{a['U']}+{a['INVALID_PAIR']} vs {m_d}")
            check("(3) X_i ≤ |T_i|", sc, a["X"] <= a["T"])
            check("(3) DET_i ≤ X_i", sc, a["DET"] <= a["X"])
            check("(3) |U_i^X| ≤ |U_i|", sc, a["U_X"] <= a["U"])
            check("X_i includes only DET+PND+checker-error-after-exposure", sc,
                  a["X"] == f["X"] == a["DET"] + a["PND"] + a["CHECKER_ERROR_AFTER_MASKED"])
            check("|T_i| matches the inclusion table", sc, a["T"] == f["T"])
            check("DET_i matches the inclusion table", sc, a["DET"] == f["DET"])
            check("(4) NP_i+PND_i+DET_i = C_i ≤ |T_i|", sc, a["NP"] + a["PND"] + a["DET"] == a["C"] <= a["T"])
            check("E_i definition", sc, a["E"] == _div(f["X"], f["T"]))
            check("S_i definition", sc, a["S"] == _div(f["DET"], f["X"]))
            check("S_i^optimistic definition", sc,
                  a["S_optimistic"] == _div(a["DET"] + a["CHECKER_ERROR_AFTER_MASKED"], a["X"]))
            if a["S"] is not None:
                check("S_i ≤ S_i^optimistic", sc, a["S"] <= a["S_optimistic"])
            if a["E"] is not None and a["E_trunc"] is not None:
                # One-sided: adding truncated pairs to the denominator can lower the
                # rate; the numerator only ever gains recorded pre-termination exposures.
                check("truncated-exposure numerator is one-sided", sc, a["X"] + a["U_X"] >= a["X"])
            # (4) miss composition, on C_i only (L390)
            e_c, s_c = a["E_C"], a["S_C"]
            if e_c is not None and s_c is not None and (1 - e_c * s_c) != 0:
                m_c = _div(a["PND"], a["NP"] + a["PND"])
                rhs = e_c * (1 - s_c) / (1 - e_c * s_c)
                check("(4) miss-composition identity on C_i", sc, close(m_c, rhs), f"M={m_c} rhs={rhs}")
        m = arm_design_metrics(rows, slots, arm, design, m_d)
        flags = artifact_metrics_from_flags([r["class"] for r in my_rows])
        flags_x, flags_det = flags["J_exposure_numerator"], flags["J_detection_numerator"]
        denom = len(mine) * m_d
        check("J_exposure numerator matches the inclusion table", scope, close(m["J_exposure"], _div(flags_x, denom))
              or (m["J_exposure"] is None and denom == 0))
        check("J_detection numerator matches the inclusion table", scope,
              close(m["J_detection"], _div(flags_det, denom)) or (m["J_detection"] is None and denom == 0))
        check("J_detection ≤ J_exposure", scope, (m["J_detection"] or 0) <= (m["J_exposure"] or 0))
        check("J_exposure ≤ J_exposure^trunc (one-sided)", scope, (m["J_exposure"] or 0) <= (m["J_exposure_trunc"] or 0))
        if m["valid_slots"]:
            check("J_exposure = V_cd × ΣX_i/(|valid|×|M_d|)", scope, close(m["J_exposure"], m["J_exposure_rhs"]))
            check("J_detection = V_cd × ΣDET_i/(|valid|×|M_d|)", scope, close(m["J_detection"], m["J_detection_rhs"]))
            check("J_detection^optimistic identity", scope,
                  close(m["J_detection_optimistic"], m["J_detection_optimistic_rhs"]))
        else:
            check("zero valid slots: J_exposure = J_detection = 0, RHS not evaluated", scope,
                  m["J_exposure"] == 0 and m["J_detection"] == 0 and "J_exposure_rhs" not in m
                  and m["no_valid_artifacts_observed"])
    return out
