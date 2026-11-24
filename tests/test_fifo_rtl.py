"""DRAFT FIFO RTL (D-005) checked against DRAFT spec v0.2 in the pinned sandbox.

Uses the production harness (Icarus 12 -g2012 + cocotb, A-040 trace rows, A-042 held
reset) and the DRAFT design materials in design/fifo/, loaded by
openvef.design_materials. Harness check (e) runs the spec's FIFO-042 predicate. These
tests verify Claude's own RTL draft. They are NOT the directed suite or the reference
driver (checklist item 14, human-written).

- the worked example of fifo-spec-v0.2.md, on RTL and on the null netlist;
- the null netlist exported twice with the DRAFT export script, with identical hashes and
  the top module and public ports preserved (Protocol L233);
- RTL versus null paired runs with no divergence;
- a seeded legal random driver, checked row by row against a model of the clauses.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

from openvef import sandbox  # noqa: E402
from openvef import design_materials  # noqa: E402
from openvef.simulation import driver_run, driver_stages, run_outcome  # noqa: E402
from test_netlist_export import ports, run_text  # noqa: E402

DOCKER = shutil.which("docker") is not None
MATERIALS = json.loads((REPO / "design/fifo/design-materials-DRAFT.json").read_text(encoding="utf-8"))
RTL = (REPO / MATERIALS["rtl"]).read_text(encoding="utf-8")
EXPORT_YS = (REPO / "design/fifo/export_null.ys").read_text(encoding="utf-8")
SPEC = (REPO / MATERIALS["spec"]).read_text(encoding="utf-8").split("<!-- PAYLOAD TEXT BELOW -->", 1)[1]
INP, OUT, NXT = "inputs_consumed_at_edge_n", "outputs_after_edge_n", "next_inputs_scheduled_for_edge_n_plus_1"
MARK = "===OPENVEF-NETLIST==="


def legal_input():
    code = re.search(r"```python\n(.*?)```", SPEC, re.S).group(1)
    ns: dict = {}
    exec(compile(code, "FIFO-042", "exec"), ns)  # noqa: S102 - the spec's own code
    return ns["legal_input"]


def example_rows() -> list[dict]:
    table = SPEC.split("### Worked example", 1)[1].split("## [Port manifest]", 1)[0]
    rows = []
    for line in table.splitlines():
        if re.match(r"^\| [0-9]+ \|", line):
            edge, wr, data, rd, c, valid, rdata, full, af, empty = [x.strip() for x in line.strip("|").split("|")]
            rows.append({"wr_en": wr, "wr_data": "00000000" if data == "-" else format(int(data, 16), "08b"),
                         "rd_en": rd, "rd_valid": valid,
                         "rd_data": None if rdata == "-" else format(int(rdata, 16), "08b"),
                         "full": full, "almost_full": af, "empty": empty})
    return rows


LOADED = design_materials.load(REPO, "design/fifo/design-materials-DRAFT.json")


def design(sources: dict) -> dict:
    return dict(LOADED["base"], verilog_sources=sources)  # check (e) runs FIFO-042


def replay_driver(vectors: list[dict]) -> str:
    return ("VECTORS = " + repr(vectors) + "\n\n"
            "def create_driver(seed):\n    return Driver()\n\n"
            "class Driver:\n"
            "    def step(self, cycle_index, outputs_after_edge):\n"
            "        if cycle_index >= len(VECTORS):\n            return 'COMPLETE'\n"
            "        return dict(VECTORS[cycle_index])\n")


# A seeded legal random driver: never writes without reading while the sampled full = 1.
RANDOM_DRIVER = """import random

def create_driver(seed):
    d = Driver()
    d.rng = random.Random(seed)
    return d

class Driver:
    def step(self, cycle_index, outputs_after_edge):
        wr = self.rng.random() < 0.6
        rd = self.rng.random() < 0.45
        if outputs_after_edge['full'] == '1' and wr and not rd:
            rd = self.rng.random() < 0.5
            wr = rd
        data = format(self.rng.randrange(256), '08b')
        return {'wr_en': '1' if wr else '0', 'wr_data': data, 'rd_en': '1' if rd else '0'}
"""


def export_null() -> tuple[str, str]:
    script = ("set -e; cat > /tmp/in.v; cat > /tmp/export.ys <<'OPENVEF_YS'\n" + EXPORT_YS + "OPENVEF_YS\n"
              f"yosys -q -s /tmp/export.ys; sha256sum /tmp/net.v | cut -c1-64; echo {MARK}; cat /tmp/net.v")
    out = run_text(["sh", "-c", script], RTL.encode(), timeout_s=300.0)
    digest, netlist = out.split(f"\n{MARK}\n", 1)
    return digest.strip(), netlist


class Model:
    """The clauses FIFO-010 to FIFO-035 as a state machine (for checking only)."""

    def __init__(self):
        self.words: list[str] = []

    def edge(self, v: dict) -> dict:
        read = v["rd_en"] == "1" and len(self.words) > 0
        write = v["wr_en"] == "1" and (len(self.words) < 4 or read)
        popped = self.words.pop(0) if read else None
        if write:
            self.words.append(v["wr_data"])
        c = len(self.words)
        return {"rd_valid": "1" if read else "0", "rd_data": popped, "full": "1" if c == 4 else "0",
                "almost_full": "1" if c >= 3 else "0", "empty": "1" if c == 0 else "0"}


@unittest.skipUnless(DOCKER, "docker not available")
class FifoRtlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()
        cls.export1 = export_null()
        cls.export2 = export_null()
        cls.rtl = design({"ovf_fifo.v": RTL})
        cls.null = design({"ovf_fifo_null.v": cls.export1[1]})

    def run_on(self, src: str, d: dict, seed: int = 0) -> list:
        r = driver_run(src, d, "rtl", seed, step_timeout_s=5.0, budget_s=120.0)
        self.assertEqual(r.get("events"), [], r.get("events"))
        self.assertEqual(r["run_status"], "COMPLETE_TRACE")
        self.assertEqual(r["reset_release_cycle"], MATERIALS["reset_release_cycle"])
        return r["rows"]

    def check_example(self, d: dict):
        expected = example_rows()
        vectors = [{k: e[k] for k in ("wr_en", "wr_data", "rd_en")} for e in expected]
        rows = self.run_on(replay_driver(vectors), d)
        release = MATERIALS["reset_release_cycle"]
        self.assertEqual(rows[release][OUT]["empty"], "1")  # after reset (FIFO-010)
        legal = legal_input()
        for k, e in enumerate(expected):
            prev, row = rows[release + k], rows[release + k + 1]
            self.assertTrue(legal(vectors[k], prev[OUT]), f"example edge {k + 1} vector illegal")
            self.assertEqual(row[INP], {**vectors[k], "rst": "0"})
            got = row[OUT]
            for port in ("rd_valid", "full", "almost_full", "empty"):
                self.assertEqual(got[port], e[port], f"example edge {k + 1}: {port}")
            if e["rd_valid"] == "1":
                self.assertEqual(got["rd_data"], e["rd_data"], f"example edge {k + 1}: rd_data")

    def test_worked_example_on_rtl(self):
        self.check_example(self.rtl)

    def test_worked_example_on_null_netlist(self):
        self.check_example(self.null)

    def test_null_export_twice_identical(self):
        (h1, n1), (h2, n2) = self.export1, self.export2
        self.assertRegex(h1, r"^[0-9a-f]{64}$")
        self.assertEqual(h1, h2)
        self.assertEqual(n1, n2)

    def test_null_export_preserves_top_and_ports(self):
        netlist = self.export1[1]
        self.assertRegex(netlist, r"\bmodule\s+ovf_fifo\b")
        self.assertEqual(ports(netlist, "ovf_fifo"), ports(RTL, "ovf_fifo"))
        self.assertEqual(ports(RTL, "ovf_fifo"), {
            "clk": ("input", 1), "rst": ("input", 1), "wr_en": ("input", 1), "wr_data": ("input", 8),
            "rd_en": ("input", 1), "rd_valid": ("output", 1), "rd_data": ("output", 8), "full": ("output", 1),
            "almost_full": ("output", 1), "empty": ("output", 1)})

    def test_paired_runs_no_divergence(self):
        vectors = [{k: e[k] for k in ("wr_en", "wr_data", "rd_en")} for e in example_rows()]
        for src in (replay_driver(vectors), RANDOM_DRIVER):
            self.assertIsNone(driver_stages(src, self.rtl, self.null, MATERIALS["output_ports"], 7,
                                            step_timeout_s=5.0, budget_s=120.0))

    def test_check_e_rejects_write_while_full_without_read(self):
        # Five writes and no reads: the fifth vector is applied while the sampled full = 1.
        src = replay_driver([{"wr_en": "1", "wr_data": "00000001", "rd_en": "0"}] * 6)
        result = driver_run(src, self.rtl, "rtl", 0, step_timeout_s=5.0, budget_s=120.0)
        self.assertEqual(run_outcome(result).diagnostic, "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE")
        self.assertEqual(result["events"][0]["cycle"], MATERIALS["reset_release_cycle"] + 4)
        self.assertEqual(result["rows"][-1][OUT]["full"], "1")
        self.assertIsNone(result["rows"][-1][NXT])  # the invalid vector is not driven

    def test_random_legal_driver_matches_model(self):
        legal = legal_input()
        release = MATERIALS["reset_release_cycle"]
        for seed in (1, 2, 3):
            rows = self.run_on(RANDOM_DRIVER, self.rtl, seed)
            self.assertEqual(len(rows), release + MATERIALS["cycle_cap"] + 1)
            model = Model()
            stats = {"read": 0, "write_at_full": 0, "af_rise": 0}
            for n in range(release + 1, len(rows)):
                v = {k: rows[n][INP][k] for k in ("wr_en", "wr_data", "rd_en")}
                self.assertEqual(rows[n][INP]["rst"], "0")
                self.assertTrue(legal(v, rows[n - 1][OUT]), f"seed {seed} row {n}: illegal vector")
                if rows[n - 1][OUT]["full"] == "1" and v["wr_en"] == "1":
                    stats["write_at_full"] += 1
                exp, got = model.edge(v), rows[n][OUT]
                for port in ("rd_valid", "full", "almost_full", "empty"):
                    self.assertEqual(got[port], exp[port], f"seed {seed} row {n}: {port}")
                if exp["rd_valid"] == "1":
                    stats["read"] += 1
                    self.assertEqual(got["rd_data"], exp["rd_data"], f"seed {seed} row {n}: rd_data")
                if got["almost_full"] == "1" and rows[n - 1][OUT]["almost_full"] == "0":
                    stats["af_rise"] += 1
            self.assertGreater(stats["read"], 5, stats)
            self.assertGreater(stats["af_rise"], 0, stats)


if __name__ == "__main__":
    unittest.main()
