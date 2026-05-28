#!/usr/bin/env python3
"""Bridge Autonomous Ops Control Plane plan output to post-closeout readiness (offline only).

Reads ``CONTROL_PLANE_PLAN_V0.json`` from the offline plan generator and emits a local
readiness summary for future post-closeout/projection planning. Does not invoke closeout,
projection, Notion, durable copy, primary evidence retention, runtime, or network.

Machine marker: ``CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0=true``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "control_plane_post_closeout_readiness_v0"
SOURCE_PLAN_SCHEMA_VERSION = "control_plane_plan_v0"
READINESS_JSON_FILENAME = "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.json"
READINESS_MACHINE_LINES_FILENAME = "CONTROL_PLANE_POST_CLOSEOUT_READINESS_MACHINE_LINES.txt"
READINESS_MD_FILENAME = "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0.md"

OWNER_CLOSEOUT_CHAIN_TEST = "tests/ops/test_closeout_to_projection_chain_automation_contract_v0.py"
OWNER_PROJECTION_BUILDER = "scripts/ops/build_post_closeout_projection_payload_v0.py"
OWNER_NOTION_DRY_RUN = "scripts/ops/notion_post_closeout_sync_dry_run_v0.py"
OWNER_DURABLE_COPY_VERIFY = "scripts/ops/durable_closeout_copy_verify_v0.py"

REQUIRED_PLAN_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "case_id",
        "decision",
        "machine_lines",
    }
)

READINESS_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0",
    "CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS",
    "PLANNING_ONLY",
    "CLOSEOUT_INVOKE_AUTHORIZED",
    "PROJECTION_INVOKE_AUTHORIZED",
    "NOTION_SYNC_AUTHORIZED",
    "DURABLE_COPY_AUTHORIZED",
    "PRIMARY_EVIDENCE_RETENTION_INVOKE_AUTHORIZED",
    "RUNTIME_START_REQUIRED",
    "SCHEDULER_START_REQUIRED",
    "SUPERVISOR_START_REQUIRED",
    "DAEMON_START_REQUIRED",
    "PAPER_SHADOW_TESTNET_LIVE_START_REQUIRED",
    "AWS_REMOTE_REQUIRED",
    "S3_UPLOAD_REQUIRED",
    "SSH_REQUIRED",
    "NETWORK_REQUIRED",
    "LIVE_AUTHORITY_CHANGED",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_plan(plan: dict[str, Any], plan_path: Path) -> str:
    missing = REQUIRED_PLAN_KEYS - plan.keys()
    if missing:
        raise ValueError(f"plan missing keys {sorted(missing)}: {plan_path}")
    if plan["schema_version"] != SOURCE_PLAN_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported plan schema {plan['schema_version']!r} "
            f"(expected {SOURCE_PLAN_SCHEMA_VERSION!r}): {plan_path}"
        )
    machine_lines = plan["machine_lines"]
    if not isinstance(machine_lines, dict):
        raise ValueError(f"plan machine_lines must be object: {plan_path}")
    status = machine_lines.get("CONTROL_PLANE_PLAN_STATUS")
    if status not in {"plan_only", "blocked"}:
        decision_status = plan.get("decision", {}).get("status")
        if decision_status in {"plan_only", "blocked"}:
            status = decision_status
        else:
            raise ValueError(f"unknown control plane plan status: {plan_path}")
    return str(status)


def _readiness_status(plan_status: str) -> str:
    if plan_status == "plan_only":
        return "ready_for_projection_planning"
    return "blocked"


def _readiness_reason(plan_status: str, case_id: str) -> str:
    if plan_status == "plan_only":
        return (
            f"case_id={case_id}: control plane plan is plan_only; "
            "projection payload planning may be prepared offline only"
        )
    return (
        f"case_id={case_id}: control plane plan is blocked; "
        "post-closeout projection planning remains blocked"
    )


def build_post_closeout_readiness_v0(
    plan: dict[str, Any],
    *,
    source_plan: str,
) -> dict[str, Any]:
    plan_status = _validate_plan(plan, Path(source_plan))
    readiness_status = _readiness_status(plan_status)
    can_prepare = plan_status == "plan_only"
    machine_lines = _build_readiness_machine_lines(readiness_status)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_plan": source_plan,
        "source_plan_schema_version": SOURCE_PLAN_SCHEMA_VERSION,
        "case_id": plan["case_id"],
        "control_plane_plan_status": plan_status,
        "planning_only": True,
        "non_authorizing": True,
        "closeout_invoke_authorized": False,
        "projection_invoke_authorized": False,
        "notion_sync_authorized": False,
        "durable_copy_authorized": False,
        "primary_evidence_retention_invoke_authorized": False,
        "readiness": {
            "can_prepare_post_closeout_projection_payload": can_prepare,
            "reason": _readiness_reason(plan_status, plan["case_id"]),
        },
        "owners": {
            "closeout_projection_chain_test": OWNER_CLOSEOUT_CHAIN_TEST,
            "projection_builder": OWNER_PROJECTION_BUILDER,
            "notion_dry_run": OWNER_NOTION_DRY_RUN,
            "durable_copy_verify": OWNER_DURABLE_COPY_VERIFY,
        },
        "machine_lines": machine_lines,
    }


def _build_readiness_machine_lines(readiness_status: str) -> dict[str, str]:
    return {
        "CONTROL_PLANE_POST_CLOSEOUT_READINESS_V0": "true",
        "CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS": readiness_status,
        "PLANNING_ONLY": "true",
        "CLOSEOUT_INVOKE_AUTHORIZED": "false",
        "PROJECTION_INVOKE_AUTHORIZED": "false",
        "NOTION_SYNC_AUTHORIZED": "false",
        "DURABLE_COPY_AUTHORIZED": "false",
        "PRIMARY_EVIDENCE_RETENTION_INVOKE_AUTHORIZED": "false",
        "RUNTIME_START_REQUIRED": "false",
        "SCHEDULER_START_REQUIRED": "false",
        "SUPERVISOR_START_REQUIRED": "false",
        "DAEMON_START_REQUIRED": "false",
        "PAPER_SHADOW_TESTNET_LIVE_START_REQUIRED": "false",
        "AWS_REMOTE_REQUIRED": "false",
        "S3_UPLOAD_REQUIRED": "false",
        "SSH_REQUIRED": "false",
        "NETWORK_REQUIRED": "false",
        "LIVE_AUTHORITY_CHANGED": "false",
        "MASTER_V2_DOUBLE_PLAY_TOUCHED": "false",
    }


def _write_machine_lines_file(path: Path, machine_lines: dict[str, str]) -> None:
    ordered = sorted(machine_lines.items())
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_readiness_markdown(path: Path, readiness: dict[str, Any]) -> None:
    lines = [
        "# Control Plane Post-Closeout Readiness v0",
        "",
        f"- case_id: `{readiness['case_id']}`",
        f"- control_plane_plan_status: `{readiness['control_plane_plan_status']}`",
        f"- readiness_status: `{readiness['machine_lines']['CONTROL_PLANE_POST_CLOSEOUT_READINESS_STATUS']}`",
        f"- planning_only: `{readiness['planning_only']}`",
        f"- closeout_invoke_authorized: `{readiness['closeout_invoke_authorized']}`",
        "",
        f"Reason: {readiness['readiness']['reason']}",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readiness_artifacts_v0(outdir: Path, readiness: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / READINESS_JSON_FILENAME).write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines_file(
        outdir / READINESS_MACHINE_LINES_FILENAME,
        readiness["machine_lines"],
    )
    _write_readiness_markdown(outdir / READINESS_MD_FILENAME, readiness)


def run_bridge(*, plan_path: Path, outdir: Path) -> dict[str, Any]:
    plan = _load_json(plan_path)
    readiness = build_post_closeout_readiness_v0(
        plan,
        source_plan=str(plan_path.resolve()),
    )
    write_readiness_artifacts_v0(outdir, readiness)
    return readiness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bridge control plane plan output to post-closeout readiness (offline only)."
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        readiness = run_bridge(
            plan_path=args.plan.resolve(),
            outdir=args.outdir.resolve(),
        )
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    for key in READINESS_MACHINE_LINE_KEYS:
        sys.stdout.write(f"{key}={readiness['machine_lines'][key]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
