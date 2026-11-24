# OpenVEF — faculty demo, 2 December 2026

**Presenter:** Krishika. **Co-owner:** Ayush Kumar Singh.

## What OpenVEF is

OpenVEF is a planned, reproducible study of **LLM-generated hardware-verification
artifacts**.
- **The artifact:** a model writes a paired *driver*, which steps a cycle-exact RTL
  design, and *checker*, which judges the recorded trace.
- **Mutation qualification:** the harness runs both on the original design and on
  mutated versions, to measure whether the checker catches real faults without false
  alarms.
- **The plan:** the methodology is fixed in a frozen planning pack (v1.3.6: 58 numbered
  documents, files 01–63, and 144 parser/harness fixtures).
- **The gates:** the pack requires every evaluator component to be built and
  independently audited before any LLM is called. **No LLM has been called by any code in
  this project.**

## What has been built (limited FIFO feasibility scope, Protocol L555 step 4)

- **Parser and validator** for model responses: envelope, JSON schema, strict Python AST
  policy, import policy, entry-point signatures and compilation.
- **Sandbox:** generated code runs in locked-down containers (no network, read-only,
  non-root, resource limits). The pinned runtime is CPython 3.11.18 by image digest.
- **Simulation harness:** Icarus Verilog plus cocotb, a reactive driver loop, four-state
  traces, paired original/null-netlist runs with a masked comparison, and checker runs
  in separate processes.
- **A 4-entry × 8-bit FIFO design:**
  - specification, RTL, null-netlist export (Yosys), frozen 24 Nov 2026
    (FREEZE-2026-11-24: Krishika's signature under governance rule D-008; Ayush's
    ratification pending);
  - an observation mask, accepted by the owner under deviation DEV-001 because no
    independent reviewer is available (not independently reviewed);
  - simultaneous read/write at full and a registered almost-full as its documented
    corner cases.
- **Fixture runner and evidence records:** hashes of every input, the interpreter, the
  image and the source files. Each run re-checks the frozen files against their signed
  hashes.
- **Feasibility-control harness (F1–F17):** built and unit-tested. F14 (export
  repeatability) and F15 (ledger identities) pass; each rests on a D-009 approval. The other controls wait
  for owner-written mutants, drivers and checkers.

## Results (latest evidence run `run-20261124T203551Z`, pinned image)

| PASS | FAIL | NOT IMPLEMENTED | ERROR | Total |
|---|---|---|---|---|
| 127 | 0 | 17 | 0 | 144 |

**What to say about these numbers:**
- **F18 is not passed.**
- **No pass is marked provisional, but 9 of the 127 carry a label:** "cleared under
  DEV-001 (non-independent review saved)". No independent mask reviewer is available, so
  Krishika accepted the mask with a saved Claude (claude.ai) review. Claude Code drafted the
  mask, so the review is not independent. The Protocol's independent signature (L271) is still missing.
- **Many passes rest on readings of ambiguous pack text.** Claude decided them under a
  delegation. Krishika approved them as decided, without itemised owner review (D-009); A-053 is approved (D-014), subject to re-audit.
  They are listed in `docs/READINGS-REVIEW.md`; R01–R13 and several M-fixtures would
  change under a competing reading.
- **The count went 139, 123, 127 around an AI audit. Say so.** Krishika accepted a finding
  against runner branches only one fixture could reach, and all 15 were removed (123). The rule
  was then replaced (D-013): an adapter now needs pack text that defines its input, plus
  synthetic tests. Five came back and one more went (127). Changing a rule after a finding
  needs a re-audit, which hasn't happened.
- **The 17 NOT IMPLEMENTED:** 15 have an input or outcome the pack doesn't define, and two
  (M42, M47) supply halt signatures the Protocol doesn't allow (PD-01).
- **The audit was by an AI model, not a human (DEV-002).** It found one
  blocker and one major issue, and could not run Docker or the pinned Python. The corrected
  code has not been re-audited. The report is in `docs/reviews/`.
- **The pack has 26 recorded defects** (pack-defects.md).
- **AI-assisted, disclosed:** the FIFO specification, RTL and mask drafts were written
  by Claude via Claude Code. The specification and RTL were approved by Krishika in the
  freeze; the mask is accepted under DEV-001. If a Claude model is ever
  evaluated, that is reported as a potential familiarity confound.
- **Benchmark overlap is disclosed.** The closest public match is GateTruth's
  synchronous FIFO; FIFO designs are not novel, and no novelty is claimed.

## 5-minute live demo (run from the repository root)

**Before the demo:** Docker running; run `.venv/bin/python -I tests/test_fifo_rtl.py`
once to warm the image (about 15 s).

1. **The frozen planning pack is byte-verified** (30 s). The 61 skipped entries are
   historical `archive_*` files that are not extracted.
   ```
   (cd baseline/OpenVEF_Planning_v1_3_6 && sha256sum -c --ignore-missing --quiet 27_SHA256SUMS.txt && echo "pack verified")
   ```
2. **The design under test** (60 s). Show the specification clauses and the 66-line RTL.
   ```
   sed -n '/^## \[Design specification\]/,/^### Worked example/p' docs/fifo-spec-v0.2.md | head -60
   cat design/fifo/rtl/ovf_fifo.v
   ```
3. **The spec is checked mechanically** (15 s): clause IDs, the executable legal-input
   rule, and the worked example against a model.
   ```
   .venv/bin/python -I tests/test_fifo_spec.py -v
   ```
4. **The real RTL in the sandbox** (30 s): the worked example on the RTL, and an illegal
   driver (a write while full) caught as `ILLEGAL_PROTOCOL_STATE`.
   ```
   .venv/bin/python -I tests/test_fifo_rtl.py -v FifoRtlTests.test_worked_example_on_rtl FifoRtlTests.test_check_e_rejects_write_while_full_without_read
   ```
5. **The evidence record** (60 s): counts, the pinned interpreter, and which results are
   provisional or cleared under DEV-001.
   ```
   python3 -c "import json;s=json.load(open('evidence/run-20261124T203551Z/summary.json'));print(s['counts']);print(s['python_version']);print(s['interpreter_status']);print('provisional:',s['provisional_fixtures']);print(s['deviation_labels'],s['deviation_cleared_fixtures'])"
   grep '"fixture_id": "M27"' evidence/run-20261124T203551Z/results.jsonl | python3 -c "import json,sys;r=json.loads(sys.stdin.read());print(r['status'],'-',r['note'])"
   ```
6. **What is open** (60 s): open `docs/DEVIATIONS.md` (the unmet mask review) and `docs/AUDIT-READINESS.md` (what the auditor will check; DEV-002: an AI model, not a human independent auditor).

*Optional, if there is time:* start a full containerized run at the beginning, writing
outside the evidence tree, and show its counts at the end. It takes a few minutes, so
time it beforehand.

```
OPENVEF_EVIDENCE_ROOT=/tmp/openvef-demo runner/run_f18_container.sh demo
```
