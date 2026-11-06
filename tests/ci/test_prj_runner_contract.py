from __future__ import annotations

from pathlib import Path


def test_prj_scripts_exist_and_are_executable():
    assert Path("scripts/ci/prj_features_smoke_and_evidence.sh").exists()
    assert Path("scripts/aiops/run_prj_features_smoke.py").exists()
    wf = Path(".github/workflows/prj-scheduled-shadow-paper-features-smoke.yml")
    assert wf.exists()
    txt = wf.read_text(encoding="utf-8")
    assert "PT_PRJ_FEATURES_SMOKE_ENABLED" in txt
    assert "upload-artifact" in txt
