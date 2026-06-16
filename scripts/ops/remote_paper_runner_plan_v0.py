#!/usr/bin/env python3
"""Offline planning-only Remote Paper runner plan CLI (OP-REMOTE-PAPER-RUNNER-IMPL-V0-DRAFT Stufe 2).

Loads local JSON paths, reuses validate_remote_paper_packet_v0.validate_inputs (import only).
Emits non-authorizing planning_valid|blocked|invalid results. Never starts runners or runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.validate_remote_paper_packet_v0 import (  # noqa: E402
    LoadedInput,
    READY_FOR_START_KEYS,
    RUNNER_START_KEYS,
    collect_bool,
    has_key_recursive,
    load_json,
    result_has_forbidden_command_template,
    scan_forbidden_raw_patterns,
    validate_inputs,
)

SCHEMA_VERSION = "peak_trade.remote_paper_runner_plan_result.v0"

STATUS_PLANNING_VALID = "planning_valid"
STATUS_BLOCKED = "blocked"
STATUS_INVALID = "invalid"

CHARTER_READY_KEYS = frozenset(
    {
        "REMOTE_HOST_INVENTORY_READY_FOR_IMPLEMENTATION_CHARTER",
        "REMOTE_COST_KILL_ORPHAN_READY_FOR_IMPLEMENTATION_CHARTER",
    }
)

FORBIDDEN_TRUE_KEYS = frozenset(
    READY_FOR_START_KEYS
    | RUNNER_START_KEYS
    | frozenset(
        {
            "preflight_blocked_lifted",
            "remote_runner_start_permitted",
            "REMOTE_PAPER_RUNNER_START_PERMITTED",
            "REMOTE_PAPER_PACKET_READY_FOR_START",
        }
    )
)


@dataclass
class RunnerPlanResult:
    schema_version: str = SCHEMA_VERSION
    status: str = STATUS_INVALID
    reasons: list[str] = field(default_factory=list)
    checked_artifacts: list[str] = field(default_factory=list)
    plan_mode: dict[str, bool] = field(
        default_factory=lambda: {
            "dry_run": True,
            "no_network": True,
            "no_execute": True,
        }
    )
    authority: dict[str, bool] = field(
        default_factory=lambda: {
            "runtime": False,
            "remote_runner_start": False,
            "live": False,
            "testnet": False,
            "broker": False,
            "exchange": False,
            "command_template": False,
        }
    )
    preflight_blocked_lifted: bool = False
    ready_for_start: bool = False
    remote_runner_start_permitted: bool = False
    runtime_commands_called: bool = False
    validator_status_mapped_from: str = "INVALID"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _authority_invariants() -> dict[str, bool]:
    return {
        "runtime": False,
        "remote_runner_start": False,
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "command_template": False,
    }


def _merge_status(current: str, new: str) -> str:
    order = {STATUS_INVALID: 3, STATUS_BLOCKED: 2, STATUS_PLANNING_VALID: 1}
    if order.get(new, 0) > order.get(current, 0):
        return new
    return current


def _map_validator_status(validator_status: str) -> str:
    if validator_status == "PASS":
        return STATUS_PLANNING_VALID
    if validator_status == "BLOCKED":
        return STATUS_BLOCKED
    return STATUS_INVALID


def _machine_line_charter_true(payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    oml = payload.get("output_machine_lines")
    if not isinstance(oml, dict):
        return reasons
    for key in CHARTER_READY_KEYS:
        if oml.get(key) is True:
            reasons.append(f"output_machine_lines:{key}_forbidden")
    return reasons


def _forbidden_truthy_keys(payload: dict[str, Any], label: str) -> list[str]:
    reasons: list[str] = []
    for key in FORBIDDEN_TRUE_KEYS:
        if collect_bool(payload, key) is True:
            reasons.append(f"{label}:{key}_forbidden")
    preflight_status = str(payload.get("status", "")).lower()
    if preflight_status == "ready_for_start":
        reasons.append(f"{label}:status_ready_for_start_forbidden")
    if has_key_recursive(payload, "command_template"):
        reasons.append(f"{label}:command_template_forbidden")
    return reasons


def _safety_runner_blocked(safety: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    max_rt = safety.get("max_runtime_seconds")
    if not isinstance(max_rt, (int, float)) or max_rt <= 0:
        reasons.append("safety:max_runtime_seconds_missing_or_invalid")
    cost = safety.get("expected_cost_ceiling")
    if not isinstance(cost, dict) or not cost:
        reasons.append("safety:expected_cost_ceiling_missing")
    for key in (
        "stop_procedure_ref",
        "kill_procedure_ref",
        "orphan_detection_ref",
        "teardown_owner",
    ):
        value = safety.get(key)
        if not value or not str(value).strip():
            reasons.append(f"safety:{key}_missing")
    return reasons


def apply_runner_layer_checks(
    *,
    plan_mode: dict[str, bool],
    loaded: list[LoadedInput | None],
    validator_status: str,
    validator_reasons: list[str],
) -> tuple[str, list[str]]:
    status = _map_validator_status(validator_status)
    reasons = list(validator_reasons)

    if not plan_mode.get("dry_run", False):
        reasons.append("plan_mode:dry_run_required")
        status = _merge_status(status, STATUS_BLOCKED)
    if not plan_mode.get("no_network", False):
        reasons.append("plan_mode:no_network_required")
        status = _merge_status(status, STATUS_BLOCKED)
    if not plan_mode.get("no_execute", False):
        reasons.append("plan_mode:no_execute_required")
        status = _merge_status(status, STATUS_BLOCKED)

    invalid_reasons: list[str] = []
    blocked_reasons: list[str] = []

    for item in loaded:
        if item is None:
            continue
        invalid_reasons.extend(
            scan_forbidden_raw_patterns(item.raw_text, item.label),
        )
        invalid_reasons.extend(_forbidden_truthy_keys(item.payload, item.label))
        invalid_reasons.extend(_machine_line_charter_true(item.payload))
        if result_has_forbidden_command_template(item.payload):
            invalid_reasons.append(f"{item.label}:command_template_forbidden")

    safety_payload: dict[str, Any] | None = None
    for item in loaded:
        if item is not None and item.label == "safety":
            safety_payload = item.payload
            break
    if safety_payload is not None:
        blocked_reasons.extend(_safety_runner_blocked(safety_payload))

    if invalid_reasons:
        status = STATUS_INVALID
        reasons = sorted(set(reasons + invalid_reasons))
    elif blocked_reasons:
        status = _merge_status(status, STATUS_BLOCKED)
        reasons = sorted(set(reasons + blocked_reasons))
    elif status == STATUS_PLANNING_VALID and validator_status != "PASS":
        status = STATUS_BLOCKED

    return status, reasons


def emit_machine_lines(result: RunnerPlanResult) -> None:
    print(f"REMOTE_PAPER_RUNNER_STATUS={result.status}")
    print("REMOTE_PAPER_RUNNER_START_PERMITTED=false")
    print("REMOTE_PAPER_RUNNER_RUNTIME_COMMANDS_CALLED=false")
    print("REMOTE_PAPER_RUNNER_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true")
    print("REMOTE_PAPER_RUNNER_PREFLIGHT_BLOCKED_LIFTED=false")
    print("REMOTE_PAPER_RUNNER_READY_FOR_START=false")
    print("REMOTE_PAPER_RUNNER_AWS_CLI_CALLED=false")
    print("REMOTE_PAPER_RUNNER_SSH_CALLED=false")
    print("REMOTE_PAPER_RUNNER_SYSTEMD_CALLED=false")
    print("REMOTE_PAPER_RUNNER_GHA_RUNNER_IMPLEMENTED=false")
    print("REMOTE_PAPER_RUNNER_IMPLEMENTATION_PERMITTED=false")
    print("REMOTE_PAPER_RUNNER_LIVE_AUTHORITY=false")
    print("REMOTE_PAPER_RUNNER_TESTNET_AUTHORITY=false")
    print("REMOTE_PAPER_RUNNER_BROKER_CREDENTIALS_PRESENT=false")
    print("REMOTE_PAPER_RUNNER_EXCHANGE_CREDENTIALS_PRESENT=false")
    if result.status == STATUS_PLANNING_VALID:
        print("REMOTE_PAPER_RUNNER_PLANNING_VALID_NON_AUTHORIZING=true")


def build_runner_result(
    *,
    status: str,
    reasons: list[str],
    checked_artifacts: list[str],
    plan_mode: dict[str, bool],
    validator_status: str,
) -> RunnerPlanResult:
    return RunnerPlanResult(
        status=status,
        reasons=sorted(set(reasons)),
        checked_artifacts=checked_artifacts,
        plan_mode=plan_mode,
        authority=_authority_invariants(),
        preflight_blocked_lifted=False,
        ready_for_start=False,
        remote_runner_start_permitted=False,
        runtime_commands_called=False,
        validator_status_mapped_from=validator_status,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline planning-only Remote Paper runner plan (local JSON; non-authorizing)."
        ),
    )
    parser.add_argument("--preflight-json", required=True, type=Path)
    parser.add_argument("--approval-packet-json", required=True, type=Path)
    parser.add_argument("--host-inventory-json", required=True, type=Path)
    parser.add_argument("--cost-kill-orphan-json", required=True, type=Path)
    parser.add_argument("--registry-json", required=True, type=Path)
    parser.add_argument("--assembly-validator-json", type=Path, default=None)
    parser.add_argument("--s3-prefix-plan-json", type=Path, default=None)
    parser.add_argument("--closeout-metadata-json", type=Path, default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Planning-only dry run (default: enabled).",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        default=True,
        help="Disallow network semantics (default: enabled).",
    )
    parser.add_argument(
        "--no-execute",
        action="store_true",
        default=True,
        help="Disallow execution semantics (default: enabled).",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    plan_mode = {
        "dry_run": bool(args.dry_run),
        "no_network": bool(args.no_network),
        "no_execute": bool(args.no_execute),
    }

    checked_paths: list[str] = []
    invalid_early: list[str] = []
    loaded_all: list[LoadedInput | None] = []

    required_specs = (
        ("preflight", args.preflight_json),
        ("packet", args.approval_packet_json),
        ("inventory", args.host_inventory_json),
        ("safety", args.cost_kill_orphan_json),
        ("registry", args.registry_json),
    )
    loaded_required: dict[str, LoadedInput | None] = {}
    for label, path in required_specs:
        loaded, errors = load_json(path, label)
        loaded_required[label] = loaded
        loaded_all.append(loaded)
        if errors:
            invalid_early.extend(errors)
        elif loaded is not None:
            checked_paths.append(str(path))

    optional_specs = (
        ("assembly", args.assembly_validator_json),
        ("s3_plan", args.s3_prefix_plan_json),
        ("closeout", args.closeout_metadata_json),
    )
    loaded_optional: dict[str, LoadedInput | None] = {}
    for label, path in optional_specs:
        if path is None:
            loaded_optional[label] = None
            continue
        loaded, errors = load_json(path, label)
        loaded_optional[label] = loaded
        loaded_all.append(loaded)
        if errors:
            invalid_early.extend(errors)
        elif loaded is not None:
            checked_paths.append(str(path))

    if invalid_early:
        result = build_runner_result(
            status=STATUS_INVALID,
            reasons=invalid_early,
            checked_artifacts=checked_paths,
            plan_mode=plan_mode,
            validator_status="INVALID",
        )
    else:
        assert loaded_required["preflight"] is not None
        assert loaded_required["packet"] is not None
        assert loaded_required["inventory"] is not None
        assert loaded_required["safety"] is not None
        assert loaded_required["registry"] is not None
        validator_result = validate_inputs(
            preflight=loaded_required["preflight"],
            packet=loaded_required["packet"],
            inventory=loaded_required["inventory"],
            safety=loaded_required["safety"],
            registry=loaded_required["registry"],
            assembly=loaded_optional["assembly"],
            s3_plan=loaded_optional["s3_plan"],
            closeout=loaded_optional["closeout"],
        )
        status, reasons = apply_runner_layer_checks(
            plan_mode=plan_mode,
            loaded=loaded_all,
            validator_status=validator_result.status,
            validator_reasons=validator_result.reasons,
        )
        result = build_runner_result(
            status=status,
            reasons=reasons,
            checked_artifacts=checked_paths,
            plan_mode=plan_mode,
            validator_status=validator_result.status,
        )

    if args.json_output:
        print(json.dumps(result.to_dict(), sort_keys=True))
    else:
        emit_machine_lines(result)

    if result.status == STATUS_PLANNING_VALID:
        return 0
    if result.status == STATUS_BLOCKED:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
