#!/usr/bin/env python3
"""Bounded offline AWS Remote 247 smoke preflight (fixture + durable evidence only).

Non-network, non-executing: validates G1-G6 using local fixture input and writes
durable evidence under --durable-output-dir. Does not call AWS, SSH, S3 upload,
or start any runtime lane.

Machine marker: ``AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_PREFLIGHT_V0=true``
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from scripts.ops.preflight_remote_runtime_runner_v0 import run_preflight as run_remote_preflight
from scripts.ops.preflight_s3_finalized_evidence_export_v0 import run_preflight as run_s3_preflight
from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)

SCHEMA_VERSION = "peak_trade.aws_remote_247_bounded_offline_smoke_preflight.v0"
PREFLIGHT_NAME = "aws_remote_247_bounded_offline_smoke_preflight_v0"
REQUIRED_APPROVED_SCOPE = "aws_remote_247_bounded_offline_smoke_implementation_v0"
MANIFEST_FILENAME = "MANIFEST.sha256"
MACHINE_LINES_FILENAME = "BOUNDED_OFFLINE_SMOKE_MACHINE_LINES.txt"
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)secret[_-]?key\s*[:=]"),
    re.compile(r"(?i)aws_secret_access_key"),
)

REMOTE_BOUNDARY_BOOLS_FALSE = (
    "runner_implemented",
    "aws_cli_called",
    "network_called",
    "s3_upload_called",
    "live_authority",
)

S3_BOUNDARY_BOOLS_FALSE = (
    "aws_cli_called",
    "upload_called",
    "network_actions_called",
    "live_authority",
)

SAFETY_MACHINE_LINES: dict[str, str] = {
    "START_RUNTIME_NOW": "false",
    "START_SCHEDULER_NOW": "false",
    "START_SUPERVISOR_NOW": "false",
    "START_DAEMON_NOW": "false",
    "START_PAPER_NOW": "false",
    "START_SHADOW_NOW": "false",
    "START_TESTNET_NOW": "false",
    "START_LIVE_NOW": "false",
    "AWS_REMOTE_TOUCHED": "false",
    "S3_UPLOAD_REQUIRED": "false",
    "SSH_REQUIRED": "false",
    "NETWORK_REQUIRED": "false",
    "LIVE_AUTHORITY_CHANGED": "false",
}

DIRECT_INPUT_MACHINE_LINES: dict[str, str] = {
    "DERIVED_PACKET_DIRECT_INPUT_USED": "true",
    "EVIDENCE_ONLY_WRAPPER_REQUIRED": "false",
    "RUN_START_ALLOWED": "false",
    "AWS_REMOTE_EXECUTION_ALLOWED": "false",
    "DO_NOT_RUN": "true",
    "HOLD_NO_PAPER_RUN": "true",
    "EXECUTABLE_RUN_COMMAND_CREATED": "false",
}

APPROVAL_PACKET_SCHEMA = "peak_trade.remote_paper_approval_command_packet.v0"
HOST_INVENTORY_SCHEMA = "peak_trade.remote_host_inventory_planning.v0"
COST_KILL_ORPHAN_SCHEMA = "peak_trade.remote_cost_kill_orphan_safety.v0"
REMOTE_PREFLIGHT_SCHEMA = "peak_trade.remote_runtime_runner_preflight.v0"

FORBIDDEN_TRUE_AUTHORITY_KEYS = frozenset(
    {
        "approve_remote_runner_start_now",
        "ready_for_start",
        "READY_FOR_START",
        "runner_implemented",
        "live_authority",
        "testnet_authority",
        "broker_credentials_present",
        "exchange_credentials_present",
        "run_start_allowed",
        "aws_remote_execution_allowed",
        "runtime_started",
        "scheduler_started",
        "supervisor_started",
        "daemon_started",
        "paper_shadow_testnet_live_started",
        "aws_remote_used",
        "s3_upload_used",
        "ssh_used",
        "network_used",
        "credentials_used",
        "testnet_allowed",
        "live_allowed",
        "broker_exchange_interaction_allowed",
        "preflight_blocked_lifted",
        "network_called",
        "aws_cli_called",
        "s3_upload_called",
        "process_control_called",
        "host_termination_called",
        "secrets_present",
    }
)


@dataclass(frozen=True)
class GateResults:
    g1: bool
    g2: bool
    g3: bool
    g4: bool
    g5: bool
    g6: bool
    reasons: tuple[str, ...]

    @property
    def all_pass(self) -> bool:
        return self.g1 and self.g2 and self.g3 and self.g4 and self.g5 and self.g6


@dataclass(frozen=True)
class DirectPacketInput:
    approval_packet: Path
    host_inventory: Path
    cost_kill_orphan_safety: Path
    remote_runtime_preflight: Path | None = None
    registry: Path | None = None


def _fail_reasons(*parts: str) -> tuple[str, ...]:
    return tuple(p for p in parts if p)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_values(node: Any) -> Iterator[Any]:
    if isinstance(node, dict):
        yield from node.values()
        for value in node.values():
            yield from _walk_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_values(item)


def _collect_bool(payload: dict[str, Any], key: str) -> bool | None:
    if key in payload and isinstance(payload[key], bool):
        return payload[key]
    for value in _walk_values(payload):
        if isinstance(value, dict) and key in value and isinstance(value[key], bool):
            return value[key]
    return None


def _paths_have_no_secret_literals(*paths: Path) -> tuple[bool, str]:
    for path in paths:
        payload = _load_json(path)
        ok, msg = _fixture_has_no_secret_literals(path, payload)
        if not ok:
            return False, msg
    return True, ""


def _verify_direct_input_authority_gates(
    *,
    approval: dict[str, Any],
    inventory: dict[str, Any],
    safety: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for label, payload in (
        ("approval", approval),
        ("inventory", inventory),
        ("safety", safety),
    ):
        if _collect_bool(payload, "do_not_run") is False:
            reasons.append(f"{label}:do_not_run_required")
        for key in FORBIDDEN_TRUE_AUTHORITY_KEYS:
            if _collect_bool(payload, key) is True:
                reasons.append(f"{label}:{key}_forbidden_true")
        if payload.get("lane_id") not in (None, "paper"):
            reasons.append(f"{label}:lane_id_not_paper")
        runtime_mode = payload.get("runtime_mode")
        if runtime_mode is not None and runtime_mode != "paper_only":
            reasons.append(f"{label}:runtime_mode_not_paper_only")

    if _collect_bool(approval, "hold_no_paper_run") is not True:
        reasons.append("approval:hold_no_paper_run_required")
    if _collect_bool(approval, "run_start_allowed") is True:
        reasons.append("approval:run_start_allowed_forbidden")
    if _collect_bool(approval, "aws_remote_execution_allowed") is True:
        reasons.append("approval:aws_remote_execution_allowed_forbidden")

    packet_ready = approval.get("output_machine_lines", {})
    if (
        isinstance(packet_ready, dict)
        and packet_ready.get("REMOTE_PAPER_PACKET_READY_FOR_START") is True
    ):
        reasons.append("approval:REMOTE_PAPER_PACKET_READY_FOR_START_forbidden")

    inv_host = inventory.get("remote_host_id")
    safety_host = safety.get("remote_host_id")
    if inv_host and safety_host and str(inv_host) != str(safety_host):
        reasons.append("remote_host_id:inconsistent")

    approval_run = approval.get("remote_run_id")
    safety_run = safety.get("remote_run_id")
    if approval_run and safety_run and str(approval_run) != str(safety_run):
        reasons.append("remote_run_id:inconsistent")

    return not reasons, reasons


def _synthesize_fixture_from_direct(
    *,
    approval: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "peak_trade.aws_remote_247_bounded_offline_smoke_fixture.v0",
        "approved_scope_name": REQUIRED_APPROVED_SCOPE,
        "offline_inventory": {
            "remote_run_id": str(approval["remote_run_id"]),
            "lane_id": str(approval.get("lane_id", "paper")),
            "runtime_host": str(approval.get("runtime_host", "remote")),
            "runtime_backend": str(approval.get("runtime_backend", "ec2")),
            "runtime_mode": str(approval.get("runtime_mode", "paper_only")),
            "max_runtime_seconds": int(approval.get("max_runtime_seconds", 3600)),
            "evidence_root_type": str(approval.get("evidence_root_type", "remote_durable")),
            "evidence_transport": str(approval.get("evidence_transport", "local_only")),
            "host_inventory_relpath": inventory.get("inventory_name", "derived_host_inventory"),
            "archive_path": "synthetic_evidence",
            "registry_evidence_transport": str(approval.get("evidence_transport", "local_only")),
        },
        "credential_boundary": {
            "secrets_present": False,
            "broker_credentials_present": False,
            "exchange_credentials_present": False,
            "aws_profile_required": False,
        },
        "closeout_plan": {"fail_closed_on_any_gate_false": True},
    }


def _verify_gate_g2_direct(
    *,
    approval: dict[str, Any],
    inventory: dict[str, Any],
    safety: dict[str, Any],
) -> tuple[bool, str]:
    if approval.get("schema_version") != APPROVAL_PACKET_SCHEMA:
        return False, "invalid_approval_packet_schema_version"
    if inventory.get("schema_version") != HOST_INVENTORY_SCHEMA:
        return False, "invalid_host_inventory_schema_version"
    if safety.get("schema_version") != COST_KILL_ORPHAN_SCHEMA:
        return False, "invalid_cost_kill_orphan_schema_version"
    for key in ("remote_run_id", "lane_id", "runtime_backend", "evidence_transport"):
        if key not in approval:
            return False, f"approval_packet_missing:{key}"
    if approval.get("lane_id") != "paper":
        return False, "approval_packet_lane_not_paper"
    if approval.get("runtime_mode") != "paper_only":
        return False, "approval_packet_runtime_mode_not_paper_only"
    return True, ""


def _verify_gate_g3_direct(
    *,
    paths: DirectPacketInput,
    approval: dict[str, Any],
    inventory: dict[str, Any],
    safety: dict[str, Any],
) -> tuple[bool, str]:
    ok, reasons = _verify_direct_input_authority_gates(
        approval=approval, inventory=inventory, safety=safety
    )
    if not ok:
        return False, ";".join(reasons)
    ok_secrets, msg = _paths_have_no_secret_literals(
        paths.approval_packet,
        paths.host_inventory,
        paths.cost_kill_orphan_safety,
    )
    if not ok_secrets:
        return False, msg
    if inventory.get("secrets_present") is not False:
        return False, "host_inventory_secrets_present"
    if inventory.get("aws_cli_called") is not False:
        return False, "host_inventory_aws_cli_called"
    if inventory.get("ssh_called") is not False:
        return False, "host_inventory_ssh_called"
    if safety.get("broker_credentials_present") is not False:
        return False, "safety_broker_credentials_present"
    if safety.get("exchange_credentials_present") is not False:
        return False, "safety_exchange_credentials_present"
    return True, ""


def _verify_gate_g4_direct(
    *,
    fixture: dict[str, Any],
    work_dir: Path,
    registry_path: Path | None,
) -> tuple[bool, str]:
    inv = fixture["offline_inventory"]
    run_id = str(inv["remote_run_id"])
    lane_id = str(inv["lane_id"])
    archive_path = str(inv.get("archive_path", "synthetic_evidence"))
    evidence_root = work_dir / archive_path
    _write_synthetic_evidence_root(evidence_root)
    reg_path = registry_path if registry_path is not None else work_dir / "registry_v1.json"
    if registry_path is None:
        _write_registry(
            reg_path,
            archive_root=work_dir,
            run_id=run_id,
            lane_id=lane_id,
            archive_path=archive_path,
            evidence_transport=str(inv.get("registry_evidence_transport", "local_only")),
        )
    elif not reg_path.is_file():
        return False, "registry_path_missing"
    remote = run_remote_preflight(
        dry_run=True,
        no_network=True,
        runtime_host=str(inv.get("runtime_host", "remote")),
        runtime_backend=str(inv.get("runtime_backend", "ec2")),
        runtime_mode=str(inv.get("runtime_mode", "paper_only")),
        lane_id=lane_id,
        remote_run_id=run_id,
        max_runtime_seconds=int(inv.get("max_runtime_seconds", 3600)),
        evidence_root_type=str(inv.get("evidence_root_type", "remote_durable")),
        evidence_transport=str(inv.get("evidence_transport", "local_only")),
        registry_json=reg_path,
        s3_prefix_plan_json=None,
        approval_record=None,
        scheduler_guard_json=None,
    )
    if remote.get("status") not in {"eligible", "blocked"}:
        return False, f"remote_preflight_status:{remote.get('status')}"
    if remote.get("dry_run") is not True or remote.get("no_network") is not True:
        return False, "remote_preflight_missing_dry_run_or_no_network"
    for field in REMOTE_BOUNDARY_BOOLS_FALSE:
        if remote.get(field) is not False:
            return False, f"remote_preflight_boundary:{field}"
    s3 = run_s3_preflight(
        evidence_root,
        dry_run=True,
        no_network=True,
        registry_json=reg_path,
        run_id=run_id,
        lane_id=lane_id,
        export_prefix_plan=True,
    )
    if s3.get("status") != "eligible":
        return False, f"s3_preflight_status:{s3.get('status')}"
    for field in S3_BOUNDARY_BOOLS_FALSE:
        if s3.get(field) is not False:
            return False, f"s3_preflight_boundary:{field}"
    return True, ""


def _fixture_has_no_secret_literals(
    fixture_path: Path, payload: dict[str, Any]
) -> tuple[bool, str]:
    text = fixture_path.read_text(encoding="utf-8") + json.dumps(payload, sort_keys=True)
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if pattern.search(text):
            return False, f"forbidden_secret_pattern:{pattern.pattern}"
    return True, ""


def _write_registry(
    path: Path,
    *,
    archive_root: Path,
    run_id: str,
    lane_id: str,
    archive_path: str,
    evidence_transport: str,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "peak_trade.generic_evidence_run_registry.v1",
                "archive_root": str(archive_root.resolve()),
                "runs": [
                    {
                        "run_id": run_id,
                        "lane_id": lane_id,
                        "archive_path": archive_path,
                        "evidence_transport": evidence_transport,
                        "manifest_verified": True,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_synthetic_evidence_root(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    (root / "evidence.txt").write_text("aws_remote_247_offline_smoke_fixture", encoding="utf-8")
    write_manifest_sha256(root)


def _verify_gate_g1(*, approved_scope_name: str, fixture: dict[str, Any]) -> tuple[bool, str]:
    if approved_scope_name != REQUIRED_APPROVED_SCOPE:
        return False, "approved_scope_name_mismatch"
    if fixture.get("approved_scope_name") != REQUIRED_APPROVED_SCOPE:
        return False, "fixture_approved_scope_mismatch"
    return True, ""


def _verify_gate_g2(fixture: dict[str, Any]) -> tuple[bool, str]:
    if (
        fixture.get("schema_version")
        != "peak_trade.aws_remote_247_bounded_offline_smoke_fixture.v0"
    ):
        return False, "invalid_fixture_schema_version"
    inv = fixture.get("offline_inventory")
    if not isinstance(inv, dict):
        return False, "offline_inventory_missing"
    required = (
        "remote_run_id",
        "lane_id",
        "host_inventory_relpath",
        "evidence_transport",
    )
    for key in required:
        if key not in inv:
            return False, f"offline_inventory_missing:{key}"
    return True, ""


def _verify_gate_g3(fixture_path: Path, fixture: dict[str, Any]) -> tuple[bool, str]:
    cred = fixture.get("credential_boundary")
    if not isinstance(cred, dict):
        return False, "credential_boundary_missing"
    for key in (
        "secrets_present",
        "broker_credentials_present",
        "exchange_credentials_present",
        "aws_profile_required",
    ):
        if cred.get(key) is not False:
            return False, f"credential_boundary_must_be_false:{key}"
    ok, msg = _fixture_has_no_secret_literals(fixture_path, fixture)
    if not ok:
        return False, msg
    inv_path = fixture_path.parent / fixture["offline_inventory"]["host_inventory_relpath"]
    if not inv_path.is_file():
        return False, "host_inventory_missing"
    inv = _load_json(inv_path)
    if inv.get("secrets_present") is not False:
        return False, "host_inventory_secrets_present"
    if inv.get("aws_cli_called") is not False:
        return False, "host_inventory_aws_cli_called"
    if inv.get("ssh_called") is not False:
        return False, "host_inventory_ssh_called"
    return True, ""


def _verify_gate_g4(
    *,
    fixture: dict[str, Any],
    work_dir: Path,
) -> tuple[bool, str]:
    inv = fixture["offline_inventory"]
    run_id = str(inv["remote_run_id"])
    lane_id = str(inv["lane_id"])
    archive_path = str(inv.get("archive_path", "synthetic_evidence"))
    evidence_root = work_dir / archive_path
    _write_synthetic_evidence_root(evidence_root)
    registry_path = work_dir / "registry_v1.json"
    _write_registry(
        registry_path,
        archive_root=work_dir,
        run_id=run_id,
        lane_id=lane_id,
        archive_path=archive_path,
        evidence_transport=str(inv.get("registry_evidence_transport", "local_only")),
    )
    remote = run_remote_preflight(
        dry_run=True,
        no_network=True,
        runtime_host=str(inv.get("runtime_host", "remote")),
        runtime_backend=str(inv.get("runtime_backend", "ec2")),
        runtime_mode=str(inv.get("runtime_mode", "paper_only")),
        lane_id=lane_id,
        remote_run_id=run_id,
        max_runtime_seconds=int(inv.get("max_runtime_seconds", 3600)),
        evidence_root_type=str(inv.get("evidence_root_type", "remote_durable")),
        evidence_transport=str(inv.get("evidence_transport", "local_only")),
        registry_json=registry_path,
        s3_prefix_plan_json=None,
        approval_record=None,
        scheduler_guard_json=None,
    )
    if remote.get("status") not in {"eligible", "blocked"}:
        return False, f"remote_preflight_status:{remote.get('status')}"
    if remote.get("dry_run") is not True or remote.get("no_network") is not True:
        return False, "remote_preflight_missing_dry_run_or_no_network"
    for field in REMOTE_BOUNDARY_BOOLS_FALSE:
        if remote.get(field) is not False:
            return False, f"remote_preflight_boundary:{field}"
    s3 = run_s3_preflight(
        evidence_root,
        dry_run=True,
        no_network=True,
        registry_json=registry_path,
        run_id=run_id,
        lane_id=lane_id,
        export_prefix_plan=True,
    )
    if s3.get("status") != "eligible":
        return False, f"s3_preflight_status:{s3.get('status')}"
    for field in S3_BOUNDARY_BOOLS_FALSE:
        if s3.get(field) is not False:
            return False, f"s3_preflight_boundary:{field}"
    return True, ""


def _verify_gate_g5(output_dir: Path) -> tuple[bool, str]:
    if is_under_tmp(output_dir):
        return False, "durable_output_dir_under_tmp"
    return True, ""


def _verify_gate_g6(
    *,
    g1: bool,
    g2: bool,
    g3: bool,
    g4: bool,
    g5: bool,
    fail_closed: bool,
) -> tuple[bool, str]:
    prior_pass = g1 and g2 and g3 and g4 and g5
    if fail_closed and not prior_pass:
        return False, "fail_closed_closeout:any_gate_false"
    if prior_pass:
        return True, ""
    return False, "gates_incomplete"


def run_bounded_offline_smoke_preflight(
    *,
    fixture_path: Path | None,
    durable_output_dir: Path,
    approved_scope_name: str,
    offline: bool,
    no_network: bool,
    direct_packet: DirectPacketInput | None = None,
) -> tuple[GateResults, dict[str, Any]]:
    reasons: list[str] = []
    if not offline:
        reasons.append("offline_flag_required")
    if not no_network:
        reasons.append("no_network_flag_required")

    use_direct = direct_packet is not None
    if use_direct and fixture_path is not None:
        reasons.append("fixture_and_direct_packet_mutually_exclusive")
    if not use_direct and (fixture_path is None or not fixture_path.is_file()):
        reasons.append("fixture_missing")
    if use_direct:
        for label, path in (
            ("approval_packet", direct_packet.approval_packet),
            ("host_inventory", direct_packet.host_inventory),
            ("cost_kill_orphan_safety", direct_packet.cost_kill_orphan_safety),
        ):
            if not path.is_file():
                reasons.append(f"{label}_missing")
        if direct_packet.remote_runtime_preflight is not None:
            if not direct_packet.remote_runtime_preflight.is_file():
                reasons.append("remote_runtime_preflight_missing")
        if direct_packet.registry is not None and not direct_packet.registry.is_file():
            reasons.append("registry_missing")

    input_label = (
        str(direct_packet.approval_packet.resolve())
        if use_direct and direct_packet is not None
        else str(fixture_path.resolve() if fixture_path else "missing")
    )

    if reasons:
        gates = GateResults(False, False, False, False, False, False, tuple(reasons))
        return gates, _build_report(
            gates,
            reasons,
            durable_output_dir,
            input_label,
            approved_scope_name,
            direct_input=use_direct,
            direct_packet=direct_packet,
        )

    fail_closed = True
    if use_direct:
        assert direct_packet is not None
        approval = _load_json(direct_packet.approval_packet)
        inventory = _load_json(direct_packet.host_inventory)
        safety = _load_json(direct_packet.cost_kill_orphan_safety)
        g1, r1 = (
            (True, "")
            if approved_scope_name == REQUIRED_APPROVED_SCOPE
            else (False, "approved_scope_name_mismatch")
        )
        if r1:
            reasons.append(r1)
        g2, r2 = _verify_gate_g2_direct(
            approval=approval, inventory=inventory, safety=safety
        )
        if r2:
            reasons.append(r2)
        g3, r3 = _verify_gate_g3_direct(
            paths=direct_packet,
            approval=approval,
            inventory=inventory,
            safety=safety,
        )
        if r3:
            reasons.append(r3)
        synthetic_fixture = _synthesize_fixture_from_direct(
            approval=approval, inventory=inventory
        )
        fail_closed = bool(
            synthetic_fixture.get("closeout_plan", {}).get(
                "fail_closed_on_any_gate_false", True
            )
        )
    else:
        assert fixture_path is not None
        fixture = _load_json(fixture_path)
        approval = inventory = safety = None
        synthetic_fixture = fixture
        g1, r1 = _verify_gate_g1(approved_scope_name=approved_scope_name, fixture=fixture)
        if r1:
            reasons.append(r1)
        g2, r2 = _verify_gate_g2(fixture)
        if r2:
            reasons.append(r2)
        g3, r3 = _verify_gate_g3(fixture_path, fixture)
        if r3:
            reasons.append(r3)
        fail_closed = bool(fixture.get("closeout_plan", {}).get("fail_closed_on_any_gate_false", True))

    g4 = False
    if g1 and g2 and g3:
        work = durable_output_dir / "work"
        work.mkdir(parents=True, exist_ok=True)
        if use_direct:
            assert direct_packet is not None
            g4, r4 = _verify_gate_g4_direct(
                fixture=synthetic_fixture,
                work_dir=work,
                registry_path=direct_packet.registry,
            )
        else:
            g4, r4 = _verify_gate_g4(fixture=synthetic_fixture, work_dir=work)
        if r4:
            reasons.append(r4)
    else:
        reasons.append("g4_skipped_prior_gates_failed")

    g5, r5 = _verify_gate_g5(durable_output_dir)
    if r5:
        reasons.append(r5)
    if g5:
        durable_output_dir.mkdir(parents=True, exist_ok=True)

    g6, r6 = _verify_gate_g6(g1=g1, g2=g2, g3=g3, g4=g4, g5=g5, fail_closed=fail_closed)
    if r6:
        reasons.append(r6)
    gates = GateResults(g1, g2, g3, g4, g5, g6, tuple(reasons))
    report = _build_report(
        gates,
        list(gates.reasons),
        durable_output_dir,
        input_label,
        approved_scope_name,
        direct_input=use_direct,
        direct_packet=direct_packet,
    )
    return gates, report


def _build_report(
    gates: GateResults,
    reasons: list[str],
    output_dir: Path,
    input_label: str,
    approved_scope_name: str,
    *,
    direct_input: bool = False,
    direct_packet: DirectPacketInput | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "preflight_name": PREFLIGHT_NAME,
        "status": "pass" if gates.all_pass else "blocked",
        "input_mode": "direct_derived_packet" if direct_input else "canonical_fixture",
        "fixture": input_label,
        "durable_output_dir": str(output_dir.resolve()),
        "approved_scope_name": approved_scope_name,
        "gates": {
            "G1_OPERATOR_SCOPE_VERIFIED": gates.g1,
            "G2_OFFLINE_INVENTORY_VERIFIED": gates.g2,
            "G3_CREDENTIAL_BOUNDARY_VERIFIED": gates.g3,
            "G4_REMOTE_S3_DRY_RUN_CONTRACT_VERIFIED": gates.g4,
            "G5_DURABLE_EVIDENCE_DESTINATION_VERIFIED": gates.g5,
            "G6_FAIL_CLOSED_CLOSEOUT_VERIFIED": gates.g6,
        },
        "reasons": reasons,
    }
    if direct_input and direct_packet is not None:
        report["direct_packet_inputs"] = {
            "approval_packet": str(direct_packet.approval_packet.resolve()),
            "host_inventory": str(direct_packet.host_inventory.resolve()),
            "cost_kill_orphan_safety": str(direct_packet.cost_kill_orphan_safety.resolve()),
            "remote_runtime_preflight": (
                str(direct_packet.remote_runtime_preflight.resolve())
                if direct_packet.remote_runtime_preflight is not None
                else None
            ),
            "registry": (
                str(direct_packet.registry.resolve()) if direct_packet.registry is not None else None
            ),
        }
    return report


def _write_machine_lines(
    path: Path,
    gates: GateResults,
    report: dict[str, Any],
    *,
    direct_input: bool = False,
) -> None:
    lines = [
        "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_PREFLIGHT_V0=true",
        f"G1_OPERATOR_SCOPE_VERIFIED={'true' if gates.g1 else 'false'}",
        f"G2_OFFLINE_INVENTORY_VERIFIED={'true' if gates.g2 else 'false'}",
        f"G3_CREDENTIAL_BOUNDARY_VERIFIED={'true' if gates.g3 else 'false'}",
        f"G4_REMOTE_S3_DRY_RUN_CONTRACT_VERIFIED={'true' if gates.g4 else 'false'}",
        f"G5_DURABLE_EVIDENCE_DESTINATION_VERIFIED={'true' if gates.g5 else 'false'}",
        f"G6_FAIL_CLOSED_CLOSEOUT_VERIFIED={'true' if gates.g6 else 'false'}",
        f"BOUNDED_OFFLINE_SMOKE_STATUS={report['status']}",
    ]
    lines.extend(f"{k}={v}" for k, v in SAFETY_MACHINE_LINES.items())
    if direct_input:
        lines.extend(f"{k}={v}" for k, v in DIRECT_INPUT_MACHINE_LINES.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_durable_evidence(
    output_dir: Path,
    gates: GateResults,
    report: dict[str, Any],
) -> tuple[bool, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_lines = [
        "# AWS Remote 247 Bounded Offline Smoke Preflight Report",
        "",
        f"- status: {report['status']}",
        f"- fixture: `{report['fixture']}`",
        "",
        "## Gates",
    ]
    for key, val in report["gates"].items():
        md_lines.append(f"- {key}: {str(val).lower()}")
    if report["reasons"]:
        md_lines.extend(["", "## Reasons", *[f"- {r}" for r in report["reasons"]]])
    (output_dir / "AWS_REMOTE_247_BOUNDED_OFFLINE_SMOKE_REPORT.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines(
        output_dir / MACHINE_LINES_FILENAME,
        gates,
        report,
        direct_input=report.get("input_mode") == "direct_derived_packet",
    )
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    verify_log = output_dir / "MANIFEST_VERIFY.log"
    if ok:
        verify_log.write_text("MANIFEST_VERIFY_RC=0\n", encoding="utf-8")
    else:
        verify_log.write_text(f"MANIFEST_VERIFY_RC=1\n{msg}\n", encoding="utf-8")
    return ok, msg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded offline AWS Remote 247 smoke preflight (fixture only; no network)."
    )
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--approval-packet", type=Path, default=None)
    parser.add_argument("--host-inventory", type=Path, default=None)
    parser.add_argument("--cost-kill-orphan-safety", type=Path, default=None)
    parser.add_argument("--remote-runtime-preflight", type=Path, default=None)
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--durable-output-dir", type=Path, required=True)
    parser.add_argument("--approved-scope-name", required=True)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--no-network", action="store_true", required=True)
    args = parser.parse_args(argv)

    direct_paths = [
        args.approval_packet,
        args.host_inventory,
        args.cost_kill_orphan_safety,
    ]
    direct_partial = any(p is not None for p in direct_paths)
    direct_complete = all(p is not None for p in direct_paths)
    if direct_partial and not direct_complete:
        sys.stderr.write(
            "direct derived packet mode requires --approval-packet, "
            "--host-inventory, and --cost-kill-orphan-safety\n"
        )
        return 2
    if args.fixture is None and not direct_complete:
        sys.stderr.write("either --fixture or full direct derived packet inputs are required\n")
        return 2

    if is_under_tmp(args.durable_output_dir):
        sys.stderr.write("durable-output-dir must be outside /tmp\n")
        return 2

    direct_packet = None
    if direct_complete:
        direct_packet = DirectPacketInput(
            approval_packet=args.approval_packet.resolve(),
            host_inventory=args.host_inventory.resolve(),
            cost_kill_orphan_safety=args.cost_kill_orphan_safety.resolve(),
            remote_runtime_preflight=(
                args.remote_runtime_preflight.resolve()
                if args.remote_runtime_preflight is not None
                else None
            ),
            registry=args.registry.resolve() if args.registry is not None else None,
        )

    gates, report = run_bounded_offline_smoke_preflight(
        fixture_path=args.fixture.resolve() if args.fixture is not None else None,
        durable_output_dir=args.durable_output_dir.resolve(),
        approved_scope_name=args.approved_scope_name,
        offline=args.offline,
        no_network=args.no_network,
        direct_packet=direct_packet,
    )
    manifest_ok, manifest_msg = _write_durable_evidence(
        args.durable_output_dir.resolve(),
        gates,
        report,
    )
    if not manifest_ok:
        report["reasons"] = list(report.get("reasons", [])) + [f"manifest_verify:{manifest_msg}"]
        gates = GateResults(
            gates.g1,
            gates.g2,
            gates.g3,
            gates.g4,
            False,
            gates.g6,
            gates.reasons + (f"manifest_verify:{manifest_msg}",),
        )

    for line in (
        (args.durable_output_dir / MACHINE_LINES_FILENAME).read_text(encoding="utf-8").splitlines()
    ):
        if line.strip():
            sys.stdout.write(line + "\n")

    if gates.all_pass and manifest_ok:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
