from pathlib import Path


def test_p123_workbook_exists():
    p = Path("docs/ops/ai/WORKBOOK_EXECUTION_NETWORKED_ONRAMP_A2Z_V1.md")
    assert p.exists()
    assert p.read_text(encoding="utf-8").strip()
