"""Synthetic source-bound SRP payload builder contract tests.

These tests model payload-building semantics from synthetic resolver output
only. They do not import production report code, read real registries, read
generated artifacts, or bind real sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATIC_SRP_V0_CONTRACT = "report_live_sessions.session_review_pack_v0"
SOURCE_BOUND_CONTRACT = "report_live_sessions.session_review_pack_source_bound_v0"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def synthetic_valid_resolver_output(*, events_present: bool = True) -> dict[str, Any]:
    missing_fields: list[str] = []
    review_state = "reference_candidate"
    if not events_present:
        missing_fields.append("references.execution_events_session_jsonl")
        review_state = "needs_review"

    return {
        "contract": "synthetic.session_review_pack_source_bound_temp_resolver_v0",
        "valid": True,
        "non_authorizing": True,
        "selection": {"mode": "explicit_session_id", "session_id": "session_a"},
        "registry_session_record": {
            "source_class": "registry_session_record",
            "registry_file": "a.json",
            "session_id": "session_a",
            "status": "started",
            "authority": dict(AUTHORITY_FLAGS),
        },
        "references": {
            "execution_events_session_jsonl": {
                "source_class": "scoped_execution_events_pointer",
                "present": events_present,
                "review_state": review_state,
                "authority": dict(AUTHORITY_FLAGS),
            }
        },
        "missing_fields": missing_fields,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def synthetic_invalid_resolver_output() -> dict[str, Any]:
    return {
        "contract": "synthetic.session_review_pack_source_bound_temp_resolver_v0",
        "valid": False,
        "non_authorizing": True,
        "error": "selected_session_id_not_found_or_not_unique",
        "missing_fields": ["source.registry_session_record"],
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def build_source_bound_srp_payload(resolver_output: dict[str, Any]) -> dict[str, Any]:
    if not resolver_output.get("valid"):
        return {
            "contract": SOURCE_BOUND_CONTRACT,
            "static_contract": STATIC_SRP_V0_CONTRACT,
            "valid": False,
            "non_authorizing": True,
            "error": resolver_output.get("error", "resolver_output_invalid"),
            "missing_fields": sorted(resolver_output.get("missing_fields", [])),
            "authority_boundary": dict(AUTHORITY_FLAGS),
        }

    registry_record = resolver_output["registry_session_record"]
    event_pointer = resolver_output["references"]["execution_events_session_jsonl"]

    return {
        "contract": SOURCE_BOUND_CONTRACT,
        "static_contract": STATIC_SRP_V0_CONTRACT,
        "valid": True,
        "non_authorizing": True,
        "selection": dict(resolver_output["selection"]),
        "session": {
            "session_id": registry_record["session_id"],
            "status": registry_record["status"],
            "source_class": registry_record["source_class"],
            "registry_file": registry_record["registry_file"],
            "authority": dict(AUTHORITY_FLAGS),
        },
        "references": {
            "execution_events_session_jsonl": {
                "source_class": event_pointer["source_class"],
                "present": event_pointer["present"],
                "review_state": event_pointer["review_state"],
                "authority": dict(AUTHORITY_FLAGS),
            }
        },
        "missing_fields": sorted(resolver_output.get("missing_fields", [])),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def assert_authority_false(payload: dict[str, Any]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    if "session" in payload:
        assert payload["session"]["authority"] == AUTHORITY_FLAGS
    for reference in payload.get("references", {}).values():
        assert reference["authority"] == AUTHORITY_FLAGS


def test_valid_resolver_output_builds_distinct_source_bound_payload() -> None:
    payload = build_source_bound_srp_payload(synthetic_valid_resolver_output())

    assert payload["valid"] is True
    assert payload["contract"] == SOURCE_BOUND_CONTRACT
    assert payload["static_contract"] == STATIC_SRP_V0_CONTRACT
    assert payload["contract"] != payload["static_contract"]
    assert payload["non_authorizing"] is True
    assert_authority_false(payload)


def test_selected_session_metadata_is_carried_through() -> None:
    payload = build_source_bound_srp_payload(synthetic_valid_resolver_output())

    assert payload["selection"] == {"mode": "explicit_session_id", "session_id": "session_a"}
    assert payload["session"] == {
        "session_id": "session_a",
        "status": "started",
        "source_class": "registry_session_record",
        "registry_file": "a.json",
        "authority": AUTHORITY_FLAGS,
    }


def test_events_present_true_is_reference_candidate_only() -> None:
    payload = build_source_bound_srp_payload(synthetic_valid_resolver_output(events_present=True))

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["present"] is True
    assert pointer["review_state"] == "reference_candidate"
    assert pointer["source_class"] == "scoped_execution_events_pointer"
    assert payload["missing_fields"] == []
    assert_authority_false(payload)


def test_events_present_false_stays_needs_review_and_missing_field() -> None:
    payload = build_source_bound_srp_payload(synthetic_valid_resolver_output(events_present=False))

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["present"] is False
    assert pointer["review_state"] == "needs_review"
    assert payload["missing_fields"] == ["references.execution_events_session_jsonl"]
    assert_authority_false(payload)


def test_invalid_resolver_output_fail_closes_and_preserves_error() -> None:
    payload = build_source_bound_srp_payload(synthetic_invalid_resolver_output())

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["contract"] == SOURCE_BOUND_CONTRACT
    assert payload["static_contract"] == STATIC_SRP_V0_CONTRACT
    assert_authority_false(payload)


def test_resolver_missing_fields_are_preserved() -> None:
    payload = build_source_bound_srp_payload(synthetic_invalid_resolver_output())

    assert payload["missing_fields"] == ["source.registry_session_record"]


def test_static_srp_v0_contract_is_not_reused_for_source_bound_payload() -> None:
    payload = build_source_bound_srp_payload(synthetic_valid_resolver_output())

    assert payload["contract"] != STATIC_SRP_V0_CONTRACT
    assert payload["static_contract"] == STATIC_SRP_V0_CONTRACT


def test_serialized_payload_contains_no_unqualified_authority_claims() -> None:
    payloads = [
        build_source_bound_srp_payload(synthetic_valid_resolver_output(events_present=True)),
        build_source_bound_srp_payload(synthetic_valid_resolver_output(events_present=False)),
        build_source_bound_srp_payload(synthetic_invalid_resolver_output()),
    ]

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

    for payload in payloads:
        serialized = json.dumps(payload, sort_keys=True).lower()
        for claim in forbidden_claims:
            assert claim not in serialized


def test_this_payload_builder_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
