"""F18 fixture runner (v1.3.6).

Implements the runner duties in Catalog (file 36) "Fixture requirements" 1-6 and L176:
verify the index, every descriptor's SHA-256 and byte length, the exact count (144),
then execute each fixture and compare exact expected values.

Rules (CLAUDE.md): the code path is chosen from the fixture INPUT shape only, never
from its ID or expected output. A fixture whose path reaches a stage that is not yet
implemented is reported NOT_IMPLEMENTED -- never PASS.

Usage (evidence, D-002a):  runner/run_f18_container.sh <run_class>
Usage (development only):  python3.11 -I runner/run_f18.py <baseline_root> <evidence_dir> <run_class>
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.envelope import Envelope, Failure, parse_envelope  # noqa: E402
from openvef.schema import SCHEMA_REL, ValidatedResponse, load_validator, validate_clause_ids, validate_schema  # noqa: E402
from openvef.import_policy import check_import_policy  # noqa: E402
from openvef.ast_signature import check_ast_signature, check_compile  # noqa: E402
from openvef.assembler import (NEAR_MATCH_REGEX_DEFAULT, SEARCH_REGEX_DEFAULT, check_reserved_heading_lines,  # noqa: E402
                               check_unresolved_placeholders, check_visible_clause_ids)
from openvef.runtime import RuntimeStageError, factory_checks  # noqa: E402
from openvef.sandbox import SandboxUnavailable, broker_mode, ensure_image  # noqa: E402
from openvef import simulator_stages  # noqa: E402
from openvef.simulation import SimulationError  # noqa: E402
from openvef.ledger import HaltSignature, halt_after_recovery, lifecycle_expectation, operational_recovery  # noqa: E402
from openvef.serializer import check_diagnostic, serialize, truncate  # noqa: E402
from openvef.stage_map import (RTL_NULL_CONTROL_FAILURE, EventError, NotDetermined, adjudicate_checker,  # noqa: E402
                               first_event, outcome_from_record, paired_run_failure, runtime_signature_failure,
                               validate_vector)
from openvef.source_ast import FILE_ORDER, UnsettledSpec, check_sources, syntax_reject  # noqa: E402

INDEX_REL = "41_F18_Fixture_Inputs/fixture-index.json"
INDEX_SHA256 = "f37808c7a662b8fdf164e27feaef023aadd6dfefaada35d11c3719185d1bde54"
EXPECTED_COUNT = 144
COMPARE_KEYS = ("disposition", "stage_id", "error_class", "diagnostic")
# 27_SHA256SUMS.txt entry for the canonical response schema (File 30 §1).
SCHEMA_SHA256 = "6fb5d282b09540949f21ee134b522841c3345031cb3e118a83bdffc18b4e7c34"
PINNED_DISTRIBUTIONS = ("jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py",
                        "typing_extensions", "cocotb", "find-libpython", "iniconfig", "packaging", "pluggy",
                        "pygments", "pytest")
# D-002a: the pinned interpreter for all F18 evidence is CPython 3.11.18 in the
# python:3.11.18-slim image pinned by digest (docs/sandbox.md).
PINNED_PYTHON_VERSION = "3.11.18 (main, Nov  5 2026, 07:57:53) [GCC 14.2.0]"
PINNED_PYTHON_SHA256 = "92d7e40ec50be176cb1b790c7568b7e08cd862137b5aa69f1413ba1967886b79"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class IntegrityError(Exception):
    pass


def load_index(root: Path) -> list[dict]:
    index_path = root / INDEX_REL
    raw = index_path.read_bytes()
    if sha256_bytes(raw) != INDEX_SHA256:
        raise IntegrityError(f"fixture index SHA-256 mismatch: {sha256_bytes(raw)}")
    fixtures = json.loads(raw)["fixtures"]
    ids = [f["fixture_id"] for f in fixtures]
    if len(fixtures) != EXPECTED_COUNT:
        raise IntegrityError(f"fixture count {len(fixtures)} != {EXPECTED_COUNT}")
    if len(set(ids)) != len(ids):
        raise IntegrityError("duplicate fixture IDs in index")
    on_disk = {p.name for p in (root / "41_F18_Fixture_Inputs").glob("*.json")} - {"fixture-index.json"}
    listed = {Path(f["path"]).name for f in fixtures}
    if on_disk != listed:
        raise IntegrityError(f"unlisted or missing descriptors: {sorted(on_disk ^ listed)}")
    return fixtures


def load_descriptor(root: Path, entry: dict) -> dict:
    raw = (root / entry["path"]).read_bytes()
    if len(raw) != entry["bytes"] or sha256_bytes(raw) != entry["sha256"]:
        raise IntegrityError(f"{entry['fixture_id']}: descriptor hash/length mismatch")
    desc = json.loads(raw)
    if desc["fixture_id"] != entry["fixture_id"]:
        raise IntegrityError(f"{entry['fixture_id']}: descriptor ID mismatch")
    if desc["expected"] != entry["expected"]:
        raise IntegrityError(f"{entry['fixture_id']}: index/descriptor expected mismatch")
    return desc


def load_schema_validator(root: Path):
    path = root / SCHEMA_REL
    if sha256_file(path) != SCHEMA_SHA256:
        raise IntegrityError(f"response schema SHA-256 mismatch: {sha256_file(path)}")
    return load_validator(path)


def failure_record(result: Failure) -> dict:
    return {
        "disposition": result.disposition,
        "stage_id": result.stage_id,
        "error_class": result.error_class,
        "diagnostic": result.diagnostic,
    }


class Blocked(Exception):
    """The fixture reaches a stage or rule that is not implemented (NOT_IMPLEMENTED)."""


ACCEPT = {"disposition": "ACCEPT", "stage_id": None, "error_class": None, "diagnostic": None}


SANDBOX: dict | None = None  # set by main() once the pinned image is verified
# D-005 DRAFT design materials for L166 (7)-(11); set by main(). Every result that uses
# them is provisional (simulator_stages.prepare lists why).
DESIGN_MATERIALS_FILE = "design/fifo/design-materials-DRAFT.json"
SIM: dict | None = None
SIM_UNAVAILABLE = "not prepared"
PROVISIONAL: dict = {}  # fixture descriptor id -> simulator details, filled by sim_stages


def source_stages(driver_source: str, checker_source: str) -> Failure | None:
    """SOURCE_AST, IMPORT_POLICY, static AST_SIGNATURE, COMPILE_DRIVER, COMPILE_CHECKER
    (Protocol §3.4 evaluation order (2)-(6)), then the sandboxed runtime import, factory
    return-type and signature checks (File 30 §3 L27, L39; L166 (7)). None means every
    implemented stage passed."""
    sources = {"driver.py": driver_source, "checker.py": checker_source}
    try:
        trees = check_sources(list(sources.items()))
        if isinstance(trees, Failure):
            return trees
        static = check_import_policy(sources, trees) or check_ast_signature(trees) or check_compile(sources)
    except UnsettledSpec as exc:
        raise Blocked(f"blocked on docs/ambiguities.md {exc}") from exc
    if static is not None:
        return static
    if SANDBOX is None:
        raise Blocked("static stages and compilation passed; sandbox unavailable, runtime stage not run")
    return factory_checks(driver_source)


def response_object(inp: dict) -> dict:
    """The response object a response input carries (envelope already accepted)."""
    if "response_object" in inp:
        return inp["response_object"]
    raw = (inp["raw_response_utf8"].encode("utf-8") if "raw_response_utf8" in inp
           else base64.b64decode(inp["raw_response_base64"], validate=True))
    return parse_envelope(raw, inp.get("provider_finish_reason")).obj


def sim_stages(desc: dict, obj: dict, port_names: list | None = None) -> Failure | None:
    """L166 (7)-(11) on the DRAFT design materials (D-005); results are provisional."""
    if SIM is None:
        raise Blocked(RUNTIME_NEXT + f" [D-005 materials: {SIM_UNAVAILABLE}]")
    failure, details = simulator_stages.run_response(SIM, obj["driver"]["source"], obj["checker"]["source"],
                                                     port_names)
    PROVISIONAL[id(desc)] = details
    return failure


def response_stages(desc: dict, inp: dict, validator) -> Failure | None:
    """Evaluation order (1)-(6) for a response input; None if all of them pass."""
    raw: bytes | None = None
    if "raw_response_utf8" in inp:
        raw = inp["raw_response_utf8"].encode("utf-8")
    elif "raw_response_base64" in inp:
        raw = base64.b64decode(inp["raw_response_base64"], validate=True)
    if raw is not None:
        envelope = parse_envelope(raw, inp.get("provider_finish_reason"))
        if isinstance(envelope, Failure):
            return envelope
        obj = envelope.obj
    else:
        # A-002 (owner decision): skip envelope decoding only.
        obj = inp["response_object"]
    # PARSE_SCHEMA part 1b; manifest clause_ids from the descriptor (A-005).
    checked = validate_schema(validator, obj)
    if isinstance(checked, ValidatedResponse):
        checked = validate_clause_ids(checked, desc["manifest_clause_ids"])
    if isinstance(checked, Failure):
        return checked
    return source_stages(obj["driver"]["source"], obj["checker"]["source"])


# L166 (7)-(11) are implemented (src/openvef/simulation.py, sandbox/sim.py; D-003 toolchain)
# but need inputs that are owner-written or TO FREEZE and absent from the pack.
MISSING_DESIGN_MATERIALS = ("FIFO RTL and null netlist; port manifest with widths; reset sequence; legal-input "
                            "predicate (owner-written FIFO specification, Scope); cycle cap, safe-idle vector and "
                            "watchdog formula (TO FREEZE, Protocol L229); observation mask (owner-written); "
                            "checker trace schema and metadata (TO FREEZE, L543)")
RUNTIME_NEXT = ("runtime import, factory and signature checks passed in the sandbox; L166 (7)-(11) simulator "
                "stages are built but blocked on design materials absent from the pack: " + MISSING_DESIGN_MATERIALS)


def run_syntax_error_vector(source_file: str, syntax_error: dict) -> Failure:
    """Apply the column rule to a given SyntaxError position (A-012, Protocol L177)."""
    lineno = syntax_error.get("lineno")
    if (source_file not in FILE_ORDER or set(syntax_error) - {"lineno", "offset"}
            or not isinstance(lineno, int) or isinstance(lineno, bool) or lineno < 1):
        raise Blocked("syntax_error vector outside the shape the column rule covers")
    offset = syntax_error.get("offset")
    if offset is not None and (not isinstance(offset, int) or isinstance(offset, bool)):
        raise Blocked("syntax_error offset is neither an integer nor null")
    return replace(syntax_reject(source_file, lineno, offset), disposition="CONTROL_EXPECTATION")


def two_runs(runs) -> tuple:
    if not isinstance(runs, list) or len(runs) != 2:
        raise Blocked("checker adjudication needs exactly two run records (L166 steps (9)-(10))")
    return outcome_from_record(runs[0]), outcome_from_record(runs[1])


def control_record(failure: Failure, **properties) -> dict:
    """A control-vector record: the stage-map fields plus named computed properties (A-032)."""
    record = {"disposition": failure.disposition, "stage_id": failure.stage_id, "error_class": failure.error_class}
    if failure.diagnostic is not None:
        record["diagnostic"] = failure.diagnostic
    record.update(properties)
    return record


def run_truncation_primitive(inp: dict) -> dict:
    """Feedback serialization step (2) alone (Protocol L168); grammar bypassed by scope."""
    raw = inp["raw_diagnostic"]
    if not (inp.get("truncate_before_json_escape") is True and inp.get("truncate_on_utf8_boundary") is True):
        raise Blocked("truncation options differ from the Protocol L168 rule")
    if inp.get("raw_diagnostic_utf8_bytes") != len(raw.encode("utf-8")):
        raise Blocked("raw_diagnostic_utf8_bytes does not match the raw diagnostic")
    out = truncate(raw, inp["byte_cap"], inp["marker"])
    data = out.encode("utf-8")
    try:
        data.decode("utf-8", errors="strict")
        valid = True
    except UnicodeDecodeError:
        valid = False
    failure = Failure("FEEDBACK_SERIALIZER", "TRUNCATION", None, "CONTROL_EXPECTATION")
    return control_record(failure, contains_marker=out.endswith(inp["marker"]), valid_utf8=valid,
                          output_diagnostic_bytes=len(data), marker_utf8_bytes=len(inp["marker"].encode("utf-8")))


def run_json_primitive(inp: dict) -> dict:
    """Feedback serialization step (3) alone (Protocol L168); grammar bypassed by scope."""
    spec = {"encoding": "UTF-8", "ensure_ascii": False, "indent": 2, "line_endings": "LF", "terminal_newline": True}
    if any(inp.get(k) != v for k, v in spec.items()):
        raise Blocked("serialization options differ from the Protocol L168 rule")
    obj = inp["feedback_object"]
    if list(obj) != ["stage_id", "error_class", "diagnostic"]:
        raise Blocked("feedback object keys differ from the L168 three-key order")
    data = serialize(obj["stage_id"], obj["error_class"], obj["diagnostic"])
    failure = Failure("FEEDBACK_SERIALIZER", "JSON_SERIALIZATION", None, "CONTROL_EXPECTATION")
    return control_record(failure, diagnostic_utf8=data.decode("utf-8"),
                          diagnostic_sha256=hashlib.sha256(data).hexdigest(), diagnostic_bytes=len(data))


RESPONSE_KEYS = ({"raw_response_utf8"}, {"raw_response_utf8", "provider_finish_reason"}, {"raw_response_base64"},
                 {"response_object"})
HALT_RECOVERY_KEYS = {"design_id", "recovery_cycles_used", "first_halt_signature", "second_halt_signature",
                      "scheduled_slots"}
OPERATIONAL_RECOVERY_KEYS = {"design_id", "slots", "evaluator_repair_attempt", "same_artifacts_for_all_slots",
                             "new_generation_calls", "required_action", "recovery_mode", "frozen_evaluator_hashes_unchanged",
                             "same_artifact_bytes", "same_slot_seeds", "f16_required", "author_visible_materials_changed",
                             "pre_halt_scored_slots", "scheduled_slots", "halt_signature"}


def dispatch(desc: dict, validator) -> Failure | dict | None:
    """The outcome for one descriptor: a Failure, a full record, or None (ACCEPT).

    The code path is chosen from the input's key set only (CLAUDE.md rule 4).
    """
    inp = desc["input"]
    keys = set(inp)

    if keys in RESPONSE_KEYS:
        result = response_stages(desc, inp, validator)
        if result is None:
            return sim_stages(desc, response_object(inp))
        return result
    if keys == {"driver_source", "checker_source"}:  # A-012 source pair
        result = source_stages(inp["driver_source"], inp["checker_source"])
        if result is None:
            raise Blocked(RUNTIME_NEXT)
        return result
    if keys == {"source_file", "syntax_error"}:  # A-012 column-rule vector
        return run_syntax_error_vector(inp["source_file"], inp["syntax_error"])

    # Composite inputs (A-028): run every implemented response stage first; the supplied
    # later-stage outcome stands in for stages that need the simulator.
    if keys == {"null_runs", "response_object"}:
        result = response_stages(desc, {"response_object": inp["response_object"]}, validator)
        if result is not None:
            return result
        return adjudicate_checker(*two_runs(inp["null_runs"]))
    if keys == {"runtime_pair", "response_object"}:
        result = response_stages(desc, {"response_object": inp["response_object"]}, validator)
        if result is not None:
            return result
        pair = inp["runtime_pair"]
        if pair.get("before_first_raw_output_divergence") is True and pair.get("next_input_schedules_equal") is False:
            return paired_run_failure(None, 0)
        raise Blocked("paired runs agree; later stages need a null trace: " + MISSING_DESIGN_MATERIALS)

    if keys == {"port_manifest", "response_object"}:
        result = response_stages(desc, {"response_object": inp["response_object"]}, validator)
        if result is not None:
            return result
        manifest = inp["port_manifest"]
        if set(manifest) != {"input_ports"} or not isinstance(manifest["input_ports"], list):
            raise Blocked("port manifest outside the names-only shape A-044 covers")
        return sim_stages(desc, inp["response_object"], manifest["input_ports"])
    if keys == {"events"}:  # A-025
        return first_event(inp["events"])
    if keys == {"lifecycle", "event", "slots", "evaluator_repair_attempt"} and inp["lifecycle"] == "MID_RUN":
        return first_event([inp["event"]])
    if keys == {"checker_runs"}:  # A-026
        return adjudicate_checker(*two_runs(inp["checker_runs"]))
    if keys == {"paired_runs"}:
        runs = inp["paired_runs"]
        result = paired_run_failure(runs["first_raw_output_divergence_cycle"], runs["first_next_input_divergence_cycle"])
        if result is None:
            raise Blocked("no paired-run failure; later stages need the simulator")
        return result
    if keys == {"design_preflight"}:
        if inp["design_preflight"].get("rtl_null_masked_divergence") is True:
            return RTL_NULL_CONTROL_FAILURE
        raise Blocked("design preflight passed; slot stages need the simulator")
    if keys == {"runtime_signature"}:
        sig = inp["runtime_signature"]
        result = runtime_signature_failure(sig["file"], sig["symbol"], sig["actual"], sig["expected"])
        if result is None:
            raise Blocked("runtime signature matches; later stages need the sandbox")
        return result
    if keys == {"driver_return", "expected_keys"}:
        try:
            result = validate_vector(inp["driver_return"], inp["expected_keys"])
        except NotDetermined as exc:
            raise Blocked(f"A-027: {exc}") from exc
        if result is None:
            raise Blocked("vector valid")
        return result
    if keys == {"driver_return", "legal_input_predicate"}:
        raise Blocked("A-038 (revisited): the descriptor's prose predicate is not the design's executable "
                      "FIFO-042 (they disagree when rd_en = 1 at full), executing the prose would need a "
                      "predicate language File 30 L83 (e) does not define, and no port set is supplied for "
                      "checks (a)-(d), which precede (e)")

    if keys == HALT_RECOVERY_KEYS:  # ledger, Protocol L185
        return halt_after_recovery(HaltSignature.given(inp["first_halt_signature"]),
                                   HaltSignature.given(inp["second_halt_signature"]), inp["recovery_cycles_used"])
    if keys == OPERATIONAL_RECOVERY_KEYS and inp["recovery_mode"] == "OPERATIONAL_RECOVERY":  # ledger, L183-L185
        rec = operational_recovery(
            scheduled_slots=inp["scheduled_slots"], frozen_evaluator_hashes_unchanged=inp["frozen_evaluator_hashes_unchanged"],
            same_artifact_bytes=inp["same_artifact_bytes"], same_slot_seeds=inp["same_slot_seeds"],
            author_visible_materials_changed=inp["author_visible_materials_changed"],
            new_generation_calls=inp["new_generation_calls"], f16_required=inp["f16_required"])
        if rec is None:
            raise Blocked("operational-recovery conditions not met; evaluator-revision path not implemented")
        return control_record(rec.failure, discard_pre_halt_scores=rec.discard_pre_halt_scores,
                              rerun_slots=rec.rerun_slots, reuse_same_artifact_bytes=rec.reuse_same_artifact_bytes,
                              new_confirmatory_generation_calls=rec.new_confirmatory_generation_calls)
    if keys == {"change_class"}:  # ledger, Protocol L175-L176, L181-L185 (A-033 revised)
        try:
            record, missing = lifecycle_expectation(inp["change_class"])
        except ValueError as exc:
            raise Blocked(str(exc)) from exc
        if missing:
            raise Blocked("A-033: no supporting Protocol sentence for " +
                          "; ".join(f"{name}: {reason}" for name, reason in missing.items()))
        return record

    if keys == {"diagnostic", "allowed_diagnostics"}:  # serializer step (1), A-029
        result = check_diagnostic(inp["diagnostic"], inp["allowed_diagnostics"])
        if result is None:
            raise Blocked("diagnostic accepted; nothing further to compare")
        return result
    if inp.get("test_scope") == "TRUNCATION_PRIMITIVE_ONLY_GRAMMAR_BYPASSED":
        return run_truncation_primitive(inp)
    if inp.get("test_scope") == "JSON_ESCAPING_PRIMITIVE_ONLY_GRAMMAR_BYPASSED":
        return run_json_primitive(inp)

    if keys == {"payload", "reserved_headings"}:
        result = check_reserved_heading_lines(inp["payload"], inp["reserved_headings"])
    elif keys == {"rendered"}:
        result = check_unresolved_placeholders(inp["rendered"])
    elif {"visible_payload", "manifest_clause_ids", "clause_id_regex"} <= keys <= {
            "visible_payload", "manifest_clause_ids", "clause_id_regex", "clause_id_search_regex",
            "clause_id_near_match_regex"}:
        result = check_visible_clause_ids(
            inp["visible_payload"], inp["manifest_clause_ids"], inp["clause_id_regex"],
            inp.get("clause_id_search_regex", SEARCH_REGEX_DEFAULT),
            inp.get("clause_id_near_match_regex", NEAR_MATCH_REGEX_DEFAULT))
    else:
        raise Blocked(f"input shape {sorted(keys)} has no implemented adapter")
    if result is None:
        raise Blocked("packet check passed; nothing further to compare")
    return result


def execute(desc: dict, validator) -> tuple[str, dict | None, str]:
    """Return (status, actual, note)."""
    try:
        outcome = dispatch(desc, validator)
    except (Blocked, NotDetermined) as exc:
        return "NOT_IMPLEMENTED", None, str(exc)
    except EventError as exc:
        return "NOT_IMPLEMENTED", None, f"input outside the adapter vocabulary: {exc}"
    if outcome is None:
        return "EXECUTED", dict(ACCEPT), ""
    if isinstance(outcome, Failure):
        return "EXECUTED", failure_record(outcome), ""
    return "EXECUTED", outcome, ""


def installed_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def git_commit() -> str:
    if broker_mode():  # D-002a: the host broker reads git; the runner container has no git
        return os.environ["OPENVEF_GIT_COMMIT"]
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", "src", "runner", "sandbox",
                                "design", "docs/fifo-spec-v0.2.md"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("+UNCOMMITTED_CHANGES" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "NO_GIT_COMMIT"


def utc_stamp() -> str:
    """ISO 8601 UTC time with milliseconds, for each run.log fixture line (§3 item 6)."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> int:
    root, evidence_root, run_class = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if broker_mode():  # D-002a: the broker created and mounted the (empty) run directory
        started = os.environ["OPENVEF_RUN_STARTED"]
        out_dir = evidence_root
        if any(out_dir.iterdir()):
            raise IntegrityError("evidence directory is not empty")
    else:
        started = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = evidence_root / f"run-{started}"
        out_dir.mkdir(parents=True, exist_ok=False)

    source_files = sorted([*(REPO / "src").rglob("*.py"), *(REPO / "runner").rglob("*.py"),
                           *(REPO / "sandbox").glob("*"), *(p for p in (REPO / "design").rglob("*") if p.is_file())])
    global SANDBOX
    try:
        SANDBOX = ensure_image()
    except (SandboxUnavailable, FileNotFoundError) as exc:
        SANDBOX = None
        print(f"sandbox unavailable: {exc}", file=sys.stderr)
    if broker_mode() and SANDBOX is None:
        raise SystemExit("D-002a: the runner container must have the sandbox identity")
    py_sha = sha256_file(Path(os.path.realpath(sys.executable)))
    pinned = broker_mode() and sys.version == PINNED_PYTHON_VERSION and py_sha == PINNED_PYTHON_SHA256
    meta = {
        "run_started_utc": started,
        "run_class": run_class,
        "interpreter_status": ("PINNED (D-002a: runner and artifacts in the pinned image)" if pinned else
                               "NOT_PINNED: development run, not F18 evidence (D-002a)"),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "python_executable_sha256": py_sha,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "fixture_index_sha256": INDEX_SHA256,
        "response_schema_sha256": SCHEMA_SHA256,
        "distributions": {name: installed_version(name) for name in PINNED_DISTRIBUTIONS},
        "git_commit": git_commit(),
        "source_sha256": {str(p.relative_to(REPO)): sha256_file(p) for p in source_files},
        "command": [sys.executable, *sys.argv],
        "sandbox": SANDBOX,
    }

    global SIM, SIM_UNAVAILABLE
    if SANDBOX is not None:
        try:
            SIM = simulator_stages.prepare(REPO, DESIGN_MATERIALS_FILE)
            meta["design_materials"] = SIM["record"]
        except (OSError, KeyError, ValueError, SimulationError) as exc:
            SIM, SIM_UNAVAILABLE = None, f"{type(exc).__name__}: {exc}"
            meta["design_materials"] = {"unavailable": SIM_UNAVAILABLE}
    provisional_ids: list = []
    counts = {"PASS": 0, "FAIL": 0, "NOT_IMPLEMENTED": 0, "ERROR": 0}
    with open(out_dir / "results.jsonl", "w", encoding="utf-8") as res, open(out_dir / "run.log", "w", encoding="utf-8") as log:
        log.write(json.dumps(meta, indent=2) + "\n")
        fixtures = load_index(root)  # IntegrityError aborts the whole run
        validator = load_schema_validator(root)
        for entry in fixtures:
            desc = load_descriptor(root, entry)
            expected = desc["expected"]
            try:
                status, actual, note = execute(desc, validator)
            except Exception as exc:  # recorded, never hidden
                status, actual, note = "ERROR", None, f"{type(exc).__name__}: {exc}"
            if status == "EXECUTED":
                # Standard expectations compare the four fields; a control-vector
                # expectation compares the whole object exactly (A-032).
                status = "PASS" if actual == expected else "FAIL"
            counts[status] += 1
            rec = {"fixture_id": entry["fixture_id"], "descriptor_sha256": entry["sha256"], "status": status,
                   "expected": expected, "actual": actual, "note": note}
            sim_details = PROVISIONAL.pop(id(desc), None)
            if sim_details is not None and SIM["provisional"]:  # reached L166 (7)-(11); items still open
                rec["provisional"] = {"reason": "depends on design items not yet frozen or signed: "
                                                + "; ".join(SIM["provisional"]),
                                      "simulator": sim_details}
                provisional_ids.append(entry["fixture_id"])
            res.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            log.write(f"{utc_stamp()} {entry['fixture_id']}: {status} {note}\n")
            log.flush()

    meta["run_finished_utc"] = utc_stamp()
    summary = {**meta, "counts": counts, "total": sum(counts.values()),
               "provisional_fixtures": provisional_ids,
               "results_sha256": sha256_file(out_dir / "results.jsonl")}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "run": f"run-{started}", "counts": counts}), file=sys.stderr)
    return 0 if counts["FAIL"] == 0 and counts["ERROR"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
