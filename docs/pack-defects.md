# OpenVEF Planning v1.3.6: pack defects for a corrected release

Baseline: OpenVEF Planning v1.3.6, ZIP SHA-256
`2e7008210a807868ad3d8a878820afa7cf1066f1c2b5b1cb437b911aa9b30c21`.

This document lists every place found so far where the v1.3.6 pack is internally
inconsistent or under-specified, so that a corrected release can settle each one in the
text. It collects the findings recorded in [ambiguities.md](ambiguities.md). Each defect
lists:
- the exact pack text;
- the defect;
- the fixtures it affects;
- how this implementation handles it for now;
- what the corrected text must settle.

How it handles it for now does not fix the pack. Owner decisions and Claude-decided
readings are interim, and a corrected release should make each of them unnecessary.

**Quotation format.** Each quote is written `> [<file> L<line>] "<exact text>"`:
- `<file>` is the pack file number (`02` Protocol, `30` Response Parser and Execution
  Contract, `31` Prompt Assembly spec, `36` F18 Fixture Catalog) or a fixture
  descriptor (`41/<ID>.json`);
- `<line>` is the line in the extracted baseline;
- the quoted text is a verbatim substring of that line.

`tests/test_doc_quotes.py` checks every quote in this file against the baseline.

**Classes.**
- **I**, internal inconsistency: two pack texts, or a text and a fixture, disagree.
- **U**, under-specification: the text needed to decide an outcome is missing.
- **R**, rule tied to fixture labels: the text states a value only for a fixture ID,
  not as a rule.

Not listed here: items the pack itself marks TO FREEZE, or reserves to owner-written
materials (the FIFO specification, mask, cycle cap and so on). Those are not defects;
they are listed in [fifo-owner-checklist.md](fifo-owner-checklist.md).

## Summary

| ID | Class | Topic | Fixtures affected now | Interim handling |
|---|---|---|---|---|
| PD-01 | I | Halt-signature domains vs M42/M47 signatures | M42, M47 | A-031 (Claude) |
| PD-02 | U, R | Change-class vectors: error classes and scope/rule tokens | M48, M50, M54, M58 (NOT_IMPLEMENTED) | A-033 (owner correction + Claude) |
| PD-03 | I | Exact comparison of four fields vs control-vector expectations with extra keys | M14, M17, M41, M48–M58 | A-032 (Claude) |
| PD-04 | U | `parser_unit_vector` and the disposition of unit vectors | M36 | A-012 (Claude) |
| PD-05 | I | OUTPUT_TRUNCATED: stage-map row order vs evaluation order | P11a | A-001 (owner, Ayush pending) |
| PD-06 | U, I | Driver-vector parameters: prose predicate, missing widths, output port in a driven vector | M26, M27 (NOT_IMPLEMENTED) | A-027, A-038 (Claude) |
| PD-07 | U | Fixture input shapes and the call under test | most non-response fixtures | A-002, A-012, A-025, A-026, A-028 |
| PD-08 | U | `UNSPECIFIED` text requirement has no mechanical rule | P21 | A-004 (owner, Ayush pending) |
| PD-09 | U | Source of the manifest `clause_ids` for fixtures | all response fixtures | A-005 (owner, Ayush pending) |
| PD-10 | I | Pointer sort: string tokens vs numeric index | none | A-006 (owner, Ayush pending) |
| PD-11 | I | SOURCE_AST order across files | none | A-007 (Claude) |
| PD-12 | U | SOURCE_AST positions and definitions: BOM in a string, invalid UTF-8, whitespace, missing line | none | A-008–A-011 (Claude) |
| PD-13 | I | IMPORT_POLICY category order within a file; equal-key ties | none | A-013, A-014 (owner, Ayush pending); tie (Claude) |
| PD-14 | U | Module-body statements not classified | none | A-015 (Claude; case 2 owner) |
| PD-15 | U | Prohibited names, `random`, identifier scan edges | none | A-016–A-019 (Claude) |
| PD-16 | U | AST_SIGNATURE: parameter checks, bindings, class body, positions | none | A-020–A-023 (Claude) |
| PD-17 | U | Missing stage-map rows: compile error without a line, import exception, factory timeout, simulator process failure | none | A-024, A-034, A-037, A-039 (Claude) |
| PD-18 | U | Post-construction check order; `check_trace` signature timing | none | A-035 (Claude) |
| PD-19 | U | Deterministic execution: hash randomization | none | A-036 (Claude) |
| PD-20 | U | Serializer emitted set; clause-ID packet check order | M15, M20 | A-029, A-030 (Claude) |
| PD-21 | U | Non-JSON number tokens | none | A-003 (owner, Ayush pending) |
| PD-22 | I | Stale planning-pack version label in File 30 | none | none needed (found while preparing this document; not in ambiguities.md) |
| PD-23 | U | Trace-row fields named only in prose; trace numbering vs `reset_release_cycle`; run-status domain | none today (simulation not exercised by fixtures) | A-040 (Claude) |

"Fixtures affected now" means the fixture's result depends on the interim handling.
"None" means no current fixture exercises the case, but a real artifact can.

---

## PD-01 — Halt-signature domains vs the M42/M47 signatures (I)

> [02 L185] "`evaluator_component` is `SIMULATOR`, `REPLAY_VERIFIER`, `RECORDER`, `TRACE_ALIGNMENT_CHECKER`, `TRACE_SERIALIZER` or `RTL_NULL_COMPARATOR`"

> [02 L185] "`stable_error_class` is a simple exception class name matching `[A-Za-z_][A-Za-z0-9_]*` for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes"

> [41/M42.json L16] "\"evaluator_component\": \"simulator\""

> [41/M47.json L23] "\"evaluator_component\": \"recorder\""

> [41/M47.json L24] "\"stable_error_class\": \"RecorderFault\""

**Defect.** M42 and M47 supply halt signatures whose components are outside the L185
domains: lower-case component names, and a non-`NONE` error class on a
trace-integrity signature. The pack does not say whether an out-of-domain signature is
invalid input, and gives no outcome for one.

**Interim (A-031).** Signatures the ledger builds from halt events enforce the domains;
ready-made signatures in a descriptor are compared for identity as given. M42 and M47
pass under this reading.

**To settle.** Either correct the M42/M47 descriptors to in-domain values, or define the
outcome for an out-of-domain signature.

## PD-02 — Change-class lifecycle vectors: error classes and tokens (U, R)

> [02 L176] "Closed `required_action` literals used by lifecycle fixtures:"

> [02 L175] "The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED`"

> [02 L175] "`M54` uses error class `HALT_SIGNATURE_SCHEMA`"

> [02 L175] "(error class `MID_RUN_REEVALUATION`)"

> [02 L154] "SIMULATOR_ERROR|target=<RTL_OR_NULL>|class=<EXCEPTION_CLASS>"

> [41/M48.json L23] "\"rerun_scope_rule\""

**Defects.**
1. **R.** L176 states each `required_action` literal against a fixture ID ("`M48` =
   …"), not against a change class or rule. The `change_class` input labels
   (`FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` and four others) appear only in
   descriptors.
2. **U.** The error class of M48, M50 and M58 is stated nowhere. L175 states error
   classes only for the M41, M53 and M54 vectors. "Error class equals the diagnostic
   CODE" is not a rule: M41's error class `MID_RUN_REEVALUATION` differs from its
   diagnostic, and L154 puts `SIMULATOR_ERROR|…` under error class
   `EVALUATOR_INFRASTRUCTURE_FAILURE`.
3. **U.** These expected-object tokens appear only in descriptors:
   - M48 `rerun_scope_rule`;
   - M50 `affected_slots`;
   - M54 `stable_error_class_rule` and `stable_diagnostic_code_rule`;
   - M58 `affected_scope` and `unaffected_design_scope`.

   Their meanings are in L176, L181, L183 and L185, but the exact token strings are not.
   The pack also gives no output schema that names these properties (see PD-03).

**Interim (A-033, revised per owner correction).** The literals are taken from L176,
keyed by change class. Every other field is derived from a cited sentence or reported as
unsupported. M53 passes; M48, M50, M54 and M58 stay NOT_IMPLEMENTED.

**To settle.**
- State the change classes and their outcome fields as rules.
- State the error class for each revision vector.
- Either put each scope or rule token in the Protocol as a literal, or define these
  properties so that the expected values follow from the text.

## PD-03 — Four-field comparison vs control-vector expectations (I)

> [36 L23] "a single exact expected disposition/stage/error/diagnostic (or exact control-vector expectation)"

> [36 L176] "disposition, stage, error class and exact diagnostic bytes"

**Defect.** Catalog L176 says the runner compares four fields. L23 also allows an
"exact control-vector expectation". M14, M17, M41 and the change-class vectors carry
extra keys (`output_diagnostic_bytes`, `rerun_slots`, …), and M14 and M17 have no
`diagnostic` key at all. The pack gives no schema for control-vector expectations, so
the property names exist only in descriptors.

**Interim (A-032).** A control-vector expectation is compared as a whole object, and
each extra key is computed from a cited rule. The property *names* come from the
descriptors.

**To settle.**
- Say which comparison applies to which fixtures.
- Give the control-vector output schema: property names, types and the rule for each.

## PD-04 — `parser_unit_vector` and unit-vector dispositions (U)

> [41/M36.json L6] "\"fixture_class\": \"parser_unit_vector\""

> [36 L27] "Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately grammar-exempt"

> [36 L15] "`CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector"

> [02 L177] "A `CONTROL_EXPECTATION` fixture exercises a serializer, protocol or lifecycle rule"

**Defect.**
- The class `parser_unit_vector` is not defined anywhere in the pack.
- The Catalog (L15) and the Protocol (L177) define `CONTROL_EXPECTATION` with different
  lists: "policy" in the Catalog, "protocol" in the Protocol.
- No rule assigns a disposition to unit vectors. `fixture_class` does not determine
  disposition either: M42 and M47 are `lifecycle_unit_vector` but expect
  `DESIGN_ABORTED_NO_SLOTS_SCORED`.

**Interim (A-012).** The input shape `{source_file, syntax_error}` applies the column
rule with disposition `CONTROL_EXPECTATION`, on the strength of L177's "protocol".

**To settle.**
- Define `parser_unit_vector`.
- Align the two `CONTROL_EXPECTATION` definitions.
- Say how a unit vector's disposition is determined.

## PD-05 — OUTPUT_TRUNCATED: row order vs evaluation order (I)

> [02 L139] "The first applicable row after the exact evaluation order below controls."

> [02 L144] "Provider finish reason explicitly reports max-token truncation"

> [02 L166] "(1) Response UTF-8/JSON/schema/manifest-clause checks."

> [30 L7] "is `OUTPUT_TRUNCATED` at `PARSE_SCHEMA` and is reported separately"

**Defect.**
- The stage map puts envelope/schema rejection before truncation, and step (1) does not
  mention the finish reason. Read literally, P11a (truncated JSON with finish reason
  `length`) would be `SCHEMA_REJECT|pointer=/`, not its expected `OUTPUT_TRUNCATED`.
- A finish reason of `length` with complete, valid JSON is unspecified.

**Interim (A-001, owner decision, Ayush pending).** Truncation is checked first, and
`length` always gives `OUTPUT_TRUNCATED`.

**To settle.** Give the position of the finish-reason check in step (1), and the
outcome for `length` with valid JSON.

## PD-06 — Driver-vector check parameters (U, I)

> [30 L83] "the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification"

> [30 L83] "Missing keys, extra keys, wrong width, non-string values, illegal symbols and illegal protocol combinations are distinct reason codes."

> [41/M27.json L14] "\"legal_input_predicate\": \"wr_en must be 0 when full is 1\""

**Defect.**
1. No predicate language or form is defined, and M27 supplies its predicate as English
   prose.
2. M27 supplies no input-port set or widths, so checks (a)–(d), which run first, cannot
   be established. Its vector includes `full`, which in a FIFO is conventionally an
   output; if so, check (a) would report `EXTRA_KEYS`, not the expected
   `ILLEGAL_PROTOCOL_STATE`.
3. M26 supplies keys without widths.
4. The order between `MISSING_KEYS` and `EXTRA_KEYS` within check (a) is not stated.

**Interim (A-027, A-038).**
- Checks run in order, and a check without parameters is not run.
- Missing keys are reported before extra keys (the order of the L125 enumeration).
- M27 stays NOT_IMPLEMENTED: executing prose would require inventing behaviour.

**To settle.**
- Define the form of the legal-input predicate (the FIFO-specific predicate itself is
  an owner checklist item).
- Give M27 a port manifest consistent with its vector.
- State the order within check (a).

## PD-07 — Fixture input shapes and the call under test (U)

> [36 L23] "a literal JSON input"

**Defect.** The Catalog defines no mapping from each input shape to the stage or
function under test, including:
- `response_object`;
- `{driver_source, checker_source}`;
- `events`, `checker_runs` and `null_runs`;
- `runtime_pair` + `response_object`;
- `port_manifest` + `response_object`;
- `change_class`.

It also does not define the event vocabulary, the precedence among several supplied
events, or the record forms of checker run outcomes. On precedence, the only guide is
the L139 sentence quoted in PD-05 and the evaluation order.

**Interim.**
- A-002 (owner, Ayush pending): `response_object` starts at schema validation.
- A-012: source pair starts at SOURCE_AST.
- A-025: event kinds map to stage-map rows, ranked by (step, row, file, line).
- A-026: four run-record forms.
- A-028: composite inputs run every available stage first.

**To settle.** Give an input-shape table: shape, entry stage, field meanings and how
the supplied outcomes stand in for later stages.

## PD-08 — `UNSPECIFIED` text requirement (U)

> [30 L9] "`UNSPECIFIED` is permitted only for behavior not specified in the received packet, and the text must identify the missing behavior."

**Defect.** The pack gives no mechanical test, diagnostic or pointer for text that does
not "identify the missing behavior".

**Interim (A-004, owner, Ayush pending).** Accepted at parse time; human review.

**To settle.** Either mark it as human-reviewed only, or define the test and its
diagnostic.

## PD-09 — Manifest `clause_ids` for fixtures (U)

> [30 L9] "against the exact `clause_ids` array and `clause_id_regex` in the frozen manifest"

**Defect.**
- No frozen manifest exists for F18.
- Each descriptor's top-level `manifest_clause_ids` field is not described in the
  Catalog.
- It is unclear whether the regex is applied separately to response values.

**Interim (A-005, owner, Ayush pending).** A descriptor's `manifest_clause_ids` is that
fixture's manifest, and the check is exact membership.

**To settle.** Define the `manifest_clause_ids` field and the role of `clause_id_regex`
at parse time.

## PD-10 — Pointer sort: string tokens vs numeric index (I)

> [02 L137] "Sort by: (1) instance-token sequence, Unicode code-point order, shorter equal prefix first"

> [02 L137] "the lowest numeric `assumptions` index"

**Defect.** The same paragraph orders array indexes as strings for schema errors (`10`
before `2`), but numerically for clause-ID errors.

**Interim (A-006, owner, Ayush pending).** Both rules are kept as written.

**To settle.** Confirm the difference is intended, or make the two rules consistent.

## PD-11 — SOURCE_AST order across files (I)

> [30 L27] "For file-local stages, process each source file in this order"

> [02 L166] "(2) Source UTF-8/BOM/empty/syntax checks in file order `driver.py`, then `checker.py`."

> [02 L139] "The first applicable row after the exact evaluation order below controls."

**Defect.** A per-file order (all checks on `driver.py` first) and a row order (a syntax
error in either file beats an empty file) give different results when `driver.py` is
empty and `checker.py` has a syntax error.

**Interim (A-007).** The per-file order is used.

**To settle.** State which order governs across files.

## PD-12 — SOURCE_AST definitions and positions (U)

> [30 L27] "strict UTF-8 decode with BOM rejection"

> [02 L145] "Invalid UTF-8/BOM or syntax parse error"

> [02 L146] "Empty/whitespace-only source"

> [02 L127] "If `offset` is absent, null or less than 1, emit `column=1`"

**Defects.**
- **BOM.** Sources arrive as JSON strings, so a byte-level "BOM" has no defined meaning,
  and no position is given for a BOM rejection (A-008).
- **Invalid UTF-8.** Lone surrogates cannot be encoded, and no position is given for
  that failure (A-009).
- **Whitespace.** "Whitespace" is not defined (A-010).
- **Missing line.** No rule covers a missing or non-positive `lineno`, or a non-SyntaxError
  exception from `ast.parse`. The pack's only fallback is for the column (A-011).

**Interim.**
- A leading U+FEFF, or a source that cannot be encoded as UTF-8, is rejected at line 1,
  column 1.
- Whitespace is Python source whitespace.
- A missing line becomes line 1.

**To settle.** Define the BOM for string input, the whitespace set, and the position
fallbacks.

## PD-13 — IMPORT_POLICY order within a file; equal-key ties (I)

> [30 L27] "`ast.parse`; module-level AST policy; import/prohibited-name policy; compilation"

> [30 L27] "within a file, source nodes use ascending `(lineno, col_offset, end_lineno, end_col_offset)`"

> [02 L166] "complete that file's import, prohibited-name and module-body checks before advancing to the next file."

**Defect.** Three texts give three different orders for the categories inside one file:
- File 30's stage list (module-body first);
- the Protocol sentence (imports first);
- the node order (source position).

Under the node order, a bare module-level `eval` gives two findings with identical spans,
and the key does not decide between them.

**Interim.**
- A-013/A-014 (owner, Ayush pending): one source-order pass.
- The tie (Claude): File 30 L27's stage list.

**To settle.** State a single order, and a tie-break.

## PD-14 — Module-body statements not classified (U)

> [02 L135] "other executable statements/calls/expressions are `MODULE_EXECUTABLE`"

> [30 L29] "Literal-only expressions are `ast.Constant` values of type string, bytes, integer, float, complex, boolean or `None`"

**Defect.** Eleven statement forms are not classified, including:
- `x += 1`;
- attribute or subscript targets;
- `x: int`;
- `pass`;
- a later string expression;
- `...`;
- `-True` and `-(-1)`;
- annotations;
- `global`;
- module-level `return`.

**Interim (A-015).** Each form is classified as listed in ambiguities.md. Case 2 is an
owner decision (Ayush pending).

**To settle.** Give an exhaustive classification of statement kinds.

## PD-15 — Prohibited names, `random`, identifier scan (U)

> [30 L19] "AST `Name` nodes whose `id` is `__import__`, `eval`, `exec`, `compile` or `open` are rejected, regardless of call context."

> [30 L20] "Any direct attribute access on the module name `random` other than `random.Random` is rejected"

> [02 L133] "UTF-8 byte length of the source-line prefix"

**Defects.**
- Prohibited names bound by `def` or a parameter, and `__builtins__.open`, are not
  covered (A-016).
- It is unclear whether the `random` check is purely syntactic or follows bindings
  (A-017).
- On CPython 3.11, identifiers inside f-string replacement fields are part of a STRING
  token, so the token scan misses them (A-018).
- "Source line" is undefined, and on 3.11 `tokenize` and `ast.parse` disagree after a
  lone CR (A-019).

**Interim.** A-016 to A-019.

**To settle.** Each of the four points above.

## PD-16 — AST_SIGNATURE details (U)

> [02 L164] "parameter checks in the order `PARAMETER_NAMES`, `PARAMETER_KIND`, then `DEFAULT_OR_VARIADIC`"

> [02 L164] "count all same-name binding definitions at the required scope"

> [30 L52] "Its body may contain one docstring, literal-only class constants, and exactly one synchronous undecorated instance method named `step`"

> [02 L164] "use the expression node's own `(lineno, col_offset, end_lineno, end_col_offset)` as its source position"

**Defects.**
- Which parameters each check compares is not stated (A-020).
- "Binding" is undefined (A-021).
- No rank or reason covers other `Driver` class-body statements (A-022).
- A source position is given only for rank 7 (A-023).

**Interim.** A-020 to A-023.

**To settle.** Each of the four points above.

## PD-17 — Failures with no stage-map row or position (U)

> [02 L135] "`COMPILE_ERROR|file=<FILE>|line=<LINE>`"

> [02 L125] "`PHASE` is `factory` or `step`"

> [02 L153] "WATCHDOG_TIMEOUT|phase=driver_step"

> [02 L154] "SIMULATOR_ERROR|target=<RTL_OR_NULL>|class=<EXCEPTION_CLASS>"

> [02 L125] "`EXCEPTION_CLASS` is the simple Python exception class name matching `[A-Za-z_][A-Za-z0-9_]*`, otherwise the fixed fallback `Exception`"

**Defects.**
- No rule covers a compile error without a line (A-024).
- No row covers an exception while importing `driver.py` or `checker.py` (A-034).
- No row covers a driver import or factory call that never returns; the watchdog row
  covers `driver_step` only. No F18 factory seed is given (A-037).
- The class token is undefined when the simulator *process* fails or hangs, because no
  Python exception occurs in the simulation (A-039).

**Interim.**
- A compile error without a line uses line 1.
- An import exception uses phase `factory`.
- A factory that never returns is recorded as an evaluator ERROR; F18 uses seed 0.
- Simulator process failures use `CalledProcessError` or `TimeoutExpired`.

**To settle.** Rows or fallbacks for each case above.

## PD-18 — Post-construction checks (U)

> [02 L166] "Factory return type and runtime signatures are checked immediately after factory construction."

**Defect.** The pack gives no order among the return-type check and the two runtime
signatures. `check_trace` lives in the checker process, so "immediately after factory
construction" cannot apply to it as written.

**Interim (A-035).** Return type, then `create_driver`, then `Driver.step`. The
`check_trace` signature is checked in the checker process before its first call.

**To settle.** State the order and where `check_trace` is checked.

## PD-19 — Deterministic execution and hash randomization (U)

> [30 L99] "Import sandbox and deterministic execution"

**Defect.** The pack requires deterministic execution and compares paired runs, but
does not address Python's per-process hash randomization. An honest driver that iterates
over a set of strings would diverge between runs.

**Interim (A-036).** `PYTHONHASHSEED=0` in the sandbox.

**To settle.** State the requirement.

## PD-20 — Serializer emitted set; clause-ID packet checks (U)

> [02 L168] "The serializer accepts only a complete diagnostic emitted by the authoritative stage map."

> [31 L30] "Separately scan for malformed"

**Defects.**
- How "emitted by the authoritative stage map" is checked is not defined. M15 supplies an
  `allowed_diagnostics` set that the text does not mention (A-029).
- File 31 does not state the order between the malformed-token check and the set
  equality check (A-030).
- File 31 does not say whether a fixture that omits a regex uses the §8 value (A-030).

**Interim.**
- Grammar check, then membership when a set is supplied.
- Near-match before set equality.
- An omitted regex uses the §8 value.

**To settle.** The emitted-set rule, the check order and the defaults.

## PD-21 — Non-JSON number tokens (U)

> [30 L7] "The model must return one UTF-8 JSON object and no Markdown fences or surrounding prose."

**Defect.** File 30 §1 requires one JSON object, but does not address `NaN`, `Infinity`
and `-Infinity`. Neither "JSON" nor the number tokens are pinned to RFC 8259. Python's `json` module accepts these,
although RFC 8259 JSON does not.

**Interim (A-003, owner, Ayush pending).** They are rejected as `SCHEMA_REJECT|pointer=/`.

**To settle.** State it.

## PD-22 — Stale planning-pack version label (I)

> [30 L7] "schema version `1.0` is independent of planning-pack version `1.3.1`"

**Defect.** File 30 of the v1.3.6 pack names the planning-pack version as `1.3.1`. It
does not affect any outcome. This was found while preparing this document and is not
an entry in ambiguities.md.

**To settle.** Update the label, or make it version-neutral.

## PD-23 — Trace-row fields named only in prose (U)

> [02 L216] "For trace row `n`, record three separate fields:"

> [02 L223] "Record cycle index, reset, consumed inputs, post-edge outputs, next-input decision, driver completion state and run status."

> [02 L221] "the initial reset inputs are defined in the design pack"

> [30 L92] "`reset_release_cycle`: non-negative integer;"

> [02 L328] "A driver/simulator error or timeout produces a truncated trace"

**Defects.**
- Only three row fields have exact names. Cycle index, reset and run status have none.
- Run status has no value domain, and the pack does not say whether it is per row or
  per trace.
- The pack does not say whether trace rows begin at reset or at reset release.
- The numbering is not tied to `reset_release_cycle` or to the driver's `cycle_index`,
  which is 0 at release (File 30 L48).
- It is unclear whether `n` in the three field names is part of the key.

**Interim (A-040).**
- The three names are used verbatim.
- Rows begin at the first reset edge, with `cycle_index` = `n`.
- `reset` is a boolean.
- `run_status` is a per-trace `COMPLETE_TRACE` or `TRUNCATED_TRACE`.

**To settle.** In the trace schema (owner checklist item 11), name every field and its
domain, fix the row numbering and its relation to `reset_release_cycle`, and say whether
`n` is literal in the field names.

