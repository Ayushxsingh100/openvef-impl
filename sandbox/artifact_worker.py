"""The artifact process (D-015, audit A9-1): runs driver.py or checker.py and nothing else.

Started by artifact_proc.py, inside the D-002 container, as its own interpreter. It holds no
evaluator module, request, design material, trace file or simulator handle. It receives one
source text, then plain JSON messages, and sends plain JSON messages back; the evaluator
treats everything it sends as untrusted. Standard library only.

Before any artifact code runs it: moves the two pipes to private descriptors and closes every
other one; makes itself the first process the OOM killer picks; limits its address space; and
installs a seccomp allow-list (a few memory, pipe and exit system calls; everything else fails
with EPERM: opening any file, /proc, sockets, fork/exec, signals, ptrace). Artifact code can
therefore corrupt this interpreter, but only this interpreter, and the only effect it can have
outside is the bytes it sends as its own answers.

Implements, on the artifact's side: File 30 §3 L27 restricted-runtime import and File 30 §6
"Enforce the same import allow-list statically and at runtime" (guarded_import). What is
measured here (return type, signatures) is reported as facts; the verdict is the evaluator's.
"""
from __future__ import annotations

import builtins
import inspect
import os
import sys
import types

ALLOWED_ROOTS = frozenset({"__future__", "collections", "copy", "functools", "itertools", "json", "math",
                           "operator", "random", "re", "statistics", "typing"})
ARTIFACT_MODULES = frozenset({"driver", "checker"})
ADDRESS_SPACE = 160 * 1024 * 1024  # build default
MAX_FRAME, MAX_NODES, MAX_DEPTH = 4 * 1024 * 1024, 200_000, 20
FD_OUT, FD_IN = 3, 4

# x86_64: read write close fstat lseek mmap mprotect munmap brk rt_sigaction rt_sigprocmask
# rt_sigreturn sched_yield mremap madvise getpid exit sigaltstack gettid time futex
# clock_gettime exit_group rseq
SYSCALLS = (0, 1, 3, 5, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25, 28, 39, 60, 131, 186, 201, 202, 228, 231, 334)

# Names used after artifact code has run are bound here, so a patched `builtins` or `json`
# does not reach this file by accident. (Deliberate tampering is contained by the process.)
_b = {k: v for k, v in vars(builtins).items() if not k.startswith("__")}
globals().update(_b)
_real_import = builtins.__import__
_read, _write = os.read, os.write
_str_all = slice(None)


def preload() -> None:
    """Everything artifact code may need lazily: no file can be opened later."""
    import encodings
    import importlib
    import pkgutil
    for root in sorted(ALLOWED_ROOTS):
        _real_import(root)
    for name in ("collections.abc", "traceback", "linecache", "tracemalloc", "contextlib", "unicodedata"):
        importlib.import_module(name)
    for m in pkgutil.iter_modules(encodings.__path__):
        if m.name not in ("mbcs", "oem", "cp65001"):
            try:
                importlib.import_module(f"encodings.{m.name}")
            except ImportError:
                pass
    for name in ("ascii", "latin-1", "utf-8", "utf-16", "utf-32", "utf-7", "unicode_escape", "raw_unicode_escape",
                 "cp1252", "hex", "idna"):
        try:
            "a".encode(name)
        except (LookupError, TypeError):
            pass


def confine() -> None:
    import ctypes
    import resource
    import struct
    os.dup2(os.dup(1), 10)
    os.dup2(os.dup(0), 11)
    null = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(null, fd)
    os.dup2(10, FD_OUT)
    os.dup2(11, FD_IN)
    os.closerange(5, 256)
    with open("/proc/self/oom_score_adj", "w") as f:
        f.write("1000")
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE, ADDRESS_SPACE))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    libc = ctypes.CDLL(None, use_errno=True)

    def ins(code, jt, jf, k):
        return struct.pack("HBBI", code, jt, jf, k)
    prog = [ins(0x20, 0, 0, 4), ins(0x15, 1, 0, 0xC000003E), ins(0x06, 0, 0, 0x80000000), ins(0x20, 0, 0, 0)]
    for nr in SYSCALLS:
        prog += [ins(0x15, 0, 1, nr), ins(0x06, 0, 0, 0x7FFF0000)]
    prog.append(ins(0x06, 0, 0, 0x00050001))  # ERRNO(EPERM)
    buf = ctypes.create_string_buffer(b"".join(prog))

    class Fprog(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]
    fprog = Fprog(len(prog), ctypes.cast(buf, ctypes.c_void_p))
    if libc.prctl(1, 9, 0, 0, 0) != 0 or libc.prctl(38, 1, 0, 0, 0) != 0:  # PDEATHSIG, NO_NEW_PRIVS
        raise OSError("prctl")
    if libc.prctl(22, 2, ctypes.byref(fprog), 0, 0) != 0:  # SECCOMP_MODE_FILTER
        raise OSError(ctypes.get_errno(), "seccomp")
    try:  # the confinement must be effective, not merely requested
        os.open("/proc/self/status", os.O_RDONLY)
    except PermissionError:
        return
    raise OSError("seccomp is not effective")


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    """The static allow-list, applied again to imports made by artifact code."""
    importer = (globals or {}).get("__name__")
    if importer in ARTIFACT_MODULES:
        if level != 0 or name.split(".", 1)[0] not in ALLOWED_ROOTS:
            raise ImportError(f"import of {name!r} is not allowed")
    return _real_import(name, globals, locals, fromlist, level)


# --- messages ----------------------------------------------------------------------------

def _quote(text: str) -> str:
    out = ['"']
    for ch in text:
        n = ord(ch)
        if ch in '"\\':
            out.append("\\" + ch)
        elif 32 <= n < 127:
            out.append(ch)
        elif n > 0xFFFF:
            n -= 0x10000
            out.append("\\u%04x\\u%04x" % (0xD800 + (n >> 10), 0xDC00 + (n & 0x3FF)))
        else:
            out.append("\\u%04x" % n)
    out.append('"')
    return "".join(out)


def _plain(text) -> str:
    return str.__getitem__(text, _str_all)


def encode(value, depth=0, budget=None) -> str:
    """Tagged plain form: s(tr) d(ict) l(ist) i(nt) b(ool) n(one) o(ther). No object crosses."""
    budget = budget if budget is not None else [MAX_NODES]
    budget[0] -= 1
    if depth > MAX_DEPTH or budget[0] < 0:
        return '["o"]'
    try:
        if value is None:
            return '["n"]'
        if value is True or value is False:
            return '["b"]'
        if type(value) is int:
            return '["i"]'
        if isinstance(value, str):
            return '["s",' + _quote(_plain(value)) + "]"
        if isinstance(value, dict):
            items = ["[" + encode(k, depth + 1, budget) + "," + encode(v, depth + 1, budget) + "]"
                     for k, v in dict.items(value)]
            return '["d",[' + ",".join(items) + "]]"
        if isinstance(value, list):
            return '["l",[' + ",".join([encode(v, depth + 1, budget) for v in list.__iter__(value)]) + "]]"
    except Exception:
        pass
    return '["o"]'


def send(body: str) -> None:
    data = body.encode("ascii")
    if len(data) > MAX_FRAME:
        data = b'{"value":["o"]}'
    data = len(data).to_bytes(4, "big") + data
    while data:
        data = data[_write(FD_OUT, data):]


def receive() -> bytes:
    def exactly(n):
        chunks = []
        while n:
            c = _read(FD_IN, n)
            if not c:
                os._exit(0)
            chunks.append(c)
            n -= len(c)
        return b"".join(chunks)
    return exactly(int.from_bytes(exactly(4), "big"))


def exc_name(exc) -> str:
    try:
        return _plain(type(exc).__name__)
    except BaseException:
        return "Exception"


def raised(phase: str, exc) -> str:
    return '{"raised":[' + _quote(phase) + "," + _quote(exc_name(exc)) + "]}"


def parameters(func) -> str:
    """The runtime signature as plain facts, or null if there is none."""
    try:
        ps = list(inspect.signature(func).parameters.values())
        return "[" + ",".join("[" + _quote(_plain(p.name)) + "," + _quote(p.kind.name) + ","
                              + ("true" if p.default is not inspect.Parameter.empty else "false") + "]" for p in ps) + "]"
    except (TypeError, ValueError):
        return "null"


def load(name: str, source: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = name + ".py"
    sys.modules[name] = module
    exec(compile(source, name + ".py", "exec", dont_inherit=True), module.__dict__)
    return module


def main() -> None:
    import json
    preload()
    scan = json.JSONDecoder().scan_once  # bound before artifact code
    confine()
    builtins.__import__ = guarded_import
    send('{"ready":true}')
    instance = check = None
    while True:
        msg = scan(receive().decode("ascii"), 0)[0]
        op = msg["op"]
        if op == "driver":
            phase = "import"
            try:
                module = load("driver", msg["source"])
                phase = "factory"
                instance = module.create_driver(msg["seed"])
            except BaseException as exc:
                send(raised(phase, exc))
                continue
            cls = getattr(module, "Driver", None)
            ok = isinstance(cls, type) and isinstance(instance, cls)
            send('{"constructed":[' + ("true" if ok else "false") + "," + parameters(module.create_driver) + ","
                 + (parameters(cls.__dict__.get("step")) if ok else "null") + "]}")
        elif op == "step":
            try:
                value = instance.step(msg["cycle_index"], msg["outputs"])
            except BaseException as exc:
                send(raised("step", exc))
                continue
            send('{"value":' + encode(value) + "}")
        elif op == "checker":
            try:
                module = load("checker", msg["source"])
            except BaseException as exc:
                send(raised("import", exc))
                continue
            check = getattr(module, "check_trace", None)
            send('{"loaded":' + parameters(check) + "}")
        elif op == "check":
            try:
                value = check(msg["trace"], msg["metadata"])
            except BaseException as exc:
                send(raised("check", exc))
                continue
            send('{"value":' + encode(value) + "}")


if __name__ == "__main__":
    main()
