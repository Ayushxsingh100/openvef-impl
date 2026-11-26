"""Evaluator side of the artifact process (D-015, audit A9-1).

No artifact code runs in this interpreter. `ArtifactProcess` starts artifact_worker.py, sends
plain JSON and accepts only frames that match the exact message schema; a value is rebuilt here
from tagged plain data, so no artifact object, method or type reaches evaluator code. The
verdicts (File 30 §3 L27, L35, L37; L97; Protocol L166 (7)) are computed here.

A-054 (docs/ambiguities.md): an artifact process that ends, or breaks the message schema, has
failed as the artifact's own code (`class=Exception`, the L125 fallback). A process killed by
SIGKILL (out of memory) or one that never became ready is an evaluator-side error.
"""
from __future__ import annotations

import json
import os
import re
import select
import signal
import subprocess
from typing import Any, Optional

WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifact_worker.py")
PYTHON = "/usr/local/bin/python3.11"
# Not `-I`: that implies -E, which would ignore PYTHONHASHSEED (A-036). -P and -s keep the
# script directory and user site off the path, and the environment is exactly this.
COMMAND = (PYTHON, "-P", "-s", "-W", "ignore", WORKER)
ENV = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C.UTF-8"}
MAX_FRAME = 4 * 1024 * 1024
_EXC = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
REQUIRED_SIGNATURES = {
    "create_driver": ("seed",),
    "Driver.step": ("self", "cycle_index", "outputs_after_edge"),
    "check_trace": ("trace", "metadata"),
}


class ArtifactFailed(Exception):
    """The artifact's own failure: raised, ended, or broke the message schema."""

    def __init__(self, phase: str, exception_class: str):
        super().__init__(f"{phase}: {exception_class}")
        self.phase, self.exception_class = phase, exception_class


class ArtifactHostError(RuntimeError):
    """The artifact process could not be confined, or was killed from outside."""


class Opaque:
    """A value of a type that has no plain form (never equal to anything plain)."""


def class_token(name: Any) -> str:
    return name if isinstance(name, str) and _EXC.fullmatch(name) else "Exception"


def decode(node: Any) -> Any:
    """Tagged form -> plain Python data. Raises ValueError on anything else."""
    if not (isinstance(node, list) and node and isinstance(node[0], str)):
        raise ValueError("node")
    tag, rest = node[0], node[1:]
    if tag in ("n", "b", "i", "o") and not rest:
        return {"n": None, "b": True, "i": 0}.get(tag) if tag != "o" else Opaque()
    if tag == "s" and len(rest) == 1 and isinstance(rest[0], str):
        return rest[0]
    if tag == "l" and len(rest) == 1 and isinstance(rest[0], list):
        return [decode(n) for n in rest[0]]
    if tag == "d" and len(rest) == 1 and isinstance(rest[0], list):
        out: dict = {}
        for pair in rest[0]:
            if not (isinstance(pair, list) and len(pair) == 2):
                raise ValueError("pair")
            key, value = decode(pair[0]), decode(pair[1])
            out[key if isinstance(key, str) and key not in out else Opaque()] = value
        return out
    raise ValueError("tag")


def _is_params(value: Any) -> bool:
    return value is None or (isinstance(value, list) and all(
        isinstance(p, list) and len(p) == 3 and isinstance(p[0], str) and isinstance(p[1], str)
        and isinstance(p[2], bool) for p in value))


def _is_literal(value: Any) -> bool:
    return value is None or (isinstance(value, list) and all(
        isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) and isinstance(p[1], str) for p in value))


def inspect_source(name: str, source: str) -> dict:
    """{symbol: parameters or None} from a fresh process that compiles and never executes the
    source (D-019). No artifact code has run in it, so its answer can be trusted."""
    with ArtifactProcess() as p:
        try:
            facts = p._call("inspect", {"op": "inspect", "name": name, "source": source}, "inspected")
        except ArtifactFailed as exc:
            raise ArtifactHostError("inspection process failed") from exc
    if not (isinstance(facts, dict) and all(_is_params(v) for v in facts.values())):
        raise ArtifactHostError("inspection process answer")
    return facts


def signature_ok(params: Optional[list], symbol: str) -> bool:
    """File 30 L35/L37: the same parameter names, kinds and counts, no defaults."""
    return params == [[n, "POSITIONAL_OR_KEYWORD", False] for n in REQUIRED_SIGNATURES[symbol]]


def runtime_signature_ok(trusted: Optional[list], reported: Optional[list], literal: Optional[list], symbol: str) -> bool:
    """The trusted definition and the code object after execution are as required, and
    inspect.signature after import did not raise and gives the trusted names/kinds/counts (D-022)."""
    return (signature_ok(trusted, symbol) and signature_ok(reported, symbol)
            and literal == [p[:2] for p in trusted])


class ArtifactProcess:
    def __init__(self) -> None:
        self._p = subprocess.Popen(COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   env=dict(ENV), cwd="/", close_fds=True)
        try:
            ready = self._receive()
        except (EOFError, ValueError) as exc:
            raise ArtifactHostError("artifact process did not start confined") from exc
        if ready != {"ready": True}:
            raise ArtifactHostError("artifact process did not start confined")

    def __enter__(self) -> "ArtifactProcess":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        self._p.kill()
        self._p.wait()
        self._p.stdin.close()
        self._p.stdout.close()

    def _exactly(self, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = os.read(self._p.stdout.fileno(), min(n - len(data), 65536))
            if not chunk:
                raise EOFError
            data += chunk
        return data

    def _receive(self) -> Any:
        size = int.from_bytes(self._exactly(4), "big")
        if size > MAX_FRAME:
            raise ValueError("frame too large")
        return json.loads(self._exactly(size).decode("ascii"))

    def _call(self, phase: str, message: dict, key: str) -> Any:
        """One request, one reply; the reply must be {key: ...} or {"raised": [phase, class]}."""
        data = json.dumps(message, ensure_ascii=True).encode("ascii")
        try:
            # Bytes waiting before the request was sent cannot be an answer to it.
            if select.select([self._p.stdout], [], [], 0)[0]:
                raise ValueError("unsolicited data")
            view = memoryview(len(data).to_bytes(4, "big") + data)
            while view:
                view = view[os.write(self._p.stdin.fileno(), view):]
            reply = self._receive()
            if not (isinstance(reply, dict) and len(reply) == 1):
                raise ValueError("reply")
            if "raised" in reply:
                r = reply["raised"]
                if not (isinstance(r, list) and len(r) == 2 and isinstance(r[0], str)):
                    raise ValueError("raised")
                raise ArtifactFailed(phase, class_token(r[1]))
            if key not in reply:
                raise ValueError("key")
            return decode(reply[key]) if key == "value" else reply[key]
        except (EOFError, BrokenPipeError, ValueError, RecursionError, UnicodeDecodeError) as exc:
            if isinstance(exc, (EOFError, BrokenPipeError)) and self._p.wait() == -signal.SIGKILL:
                raise ArtifactHostError("artifact process was killed (memory limit)") from exc
            raise ArtifactFailed(phase, "Exception") from exc

    # --- operations
    def construct(self, source: str, seed: int) -> tuple[bool, tuple, tuple]:
        """Import and create_driver: (return type ok, create_driver, step), each symbol as
        (code-object parameters, inspect.signature), all self-reported after artifact code
        ran: usable only against the artifact (D-019, D-022)."""
        facts = self._call("factory", {"op": "driver", "source": source, "seed": seed}, "constructed")
        if not (isinstance(facts, list) and len(facts) == 5 and isinstance(facts[0], bool)
                and _is_params(facts[1]) and _is_params(facts[2]) and _is_literal(facts[3]) and _is_literal(facts[4])):
            raise ArtifactFailed("factory", "Exception")
        return facts[0], (facts[1], facts[3]), (facts[2], facts[4])

    def step(self, cycle_index: int, outputs: dict) -> Any:
        return self._call("step", {"op": "step", "cycle_index": cycle_index, "outputs": outputs}, "value")

    def load_checker(self, source: str) -> tuple:
        """(code-object parameters, inspect.signature) of check_trace, self-reported."""
        facts = self._call("import", {"op": "checker", "source": source}, "loaded")
        if not (isinstance(facts, list) and len(facts) == 2 and _is_params(facts[0]) and _is_literal(facts[1])):
            raise ArtifactFailed("import", "Exception")
        return facts[0], facts[1]

    def check(self, trace: Any, metadata: Any) -> Any:
        return self._call("check", {"op": "check", "trace": trace, "metadata": metadata}, "value")
