"""tools/build_audit_bundle.py guards (D-020, D-021).

Behavioural: a copy of the real script runs as its own process in a small temporary
repository, and the test reads its exit code and the zip it wrote. Git is replaced at the
subprocess boundary (the pinned image has no git); any git call the stub does not know fails.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "tools" / "build_audit_bundle.py"
HEAD, SOURCE = "a" * 40, "b" * 40  # different, so one cannot stand in for the other
RUN = next(line.split('"')[1] for line in SRC.read_text().splitlines() if line.startswith("RUN = "))
TESTS = "evidence/container-tests-20000101T000000Z"

# Runs the script with subprocess.run answering git calls. argv: script, git state (JSON).
STUB = r"""
import json, runpy, subprocess, sys
script, state = sys.argv[1], json.loads(sys.argv[2])
def run(argv, **kw):
    assert argv[:2] == ["git", "-C"], argv
    args = argv[3:]
    if args == ["rev-parse", "HEAD"]:
        out = state["head"] + "\n"
    elif args[:3] == ["log", "-1", "--format=%H"]:
        out = state["source"] + "\n"
    elif args[:2] == ["ls-files", "-z"]:
        out = "\0".join(state["files"] if args[2] == "--" else [])
    elif args[:2] == ["status", "--porcelain"]:
        paths = args[3:]
        hit = [f for f in state["dirty"] if not paths or any(f == p or f.startswith(p + "/") for p in paths)]
        out = "".join(f" M {f}\n" for f in hit)
    else:
        raise AssertionError(argv)
    return subprocess.CompletedProcess(argv, 0, out, "")
subprocess.run = run
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BundleBuildTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        self.put("src/a.py", b"x = 1\n")
        self.put("tools/build_audit_bundle.py", SRC.read_bytes())
        hashes = {"src/a.py": sha(b"x = 1\n")}
        self.put(f"{RUN}/results.jsonl", b"{}\n")
        self.put(f"{RUN}/summary.json", json.dumps(
            {"source_sha256": hashes, "design_materials": {"file_sha256": {}}, "git_commit": "c" * 40,
             "results_sha256": sha(b"{}\n")}).encode())
        tests = json.dumps({"source_sha256": hashes, "git_commit": "d" * 40, "returncode": 0, "totals": {"pass": 1}}).encode()
        self.put(f"{TESTS}/summary.json", tests)
        self.put(f"{TESTS}/SHA256SUMS", f"{sha(tests)}  summary.json\n".encode())
        self.files = sorted(p.relative_to(self.repo).as_posix() for p in self.repo.rglob("*") if p.is_file())
        self.zip = self.repo / "dist/openvef-audit-bundle.zip"

    def put(self, name: str, data: bytes) -> None:
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def build(self, dirty=()):
        state = {"head": HEAD, "source": SOURCE, "files": self.files, "dirty": list(dirty)}
        return subprocess.run([sys.executable, "-I", "-c", STUB, str(self.repo / "tools/build_audit_bundle.py"),
                               json.dumps(state)], capture_output=True, text=True)

    def test_build_commit_is_head(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.zip) as z:
            info = json.loads(z.read("BUNDLE-INFO.json"))
        self.assertEqual(info["build_commit"], HEAD)
        self.assertEqual(info["source_commit"], SOURCE)
        printed = json.loads(result.stdout)
        self.assertEqual(printed["build_commit"], HEAD)
        self.assertEqual(printed["sha256"], sha(self.zip.read_bytes()))
        self.assertTrue(Path(f"{self.zip}.sha256").read_text().startswith(printed["sha256"]))

    def test_dirty_tree_exits_1_and_writes_nothing(self):
        for dirty in ("README.md", "src/a.py"):  # outside and inside the bundled paths
            with self.subTest(dirty=dirty):
                result = self.build([dirty])
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertRegex(result.stderr, "not clean|uncommitted changes")
                self.assertFalse(self.zip.parent.exists())


if __name__ == "__main__":
    unittest.main()
