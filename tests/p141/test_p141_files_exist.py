from pathlib import Path


def test_p141_readme_exists() -> None:
    assert Path("docs/analysis/p141/README.md").is_file()


def test_p141_script_exists() -> None:
    p = Path("scripts/ops/p141_exec_net_paper_runner_onramp_v1.sh")
    assert p.is_file()
    assert p.stat().st_size > 0
