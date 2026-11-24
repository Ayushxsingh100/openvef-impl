# Proposed corrections for a pack release v1.3.7

**DRAFT. Requires a new independent document audit.** Not approved, not frozen, not part of
any baseline. Drafted by Claude (Claude Opus 5.5, via Claude Code) at Krishika's
instruction, 24 Nov 2026 (UTC). For the owners and the independent document auditor.

- `baseline/` (v1.3.6) is not edited. Nothing here changes the implementation, the recorded
  results, or F18: **M27, M36, M42, M47, M48, M50, M54 and M58 stay NOT_IMPLEMENTED.**
- "Unblocks" means the text would then support an outcome. It is not a predicted PASS:
  each change also needs an implementation change, a new baseline and a new evidence run.
- **Conflict to weigh.** Claude wrote the implementation and drafted these corrections, so
  adopting them would make executable some fixtures it does not execute now. The scope
  and rule tokens in C2 to C4 are taken from the fixture descriptors, because the Protocol
  contains none. The auditor must decide from L181, L183 and L185 whether each token is
  the right rule, not merely whether it equals the descriptor.
- Quoted current text is checked verbatim by `tests/test_doc_quotes.py`;
  `tests/test_proposal_v137.py` checks the proposed tokens and the M27 descriptor.

| Change | Pack file | Defect | Unblocks |
|---|---|---|---|
| C1 | 02 L175 (error classes) | PD-02 (2) | M48, M50, M58 (each also needs C2) |
| C2 | 02 L176 (change classes and scope tokens) | PD-02 (1), (3) | M48, M50, M58 (with C1) |
| C3 | 02 L185 (halt-signature rule tokens) | PD-02 (3) | M54 |
| C4 | 36 L176 (control-vector comparison) | PD-03 | none alone; states the comparison M48, M50, M54, M58 rely on |
| C5 | 30 L83 (predicate form, order in check (a)) | PD-06, PD-25 | M27 (with C6) |
| C6 | 41 M27 descriptor, 36 L133 | PD-06, PD-25 | M27 (with C5), subject to the D-012 runner rule |
| C7 | 30 L7 (version label) | PD-22 | none |
| C8 | 10, 11, 22 (TechRxiv preprint) | PD-24 | none |
| C9 | 36 (parser-unit-vector contract) | PD-04 | M36, subject to the D-012 runner rule |
| C10 | 41 M41, M42, M47; 02 L185 | PD-01 | M42, M47 |

## C1 — Error classes of the revision vectors (PD-02)

**Current text**

> [02 L175] "The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; `M54` uses error class `HALT_SIGNATURE_SCHEMA` and diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`."

**Proposed replacement**

```text
Error classes of change-class control expectations are stated by rule, not by fixture: a control expectation whose diagnostic CODE is `EVALUATOR_REVISION_REQUIRED` has error class `EVALUATOR_REVISION_REQUIRED`; one whose CODE is `AUTHORING_REVISION_REQUIRED` has error class `AUTHORING_REVISION_REQUIRED`; and one whose CODE is `HALT_SIGNATURE_SCHEMA` has error class `HALT_SIGNATURE_SCHEMA`. This rule applies only to these three codes; it does not change the M41 error class `MID_RUN_REEVALUATION` or any stage-map row. The study-reset vector uses diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; the halt-signature vector uses diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

**Unblocks:** M48, M50 and M58, together with C2. M53 and M54 keep the same values.

## C2 — Change classes and scope tokens as rules (PD-02)

**Current text** (the start and end of the L176 entry; the five literals between them are
unchanged and not repeated)

> [02 L176] "- **Closed `required_action` literals used by lifecycle fixtures:** `M48` = `"

> [02 L176] "Each literal is a closed local control expectation, not a model-feedback diagnostic. `M48` re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. `M50` invalidates all designs and all arm × design slots and starts a new preregistered study. `M53` resets the preregistered design set and weights and requires fresh confirmatory slots. `M58` invalidates both arms for the affected design only when membership, estimand and weights remain unchanged."

**Proposed replacement** of the heading and of the five literal labels: each label becomes a
change class, and the literal text is unchanged.

```text
- **Closed `required_action` literals, by change class:**
```

| Current label | Proposed label |
|---|---|
| `M48` | `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` |
| `M50` | `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` |
| `M53` | `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` |
| `M54` | `HALT_SIGNATURE_COMPONENT_ENUMERATION` |
| `M58` | `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` |

**Proposed replacement** of the closing sentences:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. The change classes are closed and have these cases: `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` is the evaluator revision of §7b path (b); `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` is a shared-item revision; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` is a study reset; `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` is a design-specific revision while membership, estimand and weights remain unchanged; and `HALT_SIGNATURE_COMPONENT_ENUMERATION` is the halt-signature domain check.
Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = `shared_evaluator_component_all_designs_and_all_arm_x_design_slots; design_specific_component_affected_design_in_both_arms` (§7b: shared component, both designs and every slot; design-specific component, that design in both arms). For a shared-item revision, `affected_slots` = `all_designs_x_all_arms` (§7b: every scheduled slot across both designs and both arms). For a design-specific revision, `affected_scope` = `affected_design_in_both_arms` and `unaffected_design_scope` = `not_invalidated_when_membership_estimand_and_weights_are_unchanged`.
An evaluator revision re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. A shared-item revision invalidates all designs and all arm × design slots and starts a new preregistered study. A study reset resets the preregistered design set and weights and requires fresh confirmatory slots. A design-specific revision invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

**For the auditor:** the M48 token states the L183 rule; M50's states L181's "every scheduled
slot across both designs and both arms". M58's `unaffected_design_scope` has no single
sentence behind it: it combines L176's "affected design only when membership, estimand and
weights remain unchanged" with L181's contrast between shared and design-specific items.

**Unblocks:** M48, M50 and M58, together with C1. The descriptors need no change.

## C3 — Halt-signature rule tokens (PD-02)

**Current text**

> [02 L185] "`stable_error_class` is a simple exception class name matching `[A-Za-z_][A-Za-z0-9_]*` for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token."

**Proposed replacement**

```text
`stable_error_class` is a simple exception class name matching `[A-Za-z_][A-Za-z0-9_]*` for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes (rule token `stable_error_class_rule` = `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`); `stable_diagnostic_code` is exactly the corresponding `halt_code` token (rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

**Unblocks:** M54. Its other fields already have supporting text (A-033). This does not settle
PD-01; see C10.

## C4 — Which comparison applies to control vectors (PD-03)

**Current text**

> [36 L176] "The fixture runner verifies each descriptor's SHA-256 and byte length before loading its input, executes every mandatory case under pinned Python 3.11 and parser/schema versions, and compares actual disposition, stage, error class and exact diagnostic bytes with the expected object. Any unresolved expectation fails F18."

**Proposed replacement**

```text
The fixture runner verifies each descriptor's SHA-256 and byte length before loading its input, executes every mandatory case under pinned Python 3.11 and parser/schema versions, and compares the actual result with the expected object. When the expected object has exactly the keys `disposition`, `stage_id`, `error_class` and `diagnostic`, those four values are compared exactly. Any other expected object is a control-vector expectation: its whole object is compared exactly, key set included, and every property it names must be defined by a rule in the Protocol. Any unresolved expectation fails F18.
```

**Unblocks:** none alone. It states, as a rule, the whole-object comparison of A-032. A schema
for the existing M14, M17 and M41 property names is still missing, and PD-03 stays open on it.

## C5 — Legal-input predicate form and order in check (a) (PD-06, PD-25)

**Current text**

> [30 L83] "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification. Missing keys, extra keys, wrong width, non-string values, illegal symbols and illegal protocol combinations are distinct reason codes."

**Proposed replacement**

```text
(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification. The predicate is frozen as one Python 3.11 function of two dictionaries, `(vector, sampled)`: the driver vector, and the outputs sampled in the same row, each mapping a port name to its bit string. It returns the exact Boolean `True` for a legal vector and `False` otherwise. Any other outcome, including an exception, is an evaluator failure and is never an artifact verdict. Within check (a), missing keys are reported before extra keys. Checks (a) to (e) run in that order and the first failure is reported. A fixture that exercises check (e) must supply the input-port widths, the sampled outputs and the predicate in this form. Missing keys, extra keys, wrong width, non-string values, illegal symbols and illegal protocol combinations are distinct reason codes.
```

**For the auditor:** the two-argument scope and the `(vector, sampled)` form follow A-041 and
FIFO-042, which Krishika approved in the freeze. "Frozen top-level input-port set" versus a
harness-owned reset (A-042) is a separate question and is not changed here.

**Unblocks:** M27, together with C6. M26 is unaffected: it fails check (a).

## C6 — M27 descriptor (PD-06, PD-25)

**Current text**

> [41/M27.json L5] "\"description\": \"Driver vector violates a design-specific legal-input predicate\","

> [41/M27.json L11] "\"wr_en\": \"1\","

> [41/M27.json L12] "\"full\": \"1\""

> [41/M27.json L14] "\"legal_input_predicate\": \"wr_en must be 0 when full is 1\""

> [36 L133] "| M27 | missing-case | Driver vector violates a design-specific legal-input predicate | `REPAIR` — `DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE` | `41_F18_Fixture_Inputs/M27.json` |"

**Proposed replacement:** the whole descriptor, [fixtures/M27.json](fixtures/M27.json), and
in File 36 the row below.

```text
| M27 | missing-case | Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input predicate | `REPAIR` — `DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE` | `41_F18_Fixture_Inputs/M27.json` |
```

- The expected object is unchanged.
- The vector passes checks (a) to (d) under the supplied widths; the supplied predicate is
  FIFO-042, so `wr_en` = 1 with `rd_en` = 0 at sampled `full` = 1 is illegal.
- The old prose rule also forbade `wr_en` = 1 with `rd_en` = 1 at full, which FIFO-030 makes
  legal. The proposed fixture does not.
- The property names `input_port_widths` and `sampled_outputs` are new. Reusing the FIFO
  predicate ties this fixture to spec v0.2; the auditor may prefer a design-neutral one.

**Unblocks:** M27, together with C5.

## C7 — Stale planning-pack version label (PD-22)

**Current text**

> [30 L7] "schema version `1.0` is independent of planning-pack version `1.3.1`"

**Proposed replacement**

```text
schema version `1.0` is independent of the planning-pack version
```

**Unblocks:** none.

## C8 — Status of the TechRxiv preprint (PD-24)

File 10's header already says it is a historical draft and that the provenance log controls
where access claims differ. The log (File 22) records abstract-only access. So the pack
settles which record wins, and C8 removes the contradictory sentences. **The preprint
has not been retrieved**, and nothing below asserts what it contains.

| File | Current text | Proposed replacement |
|---|---|---|
| 10 L174 | first quotation | "**Reported proof of concept (unverified).** An earlier draft attributed a synchronous-FIFO case and numerical results to this preprint. Those details are not verified from its text (abstract-only access, File 22) and are not relied upon. The preprint is not peer reviewed." |
| 10 L308 | second quotation | "- The TechRxiv preprint is an unreviewed proof of concept; its numerical results and designs are not verified from its text (File 22) and are not relied upon." |
| 10 L353 | third quotation | "whether the TechRxiv checker-gap preprint also evaluates a synchronous FIFO is not verified (File 22)" |
| 10 L383 | fourth quotation | "Abstract only, per File 22; the earlier statement that extracted full text was read is superseded" and, in the confidence cell, "Low for method and limitations until the exact PDF is retrieved and inspected; unreviewed preprint; disclose as prior art" |
| 11 L37 | fifth quotation | "- TechRxiv checker-gap paper: abstract-only access is recorded (File 22); full-text and injection-method claims are not verified." |
| 22 L16 | sixth quotation | append: "A retrieval attempt on 24 November 2026 returned HTTP 403 from techrxiv.org; the PDF remains unretrieved." |

> [10 L174] "**Reported proof of concept.** It evaluates a round-robin arbiter and synchronous FIFO (150–350 LOC), with 12 total test cases. It reports 10/12 tests detecting targeted gaps, zero false positives on the golden design, and an approximately 80-second detection cycle. The paper itself says this sample is too small for strong statistical confidence and treats it as a feasibility demonstration (Section VII-D). It also identifies one LLM model, manual mutation injection, small single-module designs, and UVM-specific scope as limitations (Section VII-E). The preprint is not peer reviewed."

> [10 L308] "- The TechRxiv preprint reports 10/12 targeted gap detections on two small UVM IPs; it is a proof of concept, not a broad benchmark."

> [10 L353] "the TechRxiv checker-gap preprint also evaluates a synchronous FIFO"

> [10 L383] "Extracted TechRxiv PDF text, including Definitions and experimental limitations (Sections II-A, III, IV–V, VII-D/VII-E); page-image screenshot fetch failed (502) | Moderate for method and declared limitations; checker-dependent definition of output observability; unreviewed preprint, two designs, 12 cases; treat cautiously but disclose as prior art"

> [11 L37] "- TechRxiv checker-gap paper: full extracted text was read; PDF page images were not inspected; the paper's automated/manual injection descriptions conflict."

> [22 L16] "- TechRxiv: the independent Step 3 audit reports abstract-only access. Do not rely on detailed full-text claims from the earlier draft until the exact source PDF is retrieved, versioned and inspected. The reported automated/manual injection discrepancy remains unresolved."

Charter L99 and File 12 L85 already agree with this and need no change. If the owners
retrieve the PDF first, replace C8 with what it says, citing its SHA-256. Other File 10
passages about this preprint (L163–L180) rest on the same access claim and should be
re-read in the audit. The 403 was observed in a Claude Code session and is logged as such.

**Unblocks:** none. The overlap disclosure note should be re-checked if C8 is adopted.

## C9 — Parser-unit-vector input contract (PD-04; D-012 request)

**Current text**

> [36 L27] "Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately grammar-exempt; they test local utilities/policies, not model feedback."

> [36 L15] "`CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector; it does not represent an artifact feedback event."

> [02 L177] "A `CONTROL_EXPECTATION` fixture exercises a serializer, protocol or lifecycle rule; its stage and expected diagnostic are test labels, not an artifact feedback event."

> [41/M36.json L6] "\"fixture_class\": \"parser_unit_vector\","

**Proposed replacement** of the File 36 unit-vector sentence (the rest of requirement 6 is
unchanged):

```text
Serializer, lifecycle and parser unit vectors are marked by `fixture_class` (`serializer_primitive_unit_vector_grammar_exempt`, `lifecycle_unit_vector`, `parser_unit_vector`) and are deliberately grammar-exempt; they test local utilities/policies, not model feedback. A `parser_unit_vector` input has exactly the keys `source_file` and `syntax_error`. `source_file` is `driver.py` or `checker.py`. `syntax_error` has the key `lineno`, a positive integer, and may have the key `offset`, an integer or null. The vector applies the Protocol §3.4 `SOURCE_SYNTAX_REJECT` column rule to that position. Its result has stage `SOURCE_AST`, error class `SOURCE_SYNTAX_REJECT`, the diagnostic given by the rule, and disposition `CONTROL_EXPECTATION`.
```

**Proposed replacement** of the File 36 disposition text, aligned with Protocol L177:

```text
`CONTROL_EXPECTATION`: a serializer, parser, protocol or lifecycle test vector; it does not represent an artifact feedback event.
```

**For the auditor:** this is a request that the pack define the contract. The contract matches
the only existing vector, so the auditor should check that it follows from the column rule.
A second vector of this class (for example `offset` absent, or `offset` = 0) would exercise
the contract properly and is recommended; it also matters for the rule below.

**Unblocks:** M36, subject to "The D-012 runner rule" below.

## C10 — Halt signatures outside the L185 domains (PD-01; D-012 request)

**Current text**

> [02 L185] "`evaluator_component` is `SIMULATOR`, `REPLAY_VERIFIER`, `RECORDER`, `TRACE_ALIGNMENT_CHECKER`, `TRACE_SERIALIZER` or `RTL_NULL_COMPARATOR`"

> [41/M41.json L33] "\"evaluator_component\": \"simulator\","

> [41/M42.json L16] "\"evaluator_component\": \"simulator\","

> [41/M42.json L23] "\"evaluator_component\": \"simulator\","

> [41/M47.json L16] "\"evaluator_component\": \"simulator\","

> [41/M47.json L23] "\"evaluator_component\": \"recorder\","

> [41/M47.json L24] "\"stable_error_class\": \"RecorderFault\","

**Proposed replacement:** in the descriptors, the L185 values. L185 is unchanged.

| Descriptor | Field | Current | Proposed |
|---|---|---|---|
| M41 `halt_signature` | `evaluator_component` | `simulator` | `SIMULATOR` |
| M42 `first_` and `second_halt_signature` | `evaluator_component` | `simulator` | `SIMULATOR` |
| M47 `first_halt_signature` | `evaluator_component` | `simulator` | `SIMULATOR` |
| M47 `second_halt_signature` | `evaluator_component` | `recorder` | `RECORDER` |
| M47 `second_halt_signature` | `stable_error_class` | `RecorderFault` | `NONE` |

And one sentence added at the end of the L185 domain list:

```text
A supplied halt signature with any component outside these domains is an evaluator input error; it is never compared for recurrence.
```

Expected objects do not change. Under L185, M42's signatures stay identical and M47's stay
different.

**Unblocks:** M42 and M47. M41 has no adapter for a different reason (see below).

## The D-012 runner rule

Under D-012 this implementation has no adapter for an input shape that only one fixture uses,
and a test enforces it. So **C5 and C6 (M27) and C9 (M36) do not by themselves let those
fixtures run**: each shape would still belong to one fixture. Either the pack adds a second
vector of the same shape, or it defines the input contracts (PD-07) and the owners then
amend the runner rule. The same holds for M13, M14, M15, M17, M18, M19, M25, M26, M28, M37, M41, P17, R07: their rules are stated in the pack, but
their input shapes are not. This proposal does not draft those contracts.

## Consequences of adopting any of these

1. A new pack release with its own ZIP hash, change log, `27_SHA256SUMS.txt` and status files.
   C6 and C10 also change descriptor hashes and lengths, `fixture-index.json`, and its hash.
2. **A new independent document audit**, then owner approval (Ayush's ratification included
   in the D-008 entry).
3. A new baseline directory and pinned index hash in this repository, at owner instruction.
   v1.3.6 stays as it is.
4. Implementation changes: field sources in `LIFECYCLE_CASES` (C1–C3), and a generic
   vector-fixture adapter keyed on input shape (C5, C6), without fixture-specific code.
5. A new pinned evidence run. Runs against v1.3.6 remain v1.3.6 evidence.

Other recorded defects (PD-01 to PD-25 not listed above) are not covered by this proposal.
