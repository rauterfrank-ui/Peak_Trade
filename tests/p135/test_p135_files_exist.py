from pathlib import Path


def test_p135_script_exists():
    assert Path("scripts/ops/p135_shadow_readonly_evidence_pack_v1.sh").is_file()


def test_p135_readme_exists():
    assert Path("docs/analysis/p135/README.md").is_file()
