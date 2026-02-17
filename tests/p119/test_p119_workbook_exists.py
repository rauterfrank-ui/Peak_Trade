from pathlib import Path


def test_p119_workbook_exists():
    assert Path("docs/ops/ai/WORKBOOK_EXECUTION_WIRING_A2Z_V1.md").is_file()


def test_p119_readme_exists():
    assert Path("docs/analysis/p119/README.md").is_file()
