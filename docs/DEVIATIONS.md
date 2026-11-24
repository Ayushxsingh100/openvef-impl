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

**D-010 (Krishika):** the placeholder fixes are applied and the mask is re-frozen
(machine-readable: `design/fifo/freeze/deviation-DEV-001.json`):

| File | SHA-256 (frozen under D-010) | SHA-256 (as reviewed) |
|---|---|---|
| `design/fifo/mask/ovf_fifo-mask-DRAFT.json` | `ea877da0046541550a23cc2beb69c2b9960ede422727ee080e1e00827602acbe` | `78477cd41df36074c06aca31bfca3aae4de7a085980559480a35e2a08c180b0f` |
| `design/fifo/mask/ovf_fifo-mask-traceability-DRAFT.csv` | `af2a846174bead3924d10212b36bf3c46cc41380811bf1d84f636e17caf6c97e` | `3e443a68368b693e33608db0daa94ae52e8e61a9a6b7a55b55de834862360f92` |

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
- The table's `independent_reviewer` column is filled as D-010 instructs. Its value says
  "non-independent"; the column name must not be quoted as meaning an independent review.
- It does not cover any other mask, or any changed bytes of this one. The runner re-checks
  the hashes and restores the provisional reason on a mismatch.

**Effect on claims:** report DEV-001 wherever results that use the mask are reported. Whether
F18 can pass with it is for the independent implementation auditor (L555 (5)).

**Ends when** an independent human reviewer signs the mask.
