"""Feasibility-control runner, F1–F15 and pre-freeze F17 (Protocol §17) — H8.

Implements the evidence side of plan step 2 (docs/F1-F17-plan.md):
  - one evidence directory per run, with the same identity records as an F18 run
    (interpreter version and SHA-256, image identity, toolchain, source hashes, commit,
    host invocation; Owner Decision Record §5.3 items 1-9);
  - one record per control: status, critical-gate flag (L531), owner artifacts it needs
    and which are missing, provisional reasons, details;
  - a timestamped line per control in run.log.

Statuses:
  PASS / FAIL — the control ran and met / did not meet its expected result;
  ERROR — the control could not be adjudicated (evaluator-side failure), never hidden;
  BLOCKED_OWNER_ARTIFACTS — an owner-written file the control needs is missing
      (design/fifo/controls/slots.json; CLAUDE.md, D-007);
  NOT_WIRED — the owner files exist, but the control's procedure has not yet been
      composed from the harness components (plan step 8). Never reported as a pass.

Every control result on DRAFT materials is provisional (D-005); see each record.

Usage (evidence, D-002a):  runner/run_f18_container.sh <run_class> controls
Usage (development only):  python3.11 -I runner/run_controls.py <baseline_root> <evidence_dir> <run_class>
"""
from __future__ import annotations

import datetime as dt
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "runner"))

import run_f18 as F18  # noqa: E402  (identity helpers and pinned-interpreter constants)
from openvef import eda, f14, f15, simulator_stages  # noqa: E402
from openvef.sandbox import SandboxUnavailable, broker_mode, ensure_image  # noqa: E402

MATERIALS = "design/fifo/design-materials-DRAFT.json"
CONTROLS_DIR = REPO / "design" / "fifo" / "controls"
SLOTS_FILE = CONTROLS_DIR / "slots.json"
ORDER = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13", "F14", "F15", "F17")
# Protocol L531: "F2, F4, F5, F9, F15, F16, F17 and F18 are critical gates."
CRITICAL = {"F2", "F4", "F5", "F9", "F15", "F17"}
DRAFT_PROVISIONAL = "depends on DRAFT, unfrozen or unsigned design materials (D-005); not counted until frozen"


def needs(slots: dict, control: str) -> tuple[list, list]:
    files = [s["path"] for s in slots["slots"] if control in s["feeds"]]
    return files, list(slots["controls"][control]["mutant_roles"])


def missing_artifacts(slots: dict, control: str, root: Path | None = None) -> list[str]:
    """Owner files (and mutant roles) the control still lacks."""
    root = CONTROLS_DIR if root is None else root
    files, roles = needs(slots, control)
    missing = [f for f in files if not (root / f).is_file()]
    manifest = root / "mutants" / "manifest.json"
    if roles and manifest.is_file():
        try:
            declared = {r for e in json.loads(manifest.read_text(encoding="utf-8")).get("mutants", [])
                        for r in e.get("roles", [])}
        except (ValueError, AttributeError):
            declared = set()
        missing += [f"mutant role {r} (mutants/manifest.json)" for r in roles if r not in declared]
    elif roles:
        missing += [f"mutant role {r} (mutants/manifest.json)" for r in roles]
    return missing


def run_f14() -> dict:
    rec = f14.run(REPO, MATERIALS, simulator_stages.export_null, eda.interface)
    return {"status": rec.pop("status"), "provisional": [DRAFT_PROVISIONAL, *rec.pop("provisional")], "details": rec}


def run_f15(baseline: Path) -> dict:
    rec = f15.run(baseline)
    return {"status": rec.pop("status"),
            "provisional": ["case table built by Claude (plan §2 label (a)); owner review pending"],
            "details": rec}


PROCEDURES = {"F14": lambda baseline: run_f14(), "F15": run_f15}


def run_control(control: str, slots: dict, baseline: Path) -> dict:
    files, roles = needs(slots, control)
    record = {"control": control, "critical_gate": control in CRITICAL, "owner_artifacts": files,
              "mutant_roles": roles}
    missing = missing_artifacts(slots, control)
    if missing:
        return {**record, "status": "BLOCKED_OWNER_ARTIFACTS", "missing": missing}
    if control not in PROCEDURES:
        return {**record, "status": "NOT_WIRED",
                "note": "owner files present; procedure not yet composed from H1-H10 (plan step 8)"}
    started = time.monotonic()
    try:
        out = PROCEDURES[control](baseline)
    except Exception as exc:  # recorded, never hidden
        return {**record, "status": "ERROR", "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc()[-2000:]}
    return {**record, **out, "wall_s": round(time.monotonic() - started, 3)}


def main() -> int:
    baseline, evidence_root, run_class = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if broker_mode():
        started = os.environ["OPENVEF_RUN_STARTED"]
        out_dir = evidence_root
        if any(out_dir.iterdir()):
            raise F18.IntegrityError("evidence directory is not empty")
    else:
        started = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = evidence_root / f"controls-{started}"
        out_dir.mkdir(parents=True, exist_ok=False)
    try:
        sandbox = ensure_image()
    except (SandboxUnavailable, FileNotFoundError) as exc:
        sandbox = None
        print(f"sandbox unavailable: {exc}", file=sys.stderr)
    if broker_mode() and sandbox is None:
        raise SystemExit("D-002a: the runner container must have the sandbox identity")
    py_sha = F18.sha256_file(Path(os.path.realpath(sys.executable)))
    pinned = broker_mode() and sys.version == F18.PINNED_PYTHON_VERSION and py_sha == F18.PINNED_PYTHON_SHA256
    source_files = sorted([*(REPO / "src").rglob("*.py"), *(REPO / "runner").rglob("*.py"),
                           *(REPO / "sandbox").glob("*"),
                           *(p for p in (REPO / "design").rglob("*") if p.is_file())])
    meta = {
        "run_kind": "feasibility controls F1-F15, F17 (Protocol §17)",
        "run_started_utc": started, "run_class": run_class,
        "interpreter_status": ("PINNED (D-002a: runner and artifacts in the pinned image)" if pinned else
                               "NOT_PINNED: development run, not evidence (D-002a)"),
        "python_version": sys.version, "python_executable": sys.executable, "python_executable_sha256": py_sha,
        "platform": platform.platform(), "machine": platform.machine(),
        "distributions": {n: F18.installed_version(n) for n in F18.PINNED_DISTRIBUTIONS},
        "git_commit": F18.git_commit(),
        "source_sha256": {str(p.relative_to(REPO)): F18.sha256_file(p) for p in source_files},
        "slots_sha256": F18.sha256_file(SLOTS_FILE),
        "command": [sys.executable, *sys.argv], "sandbox": sandbox,
    }
    slots = json.loads(SLOTS_FILE.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    with open(out_dir / "controls.jsonl", "w", encoding="utf-8") as res, \
            open(out_dir / "run.log", "w", encoding="utf-8") as log:
        log.write(json.dumps(meta, indent=2) + "\n")
        for control in ORDER:
            rec = run_control(control, slots, baseline)
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
            res.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, default=str) + "\n")
            res.flush()
            extra = rec.get("missing") or rec.get("error") or ""
            log.write(f"{F18.utc_stamp()} {control}: {rec['status']} {extra if isinstance(extra, str) else len(extra)}"
                      f"{' missing' if rec.get('missing') else ''}\n")
            log.flush()
    meta["run_finished_utc"] = F18.utc_stamp()
    summary = {**meta, "counts": counts, "controls": len(ORDER),
               "controls_sha256": F18.sha256_file(out_dir / "controls.jsonl")}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "counts": counts}), file=sys.stderr)
    return 0 if not counts.get("FAIL") and not counts.get("ERROR") else 1


if __name__ == "__main__":
    sys.exit(main())
