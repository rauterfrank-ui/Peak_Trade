from pathlib import Path


def test_allowlist_file_exists():
    assert Path("src/execution/networked/allowlist_v1.py").is_file()


def test_readme_exists():
    assert Path("docs/analysis/p130/README.md").is_file()
