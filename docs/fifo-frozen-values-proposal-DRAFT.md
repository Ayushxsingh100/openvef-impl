# FIFO frozen-value proposals, checklist items 7–12 — DRAFT for owner review

**Status: DRAFT. Not frozen.** Approved so far, by Krishika under D-006 (24 Nov 2026;
Ayush's confirmation pending): cycle cap 64 and the per-run watchdog. Everything stays DRAFT
until both owners freeze it. Drafted by Claude (Claude
Opus 5.5, via Claude Code) under owner decision D-005 (Krishika, 24 Nov 2026; Ayush's
confirmation pending). The pack freezes these values "after feasibility validation"
(L229, L542, L543), and only the owners can freeze them.

The machine-readable form is
[design/fifo/design-materials-DRAFT.json](../design/fifo/design-materials-DRAFT.json),
which `tests/test_fifo_rtl.py` uses. It applies to spec
[fifo-spec-v0.2.md](fifo-spec-v0.2.md) and RTL
[design/fifo/rtl/ovf_fifo.v](../design/fifo/rtl/ovf_fifo.v). **The observation mask
(item 6) is not drafted here.**

Quotation format as in [fifo-owner-checklist.md](fifo-owner-checklist.md); checked by
`tests/test_doc_quotes.py`.

## Item 7 — Cycle cap

> [02 L227] "All artifacts use the same design-specific fixed cycle cap."

**Proposal: `cycle_cap` = 64** driver cycles after reset release.
- A trace then has 66 rows: one reset row, the reset-release row, 64 driver rows, and
  the row at the cap edge (A-040 convention).
- 64 cycles allow 16 complete fill-and-drain passes of a 4-deep FIFO. The worked example
  (19 edges) fits with room for more.
- The bounded-equivalence bound N must be no greater than the cap (checklist item 7,
  L293).

To validate in feasibility: whether the directed suite (human-written, item 14) fits in
64 cycles. If it doesn't, raise the cap before freeze.

## Item 8 — Safe-idle vector

> [02 L227] "supplies the fixed safe-idle vector for the remaining cycles"

**Proposal: `{"wr_en": "0", "wr_data": "00000000", "rd_en": "0"}`.**
- It is legal in every state under FIFO-041 (`tests/test_fifo_spec.py` checks this).
- No read and no write occur, so `c` and the stored words are unchanged. `rd_valid` = 0
  after every safe-idle edge.
- `rst` is held at 0 by the harness (FIFO-012), so it is not part of the vector.

## Item 9 — Watchdog / timeout

> [02 L334] "Proposed timeout: `T_timeout = max(5 × median(null-netlist wall time over 3 runs for the same artifact/design), 2 seconds)`. Validate during FIFO feasibility; freeze or amend before confirmatory generation."

**Proposal: adopt the L334 formula unchanged, as a wall-clock limit on each simulation run
(RTL or null).** The per-`step` watchdog uses the same value, because a single `step`
that exceeds a whole run's limit is necessarily a timeout.

The pack does not say whether the limit applies per run or per `step` (checklist item 9).
This proposal picks per run, plus the same per-step bound.

**Not yet implemented:** the harness takes `step_timeout_s` and `budget_s` as
parameters. Computing T_timeout needs three null runs per artifact before the measured
runs.

**Feasibility data point** (development host, not evidence; 24 Nov 2026):
- three null-netlist runs of a seeded random legal test driver for 64 cycles took
  1.73 s, 1.36 s and 1.38 s, including container start;
- the median is 1.38 s, so T_timeout = max(6.9 s, 2 s) = 6.9 s.

## Item 10 — Clock, scheduler, drive phase, same-row tie

> [02 L221] "Ordering is mandatory: sample outputs first, invoke the driver second, record its next-input vector third, drive it before the next active edge."

**Proposal: freeze the current build values in `sandbox/sim.py` (`SCHEDULER`) as they
are.**

| Parameter | Proposed value | Source |
|---|---|---|
| Timescale | `1ns/1ps` | build default |
| Clock period | 10 ns, clock starts low, first rising edge at 5 ns | build default |
| Active edge | rising edge of `clk` | FIFO-003 |
| Sampling point | Cocotb `ReadOnly` after the active edge settles | specified, L218 |
| Drive phase | the falling edge before the next active edge | build default ("designated drive phase", L219) |
| Ordering / same-row tie | output-first: sample, invoke driver, record, drive | specified, L221 |
| Reset convention | `reset_sequence[i]` is driven before edge `i`; the last reset edge is the reset-release edge; held inputs apply from the next drive phase | A-040, A-042, FIFO-011 |

The FIFO is fully synchronous with registered outputs, so a mid-cycle drive phase leaves
half a period of margin on both sides of every active edge.

## Item 11 — Trace schema

> [02 L223] "Preserve four-state `0`, `1`, `X`, `Z` values distinctly. Record cycle index, reset, consumed inputs, post-edge outputs, next-input decision, driver completion state and run status."

> [30 L87] "`check_trace(trace, metadata)` runs in a separate process over an immutable serialized trace."

**Proposal: `trace_schema_version` = `openvef-trace-0.1-draft`.** These are the rows the
harness produces today (A-040, A-042).

`trace` is a list of rows, one per active edge from the first reset edge. Each row is an
object with exactly these keys:

| Key | Type | Meaning |
|---|---|---|
| `cycle_index` | integer ≥ 0 | the row's edge `n`, counted from the first reset edge |
| `reset` | boolean | true for rows before the reset-release edge |
| `inputs_consumed_at_edge_n` | object | every top-level input except `clk` (`rst`, `wr_en`, `wr_data`, `rd_en`), as stable immediately before edge `n` (L217) |
| `outputs_after_edge_n` | object | the five outputs, sampled in `ReadOnly` after edge `n` (L218) |
| `next_inputs_scheduled_for_edge_n_plus_1` | object or null | the vector the harness drives before edge `n+1`, including held `rst`; null at the cap row or after a failure (L219) |
| `driver_completed` | boolean | true once the driver has returned `COMPLETE` (L227) |

Value encoding:
- each port value is a string, most significant bit first (FIFO-005);
- characters are `0`, `1`, `X` and `Z`, as the cocotb `LogicArray` string form prints
  them, so the four states stay distinct (L223).

`run_status` is recorded once per trace: `COMPLETE_TRACE` or `TRUNCATED_TRACE` (A-040).

**Serialization (proposed):**
- the trace is serialized as UTF-8 JSON with sorted keys and no insignificant
  whitespace, and its SHA-256 is recorded before the checker runs;
- the checker process receives the decoded value. Because each invocation runs in its own
  process, a checker that mutates its copy cannot alter the stored bytes. The bytes'
  SHA-256 can be re-checked after each invocation.

The canonical-JSON serialization and hashing are **not implemented yet**; this is a
proposal.

## Item 12 — Checker metadata

> [30 L62] "`metadata` contains exactly these public fields: `design_id` (string), `spec_version_sha256` (64-character lowercase hexadecimal string), `trace_schema_version` (string), `cycle_cap` (positive integer), `reset_release_cycle` (non-negative integer), and `trace_integrity_status` (the literal string `VALID`)."

| Field | Proposed value |
|---|---|
| `design_id` | `ovf_fifo` (placeholder, as the top module name) |
| `spec_version_sha256` | computed at freeze over the frozen specification bytes, as the File 38 manifest records it; no value while the specification is a draft |
| `trace_schema_version` | `openvef-trace-0.1-draft` (item 11) |
| `cycle_cap` | `64` (item 7) |
| `reset_release_cycle` | `1` (FIFO-011 under the A-040 row convention) |
| `trace_integrity_status` | `VALID` (fixed by the pack) |

## Not covered

- Item 6, the observation mask: not drafted. An independent human mask reviewer must
  sign it (L271).
- Item 13, the null netlist: the export script
  [design/fifo/export_null.ys](../design/fifo/export_null.ys) is a draft. Freezing the
  export script, mutation modes and mutant population is an owner item (L544).
- Items 14–16 stay human-written.
