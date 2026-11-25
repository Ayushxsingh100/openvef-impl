OpenVEF implementation audit report
Auditor model and version: OpenAI GPT-6
Operator (human who ran the audit): Krishika
Date (UTC): 25 November 2026
Not a Claude model, not the implementation author: Yes
Implementation author: Claude (Anthropic), via Claude Code.

Bundle SHA-256:
34bc810934c4865eede3142e876efb54bd83de8ed10ec177f4f2c607744ec0c0


MANIFEST.sha256 verified
All 277 manifest-listed files passed sha256sum -c MANIFEST.sha256. The uploaded archive contains 279 ZIP entries, including the manifest and bundle information.
Summary
BLOCKER found
The re-audit identified a critical sandbox-integrity vulnerability: artifact code can modify the shared Python json module used by the simulator recorder. This permits artifact code to influence evaluator-generated trace and result data.

The audit also found that the D-013 adapter relaxation does not fully satisfy its own input-contract requirement for M18.
Earlier findings: explicit resolution decisions
Earlier finding	Re-audit verdict	Reason
A1-1 — BLOCKER	Not fully resolved	The original strict criterion is still violated by five single-fixture input shapes. Under D-013, four adapters satisfy the revised requirements; M18's input contract does not adequately establish the canonical reserved-heading domain.
A8-1 — MAJOR	Resolved	The A-031 reading has been reversed. Supplied halt signatures are now validated against Protocol L185, and M42/M47 are NOT_IMPLEMENTED rather than incorrectly passing.

The previous GPT-6 report itself is not included in this bundle. Consequently, the precise original wording of A8-1 cannot be independently recovered; the resolution above concerns the A-031 issue identified in the change records.
Area verdicts
Area	Verdict	Blocker	Major	Minor	Limitation
A1. Fixture runner	FINDINGS	1	0	0	0
A2. Parser/static stages	FINDINGS	0	0	0	1
A3. Runtime/simulation/checker	FINDINGS	0	0	0	1
A4. Serializer/assembler/lifecycle	PASS	0	0	0	0
A5. Evidence run	PASS	0	0	0	0
A6. Freeze record	PASS	0	0	0	0
A7. Deviations/mask	FINDINGS	0	0	0	1
A8. Readings	FINDINGS	0	1	0	0
A9. Sandbox	FINDINGS	1	0	0	0
A10. Claims/disclosure	FINDINGS	0	0	1	0

The limitations are material: this environment has CPython 3.13.5 rather than the pinned CPython 3.11.18, and Docker is unavailable.
Detailed findings
A1-1 [BLOCKER] M18 does not have a sufficiently grounded input contract
Files and lines:
- runner/adapter_contracts.py: 79–82
- runner/run_f18.py: 269–270
- tests/test_dispatch_shapes.py: 57–69, 72–85
Exact pack text:

File 31, L9:
Each model-visible block starts at an exact complete line equal to one of the nine reserved headings in the sidecar.

File 31, L11:
Reject unknown, duplicate, missing or malformed headings. Reject a payload line that is exactly equal to any reserved heading after LF normalization.

Check performed:

M18 supplies:
{
  "payload": "line 1\n[Design specification]\nline 3",
  "reserved_headings": ["[Design specification]"]
}


The adapter calls:
check_reserved_heading_lines(    desc["input"]["payload"],    desc["input"]["reserved_headings"])



The problem is that the adapter trusts the descriptor-supplied heading list. It does not establish that this list is the canonical nine headings defined by the sidecar.

The contract cites File 31 L11 but does not cite the actual sidecar definition establishing the complete domain.

The dispatch tests check that quotations are verbatim. They do not check that the cited text actually establishes every input property's domain.

Expected: The adapter must use or validate against the canonical sidecar heading set.

Actual: Arbitrary caller-supplied headings determine the rejection.

Ran or reasoned: Ran all 13 test_dispatch_shapes.py tests successfully under Python 3.13.5. The semantic deficiency was identified by code inspection.

Confidence: High.

Resolution decision: A1-1 remains unresolved.
- Original strict criterion: five single-fixture input shapes remain.
- D-013 criterion: four adapters satisfy the revised checks; M18 does not.
- D-013's three-vector minimum is also insufficient as a general guarantee against overfitting: the test measures distinctness, not semantic coverage or canonical input-domain enforcement.
A4-1 [MAJOR] Serializer accepts mismatched stage/error-class records
File and lines: src/openvef/serializer.py: 92–97, 124–128.

Exact pack text — Protocol L168:
The serializer accepts only a complete diagnostic emitted by the authoritative stage map.

Check performed:

I supplied this adversarial input:
Failure(    "CHECKER_NULL",    "WRONG_CLASS",    "COMPILE_ERROR|file=driver.py|line=1")



Expected: Reject the record because its stage and error class do not correspond to the diagnostic emitted by the authoritative stage map.

Actual: feedback_bytes() accepts it and serializes:
{
  "stage_id": "CHECKER_NULL",
  "error_class": "WRONG_CLASS",
  "diagnostic": "COMPILE_ERROR|file=driver.py|line=1"
}


The implementation checks the diagnostic grammar but does not validate the stage/error-class/diagnostic combination. The optional emitted argument in check_diagnostic() is not supplied by feedback_bytes().

This is a real helper-level contract violation, although I found no current caller of feedback_bytes() in the bundled runner.

Ran or reasoned: Ran the adversarial input under Python 3.13.5 and observed the incorrectly accepted serialization.

Confidence: High.
A8-2 [MAJOR] D-014's A-053 reading is not fully supported for M18
This is the same underlying contract defect identified in A1-1, viewed from the specification-reading perspective.

Files and lines: runner/adapter_contracts.py: 79–82; docs/READINGS-REVIEW.md: 30–32.

Exact pack text: File 31 L9 and L11, quoted above.

Expected: A-053 must establish the meaning and domain of every input property, including the canonical reserved-heading domain.

Actual: The M18 contract cites a generic rejection rule without establishing the canonical heading set. D-014's approval cannot substitute for that missing evidence.

Ran or reasoned: Reasoned from the contract, sidecar and adapter implementation.

Confidence: High.
A9-1 [BLOCKER] Artifact code can modify evaluator serialization
Files and lines:
- sandbox/harness.py: 37–39, 76–82, 98–110
- sandbox/sim_cocotb.py: 15–19, 42–56, 145–152, 205–219
- src/openvef/import_policy.py: 212–237
Exact pack text — File 30 L101:
The runtime sandbox denies network, filesystem access beyond the designated temporary output directory, environment variables, wall-clock reads, subprocess and simulator access.

Problem:

The artifact and simulator recorder share the same Python process during simulation.

The artifact is allowed to import json. That import returns the same mutable module object used by sim_cocotb.py.

The trusted recorder calls:
json.dumps(row)json.dump(result, f)



at sim_cocotb.py lines 47 and 56.

Artifact code can replace those module functions during create_driver(). The replacements remain active after the artifact's function returns.

Concrete adversarial input tested:

A driver that imports json, saves the original json.dump and json.dumps, and replaces them with functions that:
- substitute serialized trace rows;
- substitute the final result.json content;
- preserve ordinary serialization for unrelated objects.
I ran this source through:
- check_sources
- check_import_policy
- check_ast_signature
All three accepted the adversarial source
The test ran under Python 3.13.5, not inside Docker. The shared-module execution path is established by the bundled source; actual container exploitation was not run.

Expected: Artifact code must not be able to modify evaluator-owned recorder functions or forge the evaluator's trace/result records.

Actual: The import allow-list restricts module imports but does not isolate mutable module state. The artifact can alter functions subsequently used by trusted evaluator code.

Ran or reasoned: Static adversarial input ran successfully; end-to-end exploitation reasoned from the simulator execution path.

Confidence: High.

Severity rationale: This is an evaluator-integrity failure. It can undermine the validity of trace comparisons and subsequent checker evaluation. It must be fixed before relying on simulation-backed results.
Remaining audit areas
A2 — Parser and static stages
LIMITATION
Inspected:
- Envelope and schema validation.
- Source UTF-8, BOM and syntax handling.
- Import-policy precedence.
- AST signatures and entry-point validation.
- Prohibited names and non-ASCII identifier scanning.
Execution results:
- The available interpreter was CPython 3.13.5.
- The pinned runtime required by the project is CPython 3.11.18.
- tests/test_import_policy.py has a version-dependent failure in test_fstring_identifier_not_scanned_on_311.
The test explicitly documents its CPython 3.11 assumption. I do not classify that failure as an implementation defect.

Expected: Full adversarial verification under CPython 3.11.18.

Actual: Static inspection and partial execution only.

Verdict: Cannot certify the pinned-runtime behavior.
A3 — Runtime, simulation and checker
LIMITATION
Inspected:
- sandbox/harness.py
- sandbox/sim.py
- sandbox/sim_cocotb.py
- src/openvef/simulation.py
- src/openvef/simulator_stages.py
- src/openvef/trace.py
- src/openvef/stage_map.py
Docker was unavailable.

Consequently, these tests could not be completed:
Test suite	Docker-dependent tests skipped
Sandbox	18
Simulation	25
FIFO RTL	7
Netlist export	4
Miter alignment	7

I reviewed scheduler ordering, trace recording, watchdog handling, paired-run comparison and checker isolation statically.

The A9 vulnerability is particularly important here: the runtime import restriction does not provide isolation from shared Python module state.

Verdict: Implementation inspected, but runtime behavior not independently demonstrated.
A4 — Serializer, assembler and lifecycle
FINDINGS
The serializer finding A4-1 is described above.

Other checks:
- Reserved-heading detection.
- Placeholder rejection.
- Clause-ID extraction and comparison.
- UTF-8 truncation.
- JSON serialization.
- Halt-signature validation.
- Lifecycle recovery and repeated-halt handling.
Executed successfully:
- tests/test_local_rules.py: 23 tests.
- tests/test_lifecycle.py: 5 tests.
- tests/test_doc_quotes.py: 1 test.
The tests pass, but they do not catch the mismatched stage/error-class case.

Verdict: Not clean because of A4-1.
A5 — Evidence run
PASS
Evidence inspected:

evidence/run-20261124T203551Z/
Recorded F18 results
127
PASS

17
NOT_IMPLEMENTED

0
FAIL

0
ERROR



144 mandatory fixtures accounted for

Independently checked:
- All 144 descriptor SHA-256 values.
- All descriptor byte lengths.
- Expected versus actual fixture results.
- Results JSONL hash.
- Fixture-index hash.
- Response-schema hash.
- 45 recorded source-file hashes.
- Dockerfile and requirements-lock hashes.
- Recorded interpreter and image identities.
All recomputed file hashes matched their recorded values.

The nine DEV-001-labelled passes are:

P01, P14, P21, P42, M07, M31, M32, M33, M57.

They are not equivalent to independently reviewed passes.

Important: The evidence run's recorded result is internally consistent. That does not establish that the evaluator is secure against adversarial artifacts.
A6 — Freeze record
PASS
Inspected:
- docs/OWNER-FREEZE-PACKAGE.md
- docs/FREEZE-RECORD-2026-11-24.md
- design/fifo/freeze/freeze-record-2026-11-24.json
- D-010 and D-011 amendments.
- DEV-001 hash-bound record.
- D-009 reading approvals.
tests/test_freeze_package.py passed all 13 tests.

Verified:
- 20 signed freeze items, A1–F1.
- Mask section G is not treated as signed.
- DEV-001 clears only the specified mask reason and only for matching hashes.
- D-009 contains 39 retained decisions after A-031 withdrawal.
- Changes to frozen files are detected.
No finding.
A7 — Mask and deviations
LIMITATION
Inspected the primary and stricter FIFO masks and their traceability table.

The mask's principal behavior is internally consistent:
- rd_data is masked only during the documented don't-care window in the primary mask.
- Predicate signals remain observable.
- The stricter variant compares rd_data throughout.
- The traceability table includes specification clauses and excerpts.
tests/test_fifo_mask.py passed seven tests, with one Docker-dependent test skipped.

Independence status:

Protocol L271 and File 21 L32 remain unmet.

This is disclosed correctly:
- DEV-001 explicitly records the deviation.
- The Claude review is identified as non-independent.
- Claude Code did not perform the sign-off.
- Section G of the owner-freeze package remains unsigned.
- The stricter-mask review checkbox remains unconfirmed.
The label cleared under DEV-001 (non-independent review saved) is appropriately qualified.

I do not treat the absence of an independent reviewer as a newly discovered defect because the deviation is explicitly recorded.

Limitation: Actual null-trace X/Z validation and RTL/null comparison could not be independently exercised without Docker.
A8 — Reading decisions
FINDINGS
I reviewed A-012 and the A-025–A-033 decisions, including their implementation, citations and affected fixtures.

Earlier A8-1 resolution:

The D-012 correction is substantively correct.
- HaltSignature.given() validates the Protocol L185 domains.
- M42's lowercase simulator component is invalid.
- M47's lowercase recorder component is invalid; its TRACE_INTEGRITY_FAILURE signature also has an invalid non-NONE error class.
- Both fixtures now produce NOT_IMPLEMENTED with PD-01.
The valid-signature recurrence path also conservatively returns NOT_IMPLEMENTED because the pack does not specify the required error-class mapping (PD-26).

D-013 and D-014:

The four restored adapters other than M18 have documented input contracts and synthetic tests.

The M18 problem is detailed in A8-2 above. The D-014 approval does not cure that missing domain definition.

The 17 NOT_IMPLEMENTED results:

The dispositions are conservative and do not constitute false PASS results.
- 15 fixtures have no adapter satisfying the revised contract requirements, or have unsupported input/outcome fields.
- M42 and M47 are blocked by PD-01.
- Valid repeated-halt signatures still lack a fully specified output mapping under PD-26.
I found no justification for converting those blocked cases into PASS.
A10 — Claims, provenance and disclosure
PASS
Checked:
- docs/DEMO-2DEC.md
- docs/AUDIT-READINESS.md
- docs/DEVIATIONS.md
- docs/assistance-log.md
- docs/traceability.md
The bundle appropriately discloses:
- Claude Code implementation authorship.
- AI-assisted specification, RTL and mask development.
- Non-independent mask review.
- The 139 → 123 → 127 count changes.
- D-013's changed adapter rule and need for re-audit.
- The distinction between PASS and NOT_IMPLEMENTED.
- The fact that an AI audit is not a human independent audit.
It also explicitly says F18 has not passed.

No material overstatement of audit completion was identified.

Final disposition
NOT CLEARED
The implementation is not ready to be treated as independently audited or as having passed F18.
Finding	Severity	Status
A1-1: M18/D-013 input-contract failure	BLOCKER	Open
A4-1: Serializer accepts mismatched failure records	MAJOR	Open
A8-2: A-053/M18 contract deficiency	MAJOR cross-reference	Open
A9-1: Artifact can modify evaluator serialization	BLOCKER	Open
A2-1: Pinned Python verification	Limitation	Outstanding
A3-1: Docker runtime verification	Limitation	Outstanding
A7-1: Full mask/runtime verification	Limitation	Outstanding

A8-2 cross-references the same underlying M18 problem as A1-1; it is not an additional independent defect.
Required remediation order
1. A9: Isolate artifact execution from evaluator modules and recorder state. Prevent mutation of shared interpreter modules. Add adversarial tests that attempt to forge trace rows and result records.
2. A1: Fix M18 so the canonical sidecar headings, not descriptor-supplied arbitrary values, determine the check. Strengthen D-013 contract validation.
3. A4: Validate the complete stage/error-class/diagnostic tuple before serialization.
4. A2/A3/A7: Repeat verification under the pinned CPython 3.11.18 Docker image, including end-to-end simulation and mask checks.
5. Rebuild the bundle, regenerate evidence, and perform another independent re-audit.
Final identity record
- Model: OpenAI GPT-6
- Human operator: Krishika
- Implementation author: Claude (Anthropic), via Claude Code
- Audit type: AI implementation re-audit, not human independent audit.
- Audited archive SHA-256: 34bc810934c4865eede3142e876efb54bd83de8ed10ec177f4f2c607744ec0c0
Bottom line: D-012 made a meaningful correction, and A8-1 is resolved. However, D-013 did not completely resolve A1-1, the serializer has a separate major defect, and the sandbox permits artifact-to-evaluator interference. The implementation must not be cleared until the two blockers are addressed.