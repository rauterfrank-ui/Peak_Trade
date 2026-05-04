# tests/trading/master_v2/test_double_play_futures_input_producer.py
from __future__ import annotations

import ast
import json
from dataclasses import fields
from pathlib import Path

import pytest

from src.ops.common.serialize_v1 import to_jsonable_v1

from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesInputBlockReason,
    FuturesInputReadinessDecision,
    FuturesInputSnapshot,
    FuturesMarketType,
    FuturesReadinessStatus,
)
from trading.master_v2.double_play_futures_input_producer import (
    DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_LAYER_VERSION,
    FuturesProducerAdapterBlockReason,
    FuturesProducerAdapterStatus,
    FuturesProducerCandidate,
    FuturesProducerDerivatives,
    FuturesProducerLiquidity,
    FuturesProducerMarketDataProvenance,
    FuturesProducerOpportunity,
    FuturesProducerPacket,
    FuturesProducerRanking,
    FuturesProducerInstrumentMetadata,
    FuturesProducerVolatility,
    adapt_producer_packet_to_futures_input_snapshot,
    producer_packet_has_runtime_handles,
    producer_packet_to_snapshot,
    producer_packet_complete_enough_for_snapshot,
)
from trading.master_v2 import double_play_futures_input as _fi
from trading.master_v2 import double_play_futures_input_producer as _producer


def _pcand(**overrides: object) -> FuturesProducerCandidate:
    d: dict = {
        "candidate_id": "producer-packet-c1",
        "instrument_id": "inst-btc-perp",
        "symbol": "BTC-USDT-PERP",
        "market_type": FuturesMarketType.PERPETUAL,
        "exchange": "example",
        "base_currency": "BTC",
        "quote_currency": "USDT",
        "live_authorization": False,
    }
    d.update(overrides)
    return FuturesProducerCandidate(**d)


def _prank(**overrides: object) -> FuturesProducerRanking:
    d: dict = {
        "source_universe_size": 200,
        "selected_top_n": 20,
        "rank": 3,
        "score": 0.91,
        "score_components_complete": True,
        "is_top_n_member": True,
    }
    d.update(overrides)
    return FuturesProducerRanking(**d)


def _pinst(**overrides: object) -> FuturesProducerInstrumentMetadata:
    d: dict = {
        "complete": True,
        "contract_size_known": True,
        "tick_size_known": True,
        "step_size_known": True,
        "min_qty_known": True,
        "min_notional_known": True,
        "margin_asset_known": True,
        "settlement_asset_known": True,
        "leverage_bounds_known": True,
        "missing_fields": (),
    }
    d.update(overrides)
    return FuturesProducerInstrumentMetadata(**d)


def _pprov(**overrides: object) -> FuturesProducerMarketDataProvenance:
    d: dict = {
        "complete": True,
        "freshness_state": FuturesFreshnessState.FRESH,
        "dataset_id": "ds-producer-packet-1",
        "source": "fixture",
        "mark_available": True,
        "index_available": True,
        "last_available": True,
        "ohlcv_available": True,
        "funding_available": True,
        "open_interest_available": True,
        "missing_fields": (),
    }
    d.update(overrides)
    return FuturesProducerMarketDataProvenance(**d)


def _pvol(**overrides: object) -> FuturesProducerVolatility:
    d: dict = {
        "realized_volatility": 0.42,
        "atr_or_rolling_range": 120.0,
        "volatility_regime": "medium",
        "dynamic_scope_usable": True,
    }
    d.update(overrides)
    return FuturesProducerVolatility(**d)


def _pliq(**overrides: object) -> FuturesProducerLiquidity:
    d: dict = {
        "spread_bps": 1.5,
        "average_spread_bps": 1.8,
        "volume": 1_000_000.0,
        "quote_volume": 50_000_000.0,
        "liquidity_regime": "deep",
        "spread_quality": "tight",
    }
    d.update(overrides)
    return FuturesProducerLiquidity(**d)


def _pder(**overrides: object) -> FuturesProducerDerivatives:
    d: dict = {
        "funding_available": True,
        "funding_rate": 0.0001,
        "funding_regime": "neutral",
        "open_interest_available": True,
        "open_interest": 1e9,
        "open_interest_regime": "high",
    }
    d.update(overrides)
    return FuturesProducerDerivatives(**d)


def _popp(**overrides: object) -> FuturesProducerOpportunity:
    d: dict = {
        "opportunity_score": 0.75,
        "inactivity_score": 0.1,
        "movement_above_fee_slippage_breakeven": True,
        "chop_risk": "low",
        "candidate_is_inactive": False,
    }
    d.update(overrides)
    return FuturesProducerOpportunity(**d)


def _ppacket(**overrides: object) -> FuturesProducerPacket:
    parts: dict = {
        "candidate": _pcand(),
        "ranking": _prank(),
        "instrument": _pinst(),
        "provenance": _pprov(),
        "volatility": _pvol(),
        "liquidity": _pliq(),
        "derivatives": _pder(),
        "opportunity": _popp(),
        "dashboard_label": "producer_adapter_fixture",
        "ai_summary": None,
    }
    parts.update(overrides)
    return FuturesProducerPacket(**parts)


def _assert_adapter_output_data_only(
    snap: FuturesInputSnapshot,
    readiness: FuturesInputReadinessDecision,
    *,
    _seen: set[int] | None = None,
) -> None:
    if _seen is None:
        _seen = set()
    for obj in (snap, readiness):
        _walk_data_only(obj, _seen=_seen)


def _walk_data_only(obj: object, *, _seen: set[int]) -> None:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, (FuturesMarketType, FuturesFreshnessState, FuturesReadinessStatus)):
        return
    if isinstance(obj, (FuturesInputBlockReason, FuturesProducerAdapterBlockReason)):
        return
    oid = id(obj)
    if oid in _seen:
        return
    if isinstance(obj, tuple):
        _seen.add(oid)
        for item in obj:
            _walk_data_only(item, _seen=_seen)
        return
    fields = getattr(obj, "__dataclass_fields__", None)
    if fields is not None:
        _seen.add(oid)
        for f in fields.values():
            _walk_data_only(getattr(obj, f.name), _seen=_seen)
        return
    raise AssertionError(f"disallowed value in adapter output: {type(obj)!r}")


def _assert_json_native(obj: object, *, depth: int = 0) -> None:
    if depth > 24:
        raise AssertionError("json structure too deep for contract bound")
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str), (type(k), obj)
            _assert_json_native(v, depth=depth + 1)
        return
    if isinstance(obj, list):
        for item in obj:
            _assert_json_native(item, depth=depth + 1)
        return
    raise AssertionError(f"non-json-native type after serialization: {type(obj)!r}")


def test_futures_producer_packet_jsonable_stdlib_roundtrip_v0() -> None:
    """Frozen producer packet survives ops ``to_jsonable_v1`` and stdlib ``json`` roundtrip.

    Non-authorizing wire reproducibility fixture: ``live_authorization`` is False on the packet.
    """
    packet = _ppacket()
    assert packet.candidate.live_authorization is False
    assert not producer_packet_has_runtime_handles(packet)

    jsonable = to_jsonable_v1(packet)
    assert frozenset(jsonable.keys()) == {f.name for f in fields(FuturesProducerPacket)}
    _assert_json_native(jsonable)

    wire = json.dumps(jsonable, sort_keys=True)
    decoded = json.loads(wire)
    assert decoded == jsonable

    cand = jsonable["candidate"]
    assert isinstance(cand, dict)
    assert cand["live_authorization"] is False


def test_producer_layer_version_v0() -> None:
    assert DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_LAYER_VERSION == "v0"


def test_complete_packet_maps_and_is_data_ready() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(_ppacket())
    assert dec.adapter_status is FuturesProducerAdapterStatus.OK
    assert dec.snapshot is not None
    assert dec.readiness is not None
    assert dec.readiness.status is FuturesReadinessStatus.DATA_READY
    assert dec.readiness.ready_for_downstream_model_use
    assert dec.readiness.ready_for_dynamic_scope
    assert dec.readiness.ready_for_capital_slot
    assert not dec.readiness.live_authorization


def test_missing_instrument_metadata_fails_closed() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(instrument=_pinst(complete=False, missing_fields=("tick_size",)))
    )
    assert dec.readiness is not None
    assert dec.readiness.status is FuturesReadinessStatus.BLOCKED
    assert not dec.readiness.ready_for_downstream_model_use
    assert FuturesInputBlockReason.INSTRUMENT_METADATA_INCOMPLETE in dec.readiness.block_reasons


def test_missing_provenance_fails_closed() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(provenance=_pprov(complete=False, missing_fields=("dataset_id",)))
    )
    assert dec.readiness is not None
    assert dec.readiness.status is FuturesReadinessStatus.BLOCKED
    assert FuturesInputBlockReason.MARKET_DATA_PROVENANCE_INCOMPLETE in dec.readiness.block_reasons


def test_rank_only_packet_fails_closed() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(
            ranking=_prank(
                rank=2, score=0.95, is_top_n_member=True, score_components_complete=False
            ),
            instrument=_pinst(complete=False, missing_fields=("tick_size", "contract_size")),
            provenance=_pprov(complete=False, missing_fields=("dataset_id", "source")),
            volatility=_pvol(
                realized_volatility=None, atr_or_rolling_range=None, dynamic_scope_usable=False
            ),
            liquidity=_pliq(spread_bps=None, volume=None, quote_volume=None),
            derivatives=_pder(funding_available=False, funding_rate=None),
        )
    )
    assert dec.readiness is not None
    assert dec.readiness.status is FuturesReadinessStatus.BLOCKED
    assert not dec.readiness.ready_for_downstream_model_use


def test_generic_market_scan_like_packet_fails_closed() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(
            candidate=_pcand(
                candidate_id="market-scan-run-opaque-id",
                instrument_id="",
                symbol="BTC/EUR",
                market_type=FuturesMarketType.UNKNOWN,
                exchange="kraken",
            ),
            ranking=_prank(
                source_universe_size=50,
                selected_top_n=20,
                rank=7,
                score=1.15,
                score_components_complete=False,
                is_top_n_member=True,
            ),
            instrument=_pinst(
                complete=False,
                contract_size_known=False,
                tick_size_known=False,
                step_size_known=False,
                min_qty_known=False,
                min_notional_known=False,
                margin_asset_known=False,
                settlement_asset_known=False,
                leverage_bounds_known=False,
                missing_fields=("instrument_metadata",),
            ),
            provenance=_pprov(
                complete=False,
                freshness_state=FuturesFreshnessState.UNKNOWN,
                dataset_id=None,
                source=None,
                mark_available=False,
                index_available=False,
                last_available=False,
                ohlcv_available=False,
                funding_available=False,
                open_interest_available=False,
                missing_fields=("provenance",),
            ),
            volatility=_pvol(
                realized_volatility=None,
                atr_or_rolling_range=None,
                dynamic_scope_usable=False,
            ),
            liquidity=_pliq(spread_bps=None, volume=None, quote_volume=None),
            derivatives=_pder(
                funding_available=False,
                funding_rate=None,
                open_interest_available=False,
                open_interest=None,
            ),
            opportunity=_popp(opportunity_score=1.15, inactivity_score=None),
        )
    )
    assert dec.readiness is not None
    assert dec.readiness.status is FuturesReadinessStatus.BLOCKED
    assert not dec.readiness.ready_for_capital_slot
    assert FuturesInputBlockReason.MARKET_TYPE_UNKNOWN in dec.readiness.block_reasons


@pytest.mark.parametrize("market_type", [FuturesMarketType.PERPETUAL, FuturesMarketType.SWAP])
def test_perpetual_like_missing_funding_fails_closed(market_type: FuturesMarketType) -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(
            candidate=_pcand(market_type=market_type),
            derivatives=_pder(funding_available=False, funding_rate=None),
        )
    )
    assert dec.readiness is not None
    assert FuturesInputBlockReason.PERPETUAL_FUNDING_INCOMPLETE in dec.readiness.block_reasons
    assert not dec.readiness.ready_for_capital_slot


def test_missing_liquidity_spread_blocks_capital_slot() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(liquidity=_pliq(spread_bps=None, volume=100.0, quote_volume=None))
    )
    assert dec.readiness is not None
    assert not dec.readiness.ready_for_capital_slot
    assert FuturesInputBlockReason.LIQUIDITY_INCOMPLETE in dec.readiness.block_reasons


def test_missing_volatility_blocks_dynamic_scope() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(
            volatility=_pvol(
                realized_volatility=None,
                atr_or_rolling_range=10.0,
                dynamic_scope_usable=False,
            )
        )
    )
    assert dec.readiness is not None
    assert not dec.readiness.ready_for_dynamic_scope
    assert FuturesInputBlockReason.VOLATILITY_INCOMPLETE in dec.readiness.block_reasons


def test_adapter_output_has_no_runtime_handles() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(_ppacket())
    assert dec.snapshot is not None
    assert dec.readiness is not None
    _assert_adapter_output_data_only(dec.snapshot, dec.readiness)


def test_live_authorization_on_packet_is_stripped() -> None:
    dec = adapt_producer_packet_to_futures_input_snapshot(
        _ppacket(candidate=_pcand(live_authorization=True))
    )
    assert dec.snapshot is not None
    assert dec.snapshot.candidate.live_authorization is False
    assert dec.readiness is not None
    assert not dec.readiness.live_authorization


def test_runtime_handle_in_packet_blocks_adapter() -> None:
    bad = _ppacket(dashboard_label=object())  # type: ignore[arg-type]
    assert producer_packet_has_runtime_handles(bad)
    dec = adapt_producer_packet_to_futures_input_snapshot(bad)
    assert dec.adapter_status is FuturesProducerAdapterStatus.BLOCKED
    assert FuturesProducerAdapterBlockReason.RUNTIME_HANDLE_DETECTED in dec.adapter_block_reasons
    assert dec.snapshot is None
    assert dec.readiness is None


def test_producer_packet_to_snapshot_rejects_handles() -> None:
    bad = _ppacket(dashboard_label=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="runtime handles"):
        producer_packet_to_snapshot(bad)


def test_producer_packet_complete_enough_for_snapshot() -> None:
    p = _ppacket()
    assert producer_packet_complete_enough_for_snapshot(p)
    assert not producer_packet_has_runtime_handles(p)


def test_producer_module_imports_exclude_operational_surfaces() -> None:
    path = Path(_producer.__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned_roots = frozenset(
        {
            "ccxt",
            "requests",
            "urllib",
            "http",
            "socket",
            "subprocess",
            "scripts",
            "src",
        }
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root not in banned_roots, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            assert root not in banned_roots, node.module
            assert not node.module.startswith("scripts."), node.module
            assert not node.module.startswith("src.exchange"), node.module


def test_producer_reuses_canonical_futures_input_types() -> None:
    assert FuturesMarketType is _fi.FuturesMarketType
    assert FuturesFreshnessState is _fi.FuturesFreshnessState
