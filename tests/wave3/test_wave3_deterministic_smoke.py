from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_and_load(script: str, out_file: Path) -> dict:
    root = Path(__file__).resolve().parent.parent.parent
    out_path = root / out_file
    if out_path.exists():
        out_path.unlink()

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert out_path.exists()
    return json.loads(out_path.read_text(encoding="utf-8"))


def test_model_registry_loader_deterministic_smoke() -> None:
    payload = _run_and_load(
        "scripts/wave3/model_registry_loader_smoke.py",
        Path("out/ops/model_registry_loader_smoke/model_registry_loader_smoke.json"),
    )
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "model_registry_loader"
    assert payload["registry_name"] == "local_test_registry"
    assert payload["model_count"] == 2
    assert payload["default_model"] == "gpt-5.2-pro"


def test_metrics_server_deterministic_smoke() -> None:
    payload = _run_and_load(
        "scripts/wave3/metrics_server_smoke.py",
        Path("out/ops/metrics_server_smoke/metrics_server_smoke.json"),
    )
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "metrics_server"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 9109
    assert payload["enabled"] is True


def test_api_manager_deterministic_smoke() -> None:
    payload = _run_and_load(
        "scripts/wave3/api_manager_smoke.py",
        Path("out/ops/api_manager_smoke/api_manager_smoke.json"),
    )
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "api_manager"
    assert payload["provider"] == "local"
    assert payload["api_mode"] == "offline"
    assert payload["max_clients"] == 2
