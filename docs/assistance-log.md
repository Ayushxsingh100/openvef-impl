# LLM assistance log

Rule (Owner Sign-off Pack, Part 1 §3 and Part 2): one entry per session; itemised
suggestions only for human-written items. Retrospective entries document history only.

## Retrospective entries (before adoption on 23 Nov 2026)

| Date | Tool / model | Scope | Files / artifacts | Outcome |
|---|---|---|---|---|
| Not recorded (before 23 Nov 2026) | ChatGPT (model not recorded) | Owners to complete. Known from this chat: handoff text, ZIP re-verification, reviews of Claude's reports, interpretation-note drafts. Role in drafting the pack itself: not recorded | Owners to complete | Not recorded |
| Not recorded (before 23 Nov 2026) | Claude (separate sessions) | Independent document audits of earlier pack releases and of v1.3.6 | Audit exports (files 07, 08, 14, 26, 28, 29, 39, 43, 54, 59, 61, 62); v1.3.6 audit doc | Audits recorded in the pack |
| 23 Nov 2026, 11:00–13:45 IST | Claude Opus 5.5 (claude.ai) | Read decision record and audit; verified ZIP and manifest; clause analysis; reviewed interpretation-note drafts; TEEP/prototype advice; drafted sign-off pack | Sign-off pack (new doc); Owner Decision Record (boxes marked on owners' written instruction) | Pack files unchanged |

## Entries after adoption

| Date | Tool / model | Scope | Files | Outcome |
|---|---|---|---|---|
| 23 Nov 2026, from 13:55 IST | Claude Opus 5.5 (claude.ai workspace, acting under Part 2 row 1) | Session 1: repository setup, verified baseline copy, F18 runner, parser step 1a (envelope) | CLAUDE.md, src/openvef/envelope.py, runner/run_f18.py, docs/* | AI-built canonical code (Part 2 row 1) |
| 23 Nov 2026 (session 2, Codespaces) | Claude Code, Claude Opus 5.5 (claude-opus-5-5), acting under Part 2 row 1 | Parser step 1b: schema validation, JSON Pointer selection, clause-ID check; D-001 pin; dev evidence run | requirements.in, requirements.lock, .gitignore, src/openvef/schema.py, src/openvef/envelope.py (docstring), runner/run_f18.py, tests/test_schema.py, docs/ambiguities.md (D-001, A-004–A-006), docs/traceability.md, docs/assistance-log.md, evidence/run-20261123T153734Z | AI-built canonical code (Part 2 row 1). No human-written items touched |
| 23 Nov 2026 (session 3, Codespaces) | Claude Code, Claude Opus 5.5 (claude-opus-5-5) | Pre-push follow-ups: D-001 status corrected to pending (Ayush's confirmation outstanding); A-006 code reviewed, no behaviour change | docs/ambiguities.md (D-001), docs/traceability.md, docs/assistance-log.md | Docs only. No code or human-written items touched |
