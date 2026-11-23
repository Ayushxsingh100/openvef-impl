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


def subprocess_stdout(code: str) -> str:
    """Same flags as run_in_sandbox, capturing plain stdout for assertions."""
    argv = sandbox.docker_argv(sandbox.image_tag(), ["python", "-I", "-c", code])
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr[-1000:])
    return proc.stdout


if __name__ == "__main__":
    unittest.main()
