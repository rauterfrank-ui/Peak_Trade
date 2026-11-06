"""Preserve stored correlation and exact producer identity across Pending creation."""

import json

from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import (
    maybe_create_natural_enter_pending_outcome_v1,
)
from tests.ops.test_pending_decision_parent_lineage_v1 import _setup


def test_pending_uses_verified_parent_correlation_instead_of_cycle_name_guess(tmp_path):
    path, args = _setup(tmp_path)
    parent = AppendOnlyDdoLedgerV0(path).get(args["reporting"].dpo["decision_event_ref"])
    assert parent["correlation_id"] == "ddo.corr.test"
    result = maybe_create_natural_enter_pending_outcome_v1(**args)
    assert result.created
    assert result.record.correlation_id == parent["correlation_id"]


def test_pending_records_existing_exact_policy_decision_id(tmp_path):
    _, args = _setup(tmp_path)
    producer = json.loads(args["reporting"].decision_context.producer_payload_json)
    result = maybe_create_natural_enter_pending_outcome_v1(**args)
    assert result.created
    assert result.record.decision_id == producer["policy_decision_id"]
    assert result.record.decision_id != result.record.decision_event_ref


def test_conflicting_caller_decision_id_is_rejected(tmp_path):
    _, args = _setup(tmp_path)
    result = maybe_create_natural_enter_pending_outcome_v1(
        **args, decision_id="other-policy-decision"
    )
    assert not result.created and result.reason == "PENDING_DECISION_LINEAGE_UNBOUND"


def test_actual_capture_parent_correlation_reaches_learning_closure(tmp_path, monkeypatch):
    from dataclasses import replace
    from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import _norm, REPO_SHA
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
        resolver_v1 as resolver,
    )
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
        EVIDENCE_CLASS_REAL_PUBLIC,
    )

    path, args = _setup(tmp_path)
    pending = maybe_create_natural_enter_pending_outcome_v1(**args).record
    first_open = (int(pending.decision_timestamp_unix) // 3600 + 1) * 3600
    # Explicit injected clock/source contract in a temporary ledger, not natural evidence.
    monkeypatch.setattr(resolver.time, "time", lambda: first_open + 7300.0)
    for event in (first_open + 1.0, first_open + 3601.0, first_open + 7200.0):
        normalized = replace(
            _norm(mark=1234.5, event_ts=event),
            canonical_instrument_id=pending.canonical_instrument_id,
            venue_instrument_id=pending.native_id,
        )
        result = resolver.ingest_pending_outcome_mark_observation_v1(
            lane_state_root=args["lane_state_root"],
            pending=pending,
            normalized=normalized,
            repository_sha=REPO_SHA,
            evidence_class=EVIDENCE_CLASS_REAL_PUBLIC,
        )
        pending = result.record
    assert result.closed, result.reason
    learned = [
        rec
        for rec in AppendOnlyDdoLedgerV0(path).read_all()
        if rec["schema_name"] == "learning_state_record"
    ]
    assert learned
    assert all(rec["correlation_id"] == "ddo.corr.test" for rec in learned)
