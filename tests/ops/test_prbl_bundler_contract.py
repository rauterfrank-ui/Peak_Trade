from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "lines1,lines2,expected",
    [
        (["a", "b"], ["c"], ["a", "b", "c"]),
        ([], ["x"], ["x"]),
    ],
)
def test_bundle_line_concat(tmp_path: Path, lines1, lines2, expected):
    # Minimal contract: bundler concatenation logic (without gh). We emulate bundle target.
    p1 = tmp_path / "r1" / "execution_events.jsonl"
    p1.parent.mkdir(parents=True, exist_ok=True)
    p1.write_text("\n".join(lines1) + ("\n" if lines1 else ""), encoding="utf-8")

    p2 = tmp_path / "r2" / "execution_events.jsonl"
    p2.parent.mkdir(parents=True, exist_ok=True)
    p2.write_text("\n".join(lines2) + ("\n" if lines2 else ""), encoding="utf-8")

    out = tmp_path / "execution_events_bundled.jsonl"
    lines = []
    for p in [p1, p2]:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s:
                lines.append(s)
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    assert out.read_text(encoding="utf-8").splitlines() == expected
