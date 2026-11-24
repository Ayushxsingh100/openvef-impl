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

**Frozen under DEV-001**, at the hashes of OWNER-FREEZE-PACKAGE.md section G
(machine-readable: `design/fifo/freeze/deviation-DEV-001.json`):

| File | SHA-256 |
|---|---|
| `design/fifo/mask/ovf_fifo-mask-DRAFT.json` | `78477cd41df36074c06aca31bfca3aae4de7a085980559480a35e2a08c180b0f` |
| `design/fifo/mask/ovf_fifo-mask-traceability-DRAFT.csv` | `3e443a68368b693e33608db0daa94ae52e8e61a9a6b7a55b55de834862360f92` |

**Label on every affected result:** "cleared under DEV-001 (non-independent mask review)".

**What this does not do:**
- L271 and File 21 L32 remain **unmet**. Nobody signed section G, and the mask table's
  own reviewer cells still say unsigned.
- "Claude's review" is not independent: Claude drafted the mask and the table (D-005).
  The claude.ai review is as stated by Krishika; no record of it is in this repository.
  Claude Code performed no sign-off review.
- It does not cover any other mask, or any changed bytes of this one. The runner re-checks
  the hashes and restores the provisional reason on a mismatch.

**Known limits of freezing at the current hashes:** in the table, `spec_version_sha256`
still reads `TO_FREEZE` and `review_status` still reads `DRAFT_UNSIGNED`; the mask JSON
also says `TO_FREEZE`. Filling them in would change the hashes.

**Effect on claims:** report DEV-001 wherever results that use the mask are reported. Whether
F18 can pass with it is for the independent implementation auditor (L555 (5)).

**Ends when** an independent human reviewer signs the mask.
