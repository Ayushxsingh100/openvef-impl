# OpenVEF implementation audit report

Auditor model and version: OpenAI GPT-6
Operator (human who ran the audit): Not identified in the supplied bundle or instruction
Date (UTC): 2026-11-25
Not a Claude model, not the implementation author: yes
Bundle SHA-256: `e0ee23ff6e29ec78c5310405edd6dd50d7625a8893c75bffdbd0d026464fa01`  
MANIFEST.sha256 verified: yes (274 entries; 0 missing, malformed or mismatched)
Environment (Python version, Docker available, tools): CPython 3.13.5; Docker unavailable (`docker` executable absent); `sha256sum`, Python standard library, `python3 -I` test execution. The pinned CPython 3.11.18 image could not be started or independently inspected. No bundle files were edited.

## Summary

| Area | Verdict (PASS or FINDINGS) | Blocker | Major | Minor | Limitation | Method (ran / read) |
|---|---|---:|---:|---:|---:|---|
| A1. Fixture runner | FINDINGS | 1 | 0 | 0 | 0 | ran / read |
| A2. Parser and static stages | FINDINGS | 0 | 0 | 0 | 1 | ran / read |
| A3. Runtime, simulation and checker stages | FINDINGS | 0 | 0 | 0 | 1 | ran / read |
| A4. Serializer, assembler, lifecycle | PASS | 0 | 0 | 0 | 0 | ran / read |
| A5. Evidence run | FINDINGS | 0 | 0 | 0 | 1 | ran / read |
| A6. Freeze record | PASS | 0 | 0 | 0 | 0 | ran / read |
| A7. Deviations and mask | PASS | 0 | 0 | 0 | 0 | read (plus unit test) |
| A8. Readings | FINDINGS | 0 | 1 | 0 | 0 | ran / read |
| A9. Sandbox | FINDINGS | 0 | 0 | 0 | 1 | read |
| A10. Claims and disclosure | PASS | 0 | 0 | 0 | 0 | read |

## Findings

### A1-1 [BLOCKER] Fixture-specific dispatch by singleton input shapes

File and line:
- `runner/run_f18.py:298-299` dispatches the `{source_file, syntax_error}` shape to the M36 column-rule adapter.
- `runner/run_f18.py:355-359` has a separate branch for `{driver_return, legal_input_predicate}` and embeds the FIFO-042 disagreement and blocking explanation.
- The corresponding fixture inputs are `baseline/OpenVEF_Planning_v1_3_6/41_F18_Fixture_Inputs/M36.json` and `M27.json`; each input-key shape occurs in only one descriptor in the 144-fixture index.

Pack / implementation rule (exact, file and line):
- `CLAUDE.md:55-56`: “No fixture-specific code: never branch on fixture IDs, file names under `41_F18_Fixture_Inputs/`, or expected outputs. Behaviour must follow the spec text.”
- The audit brief §4 A1 additionally explicitly requires no fixture-specific code “directly or by input shapes that occur in only one fixture.”
- Catalog File 36, lines 22-26, says every descriptor is mandatory and the fixture index, descriptor hash, expected object and exact count must agree.

Check or input:
- Counted input-key sets across all 144 indexed descriptors. There are 27 distinct shapes; the M36 and M27 shapes each occur exactly once.
- Read the corresponding `dispatch` branches and compared them with M36/M27 descriptors and the records in the audited run.

Expected:
- The runner's behavior should be derived from generally specified input contracts, without a branch whose only matching input is one mandatory fixture. Where the pack does not define an input contract, the runner should not manufacture a fixture-specific route or outcome.

Actual:
- M36's unique shape is routed to `run_syntax_error_vector`, which assigns `CONTROL_EXPECTATION`; M36 is recorded PASS. `docs/ambiguities.md:247` explicitly records that this interpretation moves M36 to PASS.
- M27's unique shape is routed to a special branch that returns NOT_IMPLEMENTED with a message naming the FIFO-042 disagreement. It is not a PASS, but it is still a fixture-singleton branch.
- The code therefore violates the explicit no-singleton-shape rule. This is a BLOCKER under the brief even though the M36 expected and actual fields match.

Ran or reasoned: Ran the descriptor shape-frequency analysis and inspected the dispatch and result records; reasoned from the stated no-singleton-shape rule.
Confidence: High.

### A2-1 [LIMITATION] Pinned Python 3.11 parser behavior and adversarial checks not independently run

File and line:
- `src/openvef/import_policy.py` (identifier tokenization implementation).
- `tests/test_import_policy.py:105` (`test_fstring_identifier_not_scanned_on_311`).

Pack text (exact, file and line):
- `CLAUDE.md:46-52` requires the pinned CPython 3.11.18 interpreter and says host-Python results are for development only and “are not evidence.”
- Protocol File 02, §3.4, line 166 specifies the ordered source and identifier scan.

Check or input:
- Ran the full `tests/test_import_policy.py` under the available CPython 3.13.5.
- The single failing test is specifically the test asserting CPython 3.11 f-string tokenization behavior. Ran the remaining parser/static test files available in the bundle.
- Did not run custom adversarial parser inputs on CPython 3.11.18 because the pinned image/interpreter was unavailable.

Expected:
- The parser and static-stage checks should be independently exercised under CPython 3.11.18, including adversarial cases, as required by the brief.

Actual:
- `test_import_policy.py` has one failure under Python 3.13.5: the f-string identifier test receives `NON_ASCII_IDENTIFIER|file=checker.py|line=1|column=8` where the test expects no finding under 3.11 tokenization. This is a version mismatch and is not treated as a product defect.
- `test_schema.py` (12), `test_source_ast.py` (13), and `test_ast_signature.py` (26) passed under 3.13.5. The required pinned-version verification remains outstanding.

Ran or reasoned: Ran the tests stated above; limitation is based on the unavailable interpreter/image.
Confidence: High.

### A3-1 [LIMITATION] Container-backed runtime, simulation and checker execution unavailable

File and line:
- `sandbox/sim.py`, `sandbox/sim_cocotb.py`, `sandbox/harness.py`.
- `src/openvef/simulation.py`, `src/openvef/simulator_stages.py`.
- `tests/test_sandbox.py`, `tests/test_simulation.py`.

Pack text (exact, file and line):
- Protocol File 02, line 166, steps (7)-(11), requires RTL/null execution, paired comparison, and two separate checker invocations.
- File 30 §6 (referenced by `docs/sandbox.md`) requires the same import allow-list statically and at runtime.

Check or input:
- Read the runner, sandbox harness, simulation orchestration, stage map and test implementations.
- Ran `tests/test_sandbox.py` and `tests/test_simulation.py` in the available environment.

Expected:
- The real container-backed runtime, watchdog, trace alignment, paired comparison and two checker runs should be exercised, not inferred solely from unit tests or source inspection.

Actual:
- Docker is unavailable. `tests/test_sandbox.py` skipped all 18 tests. `tests/test_simulation.py` passed its non-container tests and skipped 25 container-backed tests. No live FIFO RTL/null simulation or checker pair was independently run.

Ran or reasoned: Read source; ran tests, which reported the stated skips.
Confidence: High.

### A5-1 [LIMITATION] Pinned interpreter and image identity cannot be independently attested from this environment

File and line:
- `evidence/run-20261124T195537Z/summary.json` fields `python_version`, `python_executable_sha256`, `sandbox.base_image_digest`, `sandbox.image_id` and `sandbox.toolchain`.
- `runner/run_f18.py:475-490` records the interpreter identity and pinned status.

Pack text (exact, file and line):
- `CLAUDE.md:46-52` requires evidence runs to use CPython 3.11.18 inside the digest-pinned image and states other-interpreter results are not evidence.
- Audit brief §6 says a re-run needs Docker and a git checkout.

Check or input:
- Compared the summary's claimed interpreter and image identities with the runner's pinned constants and `docs/sandbox.md` claims.
- Verified every `source_sha256` entry against the bundled file and checked the run's result digest and fixture records (see Checks performed, A5).
- Attempted to inspect Docker availability; the executable is absent. The bundle has no git history.

Expected:
- The pinned image, interpreter binary and toolchain should be independently reproducible or inspectable for a full evidence audit.

Actual:
- The evidence record claims CPython 3.11.18 and records image/toolchain hashes, but this audit could not launch or inspect that image or verify the binary in situ. Source hashes match the bundle; the commit ID cannot be independently checked against git history in this archive.

Ran or reasoned: Ran hash comparisons; reasoned from the absence of Docker and git history for the identity limitation.
Confidence: High.

### A8-1 [MAJOR] Ready-made halt signatures bypass the protocol's closed component domains

File and line:
- `src/openvef/ledger.py:65-70` (`HaltSignature.given`) checks only the five-key set and constructs a tuple without validating component domains.
- `src/openvef/ledger.py:16-19` documents the A-031 interpretation.
- `src/openvef/ledger.py:73-76` compares supplied signatures for recurrence.
- `docs/ambiguities.md:247` is unrelated; the applicable reading is A-031 in `docs/ambiguities.md` and `docs/READINGS-REVIEW.md`.

Pack text (exact, file and line):
- Protocol File 02, line 185: “Its components have these exact domains: `design_id` is `FIFO` or `UART`; `halt_code` is `SIMULATOR_ERROR`, `TRACE_INTEGRITY_FAILURE` or `RTL_NULL_CONTROL_FAILURE`; `evaluator_component` is `SIMULATOR`, `REPLAY_VERIFIER`, `RECORDER`, `TRACE_ALIGNMENT_CHECKER`, `TRACE_SERIALIZER` or `RTL_NULL_COMPARATOR`; `stable_error_class` is a simple exception class name matching `[A-Za-z_][A-Za-z0-9_]*` for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token.”

Check or input:
- Inspected the M42 and M47 descriptor inputs, `HaltSignature.given`, and the run records.
- M42 supplies `evaluator_component: "simulator"` (lowercase).
- M47 supplies `evaluator_component: "recorder"` (lowercase) and `stable_error_class: "RecorderFault"` for a trace-integrity halt.

Expected:
- A signature described as having “these exact domains” should be validated against those domains, or the protocol should explicitly define the treatment of out-of-domain supplied signatures before they can be used to establish recurrence.

Actual:
- `HaltSignature.given` accepts both signatures without checking the domains. M42 and M47 are recorded PASS. A-031 chooses to validate only signatures constructed by `HaltSignature.build`, while comparing descriptor-supplied signatures as-is. The pack itself records this as PD-01 and acknowledges that no outcome is defined for out-of-domain signatures. This reading is not supported by the unqualified domain statement and changes two fixture outcomes to PASS.

Ran or reasoned: Ran inspection of the exact fixture records and source; independently recomputed the audited result records. No separate execution of M42/M47 under an alternate validation rule was performed.
Confidence: High.

### A9-1 [LIMITATION] Sandbox boundary could not be exercised against a live hostile artifact

File and line:
- `sandbox/harness.py` (restricted import, task dispatch and output framing).
- `src/openvef/sandbox.py` and `runner/run_f18_container.sh` (container launch/broker boundary).
- `docs/sandbox.md` (documented limits and residuals).

Pack text (exact, file and line):
- File 30 §6 requires a restricted execution container; `docs/sandbox.md` quotes the requirement that the runtime sandbox denies network, filesystem access beyond designated temporary output, environment variables, wall-clock reads, subprocess and simulator access.

Check or input:
- Read the artifact harness, import guard, container flags, broker protocol and sandbox documentation. Checked whether the request path exposes expected outcomes or writable evaluator files to artifact code.
- No live hostile artifact was launched because Docker is unavailable.

Expected:
- Demonstrate that artifact code cannot read or influence expected outputs, evaluator state, the host or a later fixture under the actual container configuration.

Actual:
- Static inspection found separate artifact containers, read-only harness mount/root, no network, no capabilities, non-root identity, constrained `/tmp`, captured artifact stdout/stderr, and no expected-output field in the artifact task requests. No concrete escape was found by reading. The live isolation and cross-fixture tests could not be run; documentation also notes that directory ACLs were not inspected.

Ran or reasoned: Reasoned from source and configuration only.
Confidence: Medium.

## Pack defects noticed (PACK)

### PACK-1 — PD-01: halt-signature domain ambiguity affects M42 and M47

Exact pack text: Protocol File 02, line 185, states that the halt-signature components “have these exact domains” and specifies the allowed `evaluator_component` values and the `stable_error_class` rule.

Concrete conflicting inputs: File 41 `M42.json` supplies lowercase `"simulator"`; `M47.json` supplies lowercase `"recorder"` and `"RecorderFault"` for a trace-integrity signature. The descriptors do not satisfy the stated domains.

The pack does not define whether such a supplied signature is invalid input or what outcome should follow. `docs/pack-defects.md:73-95` accurately records this as PD-01, but A-031's interim reading makes both fixtures PASS by exempting ready-made signatures from validation. Correct the descriptors or define the invalid-signature outcome in the normative pack before treating these results as unambiguous.

No other pack defect was independently established beyond those already explicitly disclosed in `docs/pack-defects.md`.

## Checks performed, per area

- **A1:** Verified `MANIFEST.sha256` (274 entries). Parsed the fixture index and all 144 descriptors; counted 27 input shapes and identified singleton shapes. Read `runner/run_f18.py` dispatch/execute path. Reconciled M27 and M36 with their `results.jsonl` records. Confirmed that the M36 branch returns a computed control expectation and that M27 has a singleton-shape special case.
- **A2:** Ran `tests/test_schema.py` (12 passed), `tests/test_source_ast.py` (13 passed), `tests/test_ast_signature.py` (26 passed), and `tests/test_import_policy.py` (70 passed, 1 failed under Python 3.13.5). Read `envelope.py`, `schema.py`, `source_ast.py`, `import_policy.py`, `ast_signature.py`, and relevant stage-map logic. Did not claim Python 3.11.18 coverage.
- **A3:** Read `runtime.py`, `simulation.py`, `simulator_stages.py`, `trace.py`, `stage_map.py`, `sandbox/sim.py`, `sandbox/sim_cocotb.py` and `sandbox/harness.py`. Ran the corresponding tests; Docker-dependent tests skipped as detailed above. Did not independently verify real watchdog timing or the two checker invocations in containers.
- **A4:** Ran the complete `tests/test_*.py` collection under Python 3.13.5. `tests/test_lifecycle.py` (5), `tests/test_local_rules.py`, `tests/test_trace.py`, `tests/test_schema.py`, `tests/test_doc_quotes.py` and other non-container tests passed. Reviewed `serializer.py`, `assembler.py` and `ledger.py`. The one import-policy failure and Docker skips are reported under their relevant areas, not treated as A4 failures.
- **A5:** Recomputed SHA-256 of `results.jsonl`: `8268ca65420fcbfebc3052f1cf18194a00d7404b1e9c67705dbf503785cf81c1`, matching `summary.json.results_sha256`. Recomputed status counts: 139 PASS, 0 FAIL, 5 NOT_IMPLEMENTED, 0 ERROR; 144 records and 144 distinct fixture IDs. Compared every record's fixture ID, descriptor hash and `expected` with the corresponding indexed descriptor; no mismatches. Verified every PASS has `actual == expected`. Verified all `source_sha256` entries against the bundled files; no mismatches. `run.log` has 144 fixture lines plus metadata. Confirmed zero `provisional` result blocks and exactly 10 `cleared_under_deviation` records with the label “cleared under DEV-001 (non-independent review saved)”. Could not independently verify the image or interpreter in Docker.
- **A6:** Ran `tests/test_freeze_package.py` (13 passed). Reviewed `FREEZE-RECORD-2026-11-24.md`, `OWNER-FREEZE-PACKAGE.md`, `freeze-record-2026-11-24.json`, `deviation-DEV-001.json`, `freeze.py`, and the hash-test implementation. The signed A1–F1 freeze items are represented separately from the unsigned D-010/D-011 mask amendments. D-011 supersedes D-010 mask hashes, and the current mask hashes agree with the freeze/deviation records. No claim is made that D-010/D-011 carry the A1–F1 owner signature.
- **A7:** Read `DEVIATIONS.md`, `docs/reviews/claude-mask-review-2026-11-25.md`, the primary/stricter mask JSON, traceability CSV, FIFO-013/FIFO-021/FIFO-022/FIFO-028/FIFO-029 and Protocol L268–L280 references. Ran `tests/test_fifo_mask.py` (one test skipped in this environment). The record plainly says L271 and File 21 L32 remain unmet; the review and labels consistently say non-independent. The primary mask compares predicate/status outputs continuously and compares `rd_data` only when the null trace has `rd_valid == 1`; the stricter variant compares `rd_data` in every row.
- **A8:** Read `READINGS-REVIEW.md`, `ambiguities.md`, `ledger.py`, `stage_map.py`, `pack-defects.md`, M27/M42/M47 and the five NOT_IMPLEMENTED lifecycle descriptors. Verified the stated reason for M27's NOT_IMPLEMENTED status (no supplied port set/widths and a prose predicate not executable under the defined contract). Verified M48/M50/M54/M58 remain NOT_IMPLEMENTED where `LIFECYCLE_CASES` records unsupported fields. Identified the A-031/PD-01 domain conflict described above. The 40 D-009 decisions are disclosed as approved without itemised owner review; that disclosure is not treated as substantive proof of correctness.
- **A9:** Read the runner/artifact container argument files, Dockerfile, `sandbox.py`, `harness.py`, `sim.py`, broker launcher, and sandbox documentation. No live container or hostile-artifact test was possible.
- **A10:** Read `AUDIT-READINESS.md`, `DEMO-2DEC.md`, `traceability.md`, `assistance-log.md`, and `pack-defects.md`. AI authorship of the implementation materials and non-independent mask review are disclosed. The readiness document expressly says F18 is not passed, L271 is unmet and L555(5) has not started. The F1–F17 controls are out of scope and their absent runs are disclosed.
- **Pack baseline integrity:** Ran `sha256sum --ignore-missing -c 27_SHA256SUMS.txt`; 172 available pack files verified, zero failures.

## What was not checked

- No full F18 rerun. Docker is unavailable and the archive has no git history; the brief itself says a rerun requires both.
- No execution under the pinned CPython 3.11.18 interpreter or its digest-pinned image. The available interpreter is 3.13.5.
- No real container-backed artifact execution, FIFO RTL/null simulation, live watchdog test, paired trace comparison, or two-process checker invocation.
- No live hostile-artifact sandbox escape attempt. Static review cannot prove the isolation boundary.
- No independent human review or signature of the observation mask. This is explicitly unmet under DEV-001 and is not cured by this audit.
- No independent verification of the source commit IDs against git history; no git history is included.
- No LLM/provider API was called by this audit.
- F1–F17 control results are outside this audit's scope.

## Overall statement

The archive and its recorded evidence are internally consistent on the checks that could be performed: the top-level manifest verifies; the pack's available checksums verify; the evidence results digest and fixture counts recompute; every result maps to the indexed descriptor; all recorded PASS entries match their expected objects; and the recorded source hashes match the bundled files. The evidence reports **139 PASS, 0 FAIL, 5 NOT_IMPLEMENTED, 0 ERROR**. Ten PASS records carry the exact non-independent DEV-001 clearance label.

This audit nevertheless identifies a **BLOCKER**: the fixture runner contains branches for input shapes occurring in only one fixture, contrary to the explicit no-fixture-specific-code rule. It also identifies a **MAJOR** unsupported reading in A-031: ready-made halt signatures outside Protocol L185's stated exact domains are accepted, causing M42 and M47 to PASS. PD-01 is a pack defect that must be resolved normatively.

Areas A2, A3, A5 and A9 remain limited by the absence of the pinned Python 3.11.18/Docker environment. Their verdicts are FINDINGS because required checks could not be completed, not because the skipped runtime tests were assumed to fail.

**This report does not state that F18 has passed. It does not state that Protocol L555(5) is satisfied; whether this AI audit counts toward that gate remains an owner decision. It does not satisfy or replace the independent human mask review required by L271.** The five NOT_IMPLEMENTED fixtures remain unresolved, and the ten DEV-001-cleared results remain subject to the disclosed non-independent mask review deviation.
