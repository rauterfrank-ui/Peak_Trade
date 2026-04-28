"""Synthetic GLB-018 decision-packet validator contract tests.

These tests characterize a future non-authorizing validator surface. They do
not import production validator code, read real registries, read generated
artifacts, close sessions, or authorize live trading.
"""

from __future__ import annotations

import copy
import json
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


def canonical_packet() -> dict[str, Any]:
    rows = [
        {
            "session_id": "session_20260319_152033_bounded_pilot_8e5f2c",
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260319_151416_bounded_pilot_579507",
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260318_154852_bounded_pilot_979b86",
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122341_bounded_pilot_02c8eb",
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122123_bounded_pilot_8c7be9",
            "operator_decision": "evidence_missing_review",
        },
    ]
    return {
        "contract": INPUT_CONTRACT,
        "non_authorizing": True,
        "session_decisions": rows,
        "decision_counts": dict(EXPECTED_DECISION_COUNTS),
        "operator_decision_required": True,
        "authority_boundary": dict(AUTHORITY_FLAGS),
        "hard_boundaries": [
            "do_not_mutate_registry_json",
            "do_not_mutate_out_ops",
            "do_not_close_sessions_from_this_packet",
            "do_not_infer_live_readiness",
            "do_not_authorize_live_trading",
        ],
    }


def validate_glb018_decision_packet_v0(packet: dict[str, Any]) -> dict[str, Any]:
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

    expected_reported_counts = packet.get("decision_counts")
    if expected_reported_counts != EXPECTED_DECISION_COUNTS:
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


def assert_validator_non_authorizing(result: dict[str, Any]) -> None:
    assert result["non_authorizing"] is True
    assert result["authority_boundary"] == AUTHORITY_FLAGS


def test_valid_canonical_packet_passes() -> None:
    result = validate_glb018_decision_packet_v0(canonical_packet())

    assert result == {
        "contract": VALIDATOR_CONTRACT,
        "input_contract": INPUT_CONTRACT,
        "ok": True,
        "errors": [],
        "warnings": [],
        "non_authorizing": True,
        "authority_boundary": AUTHORITY_FLAGS,
    }


def test_invalid_input_contract_fails_closed() -> None:
    packet = canonical_packet()
    packet["contract"] = "wrong_contract"

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "invalid_input_contract" in result["errors"]
    assert_validator_non_authorizing(result)


def test_missing_non_authorizing_fails_closed() -> None:
    packet = canonical_packet()
    packet["non_authorizing"] = False

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "non_authorizing_required" in result["errors"]
    assert_validator_non_authorizing(result)


def test_true_authority_flag_fails_closed() -> None:
    packet = canonical_packet()
    packet["authority_boundary"] = {**AUTHORITY_FLAGS, "live_authorization": True}

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "authority_boundary_must_be_all_false" in result["errors"]
    assert_validator_non_authorizing(result)


def test_invalid_operator_decision_fails_closed() -> None:
    packet = canonical_packet()
    packet["session_decisions"][0]["operator_decision"] = "approve_live"

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "invalid_operator_decision" in result["errors"]
    assert "unexpected_decision_counts" in result["errors"]


def test_missing_session_decision_fails_closed() -> None:
    packet = canonical_packet()
    packet["session_decisions"] = packet["session_decisions"][:4]

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "expected_exactly_5_session_decisions" in result["errors"]
    assert "unexpected_decision_counts" in result["errors"]


def test_duplicate_session_id_fails_closed() -> None:
    packet = canonical_packet()
    packet["session_decisions"][1]["session_id"] = packet["session_decisions"][0]["session_id"]

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "duplicate_session_id" in result["errors"]


def test_reported_decision_count_mismatch_fails_closed() -> None:
    packet = canonical_packet()
    packet["decision_counts"] = {"closeout_path_required": 5}

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "reported_decision_counts_mismatch" in result["errors"]


def test_actual_decision_count_mismatch_fails_closed() -> None:
    packet = canonical_packet()
    packet["session_decisions"][0]["operator_decision"] = "evidence_missing_review"

    result = validate_glb018_decision_packet_v0(packet)

    assert result["ok"] is False
    assert "unexpected_decision_counts" in result["errors"]


def test_validator_output_contains_no_unqualified_authority_claims() -> None:
    result = validate_glb018_decision_packet_v0(canonical_packet())
    serialized = json.dumps(result, sort_keys=True).lower()

    forbidden_claims = [
        "live authorization granted",
        "bounded pilot approved",
        "closeout approved",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "externally authorized",
        "approved for live",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in serialized


def test_validator_does_not_mutate_input_packet() -> None:
    packet = canonical_packet()
    before = copy.deepcopy(packet)

    validate_glb018_decision_packet_v0(packet)

    assert packet == before


def test_this_validator_contract_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
