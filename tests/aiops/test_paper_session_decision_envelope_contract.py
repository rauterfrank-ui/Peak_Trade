"""Contract: when PT_EVIDENCE_INCLUDE_DECISION=1, evidence_manifest contains decision key."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.aiops.extract_policy_telemetry_summary import extract_from_evidence_manifest


def test_paper_session_cli_writes_decision_envelope_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    spec = repo_root / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"
    assert spec.exists()

    outdir = tmp_path / "session_out"
    outdir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PT_DRY_RUN", "1")
    monkeypatch.setenv("PEAK_TRADE_LIVE_ENABLED", "false")
    monkeypatch.setenv("PT_EVIDENCE_INCLUDE_DECISION", "1")

    cmd = [
        "python3",
        str(repo_root / "scripts" / "aiops" / "run_paper_trading_session.py"),
        "--spec",
        str(spec),
        "--run-id",
        "ci_contract",
        "--outdir",
        str(outdir),
        "--evidence",
        "1",
    ]
    subprocess.check_call(cmd, cwd=repo_root)

    manifest = outdir / "evidence_manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert "decision" in data
    assert isinstance(data["decision"], dict)
    assert "policy" in data["decision"]

    # Extractor yields structure (policy may be empty for paper session)
    summary = extract_from_evidence_manifest(manifest)
    assert "policy" in summary
    assert "policy_enforce" in summary
