from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    ("scripts/ai/policy_audit_smoke.py", Path("out/ops/policy_audit_smoke/policy_audit_smoke.json")),
    ("scripts/ai/switch_layer_smoke.py", Path("out/ops/switch_layer_smoke/switch_layer_smoke.json")),
    (
        "scripts/wave3/model_registry_loader_smoke.py",
        Path("out/ops/model_registry_loader_smoke/model_registry_loader_smoke.json"),
    ),
    ("scripts/wave3/metrics_server_smoke.py", Path("out/ops/metrics_server_smoke/metrics_server_smoke.json")),
    ("scripts/wave3/api_manager_smoke.py", Path("out/ops/api_manager_smoke/api_manager_smoke.json")),
]


def test_shared_smoke_contract_fields() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    for script, out_file in SCRIPTS:
        full_out = root / out_file
        if full_out.exists():
            full_out.unlink()

        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            check=False,
            cwd=root,
            env={"PYTHONPATH": str(root)},
        )
        assert result.returncode == 0, f"{script}: {result.stderr or result.stdout}"
        assert full_out.exists(), f"missing artifact for {script}"

        payload = json.loads(full_out.read_text(encoding="utf-8"))
        for field in ["contract_version", "status", "component", "run_id", "timestamp", "summary"]:
            assert field in payload, f"{script}: missing field {field}"

        assert payload["contract_version"] == "wave4.v1"
        assert payload["status"] == "SMOKE_OK"
        assert isinstance(payload["component"], str) and payload["component"]
        assert isinstance(payload["run_id"], str) and payload["run_id"]
        assert isinstance(payload["timestamp"], str) and payload["timestamp"]
        assert isinstance(payload["summary"], str) and payload["summary"]
