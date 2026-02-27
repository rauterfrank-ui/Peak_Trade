from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_and_check(script: str, out_file: Path, component: str) -> None:
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

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == component


def test_model_registry_loader_smoke() -> None:
    _run_and_check(
        "scripts/wave3/model_registry_loader_smoke.py",
        Path("out/ops/model_registry_loader_smoke/model_registry_loader_smoke.json"),
        "model_registry_loader",
    )


def test_metrics_server_smoke() -> None:
    _run_and_check(
        "scripts/wave3/metrics_server_smoke.py",
        Path("out/ops/metrics_server_smoke/metrics_server_smoke.json"),
        "metrics_server",
    )


def test_api_manager_smoke() -> None:
    _run_and_check(
        "scripts/wave3/api_manager_smoke.py",
        Path("out/ops/api_manager_smoke/api_manager_smoke.json"),
        "api_manager",
    )
