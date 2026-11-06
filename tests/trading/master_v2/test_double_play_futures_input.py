# tests/trading/master_v2/test_double_play_futures_input.py
from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_futures_input import (
    DOUBLE_PLAY_FUTURES_INPUT_LAYER_VERSION,
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
        "candidate_id": "c1",
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
        "dataset_id": "ds-1",
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
        "dashboard_label": None,
        "ai_summary": None,
    }
    parts.update(overrides)
    return FuturesInputSnapshot(**parts)


def test_layer_version_is_v0() -> None:
    assert DOUBLE_PLAY_FUTURES_INPUT_LAYER_VERSION == "v0"


def test_complete_snapshot_returns_data_only_ready_status() -> None:
    d = evaluate_futures_input_snapshot(_snapshot())
    assert d.status is FuturesReadinessStatus.DATA_READY
    assert d.ready_for_downstream_model_use
    assert d.ready_for_dynamic_scope
    assert d.ready_for_capital_slot
    assert d.ready_for_suitability
    assert d.ready_for_survival_envelope
    assert not d.block_reasons
    assert not d.is_authority
    assert not d.is_signal
    assert not d.live_authorization


def test_missing_instrument_metadata_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(instrument=_instrument(complete=False, missing_fields=("tick_size",)))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert FuturesInputBlockReason.INSTRUMENT_METADATA_INCOMPLETE in d.block_reasons
    assert "tick_size" in d.missing_inputs


def test_missing_market_data_provenance_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(provenance=_provenance(complete=False, missing_fields=("dataset_id",)))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use
    assert FuturesInputBlockReason.MARKET_DATA_PROVENANCE_INCOMPLETE in d.block_reasons


def test_stale_freshness_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(provenance=_provenance(freshness_state=FuturesFreshnessState.STALE))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert FuturesInputBlockReason.FRESHNESS_STALE in d.block_reasons
    assert not d.ready_for_downstream_model_use


def test_unknown_freshness_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(provenance=_provenance(freshness_state=FuturesFreshnessState.UNKNOWN))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert FuturesInputBlockReason.FRESHNESS_UNKNOWN in d.block_reasons


def test_unknown_market_type_fails_closed() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(candidate=_candidate(market_type=FuturesMarketType.UNKNOWN))
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert FuturesInputBlockReason.MARKET_TYPE_UNKNOWN in d.block_reasons
    assert not d.ready_for_downstream_model_use


def test_top20_rank_alone_does_not_authorize_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            ranking=_ranking(rank=1, is_top_n_member=True, score=0.99),
            instrument=_instrument(complete=False, missing_fields=("contract_size",)),
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use


def test_missing_volatility_blocks_dynamic_scope() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            volatility=_volatility(
                realized_volatility=None,
                atr_or_rolling_range=10.0,
                dynamic_scope_usable=False,
            )
        )
    )
    assert not d.ready_for_dynamic_scope
    assert FuturesInputBlockReason.VOLATILITY_INCOMPLETE in d.block_reasons
    assert d.ready_for_downstream_model_use


def test_missing_spread_liquidity_blocks_capital_slot() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(liquidity=_liquidity(spread_bps=None, volume=1.0, quote_volume=None))
    )
    assert not d.ready_for_capital_slot
    assert FuturesInputBlockReason.LIQUIDITY_INCOMPLETE in d.block_reasons


def test_missing_funding_blocks_perpetual_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            candidate=_candidate(market_type=FuturesMarketType.PERPETUAL),
            derivatives=_derivatives(funding_available=False, funding_rate=None),
        )
    )
    assert not d.ready_for_capital_slot
    assert not d.ready_for_suitability
    assert FuturesInputBlockReason.PERPETUAL_FUNDING_INCOMPLETE in d.block_reasons


def test_opportunity_score_is_data_only_does_not_unblock() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            instrument=_instrument(complete=False, missing_fields=("min_notional",)),
            opportunity=_opportunity(opportunity_score=1.0),
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.ready_for_downstream_model_use


def test_inactivity_context_is_data_only_does_not_unblock() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            provenance=_provenance(complete=False, missing_fields=("source",)),
            opportunity=_opportunity(inactivity_score=0.0, candidate_is_inactive=False),
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED


def test_dashboard_label_cannot_authorize_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            instrument=_instrument(complete=False, missing_fields=("tick_size",)),
            dashboard_label="LIVE APPROVED — OPERATOR GO",
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.live_authorization


def test_ai_summary_cannot_authorize_readiness() -> None:
    d = evaluate_futures_input_snapshot(
        _snapshot(
            provenance=_provenance(complete=False),
            ai_summary="Model recommends immediate Testnet enablement.",
        )
    )
    assert d.status is FuturesReadinessStatus.BLOCKED
    assert not d.is_authority


def test_live_authorization_on_candidate_is_ignored_in_decision() -> None:
    d = evaluate_futures_input_snapshot(_snapshot(candidate=_candidate(live_authorization=True)))
    assert not d.live_authorization


def test_no_forbidden_top_level_imports_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "double_play_futures_input.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad_roots = {
        "ccxt",
        "requests",
        "urllib3",
        "httpx",
        "aiohttp",
        "socket",
        "websockets",
        "boto3",
        "botocore",
        "mlflow",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                base = n.name.split(".")[0]
                assert base not in bad_roots
                assert base != "trading"
        if isinstance(node, ast.ImportFrom) and node.module:
            mod0 = node.module.split(".")[0]
            assert mod0 not in bad_roots
            assert mod0 != "trading"
