# OpenVEF — 10-minute faculty demo, 2 December 2026

**Presenter:** Krishika. **Co-owner:** Ayush Kumar Singh. Script prepared by Claude (Claude Code) under D-023;
every number below comes from committed evidence or a saved report, cited by ID.

| Time | Part |
|---|---|
| 0:00–1:00 | (a) What OpenVEF is |
| 1:00–5:00 | (b) Live commands (four) |
| 5:00–7:30 | (c) The audit story, #1 → #5 |
| 7:30–9:30 | (d) What is not done |
| 9:30–10:00 | Close; questions |

If any live command fails, switch to (e), the 60-second fallback, and continue with (c).

**Before the demo:** open the Codespace, `cd` to the repository root, start Docker, and run
command 4 once to warm the image. Every command in (b) is copy-paste ready.

---

## (a) What OpenVEF is (1 minute)

OpenVEF is a planned, reproducible study of hardware-verification code written by language models. A model
writes a paired *driver*, which steps a cycle-exact RTL design, and *checker*, which judges the recorded trace. The
harness runs both on the original design and on mutated versions, to measure whether the checker catches real faults
without false alarms. The method is fixed in advance in a frozen planning pack (v1.3.6, 144 mandatory
parser/harness fixtures), and the pack requires every evaluator component to be built and independently audited
**before any model is called**. What we show today is that evaluator, built only for a 4-entry × 8-bit FIFO
(feasibility scope, Protocol L555 step 4). **No LLM has been called by any code in this project.**

---

## (b) Live commands (4 minutes)

Run from the repository root. Outputs below were captured on 26 Nov 2026 (files in `docs/demo/`).

### 1. The frozen pack is byte-verified (30 s)

```
(cd baseline/OpenVEF_Planning_v1_3_6 && sha256sum -c --ignore-missing --quiet 27_SHA256SUMS.txt && echo "pack verified")
```
Expected output:
```
pack verified
```
Say: every pack file we use matches the published hash list; the pack is read-only.

### 2. The F18 fixture run, pinned interpreter (60 s)

Evidence run **`run-20261126T144718Z`** (commit `793089b`, pinned image `python:3.11.18-slim` by digest).
```
python3 -c "import json;s=json.load(open('evidence/run-20261126T144718Z/summary.json'));print('run',s['run_started_utc'],'commit',s['git_commit'][:7]);print(s['counts'],'total',s['total']);print('python',s['python_version'].split()[0],'-',s['interpreter_status']);print('SELF_REPORTED:',s['runtime_checks_self_reported']);print('cleared under DEV-001:',s['deviation_cleared_fixtures'])"
```
Expected output:
```
run 20261126T144718Z commit 793089b
{'PASS': 127, 'FAIL': 0, 'NOT_IMPLEMENTED': 17, 'ERROR': 0} total 144
python 3.11.18 - PINNED (D-002a: runner and artifacts in the pinned image)
SELF_REPORTED: ['M06:driver.py']
cleared under DEV-001: ['M07', 'M31', 'M32', 'M33', 'M57', 'P01', 'P14', 'P21', 'P42']
```
Say: 127 of 144 match the expected outcome byte for byte, none fail, 17 cannot be run because the pack does not
define their input or outcome. **That is not an F18 pass** (see (d)). Nine passes carry a deviation label, and one
carries a SELF_REPORTED label, shown next.

### 3. One rejection: M06, a driver that lies about its type (75 s)

```
python3 -c "import json;d=json.load(open('baseline/OpenVEF_Planning_v1_3_6/41_F18_Fixture_Inputs/M06.json'));print(d['description']);print(d['input']['response_object']['driver']['source'])" && grep '"fixture_id": "M06"' evidence/run-20261126T144718Z/results.jsonl | python3 -c "import json,sys;r=json.load(sys.stdin);print('status  :',r['status']);print('expected:',r['expected']['diagnostic']);print('actual  :',r['actual']['diagnostic']);print('runtime :',r['runtime_checks']);print('note    :',r['note'])"
```
Expected output:
```
Factory returns non-Driver object
import random

def create_driver(seed):
    driver = Driver()
    driver.rng = random.Random(seed)
    return object()

class Driver:
    def step(self, cycle_index, outputs_after_edge):
        return "COMPLETE"

status  : PASS
expected: ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE
actual  : ENTRY_POINT_REJECT|file=driver.py|symbol=create_driver|reason=RETURN_TYPE
runtime : {'checker.py': {'basis': 'PROVEN', 'reason': 'closed fragment'}, 'driver.py': {'basis': 'SELF_REPORTED', 'reason': 'return value at line 6'}}
note    : [SELF_REPORTED (D-020): runtime check not statically PROVEN: driver.py]
```
Say: the factory returns `object()` instead of a `Driver`; the evaluator rejects it with the exact diagnostic the pack
expects. The return type is only known from the process that ran the artifact's code, so the evaluator labels the
result **SELF_REPORTED**: a hostile artifact could have lied about it. The label is kept visible (D-020).

### 4. One isolation attack (75 s)

```
.venv/bin/python -I tests/test_artifact_isolation.py -v IsolationTests.test_system_access_is_denied
```
Expected output (about 6 s):
```
test_system_access_is_denied (__main__.IsolationTests.test_system_access_is_denied) ... ok

----------------------------------------------------------------------
Ran 1 test in 4.026s

OK
```
Say: the test plays a hostile artifact that tries to escape the sandbox: open `/proc/<pid>/mem` and `environ`,
write to another process's output, read the harness source, write files, fork, exec, kill its parent. Every attempt
must fail, and it does. This live run uses the Codespace's development Python; the same test passes in the pinned
image in **`container-tests-20261126T145729Z`** (387 of 387 tests pass), which is the evidence.

---

## (c) The audit story, #1 → #5 (2.5 minutes)

No independent human implementation auditor was available, so under deviation **DEV-002** the audit was done by a
different AI model (OpenAI GPT-6), operated by Krishika. Reports and author's notes are in `docs/reviews/`.

| # | Date | Bundle (SHA-256) | Verdict | BLOCKER | MAJOR | Limitations | Response |
|---|---|---|---|---|---|---|---|
| 1 | 25 Nov | `e0ee23ff…fa01` | FINDINGS (no overall clearance) | 1 (A1-1: runner branches only one fixture reaches) | 1 (A8-1) | 4 | D-012 to D-014 |
| 2 | 25 Nov | `34bc8109…c0c0` | NOT CLEARED | 2 (A1-1, A9-1: artifact code shared the evaluator's interpreter) | 1 (A4-1) + A8-2 cross-reference | 3 | D-015 to D-018 |
| 3 | 25 Nov | `b1235ba3…327d` | NOT CLEARED | 2 (A1-1, A9-2: runtime checks the artifact could forge) | 0 | 2 | D-019 to D-021 |
| 4 | 26 Nov | `93b249a6…1907` | NOT CLEARED | 0 | 2 (A1-1 citation, A9-2 literal `inspect.signature`) | 8 | D-022 |
| 5 | 26 Nov | `5bdc25ea…2cc2` | **CLEARED for D-022** | 0 | 0 | 11 | D-023 |

Say:
- Audits #1–#4 each found real problems; each was accepted, fixed and sent back. Audit #5 found none, only limitations. **D-023:** the sequence #1–#5 is complete
  with no open BLOCKER or MAJOR.
- Audit #5's clearance is **scoped to D-022**; its own report says it is not a clearance of the whole implementation.
- **The pass count moved 139 → 123 → 127 around audit #1.** A rule was tightened after the finding, then replaced
  (D-013) so that five fixtures came back; changing a rule after an adverse finding is disclosed wherever the count
  is quoted.
- The auditor could not run Docker or the pinned Python; it read the container logs and re-checked hashes.

---

## (d) What is not done (2 minutes)

- **L555 step (5), independent re-audit: not done.** The five audits are AI audits under DEV-002, not a human
  independent audit, and the owners do not mark the step done.
- **F18 is not passed.** 17 fixtures are NOT_IMPLEMENTED (15 have no input or outcome defined in the pack; M42 and
  M47 need halt signatures the Protocol does not allow, PD-01).
- **Independent mask review (L271): unmet.** 9 passes are "cleared under DEV-001 (non-independent review saved)";
  the mask was drafted by Claude and accepted by Krishika with a saved, non-independent Claude review.
- **Two disclosed limitations stay open:** the SELF_REPORTED residual (an artifact outside the provable fragment can
  still forge its runtime report; reported as measured and with every SELF_REPORTED artifact counted invalid, D-020),
  and A1-1-L1 (the citation-support test is not a semantic proof).
- **Feasibility controls:** F14 and F15 pass; the other 14 wait for owner-written mutants, drivers and checkers
  (`controls-20261126T144918Z`: 2 PASS, 14 BLOCKED_OWNER_ARTIFACTS).
- **Readings:** many passes rest on Claude's readings of ambiguous pack text, approved as decided without itemised
  owner review (D-009). The pack has 26 recorded defects (`docs/pack-defects.md`).
- **Ayush's ratification** of decisions Krishika signed alone is pending (D-008).
- **AI assistance is disclosed:** the FIFO specification, RTL and mask were drafted by Claude via Claude Code. If a
  Claude model is ever evaluated, that is reported as a potential familiarity confound.
- **The LLM-call gate (step 6) stays closed.**

---

## (e) 60-second fallback (if live commands fail)

The outputs of all four commands were captured on 26 Nov 2026 and saved in `docs/demo/`, each file headed by its
command, time and commit:

```
cat docs/demo/1-pack-verify.txt docs/demo/2-f18-summary.txt docs/demo/3-m06-rejection.txt docs/demo/4-isolation-attack.txt
```
If the terminal itself is unavailable, open the same files in the editor, or show the expected outputs in (b).
Say: "These were captured from the same commands; the underlying evidence runs are `run-20261126T144718Z` and
`container-tests-20261126T145729Z`, both in the repository." Then go on to (c).
