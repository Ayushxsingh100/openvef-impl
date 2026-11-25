OpenVEF Implementation Audit — Re-audit #3
Audit date: 25 November 2026
Auditor model: OpenAI GPT-6
Human operator: Krishika
Audit type: AI implementation audit; not an independent human audit.
Audit in progress — clearance not yet established
Bundle SHA-256 (computed from the uploaded ZIP):
b1235ba376442eead14c338b59d73060cb927532c67cdd59324d0f2a0a08327d


I will assess the four previously open findings individually, distinguish actual code-level resolution from documentation or approval changes, and independently challenge the A9 isolation implementation.
1. Previous findings — resolution decisions
Previous finding	Re-audit #3 verdict	Assessment
A1-1 — M18 / fixture-specific dispatch	Not resolved	M18's canonical-heading defect is fixed, but the original strict criterion still fails. I also found an incomplete domain citation in the revised adapter contracts.
A4-1 — Serializer accepts mismatched records	Resolved	The serializer now validates the complete stage/error-class/diagnostic tuple against STAGE_MAP.
A8-2 — M18 reading / A-053	Resolved	The implementation now uses canonical sidecar headings and cites the nine-heading domain.
A9-1 — Artifact modifies evaluator serialization	Not fully resolved	Separate processes close the original shared-JSON vulnerability, but worker-global tampering provides another route to forge runtime-check results.

A1 — Fixture runner
The important distinction is between the original criterion and the revised D-013/D-017 criterion.
- The five single-fixture input shapes remain.
- D-013 permits them only when their input contracts are properly supported and synthetic vectors establish meaningful behavior.
- D-017 adds boundary pairs for each cited input property.
- The tests enforce these mechanical conditions, but passing those tests does not establish that every citation actually defines the property.
Specific issue found: adapt_response permits provider_finish_reason values length and stop (runner/run_f18.py, lines 239–243).

Its contract cites:
- Protocol L144 for length, which explicitly describes max-token truncation.
- Protocol L143 for stop, which describes envelope, schema or clause-manifest rejection—not the domain of provider finish reasons.
The DOMAINS entry at runner/adapter_contracts.py lines 120–121 only establishes the max-token-truncation meaning. It does not establish stop as an allowed provider finish reason.

This means the contract test can establish verbatim quotation without establishing semantic support for the entire allowed domain.
A1-1 remains open
The M18-specific defect is resolved, but A1-1 cannot be closed while the original criterion remains unmet and the revised contract has this gap.
A4 — Serializer
The previous adversarial case was:
Failure(    "CHECKER_NULL",    "WRONG_CLASS",    "COMPILE_ERROR|file=driver.py|line=1")



The revised implementation uses in_stage_map() to validate all three fields together.

feedback_bytes() delegates to serialize(), which rejects any tuple not represented by the authoritative stage map.

The test test_auditor_case_a4_1 is present in the updated test suite. The container log reports 26 passing tests in test_local_rules.py.

Verdict: A4-1 resolved.
A8 — Reading decisions
M18 now calls check_reserved_heading_lines() against the canonical RESERVED_HEADINGS imported from the assembler. Descriptor-supplied headings are checked against that canonical set but are never used to determine the actual rejection.

This removes the original vulnerability in which an arbitrary descriptor-supplied list controlled the check.

D-018 also records Krishika's approval of A-055 and A-056 as decided. Importantly:
- A-055 approves the reading that the pack states no maximum for scheduled_slots.
- A-056 approves refusal of excluded values for which the pack supplies no outcome.
- Neither approval changes code or fixture outcomes.
- Neither approval substitutes for independent review of the underlying textual interpretation.
Verdict: A8-2 resolved. The separate A1-1 contract issue remains.
A9 — Sandbox isolation and adversarial testing
This is the most important new finding.

What D-015 successfully fixed

The original shared-interpreter vulnerability is substantially fixed:
- artifact_worker.py executes artifact code in a separate Python process.
- artifact_proc.py owns communication with that process.
- The evaluator does not import the artifact's Python objects.
- Responses are transported as length-prefixed JSON frames.
- The parent reconstructs plain Python values.
- The worker has a syscall allow-list, memory limit and restricted file descriptors.
- Artifact containers are separately constrained by Docker.
The original json.dumps / json.dump monkeypatch can no longer directly modify the evaluator's recorder module.

Therefore, the original A9-1 attack path is resolved.

However, I found a different attack against the worker's trusted runtime checks.
New finding: A9-2 — BLOCKER
New evaluator-integrity vulnerability
Files and lines:
- sandbox/artifact_worker.py: 40–45, 277–300.
- sandbox/artifact_proc.py: 85–87, 155–161.
- sandbox/harness.py: 52–67.
Relevant pack requirement — File 30, L35:
Runtime inspect.signature must confirm the same parameter names/kinds/counts.

The same line requires create_driver(seed) to return an instance of the module's Driver class.

File 30 L39 additionally states:
Runtime signature checks and the create_driver return-type check run after import in the restricted execution container.

Attack mechanism

The worker exposes its main module through Python's module registry.

An artifact can reach that namespace through an allowed import:
import collectionsworker = collections._sys.modules["__main__"]



This is not speculative access to a separate process. It is access to the worker's actual module namespace.

The worker subsequently executes:
instance = module.create_driver(msg["seed"])cls = getattr(module, "Driver", None)ok = isinstance(cls, type) and isinstance(instance, cls)send(    '{"constructed":['    + ("true" if ok else "false")    + ","    + parameters(module.create_driver)    + ","    + (parameters(cls.__dict__.get("step")) if ok else "null")    + "]}")



The calls to isinstance, parameters and send are global lookups in the worker module.

Consequently, artifact code executing inside create_driver() can replace those helpers before the worker uses them.

For example, it can:
1. Replace parameters with a function returning fabricated valid signature data.
2. Replace isinstance to report a successful factory return check.
3. Replace send to emit a fabricated but syntactically valid constructed response.
4. Restore the original helpers after the response is emitted.
A particularly useful attack is to redefine Driver.step dynamically as a variadic function inside create_driver(), while the static AST contains an initially valid method definition. The worker's signature measurement can then be falsified.

The parent receives what appears to be a successful runtime verification.

Expected: Runtime signature and return-type measurements must be generated by trusted code that artifact code cannot replace.

Actual: Artifact code can modify the worker's global helper functions before those measurements are produced.
My adversarial checks
Attack	Assessment
Access worker's __main__ namespace through collections._sys.modules	Confirmed by local Python inspection
Replace worker's signature-measurement helper	Exploitable by code inspection
Replace worker's type-check helper	Exploitable by code inspection
Forge a constructed response through the worker's send function	Exploitable by code inspection
Modify evaluator's original JSON recorder across processes	Original path closed
Read the host's files or evaluator memory	No successful route established
Persist changes into a later fixture	No successful route established

I also independently checked two relevant Python mechanisms under the available interpreter:
- collections._sys.modules["__main__"] resolves to the current main module.
- inspect.signature() can report a fabricated __signature__ for a variadic function.
These checks establish the underlying mechanisms, not an end-to-end Docker exploit.

Why the existing tests are insufficient

tests/test_artifact_isolation.py contains a useful test that deliberately patches the worker's encode function.

However, it does not test whether artifact code can replace the worker's parameters, isinstance and send functions before runtime validation.

The container log reports 21 passing isolation tests. Those tests do not cover this attack.

Remediation recommendation
- Capture trusted worker functions in protected local references before executing artifact code.
- Do not perform runtime measurements through mutable worker globals after artifact execution.
- Ensure serialization and response generation cannot be replaced by artifact code.
- Add adversarial tests for fabricated factory-return and runtime-signature results.
- Repeat these tests in the pinned container.
Verdict: Original A9-1 attack resolved; new A9-2 BLOCKER discovered. A9 cannot be cleared.

2. Container evidence and execution environment
Evidence hashes verified
I could not run Docker in this environment. I therefore followed the audit brief's alternative procedure: inspected the supplied container logs rather than claiming to have independently run the container tests.
Environment
Item	Observed
Available Python	CPython 3.13.5
Docker executable	Unavailable
Pinned runtime in evidence	CPython 3.11.18
Recorded Docker server	29.9.2-2
Recorded image	sha256:565e55470476be93f0b6b6ea6ec88776b0332598c77a9a3fba0aa305c2971c3f
Container test commit	902383f68e87e0483a2faa602c6a72f3de7c9d4f

Container test results
367 / 367
Tests reported passing by the supplied container-test harness
PASS

367

FAIL

0

ERROR

0

SKIPPED

0

Three tests concern proposals outside this audit's scope; 364 logged tests are in scope.
Important test logs:
Test suite	Logged result
test_artifact_isolation.py	21 passed
test_dispatch_shapes.py	19 passed
test_local_rules.py	26 passed
test_ast_signature.py	26 passed
test_import_policy.py	71 passed
test_simulation.py	28 passed
test_miter_alignment.py	23 passed
test_fifo_mask.py	8 passed
test_fifo_rtl.py	7 passed
test_fifo_spec.py	10 passed
test_freeze_package.py	13 passed
test_sandbox.py	18 passed

Integrity checks performed:
1. Verified all 318 entries in MANIFEST.sha256.
2. Verified the container evidence's SHA256SUMS.
3. Compared all 87 recorded container-test source hashes with the bundled files. No mismatches.
4. Checked the container's recorded interpreter and image identity against the F18 run.
5. Inspected run.log, results.jsonl, files.json, environment.json and summary.json.
These results are evidence from the implementation author's test harness. They are not independent Docker execution by me.
D-016 wall-clock restrictions
I also reviewed the clock-removal implementation and the supplied adversarial test coverage.

The implementation addresses:
- vDSO clock access;
- kernel time-data pages;
- RDTSC/RDTSCP;
- normal clock-related syscalls;
- fstat and futex clock-related paths.
The container tests include Python, libc, raw-syscall and native-instruction attempts.

The documented residuals remain important: TPAUSE and UMWAIT have not been tested on other hardware, and RDPRU's denial is not established as a universal hardware guarantee.

I found no additional demonstrated wall-clock escape, but cannot certify cross-platform clock denial.

3. F18 evidence-run verification
Recorded evidence internally consistent
I inspected:

evidence/run-20261125T075113Z/
Verification	Result
Mandatory fixture count	144
Results JSONL records	144
Results SHA-256	Matches summary
Descriptor SHA-256 values	All match
Descriptor byte lengths	All match
Expected results	All match descriptors
PASS actual versus expected	127/127 match
Source hashes	47/47 match
Provisional fixtures	0

Recorded F18 outcomes
PASS 127



NOT_IMPLEMENTED 17

FAIL 0

ERROR 0

These are the recorded results, not a new F18 execution.

The 17 NOT_IMPLEMENTED fixtures remain:
- M13, M14, M15, M17, M27, M36, M37, M41, M48, M50, M53, M54, M58.
- P17, R07.
- M42, M47.
The nine DEV-001-labelled passes remain:

P01, P14, P21, P42, M07, M31, M32, M33 and M57.

They are not independently reviewed passes.

4. Remaining audit areas
A2 — Parser and static stages
PASS — based on supplied test evidence
Inspected the implementation and relevant test results for:
- Envelope and JSON schema validation.
- Strict UTF-8 and BOM handling.
- Python syntax and source-position reporting.
- Import-policy precedence.
- Prohibited built-ins and global random access.
- AST signature checks and required entry-point ordering.
- Non-ASCII identifier detection.
The relevant pinned-container logs report successful completion:
- test_schema.py: 12 tests.
- test_source_ast.py: 13 tests.
- test_ast_signature.py: 26 tests.
- test_import_policy.py: 71 tests.
No new parser or static-stage defect was established.

Qualification: These are read container logs, not tests I independently executed under Python 3.11.18.
A3 — Runtime, simulation and checker
FINDINGS — limitation and A9 cross-reference
Reviewed:
- Driver factory and step execution.
- Watchdog and timeout handling.
- Simulation sequencing.
- Trace recording and alignment.
- RTL/null comparison.
- Checker invocation and classification.
- Separate checker processes.
The supplied logs report successful simulation and miter tests.

However, A9-2 undermines the trustworthiness of runtime signature verification. It must be fixed before relying on those runtime checks.

I could not independently execute the Docker simulation suites or perform a fresh end-to-end run.

No separate additional A3 implementation defect was established.
A4 — Serializer, assembler and lifecycle
PASS
Checks performed:
- Compared STAGE_MAP with Protocol L143–L162.
- Checked complete tuple validation.
- Checked diagnostic grammar and truncation.
- Checked JSON serialization and ordering.
- Reviewed reserved-heading and placeholder rejection.
- Reviewed lifecycle and repeated-halt handling.
- Checked the previously failing A4-1 adversarial case.
The revised serializer now rejects mismatched stage/error-class/diagnostic records.

The relevant test logs report:
- test_local_rules.py: 26 passed.
- test_lifecycle.py: 5 passed.
- test_doc_quotes.py: 1 passed.
No remaining A4-1 defect was found.
A5 — Evidence run
PASS
Checks performed:
- All 144 mandatory fixture records.
- Results SHA-256.
- Descriptor hashes and lengths.
- Expected versus actual records.
- Source-file hashes.
- Pinned interpreter and image identity.
- Provisional and deviation labels.
No evidence inconsistency was found.

This confirms internal consistency, not evaluator resistance to adversarial artifacts.
A6 — Freeze record
PASS
Reviewed:
- docs/FREEZE-RECORD-2026-11-24.md
- docs/OWNER-FREEZE-PACKAGE.md
- design/fifo/freeze/
- D-010 and D-011 amendments.
- Freeze-package verification tests.
The container log reports 13 passing freeze-package tests.

No new freeze-record defect was established.
A7 — Deviations and mask
FINDINGS — limitation
Reviewed:
- docs/DEVIATIONS.md
- docs/reviews/
- Primary and stricter FIFO masks.
- Mask traceability.
- Container logs for FIFO mask, RTL, specification and freeze tests.
The existing disclosure remains correct:
- L271 is not satisfied.
- File 21 L32 is not satisfied.
- The mask review is not independent.
- DEV-001 records the deviation.
- Section G remains unsigned.
I found no basis to claim independent mask approval.

The supplied tests support the documented mask behavior, but I did not independently execute RTL/null comparisons.

This is an existing disclosed limitation, not a newly discovered defect.
A8 — Reading decisions
PASS — reviewed changes
The two D-018 readings deserve explicit treatment.
Reading	Assessment
A-055: scheduled_slots has no stated upper bound	Supported by the denominator definitions and the meaning of a slot.
A-056: refuse excluded event-field and packet-text values	Conservative treatment of values excluded by the pack without a specified outcome.

D-018 approval is recorded, but it is not independent textual review.

The A-053/M18 defect identified in A8-2 has been corrected by using canonical sidecar headings.

The previous A8-1 correction remains in place.

No new false PASS disposition was identified in the 17 NOT_IMPLEMENTED cases.
A10 — Claims and disclosure
PASS
Reviewed:
- docs/AUDIT-READINESS.md
- docs/DEMO-2DEC.md
- docs/traceability.md
- docs/assistance-log.md
- docs/pack-defects.md
The documentation appropriately discloses:
- Claude/Anthropic implementation authorship.
- AI-assisted specification, RTL and mask development.
- GPT-6's previous audit findings.
- D-015, D-016 and D-017 requiring re-audit.
- Non-independent mask review.
- The 127 PASS / 17 NOT_IMPLEMENTED distinction.
- The fact that F18 has not passed.
No material overstatement of completion was identified.

5. Consolidated report — required format
OpenVEF implementation audit report
Auditor model and version: OpenAI GPT-6

Operator (human who ran the audit): Krishika

Date (UTC): 2026-11-25

Not a Claude model, not the implementation author: Yes

Implementation author: Claude (Anthropic), via Claude Code

Bundle SHA-256:
b1235ba376442eead14c338b59d73060cb927532c67cdd59324d0a08327d


Correction: the exact computed SHA-256 is:
b1235ba376442eead14c338b59d73060cb927532c67cdd59324d0a08327d


MANIFEST.sha256 verified: Yes — all 318 entries.

Environment: CPython 3.13.5 locally; Docker unavailable. Pinned CPython 3.11.18 and Docker results inspected through supplied container logs.
Summary
Area	Verdict	Blocker	Major	Minor	Limitation	Method
A1 Fixture runner	FINDINGS	1	0	0	0	Read
A2 Parser/static stages	PASS	0	0	0	0	Read container logs
A3 Runtime/simulation/checker	FINDINGS	0	0	0	1	Read container logs
A4 Serializer/assembler/lifecycle	PASS	0	0	0	0	Read container logs
A5 Evidence run	PASS	0	0	0	0	Ran checks/read
A6 Freeze record	PASS	0	0	0	0	Read container logs
A7 Deviations/mask	FINDINGS	0	0	0	1	Read container logs
A8 Reading decisions	PASS	0	0	0	0	Read
A9 Sandbox	FINDINGS	1	0	0	0	Read/reasoned
A10 Claims/disclosure	PASS	0	0	0	0	Read

Findings
A1-1 [BLOCKER] — Fixture-specific adapter rule remains insufficiently established

File and line:
- runner/adapter_contracts.py: 35–42, 117–121.
- runner/run_f18.py: 239–243, 359–375.
Pack text, File 02 L144:
Provider finish reason explicitly reports max-token truncation

Check: Compare the accepted provider finish reasons with their cited domain.

Expected: Every permitted value must have a citation establishing its meaning and domain.

Actual: stop is accepted but its citation points to File 02 L143, which describes envelope/schema rejection rather than a provider finish reason.

Ran or reasoned: Reasoned from code and pack text; boundary tests read from container logs.

Confidence: High.

Additionally, the five single-fixture shapes remain under the original strict criterion. D-013/D-017 do not eliminate that fact.

A9-2 [BLOCKER] — Artifact can forge worker runtime-check results

File and line:
- sandbox/artifact_worker.py: 277–300.
- sandbox/artifact_proc.py: 85–87, 155–161.
Pack text, File 30 L35:
Runtime inspect.signature must confirm the same parameter names/kinds/counts.

Check: Access the worker's __main__ module through collections._sys.modules and replace trusted runtime-measurement helpers during factory execution.

Expected: Artifact code cannot modify the trusted runtime-check mechanism.

Actual: Worker-global helper replacement can forge signature and type-check results returned to the evaluator.

Ran or reasoned: Reasoned from source; underlying Python module-access and signature-inspection mechanisms independently checked. End-to-end Docker exploitation not run.

Confidence: High.
Limitations
A3-1: No independent Docker execution of the simulation and runtime suites.

A7-1: No independent human mask review or independent RTL/null execution. The existing deviation is accurately disclosed.
Pack defects noticed (PACK)
No new independently established pack defect requiring a separate PACK finding.

The D-018 readings are conservative and have been explicitly approved, but owner approval should not be confused with independent specification review.

6. Final disposition
NOT CLEARED
Two outstanding blockers
1. A1-1 — Fixture-specific adapter criterion and incomplete provider-finish-reason domain.
2. A9-2 — Artifact can tamper with worker runtime-validation helpers.

What should happen next
My recommended remediation order:
1. Fix A9-2 first. Protect runtime signature, return-type and response-generation helpers from artifact-controlled namespace mutation.
2. Add adversarial tests that forge parameters, isinstance and send results.
3. Resolve A1-1. Correct the provider-finish-reason domain citation and decide explicitly how the five remaining single-fixture shapes satisfy the approved adapter rule.
4. Preserve the A4-1 and A8-2 fixes.
5. Repeat the entire suite under the pinned CPython 3.11.18 Docker image.
6. Have an independent human reviewer review the mask and sign the required record.
7. Rebuild the evidence bundle and perform another re-audit.
Identity and audit standing
Role	Identity
Auditor	OpenAI GPT-6
Human operator	Krishika
Implementation author	Claude (Anthropic), via Claude Code
Audit number	Re-audit #3
Audit result	NOT CLEARED
F18 status	Not passed
L555 (5)	Not independently satisfied
L271	Not satisfied
	
Final conclusion: D-015 meaningfully fixed the original shared-interpreter JSON serialization vulnerability. D-018 records the two additional owner approvals, without changing code or fixture outcomes. A4-1 and A8-2 are resolved, and the M18-specific implementation defect is fixed. However, A1-1 remains open, and I identified a new BLOCKER in the artifact worker's runtime-validation trust boundary.

The project must not be represented as independently audited or as having passed F18.

My strongest recommendation: Do not proceed to treating the current implementation as ready for confirmatory evaluation. Fix A9-2 before spending time on further fixture-level refinements. It affects the trustworthiness of the evaluator itself.
