from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_shared_smoke_aggregator_builds_summary() -> None:
    root = Path.cwd()

    prereq_scripts = [
        "scripts/ai/policy_audit_smoke.py",
        "scripts/ai/switch_layer_smoke.py",
        "scripts/wave3/model_registry_loader_smoke.py",
        "scripts/wave3/metrics_server_smoke.py",
        "scripts/wave3/api_manager_smoke.py",
    ]
    for script in prereq_scripts:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            check=False,
            cwd=root,
            env={"PYTHONPATH": str(root)},
        )
        assert result.returncode == 0, result.stderr or result.stdout

    out_file = root / "out/ops/shared_smoke_summary/shared_smoke_summary.json"
    if out_file.exists():
        out_file.unlink()

    result = subprocess.run(
        [sys.executable, "scripts/wave4/aggregate_smoke_contracts.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "wave4.summary.v1"
    assert payload["component"] == "shared_smoke_summary"
    assert payload["status"] == "SMOKE_OK"
    assert payload["component_count"] == 5
    assert payload["missing_count"] == 0
    assert len(payload["components"]) == 5
