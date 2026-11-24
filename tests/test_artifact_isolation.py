"""Adversarial tests for artifact process isolation (D-015, audit A9-1), in the pinned container.

Hostile drivers and checkers go straight to the runtime (the static stages would reject most
of them) and must not alter any trace row, event or result. Skipped only without Docker; a skip
is never a pass.
"""
from __future__ import annotations

import ast
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from openvef import runtime, sandbox  # noqa: E402
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
                                     "pkgutil", "ctypes", "resource", "struct", "json"})


if __name__ == "__main__":
    unittest.main()
