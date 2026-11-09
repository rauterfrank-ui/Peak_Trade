"""Actual public WS → original normalizer/store; explicit offline source fixtures."""

from copy import deepcopy
import json

import pytest

from src.ops.peak_trade_public_market_data_runtime_v1 import (
    event_sequence_persistence_v1 as sequence,
    runtime_orchestrator_v1 as runtime,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
    process_public_events_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_channel_normalizers_v1 import (
    PublicWsNormalizeError,
    normalize_ws_payload_to_canonical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1
from tests.ops.test_peak_trade_public_market_data_runtime_v1 import _FakeConnector

NATIVE = "ETH-USDT-SWAP"
CAPTURE = "2026-11-09T12:00:00Z"
EVENT = 1794225599900
INSTRUMENT = dict(
    canonical_instrument_id="inst-eth",
    venue_native_id=NATIVE,
    venue="okx_eea",
    instrument_type="SWAP",
    settlement_asset="USDT",
    mapping_provenance_digest="fixture-only",
)


def push(*, channel="mark-price", native=NATIVE, timestamp=EVENT, **values):
    return dict(
        arg=dict(channel=channel, instId=native),
        data=[dict(instId=native, ts=str(timestamp), **values)],
    )


def normalize(message):
    return normalize_ws_payload_to_canonical_facts_v1(
        message,
        instrument_ref=INSTRUMENT,
        captured_at=CAPTURE,
        session_id="offline-fixture",
    )


def make_runtime(tmp_path, messages):
    transport = PublicWsTransportV1.from_ratified_binding(
        connector=_FakeConnector(),
        message_source=lambda: iter(messages),
        venue_native_id=NATIVE,
    )
    transport.connect_and_subscribe()
    return runtime.PublicMarketDataRuntimeV1(
        store_root=tmp_path,
        venue_native_id=NATIVE,
        canonical_instrument_id="inst-eth",
        ws_transport=transport,
    )


def test_genuine_nested_mark_reaches_original_store_and_cold_read(tmp_path):
    message = push(markPx="100.125", last="99999")
    producer = make_runtime(tmp_path, [message])
    assert producer.ws_transport.binding.subscribe_args_for_instrument(NATIVE)[0] == dict(
        channel="mark-price",
        instId=NATIVE,
    )
    producer.run_observation_cycle(captured_at=CAPTURE)
    (fact,) = load_all_facts_v1(default_store_paths_v1(tmp_path))
    assert fact["fact_kind"] == "MarkPriceFactV1"
    assert fact["mark_px"] == "100.125"
    assert fact["timestamps"]["venue_event_time_ms"] == EVENT
    assert fact["timestamps"]["captured_at"] == CAPTURE
    assert fact["provenance"]["endpoint_or_channel"] == "mark-price"
    assert fact["instrument"]["venue_native_id"] == NATIVE
    restarted = make_runtime(tmp_path, [message])
    restarted.load_durable_event_state()
    restarted.run_observation_cycle(captured_at=CAPTURE)
    facts = load_all_facts_v1(default_store_paths_v1(tmp_path))
    assert len(facts) == 2 and facts[-1]["quality"]["duplicate"] is True
    assert (
        restarted.event_state.last_event_ts_ms_by_stream
        == producer.event_state.last_event_ts_ms_by_stream
    )


def test_last_trade_price_never_becomes_a_canonical_mark():
    assert normalize(push(channel="tickers", last="200")) == []
    with pytest.raises(PublicWsNormalizeError, match="MARK_PX_MISSING_OR_INVALID"):
        normalize(push(last="200"))


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "0", "-1", "", True])
def test_nonfinite_or_nonpositive_mark_rejected(value):
    with pytest.raises(PublicWsNormalizeError):
        normalize(push(markPx=value))


@pytest.mark.parametrize("timestamp", [None, True, "NaN", "0", "-1", "1.2"])
def test_missing_or_invalid_event_clock_rejected(timestamp):
    message = push(markPx="100")
    message["data"][0]["ts"] = timestamp
    with pytest.raises(PublicWsNormalizeError, match="MARK_EVENT_TIME"):
        normalize(message)


def test_wrong_instrument_not_relabelled_to_bound_scope():
    with pytest.raises(PublicWsNormalizeError, match="WS_INSTRUMENT_MISMATCH"):
        normalize(push(native="SOL-USDT-SWAP", markPx="100"))
    message = push(markPx="100")
    message["data"][0]["instId"] = "SOL-USDT-SWAP"
    with pytest.raises(PublicWsNormalizeError, match="MARK_INSTRUMENT_MISMATCH"):
        normalize(message)


def test_separate_stream_clocks_do_not_reject_a_valid_mark(tmp_path):
    events = [
        push(channel="trades", timestamp=EVENT + 200, tradeId="t1", px="100", sz="1", side="buy"),
        push(timestamp=EVENT, markPx="100"),
        push(native="SOL-USDT-SWAP", timestamp=EVENT - 100, markPx="20"),
        push(timestamp=EVENT - 1, markPx="99"),
    ]
    envelopes, state, gaps = process_public_events_v1(events=events, state=EventSequenceStateV1())
    assert [item.out_of_order for item in envelopes] == [False, False, False, True]
    assert not gaps  # Live ticks are not a finalized PT1M candle sequence.
    sequence.persist_event_sequence_state_v1(tmp_path, state)
    restored = sequence.load_event_sequence_state_v1(tmp_path)
    assert restored == state
    repeated, _, _ = process_public_events_v1(events=events[:1], state=restored)
    assert repeated[0].duplicate


def test_same_timestamp_changed_mark_is_retained_but_identical_replay_is_duplicate():
    first, correction = push(markPx="100"), push(markPx="100.01")
    rows, _, _ = process_public_events_v1(
        events=[first, correction, deepcopy(correction), {**first, "_duplicate": True}],
        state=EventSequenceStateV1(),
    )
    assert [row.duplicate for row in rows] == [False, False, True, False]
    assert [row.corrected for row in rows] == [False, True, False, True]
    assert not any(row.out_of_order for row in rows)
    assert rows[0].event_ts_ms == rows[1].event_ts_ms


def test_continuous_mark_snapshots_keep_bounded_dedup_state_and_resume_corrections(tmp_path):
    messages = [push(timestamp=EVENT + i, markPx=str(100 + i)) for i in range(2000)]
    producer = make_runtime(tmp_path, messages)
    producer.run_observation_cycle(captured_at=CAPTURE)
    assert producer.event_state.seen_ids == set()
    assert producer.ws_transport.state.seen_message_ids == set()
    assert len(producer.event_state.last_event_id_by_stream) == 1
    cold = sequence.load_event_sequence_state_v1(tmp_path)
    assert cold == producer.event_state
    rows, _, _ = process_public_events_v1(
        events=[messages[-1], push(timestamp=EVENT + 1999, markPx="100"), messages[-1]],
        state=cold,
    )
    assert [r.duplicate for r in rows] == [True, False, False]
    assert [r.corrected for r in rows] == [False, True, True]


def test_invalid_mark_does_not_advance_original_runtime_cursor_or_write_partial_batch(tmp_path):
    producer = make_runtime(tmp_path, [push(markPx="100"), push(timestamp=EVENT + 1, last="101")])
    with pytest.raises(PublicWsNormalizeError):
        producer.run_observation_cycle(captured_at=CAPTURE)
    assert producer.event_state == EventSequenceStateV1()
    assert not (tmp_path / sequence.SEQUENCE_STATE_FILENAME).exists()
    assert load_all_facts_v1(default_store_paths_v1(tmp_path)) == []


def test_interrupted_sequence_replace_preserves_previous_durable_clock(tmp_path, monkeypatch):
    state = EventSequenceStateV1(last_event_ts_ms=1000, seen_ids={"before"})
    target = sequence.persist_event_sequence_state_v1(tmp_path, state)
    before = target.read_bytes()

    def fail(*_args):
        raise OSError("injected sequence replace failure")

    monkeypatch.setattr(sequence.os, "replace", fail)
    with pytest.raises(OSError, match="injected"):
        sequence.persist_event_sequence_state_v1(tmp_path, EventSequenceStateV1(seen_ids={"after"}))
    assert target.read_bytes() == before
    assert sequence.load_event_sequence_state_v1(tmp_path) == state


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"schema_version": "foreign"},
        {"schema_version": sequence.SCHEMA_VERSION, "seen_ids": True},
    ],
)
def test_broken_sequence_is_not_an_empty_bootstrap(tmp_path, payload):
    (tmp_path / sequence.SEQUENCE_STATE_FILENAME).write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sequence.load_event_sequence_state_v1(tmp_path)


@pytest.mark.parametrize(
    "classify", [classify_live_mark_price_freshness_v1, classify_live_best_bid_ask_freshness_v1]
)
@pytest.mark.parametrize("age", [float("nan"), float("inf"), float("-inf"), True, "0", None])
def test_invalid_age_cannot_be_positive_freshness(classify, age):
    verdict = classify(age_seconds=age)
    assert not verdict.publishable and verdict.stale and verdict.reason == "AGE_INVALID"


@pytest.mark.parametrize(
    "classify", [classify_live_mark_price_freshness_v1, classify_live_best_bid_ask_freshness_v1]
)
def test_original_five_second_freshness_boundary_is_unchanged(classify):
    assert classify(age_seconds=0).publishable
    assert classify(age_seconds=5).publishable
    assert not classify(age_seconds=5.000001).publishable
    assert not classify(age_seconds=-0.000001).publishable
