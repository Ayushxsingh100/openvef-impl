# OpenVEF implementation — rules for Claude Code

Baseline: OpenVEF Planning v1.3.6, ZIP SHA-256
`2e7008210a807868ad3d8a878820afa7cf1066f1c2b5b1cb437b911aa9b30c21`.
Owners: Krishika and Ayush Kumar Singh. Governing records: Owner Sign-off Pack
(Part 1 interpretation note, Part 2 build-method decision) and the Owner Decision Record.

## Scope
Only the limited hand-built FIFO scope of Protocol §18(4) is open. Build the parser,
assembler, harness, ledger and runner. Do NOT write: F6/F17 control checkers or drivers,
the directed suite, the FIFO specification, authoring-packet text, observation mask or
control mutants. Owners write those by hand; Claude may comment on them in prose only.

## Hard rules
1. The v1.3.6 pack under `baseline/` is read-only. Never edit, reformat or regenerate it.
2. Runtime: CPython 3.11.18 only (pinned). Record `sys.version` and the interpreter
   SHA-256 in every evidence run. Results from any other interpreter are not evidence.
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
  decision stays "owner review pending" until both owners review it.
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
- `evidence/` — run outputs, logs, hashes (append-only)
- `docs/` — traceability, ambiguities, assistance log
