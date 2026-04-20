"""Tests for scripts/ops/pilot_go_no_go_eval_v1.py — Pilot Go/No-Go checklist evaluation."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"


def test_script_exists() -> None:
    """Script file exists."""
    assert SCRIPT.is_file()


def test_script_runs_with_repo_root(tmp_path: Path) -> None:
    """Script runs with --repo-root and produces verdict."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1, 2), f"stderr: {r.stderr}"
    assert "verdict=" in r.stdout or "verdict" in r.stdout


def test_script_json_output(tmp_path: Path) -> None:
    """Script --json produces valid JSON with contract and rows."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1, 2)
    data = json.loads(r.stdout)
    assert data["contract"] == "pilot_go_no_go_eval_v1"
    assert data["verdict"] in ("NO_GO", "CONDITIONAL", "GO_FOR_NEXT_PHASE_ONLY")
    assert "rows" in data
    assert len(data["rows"]) == 11
    for row in data["rows"]:
        assert "row" in row
        assert "area" in row
        assert row["status"] in ("PASS", "FAIL", "UNKNOWN")


def test_evaluate_function_importable() -> None:
    """evaluate() can be imported and called with payload."""
    # Import via running the module's namespace
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pilot_go_no_go_eval_v1",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {
        "policy_state": {
            "enabled": False,
            "armed": False,
            "blocked": True,
            "kill_switch_active": False,
        },
        "guard_state": {"treasury_separation": "enforced"},
        "exposure_state": {"caps_configured": []},
        "stale_state": {"summary": "ok"},
        "evidence_state": {"summary": "ok"},
        "dependencies_state": {"summary": "unknown"},
        "human_supervision_state": {"status": "operator_supervised"},
        "incident_state": {"requires_operator_attention": True},
    }
    result = mod.evaluate(payload)
    assert result["verdict"] == "NO_GO"  # caps_configured empty -> row 5 FAIL
    assert any(r["row"] == 5 and r["status"] == "FAIL" for r in result["rows"])


def test_evaluate_all_pass_verdict() -> None:
    """When all rows PASS, verdict is GO_FOR_NEXT_PHASE_ONLY."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pilot_go_no_go_eval_v1",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {
        "policy_state": {
            "enabled": True,
            "armed": True,
            "dry_run": False,
            "confirm_token_required": True,
            "blocked": False,
            "action": "TRADE_READY",
            "kill_switch_active": False,
        },
        "guard_state": {"treasury_separation": "enforced"},
        "exposure_state": {
            "caps_configured": [{"limit_id": "max_total_exposure", "cap_value": 1000}]
        },
        "stale_state": {"summary": "ok"},
        "evidence_state": {"summary": "ok"},
        "dependencies_state": {"summary": "ok"},
        "human_supervision_state": {"status": "operator_supervised"},
        "incident_state": {"requires_operator_attention": False},
    }
    result = mod.evaluate(payload)
    assert result["verdict"] == "GO_FOR_NEXT_PHASE_ONLY"
    assert all(r["status"] == "PASS" for r in result["rows"])


def test_evaluate_trade_ready_with_dry_run_true_is_no_go() -> None:
    """TRADE_READY while dry_run=True is inconsistent → policy row FAIL → NO_GO."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pilot_go_no_go_eval_v1",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {
        "policy_state": {
            "enabled": True,
            "armed": True,
            "dry_run": True,
            "confirm_token_required": True,
            "blocked": False,
            "action": "TRADE_READY",
            "kill_switch_active": False,
        },
        "guard_state": {"treasury_separation": "enforced"},
        "exposure_state": {
            "caps_configured": [{"limit_id": "max_total_exposure", "cap_value": 1000}]
        },
        "stale_state": {"summary": "ok"},
        "evidence_state": {"summary": "ok"},
        "dependencies_state": {"summary": "ok"},
        "human_supervision_state": {"status": "operator_supervised"},
        "incident_state": {"requires_operator_attention": False},
    }
    result = mod.evaluate(payload)
    assert result["verdict"] == "NO_GO"
    assert any(r["row"] == 3 and r["status"] == "FAIL" for r in result["rows"])


def test_evaluate_safety_gates_reject_non_bool_fields() -> None:
    """Row 1 requires real booleans, not stringly-typed flags."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pilot_go_no_go_eval_v1",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {
        "policy_state": {
            "enabled": "true",
            "armed": True,
            "dry_run": False,
            "confirm_token_required": True,
            "blocked": False,
            "action": "TRADE_READY",
            "kill_switch_active": False,
        },
        "guard_state": {"treasury_separation": "enforced"},
        "exposure_state": {
            "caps_configured": [{"limit_id": "max_total_exposure", "cap_value": 1000}]
        },
        "stale_state": {"summary": "ok"},
        "evidence_state": {"summary": "ok"},
        "dependencies_state": {"summary": "ok"},
        "human_supervision_state": {"status": "operator_supervised"},
        "incident_state": {"requires_operator_attention": False},
    }
    result = mod.evaluate(payload)
    assert any(r["row"] == 1 and r["status"] == "UNKNOWN" for r in result["rows"])
