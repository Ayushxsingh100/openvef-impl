# Artifact-execution sandbox

Owner decision **D-002** (Krishika, 23 Nov 2026; Ayush's confirmation pending): F18
artifact execution uses Docker image `python:3.11.18-slim` pinned by digest, run with
`--network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges`, a non-root
user, tmpfs for scratch, pids/memory/CPU limits and a wall-clock timeout. The pinned
`requirements.lock` is installed with `--require-hashes` inside the image. Cocotb and the
simulator are not pinned, so any fixture that needs them stays NOT_IMPLEMENTED.

Pack requirements this implements: File 30 §3 L39 ("Runtime signature checks and the
`create_driver` return-type check run after import in the restricted execution container.
The container sandbox is the security boundary and must be pinned and tested before
F16.") and File 30 §6 ("The runtime sandbox denies network, filesystem access beyond the
designated temporary output directory, environment variables, wall-clock reads,
subprocess and simulator access. It must allow the interpreter to initialize the
standard-library `random` module … F18 must test `import random` plus
construction/use of `random.Random(seed)` inside the sandbox before F16.").

**Status:** development configuration. The pack also requires the sandbox to be "pinned
and tested before F16". The tests below are the F18-side part of that. Whether this
configuration is adequate as the security boundary for F16 is for the owners to review.

## Image

| Item | Value |
|---|---|
| Base image | `python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535` (`python:3.11.18-slim`, linux/amd64, resolved with `docker pull` on 23 Nov 2026) |
| Container interpreter | `3.11.18 (main, Nov  5 2026, 07:57:53) [GCC 14.2.0]`, SHA-256 `92d7e40e…6b79` |
| Build | [sandbox/Dockerfile](../sandbox/Dockerfile): base by digest; `pip install --require-hashes --no-deps -r requirements.lock`; user `sandbox` uid/gid 10001 |
| Build context | `.dockerignore` admits only `requirements.lock` |
| Local tag | `openvef-sandbox:<first 16 hex of SHA-256(Dockerfile, requirements.lock)>`, rebuilt automatically when either changes |

The container interpreter is CPython 3.11.18, but it is a different binary from the host
interpreter used for the static stages (host: GCC 13.3.0, SHA-256 `518f54d1…5356`).
Every evidence run records both: the host interpreter as before, and under
`sandbox` the base digest, image ID, container `sys.version`, container interpreter
SHA-256, harness SHA-256 and the exact `docker run` flags.

## What is isolated, and how

All flags are built in one function, `docker_argv` in
[src/openvef/sandbox.py](../src/openvef/sandbox.py). Each execution starts a new
container and removes it afterwards (`--rm`).

| Concern | Mechanism | Test (`tests/test_sandbox.py`) |
|---|---|---|
| Network | `--network=none`: only the loopback interface exists; no route, no DNS | `test_no_network`: TCP connect fails, `getaddrinfo` fails, interfaces are `['lo']` |
| Filesystem | `--read-only` root; harness directory mounted `:ro`; only `/tmp` writable: tmpfs, 16 MiB, `noexec,nosuid,nodev` | `test_read_only_root_and_writable_tmp`: writes to `/usr/local/lib`, `/opt/openvef`, `/`, `/home` fail; `/tmp` writable; a file in `/tmp` cannot be executed |
| Identity and privileges | `--user=10001:10001` (also the image `USER`); `--cap-drop=ALL`; `--security-opt=no-new-privileges` | `test_non_root_no_capabilities_no_new_privileges`: uid/euid/gid 10001; `CapEff` and `CapPrm` are zero; `NoNewPrivs: 1` |
| Environment variables | No host variables are passed; only `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` and the image's own `PATH`/`HOME`/`HOSTNAME`/`LANG`/`GPG_KEY`/`PYTHON_*` | `test_environment_is_minimal` (it caught `PIP_*` variables leaking from the Dockerfile; now scoped to the build step) |
| Processes | `--pids-limit=64`; `--ipc=none` | `test_pids_limit`: fork loop stops at the limit |
| Memory, CPU, files | `--memory=256m --memory-swap=256m` (no swap); `--cpus=1`; `--ulimit nofile=64:64` | — (configuration only) |
| Wall-clock time | Host timeout (default 20 s per container). On expiry the launcher runs `docker kill` and `docker rm -f` by the container's unique name | `test_timeout_kills_and_removes_container`: a busy loop under a 4 s limit is reported as timed out, and no `openvef-*` container remains |
| Simulator | No simulator is installed in the image | — |
| Determinism | `PYTHONHASHSEED=0`, so `str`/`bytes` hashing (set iteration order) is the same in every run (A-036) | — |
| `random` | Standard-library `random` initializes normally; artifacts may only use a local `random.Random(seed)` (enforced statically at IMPORT_POLICY) | `test_seeded_local_random_works`: same sequence as the host for seed 7 |

What the container does **not** do by itself: it does not stop artifact code from
calling allowed standard-library functions. The import allow-list, prohibited names and
module-global `random` are enforced statically at IMPORT_POLICY. At runtime, the
harness enforces the same import allow-list for imports made by artifact code (File 30
§6 "Enforce the same import allow-list statically and at runtime"; see
`sandbox/harness.py`). The container flags are what contain anything the static and
runtime checks miss.

## Harness and integrity guard

[sandbox/harness.py](../sandbox/harness.py) runs inside each container (standard library
only). Each request runs one task:
- `factory`: restricted import of `driver.py`, `create_driver(0)`, return type, runtime
  signatures;
- `checker`: one null invocation of `check_trace`.

It writes one framed result line to the original stdout. Artifact stdout/stderr is
captured and discarded, so an artifact cannot forge a result
(`test_artifact_output_cannot_forge_result`). The harness directory is bind-mounted
read-only. Before every run the launcher refuses to start if any file in it is group- or
other-writable, or unreadable by the sandbox uid (`check_harness_permissions`). That guard
was added after new files in this checkout were found created with mode 646. Directory
ACLs (the `+` in `ls -l`) were not inspected: `getfacl` is not installed here.

## Running the tests

```
.venv/bin/python -I tests/test_sandbox.py -v
```

Docker must be available; without it the tests are reported as skipped, never as
passed. They run real containers with exactly the flags used for artifacts.

## Not covered here

- Cocotb and the simulator are not pinned (D-002), so nothing that needs a simulation
  (driver steps against RTL/null, null traces for the checker) runs in this sandbox yet.
- The resource limits and timeout values are this build's defaults, not frozen pack
  values.
- Development host: Docker 29.9.2 (not rootless), default AppArmor profile, built-in
  seccomp profile, cgroup v2. A different Docker setup needs the tests re-run before its
  results count.
