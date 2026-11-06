#!/usr/bin/env python3
"""Offline/static Remote Paper packet validator CLI (OP-REMOTE-PAPER-VALIDATOR-CLI-IMPL-V0).

Reads explicit local JSON paths only; emits non-authorizing PASS|BLOCKED|INVALID results.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "peak_trade.remote_paper_validator_cli_result.v0"
CLI_NAME = "validate_remote_paper_packet_v0"

FORBIDDEN_RAW_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"AKIA[0-9A-Z]{16}"), "forbidden_secret_pattern:AKIA"),
    (re.compile(r"arn:aws:", re.IGNORECASE), "forbidden_secret_pattern:arn_aws"),
    (re.compile(r"s3://", re.IGNORECASE), "forbidden_secret_pattern:s3_uri"),
    (
        re.compile(r"BEGIN OPENSSH PRIVATE KEY", re.IGNORECASE),
        "forbidden_secret_pattern:openssh_key",
    ),
    (
        re.compile(r"BEGIN RSA PRIVATE KEY", re.IGNORECASE),
        "forbidden_secret_pattern:rsa_private_key",
    ),
    (re.compile(r"aws_access_key", re.IGNORECASE), "forbidden_secret_pattern:aws_access_key"),
    (re.compile(r"aws_secret", re.IGNORECASE), "forbidden_secret_pattern:aws_secret"),
    (re.compile(r"\bssh_user\b", re.IGNORECASE), "forbidden_secret_pattern:ssh_user"),
    (
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        "forbidden_secret_pattern:ipv4_literal",
    ),
)

UNBLOCKED_PREFLIGHT_STATUSES = frozenset(
    {"ready_for_start", "ready_for_operator_arming", "unblocked", "pass"}
)
READY_FOR_START_KEYS = frozenset({"ready_for_start", "READY_FOR_START"})
RUNNER_START_KEYS = frozenset(
    {"approve_remote_runner_start_now", "APPROVE_REMOTE_RUNNER_START_NOW"}
)
CLOSEOUT_PROOF_KEYS = frozenset(
    {
        "durable_copy_readme",
        "manifest_verify_rc",
        "manifest_sha256",
        "durable_closeout_path",
        "section_2b_1_proof",
    },
)


@dataclass
class LoadedInput:
    label: str
    path: Path
    payload: dict[str, Any]
    raw_text: str


@dataclass
class ValidatorResult:
    schema_version: str = SCHEMA_VERSION
    status: str = "INVALID"
    reasons: list[str] = field(default_factory=list)
    checked_artifacts: list[str] = field(default_factory=list)
    authority: dict[str, bool] = field(
        default_factory=lambda: {
            "runtime": False,
            "remote_runner_start": False,
            "testnet": False,
            "live": False,
            "command_template": False,
        }
    )
    preflight_blocked_lifted: bool = False
    ready_for_start: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _authority_invariants() -> dict[str, bool]:
    return {
        "runtime": False,
        "remote_runner_start": False,
        "testnet": False,
        "live": False,
        "command_template": False,
    }


def make_result(
    status: str,
    reasons: list[str],
    checked_artifacts: list[str],
) -> ValidatorResult:
    return ValidatorResult(
        status=status,
        reasons=sorted(set(reasons)),
        checked_artifacts=checked_artifacts,
        authority=_authority_invariants(),
        preflight_blocked_lifted=False,
        ready_for_start=False,
    )


def load_json(path: Path, label: str) -> tuple[LoadedInput | None, list[str]]:
    if not path.is_file():
        return None, [f"{label}:missing_file:{path}"]
    raw_text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, [f"{label}:invalid_json"]
    if not isinstance(payload, dict):
        return None, [f"{label}:invalid_shape"]
    return LoadedInput(label=label, path=path, payload=payload, raw_text=raw_text), []


def scan_forbidden_raw_patterns(raw_text: str, label: str) -> list[str]:
    reasons: list[str] = []
    for pattern, reason_code in FORBIDDEN_RAW_PATTERNS:
        if pattern.search(raw_text):
            reasons.append(f"{label}:{reason_code}")
    return reasons


def _walk_values(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        items: list[Any] = []
        for value in payload.values():
            items.extend(_walk_values(value))
        return items
    if isinstance(payload, list):
        items = []
        for item in payload:
            items.extend(_walk_values(item))
        return items
    return [payload]


def _walk_key_hits(payload: Any, keys: frozenset[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                hits.append(key)
            hits.extend(_walk_key_hits(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            hits.extend(_walk_key_hits(item, keys))
    return hits


def has_key_recursive(payload: Any, key: str) -> bool:
    if isinstance(payload, dict):
        if key in payload:
            return True
        return any(has_key_recursive(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(has_key_recursive(item, key) for item in payload)
    return False


def collect_remote_run_ids(payload: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in ("remote_run_id", "run_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            ids.append(value.strip())
    for value in _walk_values(payload):
        if isinstance(value, dict):
            ids.extend(collect_remote_run_ids(value))
    return ids


def collect_bool(payload: dict[str, Any], key: str) -> bool | None:
    if key in payload and isinstance(payload[key], bool):
        return payload[key]
    for value in _walk_values(payload):
        if isinstance(value, dict) and key in value and isinstance(value[key], bool):
            return value[key]
    return None


def _truthy_start_claim(payload: dict[str, Any]) -> bool:
    for key in READY_FOR_START_KEYS | RUNNER_START_KEYS:
        if collect_bool(payload, key) is True:
            return True
    for key, value in payload.items():
        if key in READY_FOR_START_KEYS and value is True:
            return True
    return False


def validate_inputs(
    *,
    preflight: LoadedInput,
    packet: LoadedInput,
    inventory: LoadedInput,
    safety: LoadedInput,
    registry: LoadedInput,
    assembly: LoadedInput | None,
    s3_plan: LoadedInput | None,
    closeout: LoadedInput | None,
) -> ValidatorResult:
    checked = [
        str(preflight.path),
        str(packet.path),
        str(inventory.path),
        str(safety.path),
        str(registry.path),
    ]
    if assembly is not None:
        checked.append(str(assembly.path))
    if s3_plan is not None:
        checked.append(str(s3_plan.path))
    if closeout is not None:
        checked.append(str(closeout.path))

    invalid_reasons: list[str] = []
    blocked_reasons: list[str] = []

    for loaded in (preflight, packet, inventory, safety, registry, assembly, s3_plan, closeout):
        if loaded is None:
            continue
        invalid_reasons.extend(scan_forbidden_raw_patterns(loaded.raw_text, loaded.label))
        if has_key_recursive(loaded.payload, "command_template"):
            invalid_reasons.append(f"{loaded.label}:command_template_forbidden")

    if invalid_reasons:
        return make_result("INVALID", invalid_reasons, checked)

    for loaded in (preflight, packet, inventory, safety, registry):
        if _truthy_start_claim(loaded.payload):
            blocked_reasons.append(f"{loaded.label}:ready_for_start_forbidden")

    run_ids: list[str] = []
    for loaded in (preflight, packet, safety, registry):
        run_ids.extend(collect_remote_run_ids(loaded.payload))
    distinct_run_ids = sorted(set(run_ids))
    if not distinct_run_ids:
        invalid_reasons.append("remote_run_id:missing")
    elif len(distinct_run_ids) > 1:
        invalid_reasons.append("remote_run_id:inconsistent")
    canonical_run_id = distinct_run_ids[0] if distinct_run_ids else ""

    if invalid_reasons:
        return make_result("INVALID", invalid_reasons, checked)

    def lane_id(payload: dict[str, Any]) -> str | None:
        value = payload.get("lane_id")
        return str(value) if value is not None else None

    def runtime_mode(payload: dict[str, Any]) -> str | None:
        value = payload.get("runtime_mode")
        return str(value) if value is not None else None

    for label, payload in (
        ("preflight", preflight.payload),
        ("packet", packet.payload),
        ("safety", safety.payload),
    ):
        current_lane = lane_id(payload)
        if current_lane is not None and current_lane != "paper":
            blocked_reasons.append(f"{label}:lane_id_not_paper")
        current_mode = runtime_mode(payload)
        if current_mode is not None and current_mode != "paper_only":
            blocked_reasons.append(f"{label}:runtime_mode_not_paper_only")

    for label, payload in (
        ("preflight", preflight.payload),
        ("packet", packet.payload),
        ("inventory", inventory.payload),
        ("safety", safety.payload),
    ):
        if collect_bool(payload, "live_authority") is True:
            blocked_reasons.append(f"{label}:live_authority_forbidden")
        if collect_bool(payload, "testnet_authority") is True:
            blocked_reasons.append(f"{label}:testnet_authority_forbidden")
        if collect_bool(payload, "broker_credentials_present") is True:
            blocked_reasons.append(f"{label}:broker_credentials_forbidden")
        if collect_bool(payload, "exchange_credentials_present") is True:
            blocked_reasons.append(f"{label}:exchange_credentials_forbidden")

    preflight_status = str(preflight.payload.get("status", "")).lower()
    if preflight_status in UNBLOCKED_PREFLIGHT_STATUSES:
        blocked_reasons.append("preflight:unblocked_status_forbidden")
    if collect_bool(preflight.payload, "preflight_blocked_lifted") is True:
        blocked_reasons.append("preflight:preflight_blocked_lifted_forbidden")

    if collect_bool(packet.payload, "do_not_run") is False:
        blocked_reasons.append("packet:do_not_run_required")
    packet_ready = packet.payload.get("output_machine_lines", {})
    if (
        isinstance(packet_ready, dict)
        and packet_ready.get("REMOTE_PAPER_PACKET_READY_FOR_START") is True
    ):
        blocked_reasons.append("packet:REMOTE_PAPER_PACKET_READY_FOR_START_forbidden")

    inv_host = inventory.payload.get("remote_host_id")
    safety_host = safety.payload.get("remote_host_id")
    if inv_host and safety_host and str(inv_host) != str(safety_host):
        invalid_reasons.append("remote_host_id:inconsistent")

    packet_transport = str(packet.payload.get("evidence_transport", "local_only"))
    if s3_plan is not None and packet_transport == "local_only":
        blocked_reasons.append("s3_prefix_plan:unexpected_for_local_only_transport")

    if closeout is not None:
        if collect_bool(closeout.payload, "closeout_complete") is True:
            if not any(key in closeout.payload for key in CLOSEOUT_PROOF_KEYS):
                blocked_reasons.append("closeout:complete_without_section_2b1_proof")

    runs = registry.payload.get("runs")
    registry_row: dict[str, Any] | None = None
    if isinstance(runs, list):
        for row in runs:
            if not isinstance(row, dict):
                continue
            if row.get("run_id") == canonical_run_id and row.get("lane_id") == "paper":
                registry_row = row
                break
    if registry_row is None:
        blocked_reasons.append("registry:run_row_missing")

    if assembly is not None:
        canonical = assembly.payload.get("canonical_cross_artifact_fields", {})
        if isinstance(canonical, dict):
            asm_run = canonical.get("remote_run_id")
            if asm_run and str(asm_run) != canonical_run_id:
                invalid_reasons.append("assembly:remote_run_id_mismatch")

    if invalid_reasons:
        return make_result("INVALID", invalid_reasons, checked)
    if blocked_reasons:
        return make_result("BLOCKED", blocked_reasons, checked)
    return make_result("PASS", [], checked)


def emit_machine_lines(result: ValidatorResult) -> None:
    print(f"REMOTE_PAPER_VALIDATOR_CLI_STATUS={result.status}")
    print("REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false")
    print("REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false")
    print("REMOTE_PAPER_VALIDATOR_CLI_RUNTIME_COMMANDS_CALLED=false")
    print("REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true")
    print("REMOTE_RUNNER_IMPLEMENTATION_PERMITTED=false")
    print("REMOTE_RUNNER_START_PERMITTED=false")
    print("VALIDATOR_CLI_IMPLEMENTATION_SLICE_PERMITTED_BY_CHARTER=true")
    print("DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false")
    print("CLOSEOUT_HELPER_EXECUTION_CALLED=false")
    print("AWS_CLI_CALLED=false")
    print("RCLONE_CALLED=false")
    print("NETWORK_CALLED=false")
    print("S3_UPLOAD_CALLED=false")
    print("S3_DOWNLOAD_CALLED=false")
    print("SSH_CALLED=false")
    print("SYSTEMD_CALLED=false")
    print("DOCKER_CALLED=false")
    print("PROCESS_CONTROL_CALLED=false")
    print("HOST_TERMINATION_CALLED=false")
    print("NOTION_WRITE_CALLED=false")
    print("MARKET_DASHBOARD_CHANGED=false")


def result_has_forbidden_command_template(payload: Any, *, parent_key: str | None = None) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "command_template" and parent_key != "authority":
                return True
            if result_has_forbidden_command_template(value, parent_key=key):
                return True
        return False
    if isinstance(payload, list):
        return any(
            result_has_forbidden_command_template(item, parent_key=parent_key) for item in payload
        )
    return False


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline/static Remote Paper packet validator (local JSON only; non-authorizing)."
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
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    checked_paths: list[str] = []
    invalid_early: list[str] = []

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
        if errors:
            invalid_early.extend(errors)
        elif loaded is not None:
            checked_paths.append(str(path))

    if invalid_early:
        result = make_result("INVALID", invalid_early, checked_paths)
    else:
        assert loaded_required["preflight"] is not None
        assert loaded_required["packet"] is not None
        assert loaded_required["inventory"] is not None
        assert loaded_required["safety"] is not None
        assert loaded_required["registry"] is not None
        result = validate_inputs(
            preflight=loaded_required["preflight"],
            packet=loaded_required["packet"],
            inventory=loaded_required["inventory"],
            safety=loaded_required["safety"],
            registry=loaded_required["registry"],
            assembly=loaded_optional["assembly"],
            s3_plan=loaded_optional["s3_plan"],
            closeout=loaded_optional["closeout"],
        )

    if result_has_forbidden_command_template(result.to_dict()):
        result.status = "INVALID"
        result.reasons.append("output:command_template_forbidden")

    if args.json_output:
        print(json.dumps(result.to_dict(), sort_keys=True))
    else:
        emit_machine_lines(result)

    if result.status == "PASS":
        return 0
    if result.status == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
