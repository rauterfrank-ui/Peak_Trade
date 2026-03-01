"""Offline contract test for aws_export_write_smoke report format."""

import json
import subprocess
import sys
from pathlib import Path


def test_contract_disabled_produces_reports():
    """With PT_EXPORT_SMOKE_WRITE_ENABLED unset, script exits 2 and writes WRITE_SMOKE_DISABLED."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    env = {
        "PT_EXPORT_REMOTE": "",
        "PT_EXPORT_PREFIX": "",
        "PT_RCLONE_CONF_B64": "",
        "PT_EXPORT_SMOKE_WRITE_ENABLED": "",
        "PT_EXPORT_SMOKE_CONFIRM_TOKEN": "",
    }
    r = subprocess.run(
        [sys.executable, str(repo_root / "scripts/ops/aws_export_write_smoke.py")],
        capture_output=True,
        text=True,
        env={**env},
        cwd=str(repo_root),
    )
    assert r.returncode == 2
    jpath = repo_root / "reports/status/aws_export_write_smoke.json"
    assert jpath.exists()
    obj = json.loads(jpath.read_text())
    assert obj["ok"] is False
    assert obj["reason"] == "WRITE_SMOKE_DISABLED"
    assert "timestamp_utc" in obj
    assert "wrote" in obj
    assert obj["wrote"] is False
