"""Validate a local GLB-018 operator decision packet.

This CLI is read-only. It validates an explicitly supplied JSON file and emits a
non-authorizing validation payload. It does not read registries, read artifacts,
mutate files, close sessions, or authorize live trading.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALIDATOR_CONTRACT = "glb018_decision_packet_validator_v0"
INPUT_CONTRACT = "operator_glb018_decision_packet_v0"

ALLOWED_DECISIONS = {
    "review_with_events",
    "evidence_missing_review",
    "defer_by_authority",
    "closeout_path_required",
    "stop",
}

EXPECTED_DECISION_COUNTS = {
    "closeout_path_required": 2,
    "evidence_missing_review": 3,
}

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def validate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if packet.get("contract") != INPUT_CONTRACT:
        errors.append("invalid_input_contract")

    if packet.get("non_authorizing") is not True:
        errors.append("non_authorizing_required")

    if packet.get("authority_boundary") != AUTHORITY_FLAGS:
        errors.append("authority_boundary_must_be_all_false")

    rows = packet.get("session_decisions")
    if not isinstance(rows, list):
        rows = []
        errors.append("session_decisions_must_be_list")

    if len(rows) != 5:
        errors.append("expected_exactly_5_session_decisions")

    seen: set[str] = set()
    actual_counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("session_decision_row_must_be_object")
            continue

        session_id = row.get("session_id")
        decision = row.get("operator_decision")

        if not session_id:
            errors.append("missing_session_id")
        elif session_id in seen:
            errors.append("duplicate_session_id")
        else:
            seen.add(session_id)

        if decision not in ALLOWED_DECISIONS:
            errors.append("invalid_operator_decision")
        else:
            actual_counts[decision] = actual_counts.get(decision, 0) + 1

    if actual_counts != EXPECTED_DECISION_COUNTS:
        errors.append("unexpected_decision_counts")

    if packet.get("decision_counts") != EXPECTED_DECISION_COUNTS:
        errors.append("reported_decision_counts_mismatch")

    return {
        "contract": VALIDATOR_CONTRACT,
        "input_contract": packet.get("contract"),
        "ok": not errors,
        "errors": sorted(set(errors)),
        "warnings": warnings,
        "non_authorizing": True,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def load_packet(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        packet = json.load(fh)
    if not isinstance(packet, dict):
        raise ValueError("packet JSON root must be an object")
    return packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a local GLB-018 operator decision packet."
    )
    parser.add_argument(
        "--packet",
        required=True,
        type=Path,
        help="Path to operator_glb018_decision_packet_v0 JSON.",
    )
    parser.add_argument("--json", action="store_true", required=True, help="Emit JSON to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        packet = load_packet(args.packet)
    except Exception as exc:
        result = {
            "contract": VALIDATOR_CONTRACT,
            "input_contract": None,
            "ok": False,
            "errors": ["packet_read_or_parse_failed"],
            "warnings": [f"{type(exc).__name__}: {exc}"],
            "non_authorizing": True,
            "authority_boundary": dict(AUTHORITY_FLAGS),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    result = validate_packet(packet)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
