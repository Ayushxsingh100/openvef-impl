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
6. When a rule in the pack is ambiguous, stop and write it up in `docs/ambiguities.md`
   (exact quote, competing readings, what changes). Do not pick a reading silently.
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
