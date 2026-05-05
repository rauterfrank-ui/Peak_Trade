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
    assert payload["scheduler_execution_authorized"] is False
    assert payload["dry_run_only"] is True
    assert payload["paper_jobs"] == []
    assert payload["shadow_jobs"] == []
    assert payload["commands"] == []
    assert payload["output_paths"] == []
    assert payload["stop_command"] is None
    assert payload["emergency_stop_command"] is None
    assert payload["risk_flags"] == {
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "orders": False,
        "network": False,
    }


def test_build_paper_shadow_247_preflight_status_reuses_existing_contract_surfaces() -> None:
    payload = build_paper_shadow_247_preflight_status(REPO_ROOT)

    assert all(payload["required_files"].values())
    assert payload["contract_markers"]["contract_doc_exists"] is True
    assert payload["contract_markers"]["contract_states_blocked"] is True
    assert payload["contract_markers"]["contract_mentions_stop"] is True
    assert payload["contract_markers"]["contract_non_authority"] is True
    assert payload["contract_markers"]["scheduler_doc_links_contract"] is True
    assert payload["contract_markers"]["scheduler_config_has_direct_247_job"] is False
    assert "canonical_owner_missing" in payload["blockers"]
    assert "paper_shadow_job_set_missing" in payload["blockers"]


def test_cli_json_output_is_json_native_and_does_not_execute_scheduler() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
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
