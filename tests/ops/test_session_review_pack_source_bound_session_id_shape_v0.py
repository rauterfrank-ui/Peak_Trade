"""Synthetic source-bound SRP session-id shape tests.

These tests model a future source-bound Session Review Pack shape with explicit
operator-selected session identity. They do not implement CLI flags, import
report code, read real registries, or bind real sessions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATIC_SRP_V0_CONTRACT = "report_live_sessions.session_review_pack_v0"
SOURCE_BOUND_SRP_CONTRACT = "report_live_sessions.session_review_pack_source_bound_v0"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


@dataclass(frozen=True)
class SyntheticSessionCandidate:
    session_id: str
    status: str = "started"
    execution_events_present: bool | None = True


def build_source_bound_srp_shape(
    *,
    candidates: list[SyntheticSessionCandidate],
    selected_session_id: str | None,
) -> dict[str, Any]:
    if selected_session_id is None:
        return {
            "contract": SOURCE_BOUND_SRP_CONTRACT,
            "valid": False,
            "error": "explicit_session_id_required",
            "non_authorizing": True,
            "authority_boundary": dict(AUTHORITY_FLAGS),
            "candidate_count": len(candidates),
            "missing_fields": ["selection.session_id"],
        }

    matches = [candidate for candidate in candidates if candidate.session_id == selected_session_id]
    if len(matches) != 1:
        return {
            "contract": SOURCE_BOUND_SRP_CONTRACT,
            "valid": False,
            "error": "selected_session_id_not_found_or_not_unique",
            "non_authorizing": True,
            "authority_boundary": dict(AUTHORITY_FLAGS),
            "candidate_count": len(candidates),
            "selected_session_id": selected_session_id,
            "missing_fields": ["source.registry_session_record"],
        }

    selected = matches[0]
    missing_fields: list[str] = []
    if selected.execution_events_present is None:
        missing_fields.append("references.execution_events_session_jsonl.present")
        events_reference = {
            "present": None,
            "review_state": "missing",
            "source_class": "scoped_execution_events_unknown",
            "authority": dict(AUTHORITY_FLAGS),
        }
    elif selected.execution_events_present:
        events_reference = {
            "present": True,
            "review_state": "reference_candidate",
            "source_class": "scoped_execution_events_present_true",
            "authority": dict(AUTHORITY_FLAGS),
        }
    else:
        missing_fields.append("references.execution_events_session_jsonl")
        events_reference = {
            "present": False,
            "review_state": "needs_review",
            "source_class": "scoped_execution_events_present_false",
            "authority": dict(AUTHORITY_FLAGS),
        }

    return {
        "contract": SOURCE_BOUND_SRP_CONTRACT,
        "static_contract": STATIC_SRP_V0_CONTRACT,
        "valid": True,
        "non_authorizing": True,
        "selection": {
            "mode": "explicit_session_id",
            "session_id": selected.session_id,
            "auto_primacy": False,
        },
        "session": {
            "session_id": selected.session_id,
            "status": selected.status,
            "source_class": "registry_session_record",
        },
        "references": {
            "execution_events_session_jsonl": events_reference,
        },
        "missing_fields": sorted(missing_fields),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def assert_authority_false(payload: dict[str, Any]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    for reference in payload.get("references", {}).values():
        assert reference["authority"] == AUTHORITY_FLAGS


def test_source_bound_contract_is_distinct_from_static_srp_v0() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[SyntheticSessionCandidate(session_id="session_a")],
        selected_session_id="session_a",
    )

    assert payload["contract"] == SOURCE_BOUND_SRP_CONTRACT
    assert payload["static_contract"] == STATIC_SRP_V0_CONTRACT
    assert payload["contract"] != payload["static_contract"]


def test_explicit_session_id_is_required() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[SyntheticSessionCandidate(session_id="session_a")],
        selected_session_id=None,
    )

    assert payload["valid"] is False
    assert payload["error"] == "explicit_session_id_required"
    assert payload["missing_fields"] == ["selection.session_id"]
    assert payload["non_authorizing"] is True
    assert_authority_false(payload)


def test_multiple_candidates_without_explicit_selection_fail_closed() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_a"),
            SyntheticSessionCandidate(session_id="session_b"),
        ],
        selected_session_id=None,
    )

    assert payload["valid"] is False
    assert payload["candidate_count"] == 2
    assert payload["error"] == "explicit_session_id_required"
    assert "selection.session_id" in payload["missing_fields"]
    assert_authority_false(payload)


def test_selected_session_id_chooses_exactly_one_synthetic_source() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_a"),
            SyntheticSessionCandidate(session_id="session_b"),
        ],
        selected_session_id="session_b",
    )

    assert payload["valid"] is True
    assert payload["selection"] == {
        "mode": "explicit_session_id",
        "session_id": "session_b",
        "auto_primacy": False,
    }
    assert payload["session"]["session_id"] == "session_b"
    assert payload["session"]["source_class"] == "registry_session_record"
    assert payload["missing_fields"] == []


def test_selected_session_with_events_present_is_reference_candidate_only() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_a", execution_events_present=True)
        ],
        selected_session_id="session_a",
    )

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["present"] is True
    assert pointer["review_state"] == "reference_candidate"
    assert pointer["source_class"] == "scoped_execution_events_present_true"
    assert pointer["authority"] == AUTHORITY_FLAGS
    assert_authority_false(payload)


def test_selected_session_with_events_missing_stays_needs_review() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_a", execution_events_present=False)
        ],
        selected_session_id="session_a",
    )

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["present"] is False
    assert pointer["review_state"] == "needs_review"
    assert pointer["source_class"] == "scoped_execution_events_present_false"
    assert "references.execution_events_session_jsonl" in payload["missing_fields"]
    assert_authority_false(payload)


def test_unknown_events_presence_is_missing_field_not_authority() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_a", execution_events_present=None)
        ],
        selected_session_id="session_a",
    )

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["present"] is None
    assert pointer["review_state"] == "missing"
    assert pointer["source_class"] == "scoped_execution_events_unknown"
    assert "references.execution_events_session_jsonl.present" in payload["missing_fields"]
    assert_authority_false(payload)


def test_serialized_output_contains_no_unqualified_authority_claims() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[SyntheticSessionCandidate(session_id="session_a")],
        selected_session_id="session_a",
    )
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_claims = [
        "live authorization granted",
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


def test_this_shape_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text


def test_selected_session_id_not_found_fails_closed() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[SyntheticSessionCandidate(session_id="session_a")],
        selected_session_id="session_missing",
    )

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["selected_session_id"] == "session_missing"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_duplicate_selected_session_id_fails_closed_not_unique() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[
            SyntheticSessionCandidate(session_id="session_duplicate"),
            SyntheticSessionCandidate(session_id="session_duplicate"),
        ],
        selected_session_id="session_duplicate",
    )

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["selected_session_id"] == "session_duplicate"
    assert payload["candidate_count"] == 2
    assert "source.registry_session_record" in payload["missing_fields"]
    assert_authority_false(payload)


def test_empty_candidate_list_with_explicit_session_id_fails_closed() -> None:
    payload = build_source_bound_srp_shape(
        candidates=[],
        selected_session_id="session_a",
    )

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["candidate_count"] == 0
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_blank_selected_session_id_fails_closed_as_missing_selector() -> None:
    selected_session_id = ""
    normalized_selected_session_id = selected_session_id or None

    payload = build_source_bound_srp_shape(
        candidates=[SyntheticSessionCandidate(session_id="session_a")],
        selected_session_id=normalized_selected_session_id,
    )

    assert payload["valid"] is False
    assert payload["error"] == "explicit_session_id_required"
    assert payload["missing_fields"] == ["selection.session_id"]
    assert_authority_false(payload)


def test_unsupported_malformed_candidate_does_not_match_and_fails_closed() -> None:
    malformed_candidate = SyntheticSessionCandidate(session_id="unsupported_source")
    payload = build_source_bound_srp_shape(
        candidates=[malformed_candidate],
        selected_session_id="session_a",
    )

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)
