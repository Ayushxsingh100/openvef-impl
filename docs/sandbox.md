# Artifact-execution sandbox

Owner decision **D-002** (Krishika, 23 Nov 2026; Ayush's confirmation pending): F18
artifact execution uses Docker image `python:3.11.18-slim` pinned by digest, run with
`--network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges`, a non-root
user, tmpfs for scratch, pids/memory/CPU limits and a wall-clock timeout. The pinned
`requirements.lock` is installed with `--require-hashes` inside the image.

Owner decision **D-002a** (Krishika, 23 Nov 2026; Ayush's confirmation pending): the
pinned interpreter for all F18 evidence is the CPython in that container. The whole
runner, static stages included, runs in the image; host Python is for development only.

Owner decision **D-003** (Krishika, 23 Nov 2026; Ayush's confirmation pending): toolchain
per the Charter ("Cocotb; Icarus Verilog initially"), pinned at the latest stable versions
installable in the image: cocotb from `requirements.lock` with hashes, Icarus Verilog from
the image's package manager with its exact version recorded.

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
| Pinned interpreter (D-002a) | `3.11.18 (main, Nov  5 2026, 07:57:53) [GCC 14.2.0]`, `/usr/local/bin/python3.11`, SHA-256 `92d7e40ec50be176cb1b790c7568b7e08cd862137b5aa69f1413ba1967886b79` |
| Icarus Verilog (D-003) | Debian package `iverilog` `12.0-2+b1` from snapshot.debian.org (`iverilog -V`: "Icarus Verilog version 12.0 (stable)"); `.deb` SHA-256 `febe027d2d3f5a7e570844d55758339ab5490acc09f404f214a8719d89d07056`, checked with `sha256sum -c` before `dpkg -i`; `/usr/bin/iverilog` SHA-256 `99633b21…8462`, `/usr/bin/vvp` SHA-256 `dc287630…c1df` |
| cocotb (D-003) | `cocotb==2.1.0` (cp311 manylinux wheel) and its dependencies `find-libpython==0.5.1`, `iniconfig==2.3.1`, `packaging==26.3`, `pluggy==1.7.0`, `pygments==2.21.0`, `pytest==9.2.0`, all with hashes in `requirements.lock` (pip-tools 7.7.0 `pip-compile --generate-hashes`, run in the pinned base image). Earlier pins are unchanged. |
| Build | [sandbox/Dockerfile](../sandbox/Dockerfile): base by digest; iverilog `.deb` from snapshot.debian.org by URL, version and SHA-256; `pip install --require-hashes --no-deps -r requirements.lock`; user `sandbox` uid/gid 10001 |
| Build context | `.dockerignore` admits only `requirements.lock` |
| Local tag | `openvef-sandbox:<first 16 hex of SHA-256 of the sha256sum listing of sandbox/Dockerfile and requirements.lock>`, rebuilt automatically when either changes |

"Latest stable" was checked on 23 Nov 2026 in the pinned base image: `pip index versions
cocotb` lists 2.1.0 as newest; `apt-cache policy iverilog` lists only 12.0-2+b1 (Debian
13 "trixie"), and Icarus 12.0 is the upstream stable release.

Source of the `.deb`: snapshot.debian.org,
`https://snapshot.debian.org/archive/debian/20240313T032420Z/pool/main/i/iverilog/iverilog_12.0-2%2Bb1_amd64.deb`.
`20240313T032420Z` is the archive timestamp at which this file (SHA-1
`dfb2b1db5303c41fcb565ab69480165875ad39d3`, 2,046,080 bytes) was first seen, per the
snapshot `mr/binary/iverilog/12.0-2+b1/binfiles` API. The same SHA-256 check runs before
`dpkg -i`. The build therefore no longer depends on the live Debian archive. After the
switch, `/usr/bin/iverilog` and `/usr/bin/vvp` have the same SHA-256 as before, and a
containerized smoke run gave results identical to run-20261123T195936Z. The image ID
changes, because the Dockerfile changed, and each run records it.

## Where things run (D-002a)

| Role | Where | Interpreter |
|---|---|---|
| F18 runner: index/hash checks, all static stages, ledger, serializer, comparisons, evidence writing | runner container from the pinned image ([runner/runner-container.args](../runner/runner-container.args)) | pinned |
| Each artifact execution (factory, checker invocation, later simulation) | a fresh artifact container from the same image ([runner/artifact-container.args](../runner/artifact-container.args)) | pinned |
| Host | [runner/run_f18_container.sh](../runner/run_f18_container.sh): bash only; builds the image, starts the runner, launches artifact containers on request | none |

The runner container has no Docker access. When it needs an artifact execution it writes
`OPENVEF_SANDBOX_REQUEST <timeout> <base64 JSON>` on stdout; the broker starts one
artifact container running the fixed command `python -I /opt/openvef/harness.py` with
that JSON on stdin and the flags from `artifact-container.args`, and replies with the
exit code and base64 output, or `TIMEOUT` (after `docker kill` and `docker rm -f`). The
runner chooses neither the command, the image nor the flags. The broker does not read
results.

The runner container is isolated like an artifact container (`--network=none`,
`--read-only`, `--cap-drop=ALL`, `no-new-privileges`, tmpfs `/tmp`) except: it runs as the
invoking host uid so it can write its one evidence directory, which is the only writable
mount; the baseline and the `src/`, `runner/`, `sandbox/` trees are mounted read-only; it
has larger limits (1 GiB, 128 pids, 2 CPUs).

Every run's `summary.json` records `interpreter_status` (`PINNED` only when the runner is
in the container and `sys.version` and the interpreter SHA-256 equal the pinned values),
the interpreter, all distributions, and under `sandbox`: base digest, image tag and ID,
Dockerfile and lock SHA-256, broker SHA-256, both flag lists, the artifact command,
harness SHA-256s, Docker server version, host kernel, and the toolchain (cocotb version,
`iverilog -V`/`vvp -V` lines, `.deb` version, binary SHA-256s). A run started with
`python runner/run_f18.py` on the host records `NOT_PINNED` and is not evidence.

`OPENVEF_EVIDENCE_ROOT` redirects the run directory for smoke tests outside `evidence/`.

## What is isolated, and how

Artifact-container flags are defined only in
[runner/artifact-container.args](../runner/artifact-container.args), read by both the
broker and the development launcher (`docker_argv` in
[src/openvef/sandbox.py](../src/openvef/sandbox.py)). Each execution starts a new
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
| Simulator | Icarus Verilog and cocotb are installed (D-003) for the harness. Artifact code cannot reach them: `cocotb` is not on the import allow-list (static and runtime), and subprocess/`os` are not importable | `test_artifact_cannot_import_cocotb` |
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

## Simulation stage (Protocol §3.4 L166 (7)-(8); D-003)

Task `simulate` ([sandbox/sim.py](../sandbox/sim.py), [sandbox/sim_cocotb.py](../sandbox/sim_cocotb.py))
runs one driver on one target (`rtl` or `null`) in its own artifact container:
`iverilog -g2012` compiles the design sources, `vvp` runs them with cocotb's Icarus VPI
library, and the cocotb test module runs the cycle loop. The artifact is imported with
the same restricted import as the factory task, its output is discarded, and `step`
receives only a dict of strings, never a simulator handle. `sim.py` watches a heartbeat
file and kills `vvp` when a `step` call exceeds the per-step watchdog (`WATCHDOG_TIMEOUT|phase=driver_step`).
The runner side is [src/openvef/simulation.py](../src/openvef/simulation.py): RTL run, then
null run, then the L166 (8) paired comparison.

Request fields (design materials; **all supplied by the caller, no defaults**):
`toplevel`, `verilog_sources`, `clock_port`, `input_ports` (name → width), `output_ports`,
`reset_sequence`, `cycle_cap`, `safe_idle`, `legal_input_predicate`, plus `seed`,
`step_timeout_s`, `budget_s`. The only executable predicate is the literal
`ALL_INPUTS_LEGAL` (used by the toy tests). Any other value makes the result not
determined (A-027, A-038), never a pass.

**Build defaults for choices the pack leaves TO FREEZE** (Protocol L229 "Cycle cap,
safe-idle vectors and timeout formula are **TO FREEZE**"; L542 "Freeze driver API,
scheduler, alignment, same-row tie, cap, safe-idle and watchdog"). These are not
readings of the text. Each result records them under `scheduler`, and the owners must
freeze them:
- timescale 1ns/1ps;
- clock period 10 ns, starting low (first active edge at half a period);
- inputs driven at the falling edge before the next active edge (the pack says only "the
  designated drive phase before edge `n+1`", Protocol L219);
- `reset_sequence[i]` is driven before active edge *i*, and the edge after the last
  vector is the reset-release edge.

Correction (23 Nov 2026): an earlier version of this list also called the sampling point a
build default. It is specified by the pack: "`outputs_after_edge_n`: top-level outputs
sampled in Cocotb `ReadOnly` after edge `n` settles" (Protocol L218), and the harness
follows it.

**Known gap against Protocol §5.2 (L217–L223), not yet fixed:** the raw rows that
`sim_cocotb.py` records have `cycle`, `outputs_after_edge`, `next_inputs` and
`driver_completed`. §5.2 also requires:
- `inputs_consumed_at_edge_n`;
- the reset state;
- run status;
- an FST/VCD audit file "where supported".

It also names the three row fields `inputs_consumed_at_edge_n`, `outputs_after_edge_n`
and `next_inputs_scheduled_for_edge_n_plus_1`. No fixture result depends on this today.
The rows must be brought in line before the trace schema (owner item 11 in
[fifo-owner-checklist.md](fifo-owner-checklist.md)) is used.

**What blocks the 10 fixtures** (P01, P14, P17, P21, P42, M07, M31, M32, M33, M57): the
FIFO RTL and null netlist, the port manifest with widths, the reset sequence and
legal-input rules (owner-written FIFO specification), the cycle cap, safe-idle vector
and watchdog formula (TO FREEZE), the observation mask (owner-written), and the checker
trace schema and metadata (TO FREEZE, L543). None of these are in the pack. Writing them
is outside the Scope section and outside the delegation.

Tests: [tests/test_simulation.py](../tests/test_simulation.py) (16). They use
**test-only** toy designs in `tests/sim_designs/`, which are not a FIFO and not derived
from any owner material.

## Running the tests

```
.venv/bin/python -I tests/test_sandbox.py -v
.venv/bin/python -I tests/test_simulation.py -v
.venv/bin/python -I tests/test_broker.py -v
```

Docker must be available; without it the tests are reported as skipped, never as
passed. They run real containers with exactly the flags used for artifacts.

## Not covered here

- The simulator-backed stages need FIFO design materials (RTL, null netlist, port
  manifest, reset/legal-input rules, cycle cap, safe-idle vector, trace schema, mask)
  that are owner-written or still TO FREEZE; see docs/traceability.md.
- The resource limits and timeout values are this build's defaults, not frozen pack
  values.
- Development host: Docker 29.9.2 (not rootless), default AppArmor profile, built-in
  seccomp profile, cgroup v2. A different Docker setup needs the tests re-run before its
  results count.
