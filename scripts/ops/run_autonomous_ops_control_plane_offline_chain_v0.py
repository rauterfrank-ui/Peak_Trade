#!/usr/bin/env python3
"""Offline Autonomous Ops Control Plane chain orchestrator stub v0 (composition only).

Reads a transition fixture, composes existing plan generator + readiness bridge outputs,
and writes a combined offline chain artifact directory. Does not invoke closeout,
projection, Notion, durable copy, primary evidence retention, runtime, or network.

Machine marker: ``CONTROL_PLANE_OFFLINE_CHAIN_V0=true``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import bridge_control_plane_plan_to_post_closeout_readiness_v0 as bridge_mod
from scripts.ops import build_autonomous_ops_control_plane_plan_v0 as plan_mod

SCHEMA_VERSION = "control_plane_offline_chain_v0"
CHAIN_JSON_FILENAME = "CONTROL_PLANE_OFFLINE_CHAIN_V0.json"
CHAIN_MACHINE_LINES_FILENAME = "CONTROL_PLANE_OFFLINE_CHAIN_MACHINE_LINES.txt"
CHAIN_MD_FILENAME = "CONTROL_PLANE_OFFLINE_CHAIN_V0.md"

PLAN_SUBDIR = "plan"
READINESS_SUBDIR = "readiness"

CHAIN_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "CONTROL_PLANE_OFFLINE_CHAIN_V0",
    "PLANNING_ONLY",
    "NON_AUTHORIZING",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED",
    "CLOSEOUT_INVOKED",
    "PROJECTION_INVOKED",
    "NOTION_SYNC_INVOKED",
    "DURABLE_COPY_INVOKED",
    "PRIMARY_EVIDENCE_RETENTION_INVOKED",
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
    "PLAN_STATUS",
    "READINESS_STATUS",
)


def _plan_status(plan: dict[str, Any]) -> str:
    machine = plan.get("machine_lines") or {}
    status = machine.get("CONTROL_PLANE_PLAN_STATUS")
    if status in {"plan_only", "blocked"}:
        return str(status)
    decision = plan.get("decision") or {}
    return str(decision.get("status", "blocked"))


def _readiness_status(readiness: dict[str, Any]) -> str:
    machine = readiness.get("machine_lines") or {}
    return str(machine.get("CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS", "blocked"))


def _build_chain_machine_lines(plan_status: str, readiness_status: str) -> dict[str, str]:
    return {
        "CONTROL_PLANE_OFFLINE_CHAIN_V0": "true",
        "PLANNING_ONLY": "true",
        "NON_AUTHORIZING": "true",
        "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED": "false",
        "CLOSEOUT_INVOKED": "false",
        "PROJECTION_INVOKED": "false",
        "NOTION_SYNC_INVOKED": "false",
        "DURABLE_COPY_INVOKED": "false",
        "PRIMARY_EVIDENCE_RETENTION_INVOKED": "false",
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
        "PLAN_STATUS": plan_status,
        "READINESS_STATUS": readiness_status,
    }


def build_offline_chain_v0(
    *,
    source_fixture: str,
    plan_output_dir: str,
    readiness_output_dir: str,
    plan: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    plan_status = _plan_status(plan)
    readiness_status = _readiness_status(readiness)
    machine_lines = _build_chain_machine_lines(plan_status, readiness_status)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_fixture": source_fixture,
        "plan_output_dir": plan_output_dir,
        "readiness_output_dir": readiness_output_dir,
        "planning_only": True,
        "non_authorizing": True,
        "full_post_closeout_automation_implemented": False,
        "closeout_invoked": False,
        "projection_invoked": False,
        "notion_sync_invoked": False,
        "durable_copy_invoked": False,
        "primary_evidence_retention_invoked": False,
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
        "plan_status": plan_status,
        "readiness_status": readiness_status,
        "case_id": plan.get("case_id"),
        "machine_lines": machine_lines,
    }


def _write_machine_lines_file(path: Path, machine_lines: dict[str, str]) -> None:
    ordered = sorted(machine_lines.items())
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_chain_markdown(path: Path, chain: dict[str, Any]) -> None:
    lines = [
        "# Control Plane Offline Chain v0",
        "",
        f"- case_id: `{chain.get('case_id')}`",
        f"- plan_status: `{chain['plan_status']}`",
        f"- readiness_status: `{chain['readiness_status']}`",
        f"- planning_only: `{chain['planning_only']}`",
        f"- full_post_closeout_automation_implemented: `{chain['full_post_closeout_automation_implemented']}`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_offline_chain_artifacts_v0(outdir: Path, chain: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / CHAIN_JSON_FILENAME).write_text(
        json.dumps(chain, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines_file(outdir / CHAIN_MACHINE_LINES_FILENAME, chain["machine_lines"])
    _write_chain_markdown(outdir / CHAIN_MD_FILENAME, chain)


def run_offline_chain(*, fixture_path: Path, outdir: Path) -> dict[str, Any]:
    plan_dir = outdir / PLAN_SUBDIR
    readiness_dir = outdir / READINESS_SUBDIR
    plan_dir.mkdir(parents=True, exist_ok=True)
    readiness_dir.mkdir(parents=True, exist_ok=True)

    plan = plan_mod.run_plan_generator(fixture_path=fixture_path.resolve(), outdir=plan_dir)
    plan_json = plan_dir / plan_mod.PLAN_JSON_FILENAME
    readiness = bridge_mod.run_bridge(plan_path=plan_json, outdir=readiness_dir)

    chain = build_offline_chain_v0(
        source_fixture=str(fixture_path.resolve()),
        plan_output_dir=str(plan_dir.resolve()),
        readiness_output_dir=str(readiness_dir.resolve()),
        plan=plan,
        readiness=readiness,
    )
    write_offline_chain_artifacts_v0(outdir, chain)
    return chain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline Autonomous Ops Control Plane chain stub (fixture-only composition)."
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        chain = run_offline_chain(
            fixture_path=args.fixture.resolve(),
            outdir=args.outdir.resolve(),
        )
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    for key in CHAIN_MACHINE_LINE_KEYS:
        sys.stdout.write(f"{key}={chain['machine_lines'][key]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
