"""Build proposals/v1.3.7/pack/: OpenVEF Planning v1.3.6 with the v1.3.7 candidate corrections applied.

Cycle 1: C1-C16, amendments A1-A2, stale references S, OWNER-SPECIFIED OS-1-OS-3 (D-024, D-025, D-026; CHANGELOG
E01-E158). Cycle 2 (D-027, after document audit #1): OWNER-DECIDED OD-n rules and numbered amendments, applied after
every cycle-1 edit and logged after E158, so no cycle-1 entry number moves.

v1.3.7 CANDIDATE, not audited. Document tooling only: no evaluator code. The baseline is read, never written.

Every edit replaces text inside one line, so no line of any pack file moves: citations by line number
(`02 L185` and so on) mean the same line in v1.3.6 and in the candidate. Each edit asserts that its old text
occurs exactly once in that line of the v1.3.6 file. Rationale for each correction:
proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md.

Usage: python3 -I proposals/v1.3.7/build_candidate.py [OUT_DIR]   (default proposals/v1.3.7/pack)
The output directory is deleted and rebuilt; the build is deterministic.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BASE = REPO / "baseline" / "OpenVEF_Planning_v1_3_6"
DEFAULT_OUT = HERE / "pack"

LABEL = "v1.3.7 CANDIDATE, not audited"
VERSION_LABEL = "1.3.7-candidate, not audited"
CHANGELOG = "CHANGELOG-v1.3.7-candidate.md"
LABEL_FILE = "CANDIDATE-LABEL.md"
SUMS = "SHA256SUMS-v1.3.7-candidate.txt"
OWN_FILES = (CHANGELOG, LABEL_FILE, SUMS)

P02 = "02_OpenVEF_Experimental_Protocol_v1.3.6.md"
P30 = "30_Response_Parser_and_Execution_Contract_v1.3.6.md"
P36 = "36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md"
P10 = "10_LLM_Era_Hardware_Verification_Literature_Review.md"
P11 = "11_Comparative_Research_Matrix.md"
P22 = "22_Source_Access_Provenance_Log_v1.2.md"
P25 = "25_Common_System_and_Repair_Prompt_Templates.txt"
# Amendment A2 (D-025): File 25 L32 says "NORMATIVE CONTROL COPY (NOT MODEL-VISIBLE; normative text below is identical
# to Protocol §3.4)", and its L33-L130 equal Protocol L90-L187 line for line. Every edit inside that Protocol range is
# applied to the copy as well (logged as A2), so the copy stays identical. Outside the model-visible bodies.
MIRROR = (P02, 90, 187, P25, -57)
FX = "41_F18_Fixture_Inputs/"

TRAILER = (f"\n---\n\n**{LABEL}.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in "
           f"`{CHANGELOG}` (owner decision D-024). It is not part of any released, audited or approved pack; "
           "v1.3.6 remains the default.\n")

_CC = {"M48": "FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED",
       "M50": "SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED",
       "M53": "DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START",
       "M54": "HALT_SIGNATURE_COMPONENT_ENUMERATION",
       "M58": "DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED"}

# (correction, PD, fixtures affected, file, line, old text, new text). Applied in this order; several edits may
# touch one line, each against the line as left by the previous edit.
EDITS: list[tuple[str, str, str, str, int, str, str]] = [
    ("C1", "PD-02 (2)", "M48, M50, M53, M54, M58", P02, 175,
     "The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic "
     "`AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; `M54` uses error class "
     "`HALT_SIGNATURE_SCHEMA` and diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.",
     "Error classes of change-class control expectations are stated by rule, not by fixture: a control expectation "
     "whose diagnostic CODE is `EVALUATOR_REVISION_REQUIRED` has error class `EVALUATOR_REVISION_REQUIRED`; one whose "
     "CODE is `AUTHORING_REVISION_REQUIRED` has error class `AUTHORING_REVISION_REQUIRED`; and one whose CODE is "
     "`HALT_SIGNATURE_SCHEMA` has error class `HALT_SIGNATURE_SCHEMA`. This rule applies only to these three codes; it "
     "does not change the M41 error class `MID_RUN_REEVALUATION` or any stage-map row. The study-reset vector uses "
     "diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; the halt-signature vector "
     "uses diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`."),
    ("C2", "PD-02 (1)", "M48, M50, M53, M54, M58", P02, 176,
     "**Closed `required_action` literals used by lifecycle fixtures:** `M48` = `",
     f"**Closed `required_action` literals, by change class:** `{_CC['M48']}` = `"),
    ("C2", "PD-02 (1)", "M50", P02, 176, "`; `M50` = `", f"`; `{_CC['M50']}` = `"),
    ("C2", "PD-02 (1)", "M53", P02, 176, "`; `M53` = `", f"`; `{_CC['M53']}` = `"),
    ("C2", "PD-02 (1)", "M54", P02, 176, "`; `M54` = `", f"`; `{_CC['M54']}` = `"),
    ("C2", "PD-02 (1)", "M58", P02, 176, "`; and `M58` = `", f"`; and `{_CC['M58']}` = `"),
    ("C2", "PD-02 (1), (3)", "M48, M50, M53, M54, M58", P02, 176,
     "Each literal is a closed local control expectation, not a model-feedback diagnostic. `M48` re-evaluates the "
     "affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. `M50` invalidates "
     "all designs and all arm × design slots and starts a new preregistered study. `M53` resets the preregistered "
     "design set and weights and requires fresh confirmatory slots. `M58` invalidates both arms for the affected "
     "design only when membership, estimand and weights remain unchanged.",
     "Each literal is a closed local control expectation, not a model-feedback diagnostic. The change classes are "
     f"closed and have these cases: `{_CC['M48']}` is the evaluator revision of §7b path (b); `{_CC['M50']}` is a "
     f"shared-item revision; `{_CC['M53']}` is a study reset; `{_CC['M58']}` is a design-specific revision while "
     f"membership, estimand and weights remain unchanged; and `{_CC['M54']}` is the halt-signature domain check. "
     "Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = "
     "`shared_evaluator_component_all_designs_and_all_arm_x_design_slots; "
     "design_specific_component_affected_design_in_both_arms` (§7b: shared component, both designs and every slot; "
     "design-specific component, that design in both arms). For a shared-item revision, `affected_slots` = "
     "`all_designs_x_all_arms` (§7b: every scheduled slot across both designs and both arms). For a design-specific "
     "revision, `affected_scope` = `affected_design_in_both_arms` and `unaffected_design_scope` = "
     "`not_invalidated_when_membership_estimand_and_weights_are_unchanged`. An evaluator revision re-evaluates the "
     "affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. A shared-item "
     "revision invalidates all designs and all arm × design slots and starts a new preregistered study. A study reset "
     "resets the preregistered design set and weights and requires fresh confirmatory slots. A design-specific "
     "revision invalidates both arms for the affected design only when membership, estimand and weights remain "
     "unchanged."),
    ("C3", "PD-02 (3)", "M54", P02, 185,
     "for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly "
     "the corresponding `halt_code` token.",
     "for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes (rule token `stable_error_class_rule` "
     "= `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`); `stable_diagnostic_code` is exactly the corresponding "
     "`halt_code` token (rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`)."),
    ("C10", "PD-01", "M41, M42, M47", P02, 185,
     "(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).",
     "(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`). A supplied halt signature with any "
     "component outside these domains is an evaluator input error; it is never compared for recurrence."),
    ("C4", "PD-03", "M14, M17, M41, M48, M50, M53, M54, M58", P36, 176,
     "compares actual disposition, stage, error class and exact diagnostic bytes with the expected object.",
     "compares the actual result with the expected object. When the expected object has exactly the keys "
     "`disposition`, `stage_id`, `error_class` and `diagnostic`, those four values are compared exactly. Any other "
     "expected object is a control-vector expectation: its whole object is compared exactly, key set included, and "
     "every property it names must be defined by a rule in the Protocol."),
    ("C5", "PD-06, PD-25", "M27", P30, 83,
     "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible "
     "reset/legal-input specification.",
     "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible "
     "reset/legal-input specification. The predicate is frozen as one Python 3.11 function of two dictionaries, "
     "`(vector, sampled)`: the driver vector, and the outputs sampled in the same row, each mapping a port name to its "
     "bit string. It returns the exact Boolean `True` for a legal vector and `False` otherwise. Any other outcome, "
     "including an exception, is an evaluator failure and is never an artifact verdict. Within check (a), missing keys "
     "are reported before extra keys. Checks (a) to (e) run in that order and the first failure is reported. A fixture "
     "that exercises check (e) supplies the input properties `driver_return` (the vector), `input_port_widths` (each "
     "input port name mapped to its width), `sampled_outputs` (the outputs sampled in the same row) and "
     "`legal_input_predicate` (an object with `language` = `python3.11`, `function`, the function's name, and "
     "`source`, its Python source)."),
    ("C6", "PD-06, PD-25", "M27", P36, 133,
     "| M27 | missing-case | Driver vector violates a design-specific legal-input predicate |",
     "| M27 | missing-case | Driver vector passes the key, type, width and symbol checks and violates the supplied "
     "legal-input predicate |"),
    ("C7", "PD-22", "none", P30, 7,
     "is independent of planning-pack version `1.3.1`.", "is independent of the planning-pack version."),
    ("C8", "PD-24", "none", P10, 174,
     "**Reported proof of concept.** It evaluates a round-robin arbiter and synchronous FIFO (150–350 LOC), with 12 "
     "total test cases. It reports 10/12 tests detecting targeted gaps, zero false positives on the golden design, and "
     "an approximately 80-second detection cycle. The paper itself says this sample is too small for strong "
     "statistical confidence and treats it as a feasibility demonstration (Section VII-D). It also identifies one LLM "
     "model, manual mutation injection, small single-module designs, and UVM-specific scope as limitations (Section "
     "VII-E). The preprint is not peer reviewed.",
     "**Reported proof of concept (unverified).** An earlier draft attributed a synchronous-FIFO case and numerical "
     "results to this preprint. Those details are not verified from its text (abstract-only access, File 22) and are "
     "not relied upon. The preprint is not peer reviewed."),
    ("C8", "PD-24", "none", P10, 308,
     "- The TechRxiv preprint reports 10/12 targeted gap detections on two small UVM IPs; it is a proof of concept, "
     "not a broad benchmark.",
     "- The TechRxiv preprint is an unreviewed proof of concept; its numerical results and designs are not verified "
     "from its text (File 22) and are not relied upon."),
    ("C8", "PD-24", "none", P10, 353,
     "the TechRxiv checker-gap preprint also evaluates a synchronous FIFO;",
     "whether the TechRxiv checker-gap preprint also evaluates a synchronous FIFO is not verified (File 22);"),
    ("C8", "PD-24", "none", P10, 383,
     "| Extracted TechRxiv PDF text, including Definitions and experimental limitations (Sections II-A, III, IV–V, "
     "VII-D/VII-E); page-image screenshot fetch failed (502) | Moderate for method and declared limitations; "
     "checker-dependent definition of output observability; unreviewed preprint, two designs, 12 cases; treat "
     "cautiously but disclose as prior art |",
     "| Abstract only, per File 22; the earlier statement that extracted full text was read is superseded | Low for "
     "method and limitations until the exact PDF is retrieved and inspected; unreviewed preprint; disclose as prior "
     "art |"),
    ("C8", "PD-24", "none", P11, 37,
     "- TechRxiv checker-gap paper: full extracted text was read; PDF page images were not inspected; the paper's "
     "automated/manual injection descriptions conflict.",
     "- TechRxiv checker-gap paper: abstract-only access is recorded (File 22); full-text and injection-method claims "
     "are not verified."),
    ("C9", "PD-04", "M36", P36, 27,
     "Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately "
     "grammar-exempt; they test local utilities/policies, not model feedback.",
     "Serializer, lifecycle and parser unit vectors are marked by `fixture_class` "
     "(`serializer_primitive_unit_vector_grammar_exempt`, `lifecycle_unit_vector`, `parser_unit_vector`) and are "
     "deliberately grammar-exempt; they test local utilities/policies, not model feedback. A `parser_unit_vector` "
     "input has exactly the keys `source_file` and `syntax_error`. `source_file` is `driver.py` or `checker.py`. "
     "`syntax_error` has the key `lineno`, a positive integer, and may have the key `offset`, an integer or null. The "
     "vector applies the Protocol §3.4 `SOURCE_SYNTAX_REJECT` column rule to that position. Its result has stage "
     "`SOURCE_AST`, error class `SOURCE_SYNTAX_REJECT`, the diagnostic given by the rule, and disposition "
     "`CONTROL_EXPECTATION`."),
    ("C9", "PD-04", "M36", P36, 15,
     "- `CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector;",
     "- `CONTROL_EXPECTATION`: a serializer, parser, protocol or lifecycle test vector;"),
    ("C9", "PD-04", "M36", P02, 177,
     "exercises a serializer, protocol or lifecycle rule;", "exercises a serializer, parser, protocol or lifecycle rule;"),
    ("C10", "PD-01", "M41", FX + "M41.json", 33,
     '"evaluator_component": "simulator",', '"evaluator_component": "SIMULATOR",'),
    ("C10", "PD-01", "M42", FX + "M42.json", 16,
     '"evaluator_component": "simulator",', '"evaluator_component": "SIMULATOR",'),
    ("C10", "PD-01", "M42", FX + "M42.json", 23,
     '"evaluator_component": "simulator",', '"evaluator_component": "SIMULATOR",'),
    ("C10", "PD-01", "M47", FX + "M47.json", 16,
     '"evaluator_component": "simulator",', '"evaluator_component": "SIMULATOR",'),
    ("C10", "PD-01", "M47", FX + "M47.json", 23,
     '"evaluator_component": "recorder",', '"evaluator_component": "RECORDER",'),
    ("C10", "PD-01", "M47", FX + "M47.json", 24,
     '"stable_error_class": "RecorderFault",', '"stable_error_class": "NONE",'),
]

# --- D-025 item 3: stale references (logged as "S"). A reference is stale when its correct target in the candidate
# differs: the pack's own version, title or audit status in a current document, or the name of a renamed file. A
# reference that records history (an audit, build, approval or change of v1.3.6 or earlier) is not stale and is kept;
# owner records (Files 16, 23) are not rewritten. Rationale: CORRECTIONS-v1.3.7-candidate.md, section 6.
CAND = "v1.3.7-candidate"
RENAMES = {f: f.replace("v1.3.6", CAND) for f in (
    "01_OpenVEF_Project_Charter_v1.3.6.md", P02, "21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md",
    P30, "31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md", "32_v1.3.6_Status_and_Gates.md",
    "33_Prompt_Assembly_Sidecar_v1.3.6.json", P36, "38_Authoring_Packet_Manifest_Template_v1.3.6.json")}
P01, P21, P31, P32, P33, P38 = ("01_OpenVEF_Project_Charter_v1.3.6.md",
                                "21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md",
                                "31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md", "32_v1.3.6_Status_and_Gates.md",
                                "33_Prompt_Assembly_Sidecar_v1.3.6.json", "38_Authoring_Packet_Manifest_Template_v1.3.6.json")
_VERSION = (f"**Version:** 1.3.7-candidate (OpenVEF Planning v1.3.6 with the corrections in "
            f"`CHANGELOG-v1.3.7-candidate.md`; not audited; not frozen; not approved). Based on: ")
_S = ("S", "—", "—")
STALE: list[tuple[str, int, str, str]] = [
    (P01, 1, "# OpenVEF Project Charter v1.3.6", f"# OpenVEF Project Charter {CAND}"),
    (P01, 4, "**Version:** 1.3.6 (", _VERSION + "1.3.6 ("),
    (P01, 9, "independent v1.3.6 document re-audit is pending.",
     f"independent v1.3.6 document re-audit is pending. The {CAND} pack is not audited."),
    (P01, 184, f"`{P02}`", f"`{RENAMES[P02]}`"),
    (P02, 1, "# OpenVEF Experimental Protocol v1.3.6", f"# OpenVEF Experimental Protocol {CAND}"),
    (P02, 4, "**Version:** 1.3.6 (", _VERSION + "1.3.6 ("),
    (P02, 9, "current v1.3.6 re-audit-pending status are recorded in §19.",
     f"v1.3.6 re-audit-pending status, and the not-audited {CAND} status, are recorded in §19."),
    (P02, 81, f"`{P30}`", f"`{RENAMES[P30]}`"),
    (P02, 81, f"`{P31}`", f"`{RENAMES[P31]}`"),
    (P02, 83, f"`{P31}`", f"`{RENAMES[P31]}`"),
    (P02, 187, f"`{P36}`", f"`{RENAMES[P36]}`"),
    (P02, 288, f"`{P30}`", f"`{RENAMES[P30]}`"),
    (P02, 555, "(1) Complete the v1.3.6 corrective document pack", f"(1) Complete the {CAND} document pack"),
    (P02, 555, "(2) Obtain an independent document-only v1.3.6 re-audit", f"(2) Obtain an independent document-only {CAND} audit"),
    (P02, 559, "v1.3.6 is a corrective evidence/metadata release",
     f"{CAND} is OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md`; it is not audited, "
     "frozen or approved, and v1.3.6 remains the default pack. v1.3.6 is a corrective evidence/metadata release"),
    (P21, 1, "Checklist (F18) v1.3.6", f"Checklist (F18) {CAND}"),
    *((P21, 3, f"`{old}`", f"`{RENAMES[old]}`") for old in (P30, P31, P33, P38, P36)),
    (P21, 63, "Protocol §3.4 and Catalog v1.3.6;", f"Protocol §3.4 and Catalog {CAND};"),
    (P30, 1, "# OpenVEF Response Parser and Execution Contract v1.3.6", f"# OpenVEF Response Parser and Execution Contract {CAND}"),
    (P30, 109, f"`{P36}`", f"`{RENAMES[P36]}`"),
    (P31, 1, "Canonicalization Specification v1.3.6", f"Canonicalization Specification {CAND}"),
    (P31, 17, f"`{P33}`", f"`{RENAMES[P33]}`"),
    (P31, 84, "after all v1.3.6 document and model-visible text edits are complete. This v1.3.6 release",
     f"after all {CAND} document and model-visible text edits are complete. This {CAND} release"),
    (P31, 84, "retain their exact values in the v1.3.6 sidecar", f"retain their exact values in the {CAND} sidecar"),
    (P32, 1, "# OpenVEF v1.3.6 Status and Gates", f"# OpenVEF {CAND} Status and Gates"),
    (P32, 3, "**Current release:** v1.3.6 corrective evidence/metadata pack.",
     f"**Current release:** {CAND} (the v1.3.6 corrective evidence/metadata pack with the corrections in "
     "`CHANGELOG-v1.3.7-candidate.md`; not audited, not frozen, not approved; v1.3.6 remains the default)."),
    (P32, 5, "**Current document audit status:** PENDING INDEPENDENT RE-AUDIT.",
     f"**Current document audit status:** {CAND} NOT AUDITED; v1.3.6 PENDING INDEPENDENT RE-AUDIT."),
    (P32, 48, "1. Independent document-only audit of the actual v1.3.6 pack.",
     f"1. Independent document-only audit of the actual {CAND} pack."),
    (P33, 2, '"sidecar_version": "1.3.6",', f'"sidecar_version": "{VERSION_LABEL}",'),
    (P33, 189, f'"payload_manifest_file": "{P38}",', f'"payload_manifest_file": "{RENAMES[P38]}",'),
    (P36, 1, "Missing-Case Fixture Catalog v1.3.6", f"Missing-Case Fixture Catalog {CAND}"),
    (P38, 71, '"Planning-pack v1.3.6 corrective evidence/metadata release.',
     f'"Planning-pack {CAND} (v1.3.6 corrective evidence/metadata release with the corrections in '
     'CHANGELOG-v1.3.7-candidate.md; not audited).'),
    ("README.md", 1, "# OpenVEF Planning Pack v1.3.6", f"# OpenVEF Planning Pack {CAND}"),
    ("README.md", 3, "**Status:** Corrective evidence/metadata release",
     f"**Status:** {LABEL}: OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md` "
     "(`CANDIDATE-LABEL.md` lists every file); v1.3.6 remains the default. v1.3.6 status: Corrective evidence/metadata release"),
    *(("README.md", n, f"`{old}`", f"`{RENAMES[old]}`") for n, old in (
        (7, P01), (8, P02), (11, P21), (13, P30), (14, P31), (14, P33), (16, P36), (17, P38))),
    ("README.md", 9, "— current release changes and audit lineage.",
     "— v1.3.6 release changes and audit lineage; the candidate's changes are in `CHANGELOG-v1.3.7-candidate.md`."),
    ("README.md", 46, "The current v1.3.6 independent document audit is pending.",
     f"The v1.3.6 independent document audit is pending; the {CAND} pack is not audited."),
]

# --- D-025 Phase A: C11-C16 (PD-26, PD-20, PD-03, PD-07). Rationale: CORRECTIONS-v1.3.7-candidate.md section 7.
EDITS += [
    ("C11", "PD-26", "M42, M47", P02, 185,
     "terminate with `DESIGN_HALT_REPEATED|reason=SECOND_HALT_AFTER_RECOVERY`.",
     "terminate with `DESIGN_HALT_REPEATED|reason=SECOND_HALT_AFTER_RECOVERY`. Both terminations are recorded at stage "
     "`DESIGN_HALT` with error class `DESIGN_HALT_REPEATED`."),
    ("C11", "PD-26", "M15", P02, 174,
     "The M17 JSON-escaping primitive uses error class `JSON_SERIALIZATION`.",
     "The M17 JSON-escaping primitive uses error class `JSON_SERIALIZATION`. "
     "`FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC` is recorded at stage `FEEDBACK_SERIALIZER` with error "
     "class `FEEDBACK_SERIALIZER_REJECT` and disposition `CONTROL_EXPECTATION`."),
    ("C13", "PD-02 (1), PD-03", "M14, M17", P02, 174,
     "The M14 truncation primitive uses error class `TRUNCATION`. The M17 JSON-escaping primitive uses error class "
     "`JSON_SERIALIZATION`.",
     "A truncation-primitive vector uses error class `TRUNCATION` and a JSON-escaping-primitive vector uses error class "
     "`JSON_SERIALIZATION`; both are recorded at stage `FEEDBACK_SERIALIZER` with disposition `CONTROL_EXPECTATION`."),
    ("C12", "PD-20", "M15", P02, 168,
     "a path-bearing or otherwise non-normative diagnostic fails the closed-grammar check and is not sent.",
     "a path-bearing or otherwise non-normative diagnostic fails the closed-grammar check and is not sent. When the set "
     "of diagnostics the stage map emitted is given, a diagnostic that passes the grammar but is not in that set is also "
     "rejected at step (1), with the same `FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC`."),
    ("C13", "PD-03", "M14, M17", P02, 168,
     "No raw exception text, validator/compiler message, file path, trace/output value or arbitrary free-form content "
     "is sent to the model.",
     "No raw exception text, validator/compiler message, file path, trace/output value or arbitrary free-form content "
     "is sent to the model. A truncation-primitive vector applies step (2) alone to its input string and reports "
     "`contains_marker` (whether the output ends with the marker), `valid_utf8` (whether the output bytes are valid "
     "UTF-8), `output_diagnostic_bytes` (the output's UTF-8 byte length) and `marker_utf8_bytes` (the marker's UTF-8 "
     "byte length). A JSON-escaping-primitive vector applies step (3) alone to its three-key object and reports "
     "`diagnostic_utf8` (the serialized text), `diagnostic_sha256` (the lowercase hexadecimal SHA-256 of its UTF-8 "
     "bytes) and `diagnostic_bytes` (their number)."),
    ("C16", "PD-07", "R07", P02, 179,
     "Any baseline mismatch halts the design before slots exist; no slot is scored.",
     "Any baseline mismatch halts the design before slots exist; no slot is scored. It is recorded at stage "
     "`DESIGN_HALT` with error class `RTL_NULL_CONTROL_FAILURE`, diagnostic "
     "`RTL_NULL_CONTROL_FAILURE|reason=MASKED_OUTPUT_DIVERGENCE` and disposition `DESIGN_HALT_NO_SLOT_SCORED`."),
]

# Lines appended after a file's last line (no existing line moves): File 36 input-shape section (PD-07; C12-C16).
APPENDS: dict[str, list[str]] = {P36: [
    "",
    "## Input shapes of control and lifecycle vectors (v1.3.7 candidate, C12–C16)",
    "",
    "Each shape below is the complete input of a fixture; a property outside its stated domain is an input error, not an "
    "outcome. A property whose value the Protocol fixes must equal that value and does not change the result.",
    "",
    "- **Serializer-grammar vector** (C12): `diagnostic` (a string) and, optionally, `allowed_diagnostics` (the "
    "duplicate-free list of diagnostics the stage map emitted). It applies Protocol §3.4 feedback-serialization step "
    "(1): the closed grammar, then membership when the list is given. A failure is the `FEEDBACK_SERIALIZER_REJECT` "
    "record; a pass has no record to compare.",
    "- **Truncation-primitive vector** (C13): `raw_diagnostic` (a string); `raw_diagnostic_utf8_bytes` (its UTF-8 byte "
    "length); `byte_cap` = `2048`; `marker` = `...[TRUNCATED]`; `truncate_on_utf8_boundary` = `true`; "
    "`truncate_before_json_escape` = `true`; `test_scope` = `TRUNCATION_PRIMITIVE_ONLY_GRAMMAR_BYPASSED`. The result is "
    "the step (2) control vector of Protocol §3.4.",
    "- **JSON-escaping-primitive vector** (C14): `feedback_object` (exactly the string keys `stage_id`, `error_class`, "
    "`diagnostic`); `encoding` = `UTF-8`; `ensure_ascii` = `false`; `indent` = `2`; `line_endings` = `LF`; "
    "`terminal_newline` = `true`; `grammar_exempt_for_primitive_test` = `true`; `test_scope` = "
    "`JSON_ESCAPING_PRIMITIVE_ONLY_GRAMMAR_BYPASSED`. The result is the step (3) control vector of Protocol §3.4, "
    "keys serialized in the order `stage_id`, `error_class`, `diagnostic`.",
    "- **Lifecycle halt-event vector** (C15): `lifecycle` = `MID_RUN` (the halt occurs after slots have begun, §7b); "
    "`event`, one stage-map event of kind `simulator_error` (`target` `rtl` or `null`, `exception_class`) or "
    "`trace_integrity` (`reason`); `slots` with non-negative integers `scheduled` (at least 1), `previously_evaluated`, "
    "`triggering_slot` (1 to `scheduled`) and `remaining`, where `previously_evaluated` + 1 + `remaining` = "
    "`scheduled`; `evaluator_repair_attempt` = `1`, the ordinal of the recovery cycle this halt opens (§7b allows one; "
    "a halt after that cycle is a recurrence, given as two halt signatures). The result is the event's stage-map row "
    "with disposition `DESIGN_HALT_NO_SLOT_SCORED`; the slot counts do not change it.",
    "- **Design-preflight vector** (C16): `design_preflight`, an object with exactly the Boolean "
    "`rtl_null_masked_divergence`. `true` is the §7a baseline mismatch record; `false` passes the gate, with no record "
    "to compare.",
]}

# --- D-026 Phase A: OWNER-SPECIFIED items OS-1-OS-3 (M41, M37, P17). Not pack-derived: owner decision D-026 (Krishika)
# fixes how each vector reaches the stage its pack-fixed outcome names, and adds no outcome code. Rationale and the
# rule each line applies: CORRECTIONS-v1.3.7-candidate.md section 10. Appended after the C12-C16 lines (no line moves).
OS_BLOCK = (
    "OS-1–OS-3 (OWNER-SPECIFIED, D-026)", "PD-07, PD-01, PD-03", "M41, M37, P17", [
        "",
        "## Owner-specified vector inputs (v1.3.7 candidate, OWNER-SPECIFIED OS-1–OS-3, owner decision D-026)",
        "",
        "These items are OWNER-SPECIFIED, not derived from pack text: the Protocol fixes each expected outcome, and owner "
        "decision D-026 specifies only how the vector reaches the stage that outcome names. They add no outcome code. A "
        "property outside its stated domain, or an input for which neither these items nor the Protocol states an "
        "outcome, is an input error, not an outcome.",
        "",
        "- **Operational-recovery vector** (OS-1, §7b): `design_id` (`FIFO` or `UART`, equal to the `design_id` of "
        "`halt_signature`); `halt_signature`, the halt's signature in the Protocol §7b domains, with `halt_code` "
        "`SIMULATOR_ERROR` or `TRACE_INTEGRITY_FAILURE` (a masked RTL/null divergence may use operational recovery only "
        "after a root-cause review, which this vector does not carry); `slots` as in the lifecycle halt-event vector, so the "
        "halt occurred after slots had begun; `evaluator_repair_attempt` = `1`; `recovery_mode` = `OPERATIONAL_RECOVERY`; "
        "the Booleans `frozen_evaluator_hashes_unchanged`, `f16_required`, `same_artifact_bytes` and "
        "`author_visible_materials_changed`; `pre_halt_scored_slots` (1 to `previously_evaluated`), the number of pre-halt "
        "scores; `scheduled_slots` = `scheduled`, the scheduled slots of the affected scope; `same_artifacts_for_all_slots` "
        "= `true`, `same_slot_seeds` = `true` and `new_generation_calls` = `0`, which restate §7b; and `required_action`, a "
        "string that is an informational label, not an outcome input. Only the properties named by the §7b recovery "
        "conditions decide the outcome. When `frozen_evaluator_hashes_unchanged` is `true`, `f16_required` is `false`, "
        "`same_artifact_bytes` is `true` and `author_visible_materials_changed` is `false`, the result is the "
        "successful-operational-recovery control expectation of Protocol §3.4 at stage `DESIGN_HALT` with disposition "
        "`CONTROL_EXPECTATION` and the properties `discard_pre_halt_scores` = `true`, `rerun_slots` = `scheduled_slots`, "
        "`reuse_same_artifact_bytes` = `true` and `new_confirmatory_generation_calls` = `0`. When the frozen evaluator "
        "hashes changed (`frozen_evaluator_hashes_unchanged` is `false`, `f16_required` is `true`, `same_artifact_bytes` "
        "is `true` and `author_visible_materials_changed` is `false`), the recovery is an evaluator revision and the result "
        "is the change-class control expectation of `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED`. The Protocol "
        "states no outcome for any other combination, including an author-visible change, which §7b sends to a study or "
        "design revision that the vector does not identify; such an input is outside this vector's scope.",
        "- **Paired-run outcome vector** (OS-2): `response_object` (a response object, as for any response input) and "
        "`runtime_pair`, an object with exactly `driver_source_excerpt` (a string that documents the access under test; it "
        "is not executed, matched or read for the outcome) and the Booleans `before_first_raw_output_divergence` and "
        "`next_input_schedules_equal`. Protocol §3.4 evaluation steps (1)–(6) run on the response object, and their first "
        "failure is the result. If all pass, `runtime_pair` stands in for steps (7)–(8), the paired run, which is not "
        "executed: `before_first_raw_output_divergence` = `true` with `next_input_schedules_equal` = `false` is the "
        "`DRIVER_NONDETERMINISM|reason=NEXT_INPUT_DIVERGENCE` row of the stage map. Any other pair does not determine the "
        "paired run's outcome and is outside this vector's scope.",
        "- **Runtime driver-vector input** (OS-3): `response_object` with `port_manifest` (`input_ports`). Its expected "
        "stage, `DRIVER_VECTOR`, is checked within evaluation step (7), while `Driver.step` runs on the original RTL; the "
        "input gives no design, RTL or port widths, and no rule states how the driver's vector is obtained outside that "
        "run. This input is not specified, and a fixture with it stays NOT_IMPLEMENTED.",
    ])
APPENDS[P36] = APPENDS[P36] + OS_BLOCK[3]
C12_C16_LINES = len(APPENDS[P36]) - len(OS_BLOCK[3])

# C6, as amended by A1 (D-025): the whole M27 descriptor is replaced (its input shape changes). The expected object
# is unchanged. A1 replaces the FIFO-042 predicate of the 24 Nov draft by the v1.3.6 descriptor's own rule,
# "wr_en must be 0 when full is 1", over a port set holding `wr_en` only, with `full` as a sampled output.
M27_NEW = {
    "fixture_id": "M27",
    "fixture_version": VERSION_LABEL,
    "scope": "missing-case",
    "description": "Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input "
                   "predicate",
    "manifest_clause_ids": ["FIFO-001"],
    "input": {
        "driver_return": {"wr_en": "1"},
        "input_port_widths": {"wr_en": 1},
        "sampled_outputs": {"full": "1"},
        "legal_input_predicate": {
            "language": "python3.11",
            "function": "legal_input",
            "source": "def legal_input(vector, sampled):\n"
                      "    return not (sampled[\"full\"] == \"1\" and vector[\"wr_en\"] == \"1\")\n"},
    },
    "expected": {"disposition": "REPAIR", "stage_id": "DRIVER_VECTOR", "error_class": "DRIVER_VECTOR_INVALID",
                 "diagnostic": "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"},
}
WHOLE_FILES = {FX + "M27.json": ("C6 + A1", "PD-06, PD-25", "M27")}
# In-file version labels on changed descriptors (approved labelling: changed files carry the label in-file).
VERSION_LINES = {FX + n: 3 for n in ("M41.json", "M42.json", "M47.json")}


# --- D-027: correction cycle 2 (document audit #1, docs/reviews/doc-audit1-gpt6-2026-11-27.md, findings D1-1..D1-9).
# OD-n = OWNER-DECIDED: a normative rule the owners add that v1.3.6 does not state (owner decision D-027, Krishika).
# Every cycle-2 edit is applied to the text as cycle 1 left it, after all cycle-1 edits, and logged after E158; the
# `pd` column holds the audit finding. Rationale: CORRECTIONS-v1.3.7-candidate.md section 11.
# (item, finding, fixtures, file, line, old text, new text): one-line edits, mirrored into File 25 like cycle 1.
CYCLE2: list[tuple[str, str, str, str, int, str, str]] = []
# (item, finding, fixtures, file, lines): lines appended after the file's last line as cycle 1 left it.
CYCLE2_APPENDS: list[tuple[str, str, str, str, list[str]]] = []

# OD-1 (D1-5, the BLOCKER): the error classes C11 chose by a majority pattern now rest on an owner convention.
_OD1 = ("**OWNER-DECIDED OD-1** (owner decision D-027; v1.3.6 does not state it): a stage-map row with a single "
        "diagnostic code and no stated error class has the error class equal to that diagnostic code; the "
        "`SIMULATOR_ERROR` row, whose stated error class is `EVALUATOR_INFRASTRUCTURE_FAILURE`, is the stated exception. "
        "An error-class cell `—` states that a row has no error class, so OD-1 does not apply to it. OD-1 decides exactly "
        "two error classes, those of the local-ledger rows `FEEDBACK_SERIALIZER_REJECT` and `DESIGN_HALT_REPEATED`; "
        "every other row of the stage map and of this vocabulary states its error class. By OD-1, ")
CYCLE2 += [
    ("OD-1", "D1-5", "M15", P02, 174,
     "`FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC` is recorded at stage `FEEDBACK_SERIALIZER` with error "
     "class `FEEDBACK_SERIALIZER_REJECT` and disposition `CONTROL_EXPECTATION`.",
     _OD1 + "`FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC` is recorded at stage `FEEDBACK_SERIALIZER` "
     "with error class `FEEDBACK_SERIALIZER_REJECT` and disposition `CONTROL_EXPECTATION`."),
    ("OD-1", "D1-5", "M42, M47", P02, 185,
     "Both terminations are recorded at stage `DESIGN_HALT` with error class `DESIGN_HALT_REPEATED`.",
     "Both terminations are recorded at stage `DESIGN_HALT` with error class `DESIGN_HALT_REPEATED` (OWNER-DECIDED "
     "OD-1, §3.4 local-ledger error classes)."),
]
# Descriptors first changed in cycle 2 get the in-file version label, logged in cycle 2.
CYCLE2_VERSION_LINES: dict[str, int] = {}
# Whole-descriptor replacements in cycle 2: rel -> (item, finding, fixtures, transform of the cycle-1 descriptor).
CYCLE2_WHOLE: dict[str, tuple[str, str, str, Callable[[dict], dict]]] = {}

# OD-2 (D1-3, D1-4): the owners adopt Python 3.11 as the predicate representation (C5 is re-based on it, A1 stands on
# it, the original C6 stays superseded). Hash gate: the frozen source's SHA-256, checked before the evaluator runs it.
CYCLE2 += [
    ("OD-2", "D1-3", "M27", P30, 83,
     "The predicate is frozen as one Python 3.11 function of two dictionaries, `(vector, sampled)`: the driver vector, and "
     "the outputs sampled in the same row, each mapping a port name to its bit string.",
     "**OWNER-DECIDED OD-2** (owner decision D-027; v1.3.6 does not state how the predicate is represented): the owners "
     "adopt Python 3.11 as its representation. The predicate is frozen as one Python 3.11 function of two dictionaries, "
     "`(vector, sampled)`: the driver vector, and the outputs sampled in the same row, each mapping a port name to its "
     "bit string. The function is pure: its result depends only on its two arguments, and it has no other effect."),
    ("OD-2", "D1-3", "M27", P30, 83,
     "Any other outcome, including an exception, is an evaluator failure and is never an artifact verdict.",
     "Any other outcome, including an exception, is an evaluator failure and is never an artifact verdict. The predicate "
     "is evaluator material, not artifact code: the evaluator executes it, outside every artifact process. It is "
     "hash-gated: the SHA-256 of its UTF-8 source is recorded when it is frozen, and the evaluator executes it only after "
     "checking that the source has that hash; a mismatch is an evaluator failure."),
    ("OD-2", "D1-3", "M27", P30, 83,
     "`function`, the function's name, and `source`, its Python source)",
     "`function`, the function's name, `source`, its Python source, and `source_sha256`, the lowercase hexadecimal "
     "SHA-256 of `source` in UTF-8, which is the frozen hash of OD-2)"),
]


def _od2_m27(d: dict) -> dict:
    """OD-2: M27's predicate carries its frozen hash; the source, the rest of the input and the expected object are A1's."""
    pred = d["input"]["legal_input_predicate"]
    pred["source_sha256"] = hashlib.sha256(pred["source"].encode("utf-8")).hexdigest()
    return d


CYCLE2_WHOLE[FX + "M27.json"] = ("OD-2", "D1-3, D1-4", "M27", _od2_m27)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lines_of(text: str) -> list[str]:
    assert text.endswith("\n")
    return text[:-1].split("\n")


def build(out: Path) -> dict:
    if out.exists():
        for p in [out, *out.rglob("*")]:
            p.chmod(0o755 if p.is_dir() else 0o644)
        shutil.rmtree(out)
    shutil.copytree(BASE, out, copy_function=shutil.copyfile)
    for p in [out, *out.rglob("*")]:  # fixed modes: the baseline is read-only, the copy is a working file set
        p.chmod(0o755 if p.is_dir() else 0o644)
    log: list[dict] = []
    texts: dict[str, list[str]] = {}

    def line_of(rel: str) -> list[str]:
        if rel not in texts:
            texts[rel] = lines_of((BASE / rel).read_text("utf-8"))
        return texts[rel]

    src, first, last, copy, shift = MIRROR
    assert line_of(src)[first - 1:last] == line_of(copy)[first - 1 + shift:last + shift], "File 25 copy differs"
    for cid, pd, fixtures, rel, n, old, new in [*EDITS, *((*_S, f, n, o, w) for f, n, o, w in STALE)]:
        targets = [(rel, n, cid)]
        if rel == src and first <= n <= last:
            targets.append((copy, n + shift, f"A2 (copy of {cid})"))
        for path, m, label in targets:
            lines = line_of(path)
            assert lines[m - 1].count(old) == 1, (label, path, m, old[:60])
            lines[m - 1] = lines[m - 1].replace(old, new)
            log.append({"correction": label, "pd": pd, "fixtures": fixtures, "file": path, "line": m, "old": old,
                        "new": new})
    for rel, n in VERSION_LINES.items():
        lines = line_of(rel)
        old = lines[n - 1]
        assert old.strip().startswith('"fixture_version": '), (rel, old)
        lines[n - 1] = old[:old.index(":") + 2] + json.dumps(VERSION_LABEL) + ","
        log.append({"correction": "label", "pd": "—", "fixtures": rel[len(FX):-5], "file": rel, "line": n,
                    "old": old.strip(), "new": lines[n - 1].strip()})
    os_entry = None
    for rel, extra in APPENDS.items():
        lines = line_of(rel)
        first_lines = extra[:C12_C16_LINES] if rel == P36 else extra
        log.append({"correction": "C12–C16", "pd": "PD-07", "fixtures": "M13, M14, M15, M17, R07", "file": rel,
                    "line": f"{len(lines) + 1}–{len(lines) + len(first_lines)}", "old": "(after the last line)",
                    "new": "\n".join(first_lines)})
        if rel == P36:  # D-026: logged last, so the CHANGELOG numbers of every earlier entry stay the same
            start = len(lines) + C12_C16_LINES + 1
            os_entry = {"correction": OS_BLOCK[0], "pd": OS_BLOCK[1], "fixtures": OS_BLOCK[2], "file": rel,
                        "line": f"{start}–{start + len(OS_BLOCK[3]) - 1}", "old": "(after the C12–C16 lines)",
                        "new": "\n".join(OS_BLOCK[3])}
        lines.extend(extra)

    # D-027 cycle 2: after every cycle-1 edit; logged in log2, which follows E158.
    touched1, log2 = set(texts), []
    for cid, pd, fixtures, rel, n, old, new in CYCLE2:
        targets = [(rel, n, cid)]
        if rel == src and first <= n <= last:
            targets.append((copy, n + shift, f"A2 (copy of {cid})"))
        for path, m, label in targets:
            lines = line_of(path)
            assert lines[m - 1].count(old) == 1, (label, path, m, old[:60])
            lines[m - 1] = lines[m - 1].replace(old, new)
            log2.append({"correction": label, "pd": pd, "fixtures": fixtures, "file": path, "line": m, "old": old,
                         "new": new})
    for rel, n in CYCLE2_VERSION_LINES.items():
        lines = line_of(rel)
        old = lines[n - 1]
        assert old.strip().startswith('"fixture_version": ') and VERSION_LABEL not in old, (rel, old)
        lines[n - 1] = old[:old.index(":") + 2] + json.dumps(VERSION_LABEL) + ","
        log2.append({"correction": "label", "pd": "—", "fixtures": rel[len(FX):-5], "file": rel, "line": n,
                     "old": old.strip(), "new": lines[n - 1].strip()})
    for cid, pd, fixtures, rel, extra in CYCLE2_APPENDS:
        lines = line_of(rel)
        log2.append({"correction": cid, "pd": pd, "fixtures": fixtures, "file": rel,
                     "line": f"{len(lines) + 1}–{len(lines) + len(extra)}", "old": "(after the last line)",
                     "new": "\n".join(extra)})
        lines.extend(extra)

    for rel, lines in texts.items():
        body = "\n".join(lines) + "\n"
        if rel.endswith(".md") or rel == P25:  # File 25: after its last line, outside the model-visible bodies
            body += TRAILER
            (log if rel in touched1 else log2).append({"correction": "label", "pd": "—", "fixtures": "—", "file": rel,
                        "line": len(lines) + 1, "old": "(end of file)", "new": "appended trailer: " + TRAILER.strip()})
        (out / rel).write_text(body, "utf-8")

    # Stale reference (S): File 22's provenance rows cite the literature-review record, File 10, by SHA-256. C8 and the
    # candidate label change File 10, so the rows now cite the candidate File 10 (written above).
    old_hash, new_hash = sha((BASE / P10).read_bytes()), sha((out / P10).read_bytes())
    lines22 = lines_of((BASE / P22).read_text("utf-8"))
    for i, text in enumerate(lines22):
        if old_hash in text:
            lines22[i] = text.replace(old_hash, new_hash)
            log.append({"correction": "S", "pd": "—", "fixtures": "—", "file": P22, "line": i + 1,
                        "old": f"Literature review record: SHA-256 {old_hash}",
                        "new": f"Literature review record: SHA-256 {new_hash}"})
    (out / P22).write_text("\n".join(lines22) + "\n" + TRAILER, "utf-8")
    log.append({"correction": "label", "pd": "—", "fixtures": "—", "file": P22, "line": len(lines22) + 1,
                "old": "(end of file)", "new": "appended trailer: " + TRAILER.strip()})

    for rel, (cid, pd, fixtures) in WHOLE_FILES.items():
        old_text = (BASE / rel).read_text("utf-8")
        new_text = json.dumps(M27_NEW, indent=2) + "\n"
        old_d = json.loads(old_text)
        assert old_d["expected"] == M27_NEW["expected"] and old_d["fixture_id"] == "M27"
        (out / rel).write_text(new_text, "utf-8")
        log.append({"correction": cid, "pd": pd, "fixtures": fixtures, "file": rel, "line": "all",
                    "old": old_text, "new": new_text})
    for rel, (cid, pd, fixtures, transform) in CYCLE2_WHOLE.items():  # D-027: on the descriptor cycle 1 left
        old_text = (out / rel).read_text("utf-8")
        old_d = json.loads(old_text)
        new_d = transform(json.loads(old_text))
        assert new_d["expected"] == old_d["expected"] and new_d["fixture_id"] == old_d["fixture_id"]
        new_text = json.dumps(new_d, indent=2) + "\n"
        (out / rel).write_text(new_text, "utf-8")
        log2.append({"correction": cid, "pd": pd, "fixtures": fixtures, "file": rel, "line": "all",
                     "old": old_text, "new": new_text})

    # Derived: the fixture index records each descriptor's SHA-256 and byte length (36 L176), and its version.
    changed_desc = sorted({e["file"] for e in log if e["file"].startswith(FX)})
    changed_desc2 = sorted({e["file"] for e in log2 if e["file"].startswith(FX)} - set(changed_desc))
    idx_rel = FX + "fixture-index.json"
    idx = lines_of((BASE / idx_rel).read_text("utf-8"))
    for rel in changed_desc + changed_desc2:
        target = log if rel in changed_desc else log2
        data = (out / rel).read_bytes()
        at = idx.index(f'      "path": "{rel}",')
        for k, v in (("sha256", json.dumps(sha(data))), ("bytes", str(len(data)))):
            j = next(i for i in range(at, at + 6) if idx[i].startswith(f'      "{k}": '))
            old = idx[j]
            idx[j] = f'      "{k}": {v},'
            target.append({"correction": "derived", "pd": "—", "fixtures": rel[len(FX):-5], "file": idx_rel,
                        "line": j + 1, "old": old.strip(), "new": idx[j].strip()})
    j = idx.index('  "fixture_index_version": "1.3.6",')
    idx[j] = f'  "fixture_index_version": {json.dumps(VERSION_LABEL)},'
    log.append({"correction": "label", "pd": "—", "fixtures": "—", "file": idx_rel, "line": j + 1,
                "old": '"fixture_index_version": "1.3.6",', "new": idx[j].strip()})
    (out / idx_rel).write_text("\n".join(idx) + "\n", "utf-8")

    for old, new in RENAMES.items():  # S: a current document's file name carries the pack version
        (out / old).rename(out / new)
        log.append({"correction": "S", "pd": "—", "fixtures": "—", "file": old, "line": "name", "old": old, "new": new})

    # Derived: 27_SHA256SUMS.txt lines of every changed file (the pack's own integrity list).
    sums_rel = "27_SHA256SUMS.txt"
    sums = lines_of((BASE / sums_rel).read_text("utf-8"))
    changed = sorted({e["file"] for e in log})
    changed2 = sorted({e["file"] for e in log2} - set(changed))
    for rel in changed + changed2:
        j = next(i for i, s in enumerate(sums) if s.endswith("  " + rel))
        old, name = sums[j], RENAMES.get(rel, rel)
        sums[j] = f"{sha((out / name).read_bytes())}  {name}"
        (log if rel in changed else log2).append({"correction": "derived", "pd": "—", "fixtures": "—", "file": sums_rel, "line": j + 1,
                    "old": old, "new": sums[j]})
    (out / sums_rel).write_text("\n".join(sums) + "\n", "utf-8")

    if os_entry is not None:
        log.append(os_entry)
    log.extend(log2)  # D-027: cycle 2 follows E158
    write_changelog(out, log)
    write_label(out, log)
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file() and p.name != SUMS)
    (out / SUMS).write_text("".join(f"{sha((out / f).read_bytes())}  {f}\n" for f in files), "utf-8")
    return {"edits": log, "files": len(files) + 1}


def fence(text: str) -> str:
    tick = "````" if "```" in text else "```"
    return f"{tick}text\n{text.rstrip(chr(10))}\n{tick}\n"


def shown(rel: str) -> str:
    return f"{RENAMES[rel]}` (was `{rel}" if rel in RENAMES else rel


def write_changelog(out: Path, log: list[dict]) -> None:
    rows = ["# CHANGELOG — OpenVEF Planning v1.3.7 CANDIDATE (from v1.3.6)", "",
            f"**{LABEL}.** Built by `proposals/v1.3.7/build_candidate.py` from `baseline/OpenVEF_Planning_v1_3_6/`",
            "(read-only, unchanged) under owner decision D-024 (Krishika). Rationale for every correction, with the",
            "conflicting v1.3.6 text and the alternatives rejected: `proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md`.",
            "", "- Every edit replaces text inside one line; no line moves, so line citations are the same in both packs.",
            "- `correction` = C1–C16; `A1`, `A2` = numbered amendments; `OS-1–OS-3` = OWNER-SPECIFIED items (owner",
            "  decision D-026; not pack-derived, counted separately from C1–C16); `S` = a stale reference fixed (D-025 item 3;",
            "  `line` `name` = a file renamed); `label` = the in-file candidate label; `derived` = a hash or byte length",
            "  that follows mechanically from another edit. Old and new text are the replaced part of the line, unless",
            "  `line` is `all` (whole-file replacement).",
            "- **Correction cycle 2 (owner decision D-027), after document audit #1 (NOT CLEARED;",
            "  `docs/reviews/doc-audit1-gpt6-2026-11-27.md` in the implementation repository).** Its entries follow the last",
            "  cycle-1 entry (E158) and edit the text as cycle 1 left it, so no cycle-1 entry number moves. `OD-n` =",
            "  OWNER-DECIDED: a normative rule the owners add that v1.3.6 does not state, labelled as such in the pack text;",
            "  every fixture that depends on one is counted OWNER-DECIDED. For cycle-2 entries the `PD` column holds the",
            "  audit finding (`D1-n`). `derived` entries show the hashes of the final build, cycle 2 included.",
            "- **Kept on purpose (not stale):** references that record history — the v1.3.6 change log, build, correction",
            "  and audit records (Files 03, 48, 50, 56, 57, 58, 63 and the audit transcripts), and statements of what",
            "  v1.3.6 did — and the owners' records (Files 16, 23), which describe owner decisions on v1.3.6 and are not",
            "  rewritten for a candidate the owners have not approved.",
            "- The 61 `archive_*` entries of `27_SHA256SUMS.txt` are not in the extracted baseline and are not in this copy.",
            "", "| # | Correction | PD / finding | Fixtures | File | Line |", "|---|---|---|---|---|---|"]
    for i, e in enumerate(log, 1):
        rows.append(f"| E{i:02d} | {e['correction']} | {e['pd']} | {e['fixtures']} | `{shown(e['file'])}` | {e['line']} |")
    rows.append("")
    for i, e in enumerate(log, 1):
        rows += [f"## E{i:02d} — {e['correction']} · `{shown(e['file'])}` L{e['line']} · {e['pd']} · fixtures: {e['fixtures']}",
                 "", "Old:", "", fence(e["old"]), "New:", "", fence(e["new"])]
    (out / CHANGELOG).write_text("\n".join(rows), "utf-8")


def write_label(out: Path, log: list[dict]) -> None:
    changed = {RENAMES.get(e["file"], e["file"]) for e in log} | {CHANGELOG}
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    rows = [f"# {LABEL}", "",
            f"**Every file in this directory is part of OpenVEF Planning {LABEL}.** It is a copy of v1.3.6 with",
            "corrections C1–C16 and amendments A1–A2 applied (owner decisions D-024, D-025) and the OWNER-SPECIFIED",
            "items OS-1–OS-3 (owner decision D-026; `" + CHANGELOG + "`), and with correction cycle 2 (owner",
            "decision D-027: OWNER-DECIDED rules OD-n and numbered amendments) after document audit #1 of cycle 1",
            "(NOT CLEARED). It is not released, not audit-cleared and not approved, and v1.3.6 (`baseline/`) remains",
            "the default pack.", "",
            "- **In-file label:** every file a correction changed carries the label itself (Markdown and File 25: an",
            "  appended trailer, in File 25 after its last line and outside the model-visible bodies; fixture JSON:",
            "  `fixture_version` / `fixture_index_version`). `27_SHA256SUMS.txt` is changed",
            "  (derived hashes) but cannot carry text without breaking its format; it is labelled here.",
            "- **Labelled by this file:** every other file is byte-identical to v1.3.6 (JSON, CSV, prompt templates",
            "  and verbatim audit records cannot be edited without changing bytes that tools or provenance depend on).",
            f"- `{SUMS}` lists the SHA-256 of every file here except itself.", "",
            "| File | Status |", "|---|---|"]
    for f in files + [LABEL_FILE, SUMS]:
        if f in (LABEL_FILE, SUMS) and f in files:
            continue
        status = ("candidate record; labelled in-file" if f in OWN_FILES else
                  "changed (derived); labelled here" if f == "27_SHA256SUMS.txt" else
                  "changed; labelled in-file" if f in changed else "identical to v1.3.6; labelled here")
        rows.append(f"| `{f}` | {status} |")
    (out / LABEL_FILE).write_text("\n".join(rows) + "\n", "utf-8")


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUT
    result = build(target)
    print(json.dumps({"out": str(target), "edits": len(result["edits"]), "files": result["files"]}))
