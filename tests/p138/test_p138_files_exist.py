from pathlib import Path


def test_p138_readme_exists() -> None:
    assert Path("docs/analysis/p138/README.md").is_file()
