"""F18 fixture runner (v1.3.6).

Implements the runner duties in Catalog (file 36) "Fixture requirements" 1-6 and L176:
verify the index, every descriptor's SHA-256 and byte length, the exact count (144),
then execute each fixture and compare exact expected values.

Rules (CLAUDE.md): the code path is chosen from the fixture INPUT shape only, never
from its ID or expected output. A fixture whose path reaches a stage that is not yet
implemented is reported NOT_IMPLEMENTED -- never PASS.

Usage:  python3.11 -I runner/run_f18.py <baseline_root> <evidence_dir> <run_class>
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.envelope import Envelope, Failure, parse_envelope  # noqa: E402
from openvef.schema import SCHEMA_REL, ValidatedResponse, load_validator, validate_clause_ids, validate_schema  # noqa: E402

INDEX_REL = "41_F18_Fixture_Inputs/fixture-index.json"
INDEX_SHA256 = "f37808c7a662b8fdf164e27feaef023aadd6dfefaada35d11c3719185d1bde54"
EXPECTED_COUNT = 144
COMPARE_KEYS = ("disposition", "stage_id", "error_class", "diagnostic")
# 27_SHA256SUMS.txt entry for the canonical response schema (File 30 §1).
SCHEMA_SHA256 = "6fb5d282b09540949f21ee134b522841c3345031cb3e118a83bdffc18b4e7c34"
PINNED_DISTRIBUTIONS = ("jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py",
                        "typing_extensions")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class IntegrityError(Exception):
    pass


def load_index(root: Path) -> list[dict]:
    index_path = root / INDEX_REL
    raw = index_path.read_bytes()
    if sha256_bytes(raw) != INDEX_SHA256:
        raise IntegrityError(f"fixture index SHA-256 mismatch: {sha256_bytes(raw)}")
    fixtures = json.loads(raw)["fixtures"]
    ids = [f["fixture_id"] for f in fixtures]
    if len(fixtures) != EXPECTED_COUNT:
        raise IntegrityError(f"fixture count {len(fixtures)} != {EXPECTED_COUNT}")
    if len(set(ids)) != len(ids):
        raise IntegrityError("duplicate fixture IDs in index")
    on_disk = {p.name for p in (root / "41_F18_Fixture_Inputs").glob("*.json")} - {"fixture-index.json"}
    listed = {Path(f["path"]).name for f in fixtures}
    if on_disk != listed:
        raise IntegrityError(f"unlisted or missing descriptors: {sorted(on_disk ^ listed)}")
    return fixtures


def load_descriptor(root: Path, entry: dict) -> dict:
    raw = (root / entry["path"]).read_bytes()
    if len(raw) != entry["bytes"] or sha256_bytes(raw) != entry["sha256"]:
        raise IntegrityError(f"{entry['fixture_id']}: descriptor hash/length mismatch")
    desc = json.loads(raw)
    if desc["fixture_id"] != entry["fixture_id"]:
        raise IntegrityError(f"{entry['fixture_id']}: descriptor ID mismatch")
    if desc["expected"] != entry["expected"]:
        raise IntegrityError(f"{entry['fixture_id']}: index/descriptor expected mismatch")
    return desc


def load_schema_validator(root: Path):
    path = root / SCHEMA_REL
    if sha256_file(path) != SCHEMA_SHA256:
        raise IntegrityError(f"response schema SHA-256 mismatch: {sha256_file(path)}")
    return load_validator(path)


def failure_record(result: Failure) -> dict:
    return {
        "disposition": result.disposition,
        "stage_id": result.stage_id,
        "error_class": result.error_class,
        "diagnostic": result.diagnostic,
    }


def execute(desc: dict, validator) -> tuple[str, dict | None, str]:
    """Return (status, actual, note). Dispatch on input shape only."""
    inp = desc["input"]
    raw: bytes | None = None
    if set(inp) <= {"raw_response_utf8", "provider_finish_reason"} and "raw_response_utf8" in inp:
        raw = inp["raw_response_utf8"].encode("utf-8")
    elif set(inp) == {"raw_response_base64"}:
        raw = base64.b64decode(inp["raw_response_base64"], validate=True)

    if raw is not None:
        envelope = parse_envelope(raw, inp.get("provider_finish_reason"))
        if isinstance(envelope, Failure):
            return "EXECUTED", failure_record(envelope), ""
        assert isinstance(envelope, Envelope)
        obj = envelope.obj
    elif set(inp) == {"response_object"}:
        # A-002 (owner decision): skip envelope decoding only; the already-decoded
        # object goes to schema validation as given.
        obj = inp["response_object"]
    else:
        return "NOT_IMPLEMENTED", None, f"input shape {sorted(inp)} has no implemented adapter (see A-002)"

    # PARSE_SCHEMA part 1b: schema, then manifest clause IDs (Protocol §3.4 evaluation
    # order step 1). The manifest clause_ids come from the descriptor's
    # `manifest_clause_ids` field (docs/ambiguities.md A-005).
    checked = validate_schema(validator, obj)
    if isinstance(checked, ValidatedResponse):
        checked = validate_clause_ids(checked, desc["manifest_clause_ids"])
    if isinstance(checked, Failure):
        return "EXECUTED", failure_record(checked), ""
    return "NOT_IMPLEMENTED", None, "PARSE_SCHEMA passed; next stage (source decode / AST) not implemented"


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", "src", "runner"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("+UNCOMMITTED_CHANGES" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "NO_GIT_COMMIT"


def main() -> int:
    root, evidence_root, run_class = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = evidence_root / f"run-{started}"
    out_dir.mkdir(parents=True, exist_ok=False)

    source_files = sorted([*(REPO / "src").rglob("*.py"), *(REPO / "runner").rglob("*.py")])
    meta = {
        "run_started_utc": started,
        "run_class": run_class,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "python_executable_sha256": sha256_file(Path(os.path.realpath(sys.executable))),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "fixture_index_sha256": INDEX_SHA256,
        "response_schema_sha256": SCHEMA_SHA256,
        "distributions": {name: importlib.metadata.version(name) for name in PINNED_DISTRIBUTIONS},
        "git_commit": git_commit(),
        "source_sha256": {str(p.relative_to(REPO)): sha256_file(p) for p in source_files},
        "command": [sys.executable, *sys.argv],
    }

    counts = {"PASS": 0, "FAIL": 0, "NOT_IMPLEMENTED": 0, "ERROR": 0}
    with open(out_dir / "results.jsonl", "w", encoding="utf-8") as res, open(out_dir / "run.log", "w", encoding="utf-8") as log:
        log.write(json.dumps(meta, indent=2) + "\n")
        fixtures = load_index(root)  # IntegrityError aborts the whole run
        validator = load_schema_validator(root)
        for entry in fixtures:
            desc = load_descriptor(root, entry)
            expected = desc["expected"]
            try:
                status, actual, note = execute(desc, validator)
            except Exception as exc:  # recorded, never hidden
                status, actual, note = "ERROR", None, f"{type(exc).__name__}: {exc}"
            if status == "EXECUTED":
                if set(expected) != set(COMPARE_KEYS):
                    status, note = "NOT_IMPLEMENTED", "expected object has non-standard keys; comparator not implemented"
                else:
                    status = "PASS" if all(actual[k] == expected[k] for k in COMPARE_KEYS) else "FAIL"
            counts[status] += 1
            rec = {"fixture_id": entry["fixture_id"], "descriptor_sha256": entry["sha256"], "status": status,
                   "expected": expected, "actual": actual, "note": note}
            res.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            log.write(f"{entry['fixture_id']}: {status} {note}\n")

    summary = {**meta, "counts": counts, "total": sum(counts.values()),
               "results_sha256": sha256_file(out_dir / "results.jsonl")}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "counts": counts}, indent=2))
    return 0 if counts["FAIL"] == 0 and counts["ERROR"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
