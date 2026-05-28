#!/usr/bin/env python3
"""Offline Control Plane automation hook dry-run summary stub v0 (summary-only).

Reads offline chain root + durable attachment plan JSON and writes a local hook dry-run
summary. Does not execute hooks, copy, verify, write MANIFEST.sha256, retain evidence,
invoke closeout, projection, Notion, runtime, or network.

Machine marker: ``CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_CLI_STUB_V0=true``
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.plan_control_plane_offline_chain_durable_attachment_v0 import (
    DURABLE_ATTACHMENT_CONTRACT_MODE,
    STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING,
    missing_chain_rel_paths,
)
from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

SCHEMA_VERSION = "control_plane_hook_dry_run_summary_v0"

SUMMARY_JSON_FILENAME = "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_V0.json"
SUMMARY_MACHINE_LINES_FILENAME = "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_MACHINE_LINES.txt"
SUMMARY_MD_FILENAME = "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_V0.md"

STATUS_READY_FOR_CP_HOOK_DRY_RUN = "ready_for_control_plane_hook_dry_run"
STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE = "blocked_offline_chain_incomplete"
STATUS_BLOCKED_ATTACHMENT_NOT_READY = "blocked_attachment_not_ready"
STATUS_BLOCKED_POINTER_ONLY_REQUIRED = "blocked_pointer_only_required"
STATUS_BLOCKED_TARGET_ARCHIVE_UNDER_TMP = "blocked_target_archive_under_tmp"
STATUS_BLOCKED_HOOK_IMPLEMENTED = "blocked_hook_implemented"
STATUS_BLOCKED_FULL_AUTOMATION_CLAIMED = "blocked_full_automation_claimed"
STATUS_BLOCKED_INVOKE_OR_START_FLAG = "blocked_invoke_or_start_flag"

OWNER_REFERENCES_V0: tuple[str, ...] = (
    "tests/ops/test_control_plane_first_automation_hook_dry_run_contract_v0.py",
    "scripts/ops/plan_control_plane_offline_chain_durable_attachment_v0.py",
    "tests/ops/test_control_plane_planner_and_hook_e2e_cli_contract_v0.py",
    "tests/ops/test_post_closeout_automation_hook_owner_precheck_v0.py",
    "tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py",
)

FORBIDDEN_CLI_FLAGS: tuple[str, ...] = (
    "--execute",
    "--copy",
    "--verify",
    "--retention",
    "--closeout",
    "--projection",
    "--notion-sync",
    "--upload",
    "--s3",
    "--ssh",
    "--start",
)

SUMMARY_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_CLI_STUB_V0",
    "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_STATUS",
    "HOOK_IMPLEMENTED",
    "HOOK_DRY_RUN_ONLY",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED",
    "DURABLE_ATTACHMENT_CONTRACT_MODE",
    "DURABLE_COPY_INVOKED",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED",
    "MANIFEST_WRITE_INVOKED",
    "COPY_VERIFY_INVOKED",
    "CLOSEOUT_INVOKED",
    "PROJECTION_INVOKED",
    "NOTION_SYNC_INVOKED",
    "RUNTIME_STARTED",
    "SCHEDULER_STARTED",
    "SUPERVISOR_STARTED",
    "DAEMON_STARTED",
    "PAPER_SHADOW_TESTNET_LIVE_STARTED",
    "AWS_REMOTE_TOUCHED",
    "S3_UPLOAD_REQUIRED",
    "SSH_REQUIRED",
    "NETWORK_REQUIRED",
    "LIVE_AUTHORITY_CHANGED",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED",
    "KRAKEN_TESTNET_CRON_REARMED",
    "AI_PAID_VARS_REARMED",
)


@dataclass(frozen=True)
class ControlPlaneAutomationHookDryRunInputs:
    """Hook dry-run readiness inputs (offline summary only; not production API)."""

    offline_chain_complete: bool = False
    attachment_e2e_complete: bool = False
    attachment_status: str = "blocked_missing_required_chain_artifact"
    pointer_only: bool = False
    target_archive_root: Path | None = None
    hook_implemented: bool = False
    full_post_closeout_automation_implemented: bool = False
    closeout_invoked: bool = False
    projection_invoked: bool = False
    notion_sync_invoked: bool = False
    durable_copy_invoked: bool = False
    primary_evidence_retention_invoked: bool = False
    manifest_write_invoked: bool = False
    copy_verify_invoked: bool = False
    runtime_started: bool = False
    scheduler_started: bool = False
    supervisor_started: bool = False
    daemon_started: bool = False
    paper_shadow_testnet_live_started: bool = False
    aws_remote_touched: bool = False
    network_required: bool = False
    live_authority_changed: bool = False
    master_v2_double_play_touched: bool = False
    replaces_generic_hook_owners: bool = False


def build_control_plane_automation_hook_dry_run_summary(
    inp: ControlPlaneAutomationHookDryRunInputs,
) -> tuple[str, list[str]]:
    """Return (status, blockers) matching #3763 contract semantics."""
    blockers: list[str] = []

    if not inp.offline_chain_complete:
        blockers.append("offline_chain_complete_required")
    if not inp.attachment_e2e_complete:
        blockers.append("attachment_e2e_complete_required")
    if inp.attachment_status != STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING:
        blockers.append("attachment_status_not_ready_for_durable_attachment_planning")
    if not inp.pointer_only:
        blockers.append("pointer_only_durable_attachment_required")
    if inp.target_archive_root is None:
        blockers.append("target_archive_root_missing")
    elif is_under_tmp(inp.target_archive_root):
        blockers.append("target_archive_root_under_tmp")
    if inp.hook_implemented:
        blockers.append("hook_implemented_must_remain_false")
    if inp.full_post_closeout_automation_implemented:
        blockers.append("full_post_closeout_automation_must_remain_false")
    if inp.replaces_generic_hook_owners:
        blockers.append("must_not_replace_generic_post_closeout_hook_owners")

    invoke_flags = (
        ("closeout_invoked", inp.closeout_invoked),
        ("projection_invoked", inp.projection_invoked),
        ("notion_sync_invoked", inp.notion_sync_invoked),
        ("durable_copy_invoked", inp.durable_copy_invoked),
        ("primary_evidence_retention_invoked", inp.primary_evidence_retention_invoked),
        ("manifest_write_invoked", inp.manifest_write_invoked),
        ("copy_verify_invoked", inp.copy_verify_invoked),
        ("runtime_started", inp.runtime_started),
        ("scheduler_started", inp.scheduler_started),
        ("supervisor_started", inp.supervisor_started),
        ("daemon_started", inp.daemon_started),
        ("paper_shadow_testnet_live_started", inp.paper_shadow_testnet_live_started),
        ("aws_remote_touched", inp.aws_remote_touched),
        ("network_required", inp.network_required),
        ("live_authority_changed", inp.live_authority_changed),
        ("master_v2_double_play_touched", inp.master_v2_double_play_touched),
    )
    for name, value in invoke_flags:
        if value:
            blockers.append(f"forbidden_invoke_or_start:{name}")

    if blockers:
        if "offline_chain_complete_required" in blockers:
            status = STATUS_BLOCKED_OFFLINE_CHAIN_INCOMPLETE
        elif "attachment_e2e_complete_required" in blockers or (
            "attachment_status_not_ready_for_durable_attachment_planning" in blockers
        ):
            status = STATUS_BLOCKED_ATTACHMENT_NOT_READY
        elif "pointer_only_durable_attachment_required" in blockers:
            status = STATUS_BLOCKED_POINTER_ONLY_REQUIRED
        elif "target_archive_root_under_tmp" in blockers:
            status = STATUS_BLOCKED_TARGET_ARCHIVE_UNDER_TMP
        elif "hook_implemented_must_remain_false" in blockers:
            status = STATUS_BLOCKED_HOOK_IMPLEMENTED
        elif "full_post_closeout_automation_must_remain_false" in blockers:
            status = STATUS_BLOCKED_FULL_AUTOMATION_CLAIMED
        elif any(b.startswith("forbidden_invoke_or_start:") for b in blockers):
            status = STATUS_BLOCKED_INVOKE_OR_START_FLAG
        else:
            status = STATUS_BLOCKED_ATTACHMENT_NOT_READY
        return status, blockers

    return STATUS_READY_FOR_CP_HOOK_DRY_RUN, []


def hook_inputs_from_attachment_plan(
    *,
    chain_root: Path,
    plan: dict[str, Any],
    attachment_e2e_complete: bool = True,
) -> ControlPlaneAutomationHookDryRunInputs:
    """Map planner attachment plan JSON to hook dry-run inputs."""
    missing = missing_chain_rel_paths(chain_root)
    offline_chain_complete = len(missing) == 0
    target_raw = plan.get("target_archive_root")
    return ControlPlaneAutomationHookDryRunInputs(
        offline_chain_complete=offline_chain_complete,
        attachment_e2e_complete=attachment_e2e_complete,
        attachment_status=str(plan["status"]),
        pointer_only=bool(plan.get("pointer_only")),
        target_archive_root=Path(target_raw) if target_raw else None,
        hook_implemented=bool(plan.get("hook_implemented")),
        full_post_closeout_automation_implemented=bool(
            plan.get("full_post_closeout_automation_implemented")
        ),
    )


def build_summary_machine_lines(status: str) -> dict[str, str]:
    return {
        "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_CLI_STUB_V0": "true",
        "CONTROL_PLANE_HOOK_DRY_RUN_SUMMARY_STATUS": status,
        "HOOK_IMPLEMENTED": "false",
        "HOOK_DRY_RUN_ONLY": "true",
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED": "false",
        "DURABLE_ATTACHMENT_CONTRACT_MODE": DURABLE_ATTACHMENT_CONTRACT_MODE,
        "DURABLE_COPY_INVOKED": "false",
        "PRIMARY_EVIDENCE_RETENTION_INVOKED": "false",
        "MANIFEST_WRITE_INVOKED": "false",
        "COPY_VERIFY_INVOKED": "false",
        "CLOSEOUT_INVOKED": "false",
        "PROJECTION_INVOKED": "false",
        "NOTION_SYNC_INVOKED": "false",
        "RUNTIME_STARTED": "false",
        "SCHEDULER_STARTED": "false",
        "SUPERVISOR_STARTED": "false",
        "DAEMON_STARTED": "false",
        "PAPER_SHADOW_TESTNET_LIVE_STARTED": "false",
        "AWS_REMOTE_TOUCHED": "false",
        "S3_UPLOAD_REQUIRED": "false",
        "SSH_REQUIRED": "false",
        "NETWORK_REQUIRED": "false",
        "LIVE_AUTHORITY_CHANGED": "false",
        "MASTER_V2_DOUBLE_PLAY_TOUCHED": "false",
        "KRAKEN_TESTNET_CRON_REARMED": "false",
        "AI_PAID_VARS_REARMED": "false",
    }


def evaluate_hook_dry_run_summary_v0(
    *,
    chain_root: Path,
    attachment_plan_path: Path,
    attachment_e2e_complete: bool = True,
) -> dict[str, Any]:
    """Evaluate hook dry-run summary from chain root + attachment plan JSON path."""
    plan = json.loads(attachment_plan_path.read_text(encoding="utf-8"))
    chain_root_resolved = chain_root.resolve()
    attachment_plan_resolved = attachment_plan_path.resolve()

    inp = hook_inputs_from_attachment_plan(
        chain_root=chain_root_resolved,
        plan=plan,
        attachment_e2e_complete=attachment_e2e_complete,
    )
    status, blockers = build_control_plane_automation_hook_dry_run_summary(inp)
    machine_lines = build_summary_machine_lines(status)

    return {
        "schema_version": SCHEMA_VERSION,
        "source_chain_root": str(chain_root_resolved),
        "attachment_plan_path": str(attachment_plan_resolved),
        "attachment_plan_status": str(plan["status"]),
        "status": status,
        "blockers": blockers,
        "hook_implemented": False,
        "hook_dry_run_only": True,
        "full_post_closeout_automation_implemented": False,
        "durable_attachment_contract_mode": DURABLE_ATTACHMENT_CONTRACT_MODE,
        "owner_references": list(OWNER_REFERENCES_V0),
        "machine_lines": machine_lines,
    }


def _write_machine_lines_file(path: Path, machine_lines: dict[str, str]) -> None:
    ordered = sorted(machine_lines.items())
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Control Plane Hook Dry-Run Summary v0",
        "",
        f"- status: `{summary['status']}`",
        f"- attachment_plan_status: `{summary['attachment_plan_status']}`",
        f"- source_chain_root: `{summary['source_chain_root']}`",
        f"- attachment_plan_path: `{summary['attachment_plan_path']}`",
        f"- hook_implemented: `{summary['hook_implemented']}`",
        f"- hook_dry_run_only: `{summary['hook_dry_run_only']}`",
        f"- blockers: `{summary['blockers']}`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hook_dry_run_summary_artifacts_v0(outdir: Path, summary: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / SUMMARY_JSON_FILENAME).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines_file(outdir / SUMMARY_MACHINE_LINES_FILENAME, summary["machine_lines"])
    _write_summary_markdown(outdir / SUMMARY_MD_FILENAME, summary)


def run_hook_dry_run_summary(
    *,
    chain_root: Path,
    attachment_plan: Path,
    outdir: Path,
) -> dict[str, Any]:
    summary = evaluate_hook_dry_run_summary_v0(
        chain_root=chain_root,
        attachment_plan_path=attachment_plan,
    )
    write_hook_dry_run_summary_artifacts_v0(outdir.resolve(), summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Control Plane hook dry-run summary (summary-only; no hook execution)."
        )
    )
    parser.add_argument("--chain-root", type=Path, required=True)
    parser.add_argument("--attachment-plan", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = run_hook_dry_run_summary(
        chain_root=args.chain_root,
        attachment_plan=args.attachment_plan,
        outdir=args.outdir,
    )
    for key in SUMMARY_MACHINE_LINE_KEYS:
        sys.stdout.write(f"{key}={summary['machine_lines'][key]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
