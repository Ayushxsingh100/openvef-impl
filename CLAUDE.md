# OpenVEF implementation — rules for Claude Code

Baseline: OpenVEF Planning v1.3.6, ZIP SHA-256
`2e7008210a807868ad3d8a878820afa7cf1066f1c2b5b1cb437b911aa9b30c21`.
Owners: Krishika and Ayush Kumar Singh. Governing records: Owner Sign-off Pack
(Part 1 interpretation note, Part 2 build-method decision) and the Owner Decision Record.

## Scope
Only the limited hand-built FIFO scope of Protocol §18(4) is open. Build the parser,
assembler, harness, ledger and runner.

Owner decision D-005 (Krishika, 24 Nov 2026; Ayush's confirmation pending; Owner
Sign-off Pack Amendment D-005, Part 2 row 4 changed) makes these items AI-assisted.
Claude drafts them; the owners review and approve them:
- the FIFO design specification, port manifest and reset/legal-input rules;
- the other payload blocks (docs/fifo-owner-checklist.md item 17);
- the FIFO RTL;
- proposed frozen values and the trace schema (checklist items 7–12).
Everything Claude drafts under D-005 is marked DRAFT. Claude never marks it approved or
frozen; only the owners do that.

The observation mask may be drafted by Claude, but it must be signed by an independent
human mask reviewer (Protocol L271). Claude is never that reviewer.
Deviation DEV-001 (Krishika, 24 Nov 2026; docs/DEVIATIONS.md): no such reviewer is
available, so the owner accepted the FIFO mask and File 24 table at their frozen hashes
(D-010) with a saved, non-independent Claude review
(docs/reviews/claude-mask-review-2026-11-25.md). L271 stays unmet. Every affected result
carries "cleared under DEV-001 (non-independent review saved)";
never call the mask independently reviewed.

Still human-written. Do NOT write: F6/F17 control checkers or drivers, the directed
suite, control mutants. Owners write those by hand; Claude may comment on them in prose
only. Owner decision D-007 (Krishika, 24 Nov 2026; Ayush's confirmation pending) adds the
control drivers and checkers for F1–F5 and F7–F13 to this list (independence from the
harness author). Control mutants are RTL edits of `design/fifo/rtl/ovf_fifo.v` (D-007).
Owner artifacts go in `design/fifo/controls/` (see its README); Claude builds only the
harness that runs them and must not place content in their slots.

Disclosure (D-005), carried in docs/assistance-log.md: "The FIFO specification, RTL and
authoring-packet payloads were drafted by Claude (Anthropic) via Claude Code and reviewed
and approved by the owners. If any Claude model is among the models evaluated, this is
reported as a potential familiarity confound."

## Hard rules
1. The v1.3.6 pack under `baseline/` is read-only. Never edit, reformat or regenerate it.
2. Runtime (owner decision D-002a): the pinned interpreter is CPython 3.11.18 inside
   `python:3.11.18-slim` pinned by digest
   (`python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535`),
   built as `sandbox/Dockerfile`. Evidence runs only via `runner/run_f18_container.sh`,
   which runs the whole runner and every artifact in that image. Record `sys.version`,
   the interpreter SHA-256 and the image identity in every evidence run. Host Python is
   for development only; results from any other interpreter are not evidence.
3. Dependencies: only those pinned in `requirements.lock` with hashes. Adding or changing
   one needs owner approval.
4. No fixture-specific code: never branch on fixture IDs, file names under
   `41_F18_Fixture_Inputs/`, or expected outputs. Behaviour must follow the spec text.
5. No LLM or provider calls from any code, test or script.
6. When a rule in the pack is ambiguous, write it up in `docs/ambiguities.md` (exact
   quote, competing readings, what changes). Then, under the standing delegation below,
   choose the reading best supported by the pack text, mark it "decided by Claude under
   standing delegation, owner review pending", give the textual reason, implement it and
   keep building without asking. Never pick a reading silently, and never pick one
   because it makes a fixture pass: argue from the pack text only (rule 4).

## Standing delegation for unsettled specification cases
Given by Krishika (owner) in Claude Code on 23 Nov 2026: "resolve every unsettled
specification case yourself by choosing the reading best supported by the pack text,
record it in docs/ambiguities.md as 'decided by Claude under standing delegation, owner
review pending', add the rule to CLAUDE.md, and keep building without asking me. This
covers A-007 to A-019, the tie case, and all future cases."
- Covers spec interpretation only. It does not relax the Scope section or hard rules
  1–5, 7 and 8, and it does not cover dependency pins (D-001 stays with the owners).
- Given by Krishika alone; Ayush Kumar Singh's agreement is not recorded. Every such
  decision stays "owner review pending" until an owner reviews it.
- Governance rule D-008 (Krishika, 24 Nov 2026): decisions and approvals signed by Krishika
  alone take effect. Ayush's agreement is recorded once, as the single "Ayush ratification
  pending" entry in docs/AUDIT-READINESS.md, not on individual items. Claude never signs or
  approves for either owner. The independent mask reviewer's signature (L271) is still
  required and no owner signature replaces it (except as DEV-001 records, for the
  FIFO mask at its frozen hashes only).
- Owner decision D-009 (Krishika, 24 Nov 2026): every reading decided under this
  delegation and not yet owner-approved (A-007..A-012, A-013 tie, A-015..A-037, A-039,
  A-045..A-052, F15 case table) is approved by Krishika as decided, without itemised owner
  review. Later readings start as "owner review pending" again.
- Evidence runs that depend on a Claude-decided reading say so in `docs/traceability.md`,
  and do not count toward F18 until the owners have reviewed that reading.
7. Every commit message names the clause it implements, e.g. `File 30 §1: reject BOM`.
   Keep `docs/traceability.md` current: requirement → module → fixtures → evidence.
8. Never report a fixture as passed unless the runner executed it on the pinned
   interpreter and the evidence file records the result.

## Assistance log
Append one entry per Claude session to `docs/assistance-log.md`: date, tool and model,
scope, files touched. Human-written items: list each suggestion and whether it was
adopted, modified or rejected.

## Layout
- `baseline/` — extracted v1.3.6 pack (read-only, verified against `27_SHA256SUMS.txt`)
- `src/openvef/` — implementation
- `tests/` — unit tests that are not F18 fixtures
- `runner/` — F18 fixture runner
- `design/fifo/` — DRAFT FIFO design materials under D-005 (RTL, export script, proposed values)
- `evidence/` — run outputs, logs, hashes (append-only)
- `docs/` — traceability, ambiguities, assistance log
