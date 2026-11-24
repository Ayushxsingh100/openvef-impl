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

Latest evidence run: **`evidence/run-20261124T112030Z`**.
- Run class `development`; commit `12abd1f`.
- Pinned image per D-002a: CPython 3.11.18, interpreter SHA-256 `92d7e40e…`. The image ID
  and toolchain identity are recorded in its `summary.json`.

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

## 3. What the independent implementation auditor needs

The v1.3.6 pack has no document named an "evidence bundle". The Owner Sign-off Pack is
not in this repository. The list below is derived from L555 step (5), the File 21 F18
checklist and CLAUDE.md. **The owners should confirm it, or supply the list they mean.**

| # | Needed for (L555 (5) / File 21) | Where it is | Status |
|---|---|---|---|
| 1 | Baseline identity | `baseline/` verified against `27_SHA256SUMS.txt`; ZIP SHA-256 in CLAUDE.md | Ready |
| 2 | Implementation and parser/assembler source at an exact commit | `src/`, `runner/`, `sandbox/`; commit `12abd1f`, plus later doc-only commits | Ready |
| 3 | Pinned Python 3.11 behaviour | `sandbox/Dockerfile` (base by digest), `requirements.lock` (hashes), [sandbox.md](sandbox.md); every run records `sys.version`, the interpreter SHA-256, the image ID and the toolchain | Ready |
| 4 | Python 3.11 Unicode tokenizer probe (File 50; L555 (4) "otherwise it must be recorded during this implementation-validation stage") | not recorded | **Open**: run File 50's probe on the pinned interpreter and record it |
| 5 | All mandatory fixture results | `evidence/run-20261124T112030Z/` (`results.jsonl`, `summary.json` with `results_sha256`, `run.log`); fixture index SHA-256 in `summary.json` | Ready as evidence of current state; F18 not passed (§2) |
| 6 | Requirement → module → fixture → evidence map | [traceability.md](traceability.md) | Ready |
| 7 | Every interpretation, with readings and reasons | [ambiguities.md](ambiguities.md) (A-001…A-044, D-001…D-006) and [pack-defects.md](pack-defects.md) (PD-01…PD-24) | Ready; many reviews outstanding (§4) |
| 8 | Sandbox and isolation behaviour (File 21 "Runtime sandbox") | `tests/test_sandbox.py`, `tests/test_broker.py`, [sandbox.md](sandbox.md) | Ready |
| 9 | Unit tests outside F18 | `tests/` (16 files; run with `.venv/bin/python -I tests/<file>`, Docker required for the sandbox tests) | Ready |
| 10 | AI-assistance disclosure | [assistance-log.md](assistance-log.md) (D-005 wording at the top) | Ready |
| 11 | Design materials, mask and freeze record (File 21 "Mask traceability", "Payload/manifest binding", "Independent reviewer") | [OWNER-FREEZE-PACKAGE.md](OWNER-FREEZE-PACKAGE.md) | **Open**: unsigned |
| 12 | Prompt-pair, assembly and clause-ID checks on the real FIFO payloads (File 21 "Payload/manifest binding", "Prompt template-stage hashes", "Clause IDs") | the assembler checks exist (`src/openvef/assembler.py`); the seven FIFO payload blocks and the File 38 manifest are not drafted | **Open** |

## 4. Open items and owners

**Owner signatures and reviews (Krishika and Ayush together, unless noted)**

| Item | Owner | Reference |
|---|---|---|
| Sign the freeze package: spec v0.2, items 7–12, RTL, export script, D-004…D-006, A-040…A-044 (and A-038), overlap disclosure | both owners | [OWNER-FREEZE-PACKAGE.md](OWNER-FREEZE-PACKAGE.md) |
| Ayush's confirmation of every owner decision recorded from Krishika alone: A-001–A-006, A-013, A-014, A-015 case 2, D-002, D-002a, D-003, D-004, D-004a, D-005, D-006 | Ayush | [ambiguities.md](ambiguities.md) |
| D-001 (Draft 2020-12 validator pin): one owner confirmation outstanding | owners | ambiguities.md D-001 |
| Review of the readings decided by Claude: A-007–A-012, A-013 tie case, A-015–A-041, A-043, A-044 (A-042 accepted by Krishika) | both owners (the delegation came from Krishika alone) | ambiguities.md; CLAUDE.md "Standing delegation" |
| Pack defects PD-01…PD-24 (settle, or accept the interim readings) | owners | [pack-defects.md](pack-defects.md) |
| M27: a revised descriptor (port manifest with widths and an executable predicate), or a decision to run it against the frozen FIFO materials with a revisited expectation | owners | A-038 (revisited) |
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
| File 50 tokenizer probe on the pinned interpreter, recorded as evidence | Claude (on request) | L555 (4) |
| Draft the remaining payload blocks (`[Execution envelope]`, `[Driver API]`, `[Trace schema]`, `[Checker contract]`) and the File 38 manifest (checklist items 2, 17), then run the assembler and clause-ID checks on them | Claude drafts; owners approve | D-005; File 31 L29–L30 |
| F1–F15 feasibility harness runs, once the control mutants exist | Claude builds the harness; owners supply the mutants | L555 (4) |
| After freeze and mask signature: a new pinned evidence run without provisional results | Claude | package "After signing" |
