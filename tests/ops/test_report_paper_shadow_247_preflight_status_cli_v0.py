"""CLI tests for the Paper/Shadow 24/7 preflight status reporter (read-only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)

try:
    import tomllib
except ImportError:
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"
PREFLIGHT_CONFIG = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"


def _assert_command_inventory_shape(payload: dict[str, object]) -> None:
    meta = tomllib.loads(PREFLIGHT_CONFIG.read_text(encoding="utf-8"))
    paper = [str(x) for x in meta["paper_jobs"]]
    shadow = [str(x) for x in meta["shadow_jobs"]]
    commands = payload["commands"]
    assert isinstance(commands, list)
    assert len(commands) == len(paper) + len(shadow)
    assert [c["name"] for c in commands] == paper + shadow
    assert [c["source"] for c in commands] == ["paper"] * len(paper) + ["shadow"] * len(shadow)

    by_name = {str(c["name"]): c for c in commands}
    preflight = by_name["paper_shadow_247_paper_only_preflight_status_v0"]
    assert preflight["found"] is True
    assert preflight["enabled"] is True
    assert preflight["command"] == "python"
    safety_pf = preflight["safety_classification"]
    assert isinstance(safety_pf, dict)
    assert safety_pf["paper_only"] is True
    assert safety_pf["dry_run_visible"] is True
    assert safety_pf["paper_runtime_job"] is None
    assert safety_pf["enabled"] is True
    assert safety_pf["disabled_by_default"] is False
    assert safety_pf["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_pf["non_authorizing"] is True
    args_pf = preflight["args"]
    assert isinstance(args_pf, dict)
    assert args_pf["script"] == "scripts/ops/report_paper_shadow_247_preflight_status.py"

    min_job = by_name["paper_shadow_247_paper_only_runtime_min_v0"]
    assert min_job["found"] is True
    assert min_job["enabled"] is False
    assert min_job["command"] == "python"
    assert min_job["timeout_seconds"] == 600
    safety_min = min_job["safety_classification"]
    assert isinstance(safety_min, dict)
    assert safety_min["paper_only"] is True
    assert safety_min["dry_run_visible"] is True
    assert safety_min["paper_runtime_job"] is True
    assert safety_min["enabled"] is False
    assert safety_min["disabled_by_default"] is True
    assert safety_min["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_min["non_authorizing"] is True
    args_min = min_job["args"]
    assert isinstance(args_min, dict)
    assert args_min["script"] == "scripts/aiops/run_paper_trading_session.py"
    assert args_min["spec"] == "tests/fixtures/p7/paper_run_min_v0.json"
    assert args_min["outdir"] == "out/paper_shadow_247/runtime/min/__DRY_RUN_PLACEHOLDER__"

    high_job = by_name["paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"]
    assert high_job["found"] is True
    assert high_job["enabled"] is False
    assert high_job["command"] == "python"
    assert high_job["timeout_seconds"] == 600
    safety_high = high_job["safety_classification"]
    assert isinstance(safety_high, dict)
    assert safety_high["paper_only"] is True
    assert safety_high["dry_run_visible"] is True
    assert safety_high["paper_runtime_job"] is True
    assert safety_high["enabled"] is False
    assert safety_high["disabled_by_default"] is True
    assert safety_high["authorization_flags"] == {
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
    }
    assert safety_high["non_authorizing"] is True
    args_high = high_job["args"]
    assert isinstance(args_high, dict)
    assert args_high["script"] == "scripts/aiops/run_paper_trading_session.py"
    assert args_high["spec"] == "tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json"
    assert (
        args_high["outdir"]
        == "out/paper_shadow_247/runtime/high_vol_no_trade/__DRY_RUN_PLACEHOLDER__"
    )

    assert any(str(c["name"]).startswith("paper_runner_") and c["found"] is False for c in commands)
    for c in commands:
        if str(c["name"]).startswith("paper_runner_") and c["found"] is False:
            assert "safety_classification" not in c
            break
    shadow_entry = by_name["p7_shadow_high_vol_no_trade_runner_manual_v0"]
    assert shadow_entry["source"] == "shadow"
    assert shadow_entry["found"] is False
    assert "safety_classification" not in shadow_entry


def _assert_operator_moment_snapshot_v0(payload: dict[str, object]) -> None:
    moment = payload["operator_moment_snapshot_v0"]
    assert isinstance(moment, dict)
    assert moment["schema_version"] == "paper_shadow_247_operator_moment_snapshot.v0"
    assert moment["non_authorizing"] is True
    assert moment["does_not_activate_runtime"] is True
    mirror = moment["mirror_top_level"]
    assert isinstance(mirror, dict)
    assert mirror["status"] == "BLOCKED"
    assert mirror["activation_authorized"] is False
    assert mirror["daemon_activation_authorized"] is False
    assert mirror["paper_runtime_authorized"] is False
    assert mirror["shadow_runtime_authorized"] is False
    assert mirror["testnet_authorized"] is False
    assert mirror["live_authorized"] is False
    assert mirror["broker_authorized"] is False
    assert mirror["exchange_authorized"] is False
    assert mirror["order_submission_authorized"] is False
    assert mirror["scheduler_execution_authorized"] is False
    assert mirror["dry_run_only"] is True
    assert moment["dry_activation_readiness_ready"] is False
    summary = moment["command_inventory_summary"]
    assert isinstance(summary, dict)
    commands = payload["commands"]
    assert isinstance(commands, list)
    assert summary["commands_total"] == len(commands)
    assert summary["found_true"] + summary["found_false"] == summary["commands_total"]
    assert (
        summary["enabled_true"] + summary["enabled_false"] + summary["enabled_unset"]
        == summary["commands_total"]
    )
    assert summary["paper_runtime_jobs_scheduled_disabled"] == 2
    stop = moment["stop_signal_snapshot"]
    assert isinstance(stop, dict)
    assert stop["contract"] == "operator_stop_signal_snapshot_v1"
    assert isinstance(stop.get("summary"), str)


def _run_json() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


def test_build_paper_shadow_247_preflight_status_is_blocked_and_non_authorizing() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert payload["contract"] == "paper_shadow_247_preflight_status_v0"
    assert payload["schema_version"] == 0
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["daemon_activation_authorized"] is False
    assert payload["paper_runtime_authorized"] is False
    assert payload["shadow_runtime_authorized"] is False
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["broker_authorized"] is False
    assert payload["exchange_authorized"] is False
    assert payload["order_submission_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    assert payload["dry_run_only"] is True
    assert payload["canonical_owner"] == "ops-paper-shadow-247-readiness"
    assert payload["paper_jobs"]
    assert payload["shadow_jobs"]
    _assert_command_inventory_shape(payload)
    assert payload["output_paths"]
    assert isinstance(payload["stop_command"], str)
    assert payload["stop_command"]
    assert isinstance(payload["emergency_stop_command"], str)
    assert payload["emergency_stop_command"]
    assert payload["risk_flags"] == {
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "orders": False,
        "network": False,
    }
    assert payload["blockers"] == []
    assert payload["status_reasons"] == []
    assert "operator_moment_snapshot_v0" in payload["notes"]
    _assert_operator_moment_snapshot_v0(payload)


def test_build_paper_shadow_247_preflight_status_reuses_existing_contract_surfaces() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert all(payload["required_files"].values())
    assert payload["contract_markers"]["contract_doc_exists"] is True
    assert payload["contract_markers"]["contract_states_blocked"] is True
    assert payload["contract_markers"]["contract_mentions_stop"] is True
    assert payload["contract_markers"]["contract_non_authority"] is True
    assert payload["contract_markers"]["scheduler_doc_links_contract"] is True
    assert payload["contract_markers"]["scheduler_config_has_direct_247_job"] is True


def test_cli_json_output_is_json_native_and_does_not_execute_scheduler() -> None:
    payload = _run_json()

    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["dry_run_command"].endswith("--dry-run --once --verbose")
    assert "does_not_run_scheduler" in payload["notes"]
    assert "does_not_start_daemon" in payload["notes"]
    assert "scheduler_command_inventory_v0" in payload["notes"]
    assert "scheduler_command_safety_classification_v0" in payload["notes"]
    assert "operator_moment_snapshot_v0" in payload["notes"]
    _assert_command_inventory_shape(payload)
    _assert_operator_moment_snapshot_v0(payload)


def test_cli_human_output_is_bounded_status_only() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "status=BLOCKED",
        "activation_authorized=false",
        "dry_run_only=true",
    ]


def test_paper_shadow_247_preflight_metadata_config_is_materialized() -> None:
    config_path = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"

    assert config_path.exists()
    text = config_path.read_text(encoding="utf-8")

    assert 'schema_version = "paper_shadow_247_preflight.v0"' in text
    assert "canonical_owner" in text
    assert "paper_jobs" in text
    assert "shadow_jobs" in text
    assert "output_paths" in text
    assert "stop_command" in text
    assert "emergency_stop_command" in text
    assert "activation_authorized = false" in text
    assert "daemon_activation_authorized = false" in text
    assert "scheduler_execution_authorized = false" in text


def test_paper_shadow_247_preflight_metadata_removes_missing_field_blockers() -> None:
    payload = _run_json()

    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["daemon_activation_authorized"] is False
    assert payload["scheduler_execution_authorized"] is False
    assert payload["paper_runtime_authorized"] is False
    assert payload["shadow_runtime_authorized"] is False

    assert payload["canonical_owner"] == "ops-paper-shadow-247-readiness"
    assert payload["paper_jobs"]
    assert payload["shadow_jobs"]
    assert payload["output_paths"]
    assert payload["stop_command"]
    assert payload["emergency_stop_command"]

    status_reasons = set(payload.get("status_reasons", []))
    blockers = set(payload.get("blockers", []))

    for removed in (
        "canonical_owner_missing",
        "paper_shadow_job_set_missing",
        "output_paths_missing",
        "stop_commands_missing",
    ):
        assert removed not in status_reasons
        assert removed not in blockers

    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert payload[key] is False


def test_paper_shadow_247_preflight_reports_dry_activation_readiness_without_authorization() -> (
    None
):
    payload = _run_json()
    readiness = payload["dry_activation_readiness"]

    assert readiness["schema_version"] == "paper_shadow_247_dry_activation_readiness.v0"
    assert readiness["ready"] is False
    assert readiness["mode"] == "paper_only_dry_activation_readiness"
    assert readiness["dry_run_only"] is True
    assert readiness["decision"] == "BLOCKED_NON_AUTHORIZING_READINESS_ONLY"

    assert readiness["operator_command"] == payload["dry_run_command"]
    assert readiness["stop_command"] == payload["stop_command"]
    assert readiness["emergency_stop_command"] == payload["emergency_stop_command"]

    assert readiness["checks"] == {
        "metadata_ready": True,
        "authorization_flags_false": True,
        "stop_controls_declared": True,
        "output_paths_declared": True,
        "paper_jobs_declared": True,
        "shadow_jobs_declared": True,
    }

    for key in (
        "activation_authorized",
        "daemon_activation_authorized",
        "scheduler_execution_authorized",
        "paper_runtime_authorized",
        "shadow_runtime_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert payload[key] is False
