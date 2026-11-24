# Audit readiness — OpenVEF v1.3.6 implementation

**For:** the owners (Krishika, Ayush Kumar Singh) and the independent implementation
auditor. **Prepared by:** Claude (Claude Opus 5.5, via Claude Code), 24 Nov 2026.
It is a status document: it claims no gate as passed.

## 1. Where the project stands in the release gates

> [02 L555] "(5) Independently re-audit the implementation, parser/assembler, Python 3.11 behavior and all mandatory fixture results."

- **Step (4) scope only:** implementation is open only within the limited hand-built FIFO
  feasibility scope of L555 step (4), as the owners' Sign-off Pack opened it (CLAUDE.md).
  The v1.3.6 baseline files still record their own pre-implementation status (Files 16,
  21, 23 and 32); they are read-only and are not updated by this work.
- **Not done:** step (5), the independent implementation re-audit. It is **not
  started**, and an auditor is not yet named.
- **Prohibited:** no LLM or provider call has been made by any code, test or script
  (CLAUDE.md hard rule 5). The LLM-call gate, step (6), is closed.

## 2. Current counts

Latest evidence run: **`evidence/run-20261124T144337Z`**.
- Run class `development`; commit `3f3e355`, clean tree.
- Pinned image per D-002a: CPython 3.11.18, interpreter SHA-256 `92d7e40e…`. The image ID
  and toolchain identity are recorded in its `summary.json`.
- Outcomes are identical to the previous run, `run-20261124T112030Z` (commit `12abd1f`),
  fixture by fixture. Only the L334 wall-clock medians in the provisional records differ.

| Status | Count | Fixtures |
|---|---|---|
| PASS | 139 | 129 not provisional; 10 provisional (below) |
| FAIL | 0 | — |
| NOT_IMPLEMENTED | 5 | M27 (A-038, revisited 24 Nov 2026); M48, M50, M54, M58 (A-033: no supporting Protocol sentence) |
| ERROR | 0 | — |
| **Total** | **144** | the full mandatory set (File 21: 59 P + 13 R + 72 M) |

**Provisional PASS (10):** P01, P14, P17, P21, P42, M07, M31, M32, M33, M57. They reach
L166 (7)–(11) on the DRAFT FIFO materials (D-005). They **do not count toward F18**
until all of these hold:
- the owners freeze the materials;
- an independent human signs the mask;
- the owners review the readings they depend on (A-040, A-041, A-043, A-044; A-042
  needs Ayush's confirmation).

See [OWNER-FREEZE-PACKAGE.md](OWNER-FREEZE-PACKAGE.md).

Also not yet counting toward F18: any PASS that depends on a reading still awaiting owner
review. [traceability.md](traceability.md) marks each one.

**F18 is therefore not passed.**
- File 21: "F18 must fail if any fixture is missing, not materialized, hash-mismatched,
  ambiguous, assigned an outcome not in the normative contract, or produces a different
  stage, error class, diagnostic byte string or terminal disposition".
- Five fixtures are not run to an outcome, ten are provisional, and many readings are
  unreviewed.

## 3. Evidence bundle for the independent implementation auditor

**Source:** the evidence-bundle list in the Owner Decision Record §5.3, an external
document not in this repository. The list was supplied by Krishika on 24 Nov 2026.

Status is checked against the latest evidence run, `evidence/run-20261124T144337Z`. **9 of 9 met.**
- **Met:** the run records it as stated.
- **Partly met:** some of it is recorded; the gap is named. (None at present; items 4
  and 6 were partly met up to `run-20261124T112030Z`.)

| # | §5.3 item | Where it is in each run | Status |
|---|---|---|---|
| 1 | Fixture-index SHA-256 verified at run time | `runner/run_f18.py` `load_index` aborts the run on a mismatch with the pinned `INDEX_SHA256`; `summary.json` `fixture_index_sha256` (`f37808c7…de54`) | **Met** |
| 2 | Interpreter version and binary/image hash | `summary.json` `python_version` (3.11.18), `python_executable_sha256` (`92d7e40e…6b79`), `interpreter_status` PINNED, `sandbox.image_id`, `base_image_digest`, `dockerfile_sha256`, `requirements_lock_sha256`, `toolchain` | **Met** |
| 3 | Parser/assembler/runner source commit and per-file SHA-256 | `summary.json` `git_commit` (with `+UNCOMMITTED_CHANGES` if the tree was dirty) and `source_sha256` for every file under `src/`, `runner/`, `sandbox/` and `design/`; `sandbox.harness_sha256`; `design_materials.file_sha256` (includes the spec) | **Met** |
| 4 | Exact run commands and environment variables | `summary.json` `command` (the in-container command); `sandbox.runner_container_flags` / `artifact_container_flags` (every `--env` passed to the containers); `sandbox.host_invocation`: host `argv` (`runner/run_f18_container.sh development`), `cwd`, `docker_client`, and the host `environment` under the recorded allow-list `environment_policy` (every `OPENVEF_*` variable plus named docker CLI and locale variables, if set) | **Met.** The full host environment is deliberately not recorded: it can hold credentials. The allow-list names every variable that can change the broker script or the docker CLI |
| 5 | Per-fixture record: ID, descriptor SHA-256, actual disposition/stage/error class/diagnostic, expected, match | `results.jsonl`: `fixture_id`, `descriptor_sha256`, `actual` (four fields), `expected`, `status` (PASS = match, FAIL = mismatch), `note`; provisional block where applicable | **Met** |
| 6 | Raw run logs with timestamps | `run.log`: run metadata (with `run_started_utc`), then one line per fixture, each prefixed with an ISO 8601 UTC timestamp in milliseconds (written and flushed as the fixture finishes); `summary.json` `run_finished_utc` | **Met** |
| 7 | Results files and SHA-256 | `results.jsonl`, with its SHA-256 in `summary.json` `results_sha256`; `summary.json` itself is not hashed inside the run | **Met** for results; the summary's own hash is computable but not recorded |
| 8 | Every failed/errored/skipped fixture, with reason | `results.jsonl` `note` for every non-PASS; this run has 0 FAIL, 0 ERROR and 5 NOT_IMPLEMENTED (M27, M48, M50, M54, M58), each with its blocking reason | **Met** |
| 9 | Isolation arrangement for LLM-generated code | artifact containers: no network, read-only root, all capabilities dropped, non-root, noexec tmpfs, limits, wall-clock kill; flags in each run's `artifact_container_flags`; [sandbox.md](sandbox.md); `tests/test_sandbox.py`, `tests/test_broker.py` (D-002, D-002a) | **Met** as built. Whether it is adequate as the security boundary for F16 is for the owners to decide (sandbox.md) |

**Also available to the auditor:**
- [traceability.md](traceability.md), [ambiguities.md](ambiguities.md),
  [pack-defects.md](pack-defects.md), [assistance-log.md](assistance-log.md);
- the unit tests in `tests/`, 16 files, run with `.venv/bin/python -I tests/<file>`.

**File 50 Python 3.11 Unicode tokenizer check (L555 (4)): recorded.** Run
`evidence/probe-file50-20261124T112645Z/` on the pinned image (CPython 3.11.18,
interpreter SHA-256 `92d7e40e…6b79`, image `sha256:565e5547…`). Results:
- the File 50 code block ran byte-for-byte;
- `℘ = 1` gives `ERRORTOKEN '℘' (1, 0)`;
- `a℘ = 1` gives `NAME 'a' (1, 0)`, then `ERRORTOKEN '℘' (1, 1)`;
- `ast.parse` accepts both;
- the scanner rejects both as `NON_ASCII_IDENTIFIER|…|column=1`, at the start of the
  complete identifier lexeme;
- Unicode in a STRING and in a COMMENT is not rejected.

This **matches the audit-time CPython 3.11.18 results** in File 54 (M55: "ERRORTOKEN `℘`
at (1,0)"; M56: "NAME `a` + ERRORTOKEN `℘`"), and it differs from the 3.13.5 exploratory
result in File 50, which emitted NAME. No difference from the audit-time results was
found. The audit used a different 3.11.18 binary (`/usr/bin/python3.11`, File 54 L35);
this run is on the pinned one.

## 4. Open items and owners

**Owner signatures and reviews (Krishika and Ayush together, unless noted)**

| Item | Owner | Reference |
|---|---|---|
| Sign the freeze package: spec v0.2, items 7–12, RTL, export script, D-004…D-006, A-040…A-044 (and A-038), overlap disclosure | both owners | [OWNER-FREEZE-PACKAGE.md](OWNER-FREEZE-PACKAGE.md) |
| Ayush's confirmation of every owner decision recorded from Krishika alone: A-001–A-006, A-013, A-014, A-015 case 2, D-002, D-002a, D-003, D-004, D-004a, D-005, D-006 | Ayush | [ambiguities.md](ambiguities.md) |
| D-001 (Draft 2020-12 validator pin): one owner confirmation outstanding | owners | ambiguities.md D-001 |
| Review of the readings decided by Claude: A-007–A-012, A-013 tie case, A-015–A-041, A-043, A-044 (A-042 accepted by Krishika) | both owners (the delegation came from Krishika alone) | ambiguities.md; CLAUDE.md "Standing delegation" |
| Pack defects PD-01…PD-24 (settle, or accept the interim readings) | owners | [pack-defects.md](pack-defects.md) |
| M27: a corrected fixture in a future pack release (port manifest with widths, an executable predicate consistent with the frozen FIFO rules) | owners | PD-25; A-038 (revisited) |
| M48, M50, M54, M58: the change-class fields with no supporting Protocol sentence | owners | A-033, PD-02 |
| TechRxiv preprint: retrieve it, or record its access status; make the Charter and File 10 agree | owners | PD-24 |

**People still to be found**

| Item | Owner | Reference |
|---|---|---|
| Independent human mask reviewer: signs the mask and the File 24 table | owners to appoint; must not have authored the templates or the mask | L271; File 21 "Independent reviewer"; package §G |
| Independent implementation auditor | owners to appoint | L555 (5) |

**Human-written work (reserved by CLAUDE.md; Claude does not write it)**

| Item | Owner | Reference |
|---|---|---|
| Directed legal-input suite and reference driver (checklist item 14) | owners | L245, L415 |
| Hand-built FIFO control mutants (item 15), sufficient for F1–F15, including F5 and F10 | owners | Charter L74; L506, L514, L519 |
| F6/F17 control checkers and drivers (item 16) | owners | L489, L515 |
| Frozen L544 export script, mutation modes, mutant population, bounded-equivalence assumptions | owners | L544 |

**Work Claude can do on request (under D-005 or the build scope)**

| Item | Owner | Reference |
|---|---|---|
| Draft the remaining payload blocks (`[Execution envelope]`, `[Driver API]`, `[Trace schema]`, `[Checker contract]`) and the File 38 manifest (checklist items 2, 17), then run the assembler and clause-ID checks on them | Claude drafts; owners approve | D-005; File 31 L29–L30 |
| F1–F15 feasibility harness runs, once the control mutants exist | Claude builds the harness; owners supply the mutants | L555 (4) |
| After freeze and mask signature: a new pinned evidence run without provisional results | Claude | package "After signing" |
