#!/usr/bin/env python3
"""Local-only remote Paper-only runner dry preflight (taxonomy §6a.0).

Non-network, non-executing: validates future remote runner command shape against §6a.0.
Does not start runners, schedulers, AWS hosts, SSH, systemd, or network actions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "peak_trade.remote_runtime_runner_preflight.v0"
PREFLIGHT_NAME = "preflight_remote_runtime_runner_v0"
REGISTRY_SCHEMA = "peak_trade.generic_evidence_run_registry.v1"

ALLOWED_RUNTIME_HOST = frozenset({"remote"})
ALLOWED_RUNTIME_BACKEND = frozenset({"ec2", "vps", "gha_runner", "data_node"})
ALLOWED_RUNTIME_MODE = frozenset({"paper_only"})
ALLOWED_LANE_ID = frozenset({"paper"})
FORBIDDEN_LANE_IDS = frozenset(
    {"remote_runtime", "daemon_paper_24h", "shadow", "testnet", "live", "live_production"}
)
ALLOWED_EVIDENCE_ROOT_TYPE = frozenset({"remote_durable"})
ALLOWED_EVIDENCE_TRANSPORT = frozenset({"local_only", "s3_export_after_finalize_plan"})
REGISTRY_EVIDENCE_TRANSPORT_MAP = {
    "local_only": "local_only",
    "s3_export_after_finalize_plan": "s3_export_after_finalize",
}

MAX_RUNTIME_SECONDS_MIN = 1
MAX_RUNTIME_SECONDS_CAP = 86400 * 7

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "LIVE_ALLOWED",
        "LIVE_AUTHORITY",
        "TESTNET_AUTHORITY",
        "TESTNET_ALLOWED",
        "BROKER_EXCHANGE_ALLOWED",
        "SHADOW_LANE_AUTHORIZED",
        "START_LIVE_NOW",
        "START_TESTNET_NOW",
        "NETWORK_EXECUTION_ENABLED",
        "AWS_CLI_ENABLED",
        "RCLONE_ENABLED",
        "S3_UPLOAD_ENABLED",
        "S3_DOWNLOAD_ENABLED",
    }
)

FORBIDDEN_SCHEDULER_GUARD_TRUE = frozenset(
    {
        "SCHEDULER_EXECUTION_AUTHORIZED",
        "LIVE_AUTHORITY",
        "TESTNET_AUTHORITY",
        "RUNTIME_COMMANDS_CALLED",
        "NETWORK_CALLED",
        "AWS_CLI_CALLED",
    }
)

S3_PLAN_NON_EXECUTING_BOOLS = (
    "network_actions_called",
    "aws_cli_called",
    "rclone_called",
    "upload_called",
    "download_called",
    "mutation_called",
)

SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _boundary_fields() -> dict[str, bool]:
    return {
        "remote_runtime_is_backend_not_lane": True,
        "lane_id_remote_runtime_forbidden": True,
        "lane_id_daemon_paper_24h_not_lane": True,
        "paper_only_v0": True,
        "scheduler_guard_required": True,
        "hold_binding_required": True,
        "bounded_adapter_approval_required": True,
        "primary_evidence_retention_required": True,
        "mandatory_durable_closeout_required": True,
        "registry_v1_required": True,
        "s3_after_finalize_only": True,
        "upload_does_not_authorize_runtime": True,
        "live_authority": False,
        "testnet_authority": False,
        "notion_authority": False,
        "market_dashboard_authority": False,
        "runner_implemented": False,
        "runtime_commands_called": False,
        "aws_cli_called": False,
        "rclone_called": False,
        "network_called": False,
        "s3_upload_called": False,
        "s3_download_called": False,
        "process_control_called": False,
        "mutation_called": False,
    }


def _base_result(*, dry_run: bool, no_network: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_name": PREFLIGHT_NAME,
        "status": "invalid",
        "reasons": [],
        "dry_run": dry_run,
        "no_network": no_network,
        "runtime_host": None,
        "runtime_backend": None,
        "runtime_mode": None,
        "lane_id": None,
        "remote_run_id": None,
        "max_runtime_seconds": None,
        "evidence_root_type": None,
        "evidence_transport": None,
        **_boundary_fields(),
    }


def _parse_machine_lines(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"{path.name}_missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, f"{path.name}_malformed"
    if not isinstance(payload, dict):
        return None, f"{path.name}_invalid_shape"
    return payload, None


def _find_registry_run(
    registry: dict[str, Any], run_id: str, lane_id: str
) -> dict[str, Any] | None:
    runs = registry.get("runs")
    if not isinstance(runs, list):
        return None
    for row in runs:
        if not isinstance(row, dict):
            continue
        if row.get("run_id") == run_id and row.get("lane_id") == lane_id:
            return row
    return None


def _registry_conflicts(
    record: dict[str, Any],
    *,
    runtime_host: str,
    runtime_backend: str,
    runtime_mode: str,
    evidence_root_type: str,
    evidence_transport: str,
) -> list[str]:
    reasons: list[str] = []
    checks = (
        ("runtime_host", runtime_host),
        ("runtime_backend", runtime_backend),
        ("runtime_mode", runtime_mode),
        ("evidence_root_type", evidence_root_type),
    )
    for field, expected in checks:
        actual = record.get(field)
        if actual is not None and str(actual) != expected:
            reasons.append(f"registry_conflict:{field}")
    reg_transport = record.get("evidence_transport", "local_only")
    mapped = REGISTRY_EVIDENCE_TRANSPORT_MAP.get(evidence_transport, evidence_transport)
    if reg_transport != mapped:
        reasons.append("registry_conflict:evidence_transport")
    if record.get("live_authority") is True:
        reasons.append("registry_conflict:live_authority")
    if record.get("testnet_authority") is True:
        reasons.append("registry_conflict:testnet_authority")
    return reasons


def _validate_s3_prefix_plan(
    plan: dict[str, Any],
    *,
    remote_run_id: str,
    lane_id: str,
) -> list[str]:
    reasons: list[str] = []
    for key in S3_PLAN_NON_EXECUTING_BOOLS:
        if plan.get(key) is True:
            reasons.append(f"s3_prefix_plan_forbidden:{key}")
    if plan.get("upload_does_not_authorize_runtime") is False:
        reasons.append("s3_prefix_plan_upload_must_not_authorize_runtime")
    if plan.get("s3_authority") is True:
        reasons.append("s3_prefix_plan_s3_authority_forbidden")
    plan_run = plan.get("run_id")
    plan_lane = plan.get("lane_id")
    if plan_run is not None and str(plan_run) != remote_run_id:
        reasons.append("s3_prefix_plan_run_id_mismatch")
    if plan_lane is not None and str(plan_lane) != lane_id:
        reasons.append("s3_prefix_plan_lane_id_mismatch")
    status = str(plan.get("status", ""))
    if status and status not in {"proposed", "blocked", "planning_only"}:
        reasons.append(f"s3_prefix_plan_unexpected_status:{status}")
    return reasons


def run_preflight(
    *,
    dry_run: bool,
    no_network: bool,
    runtime_host: str,
    runtime_backend: str,
    runtime_mode: str,
    lane_id: str,
    remote_run_id: str,
    max_runtime_seconds: int,
    evidence_root_type: str,
    evidence_transport: str,
    registry_json: Path | None = None,
    s3_prefix_plan_json: Path | None = None,
    approval_record: Path | None = None,
    scheduler_guard_json: Path | None = None,
) -> dict[str, Any]:
    result = _base_result(dry_run=dry_run, no_network=no_network)
    reasons: list[str] = result["reasons"]

    result.update(
        {
            "runtime_host": runtime_host,
            "runtime_backend": runtime_backend,
            "runtime_mode": runtime_mode,
            "lane_id": lane_id,
            "remote_run_id": remote_run_id,
            "max_runtime_seconds": max_runtime_seconds,
            "evidence_root_type": evidence_root_type,
            "evidence_transport": evidence_transport,
        }
    )

    if not dry_run:
        reasons.append("missing_required_flag:dry_run")
    if not no_network:
        reasons.append("missing_required_flag:no_network")
    if not dry_run or not no_network:
        result["status"] = "invalid"
        return result

    if lane_id in FORBIDDEN_LANE_IDS:
        reasons.append(f"forbidden_lane_id:{lane_id}")
    if lane_id not in ALLOWED_LANE_ID:
        reasons.append(f"lane_id_not_paper_v0:{lane_id}")
    if runtime_host not in ALLOWED_RUNTIME_HOST:
        reasons.append(f"runtime_host_must_be_remote:{runtime_host!r}")
    if runtime_backend not in ALLOWED_RUNTIME_BACKEND:
        reasons.append(f"invalid_runtime_backend:{runtime_backend!r}")
    if runtime_mode not in ALLOWED_RUNTIME_MODE:
        reasons.append(f"runtime_mode_must_be_paper_only:{runtime_mode!r}")
    if evidence_root_type not in ALLOWED_EVIDENCE_ROOT_TYPE:
        reasons.append(f"evidence_root_type_must_be_remote_durable:{evidence_root_type!r}")
    if evidence_transport not in ALLOWED_EVIDENCE_TRANSPORT:
        reasons.append(f"invalid_evidence_transport:{evidence_transport!r}")

    if not remote_run_id or not SAFE_RUN_ID.match(remote_run_id):
        reasons.append("invalid_remote_run_id")
    if max_runtime_seconds < MAX_RUNTIME_SECONDS_MIN:
        reasons.append("max_runtime_seconds_non_positive")
    if max_runtime_seconds > MAX_RUNTIME_SECONDS_CAP:
        reasons.append("max_runtime_seconds_unsafe")

    if approval_record is not None:
        if not approval_record.is_file():
            reasons.append("approval_record_missing")
        else:
            fields = _parse_machine_lines(approval_record.read_text(encoding="utf-8"))
            for key in FORBIDDEN_APPROVAL_TRUE:
                if fields.get(key, "").lower() == "true":
                    reasons.append(f"approval_record_forbidden:{key}")
            if fields.get("SHADOW_LANE_AUTHORIZED", "").lower() == "true":
                reasons.append("approval_record_shadow_enabled_by_default")

    if scheduler_guard_json is not None:
        guard, err = _load_json_file(scheduler_guard_json)
        if err:
            reasons.append(err)
        elif guard is not None:
            for key in FORBIDDEN_SCHEDULER_GUARD_TRUE:
                if guard.get(key) is True or str(guard.get(key, "")).lower() == "true":
                    reasons.append(f"scheduler_guard_forbidden:{key}")

    if registry_json is not None:
        registry, err = _load_json_file(registry_json)
        if err:
            reasons.append(err)
        elif registry is not None:
            schema = registry.get("schema")
            if schema is not None and schema != REGISTRY_SCHEMA:
                reasons.append(f"registry_schema_unsupported:{schema}")
            record = _find_registry_run(registry, remote_run_id, lane_id)
            if record is None:
                reasons.append("registry_run_not_found")
            else:
                reasons.extend(
                    _registry_conflicts(
                        record,
                        runtime_host=runtime_host,
                        runtime_backend=runtime_backend,
                        runtime_mode=runtime_mode,
                        evidence_root_type=evidence_root_type,
                        evidence_transport=evidence_transport,
                    )
                )

    if s3_prefix_plan_json is not None:
        plan, err = _load_json_file(s3_prefix_plan_json)
        if err:
            reasons.append(err)
        elif plan is not None:
            reasons.extend(
                _validate_s3_prefix_plan(plan, remote_run_id=remote_run_id, lane_id=lane_id)
            )
    elif evidence_transport == "s3_export_after_finalize_plan":
        reasons.append("s3_prefix_plan_json_required_for_s3_transport_plan")

    if reasons:
        if any(r.startswith("missing_required_flag:") for r in reasons) and len(reasons) == sum(
            1 for r in reasons if r.startswith("missing_required_flag:")
        ):
            result["status"] = "invalid"
        else:
            result["status"] = "blocked"
        return result

    result["status"] = "eligible"
    return result


def _exit_code_for_status(status: str) -> int:
    if status == "eligible":
        return 0
    if status == "blocked":
        return 1
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local-only remote Paper-only runner dry preflight (no network)."
    )
    parser.add_argument("--out", type=Path, help="Write JSON result to path (default: stdout)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required: preflight is dry-run only",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Required: forbid network actions in this preflight path",
    )
    parser.add_argument("--runtime-host", required=True)
    parser.add_argument("--runtime-backend", required=True)
    parser.add_argument("--runtime-mode", required=True)
    parser.add_argument("--lane-id", required=True)
    parser.add_argument("--remote-run-id", required=True)
    parser.add_argument("--max-runtime-seconds", required=True, type=int)
    parser.add_argument("--evidence-root-type", required=True)
    parser.add_argument("--evidence-transport", required=True)
    parser.add_argument("--registry-json", type=Path)
    parser.add_argument("--s3-prefix-plan-json", type=Path)
    parser.add_argument("--approval-record", type=Path)
    parser.add_argument("--scheduler-guard-json", type=Path)
    args = parser.parse_args(argv)

    payload = run_preflight(
        dry_run=args.dry_run,
        no_network=args.no_network,
        runtime_host=args.runtime_host,
        runtime_backend=args.runtime_backend,
        runtime_mode=args.runtime_mode,
        lane_id=args.lane_id,
        remote_run_id=args.remote_run_id,
        max_runtime_seconds=args.max_runtime_seconds,
        evidence_root_type=args.evidence_root_type,
        evidence_transport=args.evidence_transport,
        registry_json=args.registry_json,
        s3_prefix_plan_json=args.s3_prefix_plan_json,
        approval_record=args.approval_record,
        scheduler_guard_json=args.scheduler_guard_json,
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return _exit_code_for_status(str(payload["status"]))


if __name__ == "__main__":
    raise SystemExit(main())
