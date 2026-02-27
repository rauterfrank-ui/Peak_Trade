from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_policy_audit_cli_help_smoke() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    result = subprocess.run(
        [sys.executable, "src/ops/p50/ai_model_policy_cli_v1.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={**__import__("os").environ, "PYTHONPATH": str(root)},
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_switch_layer_smoke_wrapper_runs() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    result = subprocess.run(
        [sys.executable, "scripts/ai/switch_layer_smoke.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
    )
    assert result.returncode == 0
    assert "SMOKE_OK" in result.stdout

    out_file = root / "out/ops/switch_layer_smoke/switch_layer_smoke.json"
    assert out_file.exists()
