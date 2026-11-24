"""DRAFT pack proposal (proposals/v1.3.7): tokens match the descriptors; the proposed M27
passes checks (a)-(d) and fails (e). Not an F18 fixture run and not evidence."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.stage_map import validate_vector  # noqa: E402

PROPOSAL = REPO / "proposals/v1.3.7/PROPOSED-CORRECTIONS-DRAFT.md"
FIXTURES = REPO / "baseline/OpenVEF_Planning_v1_3_6/41_F18_Fixture_Inputs"


@unittest.skipUnless(PROPOSAL.exists(), "proposal not present (audit bundle)")
class ProposalTests(unittest.TestCase):
    def test_marked_draft(self):
        self.assertIn("**DRAFT. Requires a new independent document audit.**", PROPOSAL.read_text("utf-8"))

    def test_tokens_equal_the_descriptor_strings(self):
        text = PROPOSAL.read_text("utf-8")
        for fid, keys in {"M48": ["error_class", "rerun_scope_rule"], "M50": ["error_class", "affected_slots"],
                          "M54": ["stable_error_class_rule", "stable_diagnostic_code_rule"],
                          "M58": ["error_class", "affected_scope", "unaffected_design_scope"]}.items():
            desc = json.loads((FIXTURES / f"{fid}.json").read_text("utf-8"))
            for key in keys:
                self.assertIn(f"`{desc['expected'][key]}`", text, (fid, key))
            self.assertIn(f"`{desc['input']['change_class']}`", text)

    def test_proposed_m27(self):
        new = json.loads((PROPOSAL.parent / "fixtures/M27.json").read_text("utf-8"))
        old = json.loads((FIXTURES / "M27.json").read_text("utf-8"))
        self.assertEqual(new["expected"], old["expected"])
        inp = new["input"]
        ns: dict = {}
        exec(inp["legal_input_predicate"]["source"], ns)  # repository text, not model output
        legal = ns[inp["legal_input_predicate"]["function"]]
        widths = inp["input_port_widths"]
        check = lambda v: validate_vector(v, widths, widths, lambda x: legal(x, inp["sampled_outputs"]))
        failure = check(inp["driver_return"])
        self.assertEqual({k: new["expected"][k] for k in ("stage_id", "error_class", "diagnostic")},
                         {"stage_id": failure.stage_id, "error_class": failure.error_class,
                          "diagnostic": failure.diagnostic})
        self.assertIsNone(check(dict(inp["driver_return"], rd_en="1")))  # legal at full (FIFO-030)
        spec = (REPO / "docs/fifo-spec-v0.2.md").read_text("utf-8")
        self.assertIn(inp["legal_input_predicate"]["source"], spec)


if __name__ == "__main__":
    unittest.main()
