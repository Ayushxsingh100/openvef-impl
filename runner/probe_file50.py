"""File 50 Python 3.11 Unicode identifier tokenizer check, run in the pinned image.

Part 1 executes the File 50 code block byte-for-byte (it is extracted from the baseline
file at run time, not retyped). Part 2 runs the project's identifier scanner
(openvef.import_policy.scan_identifiers) on both File 50 sources, plus STRING and COMMENT
controls. Writes probe.json and part1_stdout.txt to the output directory.

Usage (inside the pinned image): python -I runner/probe_file50.py <baseline_root> <out_dir>
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from openvef.import_policy import scan_identifiers  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    baseline, out = Path(sys.argv[1]), Path(sys.argv[2])
    f50 = (baseline / "50_Python311_Unicode_Tokenizer_Check.md").read_bytes()
    code = re.search(rb"```python\n(.*?)```", f50, re.S).group(1)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code.decode("utf-8"), "file50_block", "exec"), {"__name__": "__file50__"})  # noqa: S102
    part1 = buf.getvalue()
    (out / "part1_stdout.txt").write_text(part1, encoding="utf-8")
    cases = {
        "file50_source_1": "℘ = 1\n",
        "file50_source_2": "a℘ = 1\n",
        "string_control": 's = "naïve ℘"\n',
        "comment_control": "x = 1  # café ℘\n",
    }
    part2 = {}
    for name, src in cases.items():
        f = scan_identifiers("driver.py", src)
        part2[name] = {"source": src, "diagnostic": None if f is None else f.diagnostic}
    exe = os.path.realpath(sys.executable)
    record = {
        "python_version": sys.version, "python_executable": exe,
        "python_executable_sha256": sha(Path(exe).read_bytes()),
        "file50_sha256": sha(f50), "file50_code_block_sha256": sha(code),
        "probe_script_sha256": sha(Path(__file__).read_bytes()),
        "import_policy_sha256": sha((REPO / "src/openvef/import_policy.py").read_bytes()),
        "part1_stdout_sha256": sha(part1.encode("utf-8")), "part1_stdout": part1, "part2": part2,
    }
    (out / "probe.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(part1, end="")
    print(json.dumps(part2, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
