"""Phase 18 existing-fact MARKET_CONTEXT_V1 materialization tests (AUTHORITY=NONE)."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    BOUCHAUD_PROXY_PRODUCER,
    ExistingFactMaterializationError,
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
    MaterializationRejection,
    WP_A_PRODUCER,
    materialize_market_context_v1_from_existing_facts_v1,
    replay_market_context_serialization_v1,
    validate_governed_canonical_fact_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    MARKET_CONTEXT_AUTHORITY,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    N_BARS_BACKBONE_TOKEN,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    exact_known_61_price_fixture_v1,
)

_INSTRUMENT = "inst.SUI-USD_UM_XPERP.test"
_JUNE_BASE = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
_OBSERVED = "2026-09-26T12:00:00Z"


def _quality_finalized() -> dict:
    return {
        "finalized": True,
        "in_progress": False,
        "missing": False,
        "stale": False,
        "corrected": False,
        "duplicate": False,
        "out_of_order": False,
        "gap_detected": False,
    }


def _instrument() -> dict:
    return {
        "canonical_instrument_id": _INSTRUMENT,
        "venue_native_id": "SUI-USDT-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "a" * 64,
    }


def _timestamps(*, effective_at: str) -> dict:
    return {
        "venue_event_time_ms": None,
        "captured_at": effective_at,
        "effective_at": effective_at,
        "source_clock_class": "venue",
    }


def _governed_fact(*, kind: str, payload: dict) -> GovernedCanonicalFactV1:
    body = {**payload, "fact_kind": kind}
    digest = fact_digest(body)
    return GovernedCanonicalFactV1(
        fact_kind=kind,
        fact_digest=digest,
        payload=body,
        producer_owner=WP_A_PRODUCER,
    )


def _dt_parts(base: datetime, offset_minutes: int) -> tuple[int, str]:
    dt = base + timedelta(minutes=offset_minutes)
    ms = int(dt.timestamp() * 1000)
    iso = dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return ms, iso


def _mark_fact(
    *,
    offset_minutes: int,
    mark_px: float,
    base: datetime | None = None,
) -> GovernedCanonicalFactV1:
    ms, pit = _dt_parts(base or _JUNE_BASE, offset_minutes)
    payload = {
        "instrument": _instrument(),
        "mark_px": str(mark_px),
        "interval_start_ms": ms,
        "confirm": "1",
        "source_price_kind": "mark_price_candle",
        "timestamps": _timestamps(effective_at=pit),
        "provenance": {
            "transport": "rest",
            "endpoint_or_channel": "/api/v5/market/mark-price-candles",
            "raw_payload_digest": "b" * 64,
            "session_id": "sess.test",
            "eea_endpoint_family": "public_rest",
        },
        "quality": _quality_finalized(),
    }
    return _governed_fact(kind="FinalizedPt1mMarkFactV1", payload=payload)


def _trade_fact(*, side: str, size: str, price: str, effective_at: str) -> GovernedCanonicalFactV1:
    payload = {
        "instrument": _instrument(),
        "trade_id": f"tr-{effective_at}-{side}",
        "price": price,
        "size": size,
        "side": side,
        "timestamps": _timestamps(effective_at=effective_at),
        "provenance": {
            "transport": "ws",
            "endpoint_or_channel": "trades",
            "raw_payload_digest": "c" * 64,
            "session_id": "sess.test",
            "eea_endpoint_family": "public_ws",
        },
        "quality": _quality_finalized(),
        "immutable_after_ingestion": True,
    }
    return _governed_fact(kind="TradeFactV1", payload=payload)


def _ohlcv_fact(
    *,
    offset_minutes: int,
    close: float,
    volume: float,
    base: datetime | None = None,
) -> GovernedCanonicalFactV1:
    ms, pit = _dt_parts(base or _JUNE_BASE, offset_minutes)
    payload = {
        "instrument": _instrument(),
        "interval_id": "PT1M",
        "open_px": str(close * 0.999),
        "high_px": str(close * 1.001),
        "low_px": str(close * 0.998),
        "close_px": str(close),
        "volume": str(volume),
        "volume_unit_semantics": "base",
        "source_price_kind": "close",
        "interval_start_ms": ms,
        "confirm": "1",
        "timestamps": _timestamps(effective_at=pit),
        "provenance": {
            "transport": "rest",
            "endpoint_or_channel": "/api/v5/market/candles",
            "raw_payload_digest": "d" * 64,
            "session_id": "sess.test",
            "eea_endpoint_family": "public_rest",
        },
        "quality": _quality_finalized(),
    }
    return _governed_fact(kind="OhlcvIntervalFactV1", payload=payload)


def _volatility_marks_from_fixture() -> tuple[GovernedCanonicalFactV1, ...]:
    frame = exact_known_61_price_fixture_v1()
    facts: list[GovernedCanonicalFactV1] = []
    for i, (ts, row) in enumerate(frame.iterrows()):
        effective = ts.isoformat().replace("+00:00", "Z")
        ms = int(ts.timestamp() * 1000)
        payload = {
            "instrument": _instrument(),
            "mark_px": str(row["mark_price"]),
            "interval_start_ms": ms,
            "confirm": "1",
            "source_price_kind": "mark_price_candle",
            "timestamps": _timestamps(effective_at=effective),
            "provenance": {
                "transport": "rest",
                "endpoint_or_channel": "/api/v5/market/mark-price-candles",
                "raw_payload_digest": "e" * 64,
                "session_id": "sess.test",
                "eea_endpoint_family": "public_rest",
            },
            "quality": _quality_finalized(),
        }
        facts.append(_governed_fact(kind="FinalizedPt1mMarkFactV1", payload=payload))
    return tuple(facts)


def test_full_materialization_deterministic_replay() -> None:
    ohlcv = tuple(
        _ohlcv_fact(offset_minutes=m, close=100.0 + m * 0.01, volume=1000 + m) for m in range(25)
    )
    marks = _volatility_marks_from_fixture()
    observed = marks[-1].payload["timestamps"]["effective_at"]
    request = ExistingFactMaterializationRequestV1(
        observed_at=observed,
        instrument_ref=_INSTRUMENT,
        provenance_refs=["prov.canonical.fact.phase18"],
        price_mark_fact=marks[-1],
        trade_facts=(
            _trade_fact(side="buy", size="2", price="100", effective_at="2026-06-01T00:30:00Z"),
            _trade_fact(side="sell", size="1", price="100", effective_at="2026-06-01T00:31:00Z"),
        ),
        ohlcv_facts=ohlcv,
        volatility_mark_facts=marks,
    )
    first = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    second = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    assert first["context_id"] == second["context_id"]
    assert replay_market_context_serialization_v1(first) == replay_market_context_serialization_v1(
        second
    )
    assert first["price_state_ref"]["presence"] == "PRESENT"
    assert first["flow_state_ref"]["presence"] == "PRESENT"
    assert first["liquidity_microstructure_state_ref"]["presence"] == "PRESENT"
    assert first["volatility_state_ref"]["presence"] == "PRESENT"
    assert (
        first["liquidity_microstructure_state_ref"]["microstructure_kind"]
        == MICROSTRUCTURE_KIND_PROXY_OHLCV
    )
    assert first["derivatives_state_ref"]["presence"] == "MISSING"
    assert first["cross_market_state_ref"]["presence"] == "MISSING"
    assert first["market_context_authority"] == MARKET_CONTEXT_AUTHORITY
    assert first["n_bars_backbone_semantics"] == N_BARS_BACKBONE_TOKEN


def test_missing_sources_remain_missing() -> None:
    sept_base = datetime(2026, 9, 26, 0, 0, 0, tzinfo=timezone.utc)
    request = ExistingFactMaterializationRequestV1(
        observed_at=_OBSERVED,
        instrument_ref=_INSTRUMENT,
        provenance_refs=["prov.only"],
        price_mark_fact=_mark_fact(offset_minutes=0, mark_px=100.0, base=sept_base),
    )
    record = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    assert record["flow_state_ref"]["presence"] == "MISSING"
    assert record["liquidity_microstructure_state_ref"]["presence"] == "MISSING"
    assert record["volatility_state_ref"]["presence"] == "MISSING"


def test_future_mark_rejected() -> None:
    sept_base = datetime(2026, 9, 26, 0, 0, 0, tzinfo=timezone.utc)
    fact = _mark_fact(offset_minutes=12 * 60 + 5, mark_px=101.0, base=sept_base)
    with pytest.raises(ExistingFactMaterializationError, match="lookahead"):
        validate_governed_canonical_fact_v1(fact, observed_at=_OBSERVED)


def test_ungoverned_producer_rejected() -> None:
    fact = _mark_fact(offset_minutes=0, mark_px=100.0)
    bad = GovernedCanonicalFactV1(
        fact_kind=fact.fact_kind,
        fact_digest=fact.fact_digest,
        payload=fact.payload,
        producer_owner="unknown.producer",
    )
    with pytest.raises(ExistingFactMaterializationError, match="ungoverned_producer"):
        validate_governed_canonical_fact_v1(bad, observed_at=_OBSERVED)


def test_ambiguous_price_sources_rejected() -> None:
    sept_base = datetime(2026, 9, 26, 0, 0, 0, tzinfo=timezone.utc)
    mark = _mark_fact(offset_minutes=0, mark_px=100.0, base=sept_base)
    bar_payload = {
        "bar": {
            "canonical_instrument_id": _INSTRUMENT,
            "venue_instrument_id": "SUI-USDT-SWAP",
            "venue": "okx_eea",
            "interval": "PT1H",
            "bar_open_time": 1_759_478_400.0,
            "bar_close_time": 1_759_481_999.0,
            "finalization_state": "FINALIZED",
            "quality_state": "OK",
            "last_observation_identity": {},
            "session_id": "s",
            "repository_sha": "sha",
            "config_digest": "cfg",
            "close": 100.0,
            "revision": 1,
        },
        "quality": _quality_finalized(),
    }
    o4 = _governed_fact(kind="FinalizedPt1hO4BarFactV1", payload=bar_payload)
    request = ExistingFactMaterializationRequestV1(
        observed_at=_OBSERVED,
        instrument_ref=_INSTRUMENT,
        provenance_refs=["prov.only"],
        price_mark_fact=mark,
        price_o4_bar_fact=o4,
    )
    with pytest.raises(ExistingFactMaterializationError, match="ambiguous_price"):
        materialize_market_context_v1_from_existing_facts_v1(request)


def test_unknown_trade_side_not_inferred() -> None:
    trade = _trade_fact(side="unknown", size="1", price="1", effective_at="2026-09-26T11:00:00Z")
    request = ExistingFactMaterializationRequestV1(
        observed_at=_OBSERVED,
        instrument_ref=_INSTRUMENT,
        provenance_refs=["prov.only"],
        trade_facts=(trade,),
    )
    with pytest.raises(ExistingFactMaterializationError, match="unknown_trade_side"):
        materialize_market_context_v1_from_existing_facts_v1(request)


def test_microstructure_producer_is_bouchaud_proxy() -> None:
    sept_base = datetime(2026, 9, 26, 0, 0, 0, tzinfo=timezone.utc)
    ohlcv = tuple(
        _ohlcv_fact(
            offset_minutes=m,
            close=100.0 + math.sin(m),
            volume=500 + m,
            base=sept_base,
        )
        for m in range(25)
    )
    request = ExistingFactMaterializationRequestV1(
        observed_at=_OBSERVED,
        instrument_ref=_INSTRUMENT,
        provenance_refs=["prov.only"],
        ohlcv_facts=ohlcv,
    )
    record = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    slot = record["liquidity_microstructure_state_ref"]
    assert slot["presence"] == "PRESENT"
    assert slot["producer_owner"] == BOUCHAUD_PROXY_PRODUCER
    assert slot["microstructure_kind"] == MICROSTRUCTURE_KIND_PROXY_OHLCV


def test_no_authority_side_effects_constants() -> None:
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        LEARNING_TRADING_AUTHORITY,
        MARKET_INTELLIGENCE_TRADING_AUTHORITY,
    )

    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert LEARNING_TRADING_AUTHORITY == "NONE"
    assert MARKET_INTELLIGENCE_TRADING_AUTHORITY == "NONE"
