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
its dependencies, pinned with hashes in `requirements.lock`. The development workspace
cannot install packages; this is done on the owners' WSL machine. **Owner decision needed:
exact version.**
