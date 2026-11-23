# Specification ambiguities and open owner decisions

Each item quotes the source, lists the readings, and says what changes. Items marked
PROVISIONAL are implemented one way so work can continue; the owners must confirm or
change them before any evidence run counts toward F18.

## A-001 — OUTPUT_TRUNCATED versus envelope rejection (PROVISIONAL)

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
JSON is complete. **Owner decision needed.**

## A-002 — How fixture input shapes are fed to the parser (OPEN)

The catalog says each descriptor holds "a literal JSON input" but does not define how the
runner turns each input shape into the call under test. 86 fixtures use `response_object`
(an already-decoded JSON object); others use `events`, `null_runs`, `change_class`, etc.

For `response_object`, readings: (a) serialize to UTF-8 JSON bytes and run the full
parser; (b) skip envelope decoding and start at schema validation. For every current
`response_object` fixture both readings should give the same result, because the object
has no duplicate keys and serializes to valid JSON — this is to be confirmed when part 1b
exists. Not implemented yet. **Owner decision needed before those fixtures run.**

## A-003 — NaN / Infinity tokens (PROVISIONAL)

File 30 §1 requires one JSON object and rejection of malformed JSON. Python's `json`
module accepts `NaN`, `Infinity` and `-Infinity`, which are not JSON under RFC 8259.
Implemented: rejected as JSON syntax (`SCHEMA_REJECT|pointer=/`). No current fixture
exercises this. **Owner confirmation needed.**

## D-001 — Pin the Draft 2020-12 validator (DECISION)

Protocol §3.4: "Use the pinned Draft 2020-12 validator". Register 16 L40 lists the parser
version as TO FREEZE. Schema validation (part 1b) needs an exact `jsonschema` version and
its dependencies, pinned with hashes in `requirements.lock`.

**Decided (owners, 23 Nov 2026, session 2 instruction):** `jsonschema==4.26.0`. Resolved
with pip-tools 7.7.0 (`pip-compile --generate-hashes`, separate tools venv) on CPython
3.11.18: attrs 26.1.0, jsonschema-specifications 2025.9.1, referencing 0.37.0,
rpds-py 2026.9.1, typing-extensions 4.16.0. Installed into `.venv` with
`pip --require-hashes`. Register 16 L40 still needs this version recorded as frozen.

## A-004 — `UNSPECIFIED` text must identify the missing behavior (OPEN)

File 30 §1 L9: "`UNSPECIFIED` is permitted only for behavior not specified in the received
packet, and the text must identify the missing behavior."

Readings: (a) not mechanically checkable; the parser accepts any `UNSPECIFIED` whose text
passes the schema (`minLength` 1) and the requirement is reviewed by humans; (b) the parser
must apply some mechanical test, which the pack does not define (no diagnostic, pointer or
rule is given). Fixture P21 ("UNSPECIFIED used with a non-empty description of missing
behavior") expects acceptance at this stage and is consistent with (a).

Implemented: (a) — `UNSPECIFIED` is accepted with no text check. No pointer exists for a
failure under (b). **Owner confirmation needed.**

## A-005 — Source of the manifest `clause_ids` for fixtures (PROVISIONAL)

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
either way. **Owner confirmation needed for (a).**

## A-006 — Sorting array-index tokens in the schema pointer key (PROVISIONAL)

Protocol §3.4 / File 30 §1: sort by "instance token sequence, lexicographically by Unicode
code point". RFC 6901 tokens are strings, so array index `10` sorts before `2`. The
clause-ID rule, by contrast, says "the lowest numeric `assumptions` index".

Readings: (a) literal — compare every token as a string, so `/assumptions/10/text` is
reported before `/assumptions/2/text`; (b) compare array-index tokens numerically, as in
the clause-ID rule.

Implemented: (a), the literal text (unit test `test_array_index_tokens_compare_as_strings`).
It matters only when schema errors exist at two array indexes with different digit
counts (needs ≥ 11 assumptions or dependencies items). No current fixture exercises it.
**Owner confirmation needed.**
