# FIFO: items the owners must write or freeze

Baseline: OpenVEF Planning v1.3.6. This checklist lists every FIFO item that the pack
requires the owners to write or freeze, and that the implementation needs before the
simulator-backed F18 stages and the remaining fixtures can run.

**Requirements only.** Each item gives:
- the exact pack text that requires it;
- the form the pack requires;
- what in this implementation waits for it.

This document proposes no content, values or code for any item. Where the pack itself
proposes a value, it is quoted as the pack's proposal. Where the pack does not state the
form, the item says so.

**Update, 24 Nov 2026 (owner decision D-005, Ayush's confirmation pending):**
- Claude drafts items 1–5, 7–13 and 17. The owners review and approve them.
- Item 6, the mask, may be drafted, but it needs an independent human mask reviewer
  (L271).
- Items 14–16 stay human-written.
- Drafts so far: [fifo-spec-v0.1.md](fifo-spec-v0.1.md) (items 1–5, DRAFT).

**Quotation format**, as in [pack-defects.md](pack-defects.md):
`> [<file> L<line>] "<exact text>"`. `tests/test_doc_quotes.py` checks every quote
verbatim against the baseline.

The general freeze list is Protocol §20 (L536–L546) and Register 16 "Parameters still
TO FREEZE":

> [16 L36] "Exact FIFO and UART specifications, clause IDs, port manifests, legal-input/reset rules and payload block allocation."

> [02 L538] "Freeze original cycle-exact FIFO and UART specifications, port manifests, reset/legal-input rules and distinctive semantics."

## Index

| # | Item | Blocks here |
|---|---|---|
| 1 | FIFO design specification | all simulator-backed fixtures (via items 2–12) |
| 2 | Clause IDs and the authoring-packet manifest | frozen-manifest clause-ID checks (now fixture-supplied, A-005) |
| 3 | Port manifest: directions and widths | vector checks (a)–(d) in the simulation; P17 |
| 4 | Reset protocol | the simulation's reset sequence; checker metadata `reset_release_cycle` |
| 5 | Legal-input rules and an executable legal-input predicate | vector check (e); M27; any ACCEPT that needs (e) |
| 6 | Observation mask, stricter-mask variant, traceability table | L166 (8) masked comparison; design preflight |
| 7 | Cycle cap | the simulation's length; checker metadata `cycle_cap` |
| 8 | Safe-idle vector | after `COMPLETE` |
| 9 | Watchdog / timeout formula | per-step watchdog value |
| 10 | Clock, scheduler, drive phase, same-row tie | build defaults in `sandbox/sim.py` replaced by frozen values |
| 11 | Trace schema | the checker-facing serialized trace; L166 (9)–(11) on a real null trace; M31–M33 |
| 12 | Checker metadata values | the checker's `metadata` argument |
| 13 | Original FIFO RTL and the null netlist | every simulator-backed stage |
| 14 | Reference driver and directed legal-input baseline (directed suite) | design preflight (§7a) |
| 15 | Hand-built FIFO control mutants | F17 feasibility; F1–F15 cases |
| 16 | F6/F17 control checkers and drivers | F6, F17 |
| 17 | Execution envelope and the other payload blocks | authoring packet assembly and hashing |

Fixtures waiting on items 1–13: P01, P14, P17, P21, P42, M07, M31, M32, M33, M57. M27
also waits on item 5.

---

## 1. FIFO design specification

> [02 L59] "cycle-exact design specification;"

> [02 L202] "All MVP specs must be cycle-exact. Variable latency is out of scope"

> [01 L176] "only the FIFO specification/mask, hand-built harness, F1–F15 and F17 using hand-built FIFO control mutants"

**Form required by the pack:**
- original and cycle-exact; variable latency is out of scope;
- delivered as the `[Design specification]` payload block of the authoring-packet
  manifest:

> [38 L10] "\"block_heading\": \"[Design specification]\""

- it must state every don't-care condition the mask uses (see item 6);
- its clauses carry clause IDs (item 2).

**Waiting here:** everything below that derives from the specification.

## 2. Clause IDs and the authoring-packet manifest

> [31 L29] "The authoring-packet manifest must contain `clause_id_regex`, `clause_ids`, and the seven payload sources listed in the sidecar."

> [31 L29] "`clause_ids` must be a duplicate-free, lexicographically sorted array of strings, each of which fully matches that pattern."

> [38 L5] "\"spec_version_sha256\": \"TO_FREEZE\""

> [30 L9] "against the exact `clause_ids` array and `clause_id_regex` in the frozen manifest"

**Form required by the pack:**
- a frozen manifest in the File 38 template shape with `design_id`,
  `spec_version_sha256`, `clause_id_regex`, `clause_ids` and the seven payload blocks;
- `UNSPECIFIED` must never appear in `clause_ids`;
- the visible clause IDs in the payloads must equal the manifest set (File 31 L30).

**Waiting here:** parse-time clause-ID checks against a frozen manifest. Fixtures
currently use their own `manifest_clause_ids` (A-005); see pack-defects PD-09.

## 3. Port manifest: directions and widths

> [02 L60] "top-level port manifest and signal directions/widths;"

> [30 L83] "(a) its key set equals the frozen top-level input-port set exactly"

> [30 L83] "(c) the value length equals the port width"

> [38 L16] "\"block_heading\": \"[Port manifest]\""

**Form required by the pack:**
- every top-level port, with its direction and width;
- the input-port set is the exact key set a driver vector must have;
- the widths are exact string lengths;
- the payload block is `[Port manifest]`.

The pack does not specify the manifest's internal format.

**Waiting here:**
- the `input_ports` and `output_ports` that the simulation stage requires;
- P17, which supplies port names only and has no widths.

## 4. Reset protocol

> [02 L61] "reset protocol and legal-input assumptions;"

> [30 L48] "The first `Driver.step` call occurs after reset release, with `cycle_index=0`"

> [02 L276] "Reset/initialization windows are explicit in the specification and traceability table."

> [02 L291] "with the same reset sequence and legal-input assumptions from the design specification"

> [30 L92] "`reset_release_cycle`: non-negative integer;"

**Form required by the pack:**
- an exact reset sequence that the harness can apply before the first `step` call;
- the same sequence is used by the bounded-equivalence miter;
- it defines the reset-release active edge and the `reset_release_cycle` metadata value;
- reset windows are explicit in the specification and in the mask traceability table;
- the payload block is `[Reset and legal-input rules]`:

> [38 L22] "\"block_heading\": \"[Reset and legal-input rules]\""

**Waiting here:** the `reset_sequence` that the simulation stage requires.

## 5. Legal-input rules and an executable legal-input predicate

> [30 L83] "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification"

> [30 L83] "Missing keys, extra keys, wrong width, non-string values, illegal symbols and illegal protocol combinations are distinct reason codes."

> [02 L278] "The same mask and legal-input assumptions are used by the trace comparator and bounded-equivalence miter."

> [02 L291] "Freeze those assumptions with the design pack."

> [41/M27.json L14] "\"legal_input_predicate\": \"wr_en must be 0 when full is 1\""

**Form required by the pack:**
- author-visible rules in the reset/legal-input payload;
- a predicate over one full driven vector, which the harness evaluates before driving
  (check (e)), with `ILLEGAL_PROTOCOL_STATE` on failure;
- the same assumptions used by the miter;
- frozen with the design pack.

The pack does **not** specify the form of an executable predicate: no predicate
language is defined (pack-defects PD-06). Choosing that form is an owner decision.

For **M27** specifically:
- an executable predicate that corresponds to its prose;
- a port manifest under which M27's vector passes checks (a)–(d). M27's vector includes
  `full`, and the descriptor does not say whether `full` is an input port (PD-06).

**Waiting here:**
- check (e) in the simulation stage. The only value it accepts today is the test-only
  literal `ALL_INPUTS_LEGAL`; anything else is NOT_DETERMINED, never ACCEPT;
- M27 (A-038).

## 6. Observation mask, stricter-mask variant and traceability table

> [02 L540] "Freeze observation mask and stricter-mask sensitivity variant; evaluator-only."

> [02 L271] "Every mask entry must map to an explicit specification clause ID and a readable clause excerpt."

> [02 L271] "The table is signed by an independent mask reviewer and is checked in F18."

> [02 L279] "A stricter-mask sensitivity variant is independently reviewed and applied to archived traces. Its predicate set/hash is **TO FREEZE**."

> [24 L1] "mask_entry_id,mask_variant,spec_version_sha256,output_or_predicate_signal,cycle_window_predicate,comparison_rule,dont_care_rule,specification_clause_id,exact_supporting_clause_text"

> [02 L539] "Complete and sign mask-to-specification traceability table; every don't-care window is specified in author packet."

**Form required by the pack** (L271–L280):
- mask rows in the File 24 traceability-table columns, each mapped to a clause ID with
  its exact text;
- predicate signals are always observable and compared;
- data fields are masked only in documented don't-care windows;
- the predicate is evaluated on the null trace for both members of a pair;
- the mask cannot permit latency shifts;
- the same mask is used by the trace comparator and the miter;
- evaluator-only: never in the authoring packet;
- signed by an independent mask reviewer.

**Waiting here:**
- the masked comparison in L166 (8) and the §7a preflight. `compare_runs` takes the
  observed outputs as a parameter, so no mask is built in;
- the F18 traceability check.

## 7. Cycle cap

> [02 L62] "cycle cap and safe-idle policy;"

> [02 L227] "All artifacts use the same design-specific fixed cycle cap."

> [02 L229] "Cycle cap, safe-idle vectors and timeout formula are **TO FREEZE** after feasibility validation."

> [30 L62] "`cycle_cap` (positive integer)"

**Form required by the pack:**
- one positive integer for the FIFO, the same for every artifact;
- author-visible (authoring packet);
- passed to the checker as `metadata.cycle_cap`;
- the bounded-equivalence bound N is no greater than it (L293).

**Waiting here:** `cycle_cap` in the simulation stage.

## 8. Safe-idle vector

> [02 L210] "`COMPLETE`, after which the harness drives safe-idle inputs until the fixed cycle cap."

> [02 L227] "supplies the fixed safe-idle vector for the remaining cycles"

**Form required by the pack:**
- one fixed complete input vector for the FIFO, driven after `COMPLETE` until the cap;
- frozen after feasibility validation (L229);
- author-visible as part of the "cycle cap and safe-idle policy" (L62).

**Waiting here:** `safe_idle` in the simulation stage.

## 9. Watchdog / timeout formula

> [02 L229] "A wall-clock timeout is separate."

> [02 L334] "Proposed timeout: `T_timeout = max(5 × median(null-netlist wall time over 3 runs for the same artifact/design), 2 seconds)`. Validate during FIFO feasibility; freeze or amend before confirmatory generation."

> [02 L542] "Freeze driver API, scheduler, alignment, same-row tie, cap, safe-idle and watchdog."

**Form required by the pack:** a frozen wall-clock watchdog rule. The pack proposes the
L334 formula, to be validated in FIFO feasibility and then frozen or amended. The pack
does not say whether the watchdog applies per `step` call or per run.

**Waiting here:** the per-step watchdog value. The simulation stage takes
`step_timeout_s` and `budget_s` as parameters.

## 10. Clock, scheduler, drive phase and same-row tie

> [02 L208] "The harness owns the clock and scheduler."

> [02 L218] "`outputs_after_edge_n`: top-level outputs sampled in Cocotb `ReadOnly` after edge `n` settles;"

> [02 L219] "then applied by the harness in the designated drive phase before edge `n+1`."

> [02 L221] "Ordering is mandatory: sample outputs first, invoke the driver second, record its next-input vector third, drive it before the next active edge."

> [02 L542] "Freeze driver API, scheduler, alignment, same-row tie, cap, safe-idle and watchdog."

**Form required by the pack:**
- the sampling point is already given: Cocotb `ReadOnly` after the active rising edge;
- the "designated drive phase" is not given;
- the clock period, the timescale and the same-row tie rule are not given in numeric or
  exact form. They are frozen under L542 and validated by F2 and F10.

**Waiting here:** these build defaults in `sandbox/sim.py` (`SCHEDULER`) are replaced
by frozen values:
- clock period;
- timescale;
- drive phase;
- reset-edge convention.

## 11. Trace schema

> [02 L64] "trace schema and field definitions; and"

> [02 L543] "Freeze checker contract, trace schema and double-run null determinism requirement."

> [02 L217] "`inputs_consumed_at_edge_n`: top-level inputs stable immediately before active rising edge `n`;"

> [02 L223] "Preserve four-state `0`, `1`, `X`, `Z` values distinctly. Record cycle index, reset, consumed inputs, post-edge outputs, next-input decision, driver completion state and run status."

> [38 L40] "\"block_heading\": \"[Trace schema]\""

**Form required by the pack:**
- per-row fields including `inputs_consumed_at_edge_n`, `outputs_after_edge_n` and
  `next_inputs_scheduled_for_edge_n_plus_1`, plus cycle index, reset, driver
  completion and run status;
- four-state values kept distinct;
- the immutable serialized form that the checker receives;
- a `trace_schema_version` string;
- author-visible as the `[Trace schema]` payload block.

The serialization format and the field definitions are not given.

**Waiting here:**
- L166 (9)–(11) on a real null trace;
- M31, M32, M33 and every ACCEPT fixture, because ACCEPT needs two checker PASS
  verdicts on the null trace.

## 12. Checker metadata values

> [30 L62] "`metadata` contains exactly these public fields: `design_id` (string), `spec_version_sha256` (64-character lowercase hexadecimal string), `trace_schema_version` (string), `cycle_cap` (positive integer), `reset_release_cycle` (non-negative integer), and `trace_integrity_status` (the literal string `VALID`)."

**Form required by the pack:** exactly these six fields. Their FIFO values come from:
- the frozen manifest (`design_id`, `spec_version_sha256`);
- item 11 (`trace_schema_version`);
- item 7 (`cycle_cap`);
- item 4 (`reset_release_cycle`).

**Waiting here:** the checker invocation on a real null trace.

## 13. Original FIFO RTL and the null netlist

> [02 L233] "The null-mutant netlist is generated from the original RTL by exactly the same synthesis/export script, tool versions and top-level interface as the mutant netlists, with no mutation applied."

> [02 L233] "Export must preserve top module name and public ports. Run the export twice and compare null-netlist hashes."

**Form required by the pack:**
- original RTL implementing the frozen specification;
- a null netlist exported from it by the frozen synthesis/export script and tool
  versions (Yosys/MCY, L235, L544), keeping the top module name and public ports, with
  a repeatable hash (F14).

The RTL language and its simulator compatibility are not stated. The pinned simulator
here is Icarus Verilog 12.0 (D-003).

**Waiting here:** every simulator-backed stage. Yosys v0.71 and MCY v0.71 are pinned
under D-004/D-004a; the frozen export script is still open.

## 14. Reference driver and directed legal-input baseline (directed suite)

> [02 L245] "Before any scheduled artifact slot, run the frozen reference driver and directed legal-input baseline on original RTL and the null netlist."

> [02 L526] "Confirmatory F17 is run only after F16/re-pilots and the complete authoring packet, directed suite, mask and analysis plan are frozen and hashed"

**Form required by the pack:**
- a frozen reference driver and a directed legal-input baseline;
- run through the production harness on RTL and the null netlist;
- written against the specification only (L415, "a directed corner-case suite written
  against the specification only, before any LLM generation").

**Waiting here:** the §7a design preflight. CLAUDE.md reserves the directed suite to the
owners.

## 15. Hand-built FIFO control mutants

> [01 L74] "One null reference and a **hand-built set of distinct control mutants** sufficient to exercise the F1–F15 cases"

> [02 L506] "F17 feasibility uses only hand-built FIFO control mutants."

**Form required by the pack:**
- hand-built FIFO mutants, distinct from each other;
- sufficient to exercise F1–F15, including the F5 and F10 cases (L514, L519);
- not the confirmatory MCY manifest.

**Waiting here:** F1–F15 and F17 feasibility (not F18 fixtures).

## 16. F6/F17 control checkers and drivers

> [02 L515] "Hand-built correct checker, always-PASS checker, and non-exposing driver"

> [02 L489] "reference, always-PASS, always-FAIL, stimulus-literal, crashing, stricter-than-mask and nondeterministic checkers"

**Form required by the pack:** hand-built known-answer checkers and drivers with the
behaviours listed. CLAUDE.md reserves these to the owners.

**Waiting here:** F6 and F17 (not F18 fixtures).

## 17. Execution envelope and the other payload blocks

> [38 L28] "\"block_heading\": \"[Execution envelope]\""

> [31 L29] "the seven payload sources listed in the sidecar"

**Form required by the pack:**
- the seven design-specific payload blocks of the File 38 manifest, each with its frozen
  bytes and SHA-256: design specification, port manifest, reset and legal-input rules,
  execution envelope, driver API, trace schema, checker contract;
- the clause IDs visible in them must equal the manifest set.

The content of `[Execution envelope]` is not defined anywhere else in the pack.

**Waiting here:** authoring-packet assembly and hashing. CLAUDE.md reserves
authoring-packet text to the owners.
