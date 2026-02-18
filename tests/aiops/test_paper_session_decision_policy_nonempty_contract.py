"""Contract: when PT_EVIDENCE_INCLUDE_DECISION=1, decision.policy has action + reason_codes."""

import json
import subprocess
from pathlib import Path

import pytest


def test_paper_session_cli_decision_policy_nonempty_when_enabled(
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
    monkeypatch.delenv("PT_POLICY_ENFORCE_V0", raising=False)

    cmd = [
        "python3",
        str(repo_root / "scripts" / "aiops" / "run_paper_trading_session.py"),
        "--spec",
        str(spec),
        "--run-id",
        "ci_policy_nonempty",
        "--outdir",
        str(outdir),
        "--evidence",
        "1",
    ]
    subprocess.check_call(cmd, cwd=repo_root)

    manifest = outdir / "evidence_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    dec = data.get("decision") or {}
    pol = dec.get("policy") or {}
    assert isinstance(pol, dict)
    assert pol.get("action") in ("ALLOW", "NO_TRADE")
    assert isinstance(pol.get("reason_codes", []), list)
