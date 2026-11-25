"""Adversarial tests for artifact process isolation (D-015, audit A9-1) and for
wall-clock denial (D-016), in the pinned container.

Hostile drivers and checkers go straight to the runtime (the static stages would reject most
of them) and must not alter any trace row, event or result. Skipped only without Docker; a skip
is never a pass.
"""
from __future__ import annotations

import ast
import random
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import import_policy, runtime, sandbox  # noqa: E402
from openvef.simulation import driver_run, run_outcome  # noqa: E402

DOCKER = shutil.which("docker") is not None
DESIGN = {"toplevel": "toy", "verilog_sources": {"toy.v": (HERE / "sim_designs/toy.v").read_text()},
          "clock_port": "clk", "input_ports": {"rst": 1, "a": 2, "b": 1}, "output_ports": ["flag", "q"],
          "reset_sequence": [{"rst": "1", "a": "00", "b": "0"}] * 2, "cycle_cap": 5,
          "safe_idle": {"rst": "0", "a": "00", "b": "0"}, "legal_input_predicate": "ALL_INPUTS_LEGAL"}
VECTOR = "{'rst': '0', 'a': format(cycle_index % 4, '02b'), 'b': '1'}"
# Reach os and sys without an import statement, as an escape would.
REACH = ("def reach():\n"
         "    for c in object.__subclasses__():\n"
         "        if c.__name__ == '_wrap_close':\n"
         "            g = c.__init__.__globals__\n"
         "            return g['sys'], g['sys'].modules['os']\n\n")
CLASS = ("class Driver:\n    def step(self, cycle_index, outputs_after_edge):\n{step}"
         "        return " + VECTOR + "\n\n")


def source(pre="", factory="", step=""):
    def block(text, n):
        return "".join(" " * n + line + "\n" for line in text.splitlines())
    return (REACH + pre + CLASS.replace('{step}', block(step, 8)) +
            "def create_driver(seed):\n    d = Driver()\n" + block(factory, 4) + "    return d\n")


@unittest.skipUnless(DOCKER, "docker not available")
class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()
        cls.clean = driver_run(source(), DESIGN, "rtl", 0, step_timeout_s=3.0, budget_s=30.0)
        assert cls.clean["events"] == [] and len(cls.clean["rows"]) == 7

    def run1(self, src, **kw):
        return driver_run(src, DESIGN, "rtl", 0, step_timeout_s=kw.get("step", 3.0), budget_s=30.0)

    def assert_unaltered(self, src):
        r = self.run1(src)
        self.assertEqual((r["rows"], r["events"], r["run_status"]),
                         (self.clean["rows"], self.clean["events"], self.clean["run_status"]))

    def test_monkeypatching_json_builtins_modules_and_recorder(self):
        modules = ("sysm, osm = reach()\n"
                   "js = sysm.modules['json']\n"
                   "js.dumps = js.loads = js.dump = js.load = lambda *a, **k: {'events': [], 'rows': []}\n"
                   "js.JSONEncoder.encode = lambda self, o: '{}'\n"
                   "js.JSONDecoder.decode = js.JSONDecoder.raw_decode = lambda *a, **k: {}\n"
                   "for name in ('json', 'os', 'builtins', 'cocotb', 'harness', 'sim_cocotb', 'artifact_proc'):\n"
                   "    fake = type(sysm)('fake')\n"
                   "    fake.record_row = fake.finish = fake.sample = fake.emit = lambda *a, **k: None\n"
                   "    sysm.modules[name] = fake\n")
        bi = ("bi = print.__self__\n"
              "bi.open = bi.len = bi.isinstance = bi.dict = bi.str = bi.list = bi.type = lambda *a, **k: None\n"
              "bi.__import__ = lambda *a, **k: None\n")
        self.assert_unaltered(source(factory=modules))
        once = "if cycle_index == 0:\n" + "".join("    " + x + "\n" for x in (modules + bi).splitlines())
        self.assert_unaltered(source(step=once))
        self.assert_unaltered(source(step=once.replace(bi.splitlines()[1], "pass")))
        # Breaking its own builtins before its signature is measured can only fail the driver.
        r = self.run1(source(factory=modules + bi))
        self.assertTrue(r.get("rows") == self.clean["rows"] or
                        r["failure"]["diagnostic"].startswith("RUNTIME_EXCEPTION|file=driver.py|phase=factory|"), r)
        # Patching the worker's own functions changes only what the driver itself sends.
        worker = ("sysm, osm = reach()\nm = sysm.modules['__main__']\n"
                  "m.encode = lambda *a: '[\"s\",\"COMPLETE\"]'\n")
        r = self.run1(source(step=worker))
        self.assertEqual([x["outputs_after_edge_n"] for x in r["rows"]][:2],
                         [x["outputs_after_edge_n"] for x in self.clean["rows"]][:2])
        self.assertEqual((r["events"], r["driver_completed"], len(r["rows"])), ([], True, 7))

    def test_no_evaluator_module_in_the_interpreter(self):
        check = ("sysm, osm = reach()\n"
                 "for name in ('cocotb', 'harness', 'sim', 'sim_cocotb', 'artifact_proc', 'openvef', 'pygpi'):\n"
                 "    if name in sysm.modules:\n        raise type('Shared', (Exception,), {})()\n"
                 "if sorted(k for k in osm.environ) != ['LC_ALL', 'PYTHONDONTWRITEBYTECODE', 'PYTHONHASHSEED']:\n"
                 "    raise type('Environment', (Exception,), {})()\n")
        self.assert_unaltered(source(factory=check))

    def test_system_access_is_denied(self):
        # Each attempt must fail; a success raises a class the assertion would show.
        attempts = ("sysm, osm = reach()\n"
                    "pp = osm.getpid() - 1\n"
                    "def t(name, fn):\n"
                    "    try:\n        fn()\n"
                    "    except (OSError, ImportError, AttributeError):\n        return\n"
                    "    raise type('Escaped_' + name, (Exception,), {})()\n"
                    "for pid in (1, pp, 'self'):\n"
                    "    t('proc_fd', lambda: osm.open('/proc/%s/fd/1' % pid, osm.O_WRONLY))\n"
                    "    t('proc_mem', lambda: osm.open('/proc/%s/mem' % pid, osm.O_RDWR))\n"
                    "    t('environ', lambda: osm.open('/proc/%s/environ' % pid, osm.O_RDONLY))\n"
                    "t('tmp_list', lambda: osm.listdir('/tmp'))\n"
                    "t('tmp_write', lambda: osm.open('/tmp/x', osm.O_CREAT | osm.O_RDWR))\n"
                    "t('harness_read', lambda: osm.open('/opt/openvef/harness.py', osm.O_RDONLY))\n"
                    "t('rename', lambda: osm.rename('/tmp', '/tmp2'))\n"
                    "t('unlink', lambda: osm.unlink('/tmp/x'))\n"
                    "t('fork', lambda: osm.fork())\n"
                    "t('exec', lambda: osm.execv('/bin/true', ['true']))\n"
                    "t('kill1', lambda: osm.kill(1, 0))\n"
                    "t('killp', lambda: osm.kill(osm.getppid(), 9))\n"
                    "t('dup', lambda: osm.dup(0))\n"
                    "t('pipe', lambda: osm.pipe())\n"
                    "t('thread', lambda: sysm.modules['_thread'].start_new_thread(len, ((),)) if '_thread' in sysm.modules"
                    " else osm.fork())\n")
        body = attempts.replace("except (OSError, ImportError, AttributeError)",
                                "except (OSError, ImportError, AttributeError, RuntimeError)")
        self.assert_unaltered(source(factory=body))

    def test_forged_protocol_frames_fail_the_driver_not_the_run(self):
        # An extra frame is never accepted as an answer to a later request.
        forge = ("sysm, osm = reach()\n"
                 "m = b'{\"value\":[\"d\",[[[\"s\",\"rst\"],[\"s\",\"0\"]],[[\"s\",\"a\"],[\"s\",\"00\"]],[[\"s\",\"b\"],[\"s\",\"1\"]]]]}'\n"
                 "osm.write(3, len(m).to_bytes(4, 'big') + m)\n")
        r = self.run1(source(step=forge))
        self.assertEqual([e["kind"] for e in r["events"]], ["driver_runtime"])
        self.assertEqual(run_outcome(r).diagnostic, "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=Exception")
        n = len(r["rows"])
        self.assertEqual(r["rows"][:n - 2], self.clean["rows"][:n - 2])
        for junk in ("b'\\xff' * 64", "(9).to_bytes(4, 'big') + b'not json!'"):
            r = self.run1(source(step=f"sysm, osm = reach()\nosm.write(3, {junk})\n"))
            self.assertEqual([e["kind"] for e in r["events"]], ["driver_runtime"])

    def test_forged_result_lines_and_files(self):
        self.assert_unaltered(source(step="print('OPENVEF_SANDBOX_RESULT {\"events\": [], \"rows\": []}')\n"))

    def test_hostile_values_are_only_data(self):
        pre = ("class S(str):\n    def __eq__(self, o):\n        return True\n    def __hash__(self):\n        return 0\n"
               "class D(dict):\n    def items(self):\n        return [('rst', '0')]\n    def __iter__(self):\n"
               "        return iter(['rst', 'a', 'b'])\n"
               "class O:\n    __class__ = dict\n    def __eq__(self, o):\n        return True\n")
        for expr, reason in (("S('x')", "RETURN_TYPE"), ("O()", "RETURN_TYPE"), ("D()", "MISSING_KEYS"),
                             ("('rst',)", "RETURN_TYPE"), ("{'rst': S('0'), 'a': S('00'), 'b': 1}", "NON_STRING_VALUE"),
                             ("{'rst': '0', 'a': '00', 'b': '1', 7: '0'}", "EXTRA_KEYS")):
            with self.subTest(expr=expr):
                r = self.run1(source(pre=pre, step=f"return {expr}\n"))
                self.assertEqual(run_outcome(r).diagnostic, f"DRIVER_VECTOR_INVALID|reason={reason}")

    def test_process_end_and_memory(self):
        r = self.run1(source(step="reach()[1]._exit(0)\n"))
        self.assertEqual(run_outcome(r).diagnostic, "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=Exception")
        r = self.run1(source(step="x = bytearray(400 * 1024 * 1024)\n"))
        self.assertEqual(run_outcome(r).diagnostic, "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=MemoryError")

    def test_watchdog_still_kills(self):
        r = self.run1(source(step="while True:\n    pass\n"), step=2.0)
        self.assertEqual(run_outcome(r).diagnostic, "WATCHDOG_TIMEOUT|phase=driver_step")

    def test_hash_seed_is_fixed(self):  # A-036
        src = source(factory="raise type('H%d' % (hash('openvef') & 0xffffff), (Exception,), {})()\n")
        self.assertEqual(runtime.factory_checks(src), runtime.factory_checks(src))

    # --- checker
    def checker(self, body, trace=None):
        src = REACH + "def check_trace(trace, metadata):\n" + "".join("    " + x + "\n" for x in body.splitlines())
        return runtime.checker_invocation(src, [{"cycle_index": 0}] if trace is None else trace, {"design_id": "X"}, 6.0)

    def test_hostile_checker_cannot_change_its_classification(self):
        tamper = ("sysm, osm = reach()\n"
                  "bi = print.__self__\n"
                  "bi.isinstance = bi.set = bi.type = lambda *a: True\n"
                  "sysm.modules['json'].dumps = lambda *a, **k: '{}'\n"
                  "trace.clear()\n")
        self.assertEqual(self.checker(tamper + "return 'PASS'").error[1], "CHECKER_RETURN_INVALID|reason=NON_DICTIONARY")
        self.assertEqual(self.checker(tamper + "return {'verdict': 'FAIL', 'diagnostics': []}").verdict, "FAIL")
        self.assertEqual(self.checker("sysm, osm = reach()\nm = b'{\"value\":[\"d\",[]]}'\n"
                                      "osm.write(3, len(m).to_bytes(4, 'big') + m)\n"
                                      "return {'verdict': 'PASS', 'diagnostics': []}").error[1],
                         "CHECKER_RETURN_INVALID|reason=MISSING_DIAGNOSTICS")
        self.assertEqual(self.checker("reach()[1]._exit(0)").error[1], "CHECKER_RUNTIME_ERROR|class=Exception")
        self.assertEqual(self.checker("osm = reach()[1]\nosm.open('/proc/1/fd/1', 1)").error[1],
                         "CHECKER_RUNTIME_ERROR|class=PermissionError")


# --- wall-clock reads (D-016; File 30 §6 L101) ---------------------------------------------
NATIVE = ("import collections\n\ndef native(code):\n"
          "    c = collections._sys.modules['ctypes']\n    lib = c.CDLL(None)\n"
          "    lib.mmap.restype = c.c_void_p\n"
          "    lib.mmap.argtypes = [c.c_void_p, c.c_size_t, c.c_int, c.c_int, c.c_int, c.c_long]\n"
          "    p = lib.mmap(None, 4096, 7, 0x22, -1, 0)\n    code = bytes.fromhex(code)\n"
          "    c.memmove(p, code, len(code))\n    return c.CFUNCTYPE(c.c_long)(p)()\n\n")
RET64 = "48c1e2204809d0c3"  # shl rdx,32; or rax,rdx; ret


@unittest.skipUnless(DOCKER, "docker not available")
class WallClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()

    def factory(self, body, pre=""):
        """The class of the exception the factory ended with."""
        r = driver_run(source(pre=pre, factory=body), DESIGN, "rtl", 0, step_timeout_s=3.0, budget_s=30.0)
        prefix = "RUNTIME_EXCEPTION|file=driver.py|phase=factory|class="
        self.assertTrue(r["failure"]["diagnostic"].startswith(prefix), r)
        return r["failure"]["diagnostic"][len(prefix):]

    def test_python_clocks_are_denied(self):
        body = ("sysm, osm = reach()\nt = sysm.modules['time']\n"
                "def no(name, fn, *a):\n    try:\n        fn(*a)\n    except PermissionError:\n        return\n"
                "    raise type('Clock_' + name, (Exception,), {})()\n"
                "for n in ('time', 'time_ns', 'monotonic', 'monotonic_ns', 'perf_counter', 'perf_counter_ns',\n"
                "          'thread_time'):\n    no(n, getattr(t, n))\n"
                "for i in range(12):\n    no('id%d' % i, t.clock_gettime, i)\n"
                "no('sleep', t.sleep, 0.01)\n"
                "for fd in range(5):\n    no('fstat', osm.fstat, fd)\n"  # a pipe's mtime is the current time
                "no('stat', osm.stat, '/tmp')\nno('utime', osm.utime, '/tmp')\n"
                "if t.localtime()[0] != 1969 or t.gmtime()[0] != 1969 or not t.asctime().endswith('1969'):\n"
                "    raise type('Clock_calendar', (Exception,), {})()\n"
                "raise type('AllDenied', (Exception,), {})()\n")
        self.assertEqual(self.factory(body), "AllDenied")

    def test_process_time_does_not_advance_with_work(self):
        # CPython falls back to glibc times(), which hides the denied call and returns garbage.
        body = ("t = reach()[0].modules['time']\n"
                "seen = []\nfor i in range(4):\n    seen.append(t.process_time())\n    sum(range(4000000))\n"
                "raise type('Constant' if len(set(seen[1:])) == 1 else 'Varies', (Exception,), {})()\n")
        self.assertEqual(self.factory(body), "Constant")

    def test_libc_and_raw_system_calls_are_denied(self):
        body = ("sysm, osm = reach()\nc = sysm.modules['ctypes']\nlib = c.CDLL(None, use_errno=True)\n"
                "def check(name, ok):\n    if not ok:\n        raise type('Clock_' + name, (Exception,), {})()\n"
                "b = c.create_string_buffer(144)\n"
                "check('time', lib.time(None) == -1)\n"
                "check('gettimeofday', lib.gettimeofday(b, None) == -1 and not any(b.raw))\n"
                "for i in range(12):\n    check('clock_gettime', lib.clock_gettime(i, b) == -1 and not any(b.raw))\n"
                "check('timespec_get', lib.timespec_get(b, 1) != 1 or not any(b.raw))\n"
                # gettimeofday times time clock_gettime clock_getres clock_nanosleep fstat stat newfstatat statx
                # getrusage sysinfo adjtimex clock_adjtime nanosleep setitimer getitimer alarm timer_create
                # timerfd_create poll select ppoll epoll_create io_uring_setup perf_event_open bpf getcpu
                "for nr in (96, 100, 201, 228, 229, 230, 5, 4, 262, 332, 98, 99, 159, 305, 35, 38, 36, 37, 222,\n"
                "           283, 7, 23, 271, 213, 425, 298, 321, 309, 128, 232, 61, 302, 157):\n"
                "    c.set_errno(0)\n"
                "    check('syscall_%d' % nr, lib.syscall(nr, b, b, b, b, b) == -1 and c.get_errno() == 1)\n"
                # FUTEX_WAIT_BITSET|CLOCK_REALTIME with a deadline in the past: would say ETIMEDOUT
                "word, past = c.c_int(0), (c.c_long * 2)(1, 0)\n"
                "check('futex', lib.syscall(202, c.byref(word), 0x189, 0, past, None, -1) == -1 and c.get_errno() == 1)\n"
                "raise type('AllDenied', (Exception,), {})()\n")
        self.assertEqual(self.factory(body), "AllDenied")

    def test_native_clock_instructions(self):
        def run(code):
            return self.factory("raise type('V%d' % (native('" + code + "') & 0xffffffffffffffff), (Exception,), {})()\n",
                                pre=NATIVE)
        self.assertEqual(run("b82a000000c3"), "V42")  # control: native code does run
        # "Exception": the process was killed (A-054 fallback), so no value was obtained.
        for name, code in (("rdtsc", "0f31" + RET64), ("rdtscp", "0f01f9" + RET64), ("rdpmc", "31c90f33" + RET64),
                           ("rdpru", "31c90f01fd" + RET64), ("int80_time", "53b80d00000031dbcd805bc3")):
            with self.subTest(name=name):
                self.assertEqual(run(code), "Exception")
        # The legacy vsyscall page: time() returns -1, through the seccomp filter.
        self.assertEqual(run("4883ec0848c7c0000460ff31ffffd04883c408c3"), "V%d" % (2 ** 64 - 1))

    def test_route_through_allowed_imports_is_denied(self):
        # Passes every static rule (test below); denied only by the sandbox.
        self.assertEqual(self.factory("collections._sys.modules['time'].time()\n", pre="import collections\n\n"),
                         "PermissionError")

    def test_checker_is_denied_too(self):
        src = "import collections\n\ndef check_trace(trace, metadata):\n    collections._sys.modules['time'].time()\n"
        self.assertEqual(runtime.checker_invocation(src, [], {"design_id": "X"}, 6.0).error[1],
                         "CHECKER_RUNTIME_ERROR|class=PermissionError")

    def test_seeded_random_and_allowed_modules_still_work(self):
        body = ("r = random.Random(7)\n"
                "x = (r.random(), statistics.mean([1, 2]), json.dumps({'a': 1}), re.compile('a').match('a'))\n"
                "raise type('Works' if x[0] == " + repr(random.Random(7).random()) + " else 'Wrong', (Exception,), {})()\n")
        pre = "".join(f"import {m}\n" for m in ("collections", "copy", "functools", "itertools", "json", "math", "operator",
                                                "random", "re", "statistics", "typing")) + "\n"
        self.assertEqual(self.factory(body, pre=pre), "Works")


class StaticClockRouteTests(unittest.TestCase):
    """Which clock routes IMPORT_POLICY already rejects, and which only the sandbox stops."""

    def verdict(self, body):
        result = import_policy.check_import_policy({"driver.py": body, "checker.py": ""},
                                                   {"driver.py": ast.parse(body), "checker.py": ast.parse("")})
        return result.diagnostic if result is not None else None

    def test_rejected_statically(self):
        for module in ("time", "datetime", "os", "sys", "ctypes", "threading", "asyncio", "signal", "select", "resource"):
            self.assertEqual(self.verdict(f"import {module}\n"), f"IMPORT_NOT_ALLOWED|module={module}")
            self.assertEqual(self.verdict(f"def f():\n    from {module} import x\n"), f"IMPORT_NOT_ALLOWED|module={module}")
        for name, code in (("__import__", "__import__('time')"), ("eval", "eval('1')"), ("exec", "exec('1')"),
                           ("open", "open('/proc/uptime')")):
            self.assertEqual(self.verdict(f"def f():\n    return {code}\n"), f"PROHIBITED_BUILTIN|name={name}")
        self.assertEqual(self.verdict("import random\ndef f():\n    return random._os\n"),
                         "GLOBAL_RANDOM_USE|name=random._os")

    def test_not_rejected_statically(self):
        for code in ("import collections\ndef f():\n    return collections._sys.modules['time'].time()\n",
                     "import statistics\ndef f():\n    return statistics.sys.modules['time'].time()\n",
                     "import random\ndef f():\n    return getattr(random, '_os').times()\n",
                     "def f():\n    return object.__subclasses__()\n"):
            self.assertIsNone(self.verdict(code))


class StaticSeparationTests(unittest.TestCase):
    def test_only_the_worker_executes_artifact_source(self):
        sb = HERE.parent / "sandbox"
        for path in sb.glob("*.py"):
            tree = ast.parse(path.read_text("utf-8"))
            calls = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id in ("exec", "eval")]
            if path.name == "artifact_worker.py":
                self.assertEqual(len(calls), 1)
            elif path.name == "sim_cocotb.py":  # the design pack's legal-input predicate, not an artifact
                self.assertEqual(len(calls), 1)
            else:
                self.assertEqual(calls, [], path.name)

    def test_worker_imports_no_evaluator_module(self):
        tree = ast.parse((HERE.parent / "sandbox/artifact_worker.py").read_text("utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertLessEqual(names, {"__future__", "builtins", "inspect", "os", "sys", "types", "encodings", "importlib",
                                     "pkgutil", "ctypes", "resource", "struct", "json", "time"})


if __name__ == "__main__":
    unittest.main()
