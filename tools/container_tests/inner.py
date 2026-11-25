"""Inside the pinned container (D-017): run every tests/test_*.py, verbosely, one process per
file, and record each test's result. Started by tools/run_container_tests.py.

    python -I inner.py <repo> <out>             all files
    python -I inner.py --one <file> <result>    one file
A skip is recorded as a skip, never as a pass.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.records: dict[str, dict] = {}

    def startTest(self, test):
        self.records[test.id()] = {"status": None, "subtests": 0, "subtests_failed": 0}
        self._t = time.monotonic()
        super().startTest(test)

    def _set(self, test, status, detail=""):
        # setUpClass/module failures report a placeholder that startTest never saw
        r = self.records.setdefault(test.id(), {"status": None, "subtests": 0, "subtests_failed": 0})
        if r["status"] is None:
            r["status"] = status
        if detail:
            r["detail"] = detail

    def stopTest(self, test):
        self.records[test.id()]["seconds"] = round(time.monotonic() - self._t, 3)
        super().stopTest(test)

    def addSuccess(self, test):
        self._set(test, "pass")
        super().addSuccess(test)

    def addFailure(self, test, err):
        self._set(test, "FAIL")
        super().addFailure(test, err)

    def addError(self, test, err):
        self._set(test, "ERROR")
        super().addError(test, err)

    def addSkip(self, test, reason):
        self._set(test, "skip", reason)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self._set(test, "expected_failure")
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self._set(test, "UNEXPECTED_SUCCESS")
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        r = self.records[test.id()]
        r["subtests"] += 1
        if err is not None:
            r["subtests_failed"] += 1
            r["status"] = "FAIL" if issubclass(err[0], test.failureException) else "ERROR"
        super().addSubTest(test, subtest, err)


def one(path: Path, result: Path) -> int:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    run = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(suite)
    result.write_text(json.dumps({"ran": run.testsRun, "successful": run.wasSuccessful(), "tests": run.records}))
    return 0 if run.wasSuccessful() else 1


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    repo, out = Path(sys.argv[1]), Path(sys.argv[2])
    sys.path.insert(0, str(repo / "src"))
    from openvef.sandbox import toolchain_identity
    env = {"python_version": sys.version, "python_executable": os.path.realpath(sys.executable),
           "python_executable_sha256": sha(os.path.realpath(sys.executable)), "argv": sys.orig_argv,
           "platform": platform.platform(), "machine": platform.machine(), "uid_gid": [os.getuid(), os.getgid()],
           "environment": dict(sorted(os.environ.items())),
           "distributions": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
           "toolchain": toolchain_identity()}
    (out / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n")
    (out / "logs").mkdir()
    files, total = [], {}
    with open(out / "results.jsonl", "w") as results:
        for path in sorted((repo / "tests").glob("test_*.py")):
            argv = [sys.executable, "-I", __file__, "--one", str(path), "/tmp/result.json"]
            Path("/tmp/result.json").unlink(missing_ok=True)
            started, t = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), time.monotonic()
            with open(out / "logs" / f"{path.stem}.log", "wb") as log:
                rc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT).returncode
            try:
                data = json.loads(Path("/tmp/result.json").read_text())
            except OSError:  # the file did not load or the process died
                data = {"ran": 0, "successful": False, "tests": {f"{path.stem}.<no result>": {"status": "ERROR"}}}
            for name, r in data["tests"].items():
                total[r["status"]] = total.get(r["status"], 0) + 1
                results.write(json.dumps({"file": path.name, "test": name, **r}, sort_keys=True) + "\n")
            files.append({"file": path.name, "sha256": sha(path), "argv": argv, "started_utc": started, "returncode": rc,
                          "seconds": round(time.monotonic() - t, 2), "ran": data["ran"], "successful": data["successful"],
                          "log": f"logs/{path.stem}.log"})
            print(path.name, "ok" if rc == 0 else f"rc {rc}", data["ran"], flush=True)
    (out / "files.json").write_text(json.dumps({"totals": total, "files": files}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(total))
    return 0 if all(f["returncode"] == 0 for f in files) else 1


if __name__ == "__main__":
    sys.exit(one(Path(sys.argv[2]), Path(sys.argv[3])) if sys.argv[1] == "--one" else main())
