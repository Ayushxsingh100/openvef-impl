"""Every pack quotation in the listed documents (DOCS) is
verbatim: each line `> [<file> L<n>] "<text>"` must have <text> as a substring of line
<n> of that baseline file. <file> is a pack file number (e.g. `02`) or `41/<ID>.json`.
Inside the quotes, \\" stands for a double quote.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "baseline/OpenVEF_Planning_v1_3_6"
DOCS = ("docs/pack-defects.md", "docs/DEVIATIONS.md", "docs/fifo-owner-checklist.md", "docs/fifo-spec-v0.1.md",
        "docs/fifo-spec-v0.2.md", "docs/fifo-benchmark-overlap-disclosure-DRAFT.md",
        "docs/fifo-frozen-values-proposal-DRAFT.md",
        "docs/OWNER-FREEZE-PACKAGE.md", "docs/AUDIT-READINESS.md", "docs/F1-F17-plan.md",
        "docs/AUDIT-BRIEF.md", "proposals/v1.3.7/PROPOSED-CORRECTIONS-DRAFT.md",
        "proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md")
QUOTE = re.compile(r'^> \[(?P<file>[0-9]{2}|41/[A-Za-z0-9]+\.json) L(?P<line>[0-9]+)\] "(?P<text>.*)"$')


def resolve(tag: str) -> Path:
    if tag.startswith("41/"):
        return BASE / "41_F18_Fixture_Inputs" / tag[3:]
    matches = sorted(BASE.glob(f"{tag}_*"))
    if len(matches) != 1:
        raise AssertionError(f"file tag {tag} matches {matches}")
    return matches[0]


class DocQuoteTests(unittest.TestCase):
    def test_quotes_are_verbatim(self):
        count = 0
        for doc in DOCS:
            path = REPO / doc
            if not path.exists():
                continue
            for n, line in enumerate(path.read_text("utf-8").splitlines(), 1):
                if line.startswith("> ["):
                    m = QUOTE.match(line)
                    self.assertIsNotNone(m, f"{doc}:{n}: malformed quotation line")
                    source = resolve(m["file"]).read_text("utf-8").splitlines()
                    target = source[int(m["line"]) - 1]
                    text = m["text"].replace('\\"', '"')
                    with self.subTest(doc=doc, line=n):
                        self.assertIn(text, target, f"{doc}:{n} not verbatim at {m['file']} L{m['line']}")
                    count += 1
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
