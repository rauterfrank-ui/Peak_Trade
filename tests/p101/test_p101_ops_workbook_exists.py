from __future__ import annotations
from pathlib import Path


def test_workbook_exists_and_nonempty():
    p = Path("docs/ops/ai/WORKBOOK_OPS_LOOP_A2Z_V1.md")
    assert p.exists()
    assert p.stat().st_size > 200
