"""Contract tests for extract_policy_telemetry_summary."""

import json
from pathlib import Path

from scripts.aiops.extract_policy_telemetry_summary import extract_from_evidence_manifest


def test_extract_defaults_when_no_decision(tmp_path: Path) -> None:
    p = tmp_path / "evidence_manifest.json"
    p.write_text(json.dumps({"version": 1, "files": []}), encoding="utf-8")
    out = extract_from_evidence_manifest(p)
    assert out["source"] == "evidence_manifest"
    assert isinstance(out["policy"], dict)
    assert isinstance(out["policy_enforce"], dict)


def test_extract_policy_fields_when_present(tmp_path: Path) -> None:
    p = tmp_path / "evidence_manifest.json"
    payload = {
        "decision": {
            "policy": {
                "action": "NO_TRADE",
                "reason_codes": ["EDGE_LT_COSTS_V1"],
                "metadata": {"edge_bp": 0.0},
            },
            "policy_enforce": {"allowed": False, "reason_code": "BLOCKED", "env": "paper"},
        }
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = extract_from_evidence_manifest(p)
    assert out["policy"]["action"] == "NO_TRADE"
    assert out["policy"]["reason_codes"] == ["EDGE_LT_COSTS_V1"]
    assert out["policy"]["metadata"]["edge_bp"] == 0.0
    assert out["policy_enforce"]["allowed"] is False
