"""Smoke test for pipeline_cli delegating to risk_cli (offline-first)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _parse_json_from_stdout(stdout: str):
    """Extract a single JSON object from stdout (handles leading warnings e.g. prometheus)."""
    start = stdout.find("{")
    end = stdout.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError("no JSON object in stdout")
    return json.loads(stdout[start:end])


def test_pipeline_cli_risk_smoke(tmp_path):
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pipeline_cli.py"),
        "--run-id",
        "smoke_pipeline",
        "--artifacts-dir",
        str(tmp_path),
        "--sandbox",
        "risk",
        "var",
        "--returns-file",
        str(ROOT / "tests" / "fixtures" / "returns_normal_5k.txt"),
        "--alpha",
        "0.99",
        "--method",
        "historical",
    ]
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PEAKTRADE_SANDBOX": "1"},
    )
    assert p.returncode == 0, p.stderr or p.stdout
    data = _parse_json_from_stdout(p.stdout)
    assert data["var"] >= 0
    assert (tmp_path / "smoke_pipeline" / "meta.json").exists()
    assert (tmp_path / "smoke_pipeline" / "results" / "var.json").exists()
