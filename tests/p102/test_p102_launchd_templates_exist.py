from pathlib import Path


def test_launchd_templates_exist():
    root = Path(__file__).resolve().parents[2]
    p93 = root / "docs/ops/services/launchd_p93_status_dashboard_v1.template.plist"
    p94 = root / "docs/ops/services/launchd_p94_p93_status_dashboard_retention_v1.template.plist"
    assert p93.exists()
    assert p94.exists()
