from pathlib import Path


def test_p136_script_exists() -> None:
    assert Path("scripts/ops/p136_exec_net_shadow_readonly_finish_snapshot_v1.sh").is_file()


def test_p136_readme_exists() -> None:
    assert Path("docs/analysis/p136/README.md").is_file()
