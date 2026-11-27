# **OpenVEF — Independent Document Audit #1**

**Audit target:** Planning Pack v1.3.7 CANDIDATE\
**Baseline:** v1.3.6\
**Operator:** Krishika\
**Author of corrections:** Claude (Anthropic), via Claude Code\
**Auditor role:** Independent document auditor

## **1. Bundle identification**

SHA-256 COMPUTED

**Uploaded ZIP SHA-256:**

```
c4caff409692797b4292a1c6851c79a722d1c60cbf4371e5611f5ef4f0a4cbd7
```

- Hash computation: **RUN**
- ZIP opened and archive entries enumerated: **RUN**
- Bundle contains the v1.3.6 baseline, v1.3.7 proposal, and audit instructions: **RUN**

This hash will be reproduced exactly whenever the bundle hash is stated in this report.

## **2. Integrity verification**

PASS — MANIFEST.sha256

| Check                        | Method                                   | Result                  |
| ---------------------------- | ---------------------------------------- | ----------------------- |
| Bundle manifest              | Computed SHA-256 for every listed file   | PASS: 417/417           |
| Missing bundle entries       | Checked filesystem paths                 | None                    |
| Candidate SHA256SUMS         | Verified every listed candidate file     | PASS: 205/205           |
| Unlisted candidate files     | Compared manifest with actual directory  | None                    |
| Baseline SHA256SUMS          | Verified extracted baseline entries      | PASS: 202/202           |
| Baseline archive entries     | Checked the documented archive exception | 61 absent, as disclosed |
| Candidate rebuild            | Executed `build_candidate.py`            | PASS                    |
| Rebuilt candidate comparison | Compared every file byte-for-byte        | PASS: 206/206           |
| Candidate edit count         | Read build-script output                 | 158 edits               |
| Candidate file count         | Read build-script output                 | 206 files               |

**Important:** The 61 missing `archive_*` entries are explicitly excluded by the audit brief. They are not counted as integrity failures.

### **Candidate run evidence**

I independently checked the bundled development-run hashes:

| Check                                     | Result  |
| ----------------------------------------- | ------- |
| Candidate manifest hash in `summary.json` | Matches |
| `results.jsonl` SHA-256                   | Matches |
| Result records                            | 144     |
| PASS                                      | 143     |
| FAIL                                      | 0       |
| NOT_IMPLEMENTED                           | 1       |
| ERROR                                     | 0       |

The result categories are:

- PACK-DERIVED: 141 PASS.
- OWNER-SPECIFIED: 2 PASS, 1 NOT_IMPLEMENTED.

This verifies the integrity of the supplied run evidence. It does **not** establish that the implementation is correct or that F18 is approved.

## **3. Individual correction assessment**

I applied the brief's distinction between a genuine textual clarification and a new rule introduced to make an existing implementation or fixture executable.

In particular, a descriptor's expected value is evidence of what its author intended to test. It is not automatically normative authority for creating a new protocol rule.

### **3.1 Correction verdict matrix**

The verdicts below assess the final candidate, including amendments where applicable.

| Item | Verdict         | Main assessment                                                                                   |
| ---- | --------------- | ------------------------------------------------------------------------------------------------- |
| C1   | SOUND WITH NOTE | Error-class generalization is plausible; one code is inferred rather than expressly stated.       |
| C2   | UNSOUND         | Descriptor-derived scope tokens and incomplete change-class input specification.                  |
| C3   | SOUND WITH NOTE | Existing halt-signature rules are correctly named; token spellings originate in M54.              |
| C4   | SOUND WITH NOTE | Whole-object comparison is the better reading, but output schemas remain incomplete.              |
| C5   | UNSOUND         | Introduces an executable Python predicate contract not established by v1.3.6.                     |
| C6   | UNSOUND         | Original FIFO-042 solution relies on an external, author-created specification. Superseded by A1. |
| C7   | SOUND           | Correctly removes a stale planning-pack version reference.                                        |
| C8   | SOUND           | Correctly resolves the literature-review/provenance contradiction.                                |
| C9   | SOUND WITH NOTE | Parser unit-vector contract follows an existing Protocol rule.                                    |
| C10  | SOUND WITH NOTE | Domain corrections are textually supported; invalid-signature handling is incomplete.             |
| C11  | UNSOUND         | Error classes are inferred from a majority pattern, not a normative rule.                         |
| C12  | SOUND WITH NOTE | Membership validation follows the serializer's closed-output requirement.                         |
| C13  | SOUND           | Truncation outputs and primitive behavior follow Protocol L168.                                   |
| C14  | SOUND           | Serialization properties follow Protocol L168.                                                    |
| C15  | SOUND WITH NOTE | Event mapping is grounded; recovery-attempt semantics are inferred.                               |
| C16  | SOUND WITH NOTE | Baseline mismatch mapping is consistent with §7a and the stage map.                               |
| A1   | SOUND WITH NOTE | Better than original C6; preserves M27's stated predicate but depends on C5.                      |
| A2   | SOUND           | Correctly synchronizes the normative copy.                                                        |
| OS-1 | SOUND WITH NOTE | Faithful to D-026 and §7b, with some deliberately restricted input combinations.                  |
| OS-2 | SOUND WITH NOTE | Expected outcome is correct, but supplied runtime evidence does not execute the alleged access.   |
| OS-3 | SOUND           | Correctly leaves P17 NOT_IMPLEMENTED.                                                             |

### **3.2 Detailed correction-by-correction assessment**

**C1 — Error classes of change-class vectors**

- **Baseline:** File 02 L175 explicitly assigns `AUTHORING_REVISION_REQUIRED` to M53 and `HALT_SIGNATURE_SCHEMA` to M54.
- **Candidate:** File 02 L175 introduces the rule that these three diagnostic codes have their own names as error classes, including `EVALUATOR_REVISION_REQUIRED`.
- **Conflict:** Real. M48's expected error class was not explicitly specified.
- **Best reading:** The generalization is reasonable. M53 and M54 provide two direct examples, while the stage map contains other patterns where diagnostic code and error class coincide.
- **Implementation/fixture fitting:** The author discloses that the three expected values match the descriptors. The code's existing lifecycle handling did not support these cases. This is evidence against the claim that the fix simply preserves implementation behavior.
- **New behavior:** The evaluator-revision error-class assignment is an extrapolation, not an explicit v1.3.6 rule.

**Verdict: SOUND WITH NOTE.** The new general rule should receive explicit owner approval, particularly for the evaluator-revision case.

**C2 — Change classes and scope tokens**

- **Baseline:** File 02 L176 keys closed `required_action` literals by fixture IDs such as `M48`, `M50`, `M53`, `M54` and `M58`.
- **Candidate:** File 02 L176 replaces those keys with change-class names and introduces four scope tokens.
- **Conflict:** Real. The fixture-specific organization is inconsistent with the stated desire for reusable rules.
- **Best reading:** Partially. Grouping the rules by actual revision category is better than making the rules depend on fixture IDs.
- **Implementation/fixture fitting:** The author explicitly admits that the token strings originate in the fixture descriptors rather than Protocol text. The M58 `unaffected_design_scope` token has no single supporting sentence.
- **New behavior:** Yes, to the extent that descriptor-derived tokens and properties become accepted normative control vocabulary.

There is another problem: `HALT_SIGNATURE_COMPONENT_ENUMERATION` is described as one of the closed change classes even though it is a domain-validation case, not a revision/change class.

The input property `change_class` is also not given a complete input contract in File 36.

**Verdict: UNSOUND.** The case grouping is good, but the token vocabulary and input contract require further normative specification.

**C3 — Halt-signature rule tokens**

- **Baseline:** File 02 L185 already specifies the exception-class rule and the exact halt-code token rule. M54 L36–L37 supplies their textual identifiers.
- **Candidate:** File 02 L185 names the rules as `stable_error_class_rule` and `stable_diagnostic_code_rule`.
- **Conflict:** Real at the level of fixture representation, not underlying semantics.
- **Best reading:** The added names are reasonable labels for rules that already exist.
- **Implementation/fixture fitting:** The names are copied from M54. However, their meanings are fully determined by the adjacent normative sentences.
- **New behavior:** No substantive new behavior.

**Verdict: SOUND WITH NOTE.** Retain the labels, but identify them as descriptive rule identifiers, not independently normative semantics.

**C4 — Control-vector comparison**

- **Baseline:** File 36 L23 permits an exact control-vector expectation. File 36 L176 describes comparison of disposition, stage, error class and diagnostic bytes.
- **Candidate:** File 36 L176 explicitly requires whole-object comparison, including the key set, for control vectors.
- **Conflict:** Real. The baseline does not adequately distinguish the two comparison modes.
- **Best reading:** Whole-object comparison is the stronger and more consistent interpretation of the word *exact*.
- **Implementation/fixture fitting:** The author acknowledges that A-032 already implemented this behavior.
- **New behavior:** It establishes a comparison rule, but does not itself establish the output schema.

**Verdict: SOUND WITH NOTE.** The comparator clarification is correct. The missing schemas remain an independent defect.

**C5 — Legal-input predicate**

- **Baseline:** File 30 L83 requires a design-specific legal-input predicate from the author-visible reset/legal-input specification.
- **Candidate:** File 30 L83 requires a Python 3.11 function of `(vector, sampled)` returning exactly Boolean `True` or `False`. It also makes other outcomes, including exceptions, evaluator failures.
- **Conflict:** Real. The original text does not define an executable predicate representation.
- **Best reading:** The proposed function is one possible implementation, not the uniquely supported interpretation. A declarative predicate specification or a separately frozen, trusted evaluator function would be cleaner.
- **Implementation/fixture fitting:** Significant concern. The author explicitly says the two-argument form and ordering match A-041/FIFO-042 and existing `validate_vector` behavior. The property names were first used in M27.
- **New behavior:** Yes. It introduces an executable predicate language, function interface, sampled-state argument and exception classification.

**Verdict: UNSOUND.**

The Protocol should define the predicate representation independently of the implementation. A fixture should not be allowed to create normative execution semantics merely by supplying Python source.

**C6 — M27 descriptor**

- **Baseline:** M27 L11–L12 puts both `wr_en` and `full` in the driven vector. File 30 L83 requires exact equality with the input-port set.
- **Original candidate:** Replaces the input with a FIFO-specific vector and FIFO-042 predicate.
- **Conflict:** Real. The original fixture cannot reach check (e).
- **Best reading:** The original C6 choice is not the best one. It imports a design-specific predicate from the FIFO materials rather than fixing only the defect in M27.
- **Implementation/fixture fitting:** Strong concern. FIFO-042 was drafted by the implementation author and subsequently frozen by the owners.
- **New behavior:** The original solution binds M27 to a particular FIFO rule that is not established by the planning-pack text.

**Verdict: UNSOUND. Superseded by A1.**

**C7 — Stale version label**

- **Baseline:** File 30 L7 says the schema version is independent of planning-pack version `1.3.1`.
- **Candidate:** File 30 L7 says it is independent of the planning-pack version.
- **Conflict:** Real.
- **Best reading:** Version-neutral wording is better than repeatedly inserting a release-specific number.
- **Implementation/fixture fitting:** None. Documentation-only.
- **New behavior:** None.

**Verdict: SOUND.**

**C8 — TechRxiv preprint status**

- **Baseline:** File 10 L174 reports that the preprint evaluates a synchronous FIFO. File 22 L8–L12 records abstract-only access and unverified detailed claims.
- **Candidate:** File 10 L174 explicitly labels the FIFO attribution and numerical details unverified; File 11 L37 and File 10 L383 are also corrected.
- **Conflict:** Real and directly demonstrated by the provenance record.
- **Best reading:** The provenance record is the appropriate source for the access status. The correction preserves the historical claim without presenting it as verified evidence.
- **Implementation/fixture fitting:** None.
- **New behavior:** None.

**Verdict: SOUND.**

**C9 — Parser unit-vector contract**

- **Baseline:** File 36 L27 refers to serializer and lifecycle unit vectors but does not define `parser_unit_vector`. File 02 L177 excludes parser from its `CONTROL_EXPECTATION` definition.
- **Candidate:** File 36 L27 defines the parser input and applies the existing Protocol L127 column rule. File 02 L177 now includes parser.
- **Conflict:** Real.
- **Best reading:** The parser vector is a local test of an already-defined syntax-error column rule. `CONTROL_EXPECTATION` is appropriate.
- **Implementation/fixture fitting:** The author acknowledges that the class name originates in M36. However, the actual behavior is supported by L127.
- **New behavior:** No substantive parser behavior. It formalizes the fixture contract.

**Verdict: SOUND WITH NOTE.**

**C10 — Halt-signature domains**

- **Baseline:** File 02 L185 enumerates uppercase component values. M42 and M47 contain values outside those domains.
- **Candidate:** M42/M47 are corrected to the enumerated values; File 02 L185 explicitly says out-of-domain supplied signatures are evaluator input errors and are not compared for recurrence.
- **Conflict:** Real.
- **Best reading:** Exact domain enforcement is the correct interpretation of an explicitly enumerated domain.
- **Implementation/fixture fitting:** The author states that the implementation already rejects out-of-domain signatures. The descriptor corrections are nevertheless supported by L185.
- **New behavior:** The explicit evaluator-input-error handling is an additional rule. Its diagnostic and ledger disposition are not defined.

**Verdict: SOUND WITH NOTE.** Define the handling of invalid supplied signatures before treating the input-error path as fully specified.

**C11 — Error classes for repeated halt and serializer rejection**

- **Baseline:** File 02 L185 defines the repeated-halt diagnostics without an error class. File 02 L173 defines the serializer-rejection diagnostic without an error class.
- **Candidate:** File 02 L174 and L185 assign error classes equal to the diagnostic codes.
- **Conflict:** Real.
- **Best reading:** The majority pattern cited by the author is evidence, but it is not a normative rule. A majority of similar rows cannot independently establish the required error class.
- **Implementation/fixture fitting:** The author admits that the expected values match the descriptors and that existing serializer behavior already uses the proposed class.
- **New behavior:** Yes. Two ledger outcomes now have newly selected error classes.

**Verdict: UNSOUND.**

This requires an explicit owner decision or a properly justified general error-class convention. The implementation's existing serializer class is not sufficient evidence.

**C12 — Emitted-set rule**

- **Baseline:** File 02 L168 says the serializer accepts only complete diagnostics emitted by the authoritative stage map.
- **Candidate:** File 02 L168 specifies grammar validation followed by membership validation when the emitted set is supplied. File 36 L195 defines `allowed_diagnostics`.
- **Conflict:** Real. The membership condition was not operationally specified.
- **Best reading:** The order follows the serializer's initial grammar-validation step. The optional set is a reasonable way to provide the available emitted diagnostics.
- **Implementation/fixture fitting:** The property name originates in M15. Its meaning is now expressly defined in the candidate.
- **New behavior:** No new diagnostic code or rejection reason. It makes the existing membership restriction testable.

**Verdict: SOUND WITH NOTE.** Ensure that `allowed_diagnostics` really represents the authoritative stage-map output set and cannot be treated as an arbitrary source of normative truth.

**C13 — Truncation primitive**

- **Baseline:** File 02 L168 defines the byte cap, marker, code-point boundary and truncation position. File 02 L187 says M14 tests truncation in isolation.
- **Candidate:** File 02 L168 explicitly defines the primitive's output properties; File 36 L196 defines the input contract.
- **Conflict:** Real at the level of output schema and primitive isolation.
- **Best reading:** The primitive should be tested independently of grammar validation, as the baseline already says.
- **Implementation/fixture fitting:** The property names originate in M14, but their meanings and values are now directly grounded in L168.
- **New behavior:** None beyond specifying the output of an existing primitive.

**Verdict: SOUND.**

**C14 — JSON-escaping primitive**

- **Baseline:** File 02 L168 defines UTF-8 serialization, key order, indentation, line endings and terminal newline. File 02 L187 says M17 tests JSON escaping in isolation.
- **Candidate:** File 02 L168 explicitly specifies the three output properties. File 36 L197 defines the input shape.
- **Conflict:** Real at the level of output schema.
- **Best reading:** The isolated serializer test is consistent with L187.
- **Implementation/fixture fitting:** The property names originate in M17, but the actual serialization requirements are explicit in the Protocol.
- **New behavior:** None.

**Verdict: SOUND.**

**C15 — Lifecycle halt-event vector**

- **Baseline:** File 02 L183 allows one recovery cycle. File 02 L185 defines the repeated-halt behavior. M13 supplies `evaluator_repair_attempt`.
- **Candidate:** File 36 L198 defines the event and slot structure and assigns `evaluator_repair_attempt = 1` as the ordinal of the recovery cycle the halt opens.
- **Conflict:** Real. The input contract and the meaning of the attempt field were not defined.
- **Best reading:** The event-to-stage mapping is consistent with the stage map. The ordinal interpretation is plausible but not uniquely compelled by the Protocol.
- **Implementation/fixture fitting:** The attempt-field interpretation is derived partly from the contrast between descriptor properties `evaluator_repair_attempt` and `recovery_cycles_used`. This is precisely the kind of descriptor-based inference that needs caution.
- **New behavior:** It introduces a specific meaning and slot-count consistency requirement for the input vector.

**Verdict: SOUND WITH NOTE.** Explicitly define the recovery-attempt ordinal in the Protocol, rather than relying on the descriptor's field name.

**C16 — Design-preflight vector**

- **Baseline:** File 02 L179 says a baseline mismatch halts before slots exist. File 02 L157 identifies the same-input masked RTL/null divergence row.
- **Candidate:** File 02 L179 and File 36 L199 define the design-preflight input and its result.
- **Conflict:** Real. R07 lacks an input contract.
- **Best reading:** The baseline mismatch maps to the existing masked-divergence stage-map record. The no-slot-scored disposition is consistent with §7a.
- **Implementation/fixture fitting:** The author admits the existing `paired_run_failure` implementation already generates this record. Nevertheless, the mapping is supported by the Protocol's own stage map.
- **New behavior:** No new outcome code.

**Verdict: SOUND WITH NOTE.**

### **3.3 Amendment assessments**

**A1 — Design-neutral replacement for C6**

Baseline M27 states:

> [41/M27.json L14] `"legal_input_predicate": "wr_en must be 0 when full is 1"`

The amended M27 now supplies:

- `driver_return`: `{"wr_en": "1"}`
- `input_port_widths`: `{"wr_en": 1}`
- `sampled_outputs`: `{"full": "1"}`
- A predicate implementing the original M27 condition.

The expected object remains unchanged.

**Assessment:**

1. The conflict is real.
2. A1 is better than original C6 because it avoids importing FIFO-042 and preserves the original fixture's intended condition.
3. The predicate is derived from the descriptor's prose, not independently from normative Protocol text.
4. It does not change M27's expected outcome, but it depends on the new executable-predicate mechanism introduced by C5.

SOUND WITH NOTE

I prefer A1 over original C6. However, C5 must be independently resolved before accepting this as a normative executable contract.

**A2 — File 25 normative copy**

The baseline File 25 L32 says:

> NORMATIVE CONTROL COPY (NOT MODEL-VISIBLE; normative text below is identical to Protocol §3.4)

The candidate applies the corresponding Protocol changes to the copy.

**Verification performed:**

- File 25 L33–L130 compared against candidate Protocol L90–L187.
- All 98 lines match exactly.
- File 25 L1–L32 compared byte-for-byte with baseline v1.3.6.
- Both model-visible bodies are unchanged.
- Candidate trailer is outside the copied normative section.

SOUND

A2 correctly fixes a genuine internal inconsistency without changing the model-visible prompt bodies.

### **3.4 OWNER-SPECIFIED assessments**

These items must not be presented as corrections derived from v1.3.6.

**OS-1 — M41 operational recovery**

Relevant baseline:

> [02 L183] "One recovery cycle per affected design is allowed."

> [02 L175] "RERUN_ALL_SCHEDULED_SLOTS_WITH_SAME_FROZEN_ARTIFACTS" (error class `MID_RUN_REEVALUATION`)

Candidate: File 36 L205.

Assessment:

- The success outcome is already stated in the Protocol.
- The evaluator-revision outcome is supported by §7b path (b) and L175.
- Author-visible changes are correctly left outside the vector because the vector cannot distinguish the different revision paths.
- The masked RTL/null divergence case is correctly excluded because the required root-cause review is absent.
- `required_action` is informational, not an invented decision input.
- `pre_halt_scored_slots` is a restricted input property, not a new outcome.

The important distinction is that OS-1 specifies which inputs reach existing outcomes. It does not create a new outcome code.

**Verdict: SOUND WITH NOTE.**

The restriction to nonzero pre-halt scores is acceptable as a declared scope limitation, but should not be mistaken for a Protocol-wide restriction.

**OS-2 — M37 aliased global random access**

Relevant baseline:

> [02 L156] "| Before first raw output divergence, paired next-input schedules differ | `TERMINAL` | `DRIVER_NONDETERMINISM` |"

> [02 L166] "(8) ... paired runs ..."

Candidate: File 36 L206.

Assessment:

- The expected stage is correctly identified as `TERMINAL`.
- The supplied paired-run outcome corresponds to the stage-map condition.
- Static steps (1)–(6) run against the response object.
- Steps (7)–(8) are represented by the supplied `runtime_pair`.
- The owner has explicitly selected option (a) under D-026.

**Important limitation:** `driver_source_excerpt` is not executed, matched against the response, or used to determine the outcome. Therefore, this vector does not independently demonstrate that the response actually contains aliased global random access.

It tests the supplied paired-run outcome and static-stage precedence, not the underlying runtime behavior.

**Verdict: SOUND WITH NOTE.**

The description should make that distinction unmistakable.

**OS-3 — P17 runtime driver vector**

Relevant baseline:

> [02 L152] "| Driver return value/vector is invalid | `DRIVER_VECTOR` | `DRIVER_VECTOR_INVALID` |"

> [02 L166] "(7) Execute `create_driver(seed)` and `Driver.step` on original RTL, then on null netlist"

Candidate: File 36 L207.

Assessment:

- `DRIVER_VECTOR` is a runtime stage.
- P17 does not supply the design, RTL, widths or the necessary runtime execution context.
- The Protocol does not define an alternative way to obtain the driver's runtime vector.
- D-026 requires the fixture to remain NOT_IMPLEMENTED when the required execution contract cannot be determined.

SOUND

**P17's NOT_IMPLEMENTED status is justified.** Attempting to produce the expected `MISSING_KEYS` result without the required runtime context would invent behavior.

### **3.5 OWNER-SPECIFIED separation verification**

PASS

I checked all three required locations.

| Requirement                     | Result          |
| ------------------------------- | --------------- |
| File 36 OWNER-SPECIFIED heading | PASS, L201      |
| File 36 individual OS labels    | PASS, L205–L207 |
| CHANGELOG E158                  | PASS            |
| M41 run record label            | PASS            |
| M37 run record label            | PASS            |
| P17 run record label            | PASS            |
| Separate summary categories     | PASS            |

The candidate summary records:

| Category        | PASS | FAIL | NOT_IMPLEMENTED |
| --------------- | ---- | ---- | --------------- |
| PACK-DERIVED    | 141  | 0    | 0               |
| OWNER-SPECIFIED | 2    | 0    | 1               |

The three owner-specified items are not mixed into the pack-derived count.

This is the correct governance treatment. The distinction should be preserved in any subsequent release.

## **4. Independent findings**

The following findings are not all failures of the same kind. Some concern the correctness of the proposed correction; others concern defects that remain unresolved.

### **D1-1 — Descriptor-derived change-class vocabulary**

MAJOR

**Location:** Candidate File 02 L176; File 36 L176.

Candidate text:

> "Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = ..."

The author admits in the corrections document that these token strings exist only in the descriptors.

**Problem:**

- M58's `unaffected_design_scope` combines multiple statements.
- The token spelling is not independently specified by the Protocol.
- `HALT_SIGNATURE_COMPONENT_ENUMERATION` is categorized as a change class despite being a signature-domain test.
- The `change_class` input contract is incomplete.

**Required fix:** Define the change-class input schema, permissible values, and each output property directly in the normative Protocol. Separate revision classes from domain-validation cases.

### **D1-2 — Control-vector output schemas remain incomplete**

PACK

**Location:** Candidate File 36 L176; File 02 L175–L176.

Candidate text:

> "Every property it names must be defined by a rule in the Protocol."

This requirement is correct, but the Protocol does not meet it.

For example, M48's expected object contains:

- `new_evaluator_version_hashes_required`
- `f16_required`
- `reuse_same_artifact_bytes`
- `new_confirmatory_generation_calls`

The Protocol defines the general evaluator-revision process, but does not formally define this entire output schema.

M50, M53 and M58 similarly contain additional Boolean and numeric properties that are not all defined as output fields.

**Required fix:** Add explicit control-vector schemas containing property names, types, allowed values and the normative rule for each property.

C4 improves comparison semantics; it does not solve this defect.

### **D1-3 — Python predicate execution is an added contract**

MAJOR

**Location:** Candidate File 30 L83; File 36 M27 descriptor.

Candidate text:

> "The predicate is frozen as one Python 3.11 function of two dictionaries, `(vector, sampled)`"

The baseline only requires a design-specific legal-input predicate.

It does not prescribe:

- Python as the predicate language.
- Executable function source in the fixture.
- The two-argument interface.
- Exception-to-evaluator-failure classification.

**Required fix:** Have the owners explicitly approve the predicate language and execution contract, or use a declarative representation grounded in the author-visible specification.

### **D1-4 — C6's original FIFO dependency**

MAJOR

**Location:** Original C6 rationale; File 41/M27.json.

The original correction imported FIFO-042 from the design materials.

That is not an adequate independent basis for changing the planning pack's general fixture contract.

**Required fix:** Retain A1 rather than original C6, subject to resolution of D1-3.

### **D1-5 — Repeated-halt and serializer error classes are inferred**

BLOCKER

**Location:** Candidate File 02 L174–L185; File 36 L18.

Candidate text:

> "`FEEDBACK_SERIALIZER_REJECT` is recorded at stage `FEEDBACK_SERIALIZER` with error class `FEEDBACK_SERIALIZER_REJECT`"

and:

> "Both terminations are recorded at stage `DESIGN_HALT` with error class `DESIGN_HALT_REPEATED`."

**Problem:**

The baseline defines these diagnostics, but not their error classes.

The argument that 13 out of 14 comparable stage-map rows use the diagnostic code as the error class is not a normative rule.

The fact that the implementation already uses one of these values is not sufficient justification.

**Required fix:** Obtain an explicit owner decision for both error classes and specify them in the Protocol. Keep the existing expected objects unchanged unless the owners separately authorize a test change.

### **D1-6 — Recovery-attempt semantics are not fully normative**

MAJOR

**Location:** Candidate File 36 L198.

Candidate text:

> "`evaluator_repair_attempt` = `1`, the ordinal of the recovery cycle this halt opens"

The baseline allows one recovery cycle but does not define the meaning of an `evaluator_repair_attempt` field.

The candidate's interpretation is plausible, but the descriptor's field name is doing part of the normative work.

**Required fix:** Define the attempt ordinal explicitly in §7b, including its relationship to the recovery cycle and repeated-halt condition.

### **D1-7 — Invalid halt-signature handling is incomplete**

MAJOR

**Location:** Candidate File 02 L185.

Candidate text:

> "A supplied halt signature with any component outside these domains is an evaluator input error; it is never compared for recurrence."

The input-error classification is reasonable, but the Protocol does not give its resulting diagnostic, stage, disposition or handling.

**Required fix:** Specify the invalid-signature outcome, or explicitly leave such cases outside the executable fixture contract.

### **D1-8 — M37 does not test the source-level alias**

MINOR

**Location:** Candidate File 36 L206.

Candidate text:

> "`driver_source_excerpt` ... documents the access under test; it is not executed, matched or read for the outcome."

This is transparent, and D-026 authorizes the supplied-outcome approach.

However, the name and description of the test could lead readers to believe that aliased global random access is actually detected in the response source.

**Required fix:** Label it explicitly as a paired-outcome control vector, not an executable test of source-level alias detection.

### **D1-9 — Development-run status needs qualification**

MINOR

**Location:** Candidate File 36 L3, L176; File 32 execution-status section; README fixture-status section.

Candidate text:

> "All fixtures remain NOT RUN / NOT PASSED."

The bundle also includes a candidate development run with 143 PASS records and one NOT_IMPLEMENTED record.

The brief distinguishes this development run from an authorized F18 acceptance run, so the two statuses can coexist if the distinction is explicit.

**Required fix:** Change the status wording to distinguish:

- Development execution evidence.
- Formal/authorized F18 acceptance status.
- Implementation qualification and approval status.

Do not present the development run as an approved F18 pass.

## **5. Internal consistency audit**

### **5.1 File 25 normative copy**

PASS — RUN

| Verification                  | Result         |
| ----------------------------- | -------------- |
| Protocol L90–L187             | 98 lines       |
| File 25 L33–L130              | 98 lines       |
| Line-by-line equality         | Exact          |
| File 25 L1–L32 against v1.3.6 | Byte-identical |
| Candidate trailer placement   | Correct        |

A2 resolves the copy inconsistency.

### **5.2 Cross-reference and version verification**

| Check                            | Method                             | Result         |
| -------------------------------- | ---------------------------------- | -------------- |
| Nine renamed document filenames  | Automated text scan                | PASS           |
| References to old filenames      | Automated text scan                | None found     |
| File 22 → candidate File 10 hash | SHA-256 computation and comparison | PASS           |
| Candidate titles and labels      | Direct inspection                  | PASS           |
| Historical records               | Direct inspection                  | PASS           |
| Owner records Files 16 and 23    | Direct inspection                  | PASS           |
| File 32 implementation status    | Direct inspection                  | PASS WITH NOTE |
| Candidate SHA256SUMS             | Previously verified                | PASS           |

File 22's File 10 hash is:

```
0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

It matches the actual candidate File 10.

**The three intentional exceptions are appropriate:**

1. Historical records should retain their original v1.3.6 identity.
2. Files 16 and 23 are owner records for v1.3.6 and should not be relabelled as candidate approvals.
3. File 32 should not claim that the implementation is formally approved merely because a development run exists.

The third exception needs the clarification in D1-9.

### **5.3 CHANGELOG completeness**

PASS — RUN

I executed the supplied build script from the extracted bundle root.

Results:

- 158 edits processed.
- 206 output files produced.
- All candidate files compared against the rebuilt output.
- No missing files.
- No additional files.
- No differing file hashes.

206/206 BYTE-FOR-BYTE MATCH

This is particularly important: the supplied candidate is not merely similar to a rebuild. It is exactly reproducible from the baseline and the supplied build process.

### **5.4 Fixture descriptor verification**

PASS — RUN

I compared all 144 fixture descriptors' expected objects between v1.3.6 and the candidate.

**Result: zero expected-object changes.**

Input changes include:

- M27: corrected under C6/A1.
- M41: OWNER-SPECIFIED input.
- M42 and M47: corrected halt-signature inputs.

The expected outcomes remain unchanged.

This is an important positive finding: the candidate has not silently altered the tests' expected results to make the proposed corrections pass.

### **5.5 Cross-reference consistency**

**Method: direct inspection and targeted comparisons.**

I checked:

- Protocol stage enumeration against the stage map.
- F18 disposition and diagnostic vocabulary.
- File 36 catalogue definitions against the fixture descriptors.
- C12–C16 control-vector contracts against the relevant Protocol stages.
- OS-1–OS-3 against their expected stages.
- The renamed files and their current references.

The principal remaining consistency concerns are D1-1, D1-2, D1-5 and D1-6.

In particular, the comparison rule at File 36 L176 is stronger than the actual normative output-schema coverage. This is not a hash or build problem; it is a specification-completeness problem.

## **6. Limitations and scope boundaries**

These limitations are explicitly recorded rather than treated as successful checks.

| ID   | Severity   | Limitation                                                                                                                                                                     |
| ---- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| L-01 | LIMITATION | I did not independently execute the OpenVEF implementation or reproduce its development run.                                                                                   |
| L-02 | LIMITATION | I did not run F18, certify its fixtures or authorize any LLM/provider call.                                                                                                    |
| L-03 | LIMITATION | The 61 baseline `archive_*` entries are absent from the extraction and therefore were not individually hash-verified. The brief explicitly excludes them.                      |
| L-04 | LIMITATION | The bundled development-run records were checked for integrity, not independently validated for behavioral correctness.                                                        |
| L-05 | LIMITATION | I did not independently retrieve the original TechRxiv PDF. The audit assesses the candidate's treatment of the provenance record, not the paper's actual experimental claims. |

These limitations do not invalidate the successful integrity and rebuild checks.

This is a document audit, not an implementation audit.

## **7. Final severity assessment**

**Finding distribution**

BLOCKER

**1**

MAJOR

**5**

MINOR

**2**

PACK

**1**

Nine findings: D1-1 through D1-9. Limitations L-01 through L-05 are recorded separately.

### **Required remediation order**

I recommend addressing the findings in this order:

1. **D1-5:** Resolve the two unsupported error-class assignments.
2. **D1-3:** Obtain an explicit owner decision on the executable legal-input predicate.
3. **D1-1 and D1-2:** Complete the change-class input contracts and control-vector output schemas.
4. **D1-6:** Define recovery-attempt semantics.
5. **D1-7:** Specify invalid halt-signature handling.
6. **D1-4:** Retain A1 and remove reliance on original C6's FIFO-specific approach.
7. **D1-8 and D1-9:** Clarify M37's test scope and development-run status.

C7, C8, C9, C13, C14 and A2 do not require substantive correction based on this audit.

## **8. Final audit decision**

**OVERALL STATUS: NOT CLEARED**

The v1.3.7 candidate is structurally reproducible and passes the supplied bundle-integrity checks. However, it is not yet sufficiently grounded in normative text to be accepted as the corrected planning pack.

**Reasons for NOT CLEARED:**

1. C5 introduces an executable predicate contract not established by v1.3.6.
2. C2 relies partly on descriptor-derived vocabulary without a complete normative input contract.
3. C4 does not resolve all control-vector output schemas.
4. C11 assigns error classes without sufficient normative authority.
5. C15 and C10 contain additional semantic assumptions requiring clarification.

The remaining findings should be addressed in a new numbered correction cycle, not silently edited into the existing candidate.

**Governance recommendation:**

- Keep v1.3.6 as the default pack.
- Keep v1.3.7 as an unaudited candidate.
- Preserve the verified bundle, candidate hashes and rebuild evidence.
- Do not interpret the development-run PASS records as formal F18 approval.
- Do not authorize implementation release or LLM/provider execution on the strength of this document audit.

**Final ruling: NOT CLEARED.**

The integrity of the candidate is established; the normative correctness of several corrections is not.