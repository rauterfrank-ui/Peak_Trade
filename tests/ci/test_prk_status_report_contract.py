from __future__ import annotations

from pathlib import Path


def test_prk_status_report_assets_exist():
    assert Path(".github/workflows/prk-prj-status-report.yml").exists()
    assert Path("scripts/ci/prj_status_report.py").exists()
    assert Path(".github/workflows/prj-scheduled-shadow-paper-features-smoke.yml").exists()
