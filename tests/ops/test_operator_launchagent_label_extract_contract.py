from pathlib import Path


def test_launchagent_scripts_use_plistbuddy_for_label():
    install = Path("scripts/ops/install_operator_all_launchagent.sh").read_text(encoding="utf-8")
    uninstall = Path("scripts/ops/uninstall_operator_all_launchagent.sh").read_text(
        encoding="utf-8"
    )
    assert "/usr/libexec/PlistBuddy" in install
    assert "/usr/libexec/PlistBuddy" in uninstall
    assert "Print :Label" in install
    assert "Print :Label" in uninstall
