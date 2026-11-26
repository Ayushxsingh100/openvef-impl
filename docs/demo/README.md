# Pre-captured demo outputs (fallback for docs/DEMO-2DEC.md, part (e))

Captured on 26 Nov 2026 in the Codespace from the repository root. Each file starts with the capture time, the commit
and the exact command, and ends with its exit code. Files 1–3 read committed evidence and the read-only pack:
`run-20261126T144718Z` (F18, pinned image, commit `793089b`). File 4 is a development run of one unit test on the
Codespace's `.venv` CPython 3.11.18; it is **not evidence**. The evidence for that test is
`container-tests-20261126T145729Z` (pinned image, 387 of 387 pass).

| File | Command |
|---|---|
| `1-pack-verify.txt` | pack hash check against `27_SHA256SUMS.txt` |
| `2-f18-summary.txt` | F18 run summary |
| `3-m06-rejection.txt` | M06 driver source and its F18 record |
| `4-isolation-attack.txt` | `IsolationTests.test_system_access_is_denied` |
