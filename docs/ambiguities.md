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

**Update, 24 Nov 2026:** A-038 and A-040–A-044 were approved in the owner freeze, and
D-009 (end of this file) approves every other Claude-decided reading, as decided, without
itemised owner review; those items now read "approved under D-009". A-038 and A-040–A-044
keep the wording "owner review pending": the signed freeze covers their exact bytes, so
they are not edited. They are approved.

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

## A-007 — SOURCE_AST order across files: per file, or by stage-map row (DECIDED BY CLAUDE — approved under D-009)

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

**Decision (decided by Claude under standing delegation, approved under D-009):** reading (a), as implemented (unit test `test_driver_checked_before_checker`). Reason: File 30 §3 L27 is the only text that orders checks *within* a file, and it says to "process each source file in this order", i.e. complete one file before the next; Protocol step (2) also names the file order. The stage-map sentence chooses among rows *after* the evaluation order, so it does not reorder the per-file sequence.

## A-008 — U+FEFF at the start of a source string (DECIDED BY CLAUDE — approved under D-009)

Stage map: "Invalid UTF-8/BOM or syntax parse error" → `SOURCE_SYNTAX_REJECT`; File 30 §3
L27: "strict UTF-8 decode with BOM rejection". The source arrives as a JSON string, not
bytes, so "BOM" has no byte meaning here.

Readings: (a) a leading U+FEFF is the BOM and is rejected before the empty check — but
the pack gives no line/column for a BOM rejection; (b) U+FEFF is an ordinary character
and `ast.parse` decides (on 3.11.18 it raises SyntaxError "invalid non-printable
character U+FEFF", line 1, offset 1, so `…|line=1|column=1`); (c) strip it as Python
does when reading a UTF-8-SIG file — excluded by "BOM rejection". (a) and (b) both
reject; they can differ only in the line/column, which the pack does not give for (a).
**Decision (decided by Claude under standing delegation, approved under D-009):** a leading U+FEFF is rejected as the BOM, before the empty check: `SOURCE_SYNTAX_REJECT|file=<FILE>|line=1|column=1`. Reason: File 30 §3 L27 requires "BOM rejection" as part of the first step, and File 30 §1 forbids silently normalizing source code, which excludes (c). Readings (a) and (b) both reject; the only open point was the position, and a BOM is at line 1, column 1 by any count, which is also what `ast.parse` reports under (b). U+FEFF later in the source is still left to `ast.parse`. Unit test `test_claude_decided_cases`.

## A-009 — Source string that is not valid UTF-8 (DECIDED BY CLAUDE — approved under D-009)

JSON `\ud800` escapes decode to lone surrogates, which cannot be encoded as UTF-8.
`ast.parse` on 3.11.18 raises `UnicodeEncodeError`, not SyntaxError. The stage map
puts this under "Invalid UTF-8 …" → `SOURCE_SYNTAX_REJECT|file=<FILE>|line=<LINE>|
column=<COLUMN>` but says nothing about the line or column. (Raw input of this kind
also passes PARSE_SCHEMA: Python's `json` accepts lone-surrogate escapes.)
**Decision (decided by Claude under standing delegation, approved under D-009):** `SOURCE_SYNTAX_REJECT|file=<FILE>|line=1|column=1`. Reason: the stage map assigns invalid UTF-8 to `SOURCE_SYNTAX_REJECT` at SOURCE_AST, so it is not moved to PARSE_SCHEMA (the response bytes themselves are valid UTF-8; File 30 §1's "Reject invalid UTF-8" applies to them). CPython reports no position for this failure, and the only position rule the pack gives for a missing position is the column rule's "absent … emit `column=1`"; line 1 is the same fallback (A-011). Competing reading not taken: report the line/column of the first lone surrogate — more informative, but no text defines it, and it is not "reported by CPython".

## A-010 — Which characters count as whitespace for SOURCE_EMPTY (DECIDED BY CLAUDE — approved under D-009)

Stage map: "Empty/whitespace-only source". The pack does not define whitespace.
Readings: (a) JSON whitespace (space, tab, LF, CR); (b) `str.isspace()`, which adds
U+000B, U+000C, U+001C–U+001F, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
U+202F, U+205F, U+3000; (c) Python tokenizer whitespace (space, tab, form feed, newlines).
What changes: a source of only U+000C parses on 3.11.18 (empty module, so it passes
SOURCE_AST under (a)), but is SOURCE_EMPTY under (b) and (c); U+000B or U+00A0 alone is
`SOURCE_SYNTAX_REJECT|…|line=1|column=1` under (a)/(c) but SOURCE_EMPTY under (b).

**Decision (decided by Claude under standing delegation, approved under D-009):** reading (c), Python source whitespace: space, tab, form feed, CR and LF (Python Language Reference 2.1.2 line terminators and 2.1.9 whitespace between tokens). A source made only of these is SOURCE_EMPTY; any other character, including U+000B, U+00A0 and U+3000, goes to `ast.parse` (on 3.11.18 those give `SOURCE_SYNTAX_REJECT`). Reason: the check is on Python source, inside a stage whose authority on source is CPython 3.11; JSON whitespace (a) belongs to the response envelope, and `str.isspace()` (b) would call "empty" sources that Python itself rejects as invalid characters. A comment-only source is still not empty. Unit test `test_claude_decided_cases`.

## A-011 — SyntaxError with no usable line, or another exception from ast.parse (DECIDED BY CLAUDE — approved under D-009)

The column rule covers a missing offset ("If `offset` is absent, null or less than 1,
emit `column=1`") but nothing covers a missing or non-positive `lineno`, although
`LINE` must be a positive decimal integer. On 3.11.18, a NUL character in the source
gives SyntaxError "source code string cannot contain null bytes" with `lineno=None`.
`ast.parse` may also raise exceptions that are not SyntaxError (e.g. `RecursionError`,
`MemoryError`, `UnicodeEncodeError` — see A-009); the stage map does not say whether
these are "syntax parse error". **Decision (decided by Claude under standing delegation, approved under D-009):** a SyntaxError whose `lineno` is missing or less than 1 uses `line=1`, and its column follows the column rule as usual; any other exception from `ast.parse` (e.g. `MemoryError`, which 3.11.18 raises for very deep nesting such as 200,000 unary minus signs) is a syntax parse error with `line=1|column=1`. Reason: `LINE` must be a positive integer and the pack's only rule for a missing position is "If `offset` is absent, null or less than 1, emit `column=1`"; line 1 applies the same fallback. "Syntax parse error" in the stage map is read as "`ast.parse` did not produce a tree". Competing reading not taken for NUL bytes: report the line of the first NUL — not given by CPython or the text. Unit tests `test_claude_decided_cases`, `test_non_syntax_error_from_parse_is_line_1_column_1`.

Related observation (no change): the column rule says to emit "the positive one-based
source-character column reported by CPython". On 3.11.18 `ast.parse` of a `str` reports
a character offset (`é = 1; y = )` gives offset 12, the character column, not 13, the
byte column — unit test `test_column_counts_characters_not_utf8_bytes`). Warnings from
`ast.parse` (e.g. invalid escape sequences) are not failures; the runner must not be
started with `-W error`, which would turn them into SyntaxError.

## A-012 — Runner adapters for source-pair inputs and the M36 unit vector (DECIDED BY CLAUDE — approved under D-009)

A-002's decision covers `response_object` only. Two more input shapes reach SOURCE_AST.

**`{driver_source, checker_source}` (M16, M29) — PROVISIONAL.** Implemented: run
**Decision (decided by Claude under standing delegation, approved under D-009):** SOURCE_AST directly on the two strings (no envelope, schema or clause-ID step), then
continue with later stages. Alternative: wrap them in a full response object first —
the pack gives no wrapper, so this would need one.

**Decision on the source pair (decided by Claude under standing delegation, approved under D-009):** as implemented. Reason: the pack defines no wrapper, and inventing one would add text the pack does not contain; the input holds exactly the two strings that Protocol step (2) begins with.

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
**Decision (decided by Claude under standing delegation, approved under D-009):** (c) the pack is corrected so M36's class and disposition are defined.

**Decision on M36 (decided by Claude under standing delegation, approved under D-009):** an input of shape `{source_file, syntax_error: {lineno, offset}}` applies the column rule (`syntax_reject`) and has disposition `CONTROL_EXPECTATION`. Reason: such an input is a SyntaxError position, not a model response, so it is not an artifact feedback event; it exercises a protocol rule (Protocol §3.4 column rule) directly, and Protocol L177 defines `CONTROL_EXPECTATION` as a fixture that "exercises a serializer, protocol or lifecycle rule". This is a variant of (a) that rests on L177's "protocol" rather than on a definition of `parser_unit_vector`. The rule is keyed on the input shape, never on `fixture_class`: checked against the pack, `fixture_class` does not determine disposition (two `lifecycle_unit_vector` descriptors are not `CONTROL_EXPECTATION`, and `f18_packet_fixture` descriptors are `F18_REJECT`), so a rule keyed on the class label would contradict the pack. The adapter accepts only `driver.py`/`checker.py`, a positive integer `lineno` and an integer-or-null `offset`; anything else is NOT_IMPLEMENTED. **Effect:** M36 moves from NOT_IMPLEMENTED to PASS. This is the one decision in this batch that changes a fixture result, so it should be the first one the owners review. Reading (c) remains open to the owners as a pack correction.

## A-013 — Order of IMPORT_POLICY categories within one file (DECIDED — Ayush's confirmation pending; tie case DECIDED BY CLAUDE — approved under D-009)

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
**Decision (decided by Claude under standing delegation, approved under D-009):** tie raised `UnsettledSpec("A-013")`. No current fixture has a tie.

**Decision on the tie (decided by Claude under standing delegation, approved under D-009):** equal keys are ordered by File 30 §3 L27's stage list — "module-level AST policy; import/prohibited-name policy" — so a module-body finding wins, then an import finding, then a prohibited name, then `random` use (File 30 §2 L20 follows L19). A bare module-level `eval`, `random.seed` or `builtins.open` statement is therefore `MODULE_STATEMENT_REJECT|…|reason=MODULE_EXECUTABLE`. Reason: L27's list is the only text that ranks the categories, and the node-order sentence that reading (c) applies is exhausted by the tie. Pre-order traversal (the statement before its child) gives the same answer. Unit test `test_equal_key_tie_uses_file30_stage_order`.

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

## A-015 — Module-body statements the text does not classify (DECIDED BY CLAUDE — approved under D-009; case 2 REVISED BY OWNER — Ayush's confirmation pending)

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

**Decision (decided by Claude under standing delegation, approved under D-009):** No current fixture uses any unsettled case (P28, M04a, M04b and M57 do not).

**Decision (decided by Claude under standing delegation, approved under D-009):** Reasons, from L135/L29: the allowed list ("allow only …") is exhaustive; `MODULE_CONTROL_FLOW` covers only the statements it names; "assignments/annotated assignments" are read as `ast.Assign`/`ast.AnnAssign` (the section names AST node types throughout); the literal test is on "values"; and "calls" are named as `MODULE_EXECUTABLE`.

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

## A-016 — Prohibited-name rule: definitions, parameters and `builtins` (DECIDED BY CLAUDE — approved under D-009)

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
`PROHIBITED_BUILTIN|name=open`, consistent with the first form. **Decision (decided by Claude under standing delegation, approved under D-009):** the planned implementation: `ast.Name` nodes in any context, and `Attribute(value=Name(id="builtins"))` only; (1) and `__builtins__` are not flagged; (2) is settled by A-013 reading (c) (the import comes first in source order, so `IMPORT_NOT_ALLOWED|module=builtins`). Reasons: the text says "AST `Name` nodes" and "`builtins.<name>`"; File 30 §3 says IMPORT_POLICY "never rejects or classifies a function/class definition", which excludes flagging `def open`; parameter names are `ast.arg`, not `ast.Name`.

## A-017 — `random.<attribute>` when `random` is not the imported module (DECIDED BY CLAUDE — approved under D-009)

File 30 §2 L20: "Any direct attribute access on the module name `random` other than
`random.Random` is rejected". Protocol §3.4 (file 02 L133): "direct `random.<attribute>`
use other than `random.Random` emits `GLOBAL_RANDOM_USE`."

Unsettled: whether the check is purely syntactic (`Attribute(value=Name(id="random"))`
anywhere) or applies only when `random` is the imported module — e.g. a parameter named
`random`, or a file without `import random`. **Decision (decided by Claude under standing delegation, approved under D-009):** M09, M22, M23 all `import random` and use
it inside a method, so both readings pass them. Syntactic, as planned. Reason: the text says "the module name `random`" and "direct `random.<attribute>`", and calls the check static, saying outright that aliasing and `getattr` are not detected; binding analysis would go beyond what it describes.

## A-018 — Non-ASCII identifiers inside f-string replacement fields (DECIDED BY CLAUDE — approved under D-009)

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
for that). **Decision (decided by Claude under standing delegation, approved under D-009):** No current fixture uses an f-string with a non-ASCII identifier.
Reading (a), as implemented. Reason: the operative rule is a token procedure pinned to CPython 3.11 ("scan `tokenize.NAME` and identifier-relevant `tokenize.ERRORTOKEN` tokens", "STRING and COMMENT tokens are not scanned"), and (b) would need a column rule the text does not give. The 3.11-specific gap should be disclosed alongside the alias limitation in File 30 §2 L20.

## A-019 — Line breaks for the identifier scan: lone CR (DECIDED BY CLAUDE — approved under D-009)

File 30 §2 L21 / Protocol §3.4 (file 02 L133): the column is computed "from the UTF-8
byte length of the source-line prefix"; the pack does not define a source line. Probe
on CPython 3.11.18: for `"x = 1\ry = 2\n"`, `ast.parse` puts `y = 2` on line 2, but
`tokenize.generate_tokens` over the same string treats the lone CR as an `ERRORTOKEN`
and reports `y` on line 1. A non-ASCII identifier after a lone CR would therefore get a
line number that disagrees with the AST. CRLF is consistent in both. **Decision (decided by Claude under standing delegation, approved under D-009):** Formerly a lone CR raised `UnsettledSpec("A-019")`. No current fixture contains a lone CR.

**Decision (decided by Claude under standing delegation, approved under D-009):** a source line is a Python physical line, ended by LF, CRLF or a lone CR (Language Reference 2.1.2), which is how `ast.parse` counts lines on 3.11.18. The scanner tokenizes a copy in which each lone CR is replaced by LF; one character replaces one at a line end, so every line prefix and every UTF-8 byte column is unchanged. The source itself is not changed. Reason: the diagnostic's `line` must agree with the AST the rest of the stage uses, and CPython's own compiler translates a lone CR to a newline (so a raw CR inside a quoted string is already a syntax error at SOURCE_AST). Unit test `test_lone_cr_ends_a_line_as_for_ast_parse`.

## A-020 — What PARAMETER_NAMES, PARAMETER_KIND and DEFAULT_OR_VARIADIC each cover (DECIDED BY CLAUDE — approved under D-009)

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

**Decision (decided by Claude under standing delegation, approved under D-009):** (a).
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

## A-021 — What counts as a "binding" in the required-symbol pass (DECIDED BY CLAUDE — approved under D-009)

Protocol §3.4 (file 02 L164): "count all same-name binding definitions at the required
scope … more than one binding of any AST kind emits `EXTRA_ENTRY_POINT`; exactly one
binding with the wrong AST kind emits `WRONG_ENTRY_POINT_KIND`". The text does not list
which AST kinds bind.

**Decision (decided by Claude under standing delegation, approved under D-009):** a
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

## A-022 — `Driver` class-body statements other than methods and nested classes (DECIDED BY CLAUDE — approved under D-009)

File 30 §3 L35: "Its body may contain one docstring, literal-only class constants and
exactly one synchronous undecorated instance method named `step`". IMPORT_POLICY checks
module-body statements only. The seven AST_SIGNATURE category ranks cover methods
(rank 3), nested classes (rank 1), bases and metaclass (rank 4), decorators, async
definitions and comprehensions. None of them names a class-body statement such as
`X = f()`, `pass` or `if …:` inside `Driver`.

Readings: (a) not checked statically; later stages (restricted import) see its effects;
(b) `DRIVER_CLASS_FORM`, the only reason about the `Driver` class's form, at rank 4;
(c) a new reason — excluded, because "No unlisted value is permitted" (file 02 L125).

**Decision (decided by Claude under standing delegation, approved under D-009):** (b).
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

## A-023 — Source position of definition violations in the global pass (DECIDED BY CLAUDE — approved under D-009)

The global sort key is `(category, file_order, lineno, col_offset, end_lineno,
end_col_offset)`. The text gives the node only for rank 7 ("the expression node's own
source position").

**Decision (decided by Claude under standing delegation, approved under D-009):**
- Ranks 1–3, 5 and 6 use the offending `ClassDef`/`FunctionDef`/`AsyncFunctionDef`
  node's own position (on CPython 3.11 a decorated definition starts at its `def` or
  `class` line, not at the decorator).
- Rank 4 uses the `Driver` `ClassDef`, or the class-body statement for A-022.

Reason: the violation is a property of the definition node, which is how the text
names it ("any nested class", "any decorator on any function, class or method").
Only ties between two violations of the same category in the same file depend on this.

## A-024 — Compile errors without a line number (DECIDED BY CLAUDE — approved under D-009)

Stage map: `COMPILE_ERROR|file=<FILE>|line=<LINE>`, and `LINE` must be positive. The
pack does not say what to do if `compile()` raises a SyntaxError with no line, or
another exception.

**Decision (decided by Claude under standing delegation, approved under D-009):** use
line 1, as A-011 does for SOURCE_AST; any other exception from `compile()` is a compile
error at line 1. Reason: same as A-011. Sources reaching compilation have already parsed,
so this is a defensive rule; no known 3.11.18 input reaches it.

## A-025 — The `events` input vocabulary and multi-failure precedence (DECIDED BY CLAUDE — approved under D-009)

R01–R06, R12 and R13 give a list of observed `events` (`{"kind": …, …}`). The pack
defines neither the event vocabulary nor how several events are ranked, beyond the
evaluation order (Protocol §3.4 L166) and "The first applicable row after the exact
evaluation order below controls" (L139).

**Decision (decided by Claude under standing delegation, approved under D-009):**
- Each event kind names one stage-map row, and its fields fill that row's diagnostic
  template. The table is `EVENT_ROWS` in `src/openvef/stage_map.py`: `schema_reject`,
  `output_truncated`, `import_not_allowed`, `compile_error`, `driver_runtime`,
  `driver_vector`, `driver_watchdog`, `simulator_error`, `trace_integrity`.
- Fields are checked against the enumerated domains (file 02 L125). An unknown kind or
  out-of-domain field is NOT_IMPLEMENTED, never guessed.
- Ranking uses (evaluation step, stage-map row, file order, line). Compile errors take
  step 5 (driver) or 6 (checker).
- Within one step the first applicable row wins. This reproduces L166 (7) "exception
  wins over vector validation, which wins over watchdog". It also places simulator and
  trace-integrity faults, which have no in-cycle rule, after them.
- Two different events with an identical key are reported as outside the vocabulary.

Reason: the evaluation order is called "exact" and the row rule is the only tiebreak the
text gives.

## A-026 — Checker run-outcome records (DECIDED BY CLAUDE — approved under D-009)

`checker_runs` (R08–R11) and `null_runs` (M10–M12, P18, P19, P22) give two records per
fixture in four forms the pack does not define. **Decision (decided by Claude under
standing delegation, approved under D-009):**

| Record | Outcome |
|---|---|
| `{"timeout": true}` | `CHECKER_TIMEOUT\|phase=null_check` |
| `{"error_code": "CHECKER_RUNTIME_ERROR", "exception_class": C}` | `CHECKER_RUNTIME_ERROR\|class=C` |
| `{"type": "return_invalid", "reason": R}` | `CHECKER_RETURN_INVALID\|reason=R` |
| `{"verdict": V}` or `{"verdict": V, "diagnostics": [...]}` | a valid return with verdict V; each item is checked against B7's item form (File 30 L74) and counted as malformed if it fails |

These are outcome summaries, not literal return values: R09's `{"verdict": "FAIL"}` has
no `diagnostics` key and must not be classified as `MISSING_DIAGNOSTICS`. Real checker
returns use `classify_return` (File 30 L97 order). Adjudication follows L166 step (11)
and the CHECKER rows. A malformed item with both verdicts `PASS` gives
`ACCEPT_WITH_WARNING` with null stage and error class and diagnostic
`DIAGNOSTIC_FORMAT_WARNING` (Catalog L10). With both verdicts `FAIL`, the item is
discarded and `CHECKER_NULL_REJECT` stands ("verdict retained").

## A-027 — Driver-vector checks whose parameters are not supplied (DECIDED BY CLAUDE — approved under D-009)

File 30 L83 orders the vector checks: (a) key set, (b) string values, (c) width,
(d) `0`/`1`, (e) "the design-specific legal-input predicate". M26 supplies only the
expected keys (no widths). M27 supplies the predicate as English prose ("wr_en must be 0
when full is 1"), and `full` is an output port.

**Decision (decided by Claude under standing delegation, approved under D-009):**
- Checks run in order. A check whose parameters are not supplied cannot be run.
- If an earlier check fails, that is the result (M26: `EXTRA_KEYS`). If every runnable
  check passes, the outcome is not determined and the fixture is NOT_IMPLEMENTED,
  never ACCEPT.
- Within (a), missing keys are reported before extra keys, following the order of the
  reason enumeration (file 02 L125).
- A prose predicate is not executed. Turning prose into code would be fixture-specific
  code (rule 4), and the predicate belongs to the owner-written FIFO specification. M27
  stays NOT_IMPLEMENTED until the FIFO specification provides an executable predicate.
- Re-examined after the owner's correction of 23 Nov 2026: see A-038 (still
  NOT_IMPLEMENTED; executing it would require inventing behaviour).

## A-028 — Composite inputs: response plus a later-stage outcome (DECIDED BY CLAUDE — approved under D-009)

`null_runs` + `response_object` (M10–M12, P18, P19, P22) and `runtime_pair` +
`response_object` (M37) supply a response and the outcome of a stage that needs the
simulator. **Decision (decided by Claude under standing delegation, approved under
D-009):**
- The response is first run through every stage that can run in this environment. Today
  that is PARSE_SCHEMA through COMPILE_CHECKER; after step 4, also the sandboxed runtime
  import, `inspect.signature` and factory checks.
- A failure there is the result.
- Otherwise the supplied outcome stands in for the simulator-dependent stages (L166
  steps (7)–(10)) and is adjudicated.

Reason: these fixtures test the adjudication rule; the descriptor deliberately supplies
what a simulator would produce. Limitation: the driver's simulator runs are not
executed.

## A-029 — Serializer: grammar and the emitted-diagnostic set (DECIDED BY CLAUDE — approved under D-009)

Protocol L168: "The serializer accepts only a complete diagnostic emitted by the
authoritative stage map"; step (1) validates against "the normative closed grammar and
its enumerated values". M15 also supplies `allowed_diagnostics`. **Decision (decided by
Claude under standing delegation, approved under D-009):** the diagnostic must match the
closed grammar (L94–L123 templates with L125 domains, `src/openvef/serializer.py`
`GRAMMAR`), and, when the emitted set is supplied, be a member of it. Either failure is
`FEEDBACK_SERIALIZER_REJECT|reason=NON_NORMATIVE_DIAGNOSTIC` at stage
`FEEDBACK_SERIALIZER` with disposition `CONTROL_EXPECTATION` (Catalog L18).

## A-030 — Clause-ID packet checks: order and default regexes (DECIDED BY CLAUDE — approved under D-009)

**Decision (decided by Claude under standing delegation, approved under D-009):**
- The near-match check (`MALFORMED_CLAUSE_ID_TOKEN`) runs before set equality
  (`VISIBLE_CLAUSE_ID_SET_MISMATCH`), in the order File 31 L30 states them.
- A descriptor that omits a regex (M20 has no search or near-match regex) uses the value
  File 31 §8 fixes.
- Reserved-heading lines are compared after LF normalization (CRLF and lone CR → LF,
  File 31 L11, L27). Unresolved placeholders match `\{\{[A-Z0-9_]+\}\}` (File 31 L28).

## A-031 — Halt-signature domains versus supplied signatures (DECIDED BY CLAUDE — approved under D-009; pack inconsistency found)

Protocol L185 gives exact domains: `evaluator_component` is one of `SIMULATOR`, …,
`RTL_NULL_COMPARATOR`, and `stable_error_class` is the literal `NONE` for
`TRACE_INTEGRITY_FAILURE`. M42 and M47 supply signatures with
`"evaluator_component": "simulator"` and `"recorder"` (lower case), and M47's
trace-integrity signature has `"stable_error_class": "RecorderFault"`. These values are
outside the L185 domains.

**Decision (decided by Claude under standing delegation, approved under D-009):**
- `HaltSignature.build` enforces the L185 domains for signatures the ledger constructs
  from halt events.
- Ready-made signatures in a descriptor are compared for identity as given, because L185's
  recurrence rule needs only tuple equality.
- Under this reading M42 and M47 pass. **For the owners:** the descriptors disagree with
  L185's domains. If they should be invalid input, the pack needs a correction and a
  defined outcome for an invalid signature.

## A-032 — Control-vector expectations with extra keys (DECIDED BY CLAUDE — approved under D-009)

Catalog requirement 2 allows "a single exact expected disposition/stage/error/diagnostic
(or exact control-vector expectation)". L176 says the runner compares "disposition,
stage, error class and exact diagnostic bytes". M14, M17 and M41 add keys such as
`output_diagnostic_bytes` and `rerun_slots`, and M14/M17 have no `diagnostic` key.

**Decision (decided by Claude under standing delegation, approved under D-009):**
- A control-vector expectation is compared as a whole object: the runner's record must
  have exactly the same keys and values.
- Each extra key is a named property computed by a rule from the text:
  - M14: Protocol L168 step (2);
  - M17: L168 step (3);
  - M41: L183–L185 ("Discard all pre-halt partial scores", "every scheduled slot", "same
    frozen artifact bytes", "no confirmatory generation call").
- **Disclosure:** the property *names* come from the descriptors' expected objects,
  because the pack gives no output schema for control vectors. No *value* is read from
  an expected object.
- Comparing the four fields only was rejected, because it would report PASS while
  ignoring part of an "exact" expectation.

## A-033 — Change-class lifecycle vectors M48, M50, M53, M54, M58 (REVISED per owner correction; field derivations DECIDED BY CLAUDE — approved under D-009)

**History.** First recorded as OPEN, outside the delegation: the expected objects hold
values that appear only in the descriptors, and the `required_action` literals are
attached to fixture labels ("`M48` = …"), not to a rule.

**Owner correction (Krishika, 23 Nov 2026; Ayush's confirmation pending):** the
`required_action` values appear verbatim in the Protocol (L176); encode them from the
Protocol text. Derive the remaining fields from Protocol sentences under the delegation,
citing each sentence. Any field with no supporting sentence: say so, and keep that
fixture NOT_IMPLEMENTED.

**Decision (decided by Claude under standing delegation, approved under D-009):**
- Each `change_class` label is matched to the Protocol case its words name:
  - `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` → evaluator revision (L175
    "a frozen evaluator source/binary/…/configuration changed"; L183 (b));
  - `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` → shared-item revision
    (L181 "If any shared study item changes …");
  - `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` → study
    reset (L181 "A change in design membership, estimand or any confirmatory weight …");
  - `HALT_SIGNATURE_COMPONENT_ENUMERATION` → halt-signature schema (L175, L185);
  - `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` → design-specific revision (L181 "If a
    design-specific author-visible item changes …").
- L176 also labels each literal with its case and describes that case ("`M48`
  re-evaluates the affected scope …", "`M50` invalidates all designs …", "`M53` resets
  the preregistered design set and weights …", "`M58` invalidates both arms for the
  affected design only …"). That is how a literal is tied to a change class without
  reading the fixture ID: the code is keyed by change class, never by fixture ID.
- A field is produced only from a supporting sentence. "Supporting" means the sentence
  gives the value: a stated literal or list, or a yes/no/zero that the sentence asserts.
  A field whose *meaning* is stated but whose exact *token* appears nowhere in the
  Protocol is unsupported: writing it would mean copying the expected output (hard
  rule 4).
- The per-field table, with each citation, is `LIFECYCLE_CASES` in
  [src/openvef/ledger.py](../src/openvef/ledger.py).

| Fixture | Supported fields (citation) | Unsupported fields | Result |
|---|---|---|---|
| M53 | disposition (L176 "closed local control expectation"); stage `DESIGN_HALT` (L172, §7b); error class and diagnostic (L175 "The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic …"); `required_action` (L176); `old_confirmatory_artifacts_reusable: false` (L181 "cannot retain old confirmatory artifacts"); `new_preregistration_required: true` (L181 "always requires a new preregistered study"); `all_partial_ledgers_archived_and_disclosed: true` (L181 "archive and disclose all partial confirmatory ledgers"); `fresh_confirmatory_generation_required: true` (L181 "generate fresh confirmatory slots") | none | executed |
| M48 | disposition, stage, diagnostic (L175), `required_action` (L176), `new_evaluator_version_hashes_required` (L183 "assign a new evaluator version and hashes"), `f16_required` (L183 "run the frozen F16 eligibility procedure"), `reuse_same_artifact_bytes` (L183 "using the same already-generated artifact bytes"), `new_confirmatory_generation_calls: 0` (L183, L176) | `error_class` (see below); `rerun_scope_rule` (meaning in L183, token not in the text) | NOT_IMPLEMENTED |
| M50 | disposition, stage, diagnostic (L175), `required_action` (L176), `reuse_old_confirmatory_artifacts: false`, `new_confirmatory_generation_required: true`, `archive_and_disclose_partial_ledgers: true`, `new_preregistration_required: true` (all L181) | `error_class`; `affected_slots: "all_designs_x_all_arms"` (meaning in L181, token not in the text) | NOT_IMPLEMENTED |
| M54 | disposition, stage, error class and diagnostic (L175 "`M54` uses error class `HALT_SIGNATURE_SCHEMA` …"), `required_action` (L176), the three domain lists (L185, in its order) | `stable_error_class_rule`, `stable_diagnostic_code_rule` (meanings in L185, tokens not in the text) | NOT_IMPLEMENTED |
| M58 | disposition, stage, diagnostic (L175), `required_action` (L176), `reuse_old_artifacts_for_affected_design: false` (L181), `new_study_preregistration_required_if_…: true` (L181 "… even if the changed item is otherwise described as design-specific") | `error_class`; `affected_scope`, `unaffected_design_scope` (meanings in L181/L176, tokens not in the text) | NOT_IMPLEMENTED |

**Error class for M48, M50, M58.** No sentence states it. L175 gives error classes only
for the M41 vector (`MID_RUN_REEVALUATION`, which is *not* its diagnostic's CODE), M53 and
M54. The stage map shows that the error class need not equal the CODE (L154:
`SIMULATOR_ERROR|…` under `EVALUATOR_INFRASTRUCTURE_FAILURE`), so "error class = CODE" is
not a rule I can cite. The closest text is the v1.3.1 change log ("Corrected M53 to use
the declared `AUTHORING_REVISION_REQUIRED` error class"), which is historical, not
normative. The audit tables (file 62) likewise note "Error class … declared (L175–L176)"
only for M53 and M54.

**For the owners:** M48, M50, M54 and M58 need either a Protocol correction (error classes
for the three revision vectors, and the scope/rule tokens as literals) or an owner
ruling that these tokens may be taken from the descriptors.

## D-002 — Artifact-execution sandbox (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 23 Nov 2026 (Ayush's confirmation pending):** F18 artifact
execution uses Docker image `python:3.11.18-slim` pinned by digest, with
`--network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges`, a non-root
user, tmpfs for scratch, pids/memory/CPU limits and a wall-clock timeout. The pinned
`requirements.lock` is installed with `--require-hashes` inside the image. Cocotb and the
simulator are not pinned: fixtures that need them stay NOT_IMPLEMENTED.

Resolved digest: `python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535`.
Details and tests: [docs/sandbox.md](sandbox.md).

## D-002a — Pinned interpreter is the container's (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 23 Nov 2026 (Ayush's confirmation pending):** the pinned
interpreter for all F18 evidence is the `python:3.11.18-slim` container by digest. The
whole runner, static stages included, moves into the sandbox image; the host Python is
for development only. Recorded in docs and in every run's evidence.

Implemented: [runner/run_f18_container.sh](../runner/run_f18_container.sh) (host broker,
bash only) and the runner in broker mode; `interpreter_status` in every `summary.json`.
Pinned values: `3.11.18 (main, Nov  5 2026, 07:57:53) [GCC 14.2.0]`, SHA-256
`92d7e40ec50be176cb1b790c7568b7e08cd862137b5aa69f1413ba1967886b79`. CLAUDE.md hard
rule 2 was reworded to match (owner instruction, 23 Nov 2026). See [docs/sandbox.md](sandbox.md).

## D-003 — Simulation toolchain (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 23 Nov 2026 (Ayush's confirmation pending):** toolchain per
the Charter ("Cocotb; Icarus Verilog initially"): pin Icarus Verilog and cocotb at the
latest stable versions installable in that image; cocotb from `requirements.lock` with
hashes; iverilog via the image's package manager with the exact version recorded. This
is the owner approval hard rule 3 requires for the new lock entries.

Pinned: `cocotb==2.1.0` (+ `find-libpython==0.5.1`, `iniconfig==2.3.1`,
`packaging==26.3`, `pluggy==1.7.0`, `pygments==2.21.0`, `pytest==9.2.0`, all hashed);
Debian `iverilog` `12.0-2+b1`, `.deb` SHA-256
`febe027d2d3f5a7e570844d55758339ab5490acc09f404f214a8719d89d07056`, fetched from
snapshot.debian.org (owner instruction, 23 Nov 2026). Details in
[docs/sandbox.md](sandbox.md).

## D-004 — Yosys and MCY for the null-netlist export (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 23 Nov 2026 (Ayush's confirmation pending):** pin Yosys and
MCY for the null-netlist export (Protocol L233, L235, L544) at their latest stable
releases that build in the pinned image, from snapshot.debian.org or a pinned source
commit, with exact versions and hashes recorded in docs and in every run.

Pinned:
- **Yosys v0.71**, latest release, 12 Nov 2026. Debian trixie ships only 0.52, and that
  package would also bring a second, system Python (`python3`, `python3-click`) into
  the image.
  - Built from the release tarball `yosys.tar.gz`, SHA-256
    `2ec7c2ee63bb9b4065d6d5fff2786a1455e834f90ede8eb1d47791153ebef2a5`, the digest
    GitHub publishes.
  - Tag commit `b4c586fd37d0ec61bb38fc1a85fd6a2fde48fcd1`. The tarball's `.gitcommit`
    is CI merge commit `5628c13240f670b97aaaca3d47940c4afb8ff572`, which GitHub's
    compare shows has no file differences from it; the build asserts that value.
- **MCY v0.71**: commit `5a2cad0cbefceb7f23051c08348bd23128fd1046` (tag object
  `b062a44a…`). It is pinned by commit because MCY publishes no release asset.
  - Only the command-line tool and its scripts are installed. `mcy-dash` (Flask) and the
    GUI (Qt) are not needed for export.
- **`click`** was left out at first. Hard rule 3 requires owner approval for it, D-004
  does not mention Python packages, and the standing delegation excludes dependency
  pins. D-004a (below) approved it on 24 Nov 2026, and it is now in `requirements.lock`.
  The null-netlist export uses Yosys only.
- **Build tools** (gcc, cmake, bison, flex, …) come from snapshot.debian.org at
  `20261104T212339Z`, the snapshot recorded in the base image's own apt sources.
  - They are used in a separate build stage and are not in the final image.

Build configuration: CMake `release` preset (`-O3`), with these changes:
- Tcl off, editline off, Python off and unit tests off;
- `BUILD_SHARED_LIBS=OFF`, so no new shared libraries are needed at run time;
- everything else at release defaults, including ABC and the slang frontend.

Details and binary hashes: [docs/sandbox.md](sandbox.md). Not decided here: the frozen
export script, mutation modes and the mutant population (L544), which stay owner items.

## D-004a — `click` for the MCY command-line tool (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 24 Nov 2026 (Ayush's confirmation pending):** "approve
adding click (the version mcy requires) to requirements.lock with --require-hashes."
Recorded with D-004.

- MCY v0.71 (commit `5a2cad0c`) states no version bound for `click`. Its README says only
  `pip install click flask`, and `mcy.py` has `import click`.
- The pin is therefore the version pip-tools 7.7.0 resolves in the pinned base image:
  `click==8.5.1` (wheel and sdist hashes `8bb5376d…7e37`, `9bbfada7…72b4`). The lock is regenerated with the same `pip-compile --generate-hashes`
  command, starting from the existing lock, so the existing pins are unchanged.
- On Linux, `click` has no dependencies (`colorama` applies on Windows only).
- `flask` is not added: it serves only `mcy-dash`, which is not installed.
- After this decision, `mcy --help` runs in the image, and `tests/test_netlist_export.py`
  checks that.

## D-005 — FIFO design materials become AI-assisted (DECIDED — Ayush's confirmation pending)

**Owner decision by Krishika, 24 Nov 2026 (Ayush's confirmation pending)**, recorded in
the Owner Sign-off Pack, Amendment D-005: Part 2 row 4 changed. The Sign-off Pack is not
in this repository; this record follows the instruction as given in Claude Code.

**Now AI-assisted (Claude drafts; owners review and approve):**
- the FIFO design specification, port manifest and reset/legal-input rules;
- the other payload blocks (checklist item 17);
- the FIFO RTL;
- proposed frozen values and the trace schema (items 7–12).

**Unchanged (human-written):** F6/F17 control checkers and drivers, the directed suite and
the control mutants.

**Observation mask:** may be drafted, but it must be signed by an independent human mask
reviewer (Protocol L271).

CLAUDE.md's Scope section is updated to match. The disclosure wording is carried in
docs/assistance-log.md.

**Values:** depth 4 and width 8 were recommended by Claude in the claude.ai session and
adopted by Krishika. This attribution is as stated by Krishika on 24 Nov 2026; that
session is not in this repository. Claude Code did not recommend values in its own
session.

**Research consequence, for the owners to weigh:** Protocol L468 requires "Independently
authored, cycle-exact specs"; the pack does not define "independently authored". An
AI-drafted specification weakens that claim. The D-005 disclosure states it, and reports a
potential familiarity confound if a Claude model is evaluated.

## D-006 — Owner approvals of FIFO draft choices (DECIDED — Ayush's confirmation pending)

**Owner approvals by Krishika, 24 Nov 2026 (Ayush's confirmation pending)**, following a
review by Claude (claude.ai):
- A-042 is accepted: `rst` is harness-owned and not a driver-vector key.
- The almost-full threshold is 3 (FIFO-029).
- The top module name is `ovf_fifo`.
- The cycle cap is 64 (proposal item 7).
- The watchdog applies per run (proposal item 9).

**Not frozen.** Spec v0.2 and the item 7–12 proposals stay DRAFT until both owners freeze
them. Every run that uses them is provisional.

## D-007 — Feasibility-control authorship, mutant form, miter tool (DECIDED — Ayush's confirmation pending)

**Owner decisions by Krishika, 24 Nov 2026 (Ayush's confirmation pending)**, on a
recommendation by Claude (claude.ai), answering §8 of
[F1-F17-plan.md](F1-F17-plan.md):
1. The control drivers and checkers for F1–F5 and F7–F13 are owner-written, for
   independence from the harness author. Claude does not draft them.
2. Control mutants are RTL edits of `design/fifo/rtl/ovf_fifo.v`.
3. The mask-aware miter uses Yosys's built-in `sat` (no new dependency).
4. F1 reuses the reference driver (checklist item 14) with the F6 correct checker.

CLAUDE.md's Scope section is updated to match. The owner-artifact slots, their interfaces
and the controls each feeds are listed in `design/fifo/controls/README.md`.

## A-036 — Hash randomization inside the sandbox (DECIDED BY CLAUDE — approved under D-009)

File 30 §6 is headed "Import sandbox and deterministic execution". Paired runs compare
next-input schedules (Protocol L166 (8)), so a driver that iterates over a `set` of
strings would diverge between runs only because of Python's per-process hash
randomization. **Decision (decided by Claude under standing delegation, approved under
D-009):** the sandbox sets `PYTHONHASHSEED=0`. Reason: the section requires
deterministic execution, and the variable is set by the evaluator, so artifacts cannot
observe or change it (no `os`/`sys` import is allowed). The alternative, leaving
randomization on, would let evaluator configuration turn an honest artifact into
`DRIVER_NONDETERMINISM`.

## A-034 — An exception while importing an artifact module (DECIDED BY CLAUDE — approved under D-009)

After IMPORT_POLICY a module body holds only allowed imports, literal constants, a
docstring and definitions, so raising during import is close to impossible. The stage
map still has no row for it. **Decision (decided by Claude under standing delegation,
approved under D-009):** an exception while importing `driver.py` is
`RUNTIME_EXCEPTION|file=driver.py|phase=factory|class=<C>` at DRIVER_RUNTIME. Import is
the first execution of driver code, and the `factory` phase is the stage map's earliest
driver phase. The same rule applies to an import denied by the runtime allow-list. An
exception while importing `checker.py` in a checker invocation is
`CHECKER_RUNTIME_ERROR|class=<C>`: it is a checker process exception (File 30 L97).
Exceptions that are not `Exception` subclasses (e.g. `SystemExit` from `exit()`) are
treated the same way.

## A-035 — Order of post-construction checks; when `check_trace`'s signature is checked (DECIDED BY CLAUDE — approved under D-009)

Protocol L166 (7): "Factory return type and runtime signatures are checked immediately
after factory construction." The order between them is not given, and `check_trace`
lives in a file that runs "in a separate process after the trace is immutable" (B7).
**Decision (decided by Claude under standing delegation, approved under D-009):**
- After construction, check the return type, then `create_driver`'s signature, then
  `Driver.step`'s. This follows the sentence's order and the required-symbol sequence.
- `check_trace`'s runtime signature is checked in the checker's own process, before its
  first call. Loading checker code into the driver process would break the B7 separation.
- A runtime signature must have exactly the required names, all
  `POSITIONAL_OR_KEYWORD`, no defaults (File 30 L35/L37 "the same parameter
  names/kinds/counts").

## A-037 — Wall-clock limit during driver import or factory; F18 factory seed (DECIDED BY CLAUDE — approved under D-009)

The watchdog row is `WATCHDOG_TIMEOUT|phase=driver_step`, and `PHASE` for
`RUNTIME_EXCEPTION` is `factory` or `step`. No row covers a driver import or factory call
that never returns. **Decision (decided by Claude under standing delegation, approved
under D-009):**
- That case is an evaluator-side error: the runner records ERROR, never a REPAIR verdict
  or a made-up exception class.
- A checker invocation that exceeds the limit is `CHECKER_TIMEOUT|phase=null_check`, as
  defined.
- The factory call for F18 fixtures uses seed 0, since no fixture supplies a slot seed.
- The 20 s default limit is this build's value, not a frozen pack value.

## A-038 — M27: executing a prose legal-input predicate (DECIDED BY CLAUDE — owner review pending)

**Owner correction (Krishika, 23 Nov 2026; Ayush's confirmation pending):** "implementing
a check from prose is interpretation; do it under the delegation with citations, unless
it would require inventing behaviour." This re-examines A-027's M27 part.

M27 supplies `driver_return: {"wr_en": "1", "full": "1"}` and
`legal_input_predicate: "wr_en must be 0 when full is 1"`, and expects
`DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE`.

**Decision (decided by Claude under standing delegation, owner review pending):** M27
stays NOT_IMPLEMENTED, because executing it would require inventing behaviour:
1. The pack defines no predicate language. File 30 L83 (e) says only that "the full
   vector satisfies the design-specific legal-input predicate from the author-visible
   reset/legal-input specification". Turning the sentence into a check means inventing a
   grammar (`<port> must be <bits> when <port> is <bits>`) whose only known instance is
   this fixture's string: fixture-shaped code (hard rule 4).
2. The predicate's source is the author-visible reset/legal-input specification (L83;
   Protocol L61 "reset protocol and legal-input assumptions"). For FIFO that is the
   owner-written FIFO specification, which the Scope section reserves to the owners.
3. Checks (a)–(d) come first (L83 order), and M27 supplies no input-port set or widths.
   So the precondition that (a)–(d) pass cannot be established either. `full` is
   conventionally a FIFO output, and if so (a) would report `EXTRA_KEYS`; the pack does
   not say.

What would unblock it: an executable predicate in the FIFO specification's legal-input
rules (owner-written), plus the port manifest. The vector check then calls it as step (e).

**Revisited, 24 Nov 2026 (decided by Claude under standing delegation, owner review
pending), now that FIFO-042 exists as an executable predicate (D-005) and check (e) runs
it (A-041): M27 still stays NOT_IMPLEMENTED.** Reason 2 above no longer applies, because
the FIFO specification exists as a D-005 draft. Reasons 1 and 3 still hold, in narrower
form:
1. **FIFO-042 is not M27's predicate.**
   - M27 supplies its own predicate, "wr_en must be 0 when full is 1". FIFO-041 states a
     different rule: a write is illegal at full only "with `rd_en` = 0", because
     FIFO-030 makes a write together with a read at full legal.
   - The two disagree on the vector `wr_en` = 1, `rd_en` = 1 at full.
   - Substituting FIFO-042 would evaluate a predicate the fixture does not supply. That
     would also contradict the treatment of descriptor-supplied data in A-005 (owner
     decision) and A-044, where fixture-supplied data controls.
   - Executing M27's own string still needs a prose-to-code translation that has a
     single instance, which is fixture-shaped (hard rule 4). No predicate language exists
     (File 30 L83 (e); PD-06).
2. **No port set.** M27 gives no input-port set or widths, so checks (a)–(d), which
   precede (e) (File 30 L83), cannot be established.
   - The vector's own keys cannot be the port set, because check (a) would then pass by
     construction.
   - Under the FIFO port manifest (FIFO-004), the vector `{"wr_en", "full"}` fails (a)
     first, with `MISSING_KEYS` (`wr_data`, `rd_en`), and `full` is an output.
   - So evaluating M27 against the FIFO materials would not reach (e) at all.

**What would unblock it** (an owner or pack action, not an interpretation):
- either a revised M27 descriptor that supplies a port manifest with widths and an
  executable predicate;
- or an owner decision that M27 is evaluated against the frozen FIFO materials, in which
  case its expected outcome must be revisited, because (a) fires before (e).

## A-039 — Simulator failures: the `class` token and an overrun outside `step` (DECIDED BY CLAUDE — approved under D-009)

The stage-map row is `SIMULATOR_ERROR|target=<RTL_OR_NULL>|class=<EXCEPTION_CLASS>`
(L154), and `EXCEPTION_CLASS` is "the simple Python exception class name" (L125). A
failure of the `iverilog`/`vvp` processes is not a Python exception inside the
simulation. **Decision (decided by Claude under standing delegation, approved under
D-009):**
- The harness reports the exception its own process handling raises or would raise:
  - `CalledProcessError` when `iverilog` exits non-zero, or when `vvp` ends without the
    loop's result;
  - `TimeoutExpired` when the overall budget runs out while no `step` call is in
    progress.
- A budget overrun during driver import or factory stays an evaluator ERROR (A-037).
- An overrun inside `step` is `WATCHDOG_TIMEOUT|phase=driver_step`.

Reason: these are the simple class names of the Python exceptions that represent those
failures in the harness process, so the token is a real exception class, as L125
requires. The alternative, the fallback `Exception`, loses the distinction between a
design that does not build and a hung simulator. No current fixture depends on this.

## A-040 — Trace-row fields the pack names only in prose (DECIDED BY CLAUDE — owner review pending)

Protocol §5.2 gives three exact field names (L217 `inputs_consumed_at_edge_n`, L218
`outputs_after_edge_n`, L219 `next_inputs_scheduled_for_edge_n_plus_1`). L223 adds "Record
cycle index, reset, consumed inputs, post-edge outputs, next-input decision, driver
completion state and run status", without names or value domains. File 30 L92 gives
`reset_release_cycle` as a non-negative integer in the checker metadata. The trace
schema itself is TO FREEZE (L543).

**Decision (decided by Claude under standing delegation, owner review pending):**
1. The three given names are used verbatim as keys in every row. In these names, `n`
   refers to the row's own edge, not to a per-row key suffix: L216 says "For trace row
   `n`, record three separate fields", and a key that changed per row could not be
   "three separate fields".
2. Rows begin at the first reset edge. `cycle_index` is the row's edge number `n`. The
   reset-release edge is row `reset_release_cycle` (recorded with the trace), and the
   driver's `step` argument for row `n` is `n − reset_release_cycle`. Reason: a
   `reset_release_cycle` other than 0 is only meaningful if the trace has rows before
   release, and L221 says "the initial reset inputs are defined in the design pack". The
   competing reading, rows from release only, would make `reset_release_cycle` always
   0 and leave reset windows (L276) out of the trace.
3. `reset` is a boolean: true for rows before the reset-release edge.
4. `driver_completed` uses the name in L227 ("records `driver_completed=true`").
5. `run_status` is recorded once per trace: `COMPLETE_TRACE` when the cap is reached
   with no failure, otherwise `TRUNCATED_TRACE`. Reason: L328 "A driver/simulator error
   or timeout produces a truncated trace" and L332 "Reaching the cycle cap is normal
   termination; the checker is run on the complete trace". The tokens are built from
   those phrases. The pack gives no per-row status.
6. The row at the cap edge, and a row whose `step` failed or whose vector was invalid,
   are recorded with `next_inputs_scheduled_for_edge_n_plus_1: null`. An invalid vector
   is not driven (File 30 §4).
7. Consumed inputs are captured passively from the DUT input ports at the active edge
   (L262 "capture … passively"). If they differ from the prior row's scheduled vector,
   the run ends with `TRACE_INTEGRITY_FAILURE|reason=ROW_ALIGNMENT` (L221 "must agree
   with the prior row's scheduled input"; stage-map L155 reason domain). This branch has
   no runtime test: a correct harness does not produce it.
8. The waveform is FST through a `$dumpfile`/`$dumpvars` wrapper module (L223 "FST/VCD
   … where supported"). It is returned with its byte count and SHA-256.

**Open consequence:**
- `compare_runs` compares every row, including reset rows. Reset windows belong to the
  mask (L276), which is owner material.
- Until the mask exists, a raw divergence during reset is compared like any other row.

## A-041 — Scope of the legal-input predicate in check (e) (DECIDED BY CLAUDE — owner review pending)

File 30 L83 lists check (e) among the checks the harness makes on a returned vector
"before driving": "(e) the full vector satisfies the design-specific legal-input
predicate from the author-visible reset/legal-input specification". The same line says
"illegal protocol combinations are distinct reason codes". The pack gives no predicate
language (PD-06).

**Readings:**
- (a) The predicate sees only the vector's own values. It can then reject only
  combinations within one vector.
- (b) The predicate sees the vector together with the outputs that were sampled in the
  same row and given to the driver (`outputs_after_edge_n`, L218). Legality can then
  depend on protocol state.

**Decision (decided by Claude under standing delegation, owner review pending): (b).**
This scope is also part of the AI-drafted FIFO specification under D-005 (FIFO-040 to
FIFO-042). It therefore needs owner review twice: as a pack interpretation under the
standing delegation, and as drafted specification text under D-005.
Reasons from the pack text:
- Protocol L415 gives "undefined writes while full" as its example of an input sequence
  that violates "protocol legality". Whether a write happens while full depends on state,
  and a single vector cannot express it under reading (a).
- The reason-code wording is "illegal protocol combinations", and the stage-map token is
  `ILLEGAL_PROTOCOL_STATE` (L125). Both name protocol state, not only the vector.
- The sampled outputs are exactly what the driver was given in that `step` (L208, L221),
  so the predicate uses no information hidden from the author.

**What changes:**
- The DRAFT FIFO specification states this scope (FIFO-040) and gives the predicate as a
  Python 3.11 function of `(vector, sampled)` (FIFO-042).
- The harness's check (e) does not consume that predicate yet. It still accepts only the
  test-only literal `ALL_INPUTS_LEGAL` (A-038), and that stays so until the owners
  approve the specification.


## A-042 — Harness-owned reset and the "frozen top-level input-port" key set (DECIDED BY CLAUDE — accepted by Krishika under D-006, Ayush's confirmation pending)

File 30 L83 check (a): "its key set equals the frozen top-level input-port set exactly".
Protocol L212: "Every non-`COMPLETE` return must be a dictionary with exactly the frozen
top-level input-port keys".

**Readings:**
- (a) The key set is every top-level input port except the clock. A reset port is then
  a driver key, and the driver must always drive it inactive (FIFO spec v0.1).
- (b) The key set is the set the design pack freezes for driver vectors. It may leave out
  harness-owned control inputs, the clock and the reset, which the harness drives itself.

**Decision (decided by Claude under standing delegation, owner review pending): (b).**
This follows a spec review by Claude (claude.ai), adopted by Krishika. Reasons from the
pack text:
- Both sentences say "frozen", which points to the set the design pack freezes, not a
  mechanical list of all ports.
- The clock is already left out, even though it is a top-level input: drivers must not
  "own the clock" (L212), and "The harness owns the clock and scheduler" (L208). So the
  set is not literally every top-level input under either reading.
- Reset belongs to the harness and the design pack, not the driver:
  - L208: the first `step` call "is after reset release";
  - L221: "the initial reset inputs are defined in the design pack";
  - L260: paired runs "use identical seed, reset, simulator, cycle cap, safe-idle, driver
    API and watchdog". Reset is listed among the fixed run conditions, not among the
    driver's decisions.
- L217 still records every top-level input: "`inputs_consumed_at_edge_n`: top-level
  inputs stable immediately before active rising edge `n`". The harness therefore
  records held inputs in the consumed-input field.

**Implemented:**
- New optional design field `held_inputs` (`{port: bits}`). Reset-sequence vectors give
  these ports, and from the reset-release drive phase onward the harness holds them at
  the given values.
- They are not driver-vector keys: checks (a)–(d) use `input_ports` only.
- They are recorded in `inputs_consumed_at_edge_n` and in the scheduled vector, and
  they are part of the ROW_ALIGNMENT check.
- Designs without `held_inputs` behave exactly as before.

**Competing consequence:** under reading (a), the FIFO's `rst` returns to the driver key
set (v0.1), and `held_inputs` is unused.

## A-043 — What the L334 "null-netlist wall time" measures (DECIDED BY CLAUDE — owner review pending)

Protocol L334: "Proposed timeout: `T_timeout = max(5 × median(null-netlist wall time over
3 runs for the same artifact/design), 2 seconds)`." Item 9 is approved per run (D-006).
The pack does not say what one "wall time" covers, or what happens to the three runs'
outcomes.

**Readings:**
- (a) The evaluator's elapsed time for one complete null-netlist driver run, including the
  sandbox container start and teardown.
- (b) Only the simulator's own elapsed time inside the container.

**Decision (decided by Claude under standing delegation, owner review pending): (a).**
Reasons:
- "wall time" is the elapsed real time of a "run"; L229 says "A wall-clock timeout is
  separate" from the cycle cap, which points to a limit on the run as a whole.
- (a) can be measured identically for every artifact without instrumenting the
  simulator.

**Details:**
- The resulting T_timeout is applied as the per-run budget and as the per-step watchdog
  inside the container. That makes the limit slightly more lenient than the measurement,
  because container start is outside the in-container budget.
- The three calibration runs are used only for their wall times; their outcomes are
  ignored. Each calibration run has a build-default ceiling of 120 s (not from the pack),
  and a run that hits it counts as 120 s.

**What changes under (b):** T_timeout is smaller, and container start-up time no longer
affects it.

## A-044 — A fixture-supplied names-only port manifest (DECIDED BY CLAUDE — owner review pending)

F18 descriptor P17 carries `input.port_manifest` = `{"input_ports": [...]}` with port
names only. File 30 L83 check (a) uses "the frozen top-level input-port set". The catalog
does not say how a fixture's own manifest relates to the design materials. Here the
design materials are the D-005 DRAFT FIFO, whose ports differ from the fixture's.

**Readings:**
- (a) The fixture's names are the key set for checks (a)–(b) for that fixture, as with
  `manifest_clause_ids` (A-005, owner decision). If (a) and (b) pass under names that
  are not the design's ports, checks (c)–(e) cannot run (no widths) and the vector
  cannot be driven, so the result is not determined.
- (b) Ignore the fixture's manifest and use the design materials' ports.

**Decision (decided by Claude under standing delegation, owner review pending): (a).**
- A-005, an owner decision, already treats descriptor-supplied manifest data as the
  frozen manifest for that fixture.
- Reading (b) would discard part of the fixture's input.
- The rule is generic: it never depends on the fixture's ID or expected output.

**Implemented:** design field `driver_vector_keys`, which `run_f18.py` passes for the
`{port_manifest, response_object}` input shape. The simulation still runs on the design
materials, because the driver's `step` receives the design's outputs.

**What changes under (b):** for P17's vector `{"data": "0"}`, nothing does. It lacks
keys under both readings, so the result is `MISSING_KEYS` either way.

## A-045 — Construction of the mask-aware miter (DECIDED BY CLAUDE — approved under D-009)

> [02 L291] "Build the miter with the same observation mask as the trace comparator and with the same reset sequence and legal-input assumptions from the design specification."

The pack does not say:
- on which side's outputs a legal-input predicate that reads outputs is evaluated;
- how the comparator's executable Python predicate becomes a miter assumption;
- what the initial register state is.

FIFO-043 (DRAFT spec) says the FIFO-042 rules are the miter's assumptions.

**Decision (decided by Claude under standing delegation, approved under D-009):**
- **Legal-input predicate:** evaluated on the null (gold) side's outputs at that step,
  i.e. the outputs the driver would have sampled. This is the same side as the mask
  predicate (L273: "evaluated using the null-netlist trace for both members of a pair").
- **Assumption generated from the spec's own predicate:** by exhaustive enumeration of
  every input and output bit (`miter.compile_predicate`). Support bits are proven by
  invariance over the whole domain, and the expression is the truth table on the
  support. So the assumption equals the predicate by construction; there is no
  hand translation. This answers plan Q5.
- **Reset:** each reset vector forces every input at its step. Afterwards, held inputs
  keep their held value.
- **Initial state:** all registers start at zero (`sat -set-init-zero`), a stated
  bounded-equivalence assumption (L544, TO FREEZE). The simulator starts memories at X
  instead. A mutant that reads an unwritten FIFO slot could therefore disagree between the
  miter and the simulator. F4's replay check would show it.
- **Shortest counterexample (L293):** after a failure at the full bound, ascending bounds
  are checked; the first failing bound is the shortest.
- **Step mapping:** sat step t holds the state after t−1 edges, so trace row n is step n+2.

**What changes under another reading:**
- Evaluating the predicate on the mutant side would let a mutant that corrupts `full`
  change which inputs are legal for the comparison.
- Undefined initial state (`-set-init-undef`) would need X-aware triggers.

## A-046 — Mapping harness events to §12 terminations in a pair run (DECIDED BY CLAUDE — approved under D-009)

> [02 L306] "Driver/simulator error, split by whether a masked divergence was recorded before termination."

**Decision (decided by Claude under standing delegation, approved under D-009):** on the
mutant run:

| Harness event | §12 termination | Source |
|---|---|---|
| `driver_runtime`, `driver_vector` (an invalid or illegal vector, which the harness does not drive), `simulator_error` | DRIVER_SIM_ERROR | — |
| `driver_watchdog` | TIMEOUT | L333 |
| `trace_integrity` (row alignment) | integrity failure → INVALID_PAIR | L311 |

An evaluator-side failure of the harness itself (no adjudicable result) is raised, not
classified.

Reason: §12 has no separate class for an invalid vector after an artifact is valid.
The vector ends the run as the driver's fault, which is the "driver" half of rule 2.

The rows recorded before a watchdog kill are now kept (sandbox/sim.py `_truncated`), so
"masked divergence recorded before termination" is measured on them.

## A-047 — A null run that fails inside a pair (DECIDED BY CLAUDE — approved under D-009)

> [02 L336] "A null run must complete within its watchdog for a mutant-run timeout to be interpreted."

**Decision (decided by Claude under standing delegation, approved under D-009):** if the
null member of a pair does not complete, the pair is `INVALID_PAIR` as an integrity
failure.

Reason: the artifact's null runs passed during validation, so a failing null in the pair
can't be explained from predeclared evidence. L311: "If the cause cannot be determined
from predeclared integrity evidence, classify conservatively as INVALID_PAIR."

## A-048 — Checker invocations per pair (DECIDED BY CLAUDE — approved under D-009)

§12 classifies a pair by what "checker returns" on the complete mutant trace. The repeat
rule (two invocations) is stated for null traces (L247) and for the panel (L435), not for
pair classification.

**Decision (decided by Claude under standing delegation, approved under D-009):** one
invocation, in its own process, on the frozen mutant trace bytes. The bytes are
re-hashed afterwards. The pair record also says whether the mutant trace is
byte-identical to the null trace (needed for F8, L311).

## A-049 — Panel false-alarm event per benign trace (DECIDED BY CLAUDE — approved under D-009)

> [02 L429] "Define the false-alarm event rate as the number of `FAIL` outcomes on the `B_ds` benign original-RTL/null-netlist reference traces divided by `|G_cd| × B_ds`"

Each benign trace is evaluated twice (L417).

**Decision (decided by Claude under standing delegation, approved under D-009):** a
benign trace carries one false-alarm event if either evaluation returned FAIL. This keeps
the rate within [0, 1], and an inconsistent pair still counts the FAIL it contains, as
L423 asks ("so an error does not hide a simultaneous false alarm").

## A-050 — Which mutant traces the panel evaluates (DECIDED BY CLAUDE — approved under D-009)

**Decision (decided by Claude under standing delegation, approved under D-009):** each
checker is evaluated twice on every exposed case in `Q_ds` (L427, L435), and twice on
every raw-only unmasked case (for `PANEL_STRICTER_THAN_MASK_EVENT`, L427).

Mutant traces with no raw divergence are not evaluated: they are byte-identical to the
null trace of the same scenario, which is already in the benign set.

Plan Q6 is settled the same way: the "valid" of F5 (L514) is `rd_valid`, the predicate of
the DRAFT mask (MK05); this stays open until the mask is signed.

## A-051 — Non-deterministic run-record fields for F1 (DECIDED BY CLAUDE — approved under D-009)

> [02 L510] "Traces match excluding explicitly non-deterministic metadata"

**Decision (decided by Claude under standing delegation, approved under D-009):**
- The checker-facing trace rows are compared byte for byte, with no exclusions.
- In a simulation run record, only `waveform` is excluded, by an explicit list
  (`alignment.NONDETERMINISTIC_RESULT_FIELDS`).
- Observed on the pinned image: two otherwise identical runs give FST files that differ
  in the header date string ("… 15:16:49 2026") and in a later block. All other fields,
  including the per-row simulator times, are identical.

## A-052 — F14 "ports" comparison (DECIDED BY CLAUDE — approved under D-009)

> [02 L523] "Stable null hash, top module and ports"

**Decision (decided by Claude under standing delegation, approved under D-009):**
- Ports match when the set of (name, direction, width) is the same in the RTL and in both
  exported netlists.
- Declaration order is recorded and compared separately (`port_order_same_as_rtl`), but
  it is not a pass condition. Connections are by name in the harness and the miter.

## D-008 — Governance: approvals signed by Krishika alone take effect (DECIDED)

**Owner governance rule by Krishika (co-owner), 24 Nov 2026**, given in Claude Code:
"decisions and approvals signed by Krishika alone take effect now. Ayush Kumar Singh's
agreement is recorded ONCE, in a single 'Ayush ratification pending' entry in
docs/AUDIT-READINESS.md, and is not repeated on individual items."

**Applied to:** the owner freeze package. Krishika's signature (commit `a955245`) freezes
A1–F1. The record is
[FREEZE-RECORD-2026-11-24.md](FREEZE-RECORD-2026-11-24.md) /
`design/fifo/freeze/freeze-record-2026-11-24.json`.

**Supersedes:** step 3 of the package ("A line is frozen only when both owners approve
it"), and the CLAUDE.md line that kept Claude-decided readings "owner review pending until
both owners review it".

**Does not change:**
- the independent human mask reviewer's signature (Protocol L271), which no owner signature
  replaces;
- the standing-delegation readings that no owner has reviewed yet;
- earlier records, which keep their wording as written.

## D-009 — Approval of the remaining Claude-decided readings (DECIDED)

**Owner decision by Krishika (sole builder), 24 Nov 2026**, adopting a Claude (claude.ai)
recommendation; pasted into Claude Code: "every reading decided under the standing
delegation and not yet owner-approved (A-007..A-012, A-013 tie, A-015..A-037, A-039,
A-045..A-052, F15 case table) is approved by Krishika as decided, without itemised owner
review."

**Record:** `design/fifo/freeze/readings-approval-D-009.json` holds the SHA-256 of each
approved section, and of `src/openvef/f15.py`, as at commit `23e6193`
(`sha256_as_approved`), and after the wording cleanup of "owner review pending" to
"approved under D-009" (`sha256`). `tests/test_freeze_package.py` checks that undoing
that wording gives the approved bytes back. An item changed in any other way is not
covered. Summary table: [READINGS-REVIEW.md](READINGS-REVIEW.md).

**Limits:** no reading was reviewed item by item, and the recommendation came from Claude,
which also decided the readings. Pack defects stay defects; a reading approved here does
not correct the pack. Readings decided later are not covered. Takes effect under D-008;
Ayush's ratification stays the single entry in AUDIT-READINESS.md.

## DEV-001 — Deviation from Protocol L271 (DECIDED)

The owner accepted the observation mask and File 24 table without an independent review.
Full record: [DEVIATIONS.md](DEVIATIONS.md). This supersedes, for this mask only, D-008's
statement that no owner signature replaces the L271 signature. L271 itself stays unmet.

## D-010 — Mask placeholder fixes and re-freeze (DECIDED)

**Owner decision by Krishika**, given in Claude Code with the saved mask review: "fill
spec_version_sha256 with the frozen spec hash in both mask files; set status to "FROZEN under D-010; reviewed non-independently (DEV-001)"; set reviewer fields to "Claude (claude.ai), non-independent, DEV-001; accepted by owner Krishika". Re-freeze the mask at the new hashes". Labels
become "cleared under DEV-001 (non-independent review saved)".

**Applied to:** every row's `mask_reviewer`, `independent_reviewer` and `review_status`, and
the JSON `status`. Mask content is unchanged. The JSON status no longer repeats
"evaluator-only: never part of an authoring packet"; that Protocol rule (L270) still applies.
L271 stays unmet ([DEVIATIONS.md](DEVIATIONS.md)).

## D-011 — Independent-reviewer column and L270 reminder (DECIDED)

**Owner decision by Krishika**, given in Claude Code: "set the independent_reviewer column to
"none (DEV-001)" in every row; restore "Evaluator-only: never part of an authoring packet
(L270)" to the JSON status text. Leave file names and author_packet_location cells as they
are (record why)." This supersedes D-010 on those two points.

**Why the file names and `author_packet_location` cells stay** (reasons recorded by Claude
at the owner's instruction):
- `design/fifo/design-materials-DRAFT.json`, frozen at its signed hash (B1–B6), names
  the mask JSON by its current path. Renaming it would break a frozen item.
- The mask JSON names the table by its path, and earlier evidence, records and reviews
  cite both paths. Renaming would break that trail.
- The cells name `docs/fifo-spec-v0.2.md (DRAFT)`. The frozen specification keeps its DRAFT
  wording, because the package says signed files are not edited in place. Frozen status is
  set by the freeze record and its hashes, not by the word "DRAFT".
- The saved review covers those cells, and changing them has no effect on what is compared.
