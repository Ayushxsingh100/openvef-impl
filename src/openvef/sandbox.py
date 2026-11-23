"""Launcher for the artifact-execution sandbox (owner decisions D-002, D-002a, D-003).

Evidence runs (D-002a): the runner itself runs in the pinned image and `run_harness`
sends each request to the host broker (runner/run_f18_container.sh), which starts the
artifact container. Development: `run_in_sandbox` starts the container directly. Both
use the flags in runner/artifact-container.args, which set:

  --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges
  --user 10001:10001 --tmpfs /tmp (noexec, nosuid, nodev, size-limited)
  --pids-limit, --memory/--memory-swap, --cpus, --ulimit nofile
  an empty environment apart from fixed PYTHON* variables
  the harness directory bind-mounted read-only
  a host wall-clock timeout that kills and removes the container.

File 30 §3 L39: "Runtime signature checks and the `create_driver` return-type check run
after import in the restricted execution container. The container sandbox is the
security boundary". File 30 §6: "The runtime sandbox denies network, filesystem access
beyond the designated temporary output directory, environment variables, wall-clock
reads, subprocess and simulator access." See docs/sandbox.md.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO / "sandbox" / "Dockerfile"
HARNESS_DIR = REPO / "sandbox"
ARTIFACT_ARGS = REPO / "runner" / "artifact-container.args"
# D-002: python:3.11.18-slim pinned by digest (resolved 23 Nov 2026, linux/amd64).
BASE_IMAGE_DIGEST = "python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535"
HARNESS_COMMAND = ("python", "-I", "/opt/openvef/harness.py")

DEFAULT_TIMEOUT_S = 20.0
RESULT_MARKER = "OPENVEF_SANDBOX_RESULT "
REQUEST_MARKER = "OPENVEF_SANDBOX_REQUEST "
REPLY_MARKER = "OPENVEF_SANDBOX_REPLY "


def broker_mode() -> bool:
    """True inside the D-002a runner container: artifact containers are started by the
    host broker (runner/run_f18_container.sh), never by this process."""
    return os.environ.get("OPENVEF_BROKER") == "1"


class SandboxUnavailable(RuntimeError):
    """Docker or the pinned image is not usable; nothing may be executed."""


@dataclass(frozen=True)
class SandboxResult:
    timed_out: bool
    returncode: Optional[int]
    result: Optional[dict]       # the harness's JSON result, if it produced one
    stderr_tail: str


def image_tag() -> str:
    """Content-addressed tag: first 16 hex of SHA-256 over the `sha256sum` listing of
    sandbox/Dockerfile and requirements.lock (same rule as runner/run_f18_container.sh)."""
    listing = "".join(f"{hashlib.sha256((REPO / rel).read_bytes()).hexdigest()}  {rel}\n"
                      for rel in ("sandbox/Dockerfile", "requirements.lock"))
    return f"openvef-sandbox:{hashlib.sha256(listing.encode()).hexdigest()[:16]}"


def toolchain_identity() -> dict:
    """D-003 toolchain versions as seen inside the image (run in the image)."""
    import importlib.metadata
    iv = subprocess.run(["iverilog", "-V"], capture_output=True, text=True)
    vvp = subprocess.run(["vvp", "-V"], capture_output=True, text=True)
    dpkg = subprocess.run(["dpkg-query", "-W", "-f=${Version}", "iverilog"], capture_output=True, text=True)
    return {"cocotb": importlib.metadata.version("cocotb"),
            "iverilog_version_line": iv.stdout.splitlines()[0] if iv.stdout else None,
            "vvp_version_line": (vvp.stdout or vvp.stderr).splitlines()[0] if (vvp.stdout or vvp.stderr) else None,
            "iverilog_deb_version": dpkg.stdout.strip() or None,
            "iverilog_sha256": _sha256_path("/usr/bin/iverilog"),
            "vvp_sha256": _sha256_path("/usr/bin/vvp")}


def _sha256_path(path: str) -> Optional[str]:
    try:
        return hashlib.sha256(Path(os.path.realpath(path)).read_bytes()).hexdigest()
    except OSError:
        return None


def ensure_image() -> dict:
    """Identity of the pinned image for the evidence record.

    In the D-002a runner container the image identity comes from the host broker, and the
    interpreter and toolchain are measured here, in the same image the artifacts use.
    On a development host the image is built if needed and probed."""
    harness_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(HARNESS_DIR.glob("*.py"))}
    if broker_mode():
        env = os.environ
        return {"mode": "D-002a runner container + host broker",
                "base_image_digest": env["OPENVEF_BASE_IMAGE_DIGEST"], "image_tag": env["OPENVEF_IMAGE_TAG"],
                "image_id": env["OPENVEF_IMAGE_ID"], "docker_server_version": env["OPENVEF_DOCKER_VERSION"],
                "host_kernel": env["OPENVEF_HOST_KERNEL"], "dockerfile_sha256": env["OPENVEF_DOCKERFILE_SHA256"],
                "requirements_lock_sha256": env["OPENVEF_LOCK_SHA256"], "broker_sha256": env["OPENVEF_BROKER_SHA256"],
                "runner_container_flags": base64.b64decode(env["OPENVEF_RUNNER_FLAGS_B64"]).decode().splitlines(),
                "artifact_container_flags": base64.b64decode(env["OPENVEF_ARTIFACT_FLAGS_B64"]).decode().splitlines(),
                "artifact_command": list(HARNESS_COMMAND), "harness_sha256": harness_sha,
                "toolchain": toolchain_identity()}
    tag = image_tag()
    probe = subprocess.run(["docker", "image", "inspect", tag, "--format", "{{.Id}}"], capture_output=True, text=True)
    if probe.returncode != 0:
        build = subprocess.run(["docker", "build", "-q", "-t", tag, "-f", str(DOCKERFILE), str(REPO)],
                               capture_output=True, text=True)
        if build.returncode != 0:
            raise SandboxUnavailable(f"image build failed: {build.stderr[-500:]}")
        probe = subprocess.run(["docker", "image", "inspect", tag, "--format", "{{.Id}}"], capture_output=True, text=True)
    image_id = probe.stdout.strip()
    version = subprocess.run(docker_argv(tag, ["python", "-I", "-c", (
        "import sys,hashlib,os;p=os.path.realpath(sys.executable);"
        "print(sys.version);print(hashlib.sha256(open(p,'rb').read()).hexdigest())")]),
        capture_output=True, text=True, timeout=60)
    if version.returncode != 0:
        raise SandboxUnavailable(f"image does not start: {version.stderr[-500:]}")
    py_version, py_sha = version.stdout.strip().split("\n")
    return {"mode": "development host launcher (not evidence, D-002a)",
            "base_image_digest": BASE_IMAGE_DIGEST, "image_tag": tag, "image_id": image_id,
            "container_python_version": py_version, "container_python_sha256": py_sha,
            "harness_sha256": harness_sha, "artifact_container_flags": artifact_flags("<name>"),
            "artifact_command": list(HARNESS_COMMAND)}


def artifact_flags(name: str) -> list[str]:
    """The artifact-container flags from runner/artifact-container.args (single source)."""
    lines = ARTIFACT_ARGS.read_text(encoding="utf-8").splitlines()
    return [ln.replace("{HARNESS_DIR}", str(HARNESS_DIR)).replace("{NAME}", name)
            for ln in lines if ln.strip() and not ln.startswith("#")]


def docker_argv(image: str, command: Sequence[str], name: Optional[str] = None) -> list[str]:
    """The exact `docker run` command line used by the development launcher."""
    return ["docker", "run", *artifact_flags(name or f"openvef-{uuid.uuid4().hex[:12]}"), image, *command]


def check_harness_permissions() -> None:
    """Refuse to run if the bind-mounted harness could be changed by another local user,
    or cannot be read by the container's uid (it is neither owner nor group)."""
    import stat
    for path in [HARNESS_DIR, *HARNESS_DIR.iterdir()]:
        mode = path.stat().st_mode
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise SandboxUnavailable(f"{path} is group- or other-writable")
        needed = (stat.S_IROTH | stat.S_IXOTH) if path.is_dir() else stat.S_IROTH
        if mode & needed != needed:
            raise SandboxUnavailable(f"{path} is not readable by the sandbox uid")


def _parse_stdout(stdout: str) -> Optional[dict]:
    result = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            result = json.loads(line[len(RESULT_MARKER):])
    return result


def run_in_sandbox(command: Sequence[str], stdin: bytes = b"", timeout_s: float = DEFAULT_TIMEOUT_S,
                   image: Optional[str] = None) -> SandboxResult:
    """Run `command` in a fresh container; kill and remove it at the wall-clock limit.

    Development launcher (host Docker). Inside the runner container use `run_harness`,
    which goes through the broker."""
    if broker_mode():
        raise SandboxUnavailable("arbitrary commands are not available through the broker")
    check_harness_permissions()
    image = image or image_tag()
    name = f"openvef-{uuid.uuid4().hex[:12]}"
    try:
        proc = subprocess.run(docker_argv(image, command, name=name), input=stdin, capture_output=True,
                              timeout=timeout_s)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return SandboxResult(True, None, None, "")
    except FileNotFoundError as exc:
        raise SandboxUnavailable("docker not found") from exc
    return SandboxResult(False, proc.returncode, _parse_stdout(proc.stdout.decode("utf-8", errors="replace")),
                         proc.stderr.decode("utf-8", errors="replace")[-2000:])


def _via_broker(stdin: bytes, timeout_s: float) -> SandboxResult:
    """One request/reply exchange with runner/run_f18_container.sh over stdout/stdin."""
    sys.__stdout__.write(f"{REQUEST_MARKER}{timeout_s:g} {base64.b64encode(stdin).decode('ascii')}\n")
    sys.__stdout__.flush()
    reply = sys.__stdin__.readline()
    if not reply.startswith(REPLY_MARKER):
        raise SandboxUnavailable(f"broker reply malformed: {reply[:80]!r}")
    fields = reply[len(REPLY_MARKER):].split()
    if fields == ["TIMEOUT"]:
        return SandboxResult(True, None, None, "")
    if len(fields) not in (2, 3, 4) or fields[0] != "DONE":
        raise SandboxUnavailable(f"broker reply malformed: {reply[:80]!r}")
    out = base64.b64decode(fields[2]) if len(fields) > 2 else b""
    err = base64.b64decode(fields[3]) if len(fields) > 3 else b""
    return SandboxResult(False, int(fields[1]), _parse_stdout(out.decode("utf-8", errors="replace")),
                         err.decode("utf-8", errors="replace"))


def run_harness(request: dict[str, Any], timeout_s: float = DEFAULT_TIMEOUT_S) -> SandboxResult:
    """Run sandbox/harness.py on one JSON request in a fresh artifact container."""
    stdin = json.dumps(request).encode("utf-8")
    if broker_mode():
        return _via_broker(stdin, timeout_s)
    return run_in_sandbox(list(HARNESS_COMMAND), stdin, timeout_s)
