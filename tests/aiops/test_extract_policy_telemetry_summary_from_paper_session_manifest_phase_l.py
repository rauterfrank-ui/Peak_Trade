"""Phase L: extractor from paper session evidence_manifest yields real policy (no fallback)."""

import json
import os
import subprocess
from pathlib import Path


def test_extractor_from_paper_session_manifest_produces_nonempty_policy(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    spec = repo_root / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"
    outdir = tmp_path / "session_out"
    outdir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "PT_DRY_RUN": "1",
        "PEAK_TRADE_LIVE_ENABLED": "false",
        "PT_EVIDENCE_INCLUDE_DECISION": "1",
    }
    subprocess.check_call(
        [
            "python3",
            str(repo_root / "scripts" / "aiops" / "run_paper_trading_session.py"),
            "--spec",
            str(spec),
            "--run-id",
            "ci_phase_l",
            "--outdir",
            str(outdir),
            "--evidence",
            "1",
        ],
        cwd=repo_root,
        env=env,
    )
    manifest = outdir / "evidence_manifest.json"
    assert manifest.exists()

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
    pol = data.get("policy") or {}
    assert isinstance(pol, dict) and pol
    assert pol.get("action") in ("ALLOW", "NO_TRADE")
    assert isinstance(pol.get("reason_codes") or [], list)
    assert "AUDIT_MANIFEST_NO_DECISION_CONTEXT" not in (pol.get("reason_codes") or [])
