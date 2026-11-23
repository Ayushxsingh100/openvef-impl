# Specification ambiguities and open owner decisions

Each item quotes the source, lists the readings, and says what changes. Items marked
PROVISIONAL are implemented one way so work can continue; the owners must confirm or
change them before any evidence run counts toward F18.

Items marked **DECIDED BY CLAUDE** were decided by Claude under the standing delegation
Krishika gave on 23 Nov 2026 (see CLAUDE.md, "Standing delegation"). Each says "decided by
Claude under standing delegation, owner review pending" and gives the textual reason.
They are implemented, but like PROVISIONAL items they must be reviewed by the owners
(both: the delegation came from Krishika alone) before any evidence run that depends on
them counts toward F18.

## A-001 — OUTPUT_TRUNCATED versus envelope rejection (DECIDED — Ayush's confirmation pending)

- Protocol §3.4 stage map lists "Envelope, schema or clause manifest rejection" first and
  "Provider finish reason explicitly reports max-token truncation" second, and says "The
  first applicable row after the exact evaluation order below controls".
- The "Deterministic evaluation order" step (1) names "Response UTF-8/JSON/schema/
  manifest-clause checks" and does not mention the finish reason.
- File 30 §1: truncation "is `OUTPUT_TRUNCATED` at `PARSE_SCHEMA` and is reported separately."
- Fixture P11a: finish reason `length` with truncated JSON expects `OUTPUT_TRUNCATED`.

Readings: (a) truncation is checked before envelope decoding — matches P11a;
(b) table row order applies — P11a would give `SCHEMA_REJECT|pointer=/`, contradicting
its expected value. Unspecified either way: finish reason `length` with complete, valid JSON.

Implemented: (a). Also implemented: `length` always yields `OUTPUT_TRUNCATED`, even if the
JSON is complete.

**Decision:** truncation is checked first (reading (a), as implemented). Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending.

## A-002 — How fixture input shapes are fed to the parser (DECIDED — Ayush's confirmation pending)

The catalog says each descriptor holds "a literal JSON input" but does not define how the
runner turns each input shape into the call under test. 86 fixtures use `response_object`
(an already-decoded JSON object); others use `events`, `null_runs`, `change_class`, etc.

For `response_object`, readings: (a) serialize to UTF-8 JSON bytes and run the full
parser; (b) skip envelope decoding and start at schema validation. For every current
`response_object` fixture both readings should give the same result, because the object
has no duplicate keys and serializes to valid JSON — this is to be confirmed when part 1b
exists.

**Decision:** `response_object` fixtures start at schema validation with the object
as given (reading (b)). Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending. The decision covers `response_object` only; other input
shapes are listed in A-012.

## A-003 — NaN / Infinity tokens (DECIDED — Ayush's confirmation pending)

File 30 §1 requires one JSON object and rejection of malformed JSON. Python's `json`
module accepts `NaN`, `Infinity` and `-Infinity`, which are not JSON under RFC 8259.
Implemented: rejected as JSON syntax (`SCHEMA_REJECT|pointer=/`). No current fixture
exercises this.

**Decision:** `NaN`/`Infinity` are rejected (as implemented). Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending.

## D-001 — Pin the Draft 2020-12 validator (PENDING — one owner confirmation outstanding)

Protocol §3.4: "Use the pinned Draft 2020-12 validator". Register 16 L40 lists the parser
version as TO FREEZE. Schema validation (part 1b) needs an exact `jsonschema` version and
its dependencies, pinned with hashes in `requirements.lock`.

**Not fully decided.** Krishika has confirmed `jsonschema==4.26.0`; Ayush Kumar Singh's
confirmation is pending. Resolved with pip-tools 7.7.0 (`pip-compile --generate-hashes`, separate tools venv) on CPython
3.11.18: attrs 26.1.0, jsonschema-specifications 2025.9.1, referencing 0.37.0,
rpds-py 2026.9.1, typing-extensions 4.16.0. Installed into `.venv` with
`pip --require-hashes`. Register 16 L40 still needs this version recorded as frozen.

## A-004 — `UNSPECIFIED` text must identify the missing behavior (DECIDED — Ayush's confirmation pending)

File 30 §1 L9: "`UNSPECIFIED` is permitted only for behavior not specified in the received
packet, and the text must identify the missing behavior."

Readings: (a) not mechanically checkable; the parser accepts any `UNSPECIFIED` whose text
passes the schema (`minLength` 1) and the requirement is reviewed by humans; (b) the parser
must apply some mechanical test, which the pack does not define (no diagnostic, pointer or
rule is given). Fixture P21 ("UNSPECIFIED used with a non-empty description of missing
behavior") expects acceptance at this stage and is consistent with (a).

Implemented: (a) — `UNSPECIFIED` is accepted with no text check. No pointer exists for a
failure under (b).

**Decision:** `UNSPECIFIED` text is accepted at parse time (reading (a), as implemented).
Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending.

## A-005 — Source of the manifest `clause_ids` for fixtures (DECIDED — Ayush's confirmation pending)

File 30 §1 L9 validates clause IDs "against the exact `clause_ids` array and
`clause_id_regex` in the frozen manifest". No frozen manifest exists yet. Every F18
descriptor has a top-level `manifest_clause_ids` field outside `input`; the catalog does
not say how the runner uses it.

Readings: (a) `manifest_clause_ids` is the frozen-manifest `clause_ids` for that fixture;
(b) the runner should use a frozen manifest file (none exists; File 38 is a template).

Implemented: (a). On `clause_id_regex`: L9's next sentence defines validity completely
("an exact member of that array or the reserved literal `UNSPECIFIED`"), and File 31
L29/L91 applies the regex to each `clause_ids` element at packet freeze. So the response
check is exact membership; the regex is not re-applied to response values (any member
already matches it). If the owners read L9 as requiring a separate regex test on response
values, the outcome is unchanged for every value, because a non-member is rejected
either way.

**Decision:** fixtures use their own `manifest_clause_ids` list (reading (a), as
implemented). Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending.

## A-006 — Sorting array-index tokens in the schema pointer key (DECIDED — Ayush's confirmation pending)

Protocol §3.4 (file 02 L137): "Sort by: (1) instance-token sequence, Unicode code-point
order, shorter equal prefix first". RFC 6901 tokens are strings, so array index `10` sorts before `2`. The
clause-ID rule, by contrast, says "the lowest numeric `assumptions` index".

Readings: (a) literal — compare every token as a string, so `/assumptions/10/text` is
reported before `/assumptions/2/text`; (b) compare array-index tokens numerically, as in
the clause-ID rule.

Implemented: (a), the literal text (unit test `test_array_index_tokens_compare_as_strings`).
It matters only when schema errors exist at two array indexes with different digit
counts (needs ≥ 11 assumptions or dependencies items). No current fixture exercises it.

**Decision:** the two rules stay as implemented: schema-error pointers sort tokens by
Unicode code point (reading (a)); clause-ID rejection uses the lowest numeric index. Source: statement typed by Krishika in claude.ai on 23 Nov 2026 at 21:24 IST, naming Krishika and Ayush Kumar Singh. Ayush's own confirmation is pending.

## A-007 — SOURCE_AST order across files: per file, or by stage-map row (DECIDED BY CLAUDE — owner review pending)

- File 30 §3 L27: "For file-local stages, process each source file in this order: strict
  UTF-8 decode with BOM rejection; empty/whitespace-only rejection; `ast.parse`; …"
- Protocol §3.4 evaluation order: "(2) Source UTF-8/BOM/empty/syntax checks in file order
  `driver.py`, then `checker.py`."
- Protocol §3.4 stage map lists "Invalid UTF-8/BOM or syntax parse error" above
  "Empty/whitespace-only source", and says "The first applicable row after the exact
  evaluation order below controls".

Readings: (a) finish all checks on `driver.py`, then `checker.py`; (b) the row order
decides first, so a syntax error in either file beats an empty file. They differ only
when `driver.py` is empty and `checker.py` has a syntax error: (a) gives
`SOURCE_EMPTY|file=driver.py`, (b) gives `SOURCE_SYNTAX_REJECT|file=checker.py|…`.
Within one file, empty and syntax-error cannot both apply (whitespace-only source
parses). No fixture covers the cross-file case; M16 (both empty) agrees with both.

**Decision (decided by Claude under standing delegation, owner review pending):** reading (a), as implemented (unit test `test_driver_checked_before_checker`). Reason: File 30 §3 L27 is the only text that orders checks *within* a file, and it says to "process each source file in this order", i.e. complete one file before the next; Protocol step (2) also names the file order. The stage-map sentence chooses among rows *after* the evaluation order, so it does not reorder the per-file sequence.

## A-008 — U+FEFF at the start of a source string (DECIDED BY CLAUDE — owner review pending)

Stage map: "Invalid UTF-8/BOM or syntax parse error" → `SOURCE_SYNTAX_REJECT`; File 30 §3
L27: "strict UTF-8 decode with BOM rejection". The source arrives as a JSON string, not
bytes, so "BOM" has no byte meaning here.

Readings: (a) a leading U+FEFF is the BOM and is rejected before the empty check — but
the pack gives no line/column for a BOM rejection; (b) U+FEFF is an ordinary character
and `ast.parse` decides (on 3.11.18 it raises SyntaxError "invalid non-printable
character U+FEFF", line 1, offset 1, so `…|line=1|column=1`); (c) strip it as Python
does when reading a UTF-8-SIG file — excluded by "BOM rejection". (a) and (b) both
reject; they can differ only in the line/column, which the pack does not give for (a).
**Decision (decided by Claude under standing delegation, owner review pending):** a leading U+FEFF is rejected as the BOM, before the empty check: `SOURCE_SYNTAX_REJECT|file=<FILE>|line=1|column=1`. Reason: File 30 §3 L27 requires "BOM rejection" as part of the first step, and File 30 §1 forbids silently normalizing source code, which excludes (c). Readings (a) and (b) both reject; the only open point was the position, and a BOM is at line 1, column 1 by any count, which is also what `ast.parse` reports under (b). U+FEFF later in the source is still left to `ast.parse`. Unit test `test_claude_decided_cases`.

## A-009 — Source string that is not valid UTF-8 (DECIDED BY CLAUDE — owner review pending)

JSON `\ud800` escapes decode to lone surrogates, which cannot be encoded as UTF-8.
`ast.parse` on 3.11.18 raises `UnicodeEncodeError`, not SyntaxError. The stage map
puts this under "Invalid UTF-8 …" → `SOURCE_SYNTAX_REJECT|file=<FILE>|line=<LINE>|
column=<COLUMN>` but says nothing about the line or column. (Raw input of this kind
also passes PARSE_SCHEMA: Python's `json` accepts lone-surrogate escapes.)
**Decision (decided by Claude under standing delegation, owner review pending):** `SOURCE_SYNTAX_REJECT|file=<FILE>|line=1|column=1`. Reason: the stage map assigns invalid UTF-8 to `SOURCE_SYNTAX_REJECT` at SOURCE_AST, so it is not moved to PARSE_SCHEMA (the response bytes themselves are valid UTF-8; File 30 §1's "Reject invalid UTF-8" applies to them). CPython reports no position for this failure, and the only position rule the pack gives for a missing position is the column rule's "absent … emit `column=1`"; line 1 is the same fallback (A-011). Competing reading not taken: report the line/column of the first lone surrogate — more informative, but no text defines it, and it is not "reported by CPython".

## A-010 — Which characters count as whitespace for SOURCE_EMPTY (DECIDED BY CLAUDE — owner review pending)

Stage map: "Empty/whitespace-only source". The pack does not define whitespace.
Readings: (a) JSON whitespace (space, tab, LF, CR); (b) `str.isspace()`, which adds
U+000B, U+000C, U+001C–U+001F, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
U+202F, U+205F, U+3000; (c) Python tokenizer whitespace (space, tab, form feed, newlines).
What changes: a source of only U+000C parses on 3.11.18 (empty module, so it passes
SOURCE_AST under (a)), but is SOURCE_EMPTY under (b) and (c); U+000B or U+00A0 alone is
`SOURCE_SYNTAX_REJECT|…|line=1|column=1` under (a)/(c) but SOURCE_EMPTY under (b).

**Decision (decided by Claude under standing delegation, owner review pending):** reading (c), Python source whitespace: space, tab, form feed, CR and LF (Python Language Reference 2.1.2 line terminators and 2.1.9 whitespace between tokens). A source made only of these is SOURCE_EMPTY; any other character, including U+000B, U+00A0 and U+3000, goes to `ast.parse` (on 3.11.18 those give `SOURCE_SYNTAX_REJECT`). Reason: the check is on Python source, inside a stage whose authority on source is CPython 3.11; JSON whitespace (a) belongs to the response envelope, and `str.isspace()` (b) would call "empty" sources that Python itself rejects as invalid characters. A comment-only source is still not empty. Unit test `test_claude_decided_cases`.

## A-011 — SyntaxError with no usable line, or another exception from ast.parse (DECIDED BY CLAUDE — owner review pending)

The column rule covers a missing offset ("If `offset` is absent, null or less than 1,
emit `column=1`") but nothing covers a missing or non-positive `lineno`, although
`LINE` must be a positive decimal integer. On 3.11.18, a NUL character in the source
gives SyntaxError "source code string cannot contain null bytes" with `lineno=None`.
`ast.parse` may also raise exceptions that are not SyntaxError (e.g. `RecursionError`,
`MemoryError`, `UnicodeEncodeError` — see A-009); the stage map does not say whether
these are "syntax parse error". **Decision (decided by Claude under standing delegation, owner review pending):** a SyntaxError whose `lineno` is missing or less than 1 uses `line=1`, and its column follows the column rule as usual; any other exception from `ast.parse` (e.g. `MemoryError`, which 3.11.18 raises for very deep nesting such as 200,000 unary minus signs) is a syntax parse error with `line=1|column=1`. Reason: `LINE` must be a positive integer and the pack's only rule for a missing position is "If `offset` is absent, null or less than 1, emit `column=1`"; line 1 applies the same fallback. "Syntax parse error" in the stage map is read as "`ast.parse` did not produce a tree". Competing reading not taken for NUL bytes: report the line of the first NUL — not given by CPython or the text. Unit tests `test_claude_decided_cases`, `test_non_syntax_error_from_parse_is_line_1_column_1`.

Related observation (no change): the column rule says to emit "the positive one-based
source-character column reported by CPython". On 3.11.18 `ast.parse` of a `str` reports
a character offset (`é = 1; y = )` gives offset 12, the character column, not 13, the
byte column — unit test `test_column_counts_characters_not_utf8_bytes`). Warnings from
`ast.parse` (e.g. invalid escape sequences) are not failures; the runner must not be
started with `-W error`, which would turn them into SyntaxError.

## A-012 — Runner adapters for source-pair inputs and the M36 unit vector (DECIDED BY CLAUDE — owner review pending)

A-002's decision covers `response_object` only. Two more input shapes reach SOURCE_AST.

**`{driver_source, checker_source}` (M16, M29) — PROVISIONAL.** Implemented: run
**Decision (decided by Claude under standing delegation, owner review pending):** SOURCE_AST directly on the two strings (no envelope, schema or clause-ID step), then
continue with later stages. Alternative: wrap them in a full response object first —
the pack gives no wrapper, so this would need one.

**Decision on the source pair (decided by Claude under standing delegation, owner review pending):** as implemented. Reason: the pack defines no wrapper, and inventing one would add text the pack does not contain; the input holds exactly the two strings that Protocol step (2) begins with.

**`{source_file, syntax_error: {lineno, offset}}` with `fixture_class:
"parser_unit_vector"` (M36) — OPEN; M36 is NOT_IMPLEMENTED.**

What the pack says (exact text):
- `fixture_class` value `parser_unit_vector`: **not defined anywhere in the pack.** The
  string occurs only in `41_F18_Fixture_Inputs/M36.json`. The only text about
  `fixture_class` is Catalog (file 36) requirement 6: "Serializer unit vectors and
  lifecycle unit vectors are marked by `fixture_class` and are deliberately
  grammar-exempt; they test local utilities/policies, not model feedback." It names
  serializer and lifecycle unit vectors, not parser unit vectors.
- `CONTROL_EXPECTATION`, Catalog (file 36) dispositions list: "`CONTROL_EXPECTATION`: a
  serializer, lifecycle or policy test vector; it does not represent an artifact feedback
  event."
- `CONTROL_EXPECTATION`, Protocol (file 02 L177): "A `CONTROL_EXPECTATION` fixture
  exercises a serializer, protocol or lifecycle rule; its stage and expected diagnostic
  are test labels, not an artifact feedback event."
- The column rule itself (file 02 L127) is fully defined: "If `offset` is absent, null or
  less than 1, emit `column=1`".

Finding: neither definition names a parser vector, and no rule maps an input to the
`CONTROL_EXPECTATION` disposition. The earlier runner (commit e5eb9c0, run
run-20261123T155910Z) set `record["disposition"] = "CONTROL_EXPECTATION"` as a constant
whenever `fixture_class == "parser_unit_vector"`. That label occurs only in M36, so the
disposition was in effect copied from the descriptor, not computed. That PASS is
withdrawn: the runner now reports M36 NOT_IMPLEMENTED. The column rule is still covered
by unit tests (`ColumnRuleTests`, hand-built inputs, not F18 evidence).

Readings for the owners: (a) unit vectors of any class have disposition
`CONTROL_EXPECTATION` (would need a rule saying so, and a definition of
`parser_unit_vector`); (b) for unit vectors the runner compares stage, error class and
diagnostic only, and records the disposition label without comparing it (would change
Catalog requirement 2's "single exact expected disposition/stage/error/diagnostic");
**Decision (decided by Claude under standing delegation, owner review pending):** (c) the pack is corrected so M36's class and disposition are defined.

**Decision on M36 (decided by Claude under standing delegation, owner review pending):** an input of shape `{source_file, syntax_error: {lineno, offset}}` applies the column rule (`syntax_reject`) and has disposition `CONTROL_EXPECTATION`. Reason: such an input is a SyntaxError position, not a model response, so it is not an artifact feedback event; it exercises a protocol rule (Protocol §3.4 column rule) directly, and Protocol L177 defines `CONTROL_EXPECTATION` as a fixture that "exercises a serializer, protocol or lifecycle rule". This is a variant of (a) that rests on L177's "protocol" rather than on a definition of `parser_unit_vector`. The rule is keyed on the input shape, never on `fixture_class`: checked against the pack, `fixture_class` does not determine disposition (two `lifecycle_unit_vector` descriptors are not `CONTROL_EXPECTATION`, and `f18_packet_fixture` descriptors are `F18_REJECT`), so a rule keyed on the class label would contradict the pack. The adapter accepts only `driver.py`/`checker.py`, a positive integer `lineno` and an integer-or-null `offset`; anything else is NOT_IMPLEMENTED. **Effect:** M36 moves from NOT_IMPLEMENTED to PASS. This is the one decision in this batch that changes a fixture result, so it should be the first one the owners review. Reading (c) remains open to the owners as a pack correction.

## A-013 — Order of IMPORT_POLICY categories within one file (DECIDED — Ayush's confirmation pending; tie case DECIDED BY CLAUDE — owner review pending)

- File 30 §3 L27 (per-file stage list): "`ast.parse`; module-level AST policy;
  import/prohibited-name policy; compilation; …"
- File 30 §3 L27 (node order): "within a file, source nodes use ascending `(lineno,
  col_offset, end_lineno, end_col_offset)`."
- Protocol §3.4 evaluation order (3): "If the identifier scan passes, complete that
  file's import, prohibited-name and module-body checks before advancing to the next
  file. AST import nodes use ascending source-position order and the per-node import
  precedence above."
- Protocol §3.4 (file 02 L129): "Nodes are visited by `(lineno, col_offset, end_lineno,
  end_col_offset)` within `driver.py`, then `checker.py`."

The identifier scan runs first (settled by step (3)) and files run `driver.py` first
(settled). Not settled: which of the remaining categories wins inside one file.

Readings:
- (a) Module-body policy first, then import and prohibited-name checks — the order of
  File 30 L27's stage list.
- (b) Imports, then prohibited names, then module-body — the order of Protocol step (3)'s
  sentence.
- (c) One source-order pass: every IMPORT_POLICY violation in the file is placed by its
  node's `(lineno, col_offset, end_lineno, end_col_offset)` and the first wins, whatever
  its category — File 30 L27's node-order sentence.

What changes (driver.py examples):

| Source | (a) | (b) | (c) |
|---|---|---|---|
| `import os` (L1); `print(1)` (L2) | `MODULE_STATEMENT_REJECT\|…\|line=2\|reason=MODULE_EXECUTABLE` | `IMPORT_NOT_ALLOWED\|module=os` | `IMPORT_NOT_ALLOWED\|module=os` |
| `print(1)` (L1); `import os` (L2) | `MODULE_EXECUTABLE`, line 1 | `IMPORT_NOT_ALLOWED\|module=os` | `MODULE_EXECUTABLE`, line 1 |
| function using `eval` (L3); `X = [n for n in ()]` (L9) | `NON_LITERAL_CONSTANT`, line 9 | `PROHIBITED_BUILTIN\|name=eval` | `PROHIBITED_BUILTIN\|name=eval` |

Detail under (c): a module-level `eval("1")` is an `Expr` node and a `Name` node with
the same start `(1, 0)`; the `Name` ends first, so the key puts it first and gives
`PROHIBITED_BUILTIN`, not `MODULE_EXECUTABLE`. A module-level `x = eval("1")` starts with
the `Assign` at `(1, 0)` and gives `NON_LITERAL_CONSTANT`.

No current fixture distinguishes the readings: every IMPORT_POLICY fixture has one
violation.

**Decision:** reading (c) — one source-order pass; the first violation of any
IMPORT_POLICY category wins. Source: statement typed by Krishika in Claude Code on 23 Nov 2026: "I, Krishika, decide A-013 and A-014 as reading (c): single source-order pass, first violation wins. Ayush's confirmation is pending."
Reading (c) was suggested by Claude (claude.ai session) and relayed by Krishika.

Residual gap under (c), found when building step 7: two different findings can share
the smallest key. A bare module-level `eval` or `random.seed` statement is an `Expr`
node and a `Name`/`Attribute` node with identical spans (CPython 3.11.18:
`(1, 0, 1, 4)` for both), so "first violation wins" does not choose between
`MODULE_EXECUTABLE` and `PROHIBITED_BUILTIN`/`GLOBAL_RANDOM_USE`. Implemented: such a
**Decision (decided by Claude under standing delegation, owner review pending):** tie raised `UnsettledSpec("A-013")`. No current fixture has a tie.

**Decision on the tie (decided by Claude under standing delegation, owner review pending):** equal keys are ordered by File 30 §3 L27's stage list — "module-level AST policy; import/prohibited-name policy" — so a module-body finding wins, then an import finding, then a prohibited name, then `random` use (File 30 §2 L20 follows L19). A bare module-level `eval`, `random.seed` or `builtins.open` statement is therefore `MODULE_STATEMENT_REJECT|…|reason=MODULE_EXECUTABLE`. Reason: L27's list is the only text that ranks the categories, and the node-order sentence that reading (c) applies is exhausted by the tie. Pre-order traversal (the statement before its child) gives the same answer. Unit test `test_equal_key_tie_uses_file30_stage_order`.

## A-014 — Order between PROHIBITED_BUILTIN and GLOBAL_RANDOM_USE (DECIDED — Ayush's confirmation pending)

- File 30 §2 L19 (prohibited names) and L20 (`random`) are separate bullets; Protocol
  §3.4 (file 02 L133): "Reject AST `Name` nodes whose `id` is `__import__`, `eval`,
  `exec`, `compile` or `open`, and reject access through `builtins.<name>` for those
  same names. … direct `random.<attribute>` use other than `random.Random` emits
  `GLOBAL_RANDOM_USE`."
- Neither diagnostic carries a file or line (`PROHIBITED_BUILTIN|name=<NAME>`,
  `GLOBAL_RANDOM_USE|name=<NAME>`), so the order decides which name is reported.

Readings: (a) all prohibited-name violations before any random violation (the order in
which the text lists them); (b) one source-order pass over both kinds, separate from
imports and module-body; (c) the single source-order pass of A-013 (c). Example (one
function body): `v = random.random()` (L5); `exec("x")` (L6) — (a) gives
`PROHIBITED_BUILTIN|name=exec`; (b) and (c) give `GLOBAL_RANDOM_USE|name=random.random`.
No current fixture has both.

**Decision:** reading (c), the single source-order pass of A-013. Source: statement typed by Krishika in Claude Code on 23 Nov 2026: "I, Krishika, decide A-013 and A-014 as reading (c): single source-order pass, first violation wins. Ayush's confirmation is pending."

## A-015 — Module-body statements the text does not classify (DECIDED BY CLAUDE — owner review pending; case 2 REVISED BY OWNER — Ayush's confirmation pending)

Protocol §3.4 (file 02 L135): "At module scope, allow only permitted imports, one
optional docstring expression, … and assignments/annotated assignments whose values are
recursively literal-only. A non-literal assignment is `NON_LITERAL_CONSTANT`;
module-level control-flow statements (…) are `MODULE_CONTROL_FLOW`; other executable
statements/calls/expressions are `MODULE_EXECUTABLE`." File 30 §3 L29: "Literal-only
expressions are `ast.Constant` values of type string, bytes, integer, float, complex,
boolean or `None`, and recursively nested tuple/list/set/dict literals containing only
those values; unary plus/minus applied to a numeric literal is permitted."

Unsettled cases (each needs: accept, `NON_LITERAL_CONSTANT` or `MODULE_EXECUTABLE`):
1. `x += 1` — `ast.AugAssign` is not "assignment/annotated assignment" by name.
2. `a.b = 1`, `a[0] = 1` — literal value, but the target is not a plain name.
3. `x: int` — `ast.AnnAssign` with no value: nothing to test for literal-only.
4. `pass` — not executable in effect, but not in the allowed list.
5. A string expression that is not the first statement, or a second one — is "one
   optional docstring expression" only the first statement?
6. `X = ...` — `Ellipsis` is an `ast.Constant` but not one of the listed types.
7. `X = -True` — `bool` is an `int` subclass: is it a "numeric literal"?
8. `X = -(-1)`, `X = +-1` — unary applied to a unary, not directly to a literal.
9. The annotation of an annotated assignment (`X: foo() = 1`): the text tests "values"
   only. Implemented boundary: an annotation made only of names, attributes,
   subscripts, constants, tuples/lists and `|` (e.g. `int`, `dict[str, int] | None`)
   is not examined; any other annotation node (a call, arithmetic, …) is case 9.
10. `global x` / `nonlocal x` at module scope (both pass `ast.parse` on 3.11.18) — no
    effect, like `pass`.
11. `return`, `break`, `continue` at module scope (all pass `ast.parse` on 3.11.18;
    `compile()` would reject them) — control transfer, but not in the
    `MODULE_CONTROL_FLOW` list (`if`, `for`, `while`, `with`, `try`, `match`, `async`).

Before the decision (step 6, `classify_module_body`), each of these cases was returned as an
`UnsettledSpec("A-015")` finding at its source position, not raised at once, so a
settled violation earlier in the file can still win once A-013 is decided. A value with
a non-literal part is `NON_LITERAL_CONSTANT` even if it also has an unsettled part
(e.g. `(..., f())`), because every reading rejects it with that reason.

Treated as settled by the text (no entry needed unless the owners disagree): `del`,
`assert`, `raise` → `MODULE_EXECUTABLE` ("other executable statements"); any
expression statement that is not the first-statement string docstring, including
`await`, `yield`, a bytes or f-string first statement → `MODULE_EXECUTABLE` (File 30
§3 L29: "expressions other than a docstring … are rejected"); `async for`, `async with`
→ `MODULE_CONTROL_FLOW` ("`async` control flow"); `try`/`except*` (`ast.TryStar`) →
`MODULE_CONTROL_FLOW` (`try`); tuple/list/starred unpacking targets made only of names
count as assignments.

**Decision (decided by Claude under standing delegation, owner review pending):** No current fixture uses any unsettled case (P28, M04a, M04b and M57 do not).

**Decision (decided by Claude under standing delegation, owner review pending):** Reasons, from L135/L29: the allowed list ("allow only …") is exhaustive; `MODULE_CONTROL_FLOW` covers only the statements it names; "assignments/annotated assignments" are read as `ast.Assign`/`ast.AnnAssign` (the section names AST node types throughout); the literal test is on "values"; and "calls" are named as `MODULE_EXECUTABLE`.

| Case | Outcome |
|---|---|
| 1 `x += 1` | `MODULE_EXECUTABLE` (an augmented assignment is its own statement kind, not in the list) |
| 2 `a.b = 1`, `a[0] = 1` | **revised by owner, see below:** `MODULE_EXECUTABLE` whatever the value. (First decision, superseded: accepted if the value is literal-only.) |
| 3 `x: int` | accepted (no value to fail) |
| 4 `pass` | `MODULE_EXECUTABLE` |
| 5 later string expression | `MODULE_EXECUTABLE` (a docstring is the first statement) |
| 6 `X = ...` | `NON_LITERAL_CONSTANT` (Ellipsis is not in L29's exhaustive type list) |
| 7 `X = -True` | `NON_LITERAL_CONSTANT` (L29 lists boolean separately from the numeric types) |
| 8 `X = -(-1)`, `+-1` | `NON_LITERAL_CONSTANT` (unary applied to a unary, not to a numeric literal) |
| 9 annotation | not tested for literalness; `MODULE_EXECUTABLE` if it contains a call (e.g. `X: foo() = 1`) |
| 10 `global`/`nonlocal` | `MODULE_EXECUTABLE` |
| 11 `return`/`break`/`continue` | `MODULE_EXECUTABLE` (not in the `MODULE_CONTROL_FLOW` list) |
| any other statement type | `MODULE_EXECUTABLE` (none remain on 3.11) |

Competing reading not taken for case 9: reject every non-type annotation as `MODULE_EXECUTABLE`, since it evaluates code at import time. The text tests values only, so only the explicitly named "calls" are rejected. Unit tests `test_a015_decided_cases`, `test_a015_cases_take_part_in_source_order`.

**Case 2 revised — owner decision by Krishika, 23 Nov 2026 (Ayush's confirmation pending).** Claude's first decision (accept an attribute/subscript target when the value is literal-only, rejecting only a call in the target) is **superseded**. Krishika's instruction: "an assignment whose target is not a plain Name (e.g. a.b = 1, math.pi = 3, d[0] = 1) is not a module constant and is a side effect. Reject as MODULE_STATEMENT_REJECT reason MODULE_EXECUTABLE."

Why the first decision was wrong: it read only L135/L29's literal test, which is on values, and missed the wording on what module-level assignments are *for*. Texts cited (verified in the baseline):
- File 30 L52 (driver) and L64 (checker): the file may contain "literal-only module constants"; "Module-level executable statements, control flow, calls, comprehensions, non-literal assignments and side effects are prohibited." The same wording is in the model-visible prompt template, file 19 L25 and L40.
- File 30 L29: "Names, calls, comprehensions, f-strings, attribute access, binary operations and other expressions are not literal-only. Module-level executable statements, … non-literal assignments and other side effects are rejected."

Assigning to an attribute or subscript changes another object instead of defining a constant, so it is a side effect.

Implemented rule: an `ast.Assign` or `ast.AnnAssign` is `MODULE_STATEMENT_REJECT|file=<FILE>|line=<LINE>|reason=MODULE_EXECUTABLE` if any target is not a plain name. Plain names include names unpacked in tuples/lists and starred names, so `a, *b = 1, 2` is still allowed. The rule therefore covers `a, b.c = 1, 2`, `[a, *b[0]] = …`, `X = a.b = 1` and `d[0]: int` (no value).

Detail decided by Claude under the delegation: the target check comes before the value check, so `a.b = f()` is `MODULE_EXECUTABLE`, not `NON_LITERAL_CONSTANT`. Reason: under the owner's rule such a statement is not a module constant at all, so the constant-specific reason does not apply.

Unit tests `test_a015_decided_cases`, `test_attribute_target_is_executable_in_stage`. No current fixture has an attribute or subscript target, so no fixture result changes.

## A-016 — Prohibited-name rule: definitions, parameters and `builtins` (DECIDED BY CLAUDE — owner review pending)

File 30 §2 L19: "AST `Name` nodes whose `id` is `__import__`, `eval`, `exec`, `compile`
or `open` are rejected, regardless of call context. A `builtins` attribute whose
attribute is one of those names is also rejected. `builtins` itself is not an allowed
import root."

Unsettled: (1) `def open(): …` or `def f(eval): …` binds the name through `ast.FunctionDef.name`
or `ast.arg`, not an `ast.Name` node — rejected or not? Function definitions are
otherwise deferred to AST_SIGNATURE. (2) `import builtins` followed by `builtins.open`:
`IMPORT_NOT_ALLOWED|module=builtins` or `PROHIBITED_BUILTIN|name=open` (same as A-013).
(3) "A `builtins` attribute" — is it only `Attribute(value=Name("builtins"))`, or also
e.g. `__builtins__.open`? M24 (`builtins.open` with no import) expects
`PROHIBITED_BUILTIN|name=open`, consistent with the first form. **Decision (decided by Claude under standing delegation, owner review pending):** the planned implementation: `ast.Name` nodes in any context, and `Attribute(value=Name(id="builtins"))` only; (1) and `__builtins__` are not flagged; (2) is settled by A-013 reading (c) (the import comes first in source order, so `IMPORT_NOT_ALLOWED|module=builtins`). Reasons: the text says "AST `Name` nodes" and "`builtins.<name>`"; File 30 §3 says IMPORT_POLICY "never rejects or classifies a function/class definition", which excludes flagging `def open`; parameter names are `ast.arg`, not `ast.Name`.

## A-017 — `random.<attribute>` when `random` is not the imported module (DECIDED BY CLAUDE — owner review pending)

File 30 §2 L20: "Any direct attribute access on the module name `random` other than
`random.Random` is rejected". Protocol §3.4 (file 02 L133): "direct `random.<attribute>`
use other than `random.Random` emits `GLOBAL_RANDOM_USE`."

Unsettled: whether the check is purely syntactic (`Attribute(value=Name(id="random"))`
anywhere) or applies only when `random` is the imported module — e.g. a parameter named
`random`, or a file without `import random`. **Decision (decided by Claude under standing delegation, owner review pending):** M09, M22, M23 all `import random` and use
it inside a method, so both readings pass them. Syntactic, as planned. Reason: the text says "the module name `random`" and "direct `random.<attribute>`", and calls the check static, saying outright that aliasing and `getattr` are not detected; binding analysis would go beyond what it describes.

## A-018 — Non-ASCII identifiers inside f-string replacement fields (DECIDED BY CLAUDE — owner review pending)

File 30 §2 L21: "Every Python identifier lexeme must be ASCII. … Unicode in STRING and
COMMENT tokens is permitted." Protocol §3.4 (file 02 L133): "STRING and COMMENT tokens
are not scanned".

Question: in `f"{café}"` the identifier `café` is a real `ast.Name` node, but before
Python 3.12 (PEP 701) the whole f-string is one STRING token.

Probe result (CPython 3.11.18, pinned interpreter, step 1): `ast.parse('x = f"{café}"')`
contains `Name(id="café")`, and `tokenize` emits `NAME 'x'` then `STRING 'f"{café}"'`;
the same holds for `f"{a℘}"`. So, as the rule is written, a non-ASCII identifier inside
an f-string replacement field is **not rejected**. **This is CPython 3.11-specific:**
from 3.12, f-strings are tokenized into parts (PEP 701) and the identifier would be a
`NAME` token. Unit test `test_fstring_identifier_not_scanned_on_311` records the
behaviour.

Readings: (a) literal text — the scan covers tokens only, so f-string identifiers pass;
(b) "Every Python identifier lexeme must be ASCII" governs, so the scan must also check
`ast.Name`/`ast.Attribute` nodes inside `ast.JoinedStr` (the text gives no column rule
for that). **Decision (decided by Claude under standing delegation, owner review pending):** No current fixture uses an f-string with a non-ASCII identifier.
Reading (a), as implemented. Reason: the operative rule is a token procedure pinned to CPython 3.11 ("scan `tokenize.NAME` and identifier-relevant `tokenize.ERRORTOKEN` tokens", "STRING and COMMENT tokens are not scanned"), and (b) would need a column rule the text does not give. The 3.11-specific gap should be disclosed alongside the alias limitation in File 30 §2 L20.

## A-019 — Line breaks for the identifier scan: lone CR (DECIDED BY CLAUDE — owner review pending)

File 30 §2 L21 / Protocol §3.4 (file 02 L133): the column is computed "from the UTF-8
byte length of the source-line prefix"; the pack does not define a source line. Probe
on CPython 3.11.18: for `"x = 1\ry = 2\n"`, `ast.parse` puts `y = 2` on line 2, but
`tokenize.generate_tokens` over the same string treats the lone CR as an `ERRORTOKEN`
and reports `y` on line 1. A non-ASCII identifier after a lone CR would therefore get a
line number that disagrees with the AST. CRLF is consistent in both. **Decision (decided by Claude under standing delegation, owner review pending):** Formerly a lone CR raised `UnsettledSpec("A-019")`. No current fixture contains a lone CR.

**Decision (decided by Claude under standing delegation, owner review pending):** a source line is a Python physical line, ended by LF, CRLF or a lone CR (Language Reference 2.1.2), which is how `ast.parse` counts lines on 3.11.18. The scanner tokenizes a copy in which each lone CR is replaced by LF; one character replaces one at a line end, so every line prefix and every UTF-8 byte column is unchanged. The source itself is not changed. Reason: the diagnostic's `line` must agree with the AST the rest of the stage uses, and CPython's own compiler translates a lone CR to a newline (so a raw CR inside a quoted string is already a syntax error at SOURCE_AST). Unit test `test_lone_cr_ends_a_line_as_for_ast_parse`.

## A-020 — What PARAMETER_NAMES, PARAMETER_KIND and DEFAULT_OR_VARIADIC each cover (DECIDED BY CLAUDE — owner review pending)

Protocol §3.4 (file 02 L164): "exactly one binding of the required kind proceeds to
parameter checks in the order `PARAMETER_NAMES`, `PARAMETER_KIND`, then
`DEFAULT_OR_VARIADIC`." File 30 §3 L33: "parameter checks in the order names, kinds,
then defaults/variadic/keyword-only shape." File 30 §3 L35/L37 give the required lists:
`create_driver(seed)`, `Driver.step(self, cycle_index, outputs_after_edge)`,
`check_trace(trace, metadata)`, each "required positional-or-keyword … not
positional-only … no default, variadic, keyword-only or extra parameters".

The text does not say which parameters the names check compares. Readings: (a) the
positional parameters only (positional-only then positional-or-keyword); (b) every
named parameter, including keyword-only and variadic names. Example: `def
create_driver(seed, *args)` is `DEFAULT_OR_VARIADIC` under (a) but `PARAMETER_NAMES`
under (b); `def create_driver(*, seed)` is `PARAMETER_NAMES` under (a) but
`PARAMETER_KIND` under (b).

**Decision (decided by Claude under standing delegation, owner review pending):** (a).
- The names check compares the positional parameter names, in order, with the required
  list.
- The kind check rejects any positional-only parameter.
- `DEFAULT_OR_VARIADIC` rejects any default, `*args`, keyword-only parameter or
  `**kwargs`.
- Annotations are ignored.

Reason: File 30 groups "keyword-only" with defaults and variadics in the *third*
check. Under (b), a keyword-only or variadic parameter would already fail the names
check, which would leave the third check almost unreachable. "Extra" positional
parameters are a names mismatch under both readings. Unit tests `ParameterTests`.

## A-021 — What counts as a "binding" in the required-symbol pass (DECIDED BY CLAUDE — owner review pending)

Protocol §3.4 (file 02 L164): "count all same-name binding definitions at the required
scope … more than one binding of any AST kind emits `EXTRA_ENTRY_POINT`; exactly one
binding with the wrong AST kind emits `WRONG_ENTRY_POINT_KIND`". The text does not list
which AST kinds bind.

**Decision (decided by Claude under standing delegation, owner review pending):** a
binding is a statement in the scope's own body (module body, or `Driver`'s class body
for `step`) that is:
- a `def`, `async def` or `class` with that name;
- an assignment, or an annotated assignment *with a value*, whose target binds that
  name (unpacking included);
- an import whose bound name is that name.

An annotated name without a value (`create_driver: int`) is not counted, because Python
creates no binding for it. Definitions nested inside functions are not at the required
scope.

Reason: "binding" is Python's own term (Language Reference 4.2.1), and these are the
statements that bind a name in a module or class scope after IMPORT_POLICY. Other
binding forms (`for`, `with`, `global` from a function) cannot appear at module scope
by then. Unit tests `test_any_binding_kind_counts_as_extra`,
`test_annotation_without_value_is_not_a_binding`.

## A-022 — `Driver` class-body statements other than methods and nested classes (DECIDED BY CLAUDE — owner review pending)

File 30 §3 L35: "Its body may contain one docstring, literal-only class constants and
exactly one synchronous undecorated instance method named `step`". IMPORT_POLICY checks
module-body statements only. The seven AST_SIGNATURE category ranks cover methods
(rank 3), nested classes (rank 1), bases and metaclass (rank 4), decorators, async
definitions and comprehensions. None of them names a class-body statement such as
`X = f()`, `pass` or `if …:` inside `Driver`.

Readings: (a) not checked statically; later stages (restricted import) see its effects;
(b) `DRIVER_CLASS_FORM`, the only reason about the `Driver` class's form, at rank 4;
(c) a new reason — excluded, because "No unlisted value is permitted" (file 02 L125).

**Decision (decided by Claude under standing delegation, owner review pending):** (b).
Any `Driver` class-body statement other than these is `DRIVER_CLASS_FORM` at rank 4,
`symbol=Driver`, positioned at the statement:
- a method or nested class (handled by the other ranks);
- a first-statement string docstring;
- an assignment or annotated assignment with a plain-name target and a literal-only value
  (or no value).

Class constants use the module-constant rules, including the owner's A-015 case 2 rule
(plain-name targets only). Reason: the stage map assigns "class/method/nesting violation" to
AST_SIGNATURE, and B5 (file 19 L25, file 30 L52) states the class-body allowance to
the model, so (a) would leave a stated rule unenforced. Unit test
`test_driver_body_statements`. No current fixture has such a statement.

## A-023 — Source position of definition violations in the global pass (DECIDED BY CLAUDE — owner review pending)

The global sort key is `(category, file_order, lineno, col_offset, end_lineno,
end_col_offset)`. The text gives the node only for rank 7 ("the expression node's own
source position").

**Decision (decided by Claude under standing delegation, owner review pending):**
- Ranks 1–3, 5 and 6 use the offending `ClassDef`/`FunctionDef`/`AsyncFunctionDef`
  node's own position (on CPython 3.11 a decorated definition starts at its `def` or
  `class` line, not at the decorator).
- Rank 4 uses the `Driver` `ClassDef`, or the class-body statement for A-022.

Reason: the violation is a property of the definition node, which is how the text
names it ("any nested class", "any decorator on any function, class or method").
Only ties between two violations of the same category in the same file depend on this.

## A-024 — Compile errors without a line number (DECIDED BY CLAUDE — owner review pending)

Stage map: `COMPILE_ERROR|file=<FILE>|line=<LINE>`, and `LINE` must be positive. The
pack does not say what to do if `compile()` raises a SyntaxError with no line, or
another exception.

**Decision (decided by Claude under standing delegation, owner review pending):** use
line 1, as A-011 does for SOURCE_AST; any other exception from `compile()` is a compile
error at line 1. Reason: same as A-011. Sources reaching compilation have already parsed,
so this is a defensive rule; no known 3.11.18 input reaches it.
