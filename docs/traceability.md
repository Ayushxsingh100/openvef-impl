# Traceability: requirement → component → fixtures → evidence

| Requirement | Component | Fixtures | Status |
|---|---|---|---|
| File 36 "Fixture requirements" 1–6, L176: index hash, per-descriptor SHA-256/length, exact count, exact comparison | `runner/run_f18.py` | all 144 | Implemented |
| File 30 §1; Protocol §3.4 JSON Pointer rule: invalid UTF-8, BOM, prose, fences, trailing data, truncated JSON, duplicate keys → `SCHEMA_REJECT\|pointer=/` | `src/openvef/envelope.py` | P02, P03, P04, P05, P09, P10, P11b | Implemented |
| Protocol §3.4 stage map: provider truncation → `OUTPUT_TRUNCATED` | `src/openvef/envelope.py` | P11a | Implemented (A-001 provisional) |
| File 30 §1; Protocol §3.4: Draft 2020-12 schema validation and pointer sort | — (part 1b) | M30, P06a, P06b, P07, P08a–d | Not started (D-001) |
| File 30 §1: assumption clause-ID validation | — (part 1b) | P20 | Not started |
| Protocol §3.4: multi-failure precedence (`events` inputs) | — | R13 and other R fixtures | Not started (A-002) |

Evidence: see `evidence/run-*/summary.json`. Development runs are not pinned-environment
evidence until run on the owners' recorded interpreter.
