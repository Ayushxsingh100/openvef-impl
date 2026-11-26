# Note on the fifth implementation audit ("Audit #5", DEV-002)

**Not part of the report.** Written by Claude (Claude Opus 5.5, via Claude Code), the
implementation author, at Krishika's instruction.

**Copy and hash**
- [implementation-reaudit5-gpt6-2026-11-26.md](implementation-reaudit5-gpt6-2026-11-26.md): 18,200 bytes,
  SHA-256 `0e56d990e388fbf140f32d6fa7dbb2bf38772e60955e5b680cd00777cb74cc00`.
- Uploaded by Krishika as `docs/implementation-reaudit5-gpt6-2026-11-26.txt`, stated to be an exact copy
  from claude.ai, with that hash and size. Claude checked both before and after moving the file here
  byte for byte (renamed only; not edited). The hash shows the file equals what Krishika uploaded, not
  that it equals ChatGPT's original output. It reads as rendered text (heading marks and table pipes
  missing, code lines joined).
- **Order:** the repository was frozen at `32f222a` (release `audit5-5bdc25ea`) from the bundle's
  publication until Krishika lifted the freeze with this report. The report and this note are committed
  alone, before any D-023 change.
- **Numbering:** it calls itself "Independent Implementation Audit #5". The record now holds one audit and four
  re-audits, so it is the fifth audit and the fourth re-audit. Its scope was D-022 plus regression (AUDIT-BRIEF.md).

**Bundle hash.** The report gives `5bdc25ea3bf0be66f16a0aa5a47737c2b29f8c798f31495ffa670859689b2cc2`, which
equals `dist/openvef-audit-bundle.zip` at `32f222a` and the asset of release `audit5-5bdc25ea`. It names the
upload `openvef-audit-bundle (1).zip` (a browser download name).

**What the report says**
- **D-022 CLEARED.** 0 BLOCKER, 0 MAJOR, 0 MINOR, 11 LIMITATIONs. A1-1 (`stop` citation) and the
  A9-2 literal `inspect.signature` correction RESOLVED; no metadata bypass found; A-058 consistent.
- Regression: A4-1, A8-1, A8-2, A9-1 remain fixed; no wall-clock bypass found, documented residuals remain.
- **Still open, by its own account:** the SELF_REPORTED forgery residual (L-10); A1-1-L1, the support-table
  validator is not a semantic proof; the original single-fixture-shape criterion is unmet (superseded by D-013).
- Not done by the auditor: no Docker, no CPython 3.11.18 (it ran two test files under 3.13.5; 26 of 33
  isolation tests skipped there); container logs read, not rerun. It says F18 is not passed, L555 (5) is
  not satisfied by it, L271 is unmet, and nothing is authorised.

**Checked by Claude against the audited zip:** 327 manifest entries match and the zip holds 328 files;
container-test SHA256SUMS (31 entries) verify; all 90 container-test source hashes match; return code 0,
25 files, 387 passes; per-file counts 22 (`test_dispatch_shapes`), 33 (`test_artifact_isolation`),
26 (`test_local_rules`), 26 (`test_ast_signature`); interpreter hash equal to the F18 run's. The cited
lines (`test_dispatch_shapes.py` 90–109, `adapter_contracts.py` 121–124, `artifact_worker.py` 315–325 and
340–349, `artifact_proc.py` 108–112, `harness.py` 52–73 and 105–117, `test_artifact_isolation.py` 280–324,
`ambiguities.md` 1812–1814 and 1823–1836, `DEVIATIONS.md` 149–160 and 164–184, `sandbox.md` 147–162,
`envelope.py` 67–90) say what the report says. **A1-1-L1 reproduced:** `value_support_problems` returns
no problem when `stop`'s support is `(MEANING, "JSON")` (host Python, development only).

**Points to read with care** (kept as written; not resolved here)
- Its header says "AUDIT IN PROGRESS"; its final statement is CLEARED.
- **The clearance is scoped to D-022.** The report says so ("This is not a declaration that the complete
  OpenVEF implementation … [is] cleared"); 8 of 10 areas are FINDINGS by coverage limitation, and A6 and A7
  were "Not checked".
- `adapt_vector_keys` is listed twice: among the five one-of-a-kind shapes (M26) and again among "the other
  adapters" (the report notes the repeat). The twelve adapters are all named once otherwise.
- Limitation IDs start at L-02. The eleventh is A1-1-L1, which appears to stand in for L-01; no L-01 is named.
- The SELF_REPORTED residual is counted as a limitation (L-10), not a finding; the report still calls it OPEN.

It is an AI audit, not a human independent audit. It does not satisfy L555 (5) or L271, and F18 is not passed.
