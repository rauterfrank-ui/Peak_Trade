"""Contract: extractor handles audit manifest (no decision) -> empty policy ok."""

import json
import subprocess
from pathlib import Path

import pytest


def test_extract_policy_telemetry_summary_handles_audit_manifest(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    # Minimal audit-like manifest without decision
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "items": [{"path": "x.txt", "sha256": "00"}],
                "schema": "pt.audit.evidence.manifest.v1",
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "telemetry_summary.json"
    subprocess.check_call(
        [
            "python3",
            str(repo_root / "scripts" / "aiops" / "extract_policy_telemetry_summary.py"),
            "--manifest",
            str(manifest),
            "--out",
            str(out),
        ],
        cwd=repo_root,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    # policy may be empty if there is no decision context
    assert "policy" in data
