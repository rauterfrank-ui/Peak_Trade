"""Invariants for canonical PR-U required-checks reconciliation path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_pru_workflow_calls_canonical_reconciler_check() -> None:
    workflow = Path(".github/workflows/pru-required-checks-drift-detector.yml").read_text(
        encoding="utf-8"
    )
    assert "PR-U / Required Checks Reconciliation Check" in workflow
    assert "required-checks-reconciliation-check" in workflow
    assert "scripts/ops/reconcile_required_checks_branch_protection.py" in workflow
    assert "--check" in workflow
    assert "config/ci/required_status_checks.json" in workflow
    assert "scripts/ci/required_checks_drift_detector.py" not in workflow
    assert "GH_TOKEN: ${{ github.token }}" in workflow


def test_legacy_drift_detector_is_hard_retired() -> None:
    script = Path("scripts/ci/required_checks_drift_detector.py").read_text(encoding="utf-8")
    assert "retired and unsupported" in script
    assert "return 2" in script
    assert "subprocess.run(" not in script


def test_legacy_drift_detector_exit_code_is_nonzero_and_points_to_canonical() -> None:
    r = subprocess.run(
        [sys.executable, "scripts/ci/required_checks_drift_detector.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
        check=False,
    )
    assert r.returncode == 2
    assert "retired and unsupported" in r.stderr
    assert "reconcile_required_checks_branch_protection.py --check" in r.stderr
