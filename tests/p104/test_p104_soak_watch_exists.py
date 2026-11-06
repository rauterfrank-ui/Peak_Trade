from pathlib import Path


def test_p104_script_exists():
    p = Path("scripts/ops/p104_soak_watch_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o100  # executable


def test_p104_template_exists():
    p = Path("docs/ops/services/launchd_p104_soak_watch_v1.template.plist")
    assert p.exists()
    assert "@REPO_ROOT@" in p.read_text()


def test_p104_installer_exists():
    p = Path("scripts/ops/install_launchd_p104_soak_watch_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o100  # executable
