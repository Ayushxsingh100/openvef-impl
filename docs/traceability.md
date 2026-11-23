# Traceability: requirement → component → fixtures → evidence

| Requirement | Component | Fixtures | Status |
|---|---|---|---|
| File 36 "Fixture requirements" 1–6, L176: index hash, per-descriptor SHA-256/length, exact count, exact comparison | `runner/run_f18.py` | all 144 | Implemented |
| File 30 §1; Protocol §3.4 JSON Pointer rule: invalid UTF-8, BOM, prose, fences, trailing data, truncated JSON, duplicate keys → `SCHEMA_REJECT\|pointer=/` | `src/openvef/envelope.py` | P02, P03, P04, P05, P09, P10, P11b | Implemented |
| Protocol §3.4 stage map: provider truncation → `OUTPUT_TRUNCATED` | `src/openvef/envelope.py` | P11a | Implemented (A-001 provisional) |
| File 30 §1 L7; File 30 §1 / Protocol §3.4 JSON Pointer selection: Draft 2020-12 validation (file 34, SHA-256 checked), all errors, RFC 6901 tokens, parent pointer for `required`/`additionalProperties`, 4-level sort, first pointer | `src/openvef/schema.py` `validate_schema`; `tests/test_schema.py` | P06a, P06b, P07, P08a (raw inputs) — PASS in run-20261123T153734Z. P08b–d, M30 (`response_object`) not run: A-002 | Implemented (D-001 decided; A-006 provisional) |
| File 30 §1 L9; Protocol §3.4 clause-ID pointer `/assumptions/<index>/clause_id` | `src/openvef/schema.py` `validate_clause_ids`; `tests/test_schema.py` | P20 — PASS in run-20261123T153734Z. P21 (`response_object`) not run: A-002 | Implemented (A-004 open, A-005 provisional) |
| Protocol §3.4: multi-failure precedence (`events` inputs) | — | R13 and other R fixtures | Not started (A-002) |

Latest run: `evidence/run-20261123T153734Z` — commit 73782ad, CPython 3.11.18
(interpreter SHA-256 518f54d1…5356), jsonschema 4.26.0: 13 PASS, 0 FAIL, 131
NOT_IMPLEMENTED, 0 ERROR. P01 passes PARSE_SCHEMA and stops at the unimplemented next stage.

Evidence: see `evidence/run-*/summary.json`. Development runs are not pinned-environment
evidence until run on the owners' recorded interpreter.
