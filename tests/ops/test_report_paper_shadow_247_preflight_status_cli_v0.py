"""CLI tests for the Paper/Shadow 24/7 preflight status reporter (read-only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"


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
    assert payload["commands"] == []
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


def test_build_paper_shadow_247_preflight_status_reuses_existing_contract_surfaces() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert all(payload["required_files"].values())
    assert payload["contract_markers"]["contract_doc_exists"] is True
    assert payload["contract_markers"]["contract_states_blocked"] is True
    assert payload["contract_markers"]["contract_mentions_stop"] is True
    assert payload["contract_markers"]["contract_non_authority"] is True
    assert payload["contract_markers"]["scheduler_doc_links_contract"] is True
    assert payload["contract_markers"]["scheduler_config_has_direct_247_job"] is False


def test_cli_json_output_is_json_native_and_does_not_execute_scheduler() -> None:
    payload = _run_json()

    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False
    assert payload["dry_run_command"].endswith("--dry-run --once --verbose")
    assert "does_not_run_scheduler" in payload["notes"]
    assert "does_not_start_daemon" in payload["notes"]


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
