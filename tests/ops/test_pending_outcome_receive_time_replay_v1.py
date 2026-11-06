"""Replay a captured receipt time exactly; never reconstruct it by adding delay."""

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.resolver_v1 import (
    _normalized_from_ingest_detail_v1,
    _replay_producer_from_pending_events_v1,
    ingest_pending_outcome_mark_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    DECISION_REF,
    EVIDENCE_CLASS_TEST_FIXTURE,
    REPO_SHA,
    T_BAR1,
    _create_pending,
    _norm,
)


@pytest.fixture
def pending_case(tmp_path):
    from pathlib import Path

    root = Path(_create_pending(tmp_path))
    return root, load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)


def test_stored_fractional_receive_time_is_replayed_without_an_extra_second(pending_case):
    _root, pending = pending_case
    receive = T_BAR1 + 0.125
    detail = {"mark_px": 3500.0, "event_ts_unix": T_BAR1, "receive_ts_unix": receive}
    first = _normalized_from_ingest_detail_v1(pending, detail)
    second = _normalized_from_ingest_detail_v1(pending, detail)
    assert first.receive_ts_unix == second.receive_ts_unix == receive
    assert first.event_ts_unix == T_BAR1


def test_missing_receive_time_does_not_invent_a_receipt_from_event_time(pending_case):
    _root, pending = pending_case
    assert _normalized_from_ingest_detail_v1(
        pending, {"mark_px": 3500.0, "event_ts_unix": T_BAR1}
    ) is None


def test_actual_event_ledger_to_bar_replay_preserves_recorded_receive_time(pending_case):
    root, pending = pending_case
    observation = _norm(mark=3500.0, event_ts=T_BAR1)
    result = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=pending,
        normalized=observation,
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert result.advanced and not result.closed
    replayed = _replay_producer_from_pending_events_v1(
        lane_state_root=root, pending=result.record, repository_sha=REPO_SHA
    )
    bars = replayed.list_envelopes()
    assert len(bars) == 1
    assert bars[0]["receive_time"] == observation.receive_ts_unix
