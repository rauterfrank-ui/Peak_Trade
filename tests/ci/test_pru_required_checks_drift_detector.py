"""Invariants for PR-U drift engine cutover to canonical reconciler."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_pru_workflow_calls_canonical_reconciler_check() -> None:
    workflow = Path(".github/workflows/pru-required-checks-drift-detector.yml").read_text(
        encoding="utf-8"
    )
    assert "scripts/ops/reconcile_required_checks_branch_protection.py" in workflow
    assert "--check" in workflow
    assert "config/ci/required_status_checks.json" in workflow
    assert "scripts/ci/required_checks_drift_detector.py" not in workflow
    assert "GH_TOKEN: ${{ github.token }}" in workflow


def test_legacy_drift_detector_is_redirect_only() -> None:
    script = Path("scripts/ci/required_checks_drift_detector.py").read_text(encoding="utf-8")
    assert "DEPRECATED:" in script
    assert "reconcile_required_checks_branch_protection.py --check" in script
    assert "yaml.safe_load" not in script
    assert "load_effective_required_contexts" not in script


def test_legacy_drift_detector_help_mentions_deprecation() -> None:
    r = subprocess.run(
        [sys.executable, "scripts/ci/required_checks_drift_detector.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
        check=False,
    )
    assert r.returncode == 0
    assert "Deprecated compatibility wrapper" in r.stdout
