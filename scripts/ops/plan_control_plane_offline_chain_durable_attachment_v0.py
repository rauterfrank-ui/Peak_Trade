#!/usr/bin/env python3
"""Offline Control Plane durable attachment planner stub v0 (pointer-only, non-authorizing).

Reads offline chain output root + target durable archive root and writes a local attachment
plan. Does not copy, verify, write MANIFEST.sha256, retain evidence, invoke closeout,
projection, Notion, hooks, runtime, or network.

Machine marker: ``CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0=true``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

SCHEMA_VERSION = "control_plane_offline_chain_durable_attachment_v0"
DURABLE_ATTACHMENT_CONTRACT_MODE = "pointer_only_no_copy_no_verify"
TARGET_ARCHIVE_ROOT_POLICY = "must_be_outside_tmp"

PLAN_JSON_FILENAME = "CONTROL_PLANE_DURABLE_ATTACHMENT_PLAN_V0.json"
PLAN_MACHINE_LINES_FILENAME = "CONTROL_PLANE_DURABLE_ATTACHMENT_PLAN_MACHINE_LINES.txt"
PLAN_MD_FILENAME = "CONTROL_PLANE_DURABLE_ATTACHMENT_PLAN_V0.md"

REQUIRED_CHAIN_REL_PATHS_V0: tuple[str, ...] = (
    "plan/CONTROL_PLANE_PLAN_V0.json",
    "plan/CONTROL_PLANE_PLAN_MACHINE_LINES.txt",
    "plan/CONTROL_PLANE_PLAN_V0.md",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.json",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_MACHINE_LINES.txt",
    "readiness/CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.md",
    "CONTROL_PLANE_OFFLINE_CHAIN_V0.json",
    "CONTROL_PLANE_OFFLINE_CHAIN_MACHINE_LINES.txt",
    "CONTROL_PLANE_OFFLINE_CHAIN_V0.md",
)

OWNER_REFERENCES_V0: tuple[str, ...] = (
    "scripts/ops/primary_evidence_retention_v0.py",
    "scripts/ops/durable_closeout_copy_verify_v0.py",
    "scripts/ops/run_autonomous_ops_control_plane_offline_chain_v0.py",
    "tests/ops/test_control_plane_offline_chain_durable_evidence_attachment_contracts_v0.py",
)

STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING = "ready_for_durable_attachment_planning"
STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT = "blocked_missing_required_chain_artifact"
STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP = "blocked_target_archive_root_under_tmp"

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

PLAN_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0",
    "CONTROL_PLANE_DURABLE_ATTACHMENT_PLAN_STATUS",
    "DURABLE_ATTACHMENT_CONTRACT_MODE",
    "POINTER_ONLY",
    "DURABLE_COPY_INVOKED",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED",
    "MANIFEST_WRITE_INVOKED",
    "COPY_VERIFY_INVOKED",
    "CLOSEOUT_INVOKED",
    "PROJECTION_INVOKED",
    "NOTION_SYNC_INVOKED",
    "HOOK_IMPLEMENTED",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED",
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
)


def missing_chain_rel_paths(
    chain_root: Path,
    required_chain_rel_paths: tuple[str, ...] = REQUIRED_CHAIN_REL_PATHS_V0,
) -> list[str]:
    missing: list[str] = []
    for rel in required_chain_rel_paths:
        if not (chain_root / rel).is_file():
            missing.append(rel)
    return missing


def evaluate_attachment_plan_v0(
    *,
    source_chain_root: Path,
    target_archive_root: Path,
    required_chain_rel_paths: tuple[str, ...] = REQUIRED_CHAIN_REL_PATHS_V0,
) -> dict[str, Any]:
    """Evaluate pointer-only durable attachment plan (planner-only; no side effects)."""
    missing = missing_chain_rel_paths(source_chain_root, required_chain_rel_paths)

    if missing:
        status = STATUS_BLOCKED_MISSING_REQUIRED_CHAIN_ARTIFACT
    elif is_under_tmp(target_archive_root):
        status = STATUS_BLOCKED_TARGET_ARCHIVE_ROOT_UNDER_TMP
    else:
        status = STATUS_READY_FOR_DURABLE_ATTACHMENT_PLANNING

    machine_lines = {
        "CONTROL_PLANE_DURABLE_ATTACHMENT_PLANNER_CLI_STUB_V0": "true",
        "CONTROL_PLANE_DURABLE_ATTACHMENT_PLAN_STATUS": status,
        "DURABLE_ATTACHMENT_CONTRACT_MODE": DURABLE_ATTACHMENT_CONTRACT_MODE,
        "POINTER_ONLY": "true",
        "DURABLE_COPY_INVOKED": "false",
        "PRIMARY_EVIDENCE_RETENTION_INVOKED": "false",
        "MANIFEST_WRITE_INVOKED": "false",
        "COPY_VERIFY_INVOKED": "false",
        "CLOSEOUT_INVOKED": "false",
        "PROJECTION_INVOKED": "false",
        "NOTION_SYNC_INVOKED": "false",
        "HOOK_IMPLEMENTED": "false",
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED": "false",
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
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "source_chain_root": str(source_chain_root.resolve()),
        "target_archive_root": str(target_archive_root.resolve()),
        "required_chain_rel_paths": list(required_chain_rel_paths),
        "missing_chain_rel_paths": missing,
        "target_archive_root_policy": TARGET_ARCHIVE_ROOT_POLICY,
        "pointer_only": True,
        "status": status,
        "durable_attachment_contract_mode": DURABLE_ATTACHMENT_CONTRACT_MODE,
        "owner_references": list(OWNER_REFERENCES_V0),
        "durable_copy_invoked": False,
        "primary_evidence_retention_invoked": False,
        "manifest_write_invoked": False,
        "copy_verify_invoked": False,
        "closeout_invoked": False,
        "projection_invoked": False,
        "notion_sync_invoked": False,
        "hook_implemented": False,
        "full_post_closeout_automation_implemented": False,
        "runtime_started": False,
        "scheduler_started": False,
        "supervisor_started": False,
        "daemon_started": False,
        "paper_shadow_testnet_live_started": False,
        "aws_remote_touched": False,
        "s3_upload_required": False,
        "ssh_required": False,
        "network_required": False,
        "live_authority_changed": False,
        "master_v2_double_play_touched": False,
        "machine_lines": machine_lines,
    }


def _write_machine_lines_file(path: Path, machine_lines: dict[str, str]) -> None:
    ordered = sorted(machine_lines.items())
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_plan_markdown(path: Path, plan: dict[str, Any]) -> None:
    lines = [
        "# Control Plane Durable Attachment Plan v0",
        "",
        f"- status: `{plan['status']}`",
        f"- source_chain_root: `{plan['source_chain_root']}`",
        f"- target_archive_root: `{plan['target_archive_root']}`",
        f"- pointer_only: `{plan['pointer_only']}`",
        f"- durable_attachment_contract_mode: `{plan['durable_attachment_contract_mode']}`",
        f"- missing_chain_rel_paths: `{plan['missing_chain_rel_paths']}`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attachment_plan_artifacts_v0(outdir: Path, plan: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / PLAN_JSON_FILENAME).write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines_file(outdir / PLAN_MACHINE_LINES_FILENAME, plan["machine_lines"])
    _write_plan_markdown(outdir / PLAN_MD_FILENAME, plan)


def run_attachment_planner(
    *,
    chain_root: Path,
    target_archive_root: Path,
    outdir: Path,
) -> dict[str, Any]:
    plan = evaluate_attachment_plan_v0(
        source_chain_root=chain_root.resolve(),
        target_archive_root=target_archive_root.resolve(),
    )
    write_attachment_plan_artifacts_v0(outdir.resolve(), plan)
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Control Plane durable attachment planner (pointer-only; no copy/verify)."
        )
    )
    parser.add_argument("--chain-root", type=Path, required=True)
    parser.add_argument("--target-archive-root", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(argv)

    plan = run_attachment_planner(
        chain_root=args.chain_root,
        target_archive_root=args.target_archive_root,
        outdir=args.outdir,
    )
    for key in PLAN_MACHINE_LINE_KEYS:
        sys.stdout.write(f"{key}={plan['machine_lines'][key]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
