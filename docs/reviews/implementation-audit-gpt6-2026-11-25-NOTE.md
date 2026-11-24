# Note on the implementation audit (DEV-002)

**Not part of the report.** Written by Claude (Claude Opus 5.5, via Claude Code), the
implementation author, at Krishika's instruction. Replaces the first version of this note,
which was written before the report was available (in git at `2ddd67c`).

- **Report saved verbatim:** [implementation-audit-gpt6-2026-11-25.md](implementation-audit-gpt6-2026-11-25.md),
  uploaded by Krishika, 20,968 bytes, SHA-256 `3dfa0865bf1d3c187930ecd63ffb2aac8f0716d2e66e69bd8f865e40e4820296`,
  which matches the prefix and suffix Krishika gave (`3dfa0865…0296`). Claude did not edit it.

**Bundle hash**
- The report states `e0ee23ff6e29ec78c5310405edd6dd50d7625a8893c75bffdbd0d026464fa01`. That is
  63 hex digits, so it can't be a SHA-256.
- The real value is `e0ee23ff6e29ec78c5310405edd6dd50d7625a8893c75bffdb0d6d026464fa01`. They agree except for
  `…ffdbd0d026464fa01` against `…ffdb0d6d026464fa01`. That is consistent with a transcription
  error, as Krishika stated.
- **Independent support that this was the audited zip** (the zip at `9c89b1c`, checked by
  Claude): it has 274 manifest entries, 172 pack files that verify and 27 input shapes; its
  `results.jsonl` digest is `8268ca65…81c1`; its run is `run-20261124T195537Z`; and the
  quoted code and test counts match. All are as the report says. The hash error stays an error
  in the report; this does not correct it.

**First note checked against the report**
- *A1-1 and A8-1:* confirmed. A1-1 is **BLOCKER** and A8-1 is **MAJOR**. The first note lacked
  the severities, and no document stated them.
- *Limitations A2, A3, A5, A9:* confirmed as LIMITATION findings. What was not checked:
  - A2: nothing ran on CPython 3.11.18. The audit used 3.13.5, where one f-string test failed;
    the report treats that as a version mismatch.
  - A3: no container-backed simulation, watchdog or two-process checker run (Docker absent; 18
    sandbox tests and 25 simulation tests skipped).
  - A5: the image and interpreter were not inspected, and commit IDs could not be checked.
  - A9: no live hostile-artifact test; sandbox read only, confidence Medium.
- *PASS areas:* A4, A6, A7 and A10.

**Facts about the report a reader should know**
- **The operator is not identified**, and the version given is "OpenAI GPT-6" only. DEV-002
  requires the exact model and version. The prompt is not recorded.
- **A1-1 cites two shapes.** It says singleton shapes were identified and discusses M27 and
  M36. The audited bundle had 17 shapes used by one fixture, which D-012 acted on more
  widely. D-013 then replaced that rule.
- **A1-1 partly quotes the brief**, which the implementation author wrote.
- **A7 is PASS on the mask,** but the report does not replace the L271 human review, and says so.
- The report does not say F18 has passed or L555 (5) is satisfied.

**The code changed after this audit** (D-012, D-013), so it does not cover the current code.
**Triage is not independent:** it was by Claude (claude.ai), the same family as the author.
