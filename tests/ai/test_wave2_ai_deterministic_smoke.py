from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_policy_audit_smoke_writes_deterministic_output() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    out_file = root / "out/ops/policy_audit_smoke/policy_audit_smoke.json"
    if out_file.exists():
        out_file.unlink()

    result = subprocess.run(
        [sys.executable, "scripts/ai/policy_audit_smoke.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "ai_model_policy_audit_v1"
    assert payload["mode"] == "paper_only"
    assert payload["enabled_count"] == 2
    assert payload["blocked_count"] == 1


def test_switch_layer_smoke_writes_fixture_based_output() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    out_file = root / "out/ops/switch_layer_smoke/switch_layer_smoke.json"
    if out_file.exists():
        out_file.unlink()

    result = subprocess.run(
        [sys.executable, "scripts/ai/switch_layer_smoke.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "switch_layer_v1"
    assert payload["regime"] == "neutral"
    assert payload["volatility"] == 0.12
