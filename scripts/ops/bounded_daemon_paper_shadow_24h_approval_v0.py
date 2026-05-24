"""24h bounded Daemon Paper/Shadow approval contract validator v0.

Non-authorizing: validates machine-line approval records only.
Does not clear HOLD, start runtime, or grant Testnet/Live/broker authority.
"""

from __future__ import annotations

from typing import Mapping

CONTRACT_PROFILE = "daemon_paper_shadow_24h_v0"

REQUIRED_APPROVAL = {
    "APPROVE_EXECUTE_BOUNDED_24H_DAEMON_PAPER_SHADOW_DRY_RUN_NOW": "true",
    "PAPER_LANE_AUTHORIZED": "true",
    "SHADOW_LANE_AUTHORIZED": "true",
    "NO_AUTOMATIC_24H_72H_RERUN_REQUIRED": "true",
}

FORBIDDEN_APPROVAL_TRUE = frozenset(
    {
        "START_TESTNET_NOW",
        "START_LIVE_NOW",
        "LIVE_ALLOWED",
        "BROKER_EXCHANGE_ALLOWED",
        "BLOCKER_CLEARANCE_GRANTED",
    }
)

DAEMON_PAPER_SHADOW_24H_DURATION_SECONDS = 86400
DAEMON_PAPER_SHADOW_24H_DURATION_MINUTES = 1440


def parse_machine_lines(text: str) -> dict[str, str]:
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


def validate_approval_record(
    fields: Mapping[str, str],
    *,
    approved_run_id: str,
) -> list[str]:
    issues: list[str] = []
    for key, expected in REQUIRED_APPROVAL.items():
        if fields.get(key, "").lower() != expected:
            issues.append(f"approval record missing or invalid: {key}={expected}")
    record_run_id = fields.get("APPROVED_RUN_ID", "").strip()
    if not record_run_id:
        issues.append("approval record missing: APPROVED_RUN_ID")
    elif record_run_id != approved_run_id:
        issues.append(
            f"APPROVED_RUN_ID mismatch: expected {approved_run_id!r}, got {record_run_id!r}"
        )
    for key in FORBIDDEN_APPROVAL_TRUE:
        if fields.get(key, "false").lower() == "true":
            issues.append(f"approval record forbids {key}=true")
    return issues


def validate_paper_duration_seconds(duration_seconds: int) -> list[str]:
    if duration_seconds != DAEMON_PAPER_SHADOW_24H_DURATION_SECONDS:
        return [
            "duration-seconds must equal "
            f"{DAEMON_PAPER_SHADOW_24H_DURATION_SECONDS} for {CONTRACT_PROFILE}"
        ]
    return []


def validate_shadow_duration_minutes(duration_minutes: int) -> list[str]:
    if duration_minutes != DAEMON_PAPER_SHADOW_24H_DURATION_MINUTES:
        return [
            "duration-minutes must equal "
            f"{DAEMON_PAPER_SHADOW_24H_DURATION_MINUTES} for {CONTRACT_PROFILE}"
        ]
    return []


def load_and_validate_approval_record(
    path_text: str,
    *,
    approved_run_id: str,
) -> tuple[dict[str, str], list[str]]:
    fields = parse_machine_lines(path_text)
    return fields, validate_approval_record(fields, approved_run_id=approved_run_id)
