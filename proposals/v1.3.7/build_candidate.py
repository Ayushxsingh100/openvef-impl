"""Build proposals/v1.3.7/pack/: OpenVEF Planning v1.3.6 with corrections C1-C10 applied (D-024 Phase A).

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
    for cid, pd, fixtures, rel, n, old, new in EDITS:
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
    for rel, lines in texts.items():
        body = "\n".join(lines) + "\n"
        if rel.endswith(".md") or rel == P25:  # File 25: after its last line, outside the model-visible bodies
            body += TRAILER
            log.append({"correction": "label", "pd": "—", "fixtures": "—", "file": rel,
                        "line": len(lines) + 1, "old": "(end of file)", "new": "appended trailer: " + TRAILER.strip()})
        (out / rel).write_text(body, "utf-8")

    for rel, (cid, pd, fixtures) in WHOLE_FILES.items():
        old_text = (BASE / rel).read_text("utf-8")
        new_text = json.dumps(M27_NEW, indent=2) + "\n"
        old_d = json.loads(old_text)
        assert old_d["expected"] == M27_NEW["expected"] and old_d["fixture_id"] == "M27"
        (out / rel).write_text(new_text, "utf-8")
        log.append({"correction": cid, "pd": pd, "fixtures": fixtures, "file": rel, "line": "all",
                    "old": old_text, "new": new_text})

    # Derived: the fixture index records each descriptor's SHA-256 and byte length (36 L176), and its version.
    changed_desc = sorted({e["file"] for e in log if e["file"].startswith(FX)})
    idx_rel = FX + "fixture-index.json"
    idx = lines_of((BASE / idx_rel).read_text("utf-8"))
    for rel in changed_desc:
        data = (out / rel).read_bytes()
        at = idx.index(f'      "path": "{rel}",')
        for k, v in (("sha256", json.dumps(sha(data))), ("bytes", str(len(data)))):
            j = next(i for i in range(at, at + 6) if idx[i].startswith(f'      "{k}": '))
            old = idx[j]
            idx[j] = f'      "{k}": {v},'
            log.append({"correction": "derived", "pd": "—", "fixtures": rel[len(FX):-5], "file": idx_rel,
                        "line": j + 1, "old": old.strip(), "new": idx[j].strip()})
    j = idx.index('  "fixture_index_version": "1.3.6",')
    idx[j] = f'  "fixture_index_version": {json.dumps(VERSION_LABEL)},'
    log.append({"correction": "label", "pd": "—", "fixtures": "—", "file": idx_rel, "line": j + 1,
                "old": '"fixture_index_version": "1.3.6",', "new": idx[j].strip()})
    (out / idx_rel).write_text("\n".join(idx) + "\n", "utf-8")

    # Derived: 27_SHA256SUMS.txt lines of every changed file (the pack's own integrity list).
    sums_rel = "27_SHA256SUMS.txt"
    sums = lines_of((BASE / sums_rel).read_text("utf-8"))
    changed = sorted({e["file"] for e in log})
    for rel in changed:
        j = next(i for i, s in enumerate(sums) if s.endswith("  " + rel))
        old = sums[j]
        sums[j] = f"{sha((out / rel).read_bytes())}  {rel}"
        log.append({"correction": "derived", "pd": "—", "fixtures": "—", "file": sums_rel, "line": j + 1,
                    "old": old, "new": sums[j]})
    (out / sums_rel).write_text("\n".join(sums) + "\n", "utf-8")

    write_changelog(out, log)
    write_label(out, log)
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file() and p.name != SUMS)
    (out / SUMS).write_text("".join(f"{sha((out / f).read_bytes())}  {f}\n" for f in files), "utf-8")
    return {"edits": log, "files": len(files) + 1}


def fence(text: str) -> str:
    tick = "````" if "```" in text else "```"
    return f"{tick}text\n{text.rstrip(chr(10))}\n{tick}\n"


def write_changelog(out: Path, log: list[dict]) -> None:
    rows = ["# CHANGELOG — OpenVEF Planning v1.3.7 CANDIDATE (from v1.3.6)", "",
            f"**{LABEL}.** Built by `proposals/v1.3.7/build_candidate.py` from `baseline/OpenVEF_Planning_v1_3_6/`",
            "(read-only, unchanged) under owner decision D-024 (Krishika). Rationale for every correction, with the",
            "conflicting v1.3.6 text and the alternatives rejected: `proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md`.",
            "", "- Every edit replaces text inside one line; no line moves, so line citations are the same in both packs.",
            "- `correction` = C1–C10; `label` = the in-file candidate label; `derived` = a hash or byte length that",
            "  follows mechanically from another edit. Old and new text are the replaced part of the line, unless",
            "  `line` is `all` (whole-file replacement).",
            "- **Known stale references (not edited):** File 22 L8–L12 cite the v1.3.6 SHA-256 of File 10",
            "  (`a79a4d68…a11a`) as the literature-review record their provenance rows refer to. C8 changes File 10;",
            "  those rows still describe the v1.3.6 record and are left as written. `03_Change_Log_v1.3.6.md`,",
            "  `32_v1.3.6_Status_and_Gates.md`, `README.md` and the audit records still describe v1.3.6.",
            "- The 61 `archive_*` entries of `27_SHA256SUMS.txt` are not in the extracted baseline and are not in this copy.",
            "", "| # | Correction | PD | Fixtures | File | Line |", "|---|---|---|---|---|---|"]
    for i, e in enumerate(log, 1):
        rows.append(f"| E{i:02d} | {e['correction']} | {e['pd']} | {e['fixtures']} | `{e['file']}` | {e['line']} |")
    rows.append("")
    for i, e in enumerate(log, 1):
        rows += [f"## E{i:02d} — {e['correction']} · `{e['file']}` L{e['line']} · {e['pd']} · fixtures: {e['fixtures']}",
                 "", "Old:", "", fence(e["old"]), "New:", "", fence(e["new"])]
    (out / CHANGELOG).write_text("\n".join(rows), "utf-8")


def write_label(out: Path, log: list[dict]) -> None:
    changed = {e["file"] for e in log} | {CHANGELOG}
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    rows = [f"# {LABEL}", "",
            f"**Every file in this directory is part of OpenVEF Planning {LABEL}.** It is a copy of v1.3.6 with",
            "corrections C1–C10 applied (owner decision D-024; `" + CHANGELOG + "`). It is not released, not audited",
            "and not approved, and v1.3.6 (`baseline/`) remains the default pack.", "",
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
