"""Unit tests for stage-map rows, serializer, assembler and ledger (not F18 fixtures)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef.assembler import (check_reserved_heading_lines, check_unresolved_placeholders,  # noqa: E402
                               check_visible_clause_ids)
from openvef.ledger import HaltSignature, SignatureDomainError, halt_after_recovery, operational_recovery  # noqa: E402
from openvef.serializer import MARKER, check_diagnostic, feedback_bytes, in_grammar, serialize, truncate  # noqa: E402
from openvef.stage_map import (CHECKER_TIMEOUT, CheckerOutcome, EventError, NotDetermined,  # noqa: E402
                               adjudicate_checker, checker_runtime_error, classify_return, exception_class,
                               first_event, outcome_from_record, paired_run_failure, validate_vector)


class EventPrecedenceTests(unittest.TestCase):
    def diag(self, *events):
        return first_event(list(events)).diagnostic

    def test_evaluation_step_decides(self):
        self.assertEqual(self.diag({"kind": "driver_watchdog"}, {"kind": "compile_error", "file": "checker.py", "line": 3}),
                         "COMPILE_ERROR|file=checker.py|line=3")
        self.assertEqual(self.diag({"kind": "compile_error", "file": "checker.py", "line": 1},
                                   {"kind": "compile_error", "file": "driver.py", "line": 9}),
                         "COMPILE_ERROR|file=driver.py|line=9")

    def test_within_a_cycle_exception_vector_watchdog(self):
        e = {"kind": "driver_runtime", "phase": "step", "exception_class": "ValueError"}
        v = {"kind": "driver_vector", "reason": "WRONG_WIDTH"}
        w = {"kind": "driver_watchdog"}
        self.assertEqual(self.diag(w, v, e), "RUNTIME_EXCEPTION|file=driver.py|phase=step|class=ValueError")
        self.assertEqual(self.diag(w, v), "DRIVER_VECTOR_INVALID|reason=WRONG_WIDTH")

    def test_dispositions(self):
        f = first_event([{"kind": "trace_integrity", "reason": "ROW_ALIGNMENT"}])
        self.assertEqual((f.stage_id, f.disposition), ("DESIGN_HALT", "DESIGN_HALT_NO_SLOT_SCORED"))
        f = first_event([{"kind": "simulator_error", "target": "rtl", "exception_class": "bad name!"}])
        self.assertEqual(f.diagnostic, "SIMULATOR_ERROR|target=rtl|class=Exception")

    def test_unknown_or_out_of_domain(self):
        for events in ([{"kind": "mystery"}], [{"kind": "driver_vector", "reason": "NOPE"}],
                       [{"kind": "compile_error", "file": "x.py", "line": 1}], []):
            with self.subTest(events=events), self.assertRaises(EventError):
                first_event(events)

    def test_exception_class_fallback(self):
        self.assertEqual(exception_class("KeyError"), "KeyError")
        self.assertEqual(exception_class("module.Error"), "Exception")


class PairedRunTests(unittest.TestCase):
    def test_rule(self):
        self.assertIsNotNone(paired_run_failure(None, 4))
        self.assertIsNotNone(paired_run_failure(5, 4))
        self.assertIsNone(paired_run_failure(4, 4))  # raw outputs compared before the next-input decision
        self.assertIsNone(paired_run_failure(3, None))


class VectorTests(unittest.TestCase):
    ports = ("data", "valid")
    widths = {"data": 2, "valid": 1}

    def reason(self, value, legal=lambda v: True):
        r = validate_vector(value, self.ports, self.widths, legal)
        return None if r is None else r.diagnostic.split("=")[1]

    def test_order(self):
        self.assertIsNone(self.reason("COMPLETE"))
        self.assertEqual(self.reason("DONE"), "RETURN_TYPE")
        self.assertEqual(self.reason({"data": "00"}), "MISSING_KEYS")
        self.assertEqual(self.reason({"data": "00", "extra": "1"}), "MISSING_KEYS")
        self.assertEqual(self.reason({"data": "00", "valid": "1", "x": "0"}), "EXTRA_KEYS")
        self.assertEqual(self.reason({"data": 0, "valid": "1"}), "NON_STRING_VALUE")
        self.assertEqual(self.reason({"data": "0", "valid": "1"}), "WRONG_WIDTH")
        self.assertEqual(self.reason({"data": "0X", "valid": "1"}), "ILLEGAL_SYMBOL")
        self.assertEqual(self.reason({"data": "01", "valid": "1"}, legal=lambda v: False), "ILLEGAL_PROTOCOL_STATE")
        self.assertIsNone(self.reason({"data": "01", "valid": "1"}))

    def test_missing_parameters_are_not_determined(self):
        with self.assertRaises(NotDetermined):
            validate_vector({"data": "01", "valid": "1"}, self.ports)
        with self.assertRaises(NotDetermined):
            validate_vector({"data": "01", "valid": "1"}, self.ports, self.widths)


class CheckerTests(unittest.TestCase):
    def test_return_classification_order(self):
        self.assertEqual(classify_return("PASS").error[1], "CHECKER_RETURN_INVALID|reason=NON_DICTIONARY")
        self.assertEqual(classify_return({"verdict": "PASS", "extra": 1}).error[1],
                         "CHECKER_RETURN_INVALID|reason=MISSING_DIAGNOSTICS")
        self.assertEqual(classify_return({"verdict": "PASS", "diagnostics": [], "x": 1}).error[1],
                         "CHECKER_RETURN_INVALID|reason=TOP_LEVEL_KEYS")
        self.assertEqual(classify_return({"verdict": "pass", "diagnostics": 5}).error[1],
                         "CHECKER_RETURN_INVALID|reason=INVALID_VERDICT")
        self.assertEqual(classify_return({"verdict": "PASS", "diagnostics": 5}).error[1],
                         "CHECKER_RETURN_INVALID|reason=DIAGNOSTICS_NOT_LIST")
        ok = classify_return({"verdict": "FAIL", "diagnostics": [{"code": "C", "message": "m", "cycle": 3, "clause_id": None},
                                                                 {"code": "C", "message": "m", "cycle": True, "clause_id": None}]})
        self.assertEqual((ok.verdict, ok.error, ok.malformed_items), ("FAIL", None, 1))

    def test_adjudication(self):
        p, f = CheckerOutcome("PASS", None), CheckerOutcome("FAIL", None)
        self.assertIsNone(adjudicate_checker(p, p))
        self.assertEqual(adjudicate_checker(f, f).stage_id, "CHECKER_NULL_REJECT")
        self.assertEqual(adjudicate_checker(p, f).error_class, "CHECKER_NONDETERMINISM")
        self.assertEqual(adjudicate_checker(CHECKER_TIMEOUT, CHECKER_TIMEOUT).diagnostic, "CHECKER_TIMEOUT|phase=null_check")
        self.assertEqual(adjudicate_checker(checker_runtime_error("KeyError"), checker_runtime_error("ValueError")).stage_id,
                         "TERMINAL")
        self.assertEqual(adjudicate_checker(CHECKER_TIMEOUT, p).stage_id, "TERMINAL")
        w = adjudicate_checker(CheckerOutcome("PASS", None, 1), p)
        self.assertEqual((w.disposition, w.stage_id, w.diagnostic), ("ACCEPT_WITH_WARNING", None, "DIAGNOSTIC_FORMAT_WARNING"))
        self.assertEqual(adjudicate_checker(CheckerOutcome("FAIL", None, 1), f).stage_id, "CHECKER_NULL_REJECT")

    def test_run_records(self):
        self.assertEqual(outcome_from_record({"timeout": True}), CHECKER_TIMEOUT)
        with self.assertRaises(EventError):
            outcome_from_record({"verdict": "MAYBE"})


class SerializerTests(unittest.TestCase):
    def test_grammar(self):
        for d in ("SCHEMA_REJECT|pointer=/", "SCHEMA_REJECT|pointer=/assumptions/0/clause_id", "OUTPUT_TRUNCATED",
                  "ENTRY_POINT_REJECT|file=driver.py|symbol=helper.Nested|reason=NESTED_CLASS_FORBIDDEN",
                  "GLOBAL_RANDOM_USE|name=random.randint", "The checker returned FAIL on a legal null-netlist trace."):
            with self.subTest(d=d):
                self.assertTrue(in_grammar(d))
        for d in ("COMPILE_ERROR|path=/tmp/a.py", "COMPILE_ERROR|file=driver.py|line=0", "GLOBAL_RANDOM_USE|name=random.Random",
                  "SOURCE_EMPTY|file=driver.py|extra=1", "CHECKER_RUNTIME_ERROR|class=a.b", "PROHIBITED_BUILTIN|name=print",
                  "SCHEMA_REJECT|pointer=/a|b"):
            with self.subTest(d=d):
                self.assertFalse(in_grammar(d))

    def test_emitted_set(self):
        self.assertIsNone(check_diagnostic("OUTPUT_TRUNCATED"))
        self.assertIsNotNone(check_diagnostic("OUTPUT_TRUNCATED", ["SOURCE_EMPTY|file=driver.py"]))

    def test_truncation_on_code_point_boundary(self):
        self.assertEqual(truncate("abc"), "abc")
        out = truncate("é" * 1100)  # 2,200 bytes
        data = out.encode("utf-8")
        self.assertTrue(out.endswith(MARKER))
        self.assertLessEqual(len(data), 2048)
        self.assertEqual(len(data), 2034 + 14)
        out = truncate("x" + "é" * 1100)
        self.assertEqual(len(out.encode("utf-8")), 2047)

    def test_serialize_format(self):
        data = serialize("S", "E", 'a"é\n')
        self.assertEqual(data, b'{\n  "stage_id": "S",\n  "error_class": "E",\n  "diagnostic": "a\\"\xc3\xa9\\n"\n}\n')
        self.assertEqual(list(json.loads(data)), ["stage_id", "error_class", "diagnostic"])

    def test_feedback_bytes_rejects_non_normative(self):
        from openvef.envelope import Failure
        self.assertIsNone(feedback_bytes(Failure("COMPILE_DRIVER", "COMPILE_ERROR", "COMPILE_ERROR|path=x")))
        self.assertIsNotNone(feedback_bytes(Failure("COMPILE_DRIVER", "COMPILE_ERROR", "COMPILE_ERROR|file=driver.py|line=2")))


class AssemblerTests(unittest.TestCase):
    def test_reserved_heading(self):
        self.assertIsNotNone(check_reserved_heading_lines("a\r\n[H]\r\nb", ["[H]"]))
        self.assertIsNone(check_reserved_heading_lines("a [H]\n[H] b", ["[H]"]))

    def test_placeholder(self):
        self.assertIsNotNone(check_unresolved_placeholders("x {{A_1}} y"))
        self.assertIsNone(check_unresolved_placeholders("x {{a}} {A} y"))

    def test_clause_ids(self):
        self.assertIsNone(check_visible_clause_ids("FIFO-001 and FIFO-002.", ["FIFO-001", "FIFO-002"]))
        self.assertEqual(check_visible_clause_ids("FIFO-001", ["FIFO-001", "FIFO-002"]).diagnostic,
                         "F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH")
        self.assertEqual(check_visible_clause_ids("FIFO-001 fifo-001", ["FIFO-001"]).diagnostic,
                         "F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN")
        # Near-match before set equality (A-030).
        self.assertEqual(check_visible_clause_ids("FIFO-1", ["FIFO-001"]).diagnostic,
                         "F18_REJECT|reason=MALFORMED_CLAUSE_ID_TOKEN")
        # Seven letters: no 2-6 letter run can start at a token boundary, so no candidate.
        self.assertIsNone(check_visible_clause_ids("ABCDEFG-001; FIFO-001", ["FIFO-001"]))
        # Five letters is a valid ID under File 31 §8, so it joins the visible set.
        self.assertEqual(check_visible_clause_ids("XFIFO-001; FIFO-001", ["FIFO-001"]).diagnostic,
                         "F18_REJECT|reason=VISIBLE_CLAUSE_ID_SET_MISMATCH")


class LedgerTests(unittest.TestCase):
    def test_build_enforces_domains(self):
        self.assertEqual(HaltSignature.build("FIFO", "TRACE_INTEGRITY_FAILURE", trace_reason="ROW_ALIGNMENT"),
                         ("FIFO", "TRACE_INTEGRITY_FAILURE", "TRACE_ALIGNMENT_CHECKER", "NONE", "TRACE_INTEGRITY_FAILURE"))
        self.assertEqual(HaltSignature.build("UART", "SIMULATOR_ERROR", exception_class="OSError").evaluator_component,
                         "SIMULATOR")
        for args in (("SPI", "SIMULATOR_ERROR"), ("FIFO", "SIMULATOR_ERROR")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                HaltSignature.build(*args)

    def test_given_enforces_every_domain(self):  # D-012
        sim = HaltSignature.build("FIFO", "SIMULATOR_ERROR", exception_class="OSError")._asdict()
        trace = HaltSignature.build("UART", "TRACE_INTEGRITY_FAILURE", trace_reason="ROW_ALIGNMENT")._asdict()
        rtl = HaltSignature.build("UART", "RTL_NULL_CONTROL_FAILURE")._asdict()
        for good in (sim, trace, rtl):
            self.assertEqual(HaltSignature.given(good)._asdict(), good)
        for base, change in ((sim, {"design_id": "SPI"}), (sim, {"halt_code": "OTHER"}),
                             (sim, {"evaluator_component": "simulator"}), (sim, {"evaluator_component": "RECORDER"}),
                             (sim, {"stable_error_class": "a b"}), (sim, {"stable_error_class": None}),
                             (sim, {"stable_diagnostic_code": "X"}), (trace, {"stable_error_class": "Fault"}),
                             (trace, {"evaluator_component": "SIMULATOR"}), (rtl, {"stable_error_class": "OSError"}),
                             (rtl, {"evaluator_component": "RECORDER"})):
            with self.subTest(change=change), self.assertRaises(SignatureDomainError):
                HaltSignature.given({**base, **change})
        with self.assertRaises(SignatureDomainError):
            HaltSignature.given({k: v for k, v in sim.items() if k != "design_id"})

    def test_recurrence(self):
        a = HaltSignature.build("FIFO", "SIMULATOR_ERROR", exception_class="RuntimeError")
        b = HaltSignature.build("FIFO", "RTL_NULL_CONTROL_FAILURE")
        self.assertEqual(halt_after_recovery(a, a, 1).diagnostic, "DESIGN_HALT_REPEATED|reason=EVALUATOR_FAILURE_REPRODUCED")
        r = halt_after_recovery(a, b, 1)
        self.assertEqual((r.diagnostic, r.disposition),
                         ("DESIGN_HALT_REPEATED|reason=SECOND_HALT_AFTER_RECOVERY", "DESIGN_ABORTED_NO_SLOTS_SCORED"))
        with self.assertRaises(ValueError):
            halt_after_recovery(a, b, 0)

    def test_operational_recovery(self):
        ok = dict(scheduled_slots=10, frozen_evaluator_hashes_unchanged=True, same_artifact_bytes=True, same_slot_seeds=True,
                  author_visible_materials_changed=False, new_generation_calls=0, f16_required=False)
        self.assertEqual(operational_recovery(**ok).rerun_slots, 10)
        for key, bad in (("frozen_evaluator_hashes_unchanged", False), ("new_generation_calls", 1), ("f16_required", True)):
            with self.subTest(key=key):
                self.assertIsNone(operational_recovery(**{**ok, key: bad}))


if __name__ == "__main__":
    unittest.main()
