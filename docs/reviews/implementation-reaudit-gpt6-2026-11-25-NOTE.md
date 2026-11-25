# Note on the implementation re-audit (DEV-002)

**Not part of the report.** Written by Claude (Claude Opus 5.5, via Claude Code), the
implementation author, at Krishika's instruction.

**Copy and hash**
- [implementation-reaudit-gpt6-2026-11-25.md](implementation-reaudit-gpt6-2026-11-25.md): 16,993 bytes,
  SHA-256 `8ef52f96f75f5be983ae7032b59ab5ccc56afc2ec3d02e37e937890a2f001ec7`.
- File uploads failed, so Krishika pasted the text from claude.ai's copy into Claude Code. The text
  between the markers was extracted by script from the session transcript and not edited. **The hash
  equals the one Krishika gave**, so this copy is byte-identical to the one that hash describes
  (there is no final newline). It does not show that claude.ai's copy equals ChatGPT's original output.
- The text reads as rendered text: Markdown heading marks and table pipes are missing, and code
  lines are joined in places. It is kept as received.

**As stated by Krishika** (not verifiable from the report, except where it agrees)
- Model shown: "OpenAI GPT-6" (the report agrees; no finer version). Operator: Krishika (it agrees).
- Prompt used: "You are the implementation auditor. Unzip this bundle and follow
  docs/AUDIT-BRIEF.md exactly. This is a re-audit after fixes D-012 to D-014: state explicitly whether
  the earlier A1-1 BLOCKER and A8-1 MAJOR are resolved, judging A1 against both criteria in the brief,
  then audit all remaining areas. Report the bundle SHA-256 exactly as computed, the exact model name,
  and that I (Krishika) am the operator."

**What the report says**
- Final disposition **NOT CLEARED**. Two BLOCKERs (A1-1, A9-1); MAJOR A4-1; MAJOR A8-2, a
  cross-reference to A1-1; limitations A2-1, A3-1, A7-1 (CPython 3.13.5, no Docker).
- A1-1 **not fully resolved**: five single-fixture shapes remain under the original criterion; under
  D-013 four adapters satisfy it and M18 does not. It also says three vectors are "insufficient as a
  general guarantee against overfitting". A8-1 **resolved**.

**Checked by Claude against the audited zip** (`34bc8109…c0c0`, in git at `2ddd67c`)
- The bundle hash is right. The zip has 279 entries and `MANIFEST.sha256` lists 278 files, all verified;
  the report says 277.
- A4-1 reproduced: the old code serializes the auditor's case; the current code rejects it. It is now a
  test (`tests/test_local_rules.py`, `test_auditor_case_a4_1`).
- The first report was indeed not in that bundle (its note was), as the re-audit says.
- File 31 L9 and L11, File 30 L101 and Protocol L168: the quoted words are in the pack.

**Inconsistencies inside the report** (kept as written; not resolved here)
- A4: PASS with 0 MAJOR in the summary table; MAJOR A4-1 and "FINDINGS" in the body.
- A10: FINDINGS with 1 MINOR in the table; "PASS" in the body, and no MINOR finding is described.
- The overall reading used here is the stricter one in each case: A4 FINDINGS, A10 FINDINGS.

**What it does not cover.** It audited the code after D-012 to D-014. It does **not** cover D-015
(the fixes for its findings, made before Claude Code had seen the report) or D-016 (wall-clock reads).
Neither has been re-audited. **D-015 does not answer two of its points:** single-fixture shapes still
exist under the original criterion, and the three-vector minimum is unchanged. Those are for the
owner and the next auditor.

It is an AI audit, not a human independent audit. It does not satisfy L555 (5) or L271, and F18
is not passed.
