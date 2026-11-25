"""Build dist/openvef-audit-bundle.zip for the external AI audit (docs/AUDIT-BRIEF.md).

Only files tracked by git are bundled, and the bundled paths must have no uncommitted
changes. The build fails if a file that the evidence run hashed has changed since the run,
if the container-test evidence (D-017) is not clean, not intact or not from these sources,
or if the zip reaches 20 MB. Entries are sorted with fixed timestamps and modes, so the
same commit gives the same bytes (for the same Python/zlib). Usage:
    python3 tools/build_audit_bundle.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN = "evidence/run-20261125T173501Z"
PACK = "baseline/OpenVEF_Planning_v1_3_6"
# Pack files the code, tests, documents or the brief rely on (audit exports omitted).
PACK_TAGS = ("01", "02", "03", "10", "11", "12", "16", "19", "20", "21", "22", "23", "24", "25", "27", "30", "31",
             "32", "33", "34", "36", "38", "50", "54", "56", "57", "58")
TESTS = max((p.parent for p in (REPO / "evidence").glob("container-tests-*/summary.json")), default=REPO / "missing").relative_to(REPO).as_posix()
PATHS = ["src", "runner", "sandbox", "tests", "tools", "docs", "design", RUN, TESTS, "requirements.in", "requirements.lock",
         "CLAUDE.md"]
OUT = REPO / "dist" / "openvef-audit-bundle.zip"
LIMIT = 20_000_000


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    pack = [p for p in git("ls-files", "-z", PACK).split("\0") if p
            and (p.startswith(f"{PACK}/41_F18_Fixture_Inputs/") or Path(p).name[:3] in {t + "_" for t in PACK_TAGS})]
    names = sorted({p for p in git("ls-files", "-z", "--", *PATHS).split("\0") if p} | set(pack))
    if git("status", "--porcelain", "--", *PATHS, PACK):
        sys.exit("uncommitted changes in the bundled paths")
    if git("status", "--porcelain"):  # D-020: refuse to build on a dirty tree (any path)
        sys.exit("working tree is not clean (D-020: refuse to build on a dirty tree)")
    files = {n: (REPO / n).read_bytes() for n in names}
    summary = json.loads(files[f"{RUN}/summary.json"])
    changed = [n for n, h in {**summary["source_sha256"], **summary["design_materials"]["file_sha256"]}.items()
               if n not in files or sha(files[n]) != h]
    if changed:
        sys.exit(f"changed since the evidence run: {changed}")
    if sha(files[f"{RUN}/results.jsonl"]) != summary["results_sha256"]:
        sys.exit("results.jsonl does not match the run summary")
    tests = json.loads(files[f"{TESTS}/summary.json"])
    stale = [n for n, h in tests["source_sha256"].items() if n not in files or sha(files[n]) != h]
    sums = dict(reversed(l.split("  ", 1)) for l in files[f"{TESTS}/SHA256SUMS"].decode().splitlines())
    have = {n[len(TESTS) + 1:]: sha(d) for n, d in files.items() if n.startswith(TESTS + "/") and not n.endswith("/SHA256SUMS")}
    if stale or sums != have or "+" in tests["git_commit"] or tests["returncode"] != 0:
        sys.exit(f"container-test evidence not usable: stale {stale}, intact {sums == have}, {tests['git_commit']}, {tests['returncode']}")
    info = {"container_tests": TESTS, "container_tests_commit": tests["git_commit"], "container_tests_totals": tests["totals"],
            "brief": "docs/AUDIT-BRIEF.md", "evidence_run": RUN, "evidence_commit": summary["git_commit"],
            "source_commit": git("log", "-1", "--format=%H", "--", *PATHS, PACK).strip(),
            "build_commit": git("rev-parse", "HEAD").strip(),  # D-020: git HEAD at build time (clean tree)
            "files": len(files),
            "disclosure": "AI-assisted audit. The auditor must not be the implementation author (Claude, Anthropic)."}
    files["BUNDLE-INFO.json"] = (json.dumps(info, indent=2) + "\n").encode()
    files["MANIFEST.sha256"] = "".join(f"{sha(d)}  {n}\n" for n, d in sorted(files.items())).encode()
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n in sorted(files):
            entry = zipfile.ZipInfo(n, (1980, 1, 1, 0, 0, 0))
            entry.compress_type, entry.external_attr = zipfile.ZIP_DEFLATED, 0o100644 << 16
            z.writestr(entry, files[n])
    data = OUT.read_bytes()
    if len(data) >= LIMIT:
        OUT.unlink()
        sys.exit(f"bundle is {len(data)} bytes; the limit is {LIMIT}")
    (OUT.parent / "openvef-audit-bundle.zip.sha256").write_text(f"{sha(data)}  {OUT.name}\n")
    print(json.dumps({"zip": str(OUT.relative_to(REPO)), "bytes": len(data), "sha256": sha(data), **info}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
