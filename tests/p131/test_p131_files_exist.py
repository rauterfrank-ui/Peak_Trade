"""P131 — File existence tests."""

from pathlib import Path


def test_onramp_runner_exists() -> None:
    assert Path("src/execution/networked/onramp_runner_v1.py").is_file()


def test_allowlist_exists() -> None:
    assert Path("src/execution/networked/allowlist_v1.py").is_file()


def test_p131_readme_exists() -> None:
    assert Path("docs/analysis/p131/README.md").is_file()
