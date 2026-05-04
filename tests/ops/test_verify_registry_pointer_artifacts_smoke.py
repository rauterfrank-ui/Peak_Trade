"""Smoke tests for scripts/ops/verify_registry_pointer_artifacts.py (NO-LIVE)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "verify_registry_pointer_artifacts.py"


def test_verify_registry_pointer_artifacts_help_lists_no_live() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    # argparse may wrap the description across lines (e.g. "NO-\nLIVE")
    assert "NO-LIVE" in p.stdout.replace("\n", "")


def test_verify_registry_pointer_artifacts_main_returns_1_missing_pointer(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import verify_registry_pointer_artifacts as v  # noqa: E402

    missing = tmp_path / "missing.pointer"
    code = v.main([str(missing)])
    assert code == 1


def _run_script_with_out_base(pointer: Path, out_base: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            str(pointer),
            "--out-base",
            str(out_base),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


def _write_valid_telemetry_summary(path: Path) -> None:
    payload = {
        "policy": {
            "action": "NO_TRADE",
            "reason_codes": ["OPERATOR_HOLD"],
        },
        "source": "evidence_manifest",
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_invalid_fallback_reason_telemetry_summary(path: Path) -> None:
    payload = {
        "policy": {
            "action": "NO_TRADE",
            "reason_codes": ["AUDIT_MANIFEST_NO_DECISION_CONTEXT"],
        },
        "source": "evidence_manifest",
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_verify_registry_pointer_artifacts_offline_success_with_valid_telemetry(
    tmp_path: Path,
) -> None:
    run_id = "contract_run_ok_001"
    pointer = tmp_path / "fixture.pointer"
    pointer.write_text(f"run_id={run_id}\n", encoding="utf-8")
    out_base = tmp_path / "gh_runs"
    artifacts = out_base / run_id
    artifacts.mkdir(parents=True)
    _write_valid_telemetry_summary(artifacts / "telemetry_summary.json")

    proc = _run_script_with_out_base(pointer, out_base)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "OK: 1 telemetry_summary.json validated" in proc.stdout


def test_verify_registry_pointer_artifacts_telemetry_invariant_violation_exit_3(
    tmp_path: Path,
) -> None:
    run_id = "contract_run_fail_001"
    pointer = tmp_path / "fixture.pointer"
    pointer.write_text(f"run_id={run_id}\n", encoding="utf-8")
    out_base = tmp_path / "gh_runs"
    artifacts = out_base / run_id
    artifacts.mkdir(parents=True)
    _write_invalid_fallback_reason_telemetry_summary(artifacts / "telemetry_summary.json")

    proc = _run_script_with_out_base(pointer, out_base)
    assert proc.returncode == 3
    assert "FAIL: telemetry invariants violated" in proc.stderr
    assert "fallback code present in reason_codes" in proc.stderr
