from pathlib import Path


def test_p140_script_exists() -> None:
    assert Path("scripts/ops/p140_exec_net_paper_evidence_pack_v1.sh").is_file()


def test_p140_readme_exists() -> None:
    assert Path("docs/analysis/p140/README.md").is_file()
