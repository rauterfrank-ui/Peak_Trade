# tests/trading/master_v2/test_double_play_futures_producer_packet_contract.py
"""
Test-only contract: producer-packet expectations mapped onto FuturesInputSnapshot.

No producer adapter, no I/O, no operational imports — see MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from trading.master_v2 import double_play_futures_input as _futures_input_module
from trading.master_v2.double_play_futures_input import (
    FuturesCandidateSnapshot,
    FuturesDerivativesProfile,
    FuturesFreshnessState,
    FuturesInputBlockReason,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesLiquidityProfile,
    FuturesMarketDataProvenanceStatus,
    FuturesMarketType,
    FuturesOpportunityProfile,
    FuturesRankingSnapshot,
    FuturesReadinessStatus,
    FuturesVolatilityProfile,
    evaluate_futures_input_snapshot,
)


def _candidate(**overrides: object) -> FuturesCandidateSnapshot:
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
    return FuturesCandidateSnapshot(**d)


def _ranking(**overrides: object) -> FuturesRankingSnapshot:
    d: dict = {
        "source_universe_size": 200,
        "selected_top_n": 20,
        "rank": 3,
        "score": 0.91,
        "score_components_complete": True,
        "is_top_n_member": True,
    }
    d.update(overrides)
    return FuturesRankingSnapshot(**d)


def _instrument(**overrides: object) -> FuturesInstrumentMetadataStatus:
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
    return FuturesInstrumentMetadataStatus(**d)


def _provenance(**overrides: object) -> FuturesMarketDataProvenanceStatus:
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
    return FuturesMarketDataProvenanceStatus(**d)


def _volatility(**overrides: object) -> FuturesVolatilityProfile:
    d: dict = {
        "realized_volatility": 0.42,
        "atr_or_rolling_range": 120.0,
        "volatility_regime": "medium",
        "dynamic_scope_usable": True,
    }
    d.update(overrides)
    return FuturesVolatilityProfile(**d)


def _liquidity(**overrides: object) -> FuturesLiquidityProfile:
    d: dict = {
        "spread_bps": 1.5,
        "average_spread_bps": 1.8,
        "volume": 1_000_000.0,
        "quote_volume": 50_000_000.0,
        "liquidity_regime": "deep",
        "spread_quality": "tight",
    }
    d.update(overrides)
    return FuturesLiquidityProfile(**d)


def _derivatives(**overrides: object) -> FuturesDerivativesProfile:
    d: dict = {
        "funding_available": True,
        "funding_rate": 0.0001,
        "funding_regime": "neutral",
        "open_interest_available": True,
        "open_interest": 1e9,
        "open_interest_regime": "high",
    }
    d.update(overrides)
    return FuturesDerivativesProfile(**d)


def _opportunity(**overrides: object) -> FuturesOpportunityProfile:
    d: dict = {
        "opportunity_score": 0.75,
        "inactivity_score": 0.1,
        "movement_above_fee_slippage_breakeven": True,
        "chop_risk": "low",
        "candidate_is_inactive": False,
    }
    d.update(overrides)
    return FuturesOpportunityProfile(**d)


def _snapshot(**overrides: object) -> FuturesInputSnapshot:
    parts: dict = {
        "candidate": _candidate(),
        "ranking": _ranking(),
        "instrument": _instrument(),
        "provenance": _provenance(),
        "volatility": _volatility(),
        "liquidity": _liquidity(),
        "derivatives": _derivatives(),
        "opportunity": _opportunity(),
        "dashboard_label": "producer_like_fixture",
        "ai_summary": None,
    }
    parts.update(overrides)
    return FuturesInputSnapshot(**parts)


def _complete_producer_like_snapshot() -> FuturesInputSnapshot:
    """Fully populated snapshot standing in for a conforming static producer packet."""
    snap = _snapshot()
    _assert_fixture_values_are_data_only(snap)
    return snap


def _rank_only_snapshot() -> FuturesInputSnapshot:
    """Top-N rank/score present; instrument and provenance incomplete (rank-only trap)."""
    return _snapshot(
        ranking=_ranking(rank=2, score=0.95, is_top_n_member=True, score_components_complete=False),
        instrument=_instrument(complete=False, missing_fields=("tick_size", "contract_size")),
        provenance=_provenance(complete=False, missing_fields=("dataset_id", "source")),
        volatility=_volatility(
            realized_volatility=None, atr_or_rolling_range=None, dynamic_scope_usable=False
        ),
        liquidity=_liquidity(spread_bps=None, volume=None, quote_volume=None),
        derivatives=_derivatives(funding_available=False, funding_rate=None),
    )


def _generic_market_scan_like_snapshot() -> FuturesInputSnapshot:
    """
    Symbol + scan-style ranking only; futures metadata/provenance/microstructure missing.

    Mirrors insufficient `market_scan` row shape for a full FuturesInputSnapshot per producer contract.
    """
    return _snapshot(
        candidate=_candidate(
            candidate_id="market-scan-run-opaque-id",
            instrument_id="",
            symbol="BTC/EUR",
            market_type=FuturesMarketType.UNKNOWN,
            exchange="kraken",
        ),
        ranking=_ranking(
            source_universe_size=50,
            selected_top_n=20,
            rank=7,
            score=1.15,
            score_components_complete=False,
            is_top_n_member=True,
        ),
        instrument=_instrument(
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
        provenance=_provenance(
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
        volatility=_volatility(
            realized_volatility=None,
            atr_or_rolling_range=None,
            dynamic_scope_usable=False,
        ),
        liquidity=_liquidity(spread_bps=None, volume=None, quote_volume=None),
        derivatives=_derivatives(
            funding_available=False,
            funding_rate=None,
            open_interest_available=False,
            open_interest=None,
        ),
        opportunity=_opportunity(opportunity_score=1.15, inactivity_score=None),
    )


def _assert_fixture_values_are_data_only(obj: object, *, _seen: set[int] | None = None) -> None:
    """Fixtures must not embed clients, threads, or other runtime handles — only data."""
    if _seen is None:
        _seen = set()
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, (FuturesMarketType, FuturesFreshnessState)):
        return
    oid = id(obj)
    if oid in _seen:
        return
    if isinstance(obj, tuple):
        _seen.add(oid)
        for item in obj:
            _assert_fixture_values_are_data_only(item, _seen=_seen)
        return
    fields = getattr(obj, "__dataclass_fields__", None)
    if fields is not None:
        _seen.add(oid)
        for f in fields.values():
            _assert_fixture_values_are_data_only(getattr(obj, f.name), _seen=_seen)
        return
    raise AssertionError(f"disallowed fixture value type: {type(obj)!r}")


def test_complete_producer_like_snapshot_is_data_ready() -> None:
    d = evaluate_futures_input_snapshot(_complete_producer_like_snapshot())
    assert d.status is FuturesReadinessStatus.DATA_READY
    assert d.ready_for_downstream_model_use
    assert d.ready_for_dynamic_scope
    assert d.ready_for_capital_slot
    assert d.ready_for_suitability
    assert not d.live_authorization


def test_missing_instrument_metadata_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(instrument=_instrument(complete=False, missing_fields=("tick_size",)))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert FuturesInputBlockReason.INSTRUMENT_METADATA_INCOMPLETE in d.block_reasons


def test_missing_market_data_provenance_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(provenance=_provenance(complete=False, missing_fields=("dataset_id",)))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert FuturesInputBlockReason.MARKET_DATA_PROVENANCE_INCOMPLETE in d.block_reasons


def test_top20_rank_only_context_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(_rank_only_snapshot())
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert FuturesInputBlockReason.INSTRUMENT_METADATA_INCOMPLETE in d.block_reasons


def test_generic_market_scan_like_row_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(_generic_market_scan_like_snapshot())
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert not d.ready_for_capital_slot
    assert FuturesInputBlockReason.MARKET_TYPE_UNKNOWN in d.block_reasons


@pytest.mark.parametrize("market_type", [FuturesMarketType.PERPETUAL, FuturesMarketType.SWAP])
def test_perpetual_like_missing_funding_fails_closed(market_type: FuturesMarketType) -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            candidate=_candidate(market_type=market_type),
            derivatives=_derivatives(funding_available=False, funding_rate=None),
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert FuturesInputBlockReason.PERPETUAL_FUNDING_INCOMPLETE in d.block_reasons
    assert not d.ready_for_capital_slot


def test_missing_liquidity_spread_blocks_capital_slot_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(liquidity=_liquidity(spread_bps=None, volume=100.0, quote_volume=None))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_capital_slot
    assert not d.ready_for_suitability
    assert FuturesInputBlockReason.LIQUIDITY_INCOMPLETE in d.block_reasons


def test_missing_volatility_blocks_dynamic_scope_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            volatility=_volatility(
                realized_volatility=None,
                atr_or_rolling_range=10.0,
                dynamic_scope_usable=False,
            )
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_dynamic_scope
    assert FuturesInputBlockReason.VOLATILITY_INCOMPLETE in d.block_reasons


def test_producer_like_packet_cannot_imply_live_authorization() -> None:
    snap = _snapshot(candidate=_candidate(live_authorization=True))
    assert snap.candidate.live_authorization is True
    d = evaluate_futures_input_snapshot(snap)
    assert not d.live_authorization
    assert not d.is_authority
    assert d.status is FuturesReadinessStatus.DATA_READY


def test_producer_like_fixtures_contain_no_runtime_handles() -> None:
    _assert_fixture_values_are_data_only(_complete_producer_like_snapshot())
    _assert_fixture_values_are_data_only(_rank_only_snapshot())
    _assert_fixture_values_are_data_only(_generic_market_scan_like_snapshot())


def test_module_imports_exclude_operational_surfaces() -> None:
    src = Path(__file__).resolve().read_text(encoding="utf-8")
    tree = ast.parse(src)
    banned_roots = frozenset(
        {
            "ccxt",
            "requests",
            "urllib",
            "http",
            "socket",
            "subprocess",
            "src",
            "scripts",
        }
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root == "pytest":
                    continue
                assert root not in banned_roots, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root == "pytest":
                continue
            assert root not in banned_roots, node.module
    # Explicit allow-list: only `trading` from first-party packages
    found_from_trading = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("trading."):
            found_from_trading = True
            assert node.module.startswith("trading.master_v2"), node.module
    assert found_from_trading


def test_evaluate_futures_input_snapshot_is_canonical_authority() -> None:
    assert evaluate_futures_input_snapshot is _futures_input_module.evaluate_futures_input_snapshot
