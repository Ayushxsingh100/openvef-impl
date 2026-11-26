# OpenVEF Planning v1.3.7 CANDIDATE — corrections C1–C10 (D-024 Phase A)

**v1.3.7 CANDIDATE, not audited.** Owner decision D-024 (Krishika, on a Claude (claude.ai) plan). Written by
Claude (Claude Opus 5.5, via Claude Code), the implementation author. Not approved, not frozen, not released;
it needs an independent document audit. v1.3.6 (`baseline/`) is unchanged and remains the default.

- **What it is:** the rationale for `proposals/v1.3.7/pack/`, a full copy of v1.3.6 with only C1–C10 applied.
  The edits themselves, line by line, are in `pack/CHANGELOG-v1.3.7-candidate.md`; the build is
  `build_candidate.py`, checked by `tests/test_v137_candidate_pack.py`.
- **Order (the point of Phase A):** this file, the pack and its tests are committed **before any implementation
  change for v1.3.7**. A correction found wrong while implementing is amended in a later, numbered commit, not
  edited here silently.
- **Scope chosen by Krishika:** C1–C10 only. Fixtures no correction covers are flagged, not corrected.
- **Every edit stays inside one line**, so no line moves and every line citation means the same line in both packs.
- Quoted v1.3.6 text is checked verbatim by `tests/test_doc_quotes.py`.

**Conflict to weigh.** The corrections were drafted on 24 Nov 2026 by the implementation author, after the
v1.3.6 implementation existed, and several make executable fixtures the code does not execute now. Each
correction below states its fit with the current code. **No correction was chosen because it suits the current
code**; where it agrees with the code, that agreement is stated, and the argument rests on the pack text cited.
Where a token's exact spelling exists only in a fixture descriptor, that is said too.

## 1. The 17 NOT_IMPLEMENTED fixtures → pack defects → corrections

v1.3.6 evidence: `run-20261126T144718Z` (17 NOT_IMPLEMENTED). PD numbers are from `docs/pack-defects.md`.

| Fixture | What blocks it in v1.3.6 | PD | Correction | Covered? |
|---|---|---|---|---|
| M27 | prose predicate; no port widths; `full` (an output) in the driven vector | PD-06, PD-25 | C5, C6 | **Yes** |
| M36 | `parser_unit_vector` undefined; no input contract | PD-04, PD-07 | C9 | **Yes** |
| M48 | error class unstated; `rerun_scope_rule` token only in the descriptor; `change_class` input undefined | PD-02, PD-03, PD-07 | C1, C2, C4 | **Yes** |
| M50 | error class unstated; `affected_slots` token only in the descriptor | PD-02, PD-03, PD-07 | C1, C2, C4 | **Yes** |
| M53 | `change_class` input undefined (its values were stated) | PD-02, PD-03, PD-07 | C1, C2, C4 | **Yes** |
| M54 | `stable_*_rule` tokens only in the descriptor | PD-02, PD-03, PD-07 | C1, C2, C3, C4 | **Yes** |
| M58 | error class unstated; `affected_scope`, `unaffected_design_scope` only in the descriptor | PD-02, PD-03, PD-07 | C1, C2, C4 | **Yes** |
| M42 | signature components outside the L185 domains; no error class for `DESIGN_HALT_REPEATED` | PD-01, PD-26 | C10 (PD-01 only) | **No — PD-26 open** |
| M47 | as M42 | PD-01, PD-26 | C10 (PD-01 only) | **No — PD-26 open** |
| M41 | lower-case component; no input contract or output schema for its lifecycle input | PD-01, PD-03, PD-07 | C10 (PD-01 only), C4 (comparison only) | **No — PD-03/PD-07 open** |
| M15 | no error class for `FEEDBACK_SERIALIZER_REJECT`; `allowed_diagnostics` not in the text | PD-20, PD-26, PD-07 | none | **No** |
| M14 | no output schema for its control-vector properties; no input contract | PD-03, PD-07 | C4 (comparison only) | **No** |
| M17 | as M14 | PD-03, PD-07 | C4 (comparison only) | **No** |
| M13 | no input contract for a lifecycle `event` input | PD-07 | none | **No** |
| M37 | no input contract for `runtime_pair` | PD-07 | none | **No** |
| P17 | no input contract for `port_manifest` + `response_object` | PD-07 | none | **No** |
| R07 | no input contract for `design_preflight` | PD-07 | none | **No** |

**Flagged: 10 of the 17 are not covered by C1–C10** (M13, M14, M15, M17, M37, M41, M42, M47, P17, R07). They stay
NOT_IMPLEMENTED on the candidate pack. Covering them needs new corrections (PD-03 output schemas, PD-07 input
contracts, PD-20, PD-26), most of which would have to be derived from the descriptors themselves; Krishika chose
not to draft them in this phase.

## 2. Differences from the 24 Nov 2026 draft (`PROPOSED-CORRECTIONS-DRAFT.md`)

The draft is kept unchanged as history. Applying it exposed four points; each is decided here from the pack text:
1. **C9 also amends Protocol L177.** The draft aligned only File 36 L15, so the two `CONTROL_EXPECTATION`
   definitions PD-04 names would still differ (L177 lacks "parser"). Both now read "serializer, parser, protocol
   or lifecycle".
2. **C5 names the input properties** of a check-(e) fixture. The draft required a fixture to "supply the
   input-port widths, the sampled outputs and the predicate" without naming them, so an input contract would
   still have come from the descriptor (D-013). The names are the ones the draft's own M27 already used.
3. **C8 no longer appends to File 22 L16.** The draft added "A retrieval attempt on 24 November 2026 returned HTTP
   403". PD-24 is the File 10 vs File 22 inconsistency; File 22 is already right. The sentence would add an
   observation made in a Claude Code session to the pack's provenance log, which nothing else records.
4. **C10's sentence and C3's tokens share L185**, and **every changed file carries the candidate label** (an
   appended Markdown trailer; `fixture_version` = `1.3.7-candidate, not audited` instead of `1.3.7-DRAFT`).

## 3. The corrections

### C1 — Error classes of the change-class vectors (PD-02 (2))

**Conflicting v1.3.6 text.** Error classes are stated for two revision vectors, by fixture ID; the other three
expect one the Protocol never states, and "error class = diagnostic CODE" is not a rule the Protocol keeps:

> [02 L175] "The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED`"

> [02 L175] "`M54` uses error class `HALT_SIGNATURE_SCHEMA`"

> [02 L175] "`RERUN_ALL_SCHEDULED_SLOTS_WITH_SAME_FROZEN_ARTIFACTS` (error class `MID_RUN_REEVALUATION`)"

> [02 L154] "`SIMULATOR_ERROR|target=<RTL_OR_NULL>|class=<EXCEPTION_CLASS>`"

> [41/M48.json L16] "\"error_class\": \"EVALUATOR_REVISION_REQUIRED\","

**Chosen fix (CHANGELOG C1).** A rule limited to three CODEs: `EVALUATOR_REVISION_REQUIRED`,
`AUTHORING_REVISION_REQUIRED` and `HALT_SIGNATURE_SCHEMA` each have the error class of the same name. It
says explicitly that M41 and the stage map are unchanged, and the fixture labels are removed.

**Why.** Every error class L175 does state for these codes has the CODE's own name (the M53 and M54 sentences).
The two counter-examples are other codes: M41's diagnostic is not a CODE of this family, and L154 is a stage-map
row. A rule restricted to these three codes therefore states what L175 already does in its two examples, extends
it to the same codes in M48, M50 and M58, and contradicts nothing.

**Alternatives rejected.**
- "Error class = CODE" for every control expectation: contradicted by L175 (M41) and L154.
- More per-fixture sentences ("`M48` uses error class …"): repeats the PD-02 (1) defect (rules tied to fixture IDs).
- Changing the descriptors' expected error classes: changes the test to fit, and no text argues for other values.
- Leaving it unstated: M48, M50 and M58 stay unresolvable, and File 36 L176 makes an unresolved expectation fail F18.

**Fit with the current code.** `src/openvef/ledger.py` `LIFECYCLE_CASES` marks these three error classes
UNSUPPORTED today, so C1 changes what the code can support. The values equal the descriptors' expected values;
that is the purpose of a correction that settles an under-specification, and the argument above does not rely on it.

### C2 — Change classes and scope tokens as rules (PD-02 (1), (3); PD-07 for the `change_class` input)

**Conflicting v1.3.6 text.** The literals are keyed by fixture ID, the `change_class` input labels exist only in
descriptors, and four scope tokens exist only as expected values:

> [02 L176] "- **Closed `required_action` literals used by lifecycle fixtures:** `M48` = `"

> [02 L176] "`M48` re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls."

> [41/M48.json L23] "\"rerun_scope_rule\": \"shared_evaluator_component_all_designs_and_all_arm_x_design_slots; design_specific_component_affected_design_in_both_arms\""

> [41/M50.json L21] "\"affected_slots\": \"all_designs_x_all_arms\","

> [41/M58.json L18] "\"affected_scope\": \"affected_design_in_both_arms\","

> [41/M58.json L19] "\"unaffected_design_scope\": \"not_invalidated_when_membership_estimand_and_weights_are_unchanged\","

The meanings are in §7b:

> [02 L183] "If the revised evaluator component is shared across FIFO and UART, the affected scope is both designs and every arm × design slot; if it is design-specific, the affected scope is that design in both arms."

> [02 L181] "halt the entire study and invalidate every scheduled slot across both designs and both arms"

> [02 L181] "If a design-specific author-visible item changes, halt and invalidate every slot for that design in both arms."

**Chosen fix (CHANGELOG C2).** Each literal is keyed by a closed change class instead of a fixture ID (the literal
text is unchanged); the five change classes are defined as cases of §7b; the four scope tokens are stated as
closed tokens with the §7b sentence each one encodes; the closing sentences describe cases, not fixtures.

**Why.** L176 already says each literal is "a closed local control expectation", and its closing sentences
already describe each literal by the case it belongs to (re-evaluation, study invalidation, study reset,
design-specific invalidation). Keying by case is what those sentences describe. The tokens are spelled exactly
as the pack's own expected objects spell them, because the token is the expected output; each is placed next to
the §7b sentence whose meaning it carries.

**Alternatives rejected.**
- Removing the tokens from the descriptors' expected objects: changes the tests to fit.
- Defining scope as a structured value (lists of designs and arms) instead of tokens: no pack text uses such a
  structure, and it would also require changing the expected objects.
- Keeping fixture IDs and adding the change-class name beside each: leaves PD-02 (1) in place.

**Fit with the current code.** The token *strings* are copied from the descriptors, as the draft disclosed; the
Protocol contains none. `LIFECYCLE_CASES` already keys by these change-class labels and cites L176 literals
"labelled M48" and so on; under C2 those citations become "keyed by change class". The **M58
`unaffected_design_scope` token has no single sentence behind it**: it combines L176's "only when membership,
estimand and weights remain unchanged" with L181's contrast between shared and design-specific items.

### C3 — Halt-signature rule tokens (PD-02 (3))

**Conflicting v1.3.6 text.**

> [02 L185] "`stable_error_class` is a simple exception class name matching `[A-Za-z_][A-Za-z0-9_]*` for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token."

> [41/M54.json L36] "\"stable_error_class_rule\": \"simple_exception_class_for_SIMULATOR_ERROR_else_NONE\","

> [41/M54.json L37] "\"stable_diagnostic_code_rule\": \"exact_halt_code_token\""

**Chosen fix (CHANGELOG C3).** Each of the two rules carries its token in parentheses; the rules are unchanged.

**Why.** The tokens name exactly the two rules already stated in the same sentence; nothing else in the pack
describes them.

**Alternatives rejected.** Removing the two properties from M54 (changes the test); a structured rule language
(no pack text supports one).

**Fit with the current code.** `LIFECYCLE_CASES` marks both UNSUPPORTED today. Token strings copied from M54.

### C4 — Which comparison applies to control vectors (PD-03)

**Conflicting v1.3.6 text.**

> [36 L176] "compares actual disposition, stage, error class and exact diagnostic bytes with the expected object."

> [36 L23] "a single exact expected disposition/stage/error/diagnostic (or exact control-vector expectation)"

**Chosen fix (CHANGELOG C4).** A four-key expected object is compared on those four values; any other expected
object is a control-vector expectation, compared whole (key set included), and every property it names must be
defined by a rule in the Protocol.

**Why.** L23 already admits "exact control-vector expectation"; L176 only describes the four-field case. The
correction states both cases, and "exact" in L23 is read as the whole object, key set included.

**Alternatives rejected.**
- Comparing only the four fields of a control vector: the extra properties would go unchecked, so L23's "exact"
  would mean nothing, and M14 and M17 have no `diagnostic` key at all.
- Comparing only the keys an implementation computes: lets an implementation pass by omitting properties.

**Fit with the current code.** It states as a rule what A-032 (Claude-decided, approved under D-009) already does.
It does **not** give the output schema PD-03 asks for: the property names of M14, M17 and M41 stay undefined,
and so do the boolean property names of the change-class vectors (`f16_required` and the like), whose values
follow from §7b sentences but whose names come from the descriptors.

### C5 — Legal-input predicate form, check order, check-(e) fixture inputs (PD-06, PD-25)

**Conflicting v1.3.6 text.**

> [30 L83] "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification."

> [30 L83] "Missing keys, extra keys, wrong width, non-string values, illegal symbols and illegal protocol combinations are distinct reason codes."

> [41/M27.json L14] "\"legal_input_predicate\": \"wr_en must be 0 when full is 1\""

**Chosen fix (CHANGELOG C5).** The predicate is one Python 3.11 function of `(vector, sampled)` returning exactly
`True` or `False`; anything else is an evaluator failure, never an artifact verdict. Within (a), missing keys
before extra keys; (a)–(e) in order, first failure reported. A check-(e) fixture supplies `driver_return`,
`input_port_widths`, `sampled_outputs` and `legal_input_predicate` (`language`, `function`, `source`).

**Why.**
- **Python:** artifacts, harness and pinned interpreter are Python 3.11 (File 30); a predicate in that language
  needs no second language or interpreter.
- **Two arguments:** "illegal protocol combinations" (L83) depend on state, and the only state a driver vector
  meets is the outputs sampled in the same row.
- **Evaluator failure:** a predicate that raises is a defect in frozen evaluator material, not in the artifact.
- **Order:** (a)–(e) are lettered and "verifies before driving" lists them in order, and the Protocol's reason
  enumeration lists `MISSING_KEYS` before `EXTRA_KEYS`:

> [02 L125] "`DRIVER_VECTOR_INVALID.reason` is one of `RETURN_TYPE`, `MISSING_KEYS`, `EXTRA_KEYS`, `NON_STRING_VALUE`, `WRONG_WIDTH`, `ILLEGAL_SYMBOL`, or `ILLEGAL_PROTOCOL_STATE`."

**Alternatives rejected.**
- A declarative predicate language (truth tables, boolean expressions): no pack text defines one, and it
  would need its own interpreter.
- Reporting all failures: L83 gives one reason per invalid vector.
- Extra keys before missing keys: no text supports it; the enumeration order is the only textual order.
- One-argument predicate (vector only): cannot express any state-dependent rule such as "no write while full".

**Fit with the current code.** The two-argument form and the order equal A-041/FIFO-042 (approved by Krishika in
the freeze) and A-027 (Claude-decided, approved under D-009), which `src/openvef/stage_map.py` `validate_vector`
implements. The property names were first used in the draft's own M27, written by the implementation author.

### C6 — M27 descriptor (PD-06, PD-25)

**Amended by A1 (section 5, D-025):** the FIFO-042 predicate below is replaced by the v1.3.6 descriptor's own rule.

**Conflicting v1.3.6 text.**

> [41/M27.json L11] "\"wr_en\": \"1\","

> [41/M27.json L12] "\"full\": \"1\""

> [30 L83] "(a) its key set equals the frozen top-level input-port set exactly"

> [36 L133] "| M27 | missing-case | Driver vector violates a design-specific legal-input predicate |"

**Chosen fix (CHANGELOG C6).** M27 is replaced: a FIFO vector that passes (a)–(d) under supplied widths, the
outputs sampled in that row (`full` = 1), and FIFO-042 in the C5 form. The expected object is unchanged. The
File 36 row says what the vector exercises.

**Why.** As written M27 cannot reach (e): no port set or widths, and `full` is an output, so (a) fails first
(PD-25). The expected object is the fixture's intent, so the input is corrected to reach it. The predicate is
FIFO-042 from the frozen FIFO specification, which also keeps `wr_en` = 1 with `rd_en` = 1 at full legal
(FIFO-030); the v1.3.6 prose forbids it, which the frozen spec does not.

**Alternatives rejected.**
- Keeping the v1.3.6 prose rule in executable form: contradicts FIFO-030.
- A design-neutral toy predicate: possible, and arguably cleaner, but it would be a new rule with no pack or
  spec text behind it; the auditor may prefer it.
- Changing the expected object to `EXTRA_KEYS`: changes the test to fit the defect.

**Fit with the current code.** The FIFO predicate is DRAFT material Claude wrote under D-005 and the owners froze.
The fixture ties M27 to spec v0.2.

### C7 — Stale version label (PD-22)

> [30 L7] "schema version `1.0` is independent of planning-pack version `1.3.1`"

**Fix.** "is independent of the planning-pack version". **Why:** the pack is v1.3.6; any number here goes stale
again. **Rejected:** writing `1.3.6` or `1.3.7` (stale at the next release). **Code:** no effect. No fixture.

### C8 — TechRxiv preprint status (PD-24)

> [10 L174] "**Reported proof of concept.** It evaluates a round-robin arbiter and synchronous FIFO (150–350 LOC), with 12 total test cases."

> [10 L383] "Extracted TechRxiv PDF text, including Definitions and experimental limitations"

> [11 L37] "- TechRxiv checker-gap paper: full extracted text was read; PDF page images were not inspected; the paper's automated/manual injection descriptions conflict."

> [22 L16] "- TechRxiv: the independent Step 3 audit reports abstract-only access. Do not rely on detailed full-text claims from the earlier draft until the exact source PDF is retrieved, versioned and inspected."

**Fix (CHANGELOG C8).** Files 10 (L174, L308, L353, L383) and 11 (L37) stop asserting the preprint's contents
and say they are unverified (File 22). File 22 is unchanged.

**Why.** File 10's own header defers to the provenance log where access claims differ, and File 22 records
abstract-only access; the pack settles which wins.

**Rejected:** asserting the contents (not verified); deleting the passages (loses the record that a claim was
made); appending the 403 observation to File 22 (see section 2). **Code:** no effect. No fixture.
**Stale reference:** File 22 L8–L12 cite the v1.3.6 SHA-256 of File 10; left as written (CHANGELOG).

### C9 — `parser_unit_vector` contract (PD-04)

> [41/M36.json L6] "\"fixture_class\": \"parser_unit_vector\","

> [36 L27] "Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately grammar-exempt"

> [36 L15] "- `CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector;"

> [02 L177] "A `CONTROL_EXPECTATION` fixture exercises a serializer, protocol or lifecycle rule"

**Chosen fix (CHANGELOG C9).** File 36 L27 defines the class, its input keys (`source_file`; `syntax_error` with
`lineno` and optional `offset`), the rule it applies (the Protocol §3.4 column rule) and its result. File 36 L15
and Protocol L177 both read "serializer, parser, protocol or lifecycle".

**Why.** The column rule already exists:

> [02 L127] "If `offset` is absent, null or less than 1, emit `column=1`; otherwise emit the positive one-based source-character column reported by CPython."

The contract names exactly the inputs that rule reads (file, line, offset). The disposition `CONTROL_EXPECTATION`
follows from L177: the vector tests a rule, not an artifact. L177 is the Protocol and controls the definition;
File 36 is aligned to it, adding "parser" to both.

**Alternatives rejected.** Treating M36 as a source file to parse (the input has no source); keeping "policy" in
File 36 (it then still differs from the Protocol); a disposition by `fixture_class` alone (M42/M47 are lifecycle
vectors with a non-control disposition, PD-04).

**Fit with the current code.** `src/openvef/source_ast.py` `syntax_reject` implements the L127 column rule
already; the contract matches the only existing vector, M36. A second vector of this class would test it properly.

### C10 — Halt signatures outside the L185 domains (PD-01)

> [02 L185] "`evaluator_component` is `SIMULATOR`, `REPLAY_VERIFIER`, `RECORDER`, `TRACE_ALIGNMENT_CHECKER`, `TRACE_SERIALIZER` or `RTL_NULL_COMPARATOR`"

> [41/M42.json L16] "\"evaluator_component\": \"simulator\","

> [41/M47.json L23] "\"evaluator_component\": \"recorder\","

> [41/M47.json L24] "\"stable_error_class\": \"RecorderFault\","

**Chosen fix (CHANGELOG C10).** The descriptors use the L185 values (`SIMULATOR`, `RECORDER`, and `NONE` for the
trace-integrity signature's error class), and L185 adds: a supplied signature with any out-of-domain component is
an evaluator input error, never compared for recurrence. Expected objects are unchanged.

**Why.** L185 gives "exact domains"; the descriptors are the outliers, and their expected outcomes do not depend
on the spelling (M42's signatures stay identical, M47's stay different).

**Alternatives rejected.** Case-insensitive domains (L185 says "exact"); accepting any string (domains would be
void); keeping the descriptors and defining only the error outcome (M42 and M47 would then expect the wrong result).

**Fit with the current code.** `HaltSignature.given()` already rejects out-of-domain values (D-012, after audit
#1 A8-1). **M42 and M47 still need an error class for `DESIGN_HALT_REPEATED` (PD-26), which no correction
supplies, so they stay NOT_IMPLEMENTED.** M41 also needs an input contract (PD-07).

## 4. What a document auditor is likely to attack

1. **Author conflict:** the implementation author drafted every correction, after writing the code.
2. **Descriptor-derived tokens (C2, C3):** six token strings exist only because the descriptors contain them.
3. **C4 does not supply a schema;** boolean property names of the change-class vectors come from descriptors.
4. **C6 rewrites a fixture's input**, using a predicate the author also drafted (FIFO-042).
5. **C5 chooses Python** as the predicate language; another reading could want a declarative form.
6. **Stale references** left in place: File 22's File 10 hash, file names and headers still saying v1.3.6,
   `03_Change_Log` and `32_Status_and_Gates`; the `archive_*` entries of `27_SHA256SUMS.txt` are not in the copy.
7. **Ten fixtures are not covered,** so a v1.3.7 F18 cannot pass on these corrections alone.

## 5. Amendments (numbered; each in its own commit)

### A1 — C6: a design-neutral predicate (D-025 item 2)

**What changes.** M27's input becomes `driver_return` = `{"wr_en": "1"}`, `input_port_widths` = `{"wr_en": 1}`,
`sampled_outputs` = `{"full": "1"}`, and the predicate `not (sampled["full"] == "1" and vector["wr_en"] == "1")`. The
expected object, the File 36 row and C5 are unchanged.

**From the pack text.** The pack already states the rule M27 is meant to exercise:

> [41/M27.json L14] "\"legal_input_predicate\": \"wr_en must be 0 when full is 1\""

Its defects (PD-25) were that `full` sits in the driven vector and that no port set or widths are given:

> [41/M27.json L12] "\"full\": \"1\""

> [30 L83] "(a) its key set equals the frozen top-level input-port set exactly"

The rule names `full` only as a condition ("when full is 1"), so it is a sampled value, and `wr_en` is the only driven
port it mentions. Executing exactly that rule over a port set of `wr_en` alone, with `full` sampled, keeps the pack's
own predicate and fixes only what PD-25 names. A fixture executes "under pinned Python 3.11 and parser/schema
versions" (36 L176): nothing in that list is a design specification, so a fixture should not need one.

**Rejected.**
- **FIFO-042** (the D-024 choice): it comes from the owner-frozen FIFO specification, outside the pack, written by
  the implementation author, and ties F18 to one design's materials.
- **Abstract port names** (`a`, `b`): further from the pack's own wording than needed.
- **Adding `rd_en`**: brings back the question PD-25 raised (is a write with a read at full legal?), which the pack
  answers nowhere; FIFO-030 answers it only for the FIFO.

**Withdrawn.** C6's rejection "Keeping the v1.3.6 prose rule in executable form: contradicts FIFO-030" held only for a
port set that includes `rd_en`; with `wr_en` alone there is no such case.

**Fit with the current code.** None needed: the C5 adapter is general. The amended M27 passes (a)–(d) and fails (e);
`{"wr_en": "0"}` is legal (tests/test_v137_candidate_pack.py).

