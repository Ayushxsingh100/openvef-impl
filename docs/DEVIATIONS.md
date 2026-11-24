# Deviations from the planning pack

Owner-accepted departures from a pack requirement. A deviation does not make the
requirement met. Each affected result carries the deviation's label.

## DEV-001 — No independent mask review (Protocol L271)

> [02 L271] "The table is signed by an independent mask reviewer and is checked in F18."

> [21 L32] "| Independent reviewer | Reviewer did not author templates or mask; signs exact hashes and checklist | PENDING |"

**Owner decision (Krishika, sole builder, 24 Nov 2026), adopting a Claude (claude.ai)
recommendation; pasted into Claude Code:** "no independent human mask reviewer is
available. The observation mask and File 24 table are accepted by the owner (Krishika) on
the basis of Claude's review; this is NOT an independent review."

**Correction (Krishika, given after the first record of DEV-001, 24 Nov 2026 UTC):** the
Claude (claude.ai) mask review had **not** happened when DEV-001 was recorded, so the
words "on the basis of Claude's review" above were not true at that time. The review is
to be done afterwards and saved as `docs/reviews/claude-mask-review-2026-11-25.md`. Until
it is saved, the 10 affected results carried a "review pending" label.

**Review saved:** [claude-mask-review-2026-11-25.md](reviews/claude-mask-review-2026-11-25.md)
(supplied by Krishika, saved verbatim). Outcome: PASS with placeholder fixes.

**D-010 and D-011 (Krishika):** the placeholder fixes are applied (D-010), the
`independent_reviewer` column reads "none (DEV-001)" and the L270 reminder is restored
(D-011). The mask is re-frozen
(machine-readable: `design/fifo/freeze/deviation-DEV-001.json`):

| File | SHA-256 (frozen under D-011) | SHA-256 (as reviewed) |
|---|---|---|
| `design/fifo/mask/ovf_fifo-mask-DRAFT.json` | `64c7a9e6f25845521b9ad8164c3dff4d371f97fbd7c78c7c43c02e92540bbb59` | `78477cd41df36074c06aca31bfca3aae4de7a085980559480a35e2a08c180b0f` |
| `design/fifo/mask/ovf_fifo-mask-traceability-DRAFT.csv` | `25e15c1e38ab8ff8a4a4a1172c144feabfdad24aa00992ed5d0876a87418dfd8` | `3e443a68368b693e33608db0daa94ae52e8e61a9a6b7a55b55de834862360f92` |

Only `spec_version_sha256`, the status fields and the table's reviewer fields changed.
`tests/test_freeze_package.py` checks that undoing those changes gives the reviewed bytes.

**Label on every affected result:** "cleared under DEV-001 (non-independent review saved)".
Earlier runs keep their labels (evidence is append-only) and are superseded:
`run-20261124T193435Z` ("cleared under DEV-001 (non-independent mask review)", recorded
before any review existed) and `run-20261124T194216Z` ("cleared under DEV-001 — review
pending").

**What this does not do:**
- L271 and File 21 L32 remain **unmet**. Nobody signed section G.
- The review is not independent: Claude drafted the mask and the table (D-005), and the
  reviewer is Claude (claude.ai). Claude Code performed no sign-off review.
- The table's `independent_reviewer` column reads "none (DEV-001)". The `mask_reviewer`
  entry is the non-independent Claude review.
- It does not cover any other mask, or any changed bytes of this one. The runner re-checks
  the hashes and restores the provisional reason on a mismatch.

**Effect on claims:** report DEV-001 wherever results that use the mask are reported. Whether
F18 can pass with it is for the independent implementation auditor (L555 (5)).

**Ends when** an independent human reviewer signs the mask.

## DEV-002 — Implementation audit by an AI model (Protocol L555 (5))

> [02 L555] "(5) Independently re-audit the implementation, parser/assembler, Python 3.11 behavior and all mandatory fixture results."

**Owner decision (Krishika, recorded 24 Nov 2026 UTC; pasted into Claude Code):** "no
independent human implementation auditor is available. The implementation audit (L555 (5))
will be performed by a different AI model (ChatGPT, OpenAI), not the implementation author,
using dist/openvef-audit-bundle.zip (e0ee23ff…fa01) and docs/AUDIT-BRIEF.md. This is NOT a
human independent audit".

**Status: report received, as stated by Krishika (OpenAI GPT-6, 25 Nov 2026), but not yet
saved.** Its text was not supplied to Claude Code, so it is not under `docs/reviews/` and
Claude has not seen it; see the [note](reviews/implementation-audit-gpt6-2026-11-25-NOTE.md),
which also covers the bundle-hash difference. Step (5) is not marked done.

**Response (D-012):** A1-1 and A8-1 accepted and applied; limitations A2, A3, A5 and A9
accepted and recorded, not treated as defects. The corrected code has **not** been re-audited.
A later bundle (with evidence run-20261124T202333Z) replaces the zip in `dist/`; the audited
zip is in git at `9c89b1c`.

| Audit input | Identity |
|---|---|
| `dist/openvef-audit-bundle.zip` | SHA-256 `e0ee23ff6e29ec78c5310405edd6dd50d7625a8893c75bffdb0d6d026464fa01`, built from commit `5341c28` |
| `docs/AUDIT-BRIEF.md` | the copy inside that bundle |
| Evidence run | `run-20261124T195537Z` |

The bundle is not rebuilt for this record, so its documents predate DEV-002.

**What this does not do:**
- It does not mark step (5) done. Recording DEV-002 is not an audit result, and a report's
  findings must be settled before anyone relies on it.
- It opens no later gate. The LLM-call gate, step (6), stays closed, and F18 is not passed.
- It does not cover DEV-001: L271 stays unmet, and an AI auditor is not the independent
  human mask reviewer.
- It does not cover the document audit that `proposals/v1.3.7/` requires.

**Limits to disclose with the report:**
- The auditor is an AI model, and Claude, the implementation author, wrote the brief and
  the bundle script.
- ChatGPT had an earlier role in this project (assistance-log.md, retrospective entry):
  handoff text, reviews of Claude's reports and interpretation-note drafts, with its role in
  drafting the pack "not recorded". The auditor is a different model from the author, but
  not a stranger to the project.
- The report must state the exact model and version, and which checks were run rather than
  read. Checks that need Docker may not be possible for it.
- If a ChatGPT/OpenAI model is later evaluated in the study, the owners should disclose its
  role as auditor, as D-005 does for Claude.

**Ends when** an independent human auditor performs the implementation audit.
