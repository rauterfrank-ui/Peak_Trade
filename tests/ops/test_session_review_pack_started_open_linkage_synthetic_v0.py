"""Synthetic SRP started/open session linkage characterization tests.

These tests model Session Review Pack source classes for started/open
bounded-pilot sessions without reading real registries, generated artifacts, or
operator export trees under the repo. They pin review semantics only and do not
bind real sessions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


@dataclass(frozen=True)
class SyntheticStartedOpenSource:
    session_id: str | None = "session_synthetic_started"
    status: str | None = "started"
    execution_events_present: bool | None = True
    closeout_summary_state: str | None = "REGISTRY_NON_TERMINAL_NEWEST_ONLY"
    lifecycle_consistency_state: str | None = "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED"
    operator_review_runbook: str | None = (
        "docs/ops/runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md"
    )


def build_synthetic_srp_started_open_linkage(source: SyntheticStartedOpenSource) -> dict[str, Any]:
    missing_fields: list[str] = []

    session: dict[str, Any] = {
        "session_id": source.session_id,
        "status": source.status,
        "source_class": "registry_session_record",
    }
    if source.session_id is None:
        missing_fields.append("session.session_id")
    if source.status is None:
        missing_fields.append("session.status")

    references: dict[str, Any] = {}

    if source.execution_events_present is None:
        missing_fields.append("references.execution_events_session_jsonl.present")
        references["execution_events_session_jsonl"] = {
            "source_class": "scoped_execution_events_unknown",
            "present": None,
            "review_state": "missing",
            "authority": dict(AUTHORITY_FLAGS),
        }
    elif source.execution_events_present:
        references["execution_events_session_jsonl"] = {
            "source_class": "scoped_execution_events_present_true",
            "present": True,
            "review_state": "reference_candidate",
            "authority": dict(AUTHORITY_FLAGS),
        }
    else:
        missing_fields.append("references.execution_events_session_jsonl")
        references["execution_events_session_jsonl"] = {
            "source_class": "scoped_execution_events_present_false",
            "present": False,
            "review_state": "needs_review",
            "authority": dict(AUTHORITY_FLAGS),
        }

    if source.closeout_summary_state is None:
        missing_fields.append("references.closeout_summary_state")
    references["closeout_summary"] = {
        "source_class": "closeout_summary_state",
        "state": source.closeout_summary_state,
        "review_state": "review_only" if source.closeout_summary_state else "missing",
        "authority": dict(AUTHORITY_FLAGS),
    }

    if source.lifecycle_consistency_state is None:
        missing_fields.append("references.lifecycle_consistency_state")
    references["lifecycle_consistency"] = {
        "source_class": "lifecycle_consistency_state",
        "state": source.lifecycle_consistency_state,
        "review_state": "review_only" if source.lifecycle_consistency_state else "missing",
        "authority": dict(AUTHORITY_FLAGS),
    }

    if source.operator_review_runbook is None:
        missing_fields.append("references.operator_review_runbook")
    references["operator_review_runbook"] = {
        "source_class": "operator_review_runbook",
        "path": source.operator_review_runbook,
        "review_state": "reference_candidate" if source.operator_review_runbook else "missing",
        "authority": dict(AUTHORITY_FLAGS),
    }

    return {
        "contract": "synthetic.session_review_pack.started_open_linkage.v0",
        "non_authorizing": True,
        "session": session,
        "references": references,
        "missing_fields": sorted(missing_fields),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def _assert_all_authority_flags_false(payload: dict[str, Any]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS

    for reference in payload["references"].values():
        assert reference["authority"] == AUTHORITY_FLAGS


def test_started_open_registry_source_maps_to_non_authorizing_srp_like_payload() -> None:
    payload = build_synthetic_srp_started_open_linkage(SyntheticStartedOpenSource())

    assert payload["contract"] == "synthetic.session_review_pack.started_open_linkage.v0"
    assert payload["non_authorizing"] is True
    assert payload["session"] == {
        "session_id": "session_synthetic_started",
        "status": "started",
        "source_class": "registry_session_record",
    }
    assert payload["missing_fields"] == []
    _assert_all_authority_flags_false(payload)


def test_execution_events_present_true_is_reference_candidate_only() -> None:
    payload = build_synthetic_srp_started_open_linkage(
        SyntheticStartedOpenSource(execution_events_present=True)
    )

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["source_class"] == "scoped_execution_events_present_true"
    assert pointer["present"] is True
    assert pointer["review_state"] == "reference_candidate"
    assert pointer["authority"] == AUTHORITY_FLAGS
    assert "references.execution_events_session_jsonl" not in payload["missing_fields"]


def test_execution_events_present_false_stays_explicit_missing_review_signal() -> None:
    payload = build_synthetic_srp_started_open_linkage(
        SyntheticStartedOpenSource(execution_events_present=False)
    )

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert pointer["source_class"] == "scoped_execution_events_present_false"
    assert pointer["present"] is False
    assert pointer["review_state"] == "needs_review"
    assert pointer["authority"] == AUTHORITY_FLAGS
    assert "references.execution_events_session_jsonl" in payload["missing_fields"]


def test_closeout_and_lifecycle_states_are_review_only_not_authority() -> None:
    payload = build_synthetic_srp_started_open_linkage(SyntheticStartedOpenSource())

    assert payload["references"]["closeout_summary"] == {
        "source_class": "closeout_summary_state",
        "state": "REGISTRY_NON_TERMINAL_NEWEST_ONLY",
        "review_state": "review_only",
        "authority": AUTHORITY_FLAGS,
    }
    assert payload["references"]["lifecycle_consistency"] == {
        "source_class": "lifecycle_consistency_state",
        "state": "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED",
        "review_state": "review_only",
        "authority": AUTHORITY_FLAGS,
    }
    _assert_all_authority_flags_false(payload)


def test_missing_source_classes_are_preserved_in_missing_fields() -> None:
    payload = build_synthetic_srp_started_open_linkage(
        SyntheticStartedOpenSource(
            session_id=None,
            status=None,
            execution_events_present=None,
            closeout_summary_state=None,
            lifecycle_consistency_state=None,
            operator_review_runbook=None,
        )
    )

    assert payload["missing_fields"] == [
        "references.closeout_summary_state",
        "references.execution_events_session_jsonl.present",
        "references.lifecycle_consistency_state",
        "references.operator_review_runbook",
        "session.session_id",
        "session.status",
    ]
    _assert_all_authority_flags_false(payload)


def test_serialized_payload_contains_no_unqualified_authority_claims() -> None:
    payload = build_synthetic_srp_started_open_linkage(SyntheticStartedOpenSource())
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


def test_this_synthetic_test_file_does_not_read_real_artifact_locations() -> None:
    assert __file__.endswith("test_session_review_pack_started_open_linkage_synthetic_v0.py")
    # Build at runtime so this module source never has to *contain* these contiguous substrings
    # in a string literal (the previous list-based form defeated its own static guard).
    registry_root = "/".join(("reports", "experiments", "live_sessions"))
    ops_out = "/".join(("out", "ops"))
    scoped_events = "/".join(("execution_events", "sessions"))
    live_reg = "_".join(("live", "session", "registry"))
    forbidden_runtime_fragments = (registry_root, ops_out, scoped_events, live_reg)
    with open(__file__, encoding="utf-8") as handle:
        source_text = handle.read()
    for fragment in forbidden_runtime_fragments:
        assert fragment not in source_text
