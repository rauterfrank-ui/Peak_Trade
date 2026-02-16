from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_p95_smoke_script_exists_and_is_executable() -> None:
    p = Path("scripts/ops/p95_ops_health_meta_gate_v1.sh")
    assert p.exists()
    assert os.access(p, os.X_OK)


def test_p95_usage_is_not_needed_for_smoke() -> None:
    # We do not run the gate in CI (launchd not present).
    # Smoke just ensures script is syntactically valid.
    p = Path("scripts/ops/p95_ops_health_meta_gate_v1.sh")
    subprocess.run(["bash", "-n", str(p)], check=True)
