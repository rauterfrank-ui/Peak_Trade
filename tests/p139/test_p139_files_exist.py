from pathlib import Path


def test_p139_readme_exists() -> None:
    assert Path("docs/analysis/p139/README.md").is_file()


def test_p139_tests_exist() -> None:
    assert Path("tests/p139/test_p139_files_exist.py").is_file()
