"""Contract: extractor fallback-policy-json populates policy when manifest lacks decision."""

import json
import subprocess
from pathlib import Path


def test_extractor_fallback_policy_json_populates_policy(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"items": [{"path": "x.txt", "sha256": "00"}]}),
        encoding="utf-8",
    )

    fb = tmp_path / "fallback_policy.json"
    fb.write_text(
        json.dumps({"action": "NO_TRADE", "reason_codes": ["NO_MODEL_EDGE_V0"]}),
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
            "--fallback-policy-json",
            str(fb),
        ],
        cwd=repo_root,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    pol = data.get("policy") or {}
    assert pol.get("action") == "NO_TRADE"
    assert isinstance(pol.get("reason_codes"), list)
    assert pol.get("reason_codes")


def test_extractor_without_fallback_keeps_policy_empty(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"items": [{"path": "x.txt", "sha256": "00"}]}),
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
    assert "policy" in data
    pol = data.get("policy") or {}
    assert isinstance(pol, dict)
