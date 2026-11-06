"""Offline tests for local-only remote Paper-only runner dry preflight CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "preflight_remote_runtime_runner_v0.py"

BOUNDARY_BOOL_FIELDS = (
    "remote_runtime_is_backend_not_lane",
    "lane_id_remote_runtime_forbidden",
    "lane_id_daemon_paper_24h_not_lane",
    "paper_only_v0",
    "scheduler_guard_required",
    "hold_binding_required",
    "bounded_adapter_approval_required",
    "primary_evidence_retention_required",
    "mandatory_durable_closeout_required",
    "registry_v1_required",
    "s3_after_finalize_only",
    "upload_does_not_authorize_runtime",
    "live_authority",
    "testnet_authority",
    "notion_authority",
    "market_dashboard_authority",
    "runner_implemented",
    "runtime_commands_called",
    "aws_cli_called",
    "rclone_called",
    "network_called",
    "s3_upload_called",
    "s3_download_called",
    "process_control_called",
    "mutation_called",
)


def _import_module():
    spec = importlib.util.spec_from_file_location("preflight_remote_runtime_runner_v0", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _minimal_kwargs(**overrides):
    base = {
        "dry_run": True,
        "no_network": True,
        "runtime_host": "remote",
        "runtime_backend": "ec2",
        "runtime_mode": "paper_only",
        "lane_id": "paper",
        "remote_run_id": "remote_paper_run_v0",
        "max_runtime_seconds": 3600,
        "evidence_root_type": "remote_durable",
        "evidence_transport": "local_only",
    }
    base.update(overrides)
    return base


@pytest.fixture
def mod():
    return _import_module()


def test_missing_dry_run_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(dry_run=False))
    assert result["status"] == "invalid"
    assert "missing_required_flag:dry_run" in result["reasons"]


def test_missing_no_network_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(no_network=False))
    assert result["status"] == "invalid"
    assert "missing_required_flag:no_network" in result["reasons"]


def test_valid_minimal_remote_paper_only_eligible(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs())
    assert result["status"] == "eligible"
    assert result["reasons"] == []


@pytest.mark.parametrize(
    "lane_id", ["remote_runtime", "daemon_paper_24h", "shadow", "testnet", "live"]
)
def test_forbidden_lane_ids_block(mod, lane_id: str) -> None:
    result = mod.run_preflight(**_minimal_kwargs(lane_id=lane_id))
    assert result["status"] == "blocked"
    assert result["reasons"]


def test_runtime_mode_other_than_paper_only_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(runtime_mode="paper_then_shadow"))
    assert result["status"] == "blocked"
    assert any("runtime_mode" in r for r in result["reasons"])


def test_invalid_backend_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(runtime_backend="laptop"))
    assert result["status"] == "blocked"
    assert any("runtime_backend" in r for r in result["reasons"])


@pytest.mark.parametrize("seconds", [0, -1, 86400 * 8])
def test_invalid_max_runtime_seconds_blocks(mod, seconds: int) -> None:
    result = mod.run_preflight(**_minimal_kwargs(max_runtime_seconds=seconds))
    assert result["status"] == "blocked"
    assert any("max_runtime_seconds" in r for r in result["reasons"])


def test_evidence_root_type_other_than_remote_durable_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(evidence_root_type="local_durable"))
    assert result["status"] == "blocked"


def test_forbidden_evidence_transport_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(evidence_transport="s3_export_after_finalize"))
    assert result["status"] == "blocked"


def test_registry_conflict_blocks(mod, tmp_path: Path) -> None:
    registry = {
        "schema": "peak_trade.generic_evidence_run_registry.v1",
        "runs": [
            {
                "run_id": "remote_paper_run_v0",
                "lane_id": "paper",
                "runtime_host": "local",
                "runtime_backend": "laptop",
                "runtime_mode": "paper_only",
                "evidence_root_type": "remote_durable",
                "evidence_transport": "local_only",
            }
        ],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    result = mod.run_preflight(**_minimal_kwargs(registry_json=path))
    assert result["status"] == "blocked"
    assert any("registry_conflict" in r for r in result["reasons"])


def test_s3_prefix_plan_conflict_blocks(mod, tmp_path: Path) -> None:
    plan = {
        "status": "proposed",
        "run_id": "other_run",
        "lane_id": "paper",
        "upload_called": False,
        "network_actions_called": False,
        "upload_does_not_authorize_runtime": True,
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    result = mod.run_preflight(
        **_minimal_kwargs(
            evidence_transport="s3_export_after_finalize_plan",
            s3_prefix_plan_json=plan_path,
        )
    )
    assert result["status"] == "blocked"
    assert any("s3_prefix_plan_run_id_mismatch" in r for r in result["reasons"])


def test_s3_transport_requires_prefix_plan_json(mod) -> None:
    result = mod.run_preflight(
        **_minimal_kwargs(evidence_transport="s3_export_after_finalize_plan")
    )
    assert result["status"] == "blocked"
    assert "s3_prefix_plan_json_required_for_s3_transport_plan" in result["reasons"]


def test_output_json_includes_boundary_fields(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs())
    for field in BOUNDARY_BOOL_FIELDS:
        assert field in result
    assert result["runner_implemented"] is False
    assert result["network_called"] is False
    assert result["live_authority"] is False


def test_main_eligible_exit_zero(mod, tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    rc = mod.main(
        [
            "--dry-run",
            "--no-network",
            "--runtime-host",
            "remote",
            "--runtime-backend",
            "ec2",
            "--runtime-mode",
            "paper_only",
            "--lane-id",
            "paper",
            "--remote-run-id",
            "remote_paper_run_v0",
            "--max-runtime-seconds",
            "3600",
            "--evidence-root-type",
            "remote_durable",
            "--evidence-transport",
            "local_only",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "eligible"


def test_approval_record_forbidden_live_blocks(mod, tmp_path: Path) -> None:
    record = tmp_path / "approval.md"
    record.write_text("LIVE_ALLOWED=true\n", encoding="utf-8")
    result = mod.run_preflight(**_minimal_kwargs(approval_record=record))
    assert result["status"] == "blocked"
    assert any("approval_record_forbidden" in r for r in result["reasons"])


def test_runtime_host_not_remote_blocks(mod) -> None:
    result = mod.run_preflight(**_minimal_kwargs(runtime_host="local"))
    assert result["status"] == "blocked"
