# Specification ambiguities and open owner decisions

Each item quotes the source, lists the readings, and says what changes. Items marked
PROVISIONAL are implemented one way so work can continue; the owners must confirm or
change them before any evidence run counts toward F18.

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

## A-007 — SOURCE_AST order across files: per file, or by stage-map row (PROVISIONAL)

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

Implemented: (a), which File 30 §3 L27 states explicitly (unit test
`test_driver_checked_before_checker`). **Owner confirmation needed.**

## A-008 — U+FEFF at the start of a source string (OPEN; raises UnsettledSpec)

Stage map: "Invalid UTF-8/BOM or syntax parse error" → `SOURCE_SYNTAX_REJECT`; File 30 §3
L27: "strict UTF-8 decode with BOM rejection". The source arrives as a JSON string, not
bytes, so "BOM" has no byte meaning here.

Readings: (a) a leading U+FEFF is the BOM and is rejected before the empty check — but
the pack gives no line/column for a BOM rejection; (b) U+FEFF is an ordinary character
and `ast.parse` decides (on 3.11.18 it raises SyntaxError "invalid non-printable
character U+FEFF", line 1, offset 1, so `…|line=1|column=1`); (c) strip it as Python
does when reading a UTF-8-SIG file — excluded by "BOM rejection". (a) and (b) both
reject; they can differ only in the line/column, which the pack does not give for (a).
Not implemented: a
leading U+FEFF raises `UnsettledSpec("A-008")`, which the runner reports as
NOT_IMPLEMENTED. U+FEFF later in the source is left to `ast.parse` (a syntax error).
**Owner decision needed.**

## A-009 — Source string that is not valid UTF-8 (OPEN; raises UnsettledSpec)

JSON `\ud800` escapes decode to lone surrogates, which cannot be encoded as UTF-8.
`ast.parse` on 3.11.18 raises `UnicodeEncodeError`, not SyntaxError. The stage map
puts this under "Invalid UTF-8 …" → `SOURCE_SYNTAX_REJECT|file=<FILE>|line=<LINE>|
column=<COLUMN>` but says nothing about the line or column. (Raw input of this kind
also passes PARSE_SCHEMA: Python's `json` accepts lone-surrogate escapes.)
Not implemented: raises `UnsettledSpec("A-009")`. **Owner decision needed** (line/column
for this case, or a different rule such as rejecting lone surrogates at PARSE_SCHEMA).

## A-010 — Which characters count as whitespace for SOURCE_EMPTY (OPEN; partly implemented)

Stage map: "Empty/whitespace-only source". The pack does not define whitespace.
Readings: (a) JSON whitespace (space, tab, LF, CR); (b) `str.isspace()`, which adds
U+000B, U+000C, U+001C–U+001F, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
U+202F, U+205F, U+3000; (c) Python tokenizer whitespace (space, tab, form feed, newlines).
What changes: a source of only U+000C parses on 3.11.18 (empty module, so it passes
SOURCE_AST under (a)), but is SOURCE_EMPTY under (b) and (c); U+000B or U+00A0 alone is
`SOURCE_SYNTAX_REJECT|…|line=1|column=1` under (a)/(c) but SOURCE_EMPTY under (b).

Implemented: the empty string and sources made only of space/tab/LF/CR are SOURCE_EMPTY
(every reading agrees; covers P12a, P12b, M16). A source made only of `str.isspace()`
characters that includes any other character raises `UnsettledSpec("A-010")`. A
comment-only source is not treated as empty (comments are not whitespace).
**Owner decision needed.**

## A-011 — SyntaxError with no usable line, or another exception from ast.parse (OPEN; raises UnsettledSpec)

The column rule covers a missing offset ("If `offset` is absent, null or less than 1,
emit `column=1`") but nothing covers a missing or non-positive `lineno`, although
`LINE` must be a positive decimal integer. On 3.11.18, a NUL character in the source
gives SyntaxError "source code string cannot contain null bytes" with `lineno=None`.
`ast.parse` may also raise exceptions that are not SyntaxError (e.g. `RecursionError`,
`MemoryError`, `UnicodeEncodeError` — see A-009); the stage map does not say whether
these are "syntax parse error". Not implemented: both raise `UnsettledSpec("A-011")`.
**Owner decision needed.**

Related observation (no change): the column rule says to emit "the positive one-based
source-character column reported by CPython". On 3.11.18 `ast.parse` of a `str` reports
a character offset (`é = 1; y = )` gives offset 12, the character column, not 13, the
byte column — unit test `test_column_counts_characters_not_utf8_bytes`). Warnings from
`ast.parse` (e.g. invalid escape sequences) are not failures; the runner must not be
started with `-W error`, which would turn them into SyntaxError.

## A-012 — Runner adapters for source-pair inputs and the M36 unit vector (source pair PROVISIONAL; M36 OPEN)

A-002's decision covers `response_object` only. Two more input shapes reach SOURCE_AST.

**`{driver_source, checker_source}` (M16, M29) — PROVISIONAL.** Implemented: run
SOURCE_AST directly on the two strings (no envelope, schema or clause-ID step), then
continue with later stages. Alternative: wrap them in a full response object first —
the pack gives no wrapper, so this would need one. **Owner confirmation needed.**

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
(c) the pack is corrected so M36's class and disposition are defined.
**Owner decision needed.**

## A-013 — Order of IMPORT_POLICY categories within one file (OPEN)

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
violation. **Owner decision needed before IMPORT_POLICY is connected to the runner.**

## A-014 — Order between PROHIBITED_BUILTIN and GLOBAL_RANDOM_USE (OPEN)

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
No current fixture has both. **Owner decision needed** (with A-013).

## A-015 — Module-body statements the text does not classify (OPEN)

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
   only.

The step-6 classifier will raise `UnsettledSpec("A-015")` for these. No current fixture
uses any of them (P28, M04a, M04b and M57 do not). **Owner decision needed.**

## A-016 — Prohibited-name rule: definitions, parameters and `builtins` (OPEN)

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
`PROHIBITED_BUILTIN|name=open`, consistent with the first form. Planned implementation:
`ast.Name` nodes in any context, and `Attribute(value=Name(id="builtins"))` only; (1)
and `__builtins__` are not flagged. **Owner confirmation needed.**

## A-017 — `random.<attribute>` when `random` is not the imported module (OPEN)

File 30 §2 L20: "Any direct attribute access on the module name `random` other than
`random.Random` is rejected". Protocol §3.4 (file 02 L133): "direct `random.<attribute>`
use other than `random.Random` emits `GLOBAL_RANDOM_USE`."

Unsettled: whether the check is purely syntactic (`Attribute(value=Name(id="random"))`
anywhere) or applies only when `random` is the imported module — e.g. a parameter named
`random`, or a file without `import random`. M09, M22, M23 all `import random` and use
it inside a method, so both readings pass them. Planned implementation: syntactic.
**Owner confirmation needed.**

## A-018 — Non-ASCII identifiers inside f-string replacement fields (OPEN)

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
for that). No current fixture uses an f-string with a non-ASCII identifier.
Implemented: (a). **Owner decision needed.**

## A-019 — Line breaks for the identifier scan: lone CR (OPEN; raises UnsettledSpec)

File 30 §2 L21 / Protocol §3.4 (file 02 L133): the column is computed "from the UTF-8
byte length of the source-line prefix"; the pack does not define a source line. Probe
on CPython 3.11.18: for `"x = 1\ry = 2\n"`, `ast.parse` puts `y = 2` on line 2, but
`tokenize.generate_tokens` over the same string treats the lone CR as an `ERRORTOKEN`
and reports `y` on line 1. A non-ASCII identifier after a lone CR would therefore get a
line number that disagrees with the AST. CRLF is consistent in both. Not implemented: a
source with a CR not followed by LF raises `UnsettledSpec("A-019")`. No current fixture
contains a lone CR. **Owner decision needed.**
