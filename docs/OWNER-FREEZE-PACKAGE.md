# Owner freeze package — FIFO feasibility materials

**For:** Krishika and Ayush Kumar Singh (owners), to sign in a single sitting, and an
independent human mask reviewer (Protocol L271).
**Prepared by:** Claude (Claude Opus 5.5, via Claude Code), 24 Nov 2026. Claude prepared
this list. It approves nothing, and it does not sign.

## How to use this package

1. **Check the hashes.** Run `python3 -I tests/test_freeze_package.py` (or
   `.venv/bin/python -I tests/test_freeze_package.py`). It recomputes every SHA-256 below
   from the working tree and fails if any differs, so you know you are signing exactly
   these bytes.
   - For a plain path, the hash is the SHA-256 of the file.
   - For `docs/ambiguities.md#ID`, it is the SHA-256 of that one decision record,
     computed as described in [tests/freeze_hashes.py](../tests/freeze_hashes.py). Later
     entries elsewhere in the file therefore do not change it.
2. **Mark each line**, for each owner: **Approve**, or **Change** with a note.
3. **A line is frozen only when both owners approve it.** Any Change means a new draft,
   new hashes and a new package. The listed files are not edited in place after
   signing. The freeze is recorded separately, against these hashes, so the signed bytes
   stay the reviewed bytes.
4. **The mask needs a separate signature,** from the independent human mask reviewer
   (section F). An owner signature does not replace it.

Mark boxes as `[x]`. Write notes in the Notes column.

## A. Design specification (D-005; checklist items 1–5)

| # | Item | File | SHA-256 | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| A1 | FIFO specification v0.2: FIFO-001…FIFO-043, port manifest, reset and legal-input rules, FIFO-042 executable predicate | `docs/fifo-spec-v0.2.md` | `5e57ce18c8297aaed27e80b1a7a49476f41c70359e331fe8f5c54f96594c24b5` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

On freeze, `spec_version_sha256` (File 30 L62; File 38) is computed over the frozen
specification bytes. Until then, runs use the SHA-256 of this draft file and are
provisional.

## B. Frozen-value proposals (checklist items 7–12)

| # | Item | Proposed value | Source | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| B1 | Cycle cap (item 7) | 64 driver cycles after reset release | approved by Krishika under D-006 | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| B2 | Safe-idle vector (item 8) | `{"wr_en": "0", "wr_data": "00000000", "rd_en": "0"}` (`rst` held at 0) | proposal | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| B3 | Watchdog (item 9) | L334 formula, per run and per step; wall time per A-043; calibration ceiling 120 s (build default) | per run approved by Krishika under D-006 | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| B4 | Scheduler (item 10) | timescale 1ns/1ps; 10 ns clock, starts low; drive at the falling edge; sample in `ReadOnly` (L218); output-first (L221); reset per FIFO-011, A-040, A-042 | proposal (current build values) | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| B5 | Trace schema (item 11) | `openvef-trace-0.1-draft`: six row keys; `0`/`1`/`X`/`Z` strings; canonical UTF-8 JSON plus SHA-256 | proposal | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| B6 | Checker metadata (item 12) | `design_id` `ovf_fifo`; `spec_version_sha256` computed at freeze; `trace_schema_version` as B5; `cycle_cap` 64; `reset_release_cycle` 1; `trace_integrity_status` `VALID` | proposal | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

| File | SHA-256 |
|---|---|
| `docs/fifo-frozen-values-proposal-DRAFT.md` | `b8d5ec793bd9aef0be41f684f009afbabe819912c618da4e2da39a7244305952` |
| `design/fifo/design-materials-DRAFT.json` | `30758c86ad88a5dc34bbe7802c5272935e8cdca810f6eec5f8cd1ff8895ba393` |

## C. RTL and null-netlist export (checklist item 13)

| # | Item | File | SHA-256 | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| C1 | FIFO RTL `ovf_fifo` (Verilog, Icarus 12 `-g2012`) | `design/fifo/rtl/ovf_fifo.v` | `ca06abf55e6a82e6617dab9cd5d7e4ef0118d082b7789fce169016307fe2042b` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| C2 | Null-netlist export script (Yosys v0.71). The frozen L544 export script, mutation modes and mutant population are separate owner items, **not** frozen by this line | `design/fifo/export_null.ys` | `85dfdddda430adc22ea3df9c961397d596264b195e56cba8c49da84b4bc474b1` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

For reference, not signed here: the null netlist exported from C1 with C2 has SHA-256
`56dabfecc3768078bd96f7a026034ee9e2a795e266db89282b4ad4434ea64747`. It was identical on
two exports in each evidence run (run-20261124T111335Z, run-20261124T112030Z).

## D. Owner decisions (confirmation of Krishika's decisions; Ayush's confirmation pending on each)

| # | Record | Section | SHA-256 | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| D1 | D-004: Yosys v0.71 and MCY v0.71 pins | `docs/ambiguities.md#D-004` | `cd34f9a4b75010db7a95b918dc8251881eae85870465b4414ace1f10d67af80a` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| D2 | D-004a: `click==8.5.1` for MCY's command-line tool | `docs/ambiguities.md#D-004a` | `4f51302297ae8dc264669bc3766fdbc31b32ab1030f6a1bfe8308bfa3956b060` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| D3 | D-005: FIFO design materials AI-assisted, with disclosure | `docs/ambiguities.md#D-005` | `d3dd7667dfc1661242f013ca32b7ee7e8110e5bb791933584a86c66dbdc2d9b8` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| D4 | D-006: approvals (A-042, threshold 3, `ovf_fifo`, cap 64, watchdog per run) | `docs/ambiguities.md#D-006` | `41d68cc0a6f39cc6ddae0522400f6049a23a5c2a2d256b331a9106f0c4fccfce` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

## E. Readings decided by Claude under the standing delegation (owner review)

| # | Reading | Section | SHA-256 | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| E1 | A-040: trace-row fields and row numbering | `docs/ambiguities.md#A-040` | `2329ab5b9ee388e29ef14ff266749ce6db8b205a613b02d285f41e4027a2de9a` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| E2 | A-041: predicate scope (vector plus same-row sampled outputs) | `docs/ambiguities.md#A-041` | `6c215691edd86c33481bfc05e36e655e5a3a095941aea2deaa161c09edb67cae` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| E3 | A-042: harness-owned reset, not a driver key (accepted by Krishika, D-006) | `docs/ambiguities.md#A-042` | `423211c6484c3cb04cbce32fa9fb344050b29302608a87f9db12c5236b3d3064` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| E4 | A-043: L334 wall time = the whole null-run container | `docs/ambiguities.md#A-043` | `3e16a6d1fe840456dc7342c92ff0d32a2e4ce30b96d09c6ebe975f7c1095c0be` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| E5 | A-044: a fixture's names-only port manifest (P17) | `docs/ambiguities.md#A-044` | `395848f1bb6b6630610ab026e1025a17ca003a2bae5fce47857ea5ace19f0d3b` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |
| E6 | *(additional, not in the requested list)* A-038 revisited: M27 stays NOT_IMPLEMENTED | `docs/ambiguities.md#A-038` | `483c8539baa37494807333cffa1ba33db4cef578fe29286503604326d0800dad` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

## F. Benchmark-overlap disclosure (Protocol L468)

| # | Item | File | SHA-256 | Krishika | Ayush | Notes |
|---|---|---|---|---|---|---|
| F1 | Disclosure note with the GateTruth/DVBench comparison. **Decision: disclose; do not rename ports.** Re-check the relayed source extracts before signing | `docs/fifo-benchmark-overlap-disclosure-DRAFT.md` | `ae37c774e98a6a0db0b9af0642dd5de399c281becc58115c74ae609f433bf417` | [ ] Approve [ ] Change | [ ] Approve [ ] Change | |

The note has its own owner-signature table, which can be completed in the same sitting.

## G. Observation mask: independent human mask reviewer (Protocol L271)

> [02 L271] "The table is signed by an independent mask reviewer and is checked in F18."

> [21 L32] "| Independent reviewer | Reviewer did not author templates or mask; signs exact hashes and checklist | PENDING |"

| File | SHA-256 |
|---|---|
| `design/fifo/mask/ovf_fifo-mask-DRAFT.json` | `78477cd41df36074c06aca31bfca3aae4de7a085980559480a35e2a08c180b0f` |
| `design/fifo/mask/ovf_fifo-mask-traceability-DRAFT.csv` | `3e443a68368b693e33608db0daa94ae52e8e61a9a6b7a55b55de834862360f92` |

The mask was drafted by Claude under D-005. The reviewer must be a human who did not
author the prompt templates or the mask. Claude cannot be this reviewer.

| Field | Entry |
|---|---|
| Reviewer name | |
| Role / affiliation | |
| Independence statement: "I did not author the prompt templates or this mask." | [ ] Confirmed |
| Every row maps to an author-visible clause with an exact excerpt (L271) | [ ] Confirmed |
| Data fields masked only in documented don't-care windows; predicate signals always compared (L274–L275) | [ ] Confirmed |
| Stricter-mask variant reviewed (L279) | [ ] Confirmed |
| Decision | [ ] Approve [ ] Change |
| Notes | |
| Signature | |
| Date | |

## Owner signatures

| Owner | Signature | Date |
|---|---|---|
| Krishika | | |
| Ayush Kumar Singh | | |

## After signing

- **Record the freeze** in a new record that cites these hashes. The listed files are
  not edited in place.
- **Compute `spec_version_sha256`** over the frozen specification.
- **Re-run the pinned evidence run.** The 10 simulator fixtures stop being provisional
  only when all of these hold:
  - A1, B1–B6, C1 and C2 are frozen;
  - G is signed;
  - E1–E5 are approved.
- **Lines not covered by this package** stay open. See
  [AUDIT-READINESS.md](AUDIT-READINESS.md).
