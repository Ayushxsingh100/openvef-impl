"""D-024 Phase A: proposals/v1.3.7/pack/ is v1.3.6 with only corrections C1-C10 applied (v1.3.7 CANDIDATE,
not audited). Checks the copy, not any implementation: it is rebuilt byte for byte from the read-only baseline;
only the listed files differ; no line of a changed file moves; checksums and the fixture index agree; the
corrected M27 reaches check (e). Not an F18 run and not evidence."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
HERE = REPO / "proposals/v1.3.7"
PACK = HERE / "pack"
BASE = REPO / "baseline/OpenVEF_Planning_v1_3_6"

from openvef.stage_map import validate_vector  # noqa: E402

CHANGED = {"02_OpenVEF_Experimental_Protocol_v1.3.6.md", "30_Response_Parser_and_Execution_Contract_v1.3.6.md",
           "36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md",
           "10_LLM_Era_Hardware_Verification_Literature_Review.md", "11_Comparative_Research_Matrix.md",
           "27_SHA256SUMS.txt", "41_F18_Fixture_Inputs/fixture-index.json"} | {
    f"41_F18_Fixture_Inputs/{n}.json" for n in ("M27", "M41", "M42", "M47")}
ADDED = {"CHANGELOG-v1.3.7-candidate.md", "CANDIDATE-LABEL.md", "SHA256SUMS-v1.3.7-candidate.txt"}


def files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def builder():
    spec = importlib.util.spec_from_file_location("build_candidate", HERE / "build_candidate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(PACK.exists(), "candidate pack not present (audit bundle)")
class CandidatePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack, cls.base = files(PACK), files(BASE)

    def test_rebuild_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            builder().build(Path(tmp) / "pack")
            self.assertEqual(files(Path(tmp) / "pack"), self.pack)

    def test_only_the_listed_files_differ(self):
        self.assertEqual(set(self.pack) - set(self.base), ADDED)
        self.assertEqual(set(self.base) - set(self.pack), set())
        self.assertEqual({f for f in self.base if self.base[f] != self.pack[f]}, CHANGED)

    def test_no_line_moves_and_only_edited_lines_change(self):
        mod = builder()
        edited: dict[str, set[int]] = {}
        for _, _, _, rel, n, _, _ in mod.EDITS:
            edited.setdefault(rel, set()).add(n)
        for rel in edited:
            old = self.base[rel].decode("utf-8").split("\n")
            new = self.pack[rel].decode("utf-8").split("\n")
            with self.subTest(file=rel):
                if rel.endswith(".md"):
                    self.assertEqual("\n".join(new[len(old) - 1:]), mod.TRAILER)  # trailer only after the last line
                differ = {i + 1 for i in range(len(old) - 1) if old[i] != new[i]}
                label_line = {mod.VERSION_LINES[rel]} if rel in mod.VERSION_LINES else set()
                self.assertEqual(differ, edited[rel] | label_line)

    def test_labels(self):
        for rel in CHANGED - {"27_SHA256SUMS.txt"}:
            text = self.pack[rel].decode("utf-8")
            with self.subTest(file=rel):
                self.assertTrue("v1.3.7 CANDIDATE, not audited" in text or "1.3.7-candidate, not audited" in text)
        label = self.pack["CANDIDATE-LABEL.md"].decode("utf-8")
        for rel in self.pack:
            self.assertIn(f"`{rel}`", label)

    def test_checksums_and_index(self):
        for sums in ("SHA256SUMS-v1.3.7-candidate.txt", "27_SHA256SUMS.txt"):
            for line in self.pack[sums].decode("utf-8").splitlines():
                digest, rel = line.split("  ", 1)
                if rel in self.pack:
                    with self.subTest(sums=sums, file=rel):
                        self.assertEqual(hashlib.sha256(self.pack[rel]).hexdigest(), digest)
        listed = {line.split("  ", 1)[1] for line in self.pack["SHA256SUMS-v1.3.7-candidate.txt"].decode().splitlines()}
        self.assertEqual(listed, set(self.pack) - {"SHA256SUMS-v1.3.7-candidate.txt"})
        index = json.loads(self.pack["41_F18_Fixture_Inputs/fixture-index.json"])
        self.assertEqual(index["fixture_count"], 144)
        for f in index["fixtures"]:
            data = self.pack[f["path"]]
            self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (f["sha256"], f["bytes"]), f["fixture_id"])
            self.assertEqual(json.loads(data)["expected"], f["expected"], f["fixture_id"])

    def test_expected_objects_unchanged(self):
        for rel in self.base:
            if rel.startswith("41_F18_Fixture_Inputs/") and not rel.endswith("fixture-index.json"):
                with self.subTest(file=rel):
                    self.assertEqual(json.loads(self.pack[rel])["expected"], json.loads(self.base[rel])["expected"])

    def test_corrected_m27_reaches_check_e(self):
        m27 = json.loads(self.pack["41_F18_Fixture_Inputs/M27.json"])
        inp = m27["input"]
        ns: dict = {}
        exec(inp["legal_input_predicate"]["source"], ns)  # pack text, not model output
        legal = ns[inp["legal_input_predicate"]["function"]]
        widths = inp["input_port_widths"]
        check = lambda v: validate_vector(v, widths, widths, lambda x: legal(x, inp["sampled_outputs"]))
        failure = check(inp["driver_return"])
        self.assertEqual(failure.diagnostic, m27["expected"]["diagnostic"])
        self.assertIsNone(check({"wr_en": "0"}))  # legal at full
        self.assertIsNone(validate_vector(inp["driver_return"], widths, widths, lambda x: legal(x, {"full": "0"})))
        self.assertNotIn("FIFO", inp["legal_input_predicate"]["source"])  # A1: no design specification needed


if __name__ == "__main__":
    unittest.main()
