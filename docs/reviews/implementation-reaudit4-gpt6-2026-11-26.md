OpenVEF — Independent Implementation Audit #4

Re-audit #4
 Audit in progress

Operator: Krishika
Auditor: Independent implementation auditor (ChatGPT GPT-6)
Author: Claude / Anthropic via Claude Code
1. Bundle identity
SHA-256 — computed directly from the uploaded ZIP bytes
93b249a61eac478304162e52d856f6a5185ed32338582716103a7891585a1907


- ZIP size: 853,974 bytes.
- Hash algorithm: SHA-256.
- Hash verification: Computed, not copied from the bundle.
All subsequent findings in this report refer to this exact bundle hash.
2. Manifest verification
325 / 325 verified
I checked every entry in MANIFEST.sha256 against the actual uncompressed file bytes.
Check	Result
Manifest entries	325
Entries matching SHA-256	325
Missing files	0
Hash mismatches	0
Malformed entries	0
Unlisted bundle files (excluding manifest)	0

Manifest verdict: PASS.

The audit brief was read from the uploaded bundle. Its requirement that the audit distinguish actual execution from source inspection and container-log inspection will be followed.
3. Environment and evidence provenance
Item	Audit observation
Auditor model	GPT-6
Python available in audit environment	3.13
Required project interpreter	CPython 3.11.18
Docker run by this auditor	No
Container-test evidence	Read and hash-checked
F18 run	Inspected, not rerun

The container-test evidence reports 382 passing tests. I independently verified:
- Its SHA256SUMS entries.
- All 90 container-test source hashes against the bundle.
- The recorded container image identity.
- The recorded CPython 3.11.18 interpreter hash.
These checks establish internal consistency of the supplied evidence, not independent proof that the tests ran. I will not describe the Docker tests as auditor-executed tests.
4. Priority audit findings
A9-2 — Runtime proof and artifact isolation
The new architecture makes an important improvement: inspect_source() uses a separate worker process and compiles source without importing or executing it.

The separation itself is sound in principle. However, two separate questions must be answered:
1. Does the static proof correctly identify the source constructs it claims to prove?
2. Can the source change what the runtime later measures?
The following distinction is important: a successful compile-only signature measurement does not establish that the function remains unchanged after import.

Finding under investigation: the allow-list and its attribute restrictions must be evaluated against indirect access paths, not just direct imports and obvious dunder expressions.

The documented SELF_REPORTED residual is explicitly acknowledged in docs/sandbox.md lines 165–171 and docs/DEVIATIONS.md lines 172–181. D-020 does not claim to eliminate it. That disclosure is appropriate, but it does not establish that every source marked PROVEN is actually safe.
A1-1 — Revised adapter criterion
The original single-fixture-shape criterion is not met: five adapters still support shapes used by individual fixtures.

I distinguish this from the revised D-013 criterion, which permits those shapes only with a supported input contract and at least three meaningful synthetic vectors.

There is a concrete remaining citation problem:

runner/adapter_contracts.py:
- Lines 39–41 cite Protocol File 02 L144 for both length and stop.
- Lines 121–123 describe stop as the complement of the truncation condition, but cite only File 02 L144 and File 30 L7.
The actual pack text is:

Protocol File 02, L144:
"Provider finish reason explicitly reports max-token truncation"

File 36, L48:
"Syntactically truncated JSON without provider truncation status."

File 36 L48 is the relevant complementary evidence for the stop case. It is absent from the actual DOMAINS citation list.

This is not merely a missing explanatory comment: the citation attached to the selecting value stop does not itself define that value's domain.
A1-1 remains unresolved under D-013
The original criterion remains unmet by design, as disclosed by the owner. The revised criterion also needs correction to the actual citation contract.
A9-2 — Detailed attack assessment
Result: No successful bypass of the PROVEN fragment found by source analysis and the reviewed adversarial tests.

The following attack was specifically checked:
import collectionsdef create_driver(seed):    worker = collections._sys.modules["__main__"]    return Driver()



This was the previous route to the artifact worker's actual module namespace. The revised runtime_basis.py rejects it because collections._sys is not in the permitted module-attribute list.
SELF_REPORTED, not PROVEN
I also checked direct attempts to access interpreter internals:
print.__self__object.__subclasses__()globals()getattr(1, "x")g = (x for x in ())g.gi_frame.f_globals



These are rejected by the fragment checks. The container-test suite additionally exercises these cases and the previous worker-global forgery techniques.

What remains possible

A source outside the proven fragment can still execute:
def v(*a):    return "COMPLETE"Driver.step = v



It can also return a non-Driver object and forge the worker's response.

This is not a newly discovered bypass of PROVEN. It is the explicitly documented SELF_REPORTED residual.

The implementation's adversarial tests demonstrate that these sources are classified SELF_REPORTED even when the artifact worker can be made to accept forged runtime reports (tests/test_artifact_isolation.py, lines 302–320).

Assessment: The distinction between PROVEN and SELF_REPORTED is meaningful and the known attacks are not silently classified as PROVEN. I did not establish an additional source that passes the PROVEN checks while changing Driver.step, replacing check_trace, or returning a non-Driver object.
Compile-only inspection
The implementation has two separate measurement paths:
1. sandbox/artifact_proc.py, lines 85–95, starts a fresh process for inspection.
2. sandbox/artifact_worker.py, lines 312–322, uses compile() and dis to obtain code-object parameters without executing the supplied source.
The normal factory path in sandbox/harness.py, lines 52–73, compares those trusted parameters with the artifact process's post-import report.

The compile-only process does not share the artifact worker's module namespace. Consequently, changing sys.modules["__main__"], parameters, send, or a function's code object in the execution process does not change the separate inspection process.

The import-time attack is also addressed: tests/test_artifact_isolation.py, lines 268–274, uses a helper default expression to attempt to replace the worker's parameters function before measurement. The trusted measurement still rejects the wrong Driver.step signature.

Limitation: I could not execute this path under the pinned CPython 3.11.18 environment. My available Python is 3.13.5, and the worker's bytecode inspection is explicitly version-sensitive. An attempted local invocation under 3.13.5 encountered a changed MAKE_FUNCTION instruction representation. I do not treat that as a defect in the pinned 3.11 implementation.

The supplied container logs report the relevant forged-runtime tests passing, but those are read evidence, not my own Docker execution.
D-019 residual disclosure
The disclosure is substantially honest and correctly distinguishes:
- Source-level PROVEN signatures.
- Post-execution signatures reported by the artifact process.
- The factory return type reported by the artifact process.
- Evaluator-side classification of plain returned data.
The consequence is also correctly identified: a SELF_REPORTED artifact can be counted valid despite a forged return-type or signature report.

One qualification is important: PROVEN is a proof about the specific runtime-check properties, not a proof that the entire artifact complies with every pack restriction. For example, the documented unseeded random.Random() residual remains separate.

The residual is not closed. D-019 should therefore not be represented as complete elimination of A9-2.
5. D-020 — SELF_REPORTED policy
Disclosure and analysis policy consistent
The policy in docs/sandbox.md lines 174–184 and docs/F1-F17-plan.md lines 415–428 is explicit:
Analysis	Treatment
Primary validity endpoint	Count runtime reports as measured
Sensitivity endpoint	Count every SELF_REPORTED artifact invalid
Additional reporting	Count SELF_REPORTED artifacts per arm and design
F18 fixture verdict	Retain original PASS/FAIL status and attach label

This is an owner decision, not a change to the pack's runtime requirements.

The policy does not claim that SELF_REPORTED reports are trustworthy. It deliberately presents the primary result and the conservative sensitivity separately.

My judgment: This is an honest policy for presenting the unresolved risk. It is not equivalent to proving the validity endpoint. The primary result remains exposed to the documented false-validity possibility.
6. D-021 — Results labels and bundle builder
Verified in supplied evidence
A. SELF_REPORTED label in results.jsonl notes

The implementation in runner/run_f18.py, lines 443–453, appends the label without replacing an existing note.

tests/test_self_reported_label.py, lines 60–80, tests:
- A SELF_REPORTED fixture with no previous note.
- A SELF_REPORTED fixture with an existing note.
- A fixture that never reaches runtime checks.
- A fixture with only PROVEN checks.
The container log reports all three test methods passing.

I independently inspected the F18 results:
Check	Observed
Results records	144
SELF_REPORTED fixtures	1
Fixture	M06
Status	PASS
Label in note	Present
Per-record label fields	Present
Summary label	Present
Summary fixture/file list	M06:driver.py

B. Bundle build_commit

tools/build_audit_bundle.py, lines 44–47 and 62–67:
- Rejects a dirty working tree.
- Separates the source commit from the build commit.
- Records git rev-parse HEAD as build_commit.
tests/test_audit_bundle.py, lines 82–100, tests that:
- The ZIP's build commit equals HEAD.
- The source commit remains distinct when appropriate.
- The printed SHA-256 matches the generated ZIP.
- A dirty tree prevents bundle creation.
The container log reports both test methods passing.

The supplied BUNDLE-INFO.json records:
source_commit: 818712146ea46c3237bbe297e94de1b086b8b985
build_commit:  818712146ea46c3237bbe297e94de1b086b8b985


Because the ZIP contains no Git history, I cannot independently authenticate those commit IDs against a repository. The builder's behaviour is supported by its test and source inspection.

Additional A9-2 finding — __signature__ metadata bypass

MAJOR
 SELF_REPORTED

A further issue emerged when comparing the actual runtime measurement with the exact Protocol requirement.

Pack requirement — File 30, L35:
Runtime inspect.signature must confirm the same parameter names/kinds/counts.

The worker's code_parameters() in sandbox/artifact_worker.py, lines 264–278, reads the underlying code object's parameters. It does not call inspect.signature.

I tested this source:
class Driver:    def step(self, cycle_index, outputs_after_edge):        return "COMPLETE"def create_driver(seed):    Driver.step.__signature__ = object()    return Driver()



Results of my local Python 3.13.5 checks:
Check	Result
Static source stages	Accepted
Runtime basis	SELF_REPORTED
Underlying code parameters	Correct
Actual inspect.signature(Driver.step) after factory execution	Raises TypeError
Runtime code-object measurement	Still reports the correct parameters

This demonstrates a difference between the pack's specified introspection check and the implementation's code-object measurement.

The attack does not defeat PROVEN: it is correctly classified SELF_REPORTED. However, the runtime implementation can accept a source for which the required inspect.signature operation fails.

Why this matters to D-020: the sensitivity policy counts this source invalid, which is appropriate. The primary validity endpoint still treats the artifact's runtime report at face value.

Required disclosure: D-019 should explicitly document that post-import checking reads code-object parameters and ignores __signature__/__wrapped__ metadata, rather than describing the operation simply as runtime inspect.signature verification.

This does not invalidate the separation between the trusted compile-only process and the artifact process. It does mean that the residual-risk description is not yet complete.
7. Recheck of previous findings
Previous finding	Result	Evidence
A4-1 — Serializer accepts mismatched records	RESOLVED	serializer.py lines 84–116; test_auditor_case_a4_1 passes
A8-1 — Halt-signature component domains	RESOLVED	ledger.py lines 67–87; validation now covers all five components
A8-2 — M18 / A-053 reading	RESOLVED	assembler.py lines 32–35; canonical headings match the sidecar
A9-1 — Artifact modifies evaluator serialization	RESOLVED	Separate artifact worker, isolated process and plain-data protocol
A9-2 — Runtime-check forgery	PARTIALLY RESOLVED	Trusted compilation measurement works in principle; runtime metadata and SELF_REPORTED residual remain

A4-1
The serializer validates the complete tuple:

(stage_id, error_class, diagnostic)

It does not accept a diagnostic merely because the diagnostic string belongs to the grammar.

The previous adversarial case:
("CHECKER_NULL", "WRONG_CLASS", "COMPILE_ERROR|file=driver.py|line=1")



is explicitly tested and rejected.
A8-1
The previous halt-signature issue is fixed.

Protocol File 02, L185, specifies five component domains and a reason-to-component mapping. HaltSignature.given() now validates:
- Design ID.
- Halt code.
- Evaluator component.
- Stable error class.
- Stable diagnostic code.
The implementation also validates the component relationship for each halt code.
A8-2
The nine reserved headings are present in the implementation and tested against the sidecar's canonical block_inventory.

M18 no longer depends on a caller-supplied list to define the authoritative headings.
A9-1
The original shared-process vulnerability is addressed.

The artifact worker does not import the evaluator. Its output crosses a framed plain-data protocol. The evaluator reconstructs data rather than accepting artifact-created objects.

The supplied container tests also cover forged protocol frames, forged result lines and attempts to modify worker globals.

I found no regression in the original A9-1 attack path.

8. A-057 — Specification-reading judgment
DEFENSIBLE, WITH A CITATION QUALIFICATION
The relevant pack evidence is:

Protocol File 02, L144:
Provider finish reason explicitly reports max-token truncation

Fixture Catalog File 36, L48:
Syntactically truncated JSON without provider truncation status.

Fixture P11b, L5 and L10:
Syntactically truncated JSON without provider truncation status.

"provider_finish_reason": "stop"


My interpretation:
- length is the explicitly reported max-token-truncation case.
- stop is the non-truncation-status case represented by P11b.
- The interpretation is supported by the combination of the fixture descriptor and catalog, not by File 02 L144 alone.
I consider A-057's reading (ii) defensible for this fixture.

However, this does not repair the missing File 36 L48 citation in adapter_contracts.py. The interpretation and the actual implementation contract need to agree.

9. Consolidated area verdicts
The brief requires PASS only where the relevant checks were actually made. Unchecked areas are not silently marked PASS.
Area	Verdict	Blocker	Major	Minor	Limitation
A1. Fixture runner	FINDINGS	0	1	0	0
A2. Parser / schema	FINDINGS	0	0	0	1
A3. Import policy / AST	FINDINGS	0	0	0	1
A4. Serializer / lifecycle	FINDINGS	0	0	0	1
A5. Evidence / results	PASS	0	0	0	0
A6. Freeze / provenance	FINDINGS	0	0	0	1
A7. Mask / evaluation validity	FINDINGS	0	0	0	1
A8. Specification readings	FINDINGS	0	0	0	1
A9. Sandbox / runtime security	FINDINGS	0	1	0	1
A10. Claims / disclosure	FINDINGS	0	0	0	1
Total		0	2	0	8

The limitations above are coverage limitations, not eight additional implementation defects.
Formal findings
A1-1 — MAJOR: Incomplete domain citation for stop.
- Files: runner/adapter_contracts.py:39–41, 121–123.
- Test weakness: tests/test_dispatch_shapes.py:203–210.
- Required correction: include File 36 L48 in the provider-finish-reason domain and associate stop with the relevant evidence. The test should check the semantic support for the value, not merely whether its citation belongs to the property's citation list.
A9-2 — MAJOR: Runtime code-object measurement does not implement the literal inspect.signature requirement.
- Files: sandbox/artifact_worker.py:264–278.
- Supporting path: sandbox/artifact_proc.py:85–100.
- Adversarial example: Driver.step.__wrapped__ set to a variadic function while its underlying code signature remains correct.
- Required correction: either implement the specified runtime introspection check or obtain an explicit, documented and approved interpretation allowing code-object signatures instead. Document the metadata-override case and test it.
A9-2 residual — LIMITATION:

SELF_REPORTED sources can still forge runtime reports. D-020 makes this visible and provides a conservative sensitivity analysis, but does not eliminate the primary endpoint's exposure.

10. Checks performed versus reasoned
Check	Method	Outcome
Uploaded ZIP SHA-256	Ran	Computed
All 325 manifest entries	Ran	PASS
Planning-pack SHA256SUMS	Ran	172 available entries verified; 91 absent entries ignored
Container evidence SHA256SUMS	Ran	PASS
Container test suite	Read supplied logs	382/382 PASS
F18 source hashes	Ran	All 48 entries match
F18 results hash	Ran	Matches summary
F18 expected fixture records	Ran	All 144 match descriptors
F18 PASS records	Ran	127/127 match expected records
Runtime-basis attack examples	Ran locally under Python 3.13.5	SELF_REPORTED as expected
Full runtime-basis tests	Read container logs; attempted local subset	Container 3/3 PASS; local environment mismatch
Compile-only isolation	Read source and container tests; reasoned	No cross-process influence path found
__wrapped__ / __signature__ case	Ran local static and introspection checks; reasoned about worker acceptance	A9-2 finding
A4-1 serializer case	Read source and test log	PASS
A8-1 and A8-2	Read source, pack and test logs	PASS
A-057	Read pack and reasoned	Defensible
D-020 label and sensitivity	Read source, results and tests	PASS as a policy
D-021 build-commit test	Read source and test logs	PASS
Docker execution by this auditor	Not run	Not claimed
Full CPython 3.11.18 rerun by this auditor	Not run	Not claimed

11. Final disposition
NOT CLEARED
The implementation is materially improved, but this re-audit does not support unconditional clearance.
Reasons:
1. A1-1 remains open: the revised D-013 adapter criterion is not fully supported by the actual provider-finish-reason citation contract.
2. A9-2 remains open: the SELF_REPORTED residual is real, and the additional inspect.signature metadata discrepancy is not fully documented.
3. D-020 is acceptable as an explicitly disclosed analysis policy, but its primary validity endpoint must not be presented as independently verified for SELF_REPORTED artifacts.
4. D-021 is supported: the SELF_REPORTED result labels and bundle build-commit checks are consistent with the supplied evidence.
5. No successful PROVEN-fragment bypass was established, but a full independent CPython 3.11.18/Docker re-execution remains outstanding.
6. The F18 results are not evidence of complete F18 clearance: 127 fixtures are PASS and 17 remain NOT_IMPLEMENTED.
Recommended next action: Correct the A1-1 citation contract, resolve or formally approve the A9-2 runtime-signature interpretation, add the metadata-override regression test, rebuild the bundle and request another independent audit.

Auditor disclosure: This report is produced by GPT-6, an AI auditor, not a human auditor. I am not Claude/Anthropic and did not author the implementation. ChatGPT has participated in earlier project reviews, so this is an independent implementation re-audit, not an audit by an entirely uninvolved party.

Operator: Krishika
Final verdict: NOT CLEARED.