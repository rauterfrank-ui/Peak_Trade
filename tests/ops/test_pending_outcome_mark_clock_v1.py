"""Mark event time and measured receipt must survive the pending-outcome seam."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    InjectedContinuousObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    session_integration_v1 as session,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.resolver_v1 import (
    advance_all_open_pending_from_mark_v1,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    CANON,
    EVIDENCE_CLASS_TEST_FIXTURE,
    NATIVE,
    REPO_SHA,
    T_BAR1,
    _create_pending,
)


def _observation(row):
    return InjectedContinuousObservationV1(
        candles_payload={"data": [[str(int((T_BAR1 - 1800) * 1000))]]},
        occupancy_payloads={},
        mark_price_payload={"code": "0", "data": [row]},
    )


def _row(**overrides):
    return {"instId": NATIVE, "markPx": "3500", "ts": str(int(T_BAR1 * 1000)), **overrides}


def _wrapper(tmp_path, observation):
    class Source:
        def poll(self):
            return observation

    return session.PendingOutcomeAdvanceObservationSourceV1(
        inner=Source(),
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "ev",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        repository_sha=REPO_SHA,
    )


def test_wrapper_forwards_mark_row_time_and_measured_poll_receipt(tmp_path, monkeypatch):
    # Patch the clock module so the pre-fix module need not already import it.
    monkeypatch.setattr("time.time", lambda: T_BAR1 + 0.375)
    calls = []
    monkeypatch.setattr(
        session, "advance_all_open_pending_from_mark_v1", lambda **kw: calls.append(kw)
    )
    observation = _observation(_row(ts=str(int(T_BAR1 * 1000) + 125)))
    assert _wrapper(tmp_path, observation).poll() is observation
    assert len(calls) == 1
    assert calls[0]["event_ts_unix"] == T_BAR1 + 0.125
    assert calls[0]["receive_ts_unix"] == T_BAR1 + 0.375


@pytest.mark.parametrize(
    "row",
    [
        _row(ts=None),
        _row(ts=""),
        _row(ts="nan"),
        _row(ts="inf"),
        _row(ts=True),
        _row(ts="-1"),
        _row(ts="123.5"),
        _row(ts=str(int((T_BAR1 + 100) * 1000))),
        _row(instId="OTHER-SWAP"),
        _row(markPx="nan"),
    ],
)
def test_invalid_mark_identity_or_time_does_not_advance(tmp_path, monkeypatch, row):
    monkeypatch.setattr("time.time", lambda: T_BAR1 + 0.375)
    calls = []
    monkeypatch.setattr(
        session, "advance_all_open_pending_from_mark_v1", lambda **kw: calls.append(kw)
    )
    observation = _observation(row)
    assert _wrapper(tmp_path, observation).poll() is observation
    assert calls == []
    assert not (tmp_path / "lane").exists()


def test_mark_time_does_not_require_a_candle_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr("time.time", lambda: T_BAR1 + 0.375)
    calls = []
    monkeypatch.setattr(
        session, "advance_all_open_pending_from_mark_v1", lambda **kw: calls.append(kw)
    )
    observation = replace(_observation(_row()), candles_payload={"data": []})
    assert _wrapper(tmp_path, observation).poll() is observation
    assert len(calls) == 1


def test_explicit_receipt_reaches_stored_event_and_replay(tmp_path):
    root = Path(_create_pending(tmp_path))
    result = advance_all_open_pending_from_mark_v1(
        lane_state_root=root,
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        mark_px=3500,
        event_ts_unix=T_BAR1,
        receive_ts_unix=T_BAR1 + 0.125,
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert result[0].advanced
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
        _events_path,
        lane_pending_lane_dir_v1,
    )

    events = [
        json.loads(line)
        for line in _events_path(lane_pending_lane_dir_v1(root)).read_text().splitlines()
    ]
    detail = events[-1]["detail"]
    assert detail["receive_ts_unix"] == T_BAR1 + 0.125
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.resolver_v1 import (
        _replay_producer_from_pending_events_v1,
    )

    producer = _replay_producer_from_pending_events_v1(
        lane_state_root=root,
        pending=result[0].record,
        repository_sha=REPO_SHA,
    )
    assert producer.list_envelopes()[0]["receive_time"] == T_BAR1 + 0.125


@pytest.mark.parametrize("receipt", [None, True, float("nan"), float("inf"), T_BAR1 - 1])
def test_invalid_explicit_receipt_rejects_before_state_access(tmp_path, receipt):
    with pytest.raises((ValueError, TypeError), match="PENDING_MARK_TIMESTAMPS_INVALID"):
        advance_all_open_pending_from_mark_v1(
            lane_state_root=tmp_path / "unused",
            canonical_instrument_id=CANON,
            native_id=NATIVE,
            mark_px=3500,
            event_ts_unix=T_BAR1,
            receive_ts_unix=receipt,
            repository_sha=REPO_SHA,
        )
    assert not (tmp_path / "unused").exists()


def test_wrapper_to_real_pending_store_preserves_mark_and_receipt(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))
    monkeypatch.setattr("time.time", lambda: T_BAR1 + 0.875)
    observation = _observation(_row(ts=str(int(T_BAR1 * 1000) + 250)))
    wrapper = _wrapper(tmp_path, observation)
    wrapper.lane_state_root = root
    assert wrapper.poll() is observation
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
        _events_path,
        lane_pending_lane_dir_v1,
    )

    events = [
        json.loads(line)
        for line in _events_path(lane_pending_lane_dir_v1(root)).read_text().splitlines()
    ]
    assert events[-1]["detail"]["event_ts_unix"] == T_BAR1 + 0.250
    assert events[-1]["detail"]["receive_ts_unix"] == T_BAR1 + 0.875


@pytest.mark.parametrize(
    "payload",
    [
        {"code": "1", "data": [_row()]},
        {"code": "0", "data": [_row(), _row()]},
        {"data": [_row()]},
    ],
)
def test_unsuccessful_or_ambiguous_mark_rows_do_not_advance(tmp_path, monkeypatch, payload):
    monkeypatch.setattr("time.time", lambda: T_BAR1 + 0.375)
    calls = []
    monkeypatch.setattr(
        session, "advance_all_open_pending_from_mark_v1", lambda **kw: calls.append(kw)
    )
    observation = replace(_observation(_row()), mark_price_payload=payload)
    assert _wrapper(tmp_path, observation).poll() is observation
    assert calls == []
