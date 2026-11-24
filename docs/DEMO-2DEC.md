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
  - specification, RTL, null-netlist export (Yosys) and an observation-mask draft;
  - simultaneous read/write at full and a registered almost-full as its documented
    corner cases.
- **Fixture runner and evidence records:** hashes of every input, the interpreter, the
  image and the source files.

## Results (latest evidence run `run-20261124T163535Z`, pinned image)

| PASS | FAIL | NOT IMPLEMENTED | ERROR | Total |
|---|---|---|---|---|
| 139 | 0 | 5 | 0 | 144 |

**What to say about these numbers:**
- **F18 is not passed.**
- **10 of the 139 passes are provisional.** The FIFO materials are now frozen
  (FREEZE-2026-11-24), but the independent human reviewer hasn't signed the mask yet.
- **Several other passes rest on readings that still need owner review.** The pack was
  ambiguous in places; those readings are logged and decided under a delegation.
- **The 5 NOT IMPLEMENTED are blocked by defects in the pack itself, not by missing
  code.** One fixture (M27) is unsatisfiable as written (PD-25), and four have no
  supporting Protocol sentence (A-033).
- **The pack has 25 recorded defects** (pack-defects.md).
- **AI-assisted, disclosed:** the FIFO specification, RTL and mask drafts were written
  by Claude via Claude Code and are reviewed by the owners. If a Claude model is ever
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
   provisional.
   ```
   python3 -c "import json;s=json.load(open('evidence/run-20261124T163535Z/summary.json'));print(s['counts']);print(s['python_version']);print(s['interpreter_status']);print('provisional:',s['provisional_fixtures'])"
   grep '"fixture_id": "M27"' evidence/run-20261124T163535Z/results.jsonl | python3 -c "import json,sys;r=json.loads(sys.stdin.read());print(r['status'],'-',r['note'])"
   ```
6. **What is open** (60 s): open `docs/OWNER-FREEZE-PACKAGE.md` (what the owners sign
   next) and `docs/AUDIT-READINESS.md` (what the independent auditor will check).

*Optional, if there is time:* start a full containerized run at the beginning, writing
outside the evidence tree, and show its counts at the end. It takes a few minutes, so
time it beforehand.

```
OPENVEF_EVIDENCE_ROOT=/tmp/openvef-demo runner/run_f18_container.sh demo
```
