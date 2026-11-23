# Traceability: requirement → component → fixtures → evidence

| Requirement | Component | Fixtures | Status |
|---|---|---|---|
| File 36 "Fixture requirements" 1–6, L176: index hash, per-descriptor SHA-256/length, exact count, exact comparison | `runner/run_f18.py` | all 144 | Implemented |
| File 30 §1; Protocol §3.4 JSON Pointer rule: invalid UTF-8, BOM, prose, fences, trailing data, truncated JSON, duplicate keys → `SCHEMA_REJECT\|pointer=/` | `src/openvef/envelope.py` | P02, P03, P04, P05, P09, P10, P11b — PASS in run-20261123T155910Z | Implemented (A-003 decided, Ayush pending) |
| Protocol §3.4 stage map: provider truncation → `OUTPUT_TRUNCATED` | `src/openvef/envelope.py` | P11a — PASS in run-20261123T155910Z | Implemented (A-001 decided, Ayush pending) |
| File 30 §1 L7; File 30 §1 / Protocol §3.4 JSON Pointer selection: Draft 2020-12 validation (file 34, SHA-256 checked), all errors, RFC 6901 tokens, parent pointer for `required`/`additionalProperties`, 4-level sort, first pointer | `src/openvef/schema.py` `validate_schema`; `tests/test_schema.py` | P06a, P06b, P07, P08a (raw); P08b–d, M30 (`response_object`) — all PASS in run-20261123T155910Z | Implemented (D-001 pending Ayush's confirmation; A-006 decided, Ayush pending) |
| File 30 §1 L9; Protocol §3.4 clause-ID pointer `/assumptions/<index>/clause_id` | `src/openvef/schema.py` `validate_clause_ids`; `tests/test_schema.py` | P20 — PASS in run-20261123T155910Z. P21 passes PARSE_SCHEMA and SOURCE_AST, stops at IMPORT_POLICY (not implemented) | Implemented (A-004, A-005 decided, Ayush pending) |
| Protocol §3.4 evaluation order (1); A-002: `response_object` input starts at schema validation | `runner/run_f18.py` `execute` | P08b–d, M30, P12a/b, P25a/b and others | Implemented (A-002 decided, Ayush pending) |
| Protocol §3.4 stage map "Empty/whitespace-only source"; File 30 §3 L27 | `src/openvef/source_ast.py` `check_source`; `tests/test_source_ast.py` | P12a, P12b, M16 — PASS in run-20261123T155910Z | Implemented for space/tab/LF/CR; other whitespace raises UnsettledSpec (A-010 open) |
| Protocol §3.4 stage map "Invalid UTF-8/BOM or syntax parse error"; `ast.parse` on CPython 3.11.18 | `src/openvef/source_ast.py` `check_source` | P25a, P25b — PASS in run-20261123T155910Z | Implemented; leading U+FEFF, lone surrogates, SyntaxError without lineno and non-SyntaxError exceptions raise UnsettledSpec (A-008, A-009, A-011 open) |
| Protocol §3.4 `SOURCE_SYNTAX_REJECT.column` rule (offset absent/null/<1 → 1; else CPython character column) | `src/openvef/source_ast.py` `syntax_reject`; `tests/test_source_ast.py` | M36 (unit vector) — PASS in run-20261123T155910Z | Implemented (runner adapter A-012 provisional) |
| Protocol §3.4 evaluation order (2): driver.py before checker.py | `src/openvef/source_ast.py` `check_sources` | M16 — PASS in run-20261123T155910Z | Implemented (A-007 provisional) |
| Runner adapter: `{driver_source, checker_source}` inputs start at SOURCE_AST | `runner/run_f18.py` `execute` | M16; M29 (stops at IMPORT_POLICY) | Implemented (A-012 provisional) |
| Protocol §3.4: multi-failure precedence (`events` inputs) | — | R13 and other R fixtures | Not started (input adapter undefined) |

Latest run: `evidence/run-20261123T155910Z` — commit e5eb9c0 (clean), CPython 3.11.18
(interpreter SHA-256 518f54d1…5356), jsonschema 4.26.0: 23 PASS, 0 FAIL, 121
NOT_IMPLEMENTED, 0 ERROR. No fixture was blocked by an UnsettledSpec. 81 fixtures pass
SOURCE_AST and stop at the unimplemented IMPORT_POLICY stage (P01 among them). Development
run (Codespaces), not pinned-environment evidence; M16 and M36 passes rest on provisional
A-012, M16 also on A-007.

Evidence: see `evidence/run-*/summary.json`. Development runs are not pinned-environment
evidence until run on the owners' recorded interpreter.
