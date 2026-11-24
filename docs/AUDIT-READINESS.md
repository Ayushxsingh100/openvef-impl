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

Latest evidence run: **`evidence/run-20261124T195043Z`**.
- Run class `development`; commit `875ca7e`, clean tree; after DEV-001
  ([DEVIATIONS.md](DEVIATIONS.md)) and D-009 ([READINGS-REVIEW.md](READINGS-REVIEW.md)).
  The run re-verified all 20 frozen items, the DEV-001 mask files and the 40 D-009 items
  against their recorded hashes; none changed.
- Pinned image per D-002a: CPython 3.11.18, interpreter SHA-256 `92d7e40e…`. The image ID
  and toolchain identity are recorded in its `summary.json`.
- Every fixture's outcome is identical to the previous run, `run-20261124T194216Z`
  (commit `578cf11`). Only the mask hashes and the DEV-001 label changed; that run's label is superseded.

| Status | Count | Fixtures |
|---|---|---|
| PASS | 139 | 0 provisional; 129 unlabelled, 10 "cleared under DEV-001 (non-independent review saved)" (below) |
| FAIL | 0 | — |
| NOT_IMPLEMENTED | 5 | M27 (A-038, revisited 24 Nov 2026); M48, M50, M54, M58 (A-033: no supporting Protocol sentence) |
| ERROR | 0 | — |
| **Total** | **144** | the full mandatory set (File 21: 59 P + 13 R + 72 M) |

**Passes cleared under DEV-001 (10):** P01, P14, P17, P21, P42, M07, M31, M32, M33, M57.
They reach L166 (7)–(11) on the FIFO materials.
- **Settled by the owner freeze (`a955245`, D-008):** the specification, frozen values,
  RTL, null-export script, `spec_version_sha256`, and readings A-040–A-044.
- **Mask and File 24 table:** accepted by the owner without an independent review. A
  non-independent Claude (claude.ai) review, done after DEV-001 was recorded, is saved
  ([review](reviews/claude-mask-review-2026-11-25.md)); the mask is re-frozen under D-010. They
  carry the label "cleared under DEV-001 (non-independent review saved)". **L271 and File 21
  L32 remain unmet**; the auditor decides whether these 10 can count toward F18.

**Readings:** every other Claude-decided reading is approved by Krishika as decided, without
itemised owner review (D-009). Claude decided them, and Claude recommended the approval. The
auditor should weigh them with that in mind.

**F18 is therefore not passed.**
- File 21: "F18 must fail if any fixture is missing, not materialized, hash-mismatched,
  ambiguous, assigned an outcome not in the normative contract, or produces a different
  stage, error class, diagnostic byte string or terminal disposition".
- Five fixtures are not run to an outcome, L271 is unmet (DEV-001), and the independent
  implementation re-audit (L555 (5)) has not started.

## 2a. Feasibility controls F1–F15, F17 (Protocol §17)

Plan: [F1-F17-plan.md](F1-F17-plan.md). Owner-written control artifacts are listed in
[design/fifo/controls/README.md](../design/fifo/controls/README.md) (D-007).

Latest control run: **`evidence/controls-20261124T195210Z`**, pinned image, commit
`875ca7e`. It carries the same identity records as an F18 run.

| Status | Controls |
|---|---|
| PASS, not provisional | F14 (A-052) and F15 (case table): each rests on a D-009 approval "as decided, without itemised owner review" |
| BLOCKED_OWNER_ARTIFACTS | F1–F13, F17: each record lists the owner files it is waiting for |

**What is built:** the harness components H1–H10.
- They are unit-tested on synthetic inputs and TEST-ONLY toy designs.
- The per-control procedures for F1–F13 and F17 are composed and run as the owner files
  arrive (plan step 8).
- **No control besides F14 and F15 has run.**

## 3. Evidence bundle for the independent implementation auditor

**Source:** the evidence-bundle list in the Owner Decision Record §5.3, an external
document not in this repository. The list was supplied by Krishika on 24 Nov 2026.

Status is checked against the latest evidence run, `evidence/run-20261124T195043Z`. **9 of 9 met.**
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
| **Ayush ratification pending** (the single entry under D-008): Ayush Kumar Singh's agreement to every decision and approval Krishika signed alone, including the freeze package (`a955245`) and every decision recorded as awaiting his confirmation (D-001–D-010, DEV-001, A-001–A-006, A-013, A-014, A-015 case 2, A-042). Under D-008 these take effect now | Ayush | [ambiguities.md](ambiguities.md) D-008; [FREEZE-RECORD-2026-11-24.md](FREEZE-RECORD-2026-11-24.md) |
| Sign the overlap disclosure note's own owner-signature table (F1 in the package is approved) | owners | [fifo-benchmark-overlap-disclosure-DRAFT.md](fifo-benchmark-overlap-disclosure-DRAFT.md) |
| Itemised review of the readings approved under D-009 (A-007–A-012, A-013 tie, A-015–A-037, A-039, A-045–A-052, F15 case table): approved as decided, **not** reviewed item by item. Optional for the owners | an owner | [READINGS-REVIEW.md](READINGS-REVIEW.md); D-009 |
| Pack defects PD-01…PD-24 (settle, or accept the interim readings) | owners | [pack-defects.md](pack-defects.md) |
| M27: a corrected fixture in a future pack release (port manifest with widths, an executable predicate consistent with the frozen FIFO rules) | owners | PD-25; A-038 (revisited) |
| M48, M50, M54, M58: the change-class fields with no supporting Protocol sentence | owners | A-033, PD-02 |
| TechRxiv preprint: retrieve it, or record its access status; make the Charter and File 10 agree | owners | PD-24 |

**People still to be found**

| Item | Owner | Reference |
|---|---|---|
| Independent human mask reviewer: none available (DEV-001). Signing would end the deviation | owners to appoint if one becomes available; must not have authored the templates or the mask | L271; File 21 "Independent reviewer"; package §G |
| Independent implementation auditor | owners to appoint | L555 (5) |

**Human-written work (reserved by CLAUDE.md; Claude does not write it)**

| Item | Owner | Reference |
|---|---|---|
| Directed legal-input suite and reference driver (checklist item 14) | owners | L245, L415 |
| Hand-built FIFO control mutants (item 15), sufficient for F1–F15, including F5 and F10 | owners | Charter L74; L506, L514, L519 |
| F6/F17 control checkers and drivers (item 16); under D-007 also the F1–F5 and F7–F13 control drivers and checkers | owners | L489, L515; D-007; design/fifo/controls/README.md |
| Frozen L544 export script, mutation modes, mutant population, bounded-equivalence assumptions | owners | L544 |

**Work Claude can do on request (under D-005 or the build scope)**

| Item | Owner | Reference |
|---|---|---|
| Draft the remaining payload blocks (`[Execution envelope]`, `[Driver API]`, `[Trace schema]`, `[Checker contract]`) and the File 38 manifest (checklist items 2, 17), then run the assembler and clause-ID checks on them | Claude drafts; owners approve | D-005; File 31 L29–L30 |
| Compose and run the F1–F13 and F17 procedures from H1–H10 as the owner files arrive (harness built; F14, F15 run) | Claude; owners supply the artifacts | L555 (4); plan step 8 |
| If a mask reviewer signs: end DEV-001 and make a new pinned evidence run without its label | Claude | DEVIATIONS.md |
