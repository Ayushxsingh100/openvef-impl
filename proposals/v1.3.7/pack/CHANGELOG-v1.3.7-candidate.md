# CHANGELOG — OpenVEF Planning v1.3.7 CANDIDATE (from v1.3.6)

**v1.3.7 CANDIDATE, not audited.** Built by `proposals/v1.3.7/build_candidate.py` from `baseline/OpenVEF_Planning_v1_3_6/`
(read-only, unchanged) under owner decision D-024 (Krishika). Rationale for every correction, with the
conflicting v1.3.6 text and the alternatives rejected: `proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md`.

- Every edit replaces text inside one line; no line moves, so line citations are the same in both packs.
- `correction` = C1–C10; `label` = the in-file candidate label; `derived` = a hash or byte length that
  follows mechanically from another edit. Old and new text are the replaced part of the line, unless
  `line` is `all` (whole-file replacement).
- **Known stale references (not edited):** File 22 L8–L12 cite the v1.3.6 SHA-256 of File 10
  (`a79a4d68…a11a`) as the literature-review record their provenance rows refer to. C8 changes File 10;
  those rows still describe the v1.3.6 record and are left as written. `03_Change_Log_v1.3.6.md`,
  `32_v1.3.6_Status_and_Gates.md`, `README.md` and the audit records still describe v1.3.6.
- The 61 `archive_*` entries of `27_SHA256SUMS.txt` are not in the extracted baseline and are not in this copy.

| # | Correction | PD | Fixtures | File | Line |
|---|---|---|---|---|---|
| E01 | C1 | PD-02 (2) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 175 |
| E02 | C2 | PD-02 (1) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E03 | C2 | PD-02 (1) | M50 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E04 | C2 | PD-02 (1) | M53 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E05 | C2 | PD-02 (1) | M54 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E06 | C2 | PD-02 (1) | M58 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E07 | C2 | PD-02 (1), (3) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E08 | C3 | PD-02 (3) | M54 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 185 |
| E09 | C10 | PD-01 | M41, M42, M47 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 185 |
| E10 | C4 | PD-03 | M14, M17, M41, M48, M50, M53, M54, M58 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 176 |
| E11 | C5 | PD-06, PD-25 | M27 | `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 83 |
| E12 | C6 | PD-06, PD-25 | M27 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 133 |
| E13 | C7 | PD-22 | none | `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 7 |
| E14 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 174 |
| E15 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 308 |
| E16 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 353 |
| E17 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 383 |
| E18 | C8 | PD-24 | none | `11_Comparative_Research_Matrix.md` | 37 |
| E19 | C9 | PD-04 | M36 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 27 |
| E20 | C9 | PD-04 | M36 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 15 |
| E21 | C9 | PD-04 | M36 | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 177 |
| E22 | C10 | PD-01 | M41 | `41_F18_Fixture_Inputs/M41.json` | 33 |
| E23 | C10 | PD-01 | M42 | `41_F18_Fixture_Inputs/M42.json` | 16 |
| E24 | C10 | PD-01 | M42 | `41_F18_Fixture_Inputs/M42.json` | 23 |
| E25 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 16 |
| E26 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 23 |
| E27 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 24 |
| E28 | label | — | M41 | `41_F18_Fixture_Inputs/M41.json` | 3 |
| E29 | label | — | M42 | `41_F18_Fixture_Inputs/M42.json` | 3 |
| E30 | label | — | M47 | `41_F18_Fixture_Inputs/M47.json` | 3 |
| E31 | label | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 560 |
| E32 | label | — | — | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 190 |
| E33 | label | — | — | `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 110 |
| E34 | label | — | — | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 418 |
| E35 | label | — | — | `11_Comparative_Research_Matrix.md` | 44 |
| E36 | C6 | PD-06, PD-25 | M27 | `41_F18_Fixture_Inputs/M27.json` | all |
| E37 | derived | — | M27 | `41_F18_Fixture_Inputs/fixture-index.json` | 380 |
| E38 | derived | — | M27 | `41_F18_Fixture_Inputs/fixture-index.json` | 381 |
| E39 | derived | — | M41 | `41_F18_Fixture_Inputs/fixture-index.json` | 562 |
| E40 | derived | — | M41 | `41_F18_Fixture_Inputs/fixture-index.json` | 563 |
| E41 | derived | — | M42 | `41_F18_Fixture_Inputs/fixture-index.json` | 579 |
| E42 | derived | — | M42 | `41_F18_Fixture_Inputs/fixture-index.json` | 580 |
| E43 | derived | — | M47 | `41_F18_Fixture_Inputs/fixture-index.json` | 644 |
| E44 | derived | — | M47 | `41_F18_Fixture_Inputs/fixture-index.json` | 645 |
| E45 | label | — | — | `41_F18_Fixture_Inputs/fixture-index.json` | 2 |
| E46 | derived | — | — | `27_SHA256SUMS.txt` | 2 |
| E47 | derived | — | — | `27_SHA256SUMS.txt` | 11 |
| E48 | derived | — | — | `27_SHA256SUMS.txt` | 12 |
| E49 | derived | — | — | `27_SHA256SUMS.txt` | 28 |
| E50 | derived | — | — | `27_SHA256SUMS.txt` | 34 |
| E51 | derived | — | — | `27_SHA256SUMS.txt` | 66 |
| E52 | derived | — | — | `27_SHA256SUMS.txt` | 80 |
| E53 | derived | — | — | `27_SHA256SUMS.txt` | 81 |
| E54 | derived | — | — | `27_SHA256SUMS.txt` | 86 |
| E55 | derived | — | — | `27_SHA256SUMS.txt` | 182 |

## E01 — C1 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L175 · PD-02 (2) · fixtures: M48, M50, M53, M54, M58

Old:

```text
The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; `M54` uses error class `HALT_SIGNATURE_SCHEMA` and diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

New:

```text
Error classes of change-class control expectations are stated by rule, not by fixture: a control expectation whose diagnostic CODE is `EVALUATOR_REVISION_REQUIRED` has error class `EVALUATOR_REVISION_REQUIRED`; one whose CODE is `AUTHORING_REVISION_REQUIRED` has error class `AUTHORING_REVISION_REQUIRED`; and one whose CODE is `HALT_SIGNATURE_SCHEMA` has error class `HALT_SIGNATURE_SCHEMA`. This rule applies only to these three codes; it does not change the M41 error class `MID_RUN_REEVALUATION` or any stage-map row. The study-reset vector uses diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; the halt-signature vector uses diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

## E02 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M48, M50, M53, M54, M58

Old:

```text
**Closed `required_action` literals used by lifecycle fixtures:** `M48` = `
```

New:

```text
**Closed `required_action` literals, by change class:** `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` = `
```

## E03 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M50

Old:

```text
`; `M50` = `
```

New:

```text
`; `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` = `
```

## E04 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M53

Old:

```text
`; `M53` = `
```

New:

```text
`; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` = `
```

## E05 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M54

Old:

```text
`; `M54` = `
```

New:

```text
`; `HALT_SIGNATURE_COMPONENT_ENUMERATION` = `
```

## E06 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M58

Old:

```text
`; and `M58` = `
```

New:

```text
`; and `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` = `
```

## E07 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1), (3) · fixtures: M48, M50, M53, M54, M58

Old:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. `M48` re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. `M50` invalidates all designs and all arm × design slots and starts a new preregistered study. `M53` resets the preregistered design set and weights and requires fresh confirmatory slots. `M58` invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

New:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. The change classes are closed and have these cases: `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` is the evaluator revision of §7b path (b); `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` is a shared-item revision; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` is a study reset; `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` is a design-specific revision while membership, estimand and weights remain unchanged; and `HALT_SIGNATURE_COMPONENT_ENUMERATION` is the halt-signature domain check. Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = `shared_evaluator_component_all_designs_and_all_arm_x_design_slots; design_specific_component_affected_design_in_both_arms` (§7b: shared component, both designs and every slot; design-specific component, that design in both arms). For a shared-item revision, `affected_slots` = `all_designs_x_all_arms` (§7b: every scheduled slot across both designs and both arms). For a design-specific revision, `affected_scope` = `affected_design_in_both_arms` and `unaffected_design_scope` = `not_invalidated_when_membership_estimand_and_weights_are_unchanged`. An evaluator revision re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. A shared-item revision invalidates all designs and all arm × design slots and starts a new preregistered study. A study reset resets the preregistered design set and weights and requires fresh confirmatory slots. A design-specific revision invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

## E08 — C3 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L185 · PD-02 (3) · fixtures: M54

Old:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token.
```

New:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes (rule token `stable_error_class_rule` = `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`); `stable_diagnostic_code` is exactly the corresponding `halt_code` token (rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

## E09 — C10 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L185 · PD-01 · fixtures: M41, M42, M47

Old:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

New:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`). A supplied halt signature with any component outside these domains is an evaluator input error; it is never compared for recurrence.
```

## E10 — C4 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L176 · PD-03 · fixtures: M14, M17, M41, M48, M50, M53, M54, M58

Old:

```text
compares actual disposition, stage, error class and exact diagnostic bytes with the expected object.
```

New:

```text
compares the actual result with the expected object. When the expected object has exactly the keys `disposition`, `stage_id`, `error_class` and `diagnostic`, those four values are compared exactly. Any other expected object is a control-vector expectation: its whole object is compared exactly, key set included, and every property it names must be defined by a rule in the Protocol.
```

## E11 — C5 · `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L83 · PD-06, PD-25 · fixtures: M27

Old:

```text
(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification.
```

New:

```text
(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification. The predicate is frozen as one Python 3.11 function of two dictionaries, `(vector, sampled)`: the driver vector, and the outputs sampled in the same row, each mapping a port name to its bit string. It returns the exact Boolean `True` for a legal vector and `False` otherwise. Any other outcome, including an exception, is an evaluator failure and is never an artifact verdict. Within check (a), missing keys are reported before extra keys. Checks (a) to (e) run in that order and the first failure is reported. A fixture that exercises check (e) supplies the input properties `driver_return` (the vector), `input_port_widths` (each input port name mapped to its width), `sampled_outputs` (the outputs sampled in the same row) and `legal_input_predicate` (an object with `language` = `python3.11`, `function`, the function's name, and `source`, its Python source).
```

## E12 — C6 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L133 · PD-06, PD-25 · fixtures: M27

Old:

```text
| M27 | missing-case | Driver vector violates a design-specific legal-input predicate |
```

New:

```text
| M27 | missing-case | Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input predicate |
```

## E13 — C7 · `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L7 · PD-22 · fixtures: none

Old:

```text
is independent of planning-pack version `1.3.1`.
```

New:

```text
is independent of the planning-pack version.
```

## E14 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L174 · PD-24 · fixtures: none

Old:

```text
**Reported proof of concept.** It evaluates a round-robin arbiter and synchronous FIFO (150–350 LOC), with 12 total test cases. It reports 10/12 tests detecting targeted gaps, zero false positives on the golden design, and an approximately 80-second detection cycle. The paper itself says this sample is too small for strong statistical confidence and treats it as a feasibility demonstration (Section VII-D). It also identifies one LLM model, manual mutation injection, small single-module designs, and UVM-specific scope as limitations (Section VII-E). The preprint is not peer reviewed.
```

New:

```text
**Reported proof of concept (unverified).** An earlier draft attributed a synchronous-FIFO case and numerical results to this preprint. Those details are not verified from its text (abstract-only access, File 22) and are not relied upon. The preprint is not peer reviewed.
```

## E15 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L308 · PD-24 · fixtures: none

Old:

```text
- The TechRxiv preprint reports 10/12 targeted gap detections on two small UVM IPs; it is a proof of concept, not a broad benchmark.
```

New:

```text
- The TechRxiv preprint is an unreviewed proof of concept; its numerical results and designs are not verified from its text (File 22) and are not relied upon.
```

## E16 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L353 · PD-24 · fixtures: none

Old:

```text
the TechRxiv checker-gap preprint also evaluates a synchronous FIFO;
```

New:

```text
whether the TechRxiv checker-gap preprint also evaluates a synchronous FIFO is not verified (File 22);
```

## E17 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L383 · PD-24 · fixtures: none

Old:

```text
| Extracted TechRxiv PDF text, including Definitions and experimental limitations (Sections II-A, III, IV–V, VII-D/VII-E); page-image screenshot fetch failed (502) | Moderate for method and declared limitations; checker-dependent definition of output observability; unreviewed preprint, two designs, 12 cases; treat cautiously but disclose as prior art |
```

New:

```text
| Abstract only, per File 22; the earlier statement that extracted full text was read is superseded | Low for method and limitations until the exact PDF is retrieved and inspected; unreviewed preprint; disclose as prior art |
```

## E18 — C8 · `11_Comparative_Research_Matrix.md` L37 · PD-24 · fixtures: none

Old:

```text
- TechRxiv checker-gap paper: full extracted text was read; PDF page images were not inspected; the paper's automated/manual injection descriptions conflict.
```

New:

```text
- TechRxiv checker-gap paper: abstract-only access is recorded (File 22); full-text and injection-method claims are not verified.
```

## E19 — C9 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L27 · PD-04 · fixtures: M36

Old:

```text
Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately grammar-exempt; they test local utilities/policies, not model feedback.
```

New:

```text
Serializer, lifecycle and parser unit vectors are marked by `fixture_class` (`serializer_primitive_unit_vector_grammar_exempt`, `lifecycle_unit_vector`, `parser_unit_vector`) and are deliberately grammar-exempt; they test local utilities/policies, not model feedback. A `parser_unit_vector` input has exactly the keys `source_file` and `syntax_error`. `source_file` is `driver.py` or `checker.py`. `syntax_error` has the key `lineno`, a positive integer, and may have the key `offset`, an integer or null. The vector applies the Protocol §3.4 `SOURCE_SYNTAX_REJECT` column rule to that position. Its result has stage `SOURCE_AST`, error class `SOURCE_SYNTAX_REJECT`, the diagnostic given by the rule, and disposition `CONTROL_EXPECTATION`.
```

## E20 — C9 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L15 · PD-04 · fixtures: M36

Old:

```text
- `CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector;
```

New:

```text
- `CONTROL_EXPECTATION`: a serializer, parser, protocol or lifecycle test vector;
```

## E21 — C9 · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L177 · PD-04 · fixtures: M36

Old:

```text
exercises a serializer, protocol or lifecycle rule;
```

New:

```text
exercises a serializer, parser, protocol or lifecycle rule;
```

## E22 — C10 · `41_F18_Fixture_Inputs/M41.json` L33 · PD-01 · fixtures: M41

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E23 — C10 · `41_F18_Fixture_Inputs/M42.json` L16 · PD-01 · fixtures: M42

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E24 — C10 · `41_F18_Fixture_Inputs/M42.json` L23 · PD-01 · fixtures: M42

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E25 — C10 · `41_F18_Fixture_Inputs/M47.json` L16 · PD-01 · fixtures: M47

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E26 — C10 · `41_F18_Fixture_Inputs/M47.json` L23 · PD-01 · fixtures: M47

Old:

```text
"evaluator_component": "recorder",
```

New:

```text
"evaluator_component": "RECORDER",
```

## E27 — C10 · `41_F18_Fixture_Inputs/M47.json` L24 · PD-01 · fixtures: M47

Old:

```text
"stable_error_class": "RecorderFault",
```

New:

```text
"stable_error_class": "NONE",
```

## E28 — label · `41_F18_Fixture_Inputs/M41.json` L3 · — · fixtures: M41

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E29 — label · `41_F18_Fixture_Inputs/M42.json` L3 · — · fixtures: M42

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E30 — label · `41_F18_Fixture_Inputs/M47.json` L3 · — · fixtures: M47

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E31 — label · `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L560 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E32 — label · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L190 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E33 — label · `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L110 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E34 — label · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L418 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E35 — label · `11_Comparative_Research_Matrix.md` L44 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E36 — C6 · `41_F18_Fixture_Inputs/M27.json` Lall · PD-06, PD-25 · fixtures: M27

Old:

```text
{
  "fixture_id": "M27",
  "fixture_version": "1.0",
  "scope": "missing-case",
  "description": "Driver vector violates a design-specific legal-input predicate",
  "manifest_clause_ids": [
    "FIFO-001"
  ],
  "input": {
    "driver_return": {
      "wr_en": "1",
      "full": "1"
    },
    "legal_input_predicate": "wr_en must be 0 when full is 1"
  },
  "expected": {
    "disposition": "REPAIR",
    "stage_id": "DRIVER_VECTOR",
    "error_class": "DRIVER_VECTOR_INVALID",
    "diagnostic": "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"
  }
}
```

New:

```text
{
  "fixture_id": "M27",
  "fixture_version": "1.3.7-candidate, not audited",
  "scope": "missing-case",
  "description": "Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input predicate",
  "manifest_clause_ids": [
    "FIFO-001"
  ],
  "input": {
    "driver_return": {
      "wr_en": "1",
      "wr_data": "00000000",
      "rd_en": "0"
    },
    "input_port_widths": {
      "wr_en": 1,
      "wr_data": 8,
      "rd_en": 1
    },
    "sampled_outputs": {
      "rd_valid": "0",
      "rd_data": "00000000",
      "full": "1",
      "almost_full": "1",
      "empty": "0"
    },
    "legal_input_predicate": {
      "language": "python3.11",
      "function": "legal_input",
      "source": "def legal_input(vector: dict[str, str], sampled: dict[str, str]) -> bool:\n    return not (sampled[\"full\"] == \"1\" and vector[\"wr_en\"] == \"1\" and vector[\"rd_en\"] == \"0\")\n"
    }
  },
  "expected": {
    "disposition": "REPAIR",
    "stage_id": "DRIVER_VECTOR",
    "error_class": "DRIVER_VECTOR_INVALID",
    "diagnostic": "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"
  }
}
```

## E37 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L380 · — · fixtures: M27

Old:

```text
"sha256": "fb7cd4179e9f103a1dc6f158839cd242b054f5d1e8fcf7e3c2a046c8c145e529",
```

New:

```text
"sha256": "615c2da757b316cf16cc7a2da04ede2bba7df1ee80b80968480c6b299207ebdc",
```

## E38 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L381 · — · fixtures: M27

Old:

```text
"bytes": 558,
```

New:

```text
"bytes": 1136,
```

## E39 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L562 · — · fixtures: M41

Old:

```text
"sha256": "56ba49bdedf6eda6f72d0231a1a2861112ff8691ef3a453725341449aab11863",
```

New:

```text
"sha256": "c2e42af7bf912c214f974d5ec371a0fe6845ee8f356d729226edf2db097723b7",
```

## E40 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L563 · — · fixtures: M41

Old:

```text
"bytes": 1626,
```

New:

```text
"bytes": 1651,
```

## E41 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L579 · — · fixtures: M42

Old:

```text
"sha256": "f76023e38e25f9b04059aa7e8d1a8360229c1ea840fb19c68484e5bae7fcfc01",
```

New:

```text
"sha256": "c86181f5e754d50a891def2cae82e194711a098e42419437c0d1985745d15d03",
```

## E42 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L580 · — · fixtures: M42

Old:

```text
"bytes": 1079,
```

New:

```text
"bytes": 1104,
```

## E43 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L644 · — · fixtures: M47

Old:

```text
"sha256": "c9868971e3f2c334ce6d08c925b1319a1c4e8a9ef5b2d7620799c09fe1b27797",
```

New:

```text
"sha256": "4958c30a5d0fd2baa1b032a4104e20268a832e265a7107409a8772b9d9d7515f",
```

## E44 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L645 · — · fixtures: M47

Old:

```text
"bytes": 1119,
```

New:

```text
"bytes": 1135,
```

## E45 — label · `41_F18_Fixture_Inputs/fixture-index.json` L2 · — · fixtures: —

Old:

```text
"fixture_index_version": "1.3.6",
```

New:

```text
"fixture_index_version": "1.3.7-candidate, not audited",
```

## E46 — derived · `27_SHA256SUMS.txt` L2 · — · fixtures: —

Old:

```text
1a3015ea38f96ab97e813076476d34f3043a40a83825106937ff633d14b61a87  02_OpenVEF_Experimental_Protocol_v1.3.6.md
```

New:

```text
3e5e70d07d4f0dc104e9a363d93d346d93527dd962e8bba48b6da4389448a228  02_OpenVEF_Experimental_Protocol_v1.3.6.md
```

## E47 — derived · `27_SHA256SUMS.txt` L11 · — · fixtures: —

Old:

```text
a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a  10_LLM_Era_Hardware_Verification_Literature_Review.md
```

New:

```text
0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974  10_LLM_Era_Hardware_Verification_Literature_Review.md
```

## E48 — derived · `27_SHA256SUMS.txt` L12 · — · fixtures: —

Old:

```text
014094c32d8c521ab0e865a358207ca09959b018978f67492a35626f9ff89fbe  11_Comparative_Research_Matrix.md
```

New:

```text
3e40cc28eacce8289660ee8a2c5239fb66e91e20abf7409a99dd5bcb0e07d8a3  11_Comparative_Research_Matrix.md
```

## E49 — derived · `27_SHA256SUMS.txt` L28 · — · fixtures: —

Old:

```text
b0b43989beb81be986caed48562c6832ca981449f82fd14f6ae8bdceed5b2ba6  30_Response_Parser_and_Execution_Contract_v1.3.6.md
```

New:

```text
ae1094db1a66e2216239409c6d4106e4672f35699f5fca0ae96760b686c83625  30_Response_Parser_and_Execution_Contract_v1.3.6.md
```

## E50 — derived · `27_SHA256SUMS.txt` L34 · — · fixtures: —

Old:

```text
270ccbd73691e6e32fbec8817e7c235d50ba3a803796270f236006e938f4983e  36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md
```

New:

```text
7dd73d29ecf676912d0e320f48e26d17378f8b92b1ce3268b6a649c9b4319893  36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md
```

## E51 — derived · `27_SHA256SUMS.txt` L66 · — · fixtures: —

Old:

```text
fb7cd4179e9f103a1dc6f158839cd242b054f5d1e8fcf7e3c2a046c8c145e529  41_F18_Fixture_Inputs/M27.json
```

New:

```text
615c2da757b316cf16cc7a2da04ede2bba7df1ee80b80968480c6b299207ebdc  41_F18_Fixture_Inputs/M27.json
```

## E52 — derived · `27_SHA256SUMS.txt` L80 · — · fixtures: —

Old:

```text
56ba49bdedf6eda6f72d0231a1a2861112ff8691ef3a453725341449aab11863  41_F18_Fixture_Inputs/M41.json
```

New:

```text
c2e42af7bf912c214f974d5ec371a0fe6845ee8f356d729226edf2db097723b7  41_F18_Fixture_Inputs/M41.json
```

## E53 — derived · `27_SHA256SUMS.txt` L81 · — · fixtures: —

Old:

```text
f76023e38e25f9b04059aa7e8d1a8360229c1ea840fb19c68484e5bae7fcfc01  41_F18_Fixture_Inputs/M42.json
```

New:

```text
c86181f5e754d50a891def2cae82e194711a098e42419437c0d1985745d15d03  41_F18_Fixture_Inputs/M42.json
```

## E54 — derived · `27_SHA256SUMS.txt` L86 · — · fixtures: —

Old:

```text
c9868971e3f2c334ce6d08c925b1319a1c4e8a9ef5b2d7620799c09fe1b27797  41_F18_Fixture_Inputs/M47.json
```

New:

```text
4958c30a5d0fd2baa1b032a4104e20268a832e265a7107409a8772b9d9d7515f  41_F18_Fixture_Inputs/M47.json
```

## E55 — derived · `27_SHA256SUMS.txt` L182 · — · fixtures: —

Old:

```text
f37808c7a662b8fdf164e27feaef023aadd6dfefaada35d11c3719185d1bde54  41_F18_Fixture_Inputs/fixture-index.json
```

New:

```text
cd87c9c8964327e0dd5542bd2ff78575d49674c892e426da25fd523f81a47cf4  41_F18_Fixture_Inputs/fixture-index.json
```
