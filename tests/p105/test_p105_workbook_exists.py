from pathlib import Path


def test_p105_workbook_exists():
    p = Path("docs/ops/ai/WORKBOOK_EXCHANGE_EXECUTION_A2Z_V1.md")
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "Exchange + Execution A2Z" in txt
