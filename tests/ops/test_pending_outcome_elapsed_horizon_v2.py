"""Pending marks must preserve in-progress samples and cannot close future bars."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    resolver_v1 as resolver,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    _events_path,
    lane_pending_lane_dir_v1,
    load_pending_outcome_by_decision_ref_v1,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    DECISION_REF,
    EVIDENCE_CLASS_TEST_FIXTURE,
    REPO_SHA,
    T_BAR1,
    T_BAR2,
    _create_pending,
    _norm,
)


def _ingest(root, ts, price=3500, source=EVIDENCE_CLASS_TEST_FIXTURE, **kwargs):
    pending = load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    return resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=pending,
        normalized=_norm(mark=price, event_ts=ts),
        repository_sha=REPO_SHA,
        evidence_class=source,
        allow_test_fixture=True,
        **kwargs,
    )


def test_first_sample_stays_in_progress_until_event_time_reaches_bar_end(tmp_path):
    root = Path(_create_pending(tmp_path))
    first = _ingest(root, T_BAR1)
    assert first.ok and not first.closed
    assert first.record.bars_observed == 0
    producer = resolver._replay_producer_from_pending_events_v1(
        lane_state_root=root,
        pending=first.record,
        repository_sha=REPO_SHA,
    )
    assert producer.list_envelopes()[0]["finalization_state"] == "IN_PROGRESS_BAR"


def test_same_bar_samples_survive_replay_and_update_actual_ohlc(tmp_path):
    root = Path(_create_pending(tmp_path))
    for ts, price in [(T_BAR1, 3500), (T_BAR1 + 1, 3520), (T_BAR1 + 2, 3490)]:
        out = _ingest(root, ts, price)
        assert out.ok and not out.duplicate
    producer = resolver._replay_producer_from_pending_events_v1(
        lane_state_root=root,
        pending=out.record,
        repository_sha=REPO_SHA,
    )
    bar = producer.list_envelopes()[0]
    assert (bar["open"], bar["high"], bar["low"], bar["close"], bar["sample_count"]) == (
        3500,
        3520,
        3490,
        3490,
        3,
    )
    assert bar["receive_time"] == T_BAR1 + 3


def test_two_samples_in_successive_bars_cannot_close_a_future_horizon(tmp_path):
    root = Path(_create_pending(tmp_path))
    _ingest(root, T_BAR1)
    out = _ingest(root, T_BAR2, 3510)
    assert out.ok and not out.closed
    assert out.record.bars_observed == 1
    assert not out.record.closure_refs


def test_explicit_fixture_never_enters_productive_evaluation(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))
    ledger = root / "LANE_1/ddo_learning_capture_v1.jsonl"
    before = ledger.read_bytes()
    calls = []
    monkeypatch.setattr(
        resolver,
        "invoke_productive_n_bars_horizon_observation_v1",
        lambda *a, **kw: calls.append(kw),
    )
    for ts in (T_BAR1, T_BAR2, (int(T_BAR2) // 3600 + 1) * 3600):
        out = _ingest(root, ts)
    assert out.record.bars_observed == 2
    assert not out.closed
    assert out.reason == "PENDING_OUTCOME_PROVENANCE_NOT_BOUND"
    assert calls == [] and ledger.read_bytes() == before


@pytest.mark.parametrize("evidence_class", ["UNKNOWN", "TEST_FIXTURE", "", "anything"])
def test_unknown_source_class_cannot_be_implicitly_productive(tmp_path, evidence_class):
    root = Path(_create_pending(tmp_path))
    pending = load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    events = _events_path(lane_pending_lane_dir_v1(root))
    before = events.read_bytes()
    out = resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=pending,
        normalized=_norm(mark=3500, event_ts=T_BAR1),
        repository_sha=REPO_SHA,
        evidence_class=evidence_class,
        allow_test_fixture=True,
    )
    assert not out.ok and out.reason == "PENDING_SOURCE_CLASS_UNSUPPORTED"
    assert events.read_bytes() == before


def test_fixture_history_cannot_be_upgraded_by_one_public_class_sample(tmp_path):
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
        EVIDENCE_CLASS_REAL_PUBLIC,
    )

    root = Path(_create_pending(tmp_path))
    _ingest(root, T_BAR1)
    before = _events_path(lane_pending_lane_dir_v1(root)).read_bytes()
    out = resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=load_pending_outcome_by_decision_ref_v1(root, DECISION_REF),
        normalized=_norm(mark=3510, event_ts=T_BAR2),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_REAL_PUBLIC,
    )
    assert not out.ok and out.reason == "PENDING_SOURCE_CLASS_CONFLICT"
    assert _events_path(lane_pending_lane_dir_v1(root)).read_bytes() == before


def test_legacy_event_contract_is_preserved_and_rejected(tmp_path):
    root = Path(_create_pending(tmp_path))
    out = _ingest(root, T_BAR1)
    events = _events_path(lane_pending_lane_dir_v1(root))
    rows = [json.loads(line) for line in events.read_text().splitlines()]
    rows[-1]["detail"].pop("mark_observation_contract", None)
    events.write_text("".join(json.dumps(row) + "\n" for row in rows))
    before = events.read_bytes()
    with pytest.raises(Exception, match="PENDING_MARK_HISTORY_CONTRACT_UNSUPPORTED"):
        resolver._replay_producer_from_pending_events_v1(
            lane_state_root=root,
            pending=out.record,
            repository_sha=REPO_SHA,
        )
    assert events.read_bytes() == before


@pytest.mark.parametrize(
    "change",
    [
        {"venue_instrument_id": "FOREIGN"},
        {"venue": "foreign"},
        {"mark_px": float("nan")},
        {"mark_px": -1},
        {"receive_ts_unix": T_BAR1 - 1},
        {"event_ts_unix": float("nan")},
    ],
)
def test_direct_normalized_ingest_rejects_invalid_source_before_mutation(tmp_path, change):
    root = Path(_create_pending(tmp_path))
    events = _events_path(lane_pending_lane_dir_v1(root))
    before = events.read_bytes()
    pending = load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    out = resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=pending,
        normalized=replace(_norm(mark=3500, event_ts=T_BAR1), **change),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert not out.ok
    assert events.read_bytes() == before


def test_public_input_contract_control_closes_only_elapsed_bars_with_measured_knowledge(
    tmp_path, monkeypatch
):
    # Injected public-input contract control, not a natural/source-authenticity witness.
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
        EVIDENCE_CLASS_REAL_PUBLIC,
    )

    root = Path(_create_pending(tmp_path))
    boundary = (int(T_BAR2) // 3600 + 1) * 3600
    knowledge = boundary + 5.25
    monkeypatch.setattr(resolver.time, "time", lambda: knowledge)
    calls = []
    original = resolver.invoke_productive_n_bars_horizon_observation_v1

    def observe(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(resolver, "invoke_productive_n_bars_horizon_observation_v1", observe)
    for ts, px in ((T_BAR1, 3500), (T_BAR1 + 10, 3505), (T_BAR2, 3510), (boundary, 3520)):
        out = _ingest(root, ts, px, source=EVIDENCE_CLASS_REAL_PUBLIC)
    assert out.ok and out.closed
    assert calls[-1]["event_ts_unix"] == knowledge
    bars = calls[-1]["o4_snapshot"]["o4_bars"]
    assert len(bars) == 2
    assert max(bar["bar_close_time"] for bar in bars) <= boundary
    assert bars[0]["close"] == 3505
    assert out.record.closure_refs["learning_state_record_ref"]


def test_closure_clock_before_recorded_receipt_is_rejected(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
        EVIDENCE_CLASS_REAL_PUBLIC,
    )

    root = Path(_create_pending(tmp_path))
    boundary = (int(T_BAR2) // 3600 + 1) * 3600
    monkeypatch.setattr(resolver.time, "time", lambda: boundary + 0.5)
    for ts in (T_BAR1, T_BAR2, boundary):
        out = _ingest(root, ts, source=EVIDENCE_CLASS_REAL_PUBLIC)
    assert not out.closed and out.reason == "PENDING_OBSERVATION_CLOCK_CONFLICT"


def test_duplicate_does_not_append_and_out_of_order_does_not_mutate(tmp_path):
    root = Path(_create_pending(tmp_path))
    _ingest(root, T_BAR1)
    _ingest(root, T_BAR1 + 10)
    path = _events_path(lane_pending_lane_dir_v1(root))
    before = path.read_bytes()
    duplicate = _ingest(root, T_BAR1 + 10)
    assert duplicate.duplicate and not duplicate.advanced
    rejected = _ingest(root, T_BAR1 + 5)
    assert not rejected.ok and rejected.reason == "PENDING_MARK_OUT_OF_ORDER"
    assert path.read_bytes() == before


def test_partial_pre_decision_bar_does_not_count_as_post_decision_horizon(tmp_path):
    root = Path(_create_pending(tmp_path))
    # T0 lies within the prior hour; its tail must not increment bars_observed.
    from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import T0

    _ingest(root, T0 + 10)
    out = _ingest(root, T_BAR1)
    assert out.record.bars_observed == 0
