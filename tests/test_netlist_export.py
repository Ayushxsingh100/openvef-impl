"""Null-netlist export repeatability with the pinned Yosys/MCY (D-004; F14 pattern).

Protocol L233: "The null-mutant netlist is generated from the original RTL by exactly
the same synthesis/export script, tool versions and top-level interface as the mutant
netlists, with no mutation applied. Export must preserve top module name and public
ports. Run the export twice and compare null-netlist hashes."

Uses the TEST-ONLY toy design in tests/sim_designs/toy.v (not a FIFO, not owner
material) and a TEST-ONLY export script. The frozen export script is an owner item
(Protocol L544; docs/fifo-owner-checklist.md item 13). Each export runs in its own
sandbox container with the artifact-container flags. Skipped only if Docker is absent.
"""
from __future__ import annotations

import re
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))  # `python -I` does not add the script directory

from openvef import sandbox  # noqa: E402
from openvef.simulation import driver_stages  # noqa: E402

DOCKER = shutil.which("docker") is not None
TOY = (HERE / "sim_designs" / "toy.v").read_text()
# TEST-ONLY export script (not the frozen L544 script).
EXPORT = "read_verilog /tmp/in.v; synth -top toy; write_verilog -noattr /tmp/net.v"
MARK = "===OPENVEF-NETLIST==="


def run_text(command: list[str], stdin: bytes = b"", timeout_s: float = 120.0) -> str:
    """Run a command in the sandbox and return its stdout (development launcher)."""
    import subprocess
    import uuid
    name = f"openvef-{uuid.uuid4().hex[:12]}"
    proc = subprocess.run(sandbox.docker_argv(sandbox.image_tag(), command, name=name), input=stdin,
                          capture_output=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise AssertionError(f"exit {proc.returncode}: {proc.stderr.decode(errors='replace')[-800:]}")
    return proc.stdout.decode("utf-8")


def export() -> tuple[str, str]:
    script = (f"set -e; cat > /tmp/in.v; yosys -q -p '{EXPORT}'; "
              f"sha256sum /tmp/net.v | cut -c1-64; echo {MARK}; cat /tmp/net.v")
    out = run_text(["sh", "-c", script], TOY.encode())
    digest, netlist = out.split(f"\n{MARK}\n", 1)
    return digest.strip(), netlist


def ports(verilog: str, module: str) -> dict[str, tuple[str, int]]:
    """{name: (direction, width)} for one module's input/output declarations."""
    body = re.search(rf"\bmodule\s+{module}\b(.*?)\bendmodule\b", verilog, re.S).group(1)
    found = {}
    # Each declaration runs from its direction keyword to the next direction keyword, `;`
    # or the end of an ANSI port list. Handles ANSI headers and one-per-line netlists.
    for direction, decl in re.findall(r"\b(input|output)\b(.*?)(?=\binput\b|\boutput\b|;|\))", body, re.S):
        rng = re.search(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", decl)
        width = abs(int(rng.group(1)) - int(rng.group(2))) + 1 if rng else 1
        decl = re.sub(r"\[[^\]]*\]|\b(?:wire|reg)\b", " ", decl)
        for name in re.split(r"\s*,\s*", decl.strip()):
            if name:
                found[name] = (direction, width)
    return found


@unittest.skipUnless(DOCKER, "docker not available")
class NetlistExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox.ensure_image()
        cls.first = export()
        cls.second = export()  # a separate container

    def test_tool_versions(self):
        self.assertIn("Yosys 0.71", run_text(["yosys", "-V"]))
        self.assertEqual(run_text(["cat", "/usr/local/share/mcy/COMMIT"]).strip(),
                         "5a2cad0cbefceb7f23051c08348bd23128fd1046")
        # D-004a: `click` is in requirements.lock, so the MCY command-line tool must start.
        self.assertIn("Usage: mcy", run_text(["mcy", "--help"]))

    def test_export_twice_identical_hash(self):
        (h1, n1), (h2, n2) = self.first, self.second
        self.assertRegex(h1, r"^[0-9a-f]{64}$")
        self.assertEqual(h1, h2)
        self.assertEqual(n1, n2)

    def test_top_module_and_public_ports_preserved(self):
        netlist = self.first[1]
        self.assertRegex(netlist, r"\bmodule\s+toy\b")
        self.assertEqual(ports(netlist, "toy"), ports(TOY, "toy"))
        self.assertEqual(ports(TOY, "toy"), {"clk": ("input", 1), "rst": ("input", 1), "a": ("input", 2),
                                             "b": ("input", 1), "q": ("output", 2), "flag": ("output", 1)})

    def test_exported_netlist_simulates_equivalently(self):
        from test_simulation import COUNTER, design
        null = design(verilog_sources={"toy.v": self.first[1]})
        self.assertIsNone(driver_stages(COUNTER, design(), null, ["flag", "q"], 0, step_timeout_s=3.0, budget_s=30.0))


if __name__ == "__main__":
    unittest.main()
