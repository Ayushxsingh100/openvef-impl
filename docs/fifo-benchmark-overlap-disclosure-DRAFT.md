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

The drafting sessions for spec v0.1 and v0.2 did not open, read or copy the
specification, RTL, masks or test sequences of any of these benchmarks.

## Comparison (24 Nov 2026, after spec v0.2 was drafted)

**Sources.** Fetched on 24 Nov 2026 from public pages. The extracts were made by a
web-fetch helper and quoted to Claude; the owners should re-check them against the
sources before signing.
- **GateTruth** (arXiv:2608.12635): the paper names a Tier 2 "synchronous FIFO" task but
  gives no interface. The task itself is in the public repository
  `github.com/meetbhadra701-cloud/GateTruth`, `tasks/t2_sync_fifo/` (`spec.md`,
  `interface.sv`, `ref/ref.sv` read; `formal/` and `tb/` not read).
- **DVBench** (arXiv:2611.25066, HTML full text; Appendix E not read): the worked example
  is task dv-009, module `cva6_fifo_v3`.
- **LLM-Aided Verification Gap Detection** (TechRxiv,
  doi:10.36227/techrxiv.177069683.39144593/v1): **not retrieved**; techrxiv.org returned
  HTTP 403. The pack itself disagrees about whether its FIFO is verified (PD-24).
- **Independent data-integrity work** (File 10 §3.12): an *asynchronous* FIFO,
  per File 10 L218. Not retrieved; no interface detail is known.

| Feature | OpenVEF v0.2 (DRAFT) | GateTruth `t2_sync_fifo` | DVBench dv-009 `cva6_fifo_v3` |
|---|---|---|---|
| Clocking | single clock | single clock ("Synchronous first-word-fall-through FIFO") | single clock, rising edge |
| Reset | synchronous, active-high `rst` | **same**: "Synchronous, active-high" `rst` | asynchronous active-low `rst_ni`, plus synchronous `flush_i` |
| Depth × width | 4 × 8 | parameters, defaults DEPTH 8, WIDTH 8 (public bench uses 8 × 8) | 8 × 32 |
| Port names | `clk`, `rst`, `wr_en`, `wr_data`, `rd_en`, `rd_valid`, `rd_data`, `full`, `almost_full`, `empty` | `clk`, `rst`, `wr_en`, `rd_en`, `din`, `dout`, `full`, `empty`: **six names shared** (`clk`, `rst`, `wr_en`, `rd_en`, `full`, `empty`) | `clk_i`, `rst_ni`, `flush_i`, `push_i`, `pop_i`, `data_i`, `data_o`, `usage_o`, `full_o`, `empty_o`, `testmode_i` |
| Read data | registered: `rd_data` with `rd_valid` after the read edge; don't-care when `rd_valid` = 0 | first-word-fall-through: `dout` combinational from memory, "valid whenever `empty == 0`"; no valid port | combinational head (`data_o`); fall-through when empty |
| Read + write at empty | write only, no bypass (FIFO-026) | **same**: "only the write is performed" | fall-through: the pushed word is consumed in the same cycle |
| Read + write at full | both; `full` stays 1 (FIFO-030) | "only the pop is performed" | push at full is prohibited |
| Write while full without read | illegal input (FIFO-031, FIFO-041) | legal, ignored | prohibited |
| Read while empty | legal, no effect (FIFO-023) | legal, ignored | prohibited |
| Almost-full | registered, threshold 3 (FIFO-029, FIFO-034) | none | none (`usage_o` count instead) |
| Flags | registered | combinational from the count register | not stated |

**Findings.**
1. **Closest overlap: GateTruth `t2_sync_fifo`.** It has the same reset style and six
   identical port names, and the same rule for read+write at empty (write only). Its data
   path is different (first-word-fall-through and combinational, versus registered with
   a valid flag), as are its read+write at full (pop only, versus both) and its
   write-while-full rule (ignored, versus illegal). It has no almost-full.
2. **DVBench dv-009** differs in reset, interface, read path, the behaviour at empty, and
   the legality of operations at full and empty. Only the family-level features are
   shared.
3. **Neither benchmark** has a registered almost-full flag or a legal pass-through write
   at full. These are the two v0.2 differentiators. Absence from these two benchmarks
   does not make them novel (Charter L99): they are common in FIFO designs generally.
4. The port names `wr_en`, `rd_en`, `full`, `empty`, `clk` and `rst` are conventional, and
   they also appear in GateTruth. The owners may want to rename them, to reduce
   identifier-level overlap with a public benchmark that models may have seen in
   training (File 12 L87), or keep them and disclose. This is an owner decision; v0.2 is
   unchanged.

**Owner decision on finding 4 (Krishika, 24 Nov 2026; Ayush's confirmation pending):**
**disclose; do not rename the ports.** Both owners sign it in
[OWNER-FREEZE-PACKAGE.md](OWNER-FREEZE-PACKAGE.md).

## Overlap statement (draft wording)

> The OpenVEF FIFO is a single-clock, synchronous-reset, 4-entry by 8-bit queue with a
> read handshake (`rd_en` → `rd_valid`/`rd_data`), registered `full`, `almost_full`
> (threshold 3) and `empty` status outputs, a simultaneous read/write-at-full policy and
> no bypass at empty. Each of these features is common in published and textbook FIFO
> designs, and in FIFO tasks in public benchmarks including those named above. The
> closest public task found, GateTruth `t2_sync_fifo`, shares the synchronous active-high
> reset, six port names (`clk`, `rst`, `wr_en`, `rd_en`, `full`, `empty`) and the
> write-only rule for simultaneous read and write at empty. It differs in its read path,
> its full-side policy and the absence of almost-full. **No feature is claimed to be
> novel.** The two differentiators named in the project charter
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
