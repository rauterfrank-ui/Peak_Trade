#!/usr/bin/env python3
"""Report the current Paper/Shadow 24/7 preflight status.

This reporter is intentionally read-only and non-authorizing. It does not run
the scheduler, does not start daemons, and does not activate Paper, Shadow,
Testnet, or Live runtime paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CONTRACT = "paper_shadow_247_preflight_status_v0"
CONTRACT_DOC = "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
INCIDENT_STOP_DOC = "docs/ops/runbooks/incident_stop_freeze_rollback.md"
SCHEDULER_DOC = "docs/SCHEDULER_DAEMON.md"
SCHEDULER_CONFIG = "config/scheduler/jobs.toml"
PAPER_SHADOW_247_PREFLIGHT_METADATA = Path("config") / "ops" / "paper_shadow_247_preflight.toml"
DRY_RUN_COMMAND = (
    "python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose"
)
JOB_AUTHORIZATION_FLAGS = (
    "testnet_authorized",
    "live_authorized",
    "broker_authorized",
    "exchange_authorized",
    "order_submission_authorized",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_paper_shadow_247_preflight_metadata(root: Path) -> dict[str, Any]:
    cfg = root / PAPER_SHADOW_247_PREFLIGHT_METADATA
    if not cfg.is_file():
        return {}
    return tomllib.loads(cfg.read_text(encoding="utf-8"))


def _load_scheduler_jobs_by_name(root: Path) -> dict[str, dict[str, Any]]:
    path = root / SCHEDULER_CONFIG
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    jobs_raw = data.get("job", [])
    if not isinstance(jobs_raw, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in jobs_raw:
        if not isinstance(item, dict):
            continue
        name_any = item.get("name")
        if isinstance(name_any, str):
            out[name_any] = item
    return out


def _job_bool_or_none(job: dict[str, Any], key: str) -> bool | None:
    value = job.get(key)
    return value if isinstance(value, bool) else None


def _build_job_safety_classification(job: dict[str, Any]) -> dict[str, Any]:
    enabled = _job_bool_or_none(job, "enabled")
    authorization_flags = {
        key: _job_bool_or_none(job, key) if key in job else None for key in JOB_AUTHORIZATION_FLAGS
    }
    non_authorizing = (
        all(value is False for value in authorization_flags.values())
        if all(value is not None for value in authorization_flags.values())
        else None
    )

    return {
        "paper_only": _job_bool_or_none(job, "paper_only") if "paper_only" in job else None,
        "dry_run_visible": _job_bool_or_none(job, "dry_run_visible")
        if "dry_run_visible" in job
        else None,
        "paper_runtime_job": _job_bool_or_none(job, "paper_runtime_job")
        if "paper_runtime_job" in job
        else None,
        "enabled": enabled,
        "disabled_by_default": (enabled is False) if enabled is not None else None,
        "authorization_flags": authorization_flags,
        "non_authorizing": non_authorizing,
    }


def _job_to_command_inventory_entry(
    job_name: str,
    source: str,
    job: dict[str, Any] | None,
) -> dict[str, Any]:
    if job is None:
        return {
            "name": job_name,
            "source": source,
            "found": False,
            "command": None,
            "args": None,
            "enabled": None,
            "schedule_type": None,
            "tags": None,
            "timeout_seconds": None,
        }

    tags_raw = job.get("tags")
    tags_out: list[Any] | None
    if isinstance(tags_raw, list):
        tags_out = list(tags_raw)
    else:
        tags_out = None

    args_raw = job.get("args")
    args_out: dict[str, Any] | None
    if isinstance(args_raw, dict):
        args_out = {str(k): v for k, v in args_raw.items()}
    else:
        args_out = None

    return {
        "name": job_name,
        "source": source,
        "found": True,
        "command": job["command"] if isinstance(job.get("command"), str) else None,
        "args": args_out,
        "enabled": job.get("enabled") if "enabled" in job else None,
        "schedule_type": job.get("schedule_type")
        if isinstance(job.get("schedule_type"), str)
        else None,
        "tags": tags_out,
        "timeout_seconds": job.get("timeout_seconds")
        if isinstance(job.get("timeout_seconds"), int)
        else None,
        "safety_classification": _build_job_safety_classification(job),
    }


def _build_scheduler_command_inventory(
    paper_jobs: list[str],
    shadow_jobs: list[str],
    jobs_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for name in paper_jobs:
        commands.append(_job_to_command_inventory_entry(name, "paper", jobs_by_name.get(name)))
    for name in shadow_jobs:
        commands.append(_job_to_command_inventory_entry(name, "shadow", jobs_by_name.get(name)))
    return commands


def _build_dry_activation_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    """Return non-authorizing readiness details for a later manual paper-only dry activation."""

    metadata_ready = bool(
        payload.get("canonical_owner")
        and payload.get("paper_jobs")
        and payload.get("output_paths")
        and payload.get("stop_command")
        and payload.get("emergency_stop_command")
    )
    authorization_flags_false = all(
        payload.get(key) is False
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
        )
    )
    stop_controls_declared = bool(
        payload.get("stop_command") and payload.get("emergency_stop_command")
    )
    output_paths_declared = bool(payload.get("output_paths"))

    checks = {
        "metadata_ready": metadata_ready,
        "authorization_flags_false": authorization_flags_false,
        "stop_controls_declared": stop_controls_declared,
        "output_paths_declared": output_paths_declared,
        "paper_jobs_declared": bool(payload.get("paper_jobs")),
        "shadow_jobs_declared": bool(payload.get("shadow_jobs")),
    }

    return {
        "schema_version": "paper_shadow_247_dry_activation_readiness.v0",
        "ready": False,
        "mode": "paper_only_dry_activation_readiness",
        "dry_run_only": True,
        "checks": checks,
        "operator_command": payload.get("dry_run_command"),
        "stop_command": payload.get("stop_command"),
        "emergency_stop_command": payload.get("emergency_stop_command"),
        "decision": "BLOCKED_NON_AUTHORIZING_READINESS_ONLY",
    }


def _build_stop_signal_snapshot_for_repo(
    repo_root: Path,
    operator_decision_record: Path | None = None,
) -> dict[str, Any]:
    """Resolve `build_stop_signal_snapshot` when this module is CLI-invoked from `scripts/ops/`."""

    root_s = str(repo_root.resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    from scripts.ops.snapshot_operator_stop_signals import build_stop_signal_snapshot

    return build_stop_signal_snapshot(repo_root, operator_decision_record=operator_decision_record)


def _command_inventory_summary(commands: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(commands)
    found_true = sum(1 for c in commands if c.get("found") is True)
    found_false = sum(1 for c in commands if c.get("found") is False)
    enabled_true = sum(1 for c in commands if c.get("enabled") is True)
    enabled_false = sum(1 for c in commands if c.get("enabled") is False)
    enabled_unset = sum(1 for c in commands if c.get("enabled") is None)
    paper_runtime_disabled = 0
    for c in commands:
        sc = c.get("safety_classification")
        if (
            isinstance(sc, dict)
            and sc.get("paper_runtime_job") is True
            and c.get("enabled") is False
        ):
            paper_runtime_disabled += 1
    return {
        "commands_total": total,
        "found_true": found_true,
        "found_false": found_false,
        "enabled_true": enabled_true,
        "enabled_false": enabled_false,
        "enabled_unset": enabled_unset,
        "paper_runtime_jobs_scheduled_disabled": paper_runtime_disabled,
    }


def _build_hold_context_v0() -> dict[str, Any]:
    """Explicit unknown-HOLD audit projection: non-authorizing, JSON-native, deterministic."""

    return {
        "schema_version": "unknown_hold_context.v0",
        "current_state": "HOLD_NO_PAPER_RUN",
        "operator_classification": "unknown",
        "go_live_next_step": "blocked",
        "non_authorizing": True,
        "reason": (
            "OPERATOR_CLASSIFICATION=unknown is not a clearance state; HOLD_NO_PAPER_RUN "
            "remains active until incident-stop and governance boundaries are explicitly resolved."
        ),
        "canonical_doc_refs": [
            INCIDENT_STOP_DOC,
            SCHEDULER_DOC,
            CONTRACT_DOC,
        ],
        "progression_authorization": {
            "activation_authorized": False,
            "daemon_activation_authorized": False,
            "scheduler_execution_authorized": False,
            "paper_runtime_authorized": False,
            "shadow_runtime_authorized": False,
            "testnet_authorized": False,
            "live_authorized": False,
            "broker_authorized": False,
            "exchange_authorized": False,
            "order_submission_authorized": False,
        },
    }


def _build_operator_moment_snapshot_v0(
    payload: dict[str, Any],
    repo_root: Path,
    operator_decision_record: Path | None = None,
) -> dict[str, Any]:
    """Derived, non-authorizing operator snapshot: preflight mirror + inventory stats + stop signals."""

    commands_raw = payload.get("commands")
    commands: list[dict[str, Any]] = commands_raw if isinstance(commands_raw, list) else []
    dry = payload.get("dry_activation_readiness")
    dry_ready = dry.get("ready") if isinstance(dry, dict) else None

    stop_snapshot = _build_stop_signal_snapshot_for_repo(repo_root, operator_decision_record)

    return {
        "schema_version": "paper_shadow_247_operator_moment_snapshot.v0",
        "non_authorizing": True,
        "does_not_activate_runtime": True,
        "mirror_top_level": {
            "status": payload.get("status"),
            "activation_authorized": payload.get("activation_authorized"),
            "daemon_activation_authorized": payload.get("daemon_activation_authorized"),
            "paper_runtime_authorized": payload.get("paper_runtime_authorized"),
            "shadow_runtime_authorized": payload.get("shadow_runtime_authorized"),
            "testnet_authorized": payload.get("testnet_authorized"),
            "live_authorized": payload.get("live_authorized"),
            "broker_authorized": payload.get("broker_authorized"),
            "exchange_authorized": payload.get("exchange_authorized"),
            "order_submission_authorized": payload.get("order_submission_authorized"),
            "scheduler_execution_authorized": payload.get("scheduler_execution_authorized"),
            "dry_run_only": payload.get("dry_run_only"),
        },
        "dry_activation_readiness_ready": dry_ready,
        "hold_context_v0": payload.get("hold_context_v0"),
        "command_inventory_summary": _command_inventory_summary(commands),
        "stop_signal_snapshot": stop_snapshot,
    }


def build_paper_shadow_247_preflight_status(
    repo_root: Path | None = None,
    operator_decision_record: Path | None = None,
    durable_run_outroot: Path | None = None,
    expected_run_id: str | None = None,
) -> dict[str, Any]:
    root = (repo_root or _repo_root()).resolve()
    op_rec: Path | None = None
    if operator_decision_record is not None:
        root_s = str(root)
        if root_s not in sys.path:
            sys.path.insert(0, root_s)
        from scripts.ops.snapshot_operator_stop_signals import resolve_operator_decision_record_path

        op_rec = resolve_operator_decision_record_path(operator_decision_record)
    metadata = _load_paper_shadow_247_preflight_metadata(root)

    contract_path = root / CONTRACT_DOC
    scheduler_doc_path = root / SCHEDULER_DOC
    scheduler_config_path = root / SCHEDULER_CONFIG

    contract_text = contract_path.read_text(encoding="utf-8") if contract_path.exists() else ""
    scheduler_doc_text = (
        scheduler_doc_path.read_text(encoding="utf-8") if scheduler_doc_path.exists() else ""
    )
    scheduler_config_text = (
        scheduler_config_path.read_text(encoding="utf-8") if scheduler_config_path.exists() else ""
    )

    required_files = {
        CONTRACT_DOC: contract_path.exists(),
        SCHEDULER_DOC: scheduler_doc_path.exists(),
        SCHEDULER_CONFIG: scheduler_config_path.exists(),
    }

    canonical_owner_any = metadata.get("canonical_owner")
    canonical_owner = canonical_owner_any if isinstance(canonical_owner_any, str) else None

    paper_jobs = [str(x) for x in metadata.get("paper_jobs", []) if isinstance(x, str)]
    shadow_jobs = [str(x) for x in metadata.get("shadow_jobs", []) if isinstance(x, str)]
    output_paths = [str(x) for x in metadata.get("output_paths", []) if isinstance(x, str)]
    scheduler_jobs_by_name = _load_scheduler_jobs_by_name(root)

    stop_any = metadata.get("stop_command")
    emergency_any = metadata.get("emergency_stop_command")
    stop_command = stop_any if isinstance(stop_any, str) else None
    emergency_stop_command = emergency_any if isinstance(emergency_any, str) else None

    blockers: list[str] = []
    if not canonical_owner:
        blockers.append("canonical_owner_missing")
    if not paper_jobs or not shadow_jobs:
        blockers.append("paper_shadow_job_set_missing")
    if not output_paths:
        blockers.append("output_paths_missing")
    if not stop_command or not emergency_stop_command:
        blockers.append("stop_commands_missing")

    notes_list = [
        "read_only_reporter",
        "does_not_run_scheduler",
        "does_not_start_daemon",
        "does_not_activate_paper_or_shadow_runtime",
        "scheduler_command_inventory_v0",
        "scheduler_command_safety_classification_v0",
        "operator_moment_snapshot_v0",
        "unknown_hold_context_v0",
    ]
    if op_rec is not None:
        notes_list.append("operator_decision_context_v0")
    if durable_run_outroot is not None:
        notes_list.append("governance_outroot_clearance_v0")
        notes_list.append("activation_authorization_v0")

    # Authorization flags: never inferred from metadata alone (documentation-only TOML keys).
    payload: dict[str, Any] = {
        "contract": CONTRACT,
        "schema_version": 0,
        "status": "BLOCKED",
        "activation_authorized": False,
        "daemon_activation_authorized": False,
        "paper_runtime_authorized": False,
        "shadow_runtime_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
        "scheduler_execution_authorized": False,
        "dry_run_command": DRY_RUN_COMMAND,
        "dry_run_only": True,
        "required_files": required_files,
        "contract_markers": {
            "contract_doc_exists": required_files[CONTRACT_DOC],
            "contract_states_blocked": "Current status: **BLOCKED**." in contract_text,
            "contract_mentions_stop": "STOP" in contract_text
            and "do not activate Paper/Shadow 24/7" in contract_text,
            "contract_non_authority": "not trading authority" in contract_text
            or "Non-authority" in contract_text,
            "scheduler_doc_links_contract": "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
            in scheduler_doc_text,
            "scheduler_config_has_direct_247_job": any(
                token in scheduler_config_text.lower()
                for token in ("paper_shadow_247", "paper-shadow-247", "24/7")
            ),
        },
        "canonical_owner": canonical_owner,
        "paper_jobs": paper_jobs,
        "shadow_jobs": shadow_jobs,
        "commands": _build_scheduler_command_inventory(
            paper_jobs, shadow_jobs, scheduler_jobs_by_name
        ),
        "output_paths": output_paths,
        "state_files": [],
        "log_paths": [],
        "stop_command": stop_command,
        "emergency_stop_command": emergency_stop_command,
        "risk_flags": {
            "live": False,
            "testnet": False,
            "broker": False,
            "exchange": False,
            "orders": False,
            "network": False,
        },
        "status_reasons": blockers,
        "blockers": blockers,
        "notes": notes_list,
    }
    payload["hold_context_v0"] = _build_hold_context_v0()
    payload["dry_activation_readiness"] = _build_dry_activation_readiness(payload)
    payload["operator_moment_snapshot_v0"] = _build_operator_moment_snapshot_v0(
        payload, root, op_rec
    )
    stop_snap = payload["operator_moment_snapshot_v0"].get("stop_signal_snapshot")
    if isinstance(stop_snap, dict) and "operator_decision_context_v0" in stop_snap:
        payload["operator_decision_context_v0"] = stop_snap["operator_decision_context_v0"]
    if durable_run_outroot is not None:
        if not expected_run_id:
            raise ValueError("expected_run_id is required when durable_run_outroot is provided")
        from scripts.ops.paper_shadow_247_governance_outroot_clearance_v0 import (
            build_governance_outroot_clearance_v0,
        )

        payload["governance_outroot_clearance_v0"] = build_governance_outroot_clearance_v0(
            durable_run_outroot,
            expected_run_id=expected_run_id,
        )
        from scripts.ops.paper_shadow_247_activation_authorization_v0 import (
            build_activation_authorization_v0,
        )

        payload["activation_authorization_v0"] = build_activation_authorization_v0(
            durable_run_outroot,
            expected_run_id=expected_run_id,
            governance_outroot_clearance_v0=payload["governance_outroot_clearance_v0"],
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to inspect. Defaults to the current Peak_Trade checkout.",
    )
    parser.add_argument(
        "--operator-decision-record",
        type=Path,
        default=None,
        help=(
            "Optional path to an operator decision record; adds operator_decision_context_v0 "
            "(read-only, non-authorizing; does not change stop artifacts)."
        ),
    )
    parser.add_argument(
        "--durable-run-outroot",
        type=Path,
        default=None,
        help=(
            "Optional durable OUTROOT directory for scoped governance_outroot_clearance_v0 "
            "evidence (read-only, non-authorizing; does not clear HOLD or change status)."
        ),
    )
    parser.add_argument(
        "--expected-run-id",
        default=None,
        help="Required when --durable-run-outroot is set; RUN_ID scope for governance validation.",
    )
    args = parser.parse_args(argv)

    if (args.durable_run_outroot is None) ^ (args.expected_run_id is None):
        print(
            "ERR: --durable-run-outroot and --expected-run-id must be supplied together",
            file=sys.stderr,
        )
        return 2

    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root().resolve()
    try:
        payload = build_paper_shadow_247_preflight_status(
            root,
            operator_decision_record=args.operator_decision_record,
            durable_run_outroot=args.durable_run_outroot,
            expected_run_id=args.expected_run_id,
        )
    except ValueError as e:
        print(f"ERR: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        hold_context = payload.get("hold_context_v0") or {}
        progression = hold_context.get("progression_authorization") or {}

        print(f"status={payload['status']}")
        print(f"activation_authorized={str(payload['activation_authorized']).lower()}")
        print(f"dry_run_only={str(payload['dry_run_only']).lower()}")
        print(f"hold_current_state={hold_context.get('current_state', 'unknown')}")
        print(
            f"hold_operator_classification={hold_context.get('operator_classification', 'unknown')}"
        )
        print(f"hold_go_live_next_step={hold_context.get('go_live_next_step', 'blocked')}")
        print(
            f"hold_non_authorizing={str(bool(hold_context.get('non_authorizing', True))).lower()}"
        )
        print(
            "hold_daemon_activation_authorized="
            f"{str(bool(progression.get('daemon_activation_authorized', False))).lower()}"
        )
        print(
            "hold_scheduler_activation_authorized="
            f"{str(bool(progression.get('scheduler_execution_authorized', False))).lower()}"
        )
        print(
            "hold_paper_validation_authorized="
            f"{str(bool(progression.get('paper_runtime_authorized', False))).lower()}"
        )
        print(
            f"hold_testnet_authorized={str(bool(progression.get('testnet_authorized', False))).lower()}"
        )
        print(
            f"hold_live_authorized={str(bool(progression.get('live_authorized', False))).lower()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
