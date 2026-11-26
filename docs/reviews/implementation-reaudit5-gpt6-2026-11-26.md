OpenVEF — Independent Implementation Audit #5
Operator: Krishika · Author: Claude (Anthropic), via Claude Code
AUDIT IN PROGRESS
1. Bundle identification
Uploaded bundle: openvef-audit-bundle (1).zip

SHA-256:
5bdc25ea3bf0be66f16a0aa5a47737c2b29f8c798f31495ffa670859689b2cc2


Hash computed directly from the uploaded ZIP bytes.
2. Manifest verification
327 / 327 entries verified
- All 327 manifest entries were parsed.
- Every referenced file exists in the ZIP.
- Every SHA-256 digest matches the corresponding file bytes.
- No missing entries, malformed entries or hash mismatches were found.
- The archive contains 328 files, including MANIFEST.sha256.
The audit brief was read in full. The uploaded bundle is being treated as the evidence under examination, not as an authoritative statement of correctness.
3. Environment and execution disclosure
Item	Result
Auditor	OpenAI GPT-6
Implementation author	Claude / Anthropic, via Claude Code
Auditor is not the author	Yes
Available Python	CPython 3.13.5
Required Python 3.11.18	Not available locally
Docker execution	Not performed
Bundle modifications	None

I have already executed two relevant test files:
- tests/test_dispatch_shapes.py: 22 tests passed.
- tests/test_artifact_isolation.py: 7 passed, 26 skipped.
These executions used CPython 3.13.5, not the pinned container. They are supplementary checks, not evidence of pinned-environment execution.
4. D-022: A1-1 — provider finish reason
The new citation is:

baseline/OpenVEF_Planning_v1_3_6/36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md, line 48.

Exact pack text:
| P11b | parser | Syntactically truncated JSON without provider truncation status. | REPAIR — SCHEMA_REJECT|pointer=/ | 41_F18_Fixture_Inputs/P11b.json |

The competing value is supported separately by File 02, line 144:
| Provider finish reason explicitly reports max-token truncation | PARSE_SCHEMA | OUTPUT_TRUNCATED | OUTPUT_TRUNCATED; repair |

The distinction is meaningful:
- length: explicit provider-reported truncation.
- stop: no provider truncation status; ordinary envelope parsing applies, including rejection of syntactically truncated JSON.
The implementation at src/openvef/envelope.py, lines 67–90, follows that distinction.

Initial finding: the D-022 replacement citation is materially better and supports the intended stop case. I have not found a selecting value whose actual citation is false.

There is, however, a qualification: value_support_problems() in tests/test_dispatch_shapes.py, lines 90–109, checks substring presence and declared support categories. It does not independently establish semantic truth. The test can reject certain deliberately bad tables without proving that every accepted MEANING explanation is correct.

This is a limitation of the validation test, not presently evidence that the actual stop citation is wrong.
5. D-022: A9-2 — literal runtime signature verification
D-022 implementation verified by source analysis and supplied test evidence
What changed
The implementation now has two independent measurements.
1. Trusted measurement: sandbox/artifact_worker.py, lines 315–325, compiles source and extracts function/class code-object parameters without executing the source.
2. Literal measurement: lines 340–349 call the saved inspect.signature function after artifact import.
The evaluator compares both in sandbox/artifact_proc.py, lines 108–112:
- Trusted definition must have the required names, kinds and counts.
- Post-execution code-object measurement must agree.
- Literal inspect.signature must not raise.
- Its names and kinds must match the trusted measurement.
The factory and driver checks are invoked in sandbox/harness.py, lines 52–73. The checker check is at lines 105–117.
Adversarial metadata analysis
I examined the following attack classes:
Attack	Expected behaviour	Assessment
Wrong variadic Driver.step with correct __signature__	Reject	Correctly handled
Wrong variadic definition with __wrapped__ pointing to a good function	Reject	Correctly handled
Correct definition with hostile __signature__	Reject if introspection cannot confirm the contract	Correctly handled
__signature__ containing a variadic parameter	Reject	Correctly handled
__wrapped__ cycle	Reject	Correctly handled
Hostile parameters property	Reject	Correctly handled
Correct definition with harmless matching __wrapped__	Accept	Correctly handled

The relevant adversarial tests are in tests/test_artifact_isolation.py, lines 280–324.
A-058: defaults
The important distinction is that the pack requires no defaults in the actual definitions, but File 30 L35/L37 specifies that runtime introspection confirms names, kinds and counts.

I independently tested a correct create_driver(seed) code definition carrying a custom __signature__ that shows a default value.

PASS
 The implementation accepts it because the code-object measurement confirms no actual default, while the literal measurement compares only names and kinds.
This is consistent with A-058, docs/ambiguities.md, lines 1823–1836, approved by Krishika under D-022.

No metadata-based bypass of the required signature shape was established.

A correct definition is not wrongly rejected merely because its metadata shows a default. If metadata changes the parameter names or kinds, or causes inspect.signature to raise, rejection is required by the chosen reading.
Remaining A9-2 residual
This does not prove that all post-import runtime reports are trustworthy.

Artifact code outside the statically PROVEN fragment can still manipulate its own runtime state and forge reports. This is explicitly disclosed in:
- docs/DEVIATIONS.md, lines 164–184.
- docs/sandbox.md, lines 147–162.
- sandbox/harness.py, lines 56–59.
The consequence remains that an invalid SELF_REPORTED artifact may be counted valid. D-022 fixes the missing literal introspection operation; it does not close that residual.

Verdict on the D-022 A9-2 correction: resolved. Verdict on complete runtime-proof security: still open, as disclosed.
6. Adversarial test evidence
The supplied container-test evidence was independently inspected, not executed by me.
Evidence integrity verified
Check	Result
Container SHA256SUMS entries	31/31 verified
Bundled source hashes in container summary	90/90 match
Container return code	0
Reported test files	25
Reported passing tests	387
Reported failures	0
Reported interpreter	CPython 3.11.18
Reported interpreter SHA-256	Matches F18 run
Reported image identity	Matches F18 run

The evidence is internally consistent. Its provenance remains the implementation author's test harness and development host; I do not claim independent proof that Docker actually ran.

The most relevant logs are:
- test_dispatch_shapes.log: 22 passing tests, including D-022 support-table tests.
- test_artifact_isolation.log: 33 passing tests, including metadata spoofing, runtime signature verification, process isolation and wall-clock attacks.
- test_local_rules.log: 26 passing tests, including the A4-1 adversarial case.
- test_ast_signature.log: 26 passing tests.
A1-1: additional attempt to break the support-table validator
I found a weakness worth documenting.

The actual VALUE_SUPPORT table uses:
"stop": (MEANING, "without provider truncation status")



That is an appropriate explanation of File 36 L48.

However, I constructed a deliberately weaker support declaration:
"stop": (MEANING, "JSON")



I ran the actual value_support_problems() function against this modified support table.
WEAKNESS REPRODUCED
It returned an empty list, meaning it accepted the inadequate explanation.

This happens because the function checks whether the declared words occur in the citation, not whether those words establish the semantic distinction.

Important distinction:
- The current stop citation and current support explanation are sound.
- The validation function is not a semantic proof.
- D-022 explicitly discloses this limitation in docs/ambiguities.md, lines 1812–1814.
I therefore do not classify the actual stop citation as unsupported. I record the validator's semantic weakness as a named LIMITATION, not a new undisclosed citation defect.
7. Regression audit
A4-1 — serializer rejects mismatched tuples
RESOLVED
I compared src/openvef/serializer.py, lines 84–116, with Protocol File 02, lines 143–162.

The serializer now validates the complete tuple:

(stage_id, error_class, diagnostic)

I specifically checked the previous adversarial case:
("CHECKER_NULL", "WRONG_CLASS", "COMPILE_ERROR|file=driver.py|line=1")



It is rejected by both serialize() and feedback_bytes().

The regression test test_auditor_case_a4_1 passed locally and in the supplied container logs.
A8-1 — halt-signature domains
RESOLVED
Inspected src/openvef/ledger.py, lines 26–87.

Verified:
- Both permitted design IDs.
- All three halt codes.
- All six evaluator components.
- Exception-class and NONE rules.
- Stable diagnostic-code equality.
- Trace-integrity reason-to-component mapping during construction.
- Rejection of invalid supplied signatures.
The tests test_build_enforces_domains, test_given_enforces_every_domain and test_recurrence passed locally.
A8-2 — reserved headings and M18
RESOLVED
Inspected src/openvef/assembler.py, lines 32–49, and the sidecar's block_inventory.

All nine reserved headings match the sidecar.

The implementation uses its own fixed RESERVED_HEADINGS tuple rather than trusting a caller-provided list.

The adapter adapt_reserved_headings is covered by the dispatch-contract and boundary tests.

The relevant tests in test_dispatch_shapes.py passed.
A9-1 — artifact isolation
PREVIOUS FINDING REMAINS FIXED
Rechecked:
- sandbox/artifact_proc.py
- sandbox/artifact_worker.py
- sandbox/harness.py
- tests/test_artifact_isolation.py
The architecture maintains separate evaluator and artifact processes. The worker returns framed plain data, and the evaluator reconstructs values rather than trusting artifact-created Python objects.

The supplied container log reports all 33 artifact-isolation tests passing, including:
- Attempts to access evaluator modules.
- Attempts to access /proc and host files.
- Forged protocol frames.
- Forged result lines.
- Attempts to modify classification.
- Process termination and memory exhaustion.
- Watchdog termination.
- Wall-clock restrictions.
I found no regression of the previously identified A9-1 attack.
Wall-clock regression
No new bypass was established in the reviewed source or supplied test logs.

However, the documented limitations remain in docs/DEVIATIONS.md, lines 149–160:
- Hardware and kernel coverage is limited to one development host.
- TPAUSE and UMWAIT remain untested.
- RDPRU blocking is observed, not established by a documented guarantee.
- Native code remains possible inside the confined process.
- Startup remnants can retain previously read clock values.
These are not newly discovered defects, but they prevent a universal hardware-independent security claim.

8. D-022 consolidated verdicts
Target	Verdict	Reason
A1-1 — stop citation	RESOLVED	File 36 L48 supports the no-provider-truncation case
A1-1 — support-table test	LIMITATION	Semantic support remains author-judged
A9-2 — literal inspect.signature	RESOLVED	Called after import; compared with trusted measurement
A9-2 — metadata spoofing	NO BYPASS FOUND	Wrong signatures cannot pass both measurements in the reviewed path
A9-2 — SELF_REPORTED residual	OPEN	Runtime reports outside PROVEN remain forgeable
A4-1	RESOLVED	Complete tuple validation
A8-1	RESOLVED	Halt-signature domain enforcement
A8-2	RESOLVED	Canonical headings and adapter enforcement
A9-1	RESOLVED	Process isolation and plain-data boundary

9. Formal findings and limitations
A1-1-L1 [LIMITATION] Semantic support is not independently enforced
File and line:
- tests/test_dispatch_shapes.py, lines 90–109.
- runner/adapter_contracts.py, lines 121–124.
Pack text — File 36, L48:
Syntactically truncated JSON without provider truncation status.

Check: Ran the actual value_support_problems() function with the deliberately weak support declaration ("MEANING", "JSON") for adapt_response.stop.

Expected: The insufficient explanation should be rejected.

Actual: The function returned an empty problem list.

Method: Ran.

Severity: LIMITATION.

Confidence: High.

This weakness is explicitly disclosed by D-022. It does not invalidate the actual current stop citation.
Named coverage limitations
These are coverage limitations, not newly established implementation defects.
ID	Area	Limitation
L-02	A1	I verified the 144 records and descriptor integrity but did not independently execute the complete F18 runner under CPython 3.11.18.
L-03	A2	The complete parser/schema adversarial audit was not repeated. Supplied container logs were inspected.
L-04	A3	Full simulator, trace and checker execution was not independently repeated in Docker.
L-05	A4	The full assembler and lifecycle implementation was not re-audited beyond the serializer and relevant regression checks.
L-06	A6	The complete freeze-package hash and signed-record audit was not repeated.
L-07	A7	The complete mask-to-specification review was not repeated. Independent human mask review L271 remains unmet.
L-08	A8	Only A8-1 and A8-2 were specifically rechecked. Every other historical reading and all 17 NOT_IMPLEMENTED reasons were not re-audited.
L-09	A9	Wall-clock and native-instruction coverage is limited to the supplied one-host evidence; other hardware and kernels were not tested.
L-10	A9	SELF_REPORTED artifacts can still forge runtime results outside the statically PROVEN fragment.
L-11	A10	The complete claims, assistance-log and disclosure audit was not repeated.

Adapter disclosure: The five one-of-a-kind fixture shapes retained under D-013 map as follows:
Fixture	Adapter
M18	adapt_reserved_headings
M19	adapt_rendered
M25	adapt_runtime_signature
M26	adapt_vector_keys
M28	adapt_paired_runs

The original single-fixture-shape criterion remains unmet by design, but it was superseded by D-013. The new contract, synthetic-vector and boundary requirements were checked through tests/test_dispatch_shapes.py.

The other adapters covered by the contract table are adapt_response, adapt_source_pair, adapt_null_runs, adapt_checker_runs, adapt_events, adapt_halt_recurrence, adapt_clause_ids and adapt_vector_keys (the last is already listed above).
10. Required audit summary
Area	Verdict	Blocker	Major	Minor	Limitation	Method
A1 Fixture runner	FINDINGS	0	0	0	2	Ran / read
A2 Parser and static stages	FINDINGS	0	0	0	1	Read container logs
A3 Runtime and simulation	FINDINGS	0	0	0	1	Read container logs
A4 Serializer and lifecycle	FINDINGS	0	0	0	1	Ran / read
A5 Evidence run	PASS	0	0	0	0	Ran
A6 Freeze record	FINDINGS	0	0	0	1	Not checked
A7 Deviations and mask	FINDINGS	0	0	0	1	Not checked
A8 Specification readings	FINDINGS	0	0	0	1	Ran / read
A9 Sandbox	FINDINGS	0	0	0	2	Ran / read container logs
A10 Claims and disclosure	FINDINGS	0	0	0	1	Partial read
Total		0	0	0	11	

Pack defects noticed (PACK)
No new pack defect established.

The two important provisions are consistent:

File 30, L35:
Runtime inspect.signature must confirm the same parameter names/kinds/counts.

File 36, L48:
Syntactically truncated JSON without provider truncation status.

The first supports the literal runtime introspection requirement. The second supports the complementary stop interpretation without needing the literal word stop.
Checks performed, per area
Area	Checks actually performed
A1	Adapter contracts, value citations, support-table counterexample, dispatch shapes and synthetic-vector tests
A2	Inspected supplied parser/static-stage test evidence; no complete independent parser audit
A3	Inspected worker, process boundary and relevant isolation evidence
A4	Inspected complete-tuple serializer validation and ran regression tests
A5	Recomputed evidence hashes, fixture counts, descriptor integrity and PASS comparisons
A6	No complete freeze-package audit
A7	No independent mask audit
A8	Rechecked halt-signature domains and canonical reserved headings
A9	Inspected worker, evaluator, metadata attacks, clock restrictions and supplied container logs
A10	Reviewed audit brief and relevant disclosure statements, not the complete claims corpus

What was not checked
1. Complete F18 execution by this auditor under CPython 3.11.18.
2. Complete Docker execution by this auditor.
3. Full independent parser, schema and simulator adversarial testing.
4. Full freeze-package and signed-record recomputation.
5. Independent human mask review under Protocol L271.
6. All historical specification readings and every NOT_IMPLEMENTED reason.
7. Hardware-independent elimination of all possible clock channels.
8. All claims and supporting disclosure documents.
No Docker execution is claimed.
11. Overall statement
CLEARED
D-022 re-audit verdict: CLEARED

Both targeted MAJOR findings have been addressed:
1. A1-1: The current stop citation supports the complementary no-provider-truncation case.
2. A9-2: Literal inspect.signature is now called after import, and its names, kinds and counts must agree with the trusted measurement.
Regression checks found A4-1, A8-1, A8-2 and A9-1 remain fixed.

No new BLOCKER or MAJOR finding was established in the targeted scope.

Important qualifications:
- The semantic support-table validator has a demonstrated limitation.
- The SELF_REPORTED runtime-forgery residual remains open.
- The original single-fixture-shape criterion remains unmet under its superseded interpretation.
- The full implementation audit has 11 named coverage limitations.
- F18 is not passed.
- This audit does not itself satisfy Protocol L555 (5).
- Independent human mask review L271 remains unmet.
- This report does not authorise any LLM call or confirmatory execution.
Final distinction: D-022 is cleared. This is not a declaration that the complete OpenVEF implementation, its experimental validity, or its outstanding independent-review requirements are cleared.

Auditor: OpenAI GPT-6
Operator: Krishika
Implementation author: Claude / Anthropic, via Claude Code
Date: 26 November 2026 (UTC)
Manifest: 327/327 verified
Overall D-022 verdict: CLEARED