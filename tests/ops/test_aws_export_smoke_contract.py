"""Offline contract test for aws_export_smoke report format."""

import json
import subprocess
import sys
from pathlib import Path


def test_contract_missing_env_produces_reports():
    """With empty PT_EXPORT_REMOTE, script exits 2 and writes reports with expected format."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    env = {"PT_EXPORT_REMOTE": "", "PT_EXPORT_PREFIX": "", "PT_RCLONE_CONF_B64": ""}
    r = subprocess.run(
        [sys.executable, str(repo_root / "scripts/ops/aws_export_smoke.py")],
        capture_output=True,
        text=True,
        env={**env},
        cwd=str(repo_root),
    )
    assert r.returncode == 2
    jpath = repo_root / "reports/status/aws_export_smoke.json"
    assert jpath.exists()
    obj = json.loads(jpath.read_text())
    assert "ok" in obj
    assert obj["ok"] is False
    assert obj["reason"] == "MISSING_PT_EXPORT_REMOTE"
    assert "timestamp_utc" in obj
    assert "export_remote" in obj
    assert "sample_listing" in obj
