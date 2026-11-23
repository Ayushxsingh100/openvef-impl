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
| Protocol §3.4 `SOURCE_SYNTAX_REJECT.column` rule (offset absent/null/<1 → 1; else CPython character column) | `src/openvef/source_ast.py` `syntax_reject`; `tests/test_source_ast.py` | M36 (unit vector) — NOT_IMPLEMENTED: disposition has no spec rule (A-012 open); earlier PASS in run-20261123T155910Z withdrawn. Column rule covered by unit tests only | Function implemented; F18 fixture blocked (A-012) |
| Protocol §3.4 evaluation order (2): driver.py before checker.py | `src/openvef/source_ast.py` `check_sources` | M16 — PASS in run-20261123T155910Z | Implemented (A-007 provisional) |
| Runner adapter: `{driver_source, checker_source}` inputs start at SOURCE_AST | `runner/run_f18.py` `execute` | M16, M29 — PASS in run-20261123T162630Z | Implemented (A-012 provisional) |
| File 30 §2 L21; Protocol §3.4 L133, evaluation order (3): non-ASCII identifier scan (NAME + ERRORTOKEN, UTF-8 byte column) | `src/openvef/import_policy.py` `scan_identifiers`; `tests/test_import_policy.py` | M35, M43, M44, M45, M46, M55, M56, M62, M63, M64 — PASS in run-20261123T162630Z; M57 passes through | Implemented (A-018 open: f-string identifiers not scanned on 3.11; A-019 open: lone CR raises) |
| File 30 §2 L16–L17; Protocol §3.4 L129: `ast.Import` precedence | `import_policy.py` `classify_import` | P13, P23, P31, P32, P33, P40, P43, P44, M08b, M21, M29 — PASS in run-20261123T162630Z | Implemented |
| File 30 §2 L18; Protocol §3.4 L131: `ast.ImportFrom` precedence | `import_policy.py` `classify_import_from` | P29a, P29b, P30, P34–P39, P41, P45–P48, M08a — PASS in run-20261123T162630Z | Implemented |
| File 30 §2 L19; Protocol §3.4 L133: prohibited built-in names, `builtins.<name>` | `import_policy.py` `find_prohibited_names` | P24a–d, M24, M34 — PASS in run-20261123T162630Z | Implemented (A-016 planned reading, confirmation pending) |
| File 30 §2 L20; Protocol §3.4 L133: GLOBAL_RANDOM_USE | `import_policy.py` `find_global_random_use` | M09, M22, M23 — PASS in run-20261123T162630Z | Implemented (A-017 planned reading, confirmation pending) |
| File 30 §3 L29; Protocol §3.4 L135: module-body statements | `import_policy.py` `classify_module_body` | P28, M04a, M04b — PASS in run-20261123T162630Z; M57 passes through | Implemented; unclassified cases are UnsettledSpec findings (A-015 open) |
| Protocol §3.4 evaluation order (3); File 30 §3 L27: IMPORT_POLICY stage order — driver.py then checker.py; identifier scan first; one source-order pass, first violation wins | `import_policy.py` `check_import_policy`; runner `run_source_ast` | M29, M44 — PASS in run-20261123T162630Z; 32 fixtures pass through to AST_SIGNATURE without false rejection | Implemented (A-013/A-014 decided as (c), Ayush pending; equal-key tie raises UnsettledSpec, A-013) |
| Protocol §3.4: multi-failure precedence (`events` inputs) | — | R13 and other R fixtures | Not started (input adapter undefined) |

Latest run: `evidence/run-20261123T162630Z` — commit 20d6683 (clean), CPython 3.11.18
(interpreter SHA-256 518f54d1…5356), jsonschema 4.26.0: 70 PASS, 0 FAIL, 74
NOT_IMPLEMENTED, 0 ERROR. 48 new PASS at IMPORT_POLICY versus run-20261123T160656Z.
32 fixtures pass IMPORT_POLICY and stop at the unimplemented AST_SIGNATURE stage (P01
among them). Only M36 is blocked on an ambiguity (A-012); no fixture hit an unsettled
SOURCE_AST or IMPORT_POLICY case. R03 (IMPORT_POLICY, `events` input) not run: no
adapter. Development run (Codespaces), not pinned-environment evidence; M16 and M29 rest
on provisional A-012 (M16 also A-007); IMPORT_POLICY order rests on A-013/A-014 with
Ayush's confirmation pending.

Evidence: see `evidence/run-*/summary.json`. Development runs are not pinned-environment
evidence until run on the owners' recorded interpreter.
