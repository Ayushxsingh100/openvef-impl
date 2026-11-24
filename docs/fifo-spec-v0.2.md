# FIFO specification v0.2 — DRAFT for owner review

**Status: DRAFT. Not approved, not frozen.** Drafted by Claude (Claude Opus 5.5, via Claude
Code) under owner decision D-005 (Krishika, 24 Nov 2026; Ayush's confirmation pending).
Only the owners can approve it or freeze it.

**Values:** depth 4 and width 8 were recommended by Claude in the claude.ai session and
adopted by Krishika (as stated by Krishika; that session is not in this repository).

**Disclosure (D-005):** "The FIFO specification, RTL and authoring-packet payloads were
drafted by Claude (Anthropic) via Claude Code and reviewed and approved by the owners. If
any Claude model is among the models evaluated, this is reported as a potential
familiarity confound."

**Changes from v0.1.** These come from a review by Claude (claude.ai), adopted by
Krishika on 24 Nov 2026:
1. `rst` is no longer a driver-vector key. Like `clk`, it is harness-owned: the harness
   drives it in the reset sequence and holds it at 0 afterwards (FIFO-004, FIFO-012,
   FIFO-040, FIFO-041, FIFO-042). The reading of File 30 check (a) that allows this is
   A-042 in [ambiguities.md](ambiguities.md), decided by Claude under the standing
   delegation, owner review pending.
2. FIFO-003 now uses the pack's wording for consumed inputs: "stable immediately before"
   the active edge (L217).
3. Registered almost-full is added as a second documented differentiator (FIFO-029,
   FIFO-034, FIFO-035), with threshold 3, worked-example rows and its effect on the
   predicate stated (FIFO-041).
4. A benchmark-overlap disclosure note (L468) is drafted separately for owner signature:
   [fifo-benchmark-overlap-disclosure-DRAFT.md](fifo-benchmark-overlap-disclosure-DRAFT.md).

This front matter is for the owners and is **not** payload text. The payload text starts
at the marker line below, and is split into three sections that map onto three File 38
payload blocks:
- `[Design specification]`
- `[Port manifest]`
- `[Reset and legal-input rules]`

`tests/test_fifo_spec.py` checks the payload text mechanically:
- the File 31 clause-ID extraction gives exactly the defined clause IDs;
- there are no near-match tokens;
- the executable predicate behaves as FIFO-041 states;
- the worked example agrees with a model of the clauses.

`tests/test_fifo_rtl.py` checks the DRAFT RTL against the worked example in the sandbox.

## What the pack requires, and where this draft meets it

Quotation format as in [fifo-owner-checklist.md](fifo-owner-checklist.md); checked by
`tests/test_doc_quotes.py`.

> [02 L202] "All MVP specs must be cycle-exact. Variable latency is out of scope"

Every output after an active edge is a function of the state before that edge and the
inputs consumed at it (FIFO-003, FIFO-032). Read data has one fixed latency (FIFO-021).

> [02 L217] "`inputs_consumed_at_edge_n`: top-level inputs stable immediately before active rising edge `n`;"

FIFO-003 defines the inputs at an active edge in these words.

> [02 L514] "Mutant changes FIFO data only while valid is low, where spec says data is don't-care"

`rd_valid` is the predicate signal. `rd_data` is don't-care exactly when `rd_valid` is 0
(FIFO-022).

> [02 L519] "Mutant changes `full`; driver changes next input based on sampled output"

`full` is a registered output (FIFO-028). The legal-input rules make a driver's next
`wr_en` depend on the sampled `full` (FIFO-041).

> [02 L202] "The ALU does not exercise reactive handshake, don't-care windows or invalid-pair logic."

There are two handshakes:
- the read handshake, `rd_en` then `rd_valid`/`rd_data` (FIFO-020, FIFO-021);
- the write-side backpressure, `full` constraining `wr_en` (FIFO-041).

`almost_full` gives a driver an earlier warning, but it places no constraint on inputs.

> [01 L99] "Candidate differentiators include a carefully specified simultaneous read/write-at-full policy and registered almost-full semantics for FIFO"

> [01 L99] "These must be selected and documented, not presumed novel."

Both candidates are now selected:
- the simultaneous read/write-at-full policy (FIFO-030), with the no-bypass rule at empty
  (FIFO-026);
- registered almost-full with threshold 3 (FIFO-029, FIFO-034, FIFO-035).

**Novelty is not claimed** for either; both are common FIFO features. L468 requires
benchmark overlap to be disclosed, and the disclosure note is drafted for owner signature.

> [02 L415] "Do not use unconstrained random input sequences that violate protocol legality (for example, undefined writes while full)."

A write while full without a read is illegal (FIFO-031, FIFO-041).

> [30 L83] "(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification"

**Scope decision for the predicate (FIFO-040).** The predicate is evaluated on one driver
vector together with the outputs sampled in the same row (A-041). That scope is part of
this AI-drafted specification (D-005), so it needs owner review.

> [02 L212] "Every non-`COMPLETE` return must be a dictionary with exactly the frozen top-level input-port keys"

The frozen driver-vector key set is `wr_en`, `wr_data`, `rd_en` (FIFO-004). `clk` and
`rst` are harness-owned (A-042).

| Checklist item | Where | Notes |
|---|---|---|
| 1 Design specification | FIFO-001 … FIFO-035 | cycle-exact, original wording |
| 2 Clause IDs | all `FIFO-nnn` | match `^[A-Z]{2,6}-[0-9]{3}$`; the manifest is not drafted yet (item 17) |
| 3 Port manifest | FIFO-004, FIFO-005 | driver-vector keys `wr_en`, `wr_data`, `rd_en`; `clk` and `rst` are harness-owned (A-042) |
| 4 Reset protocol | FIFO-010 … FIFO-013 | exact sequence; `reset_release_cycle` = 1 under the A-040 row convention |
| 5 Legal-input rules | FIFO-040 … FIFO-043 | executable Python 3.11 predicate with explicit scope |

**Owner approvals so far (D-006, Krishika, 24 Nov 2026; Ayush's confirmation pending):**
A-042, the almost-full threshold 3 and the top module name `ovf_fifo` are approved.
The specification stays DRAFT until both owners freeze it.

**Open points for owner review:**
1. Top module name `ovf_fifo` is a placeholder.
2. A-042: `rst` is harness-owned and not a driver-vector key. The competing reading keeps
   `rst` as a key that must always be 0 (v0.1).
3. The almost-full threshold, 3, is a choice; any value from 1 to 3 would be cycle-exact.
4. The observation mask (item 6) is not drafted. When it is, it must be signed by an
   independent human mask reviewer (L271). The mask needs FIFO-013 and FIFO-022.
5. Items 7–12 are proposed separately:
   [fifo-frozen-values-proposal-DRAFT.md](fifo-frozen-values-proposal-DRAFT.md).

<!-- PAYLOAD TEXT BELOW -->

## [Design specification]

### Size and timing

**FIFO-001** The FIFO stores up to 4 data words.

**FIFO-002** Each data word is 8 bits wide.

**FIFO-003** The design has one clock, `clk`. An *active edge* is a rising edge of `clk`.
The inputs *at* an active edge are the top-level input values stable immediately before
that edge. State and outputs change only at active edges, and between two active edges
every output holds its value. The outputs after an active edge are determined by the
state before that edge and the inputs at that edge, as the clauses below define.

**FIFO-006** The *occupancy* `c` is the number of words currently stored, from 0 to 4.

### Reading

**FIFO-020** At an active edge with `rst` = 0, a *read* occurs exactly when `rd_en` = 1
and `c` > 0 before the edge. A read removes the oldest stored word.

**FIFO-021** After an active edge, `rd_valid` = 1 exactly when a read occurred at that
edge. When `rd_valid` = 1, `rd_data` equals the word that read removed.

**FIFO-022** After any active edge at which `rd_valid` becomes or stays 0, including
reset edges, `rd_data` is don't-care: it carries no meaning, it may hold any value, and
nothing may depend on it. This is the only don't-care condition on an output after reset.
`rd_valid`, `full`, `almost_full` and `empty` are always meaningful.

**FIFO-023** A read request while empty is legal: if `rd_en` = 1 and `c` = 0 before an
active edge with `rst` = 0, no read occurs and `rd_valid` = 0 after that edge.

### Writing

**FIFO-024** At an active edge with `rst` = 0 and `wr_en` = 1, a *write* occurs exactly
when `c` < 4 before the edge, or a read occurs at the same edge. A write stores the value
of `wr_data` at that edge as the newest word. When `wr_en` = 0, `wr_data` is ignored.

**FIFO-025** Words are read in the order they were written. Each stored word is read at
most once.

**FIFO-026** No bypass: a word written at an active edge cannot be read at that same
edge; the earliest edge that can read it is the next active edge. In particular, if
`c` = 0, `wr_en` = 1 and `rd_en` = 1 at an active edge with `rst` = 0, the write occurs,
no read occurs, `rd_valid` = 0 after the edge, and `c` = 1.

### Status outputs

**FIFO-027** After an active edge with `rst` = 0, `c` equals its value before the edge,
plus 1 if a write occurred, minus 1 if a read occurred.

**FIFO-028** After every active edge, `full` = 1 exactly when `c` = 4, and `empty` = 1
exactly when `c` = 0.

**FIFO-029** After every active edge, `almost_full` = 1 exactly when `c` ≥ 3. The
threshold is 3 words.

### Simultaneous read and write at full

**FIFO-030** If `c` = 4, `rd_en` = 1 and `wr_en` = 1 at an active edge with `rst` = 0,
then at that edge the oldest word is read and the new word is written. After the edge:
- `rd_valid` = 1, and `rd_data` is the oldest word;
- `c` = 4, and `full` stays 1. `full` never shows 0 for this case.

**FIFO-031** A write request while full without a read (`c` = 4, `wr_en` = 1, `rd_en` = 0
at an active edge with `rst` = 0) is an illegal input (FIFO-041). This specification
does not define the FIFO's behaviour for it.

### Latency

**FIFO-032** There is no variable latency. A read appears on `rd_valid` and `rd_data`
after the same active edge at which it occurs. A write affects `full`, `almost_full`,
`empty` and later reads from the active edge at which it occurs onward.

### Registered almost-full

**FIFO-034** `almost_full` is registered: it is computed from `c` *after* the active edge
(FIFO-029), and it changes only at active edges. It neither anticipates nor lags:
- a write that takes `c` from 2 to 3 sets `almost_full` = 1 in the outputs after that
  same edge, not earlier;
- a read that takes `c` from 3 to 2 clears it in the outputs after that same edge, not
  later.

**FIFO-035** When a read and a write occur at the same active edge, `c` is unchanged, so
`almost_full` is unchanged. In particular, at `c` = 3 it stays 1, and at `c` = 4
(FIFO-030) it stays 1.

### Worked example

All values are after the listed active edge. `rst` = 0 throughout. `-` marks a don't-care
or ignored value. Data values are hexadecimal here; on the ports they are 8-bit binary
strings (FIFO-005). `af` is `almost_full`.

| Edge | `wr_en` | `wr_data` | `rd_en` | `c` | `rd_valid` | `rd_data` | `full` | `af` | `empty` |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 11 | 0 | 1 | 0 | - | 0 | 0 | 0 |
| 2 | 1 | 22 | 1 | 1 | 1 | 11 | 0 | 0 | 0 |
| 3 | 1 | 33 | 0 | 2 | 0 | - | 0 | 0 | 0 |
| 4 | 1 | 44 | 0 | 3 | 0 | - | 0 | 1 | 0 |
| 5 | 1 | 55 | 0 | 4 | 0 | - | 1 | 1 | 0 |
| 6 | 1 | 66 | 1 | 4 | 1 | 22 | 1 | 1 | 0 |
| 7 | 0 | - | 1 | 3 | 1 | 33 | 0 | 1 | 0 |
| 8 | 0 | - | 1 | 2 | 1 | 44 | 0 | 0 | 0 |
| 9 | 0 | - | 1 | 1 | 1 | 55 | 0 | 0 | 0 |
| 10 | 1 | 77 | 1 | 1 | 1 | 66 | 0 | 0 | 0 |
| 11 | 0 | - | 1 | 0 | 1 | 77 | 0 | 0 | 1 |
| 12 | 1 | 88 | 1 | 1 | 0 | - | 0 | 0 | 0 |
| 13 | 0 | - | 1 | 0 | 1 | 88 | 0 | 0 | 1 |
| 14 | 0 | - | 1 | 0 | 0 | - | 0 | 0 | 1 |
| 15 | 1 | 99 | 0 | 1 | 0 | - | 0 | 0 | 0 |
| 16 | 1 | AA | 0 | 2 | 0 | - | 0 | 0 | 0 |
| 17 | 1 | BB | 0 | 3 | 0 | - | 0 | 1 | 0 |
| 18 | 1 | CC | 1 | 3 | 1 | 99 | 0 | 1 | 0 |
| 19 | 0 | - | 1 | 2 | 1 | AA | 0 | 0 | 0 |

Edge 1 starts from `c` = 0 after reset. Edge 6 is FIFO-030. Edge 12 is FIFO-026.
Edge 14 is FIFO-023. Edges 4, 17 and 8, 19 are FIFO-034. Edges 6 and 18 are FIFO-035.

## [Port manifest]

**FIFO-004** Top module `ovf_fifo` has exactly these ports:

| Port | Direction | Width | Driven by |
|---|---|---|---|
| `clk` | input | 1 | the harness clock only |
| `rst` | input | 1 | the harness only: the reset sequence, then held at 0 |
| `wr_en` | input | 1 | reset sequence, then driver vectors |
| `wr_data` | input | 8 | reset sequence, then driver vectors |
| `rd_en` | input | 1 | reset sequence, then driver vectors |
| `rd_valid` | output | 1 | the FIFO |
| `rd_data` | output | 8 | the FIFO |
| `full` | output | 1 | the FIFO |
| `almost_full` | output | 1 | the FIFO |
| `empty` | output | 1 | the FIFO |

Every driver vector has exactly the keys `wr_en`, `wr_data` and `rd_en`. `clk` and
`rst` are never keys, because the harness owns them.

**FIFO-005** Each port value is a string of `0` and `1` whose length equals the port's
width. A multi-bit value is written most significant bit first, so the first character of
`wr_data` or `rd_data` is bit 7.

## [Reset and legal-input rules]

### Reset

**FIFO-010** Reset is synchronous and active high. At any active edge where `rst` = 1:
- `c` becomes 0, and all stored words are discarded;
- `wr_en`, `wr_data` and `rd_en` are ignored;
- after the edge, `rd_valid` = 0, `full` = 0, `almost_full` = 0 and `empty` = 1, and
  `rd_data` is don't-care (FIFO-022).

**FIFO-011** The reset sequence is two input vectors, applied by the harness at two
consecutive active edges. Each vector has `rst` = 1, `wr_en` = 0, `wr_data` = 00000000
and `rd_en` = 0. Reset is released after the second of these edges. The driver's first
vector is applied at the next active edge.

**FIFO-012** After the reset sequence, the harness holds `rst` at 0 for the rest of the
run. `rst` is not a driver-vector key, and a driver cannot assert reset.

**FIFO-013** Before the first reset edge, the state and every output are unspecified.
From the outputs after the first reset edge onward, every output is specified, subject to
FIFO-022.

### Legal inputs

**FIFO-040** Scope of the legal-input predicate. It is evaluated for each driver vector
`V`, together with the outputs `S` that were sampled after the most recent active edge,
which are the outputs the driver was given in the same step. The predicate does not cover:
- the key set, the widths and the symbols of `V`, which are checked before it;
- reset-sequence vectors (FIFO-011);
- `rst`, which is not in `V` (FIFO-012).

Because `full` is registered (FIFO-028), `S` gives `full` = 1 exactly when `c` = 4 at the
edge where `V` is applied.

**FIFO-041** A driver vector is legal exactly when it does not have `wr_en` = 1 and
`rd_en` = 0 while the sampled `full` = 1. Nothing else is restricted:
- a read while empty is legal (FIFO-023);
- a write together with a read at full is legal (FIFO-030);
- any `wr_data` is legal;
- `almost_full` places no constraint: any vector is legal whatever its value.

**FIFO-042** The predicate as an executable Python 3.11 function. `vector` maps the three
driver-vector keys, and `sampled` maps the five output ports, to their strings
(FIFO-005). It returns `True` for a legal vector.

```python
def legal_input(vector: dict[str, str], sampled: dict[str, str]) -> bool:
    return not (sampled["full"] == "1" and vector["wr_en"] == "1" and vector["rd_en"] == "0")
```

**FIFO-043** The same legal-input rules are the input assumptions of the
bounded-equivalence check: after reset, `rst` = 0, and no edge has `wr_en` = 1 and
`rd_en` = 0 while `c` = 4.
