# Note on document audit #1 of the v1.3.7 CANDIDATE (D-026 item 3)

**Not part of the report.** Written by Claude (Claude Opus 5.5, via Claude Code), the implementation author and
the author of every correction under audit, at Krishika's instruction.

**Copy and hash**
- [doc-audit1-gpt6-2026-11-27.md](doc-audit1-gpt6-2026-11-27.md): 40,540 bytes,
  SHA-256 `ba81408bde5339291d4b2ef25cab70b5eaa3e518412ecd45cdbeb11f54604b95`.
- Uploaded by Krishika as `docs/doc-audit1-gpt6-2026-11-27.txt` with that hash and size. Claude checked both before
  and after moving the file here byte for byte (renamed only; not edited). The hash shows the file equals what
  Krishika uploaded, not that it equals the auditor's original output.
- **Auditor:** Krishika states the auditor was GPT-6 (OpenAI), operated by Krishika. The report itself does not name
  the model (brief §1 asked it to); its header gives only the role "Independent document auditor".
- **Order:** the report and this note are committed alone, before any D-027 change.

**Bundle hash.** The report gives `c4caff409692797b4292a1c6851c79a722d1c60cbf4371e5611f5ef4f0a4cbd7`, which equals
`dist/openvef-docaudit-bundle.zip` (build commit `8d8be84`, release `docaudit1-c4caff40`).

**What the report says**
- **NOT CLEARED.** Nine findings: 1 BLOCKER (D1-5), 5 MAJOR (D1-1, D1-3, D1-4, D1-6, D1-7), 2 MINOR (D1-8, D1-9),
  1 PACK (D1-2); limitations L-01 to L-05.
- Verdicts: UNSOUND C2, C5, C6 (superseded by A1), C11; SOUND C7, C8, C13, C14, A2, OS-3; SOUND WITH NOTE the rest.
- Positive checks it reports running: manifest 417/417, candidate SHA256SUMS 205/205, baseline 202/202 (61 archive
  entries absent as disclosed), rebuild 206/206 byte for byte from 158 edits, File 25 copy 98/98 lines, zero
  expected-object changes over 144 descriptors, OWNER-SPECIFIED separation PASS.
- It recommends a new numbered correction cycle, keeping v1.3.6 as default, and not reading the development run as F18.

**Checked by Claude against the audited zip** (extracted in a scratch directory): `MANIFEST.sha256` has 417 lines and
verifies; the zip holds 418 files; candidate `SHA256SUMS` has 205 lines; baseline `27_SHA256SUMS.txt` has 263 lines
(202 + 61 archive); the CHANGELOG's last edit is E158; candidate File 10 hashes to `0e6bd491…d974` as stated. The
quoted candidate lines (File 02 L173, L176, L185; File 30 L83; File 36 L3, L176, L198, L206) say what the report
quotes.

**Points to read with care** (kept as written; not resolved here)
- The report calls itself "Independent". It is an AI document audit by a model other than the author, not a human
  independent review, and it is not an implementation audit.
- Notes on C1 (EVALUATOR_REVISION_REQUIRED is an extrapolation), C3 (labels only), C9, C12 (`allowed_diagnostics`
  must not become a source of normative truth), C16 and OS-1 (scope restriction to nonzero pre-halt scores) carry no
  D1 finding number. D-027 addresses only D1-1 to D1-9; those notes stay as written.
- D1-2 is graded PACK, not MAJOR; the report's remediation order still lists it with D1-1 as step 3.

It does not satisfy Protocol L555 (5) or L271, F18 is not passed, and the v1.3.7 candidate remains not audited-cleared.
