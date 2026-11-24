# Readings decided by Claude under the standing delegation

**For:** the owners and the independent implementation auditor.
**Prepared by:** Claude (Claude Opus 5.5, via Claude Code), 24 Nov 2026. It approves
nothing.

**Status (D-009, Krishika, 24 Nov 2026):** every reading decided under the standing
delegation and not yet owner-approved (A-007..A-012, A-013 tie, A-015..A-037, A-039,
A-045..A-052, F15 case table) is approved by Krishika as decided, without itemised owner
review.

**What is listed:** exactly those readings, kept here so they stay auditable. The full
text is in [ambiguities.md](ambiguities.md), and the approved hashes are in
`design/fifo/freeze/readings-approval-D-009.json`. Readings approved in the freeze
(A-038, A-040–A-044; [FREEZE-RECORD-2026-11-24.md](FREEZE-RECORD-2026-11-24.md)) and
owner decisions (A-001–A-006, A-013 main rule, A-014, A-015 case 2, A-033's owner
correction) are not listed.

**How to read the "Dependants" column:**
- *changes:* the fixture's result would differ under the competing reading;
- *on path:* the fixture runs through the code that implements the reading, but no
  record shows its result would change;
- *none:* no current fixture reaches the case.

**D-012, D-013 (after the DEV-002 audit):** D-009's approval of **A-031 is withdrawn**, and
A-031 is reversed. These fixtures no longer have an adapter, and the Dependants cells naming
them describe an earlier state: M36 (A-012), M13 (A-025), M37 (A-028), M15 (A-029), M14, M17
and M41 (A-032), M53 (A-033).

**A-053 is new and owner review is pending** (what counts as a cited input contract, D-013). It
is **not** covered by D-009. It affects M16, M18–M20, M25, M26, M28, M29, M40, R01–R06, R08–R13,
M10–M12, P18, P19 and P22.

## Readings

A-045–A-052 and the F15 case table affect only the feasibility controls, not F18.

| ID | Question | Decision taken | Pack basis | Dependants |
|---|---|---|---|---|
| A-007 | When `driver.py` is empty and `checker.py` has a syntax error, which wins? | Finish every SOURCE_AST check on `driver.py` before `checker.py` → `SOURCE_EMPTY\|file=driver.py` | File 30 §3 L27 "process each source file in this order"; Protocol §3.4 step (2) file order | none (M16 on path; same under both) |
| A-008 | Is a leading U+FEFF in a JSON source string a BOM, and at what position? | Rejected as the BOM before the empty check: `SOURCE_SYNTAX_REJECT\|…\|line=1\|column=1` | File 30 §3 L27 "strict UTF-8 decode with BOM rejection"; File 30 §1 no silent normalization | none |
| A-009 | A source string that cannot be UTF-8 (lone surrogate): stage and position? | `SOURCE_SYNTAX_REJECT` at SOURCE_AST, `line=1\|column=1` | Stage map "Invalid UTF-8/BOM or syntax parse error"; column rule "absent … emit `column=1`" (02 L127) | none |
| A-010 | Which characters count as whitespace for SOURCE_EMPTY? | Python source whitespace only: space, tab, form feed, CR, LF | Stage map "Empty/whitespace-only source"; Python Language Reference 2.1.2, 2.1.9 | none (P12a, P12b, M16 on path; same under every reading) |
| A-011 | A SyntaxError with no usable line, or another exception from `ast.parse`? | `line=1`; any other exception is a syntax parse error at `line=1\|column=1` | Column-rule fallback (02 L127); `LINE` must be positive | none |
| A-012 | (1) How are `{driver_source, checker_source}` inputs fed? (2) M36's `{source_file, syntax_error}` vector: what disposition? | (1) SOURCE_AST directly on the two strings, no invented wrapper. (2) Apply the column rule; disposition `CONTROL_EXPECTATION`, keyed on input shape | (1) Protocol §3.4 step (2). (2) 02 L177 "exercises a serializer, protocol or lifecycle rule"; column rule 02 L127 | **changes: M36** (NOT_IMPLEMENTED → PASS); on path: M16, M29 |
| A-013 tie | Two IMPORT_POLICY findings with an identical source key: which wins? | File 30 §3 L27 stage order: module body, then import, then prohibited name, then `random` use | File 30 §3 L27 stage list; File 30 §2 L19–L20 | none |
| A-015 (cases 1, 3–11) | Module-body statements the text does not classify (`x += 1`, `x: int`, `pass`, a later string, `...`, `-True`, `-(-1)`, call in an annotation, `global`, `return`) | Accepted: `x: int` only. `NON_LITERAL_CONSTANT`: `...`, `-True`, `-(-1)`. Everything else: `MODULE_EXECUTABLE` (table in A-015) | 02 L135 "allow only …"; File 30 §3 L29 literal-only types | none (P28, M04a, M04b, M57 on path) |
| A-016 | Prohibited names: are `def open`, parameters and `__builtins__.open` flagged? | Only `ast.Name` nodes in any context, and `builtins.<name>` attributes; definitions, parameters and `__builtins__` are not | File 30 §2 L19 "AST `Name` nodes …", "A `builtins` attribute …"; File 30 §3 (definitions not classified in IMPORT_POLICY) | on path: P24a–d, M24, M34 (M24 is consistent with this form) |
| A-017 | Is `random.<attr>` checked syntactically, or only when `random` is the imported module? | Syntactic | File 30 §2 L20 "the module name `random`"; 02 L133 | none (M09, M22, M23 same under both) |
| A-018 | Non-ASCII identifiers inside an f-string replacement field (one STRING token on 3.11)? | Not scanned (token rule as written); CPython 3.11-specific gap to be disclosed | File 30 §2 L21; 02 L133 "STRING and COMMENT tokens are not scanned" | none |
| A-019 | Does a lone CR end a line for the identifier scan? | Yes, as `ast.parse` counts lines; the scanner tokenizes a copy with each lone CR replaced by LF | File 30 §2 L21 / 02 L133 (line-prefix column); Python Language Reference 2.1.2 | none |
| A-020 | Which parameters does each of PARAMETER_NAMES, PARAMETER_KIND, DEFAULT_OR_VARIADIC compare? | Names: positional parameters in order. Kind: any positional-only. Third check: defaults, `*args`, keyword-only, `**kwargs` | 02 L164 check order; File 30 §3 L33, L35, L37 | on path: M05, P15, P26 (and the other AST_SIGNATURE fixtures) |
| A-021 | What counts as a "binding" in the required-symbol pass? | `def`/`async def`/`class`, assignment or valued annotated assignment, or import binding the name, in the scope's own body | 02 L164; Python Language Reference 4.2.1 | on path: M60, M61, M67 |
| A-022 | `Driver` class-body statements other than methods and nested classes? | `DRIVER_CLASS_FORM` at rank 4, except a docstring and literal plain-name constants | File 30 §3 L35; B5 (File 19 L25, File 30 L52); 02 L125 "No unlisted value" | none |
| A-023 | Source position of definition violations in the global sort | The `ClassDef`/`FunctionDef` node's own position; rank 4 uses the `Driver` class or the A-022 statement | 02 L164 global sort key; rank 7 wording | none (only same-category ties) |
| A-024 | A compile error with no line, or another exception from `compile()`? | `line=1` (as A-011) | Stage map `COMPILE_ERROR\|file\|line`; `LINE` positive | none |
| A-025 | Vocabulary of `events` inputs, and ranking when several occur | One stage-map row per event kind (`EVENT_ROWS`); rank by (step, row, file, line); unknown kinds NOT_IMPLEMENTED | 02 L139 "first applicable row …"; L166 evaluation order; L125 domains | **changes: R01–R06, R12, R13, M13** (cannot run without a vocabulary) |
| A-026 | Meaning of the four checker run-outcome record forms (`checker_runs`, `null_runs`) | Mapped to timeout / runtime error / return-invalid / verdict (table in A-026); verdict records are summaries, not raw returns | File 30 L74, L97; 02 L166 (11); Catalog L10 | **changes: R08–R11, M10–M12, P18, P19, P22** |
| A-027 | Vector checks whose parameters are not supplied (no widths; prose predicate) | Run checks in order; a failure stands; if every runnable check passes, NOT_IMPLEMENTED; missing keys before extra keys; prose not executed | File 30 L83 (a)–(e); 02 L125 reason order | **changes: M26** (EXTRA_KEYS); M27 stays NOT_IMPLEMENTED |
| A-028 | A response plus a supplied later-stage outcome | Run every stage available; a failure stands; otherwise the supplied outcome stands in for L166 (7)–(10) | 02 L166 evaluation order | **changes: M10–M12, P18, P19, P22, M37** (on path: M28, R07) |
| A-029 | Serializer: what makes a diagnostic "normative"? | Must match the closed grammar and, when supplied, the emitted set; else `NON_NORMATIVE_DIAGNOSTIC` | 02 L168; L94–L125 templates and domains; Catalog L18 | **changes: M15** (on path: M14, M17) |
| A-030 | Clause-ID packet checks: order, missing regexes, line endings | Near-match before set equality; File 31 §8 defaults when a regex is omitted; LF normalization | File 31 L11, L27, L28, L30, §8 | **changes: M20** (default regex); on path: M18, M19, M40 |
| A-031 **(reversed, D-012)** | Descriptor halt signatures outside the L185 domains (lower-case components, `RecorderFault`) | Constructed signatures enforce L185; supplied signatures compared as given. **Pack inconsistency flagged** | 02 L185 domains and recurrence rule | M42, M47: now NOT_IMPLEMENTED (PD-01) |
| A-032 | Control-vector expectations with extra keys | Compared as a whole object; each extra key computed from a cited rule; property names taken from the descriptors (disclosed) | Catalog requirement 2; 02 L168 (2), (3); L176; L183–L185 | **changes: M14, M17, M41** |
| A-033 (field derivations) | Which lifecycle-vector fields have a supporting Protocol sentence? | Change class matched to its Protocol case; only fields with a supporting sentence produced (table `LIFECYCLE_CASES`) | 02 L175, L176, L181, L183, L185 | **changes: M53** (PASS); M48, M50, M54, M58 stay NOT_IMPLEMENTED |
| A-034 | An exception while importing an artifact module | `driver.py`: `RUNTIME_EXCEPTION\|…\|phase=factory\|class=C`; `checker.py`: `CHECKER_RUNTIME_ERROR\|class=C` | Stage map phases (`factory` earliest); File 30 L97 | none (no fixture raises on import; on path: every fixture reaching the runtime stage) |
| A-035 | Order of post-construction checks; when `check_trace`'s signature is checked | Return type, then `create_driver`, then `Driver.step`; `check_trace` in the checker's own process | 02 L166 (7); B7; File 30 L35/L37 | on path: M06 and every fixture reaching the runtime stage |
| A-036 | Hash randomization in the sandbox | `PYTHONHASHSEED=0`, set by the evaluator | File 30 §6 "deterministic execution"; 02 L166 (8) | none (isolation tests); affects every paired run |
| A-037 | Driver import/factory that never returns; F18 factory seed | Evaluator ERROR, not a REPAIR verdict; seed 0; 20 s build-default limit | Stage map watchdog row is `phase=driver_step` only | on path: M06 and every runtime-stage fixture |
| A-039 | `class` token for `iverilog`/`vvp` failures; budget overrun outside `step` | `CalledProcessError` / `TimeoutExpired`; overrun inside `step` is `WATCHDOG_TIMEOUT` | 02 L154; L125 "the simple Python exception class name" | none |
| A-045 | How is the mask-aware miter built (predicate side, assumption source, reset, initial state)? | Legal-input predicate on the null side; assumption generated from the spec's own predicate by exhaustive enumeration; reset vectors forced; registers zero-initialised; shortest counterexample by ascending bounds | 02 L278, L291, L293; FIFO-043 | F4, F5 |
| A-046 | Harness events → §12 terminations in a pair run | `driver_runtime`/`driver_vector`/`simulator_error` → driver/simulator error; `driver_watchdog` → timeout; `trace_integrity` → INVALID_PAIR | 02 L306, L311, L333 | F3–F12, F17 |
| A-047 | A null run that fails inside a pair | INVALID_PAIR (integrity, cause undetermined) | 02 L311, L336 | F3–F12, F17 |
| A-048 | Checker invocations per pair | One, on the frozen mutant trace; byte-identity to the null trace recorded | §12 "checker returns"; L247, L435 (repeat rule elsewhere) | F6–F12 |
| A-049 | Panel false-alarm event per benign trace (two evaluations) | One event if either evaluation returned FAIL | 02 L417, L423, L429 | F17, F15 (panel cases) |
| A-050 | Which mutant traces the panel evaluates; "valid" in F5 | EXPOSED (`Q_ds`) and raw-only traces; "valid" = `rd_valid` | 02 L427, L435, L514 | F17, F5 |
| A-051 | Non-deterministic fields excluded in F1 | Trace bytes compared exactly; only `waveform` excluded from run records (FST header date, observed) | 02 L510, L551 | F1 |
| A-052 | F14 "ports" comparison | Same set of (name, direction, width); order recorded, not a pass condition | 02 L233, L523 | **F14** (PASS rests on this) |
| F15 case table | Are the hand-built cases and known answers right? | 16 pair cases (each citing its §12 line), worked known answers for the ledger, panel cases; see `src/openvef/f15.py` | 02 L303–L328, L350–L411, L417–L437, L524, L529 | **F15** (PASS rests on this) |
