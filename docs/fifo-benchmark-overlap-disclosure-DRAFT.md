# FIFO benchmark-overlap disclosure — DRAFT for owner signature

**Status: DRAFT.** Drafted by Claude (Claude Opus 5.5, via Claude Code) under owner
decision D-005, 24 Nov 2026. It takes effect only when both owners sign it below. It
covers the FIFO specification v0.2 ([fifo-spec-v0.2.md](fifo-spec-v0.2.md)).

## Why this note exists

> [02 L468] "| Design semantics | Independently authored, cycle-exact specs with distinctive corner cases | TO FREEZE; disclose benchmark overlap |"

> [01 L99] "FIFO and UART are not novel benchmark families."

> [01 L99] "OpenVEF must author independently specified, distinctive cycle-exact semantics, not reuse public benchmark RTL, masks or test sequences without explicit permission and attribution."

## Known public benchmarks with FIFO designs (as recorded in the pack)

The pack names these; this note relies only on what the pack records about them.

> [01 L99] "GateTruth includes FIFO/UART tasks; DVBench includes a FIFO example; and a separate data-integrity work reviewed in Step 3 uses asynchronous FIFO and UART-transmitter examples."

> [01 L99] "The TechRxiv checker-gap preprint was mentioned in an earlier note as containing a FIFO, but that detail was not verified during the abstract-only access recorded in the provenance log and is not relied upon here."

The drafting sessions for this specification did not open, read or copy the specification,
RTL, masks or test sequences of any of these benchmarks. Their FIFO interfaces and
semantics have not been compared with this specification. **That comparison is an open
owner task**, and its result should be added here before signature.

## Overlap statement (draft wording)

> The OpenVEF FIFO is a single-clock, synchronous-reset, 4-entry by 8-bit queue with a
> read handshake (`rd_en` → `rd_valid`/`rd_data`), registered `full`, `almost_full`
> (threshold 3) and `empty` status outputs, a simultaneous read/write-at-full policy and
> no bypass at empty. Each of these features is common in published and textbook FIFO
> designs, and in FIFO tasks in public benchmarks including those named above. **No
> feature is claimed to be novel.** The two differentiators named in the project charter
> (simultaneous read/write at full; registered almost-full) were selected and specified
> cycle-exactly for this project, but not presumed novel (Charter L99). The specification
> text, clause structure, worked example and legal-input predicate were written for this
> project and do not reuse public benchmark RTL, masks or test sequences.

## Authorship disclosure (D-005)

> The FIFO specification, RTL and authoring-packet payloads were drafted by Claude
> (Anthropic) via Claude Code and reviewed and approved by the owners. If any Claude model
> is among the models evaluated, this is reported as a potential familiarity confound.

An AI model may reproduce patterns from its training data, which includes public FIFO
designs. The overlap statement above therefore covers patterns, not just deliberate
reuse. The owners may want to weigh this against L468's "Independently authored".

## Owner signature

| Owner | Decision (sign / amend / reject) | Date |
|---|---|---|
| Krishika | | |
| Ayush Kumar Singh | | |
