#!/usr/bin/env python3
"""Offline Autonomous Ops Control Plane plan generator v0 (fixture-only, non-authorizing).

Reads a transition fixture JSON (PR #3755 schema) and writes local plan artifacts.
Does not start runtime, scheduler, supervisor, daemon, paper, shadow, testnet, or live.
Does not invoke child processes, network, AWS, S3, or SSH.

Machine marker: ``OFFLINE_CONTROL_PLANE_PLAN_GENERATOR_V0=true``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "control_plane_plan_v0"
PLAN_JSON_FILENAME = "CONTROL_PLANE_PLAN_V0.json"
PLAN_MACHINE_LINES_FILENAME = "CONTROL_PLANE_PLAN_MACHINE_LINES.txt"
PLAN_MD_FILENAME = "CONTROL_PLANE_PLAN_V0.md"

# Frozen literals aligned with tests/ops/test_autonomous_ops_control_plane_state_model_contract_v0.py
CONTROL_PLANE_STATES_V0: tuple[str, ...] = (
    "STOP_IDLE",
    "PREFLIGHT_BLOCKED",
    "PREFLIGHT_PASS",
    "READY_FOR_OPERATOR_TOKEN",
    "RUNNING",
    "CLOSEOUT_REQUIRED",
    "EVIDENCE_VERIFIED",
    "FAILED_CLOSED",
)

FORBIDDEN_TRANSITIONS_V0: frozenset[tuple[str, str]] = frozenset(
    {
        ("STOP_IDLE", "RUNNING"),
        ("PREFLIGHT_BLOCKED", "RUNNING"),
        ("PREFLIGHT_PASS", "RUNNING"),
        ("RUNNING", "EVIDENCE_VERIFIED"),
        ("FAILED_CLOSED", "RUNNING"),
        ("EVIDENCE_VERIFIED", "RUNNING"),
    }
)

REQUIRED_INTERMEDIATE_FOR_TARGET: dict[tuple[str, str], tuple[str, ...]] = {
    ("PREFLIGHT_PASS", "RUNNING"): ("READY_FOR_OPERATOR_TOKEN",),
    ("RUNNING", "EVIDENCE_VERIFIED"): ("CLOSEOUT_REQUIRED",),
}

REQUIRED_FIXTURE_KEYS: frozenset[str] = frozenset(
    {
        "case_id",
        "initial_state",
        "target_state",
        "steps",
        "expected_forbidden",
        "required_intermediate_states",
        "expected_machine_lines",
    }
)

CORE_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "OFFLINE_CONTROL_PLANE_PLAN_GENERATOR_V0",
    "CONTROL_PLANE_PLAN_STATUS",
    "CONTROL_PLANE_PLAN_NON_AUTHORIZING",
    "START_RUNTIME_NOW",
    "START_SCHEDULER_NOW",
    "START_SUPERVISOR_NOW",
    "START_DAEMON_NOW",
    "START_PAPER_SHADOW_TESTNET_LIVE_NOW",
    "AWS_REMOTE_REQUIRED",
    "S3_UPLOAD_REQUIRED",
    "SSH_REQUIRED",
    "NETWORK_REQUIRED",
    "LIVE_AUTHORITY_CHANGED",
    "MASTER_V2_DOUBLE_PLAY_TOUCHED",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _edges(steps: list[str]) -> list[tuple[str, str]]:
    return list(zip(steps, steps[1:]))


def _has_forbidden_direct_edge(steps: list[str]) -> bool:
    return any(edge in FORBIDDEN_TRANSITIONS_V0 for edge in _edges(steps))


def _missing_required_intermediate(steps: list[str]) -> bool:
    step_set = set(steps)
    for (src, dst), required in REQUIRED_INTERMEDIATE_FOR_TARGET.items():
        if src in step_set and dst in step_set:
            for mid in required:
                if mid not in step_set:
                    return True
    return False


def transition_violation(steps: list[str]) -> bool:
    return _has_forbidden_direct_edge(steps) or _missing_required_intermediate(steps)


def _validate_fixture(fixture: dict[str, Any], fixture_path: Path) -> None:
    missing = REQUIRED_FIXTURE_KEYS - fixture.keys()
    if missing:
        raise ValueError(f"fixture missing keys {sorted(missing)}: {fixture_path}")
    states = set(CONTROL_PLANE_STATES_V0)
    for key in ("initial_state", "target_state"):
        if fixture[key] not in states:
            raise ValueError(f"unknown state {fixture[key]!r} in {fixture_path}")
    steps = fixture["steps"]
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"steps must be a non-empty list: {fixture_path}")
    if steps[0] != fixture["initial_state"] or steps[-1] != fixture["target_state"]:
        raise ValueError(f"steps must begin/end at initial/target state: {fixture_path}")
    for step in steps:
        if step not in states:
            raise ValueError(f"unknown step state {step!r} in {fixture_path}")
    if not isinstance(fixture["expected_forbidden"], bool):
        raise ValueError(f"expected_forbidden must be bool: {fixture_path}")
    computed = transition_violation(steps)
    if fixture["expected_forbidden"] != computed:
        raise ValueError(
            f"expected_forbidden={fixture['expected_forbidden']} "
            f"does not match computed violation={computed}: {fixture_path}"
        )


def _plan_status(expected_forbidden: bool) -> str:
    return "blocked" if expected_forbidden else "plan_only"


def _build_decision(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "non_authorizing": True,
        "execute_authorized": False,
        "runtime_start_authorized": False,
        "scheduler_start_authorized": False,
        "supervisor_start_authorized": False,
        "daemon_start_authorized": False,
        "paper_shadow_testnet_live_start_authorized": False,
        "aws_remote_required": False,
        "s3_upload_required": False,
        "ssh_required": False,
        "network_required": False,
        "live_authority_changed": False,
        "master_v2_double_play_touched": False,
    }


def _build_machine_lines_dict(status: str) -> dict[str, str]:
    lines = {key: "false" for key in CORE_MACHINE_LINE_KEYS if key.startswith("START_")}
    lines.update(
        {
            "OFFLINE_CONTROL_PLANE_PLAN_GENERATOR_V0": "true",
            "CONTROL_PLANE_PLAN_STATUS": status,
            "CONTROL_PLANE_PLAN_NON_AUTHORIZING": "true",
            "START_RUNTIME_NOW": "false",
            "START_SCHEDULER_NOW": "false",
            "START_SUPERVISOR_NOW": "false",
            "START_DAEMON_NOW": "false",
            "START_PAPER_SHADOW_TESTNET_LIVE_NOW": "false",
            "AWS_REMOTE_REQUIRED": "false",
            "S3_UPLOAD_REQUIRED": "false",
            "SSH_REQUIRED": "false",
            "NETWORK_REQUIRED": "false",
            "LIVE_AUTHORITY_CHANGED": "false",
            "MASTER_V2_DOUBLE_PLAY_TOUCHED": "false",
        }
    )
    return lines


def build_control_plane_plan_v0(
    fixture: dict[str, Any],
    *,
    source_fixture: str,
) -> dict[str, Any]:
    status = _plan_status(fixture["expected_forbidden"])
    machine_lines = _build_machine_lines_dict(status)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_fixture": source_fixture,
        "case_id": fixture["case_id"],
        "initial_state": fixture["initial_state"],
        "target_state": fixture["target_state"],
        "steps": list(fixture["steps"]),
        "expected_forbidden": fixture["expected_forbidden"],
        "required_intermediate_states": list(fixture["required_intermediate_states"]),
        "decision": _build_decision(status),
        "machine_lines": machine_lines,
    }


def _write_machine_lines_file(path: Path, machine_lines: dict[str, str]) -> None:
    ordered = sorted(machine_lines.items())
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
        encoding="utf-8",
    )


def _write_plan_markdown(path: Path, plan: dict[str, Any]) -> None:
    decision = plan["decision"]
    lines = [
        "# Autonomous Ops Control Plane Plan v0",
        "",
        f"- case_id: `{plan['case_id']}`",
        f"- status: `{decision['status']}`",
        f"- non_authorizing: `{decision['non_authorizing']}`",
        f"- execute_authorized: `{decision['execute_authorized']}`",
        "",
        "## Steps",
        "",
    ]
    lines.extend(f"- `{step}`" for step in plan["steps"])
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plan_artifacts_v0(outdir: Path, plan: dict[str, Any]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / PLAN_JSON_FILENAME
    json_path.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_machine_lines_file(outdir / PLAN_MACHINE_LINES_FILENAME, plan["machine_lines"])
    _write_plan_markdown(outdir / PLAN_MD_FILENAME, plan)


def run_plan_generator(
    *,
    fixture_path: Path,
    outdir: Path,
) -> dict[str, Any]:
    fixture = _load_json(fixture_path)
    _validate_fixture(fixture, fixture_path)
    plan = build_control_plane_plan_v0(
        fixture,
        source_fixture=str(fixture_path.resolve()),
    )
    write_plan_artifacts_v0(outdir, plan)
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline Autonomous Ops Control Plane plan generator (fixture-only)."
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format (json only in v0).",
    )
    args = parser.parse_args(argv)
    _ = args.format

    try:
        plan = run_plan_generator(
            fixture_path=args.fixture.resolve(),
            outdir=args.outdir.resolve(),
        )
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    for key in CORE_MACHINE_LINE_KEYS:
        sys.stdout.write(f"{key}={plan['machine_lines'][key]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
