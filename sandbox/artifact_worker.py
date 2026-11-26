"""The artifact process (D-015, audit A9-1): runs driver.py or checker.py and nothing else.

Started by artifact_proc.py, inside the D-002 container, as its own interpreter. It holds no
evaluator module, request, design material, trace file or simulator handle. It receives one
source text, then plain JSON messages, and sends plain JSON messages back; the evaluator
treats everything it sends as untrusted. Standard library only.

Before any artifact code runs it: moves the two pipes to private descriptors and closes every
other one; makes itself the first process the OOM killer picks; limits its address space; and
installs a seccomp allow-list (a few memory, pipe and exit system calls; everything else fails
with EPERM: clocks, opening any file, /proc, sockets, fork/exec, signals, ptrace). Artifact code can
therefore corrupt this interpreter, but only this interpreter, and the only effect it can have
outside is the bytes it sends as its own answers.

D-019 (audit A9-2): nothing this process says after artifact code has run can be trusted; artifact
code can replace any global or closure here, or write to the pipe itself. So the evaluator takes
the parameters from a separate process that is only ever sent `inspect`, which compiles the
source and never executes it. What is reported after execution (`constructed`, `loaded`) can only
count against the artifact.

Implements, on the artifact's side: File 30 §3 L27 restricted-runtime import and File 30 §6
"Enforce the same import allow-list statically and at runtime" (guarded_import).
"""
from __future__ import annotations

import builtins
import dis
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

# x86_64: read write close lseek mmap mprotect munmap brk rt_sigaction rt_sigprocmask
# rt_sigreturn sched_yield mremap madvise getpid exit sigaltstack gettid exit_group rseq.
# No clock (D-016): not time, gettimeofday or clock_gettime; not fstat (a pipe's mtime is the
# current time); not futex (an absolute CLOCK_REALTIME deadline tells whether it has passed).
SYSCALLS = (0, 1, 3, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25, 28, 39, 60, 131, 186, 231, 334)

# Names used after artifact code has run are bound here, so a patched `builtins` or `json`
# does not reach this file by accident. (Deliberate tampering is contained by the process.)
_b = {k: v for k, v in vars(builtins).items() if not k.startswith("__")}
globals().update(_b)
_real_import = builtins.__import__
_read, _write = os.read, os.write
_signature = inspect.signature
_KINDS = tuple((k, k.name) for k in inspect._ParameterKind)
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


def remove_clocks(libc) -> None:
    """D-016, File 30 §6 L101 ("denies ... wall-clock reads"): clocks that need no system call.

    vDSO: libc calls it without entering the kernel, so seccomp does not see it. Its code is
    replaced (its ELF headers stay) by "return -EPERM", which glibc reports as the error; the
    real clock system calls are denied by seccomp; the kernel's time data pages ([vvar*]) are unmapped. Time-stamp
    counter: PR_SET_TSC/PR_TSC_SIGSEGV makes RDTSC and RDTSCP fault.
    """
    import ctypes
    def maps():
        with open("/proc/self/maps") as f:
            rows = [line.split() for line in f]
        out = []
        for r in rows:
            if len(r) == 6 and r[5].startswith(("[vdso", "[vvar")):
                lo, hi = (int(x, 16) for x in r[0].split("-"))
                out.append((r[5], lo, hi - lo))
        return out
    ptr, size, num = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int
    libc.mmap.restype, libc.mmap.argtypes = ptr, (ptr, size, num, num, num, ctypes.c_long)
    libc.mremap.restype, libc.mremap.argtypes = ptr, (ptr, size, size, num, ptr)
    libc.mprotect.argtypes, libc.munmap.argtypes = (ptr, size, num), (ptr, size)
    failed = ptr(-1).value
    regions = maps()
    for name, lo, n in regions:
        if name.startswith("[vdso"):
            image = ctypes.string_at(lo, n)
            keep = int.from_bytes(image[32:40], "little") + (  # e_phoff + e_phentsize * e_phnum
                int.from_bytes(image[54:56], "little") * int.from_bytes(image[56:58], "little"))
            ret = bytes.fromhex("48c7c0ffffffffc3")  # mov rax, -EPERM; ret
            code = image[:keep] + b"\x90" * (n - keep - len(ret)) + ret
            new = libc.mmap(None, n, 3, 0x22, -1, 0)
            if new == failed:
                raise OSError("mmap")
            ctypes.memmove(new, code, n)
            if libc.mprotect(new, n, 5) != 0 or libc.mremap(new, n, n, 3, lo) != lo:  # MAYMOVE|FIXED
                raise OSError("vdso")
    for name, lo, n in regions:
        if name.startswith("[vvar") and libc.munmap(lo, n) != 0:
            raise OSError("vvar")
    if maps():
        raise OSError("vDSO or vvar still mapped")
    mode = num(0)
    if libc.prctl(26, 2, 0, 0, 0) != 0 or libc.prctl(25, ctypes.byref(mode), 0, 0, 0) != 0 or mode.value != 2:
        raise OSError("PR_SET_TSC")


def confine() -> None:
    import ctypes
    import resource
    import struct
    import time
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
    remove_clocks(libc)
    if libc.prctl(22, 2, ctypes.byref(fprog), 0, 0) != 0:  # SECCOMP_MODE_FILTER
        raise OSError(ctypes.get_errno(), "seccomp")
    def denied(call, *args):  # the confinement must be effective, not merely requested
        try:
            call(*args)
        except PermissionError:
            return
        raise OSError("confinement is not effective")
    denied(os.open, "/proc/self/status", os.O_RDONLY)
    denied(os.fstat, FD_OUT)
    for clock in (time.time, time.monotonic):
        denied(clock)
    for clock_id in range(12):
        denied(time.clock_gettime, clock_id)


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


def code_parameters(code, defaults: bool) -> list | None:
    """[name, kind, has default] from a code object (names/kinds/counts of inspect.signature)."""
    if code.co_flags & 0x380:  # coroutine, iterable coroutine, async generator
        return None
    names, n, k = code.co_varnames, code.co_argcount, code.co_kwonlyargcount
    out = [[p, "POSITIONAL_ONLY" if i < code.co_posonlyargcount else "POSITIONAL_OR_KEYWORD", defaults]
           for i, p in enumerate(names[:n])]
    i = n + k
    if code.co_flags & 4:
        out.append([names[i], "VAR_POSITIONAL", False])
        i += 1
    out += [[p, "KEYWORD_ONLY", defaults] for p in names[n:n + k]]
    if code.co_flags & 8:
        out.append([names[i], "VAR_KEYWORD", False])
    return out


def _bound_once(code, name: str):
    """(instructions, index) of the single STORE_NAME of `name`, if it is bound exactly once."""
    ins = [i for i in dis.get_instructions(code) if i.opname not in ("EXTENDED_ARG", "PRECALL", "CACHE")]
    at = [k for k, i in enumerate(ins) if i.opname.startswith(("STORE_", "DELETE_")) and i.argval == name]
    return (ins, at[0]) if len(at) == 1 and ins[at[0]].opname == "STORE_NAME" else (ins, None)


def _is_code(i, name: str) -> bool:
    return i.opname == "LOAD_CONST" and type(i.argval) is types.CodeType and i.argval.co_name == name


def defined_function(code, name: str) -> list | None:
    """Parameters of the plain undecorated `def name` that is the only binding of `name`."""
    ins, k = _bound_once(code, name)
    if k is None or k < 2 or ins[k - 1].opname != "MAKE_FUNCTION" or not _is_code(ins[k - 2], name):
        return None
    return code_parameters(ins[k - 2].argval, bool(ins[k - 1].arg & 3))


def defined_class(code, name: str):
    """The body code of the undecorated `class name` that is the only binding of `name`."""
    ins, k = _bound_once(code, name)
    starts = [j for j in range(k or 0) if ins[j].opname == "LOAD_BUILD_CLASS"]
    if not starts or ins[k - 1].opname != "CALL":
        return None
    j = starts[-1]
    ok = k - j >= 5 and _is_code(ins[j + 1], name) and ins[j + 2].opname == "MAKE_FUNCTION" and \
        sum(i.opname == "CALL" for i in ins[j:k]) == 1
    return ins[j + 1].argval if ok else None


def inspect_source(name: str, source: str) -> dict:
    """D-019: facts from compiled code objects. The source is compiled, never executed."""
    try:
        code = compile(source, name + ".py", "exec", dont_inherit=True)
    except Exception:
        return {}
    if name == "checker":
        return {"check_trace": defined_function(code, "check_trace")}
    body = defined_class(code, "Driver")
    return {"create_driver": defined_function(code, "create_driver"),
            "Driver.step": defined_function(body, "step") if body is not None else None}


def parameters(func) -> str:
    """Code-object measurement after execution: self-reported, never trusted."""
    try:
        if type(func) is not types.FunctionType:
            return "null"
        ps = code_parameters(func.__code__, bool(func.__defaults__ or func.__kwdefaults__))
        return "null" if ps is None else "[" + ",".join(
            "[" + _quote(n) + "," + _quote(k) + "," + ("true" if d else "false") + "]" for n, k, d in ps) + "]"
    except Exception:
        return "null"


def literal_signature(func) -> str:
    """File 30 L35/L37, literally (D-022): names and kinds from inspect.signature after import, or
    null if it raises. It honours __signature__ and __wrapped__. Self-reported, never trusted."""
    try:
        out = []
        for p in _signature(func).parameters.values():
            out.append("[" + _quote(_plain(p.name)) + "," + _quote(next(n for k, n in _KINDS if k is p.kind)) + "]")
        return "[" + ",".join(out) + "]"
    except BaseException:
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
        if op == "inspect":
            send(json.dumps({"inspected": inspect_source(msg["name"], msg["source"])}))
        elif op == "driver":
            phase = "import"
            try:
                module = load("driver", msg["source"])
                phase = "factory"
                instance = module.create_driver(msg["seed"])
            except BaseException as exc:
                send(raised(phase, exc))
                continue
            cls = getattr(module, "Driver", None)
            ok = type(cls) is type and cls in type.__dict__["__mro__"].__get__(type(instance))
            factory = getattr(module, "create_driver", None)
            step = cls.__dict__.get("step") if ok else None
            send('{"constructed":[' + ("true" if ok else "false") + "," + parameters(factory) + "," + parameters(step)
                 + "," + literal_signature(factory) + "," + literal_signature(getattr(cls, "step", None) if ok else None) + "]}")
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
            send('{"loaded":[' + parameters(check) + "," + literal_signature(check) + "]}")
        elif op == "check":
            try:
                value = check(msg["trace"], msg["metadata"])
            except BaseException as exc:
                send(raised("check", exc))
                continue
            send('{"value":' + encode(value) + "}")


if __name__ == "__main__":
    main()
