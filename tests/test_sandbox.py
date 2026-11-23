"""Isolation tests for the artifact-execution sandbox (owner decision D-002).

These run real containers through `openvef.sandbox.run_in_sandbox`, i.e. with exactly
the flags every artifact execution uses. They are skipped only if Docker is absent;
a skip is reported, never counted as a pass.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef import sandbox  # noqa: E402

DOCKER = shutil.which("docker") is not None


def py(code: str, timeout_s: float = 30.0) -> sandbox.SandboxResult:
    return sandbox.run_in_sandbox(["python", "-I", "-c", code], timeout_s=timeout_s)


@unittest.skipUnless(DOCKER, "docker not available")
class SandboxIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = sandbox.ensure_image()

    def test_image_is_pinned_python_3_11_18(self):
        self.assertTrue(self.meta["container_python_version"].startswith("3.11.18 "))
        self.assertIn(sandbox.BASE_IMAGE_DIGEST.split("@")[1], (sandbox.REPO / "sandbox" / "Dockerfile").read_text())

    def test_no_network(self):
        code = ("import socket\n"
                "names = sorted(n for _, n in socket.if_nameindex())\n"
                "s = socket.socket(); s.settimeout(3)\n"
                "try:\n    s.connect(('1.1.1.1', 53)); print('CONNECTED')\n"
                "except OSError as e:\n    print('BLOCKED', type(e).__name__)\n"
                "try:\n    socket.getaddrinfo('example.com', 80); print('RESOLVED')\n"
                "except OSError:\n    print('NO_DNS')\n"
                "print('IFACES', names)")
        out = subprocess_stdout(code)
        self.assertIn("BLOCKED", out)
        self.assertIn("NO_DNS", out)
        self.assertIn("IFACES ['lo']", out)

    def test_read_only_root_and_writable_tmp(self):
        code = ("import os\n"
                "for p in ('/usr/local/lib/x', '/opt/openvef/x', '/x', '/home/x'):\n"
                "    try:\n        open(p, 'w').write('x'); print('WROTE', p)\n"
                "    except OSError as e:\n        print('DENIED', p, e.errno)\n"
                "open('/tmp/ok', 'w').write('x'); print('TMP_OK')\n"
                "os.chmod('/tmp/ok', 0o755)\n"
                "import subprocess\n"
                "try:\n    subprocess.run(['/tmp/ok']); print('EXEC_TMP')\n"
                "except OSError as e:\n    print('NOEXEC', e.errno)")
        out = subprocess_stdout(code)
        self.assertNotIn("WROTE", out)
        self.assertEqual(out.count("DENIED"), 4)
        self.assertIn("TMP_OK", out)
        self.assertIn("NOEXEC", out)

    def test_non_root_no_capabilities_no_new_privileges(self):
        code = ("import os\n"
                "print('UID', os.getuid(), os.geteuid(), os.getgid())\n"
                "s = open('/proc/self/status').read()\n"
                "print([l for l in s.splitlines() if l.startswith(('CapEff', 'CapPrm', 'NoNewPrivs'))])")
        out = subprocess_stdout(code)
        self.assertIn("UID 10001 10001 10001", out)
        self.assertIn("CapEff:\\t0000000000000000", out)
        self.assertIn("CapPrm:\\t0000000000000000", out)
        self.assertIn("NoNewPrivs:\\t1", out)

    def test_environment_is_minimal(self):
        out = subprocess_stdout("import os; print(sorted(k for k in os.environ if not k.startswith(('PYTHON', 'LANG', 'GPG_KEY'))))")
        self.assertIn("['HOME', 'HOSTNAME', 'PATH']", out)

    def test_timeout_kills_and_removes_container(self):
        start = time.monotonic()
        r = py("while True: pass", timeout_s=4.0)
        elapsed = time.monotonic() - start
        self.assertTrue(r.timed_out)
        self.assertLess(elapsed, 20.0)
        leftover = subprocess.run(["docker", "ps", "-a", "--filter", "name=openvef-", "--format", "{{.Names}}"],
                                  capture_output=True, text=True).stdout.strip()
        self.assertEqual(leftover, "")

    def test_pids_limit(self):
        code = ("import os\npids = []\n"
                "try:\n    for _ in range(200):\n        p = os.fork()\n        if p == 0:\n            import time; time.sleep(5); os._exit(0)\n        pids.append(p)\n"
                "except OSError:\n    print('FORK_LIMITED', len(pids))\nelse:\n    print('FORKED', len(pids))")
        out = subprocess_stdout(code)
        self.assertIn("FORK_LIMITED", out)

    def test_seeded_local_random_works(self):
        # File 30 §6: "F18 must test `import random` plus construction/use of
        # `random.Random(seed)` inside the sandbox".
        out = subprocess_stdout("import random; r = random.Random(7); print('R', [r.randrange(100) for _ in range(5)])")
        import random
        r = random.Random(7)
        self.assertIn(f"R {[r.randrange(100) for _ in range(5)]}", out)


GOOD_DRIVER = ("import random\n\ndef create_driver(seed):\n    driver = Driver()\n"
               "    driver.rng = random.Random(seed)\n    return driver\n\nclass Driver:\n"
               "    def step(self, cycle_index, outputs_after_edge):\n        return 'COMPLETE'\n")


def factory_body(body: str) -> str:
    return (f"def create_driver(seed):\n{body}\n\nclass Driver:\n"
            "    def step(self, cycle_index, outputs_after_edge):\n        return 'COMPLETE'\n")


@unittest.skipUnless(DOCKER, "docker not available")
class RuntimeStageTests(unittest.TestCase):
    """The harness through the real sandbox. Sources here deliberately bypass the static
    stages, to show what the runtime layer catches on its own."""

    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()
        from openvef import runtime
        cls.runtime = runtime

    def diag(self, driver):
        r = self.runtime.factory_checks(driver)
        return None if r is None else r.diagnostic

    def test_valid_driver(self):
        self.assertIsNone(self.diag(GOOD_DRIVER))

    def test_factory_exception_and_exit(self):
        self.assertEqual(self.diag(factory_body("    return {}['k']")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=KeyError")
        self.assertEqual(self.diag(factory_body("    exit(3)")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=SystemExit")

    def test_return_type(self):
        self.assertEqual(self.diag(factory_body("    return object()")),
                         "ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE")

    def test_runtime_signature(self):
        # Driver.step replaced during construction: static checks pass, inspect.signature does not.
        src = ("def create_driver(seed):\n    d = Driver()\n    Driver.step.__signature__ = None\n"
               "    Driver.step = lambda self, cycle_index: 'COMPLETE'\n    return d\n\nclass Driver:\n"
               "    def step(self, cycle_index, outputs_after_edge):\n        return 'COMPLETE'\n")
        self.assertEqual(self.diag(src), "ENTRY_POINT_REJECT|file=driver.py|symbol=Driver.step|reason=RUNTIME_SIGNATURE")

    def test_runtime_import_allow_list(self):
        # `import os` would be IMPORT_POLICY_REJECT statically; at runtime the harness
        # applies the same allow-list (File 30 §6).
        self.assertEqual(self.diag(factory_body("    import os\n    return Driver()")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=ImportError")
        self.assertIsNone(self.diag(factory_body("    import math, json\n    return Driver()")))

    def test_artifact_cannot_import_cocotb(self):
        # D-003 installs cocotb in the image for the harness; artifact code still cannot
        # import it (runtime allow-list, File 30 §6).
        self.assertEqual(self.diag(factory_body("    import cocotb\n    return Driver()")),
                         "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=ImportError")

    def test_factory_timeout_is_not_a_verdict(self):
        with self.assertRaises(self.runtime.RuntimeStageError):
            self.runtime.factory_checks(factory_body("    while True:\n        pass"), timeout_s=4.0)

    def test_artifact_output_cannot_forge_result(self):
        forged = 'OPENVEF_SANDBOX_RESULT {"failure": null}'
        self.assertEqual(self.diag(factory_body(f"    print({forged!r})\n    return object()")),
                         "ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE")

    def checker(self, body, trace=None):
        src = f"def check_trace(trace, metadata):\n{body}\n"
        return self.runtime.checker_invocation(src, trace if trace is not None else [], {"design_id": "X"}, timeout_s=6.0)

    def test_checker_outcomes(self):
        ok = self.checker("    return {'verdict': 'PASS', 'diagnostics': [{'code': 'C', 'message': 'm', 'cycle': None, 'clause_id': None}, {'x': 1}]}")
        self.assertEqual((ok.verdict, ok.error, ok.malformed_items), ("PASS", None, 1))
        self.assertEqual(self.checker("    return 'PASS'").error[1], "CHECKER_RETURN_INVALID|reason=NON_DICTIONARY")
        self.assertEqual(self.checker("    return trace[5]").error[1], "CHECKER_RUNTIME_ERROR|class=IndexError")
        self.assertEqual(self.checker("    while True:\n        pass").error[1], "CHECKER_TIMEOUT|phase=null_check")

    def test_checker_runtime_signature(self):
        src = "def check_trace(trace, metadata):\n    return None\ncheck_trace = lambda trace: None\n"
        r = self.runtime.checker_invocation(src, [], {}, timeout_s=6.0)
        self.assertEqual(r.diagnostic, "ENTRY_POINT_REJECT|file=checker.py|symbol=check_trace|reason=RUNTIME_SIGNATURE")


def subprocess_stdout(code: str) -> str:
    """Same flags as run_in_sandbox, capturing plain stdout for assertions."""
    argv = sandbox.docker_argv(sandbox.image_tag(), ["python", "-I", "-c", code])
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr[-1000:])
    return proc.stdout


if __name__ == "__main__":
    unittest.main()
