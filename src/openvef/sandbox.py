"""Host-side launcher for the artifact-execution sandbox (owner decision D-002).

Every artifact execution goes through `run_in_sandbox`, which starts one short-lived
container from the pinned image with:

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

import hashlib
import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO / "sandbox" / "Dockerfile"
HARNESS_DIR = REPO / "sandbox"
# D-002: python:3.11.18-slim pinned by digest (resolved 23 Nov 2026, linux/amd64).
BASE_IMAGE_DIGEST = "python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535"
UID_GID = "10001:10001"

# Resource limits (values are this build's defaults; docs/sandbox.md).
LIMITS = {"pids": 64, "memory": "256m", "cpus": "1", "tmpfs_size": "16m", "nofile": 64}
DEFAULT_TIMEOUT_S = 20.0
RESULT_MARKER = "OPENVEF_SANDBOX_RESULT "


class SandboxUnavailable(RuntimeError):
    """Docker or the pinned image is not usable; nothing may be executed."""


@dataclass(frozen=True)
class SandboxResult:
    timed_out: bool
    returncode: Optional[int]
    result: Optional[dict]       # the harness's JSON result, if it produced one
    stderr_tail: str


def image_tag() -> str:
    """Content-addressed tag: changes whenever the Dockerfile or the lock file changes."""
    h = hashlib.sha256()
    for path in (DOCKERFILE, REPO / "requirements.lock"):
        h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return f"openvef-sandbox:{h.hexdigest()[:16]}"


def ensure_image() -> dict:
    """Build the image if needed; return its identity for the evidence record."""
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
    return {"base_image_digest": BASE_IMAGE_DIGEST, "image_tag": tag, "image_id": image_id,
            "container_python_version": py_version, "container_python_sha256": py_sha,
            "harness_sha256": (hashlib.sha256((HARNESS_DIR / "harness.py").read_bytes()).hexdigest()
                               if (HARNESS_DIR / "harness.py").exists() else None),
            "docker_flags": docker_argv("<image>", ["<command>"], name="<name>")}


def docker_argv(image: str, command: Sequence[str], name: Optional[str] = None) -> list[str]:
    """The exact `docker run` command line; the only place the isolation flags are set."""
    argv = ["docker", "run", "--rm", "-i",
            "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            f"--user={UID_GID}",
            f"--tmpfs=/tmp:rw,noexec,nosuid,nodev,size={LIMITS['tmpfs_size']},mode=1777",
            f"--pids-limit={LIMITS['pids']}", f"--memory={LIMITS['memory']}", f"--memory-swap={LIMITS['memory']}",
            f"--cpus={LIMITS['cpus']}", f"--ulimit=nofile={LIMITS['nofile']}:{LIMITS['nofile']}",
            "--ipc=none", "--hostname=sandbox",
            "--env=PYTHONHASHSEED=0", "--env=PYTHONDONTWRITEBYTECODE=1", "--env=PYTHONUNBUFFERED=1",
            f"--volume={HARNESS_DIR}:/opt/openvef:ro",
            "--workdir=/tmp"]
    if name:
        argv.append(f"--name={name}")
    return argv + [image, *command]


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


def run_in_sandbox(command: Sequence[str], stdin: bytes = b"", timeout_s: float = DEFAULT_TIMEOUT_S,
                   image: Optional[str] = None) -> SandboxResult:
    """Run `command` in a fresh container; kill and remove it at the wall-clock limit."""
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
    stdout = proc.stdout.decode("utf-8", errors="replace")
    result = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            result = json.loads(line[len(RESULT_MARKER):])
    return SandboxResult(False, proc.returncode, result, proc.stderr.decode("utf-8", errors="replace")[-2000:])


def run_harness(request: dict[str, Any], timeout_s: float = DEFAULT_TIMEOUT_S) -> SandboxResult:
    """Run sandbox/harness.py on one JSON request."""
    return run_in_sandbox(["python", "-I", "/opt/openvef/harness.py"], json.dumps(request).encode("utf-8"), timeout_s)
