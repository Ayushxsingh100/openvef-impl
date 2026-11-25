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


# --- forged runtime checks (D-019, audit A9-2; File 30 §3 L35, L37, L39) ----------------------
GOOD = {"create_driver": '[["seed","POSITIONAL_OR_KEYWORD",false]]',
        "step": '[["self","POSITIONAL_OR_KEYWORD",false],["cycle_index","POSITIONAL_OR_KEYWORD",false],'
                '["outputs_after_edge","POSITIONAL_OR_KEYWORD",false]]',
        "check": '[["trace","POSITIONAL_OR_KEYWORD",false],["metadata","POSITIONAL_OR_KEYWORD",false]]'}
CONSTRUCTED = '{"constructed":[true,' + GOOD["create_driver"] + "," + GOOD["step"] + "]}"
LOADED = '{"loaded":' + GOOD["check"] + "}"


def forgeries(answer, good):
    """The auditor's routes (A9-2) and others, as statements run before the worker measures."""
    main = "w = collections._sys.modules['__main__']\n"
    frame = f"b = {answer!r}.encode()\n"
    return {
        "replace parameters": main + f"g = {list(good)!r}\nw.parameters = lambda f: g.pop(0)\n",
        "replace parameters and isinstance": main + f"g = {list(good)!r}\nw.parameters = lambda f: g.pop(0)\n"
                                                    "w.isinstance = lambda *a: True\n",
        "replace code_parameters": main + "w.code_parameters = lambda *a: None\nw._quote = lambda t: t\n"
                                          f"g = {list(good)!r}\nw.parameters = lambda f: g.pop(0)\n",
        "replace send": main + f"s = w.send\nw.send = lambda body: s({answer!r})\n",
        "replace code object": main + f"g = {answer!r}\nw.send.__code__ = (lambda body: _write(3, len(G).to_bytes(4, 'big')"
                                      " + G)).__code__\nw.G = g.encode()\n",
        "replace builtins": main + f"g = {list(good)!r}\nw.parameters = lambda f: g.pop(0)\n"
                                   "bi = print.__self__\nbi.isinstance = bi.issubclass = lambda *a: True\n",
        "pipe write then exit": frame + "o = collections._sys.modules['os']\n"
                                        "o.write(3, len(b).to_bytes(4, 'big') + b)\no._exit(0)\n",
        "pipe write then hang": frame + "o = collections._sys.modules['os']\n"
                                        "o.write(3, len(b).to_bytes(4, 'big') + b)\nwhile True:\n    pass\n"}


def block(text, n=4):
    return "".join(" " * n + x + "\n" for x in text.splitlines())


STEP = "class Driver:\n    def step({params}):\n        return 'COMPLETE'\n\n"
OK_STEP = STEP.format(params="self, cycle_index, outputs_after_edge")
DRIVER_FORGERIES = forgeries(CONSTRUCTED, (GOOD["create_driver"], GOOD["step"]))
CHECKER_FORGERIES = forgeries(LOADED, (GOOD["check"],))
CHECKER_OK = "def check_trace(trace, metadata):\n    return {'verdict': 'PASS', 'diagnostics': []}\n"


def static_stages(driver, checker=CHECKER_OK):
    from openvef.ast_signature import check_ast_signature, check_compile
    from openvef.source_ast import check_sources
    sources = {"driver.py": driver, "checker.py": checker}
    trees = check_sources(list(sources.items()))
    return import_policy.check_import_policy(sources, trees) or check_ast_signature(trees) or check_compile(sources)


@unittest.skipUnless(DOCKER, "docker not available")
class ForgedRuntimeCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()

    def diag(self, src):
        r = runtime.factory_checks(src, timeout_s=8.0)
        return None if r is None else r.diagnostic

    def test_a_wrong_definition_cannot_be_forged_right(self):
        """Parameters are measured where no artifact code has run, so no forgery reaches them."""
        reject = "ENTRY_POINT_REJECT|file=driver.py|symbol={}|reason=RUNTIME_SIGNATURE"
        for name, forge in DRIVER_FORGERIES.items():
            for params in ("self, *a", "self, cycle_index, outputs_after_edge, x=1"):
                with self.subTest(forge=name, step=params):
                    src = ("import collections\n\n" + STEP.format(params=params)
                           + "def create_driver(seed):\n" + block(forge) + "    return Driver()\n")
                    self.assertEqual(self.diag(src), reject.format("Driver.step"))
        for head in ("seed, extra=1", "*seed", "seed, /", "seed, *, k=0"):
            for name in ("replace send", "replace parameters", "pipe write then exit"):
                with self.subTest(forge=name, head=head):
                    src = ("import collections\n\n" + OK_STEP + f"def create_driver({head}):\n"
                           + block(DRIVER_FORGERIES[name]) + "    return Driver()\n")
                    self.assertEqual(self.diag(src), reject.format("create_driver"))

    def test_forgery_at_import_time(self):
        """Helper defaults run at import (the static stages accept them): no help to the forger."""
        src = ("import collections\n\ndef forge(x=collections._sys.modules['__main__'].__dict__.update(\n"
               f"        parameters=lambda f, g={[GOOD['create_driver'], GOOD['step']]!r}: g.pop(0))):\n    return x\n\n")
        self.assertIsNone(static_stages(src + OK_STEP + "def create_driver(seed):\n    return Driver()\n"))
        self.assertEqual(self.diag(src + STEP.format(params="self, *a") + "def create_driver(seed):\n    return Driver()\n"),
                         "ENTRY_POINT_REJECT|file=driver.py|symbol=Driver.step|reason=RUNTIME_SIGNATURE")

    def test_spoofed_signature_attribute_is_ignored(self):
        src = (STEP.format(params="self, *a") + "def create_driver(seed):\n"
               "    def good(self, cycle_index, outputs_after_edge):\n        return None\n"
               "    Driver.step.__wrapped__ = good\n    Driver.step.__signature__ = good\n    return Driver()\n")
        self.assertEqual(self.diag(src), "ENTRY_POINT_REJECT|file=driver.py|symbol=Driver.step|reason=RUNTIME_SIGNATURE")
        dynamic = (OK_STEP + "def create_driver(seed):\n    def good(self, cycle_index, outputs_after_edge):\n"
                   "        return None\n    def v(*a):\n        return 'COMPLETE'\n    v.__wrapped__ = good\n"
                   "    Driver.step = v\n    return Driver()\n")
        self.assertEqual(self.diag(dynamic), "ENTRY_POINT_REJECT|file=driver.py|symbol=Driver.step|reason=RUNTIME_SIGNATURE")
        self.assertIsNone(static_stages(dynamic))

    def test_class_spoof_is_not_a_driver(self):
        src = OK_STEP + ("def create_driver(seed):\n    o = type('O', (), {'__class__': Driver})()\n"
                         "    o.step = len\n    return o\n")
        self.assertEqual(self.diag(src), "ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE")

    def test_checker_definition_cannot_be_forged_right(self):
        for name, forge in CHECKER_FORGERIES.items():
            if name == "pipe write then hang":  # ends as a timeout: no verdict (below)
                continue
            with self.subTest(forge=name):
                src = ("import collections\n\ndef check_trace(trace, *metadata):\n"
                       "    return {'verdict': 'PASS', 'diagnostics': []}\n" + forge)
                r = runtime.checker_invocation(src, [], {}, 8.0)
                self.assertEqual(r.diagnostic, "ENTRY_POINT_REJECT|file=checker.py|symbol=check_trace|reason=RUNTIME_SIGNATURE")

    def test_residual_forged_state_after_execution(self):
        """NOT closed (docs/sandbox.md "Runtime checks"): state that exists only after artifact code
        has run is self-reported, so a forger passes. Pinned here so that the limit is visible; every
        such source is marked SELF_REPORTED by the evaluator, whatever the process says."""
        from openvef.runtime_basis import SELF_REPORTED, basis
        bodies = {"dynamic variadic step": "def v(*a):\n    return 'COMPLETE'\nDriver.step = v\n{}return Driver()\n",
                  "not a Driver": "{}return len\n"}
        for what, body in bodies.items():
            for name in ("replace send", "replace code object", "pipe write then exit"):
                with self.subTest(what=what, forge=name):
                    src = "import collections\n\n" + OK_STEP + "def create_driver(seed):\n" + \
                        block(body.format(DRIVER_FORGERIES[name]))
                    self.assertIsNone(self.diag(src))
                    self.assertEqual(basis("driver.py", src)["basis"], SELF_REPORTED)
        # A forger that is no driver at all gains nothing in a run: its next answer fails it.
        src = "import collections\n\n" + OK_STEP + "def create_driver(seed):\n" + \
            block(DRIVER_FORGERIES["replace send"] + "return len\n")
        r = driver_run(src, DESIGN, "rtl", 0, step_timeout_s=3.0, budget_s=30.0)
        self.assertEqual([e["kind"] for e in r["events"]], ["driver_runtime"])


class RuntimeBasisTests(unittest.TestCase):
    """src/openvef/runtime_basis.py (D-019): no container needed."""

    def basis(self, driver):
        from openvef.runtime_basis import basis
        return basis("driver.py", driver)["basis"]

    def make(self, factory, pre="", step="return 'COMPLETE'", post=""):
        return (pre + "class Driver:\n    def step(self, cycle_index, outputs_after_edge):\n" + block(step, 8)
                + "\ndef create_driver(seed):\n" + block(factory) + post)

    def test_ordinary_drivers_are_proven(self):
        for src in (self.make("return Driver()"),
                    self.make("d = Driver()\nd.rng = random.Random(seed)\nd.q = [0] * 4\nreturn d", "import random\n\n",
                              "v = {'a': format(self.rng.randrange(4), '02b')}\nself.q.append(int(v['a'], 2))\nreturn v"),
                    self.make("if seed:\n    d = Driver()\n    return d\nreturn Driver()"),
                    self.make("d = Driver()\nd.x = math.floor(seed / 2)\nreturn d", "import math\n\nLIMIT = 4\n\n")):
            with self.subTest(src=src):
                self.assertIsNone(static_stages(src))
                self.assertEqual(self.basis(src), "PROVEN")

    def test_anything_else_is_not(self):
        imp = "import collections\n\n"
        cases = [self.make(f, imp) for f in (
            "return None", "pass", "yield Driver()", "d = Driver()\nd = len\nreturn d", "d = seed or Driver()\nreturn d",
            "d = Driver()\nfor d in (1,):\n    pass\nreturn d", "d = Driver()\ntry:\n    pass\nexcept Exception as d:\n    pass\nreturn d",
            "d = Driver()\n[d := x for x in (1,)]\nreturn d", "d = Driver()\ndef d():\n    return 1\nreturn d",
            "if seed:\n    return Driver()", "c = Driver\nreturn c()", "Driver.step = len\nreturn Driver()",
            "d = Driver()\nd.step = len\nreturn d", "d = Driver()\nsetattr(d, 'step', len)\nreturn d",
            "d = Driver()\nd.__class__ = int\nreturn d", "type(Driver()).step = len\nreturn Driver()",
            "vars(Driver)\nreturn Driver()", "global Driver\nDriver = len\nreturn Driver()", "Driver = len\nreturn Driver()",
            "collections._sys\nreturn Driver()", "m = collections\nreturn Driver()", "collections.abc\nreturn Driver()",
            "print.__self__\nreturn Driver()", "globals()\nreturn Driver()", "getattr(1, 'x')\nreturn Driver()",
            "g = (x for x in ())\ng.gi_frame.f_globals\nreturn Driver()", "__builtins__\nreturn Driver()",
            "try:\n    1 / 0\nexcept Exception as e:\n    e.__traceback__\nreturn Driver()",
            "create_driver.x = 1\nreturn Driver()", "exit()\nreturn Driver()",
            "match seed:\n    case int(__class__=c):\n        pass\nreturn Driver()",
            "import random\nrandom._os\nreturn Driver()", "import statistics\nstatistics.sys\nreturn Driver()",
            "import operator\noperator.attrgetter('__class__')\nreturn Driver()",
            "import json\njson.codecs\nreturn Driver()", "import copy\ncopy.types\nreturn Driver()",
            "import collections as c\nreturn Driver()", "from random import Random\nreturn Driver()")]
        cases += [self.make("return Driver()", step="self.step = len\nreturn 'COMPLETE'"),
                  self.make("return Driver()", step="Driver.step = len\nreturn 'COMPLETE'"),
                  self.make("return Driver()", post="\nclass Driver:\n    pass\n"),
                  self.make("return Driver()", post="\ndef h(Driver):\n    return Driver()\n"),
                  self.make("return Driver()", post="\ndef h(x=print.__self__):\n    return x\n"),
                  self.make("return Driver()", pre="def h():\n    global Driver\n    Driver = 1\n\n")]
        for src in cases:
            with self.subTest(src=src):
                self.assertEqual(self.basis(src), "SELF_REPORTED")

    def test_every_forgery_is_not_proven(self):
        from openvef.runtime_basis import basis
        for name, forge in DRIVER_FORGERIES.items():
            with self.subTest(forge=name):
                self.assertEqual(self.basis(self.make(forge + "return Driver()", "import collections\n\n")), "SELF_REPORTED")
        for name, forge in CHECKER_FORGERIES.items():
            with self.subTest(checker=name):
                src = "import collections\n\ndef check_trace(trace, metadata):\n" + block(forge) + "    return {}\n"
                self.assertEqual(basis("checker.py", src)["basis"], "SELF_REPORTED")
        self.assertEqual(basis("checker.py", CHECKER_OK)["basis"], "PROVEN")


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
        self.assertLessEqual(names, {"__future__", "builtins", "dis", "os", "sys", "types", "encodings", "importlib",
                                     "pkgutil", "ctypes", "resource", "struct", "json", "time"})


if __name__ == "__main__":
    unittest.main()
