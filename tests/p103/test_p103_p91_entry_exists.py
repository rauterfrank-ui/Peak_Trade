from pathlib import Path


def test_p103_entry_script_exists():
    p = Path("scripts/ops/p103_launchd_p91_audit_snapshot_entry_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o100  # executable


def test_p91_template_exists():
    p = Path("docs/ops/services/launchd_p91_audit_snapshot_runner_v1.template.plist")
    assert p.exists()
    assert "@REPO_ROOT@" in p.read_text()
