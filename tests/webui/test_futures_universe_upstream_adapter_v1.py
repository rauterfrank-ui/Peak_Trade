"""U1 — futures_universe_upstream_adapter_v1 contract/static tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MAX_RANKING_ROWS,
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
    validate_universe_selection_payload,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_universe_upstream_adapter_v1 import (
    REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE,
    REASON_INELIGIBLE_MARKET_TYPE,
    REASON_INELIGIBLE_SPOT_SYMBOL,
    REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH,
    REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE,
    REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED,
    REASON_UPSTREAM_SOURCE_EMPTY,
    FuturesUniverseUpstreamInputV1,
    map_futures_packet_sequence,
    map_futures_packets_to_universe_selection_readmodel,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesMarketType,
)
from trading.master_v2.double_play_futures_input_producer import (
    FuturesProducerCandidate,
    FuturesProducerDerivatives,
    FuturesProducerInstrumentMetadata,
    FuturesProducerLiquidity,
    FuturesProducerMarketDataProvenance,
    FuturesProducerOpportunity,
    FuturesProducerPacket,
    FuturesProducerRanking,
    FuturesProducerVolatility,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_MODULE = (
    PROJECT_ROOT
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "futures_universe_upstream_adapter_v1.py"
)

GENERATED_AT = "2026-06-08T16:30:00Z"
SOURCE_RUN_ID = "fixture_upstream_u1_v1"
SOURCE_STAGE = "paper"


def _candidate(**overrides: object) -> FuturesProducerCandidate:
    base: dict = {
        "candidate_id": "c-eth",
        "instrument_id": "inst-eth-perp",
        "symbol": "ETHUSDT",
        "market_type": FuturesMarketType.PERPETUAL,
        "exchange": "binance_futures",
        "base_currency": "ETH",
        "quote_currency": "USDT",
        "live_authorization": False,
    }
    base.update(overrides)
    return FuturesProducerCandidate(**base)


def _ranking(**overrides: object) -> FuturesProducerRanking:
    base: dict = {
        "source_universe_size": 50,
        "selected_top_n": 20,
        "rank": 1,
        "score": 0.91,
        "score_components_complete": True,
        "is_top_n_member": True,
    }
    base.update(overrides)
    return FuturesProducerRanking(**base)


def _instrument(**overrides: object) -> FuturesProducerInstrumentMetadata:
    base: dict = {
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
    base.update(overrides)
    return FuturesProducerInstrumentMetadata(**base)


def _provenance(**overrides: object) -> FuturesProducerMarketDataProvenance:
    base: dict = {
        "complete": True,
        "freshness_state": FuturesFreshnessState.FRESH,
        "dataset_id": "ds-u1-fixture",
        "source": "fixture",
        "mark_available": True,
        "index_available": True,
        "last_available": True,
        "ohlcv_available": True,
        "funding_available": True,
        "open_interest_available": True,
        "missing_fields": (),
    }
    base.update(overrides)
    return FuturesProducerMarketDataProvenance(**base)


def _volatility() -> FuturesProducerVolatility:
    return FuturesProducerVolatility(
        realized_volatility=0.4,
        atr_or_rolling_range=100.0,
        volatility_regime="medium",
        dynamic_scope_usable=True,
    )


def _liquidity() -> FuturesProducerLiquidity:
    return FuturesProducerLiquidity(
        spread_bps=1.2,
        average_spread_bps=1.5,
        volume=1_000_000.0,
        quote_volume=40_000_000.0,
        liquidity_regime="deep",
        spread_quality="tight",
    )


def _derivatives() -> FuturesProducerDerivatives:
    return FuturesProducerDerivatives(
        funding_available=True,
        funding_rate=0.0001,
        funding_regime="neutral",
        open_interest_available=True,
        open_interest=1e9,
        open_interest_regime="high",
    )


def _opportunity() -> FuturesProducerOpportunity:
    return FuturesProducerOpportunity(
        opportunity_score=0.8,
        inactivity_score=0.1,
        movement_above_fee_slippage_breakeven=True,
        chop_risk="low",
        candidate_is_inactive=False,
    )


def _packet(**overrides: object) -> FuturesProducerPacket:
    parts: dict = {
        "candidate": _candidate(),
        "ranking": _ranking(),
        "instrument": _instrument(),
        "provenance": _provenance(),
        "volatility": _volatility(),
        "liquidity": _liquidity(),
        "derivatives": _derivatives(),
        "opportunity": _opportunity(),
    }
    parts.update(overrides)
    return FuturesProducerPacket(**parts)


def _input(
    packets: tuple[FuturesProducerPacket, ...],
    **overrides: object,
) -> FuturesUniverseUpstreamInputV1:
    base: dict = {
        "source_run_id": SOURCE_RUN_ID,
        "source_stage": SOURCE_STAGE,
        "generated_at": GENERATED_AT,
        "packets": packets,
        "fixture_marked": True,
    }
    base.update(overrides)
    return FuturesUniverseUpstreamInputV1(**base)


def test_tc1_accepts_futures_only_packet() -> None:
    packets = (
        _packet(
            candidate=_candidate(candidate_id="c-eth", symbol="ETHUSDT"),
            ranking=_ranking(rank=1, score=0.91),
        ),
        _packet(
            candidate=_candidate(
                candidate_id="c-sol",
                instrument_id="inst-sol-perp",
                symbol="SOLUSDT",
                base_currency="SOL",
            ),
            ranking=_ranking(rank=2, score=0.87),
        ),
        _packet(
            candidate=_candidate(
                candidate_id="c-avax",
                instrument_id="inst-avax-perp",
                symbol="AVAXUSDT",
                base_currency="AVAX",
            ),
            ranking=_ranking(rank=3, score=0.82),
        ),
    )
    result = map_futures_packets_to_universe_selection_readmodel(_input(packets))

    assert result.status == "ok"
    assert not result.rejection_reasons
    contract = validate_universe_selection_payload(result.payload)
    assert len(contract.universe) == 3
    assert len(contract.ranking) == 3
    assert contract.selected_future is not None
    assert contract.selected_future.symbol == "ETHUSDT"
    assert contract.missing_truth.universe == "PERSISTED"
    assert contract.missing_truth.ranking == "PERSISTED"
    assert contract.missing_truth.selected_future == "PERSISTED"
    assert result.payload["non_authorizing"] is True


def test_tc2_rejects_spot_selected_truth() -> None:
    spot_packet = _packet(
        candidate=_candidate(
            candidate_id="c-btc-spot",
            instrument_id="inst-btc-spot",
            symbol="BTC/USD",
            market_type=FuturesMarketType.UNKNOWN,
            exchange="kraken",
            base_currency="BTC",
            quote_currency="USD",
        ),
        instrument=_instrument(complete=False),
        ranking=_ranking(rank=1, score=0.99),
    )
    futures_packet = _packet(
        candidate=_candidate(candidate_id="c-eth", symbol="ETHUSDT"),
        ranking=_ranking(rank=2, score=0.9),
    )
    result = map_futures_packets_to_universe_selection_readmodel(
        _input(
            (spot_packet, futures_packet),
            selected_candidate_id="c-btc-spot",
        )
    )

    assert result.payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED in result.rejection_reasons
    assert result.payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED
    assert len(result.payload["universe"]) >= 1
    assert all(row["symbol"] != "BTC/USD" for row in result.payload["universe"])


def test_tc2_rejects_btc_eur_spot_selected() -> None:
    spot_packet = _packet(
        candidate=_candidate(
            candidate_id="c-btc-eur",
            symbol="BTC/EUR",
            market_type=FuturesMarketType.UNKNOWN,
            exchange="kraken",
            quote_currency="EUR",
        ),
        instrument=_instrument(complete=False),
    )
    result = map_futures_packets_to_universe_selection_readmodel(
        _input((spot_packet,), selected_candidate_id="c-btc-eur")
    )

    assert result.status == "missing_truth"
    assert REASON_UPSTREAM_SOURCE_EMPTY in result.rejection_reasons or (
        REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED in result.rejection_reasons
    )
    assert result.payload["selected_future"]["truth_status"] == "NOT_PERSISTED"


def test_tc3_rejects_market_ranking_funnel_as_truth() -> None:
    result = map_futures_packet_sequence(
        source_run_id=SOURCE_RUN_ID,
        source_stage=SOURCE_STAGE,
        generated_at=GENERATED_AT,
        packets=(_packet(),),
        upstream_source_kind="market_ranking_funnel_readmodel.v0",
        fixture_marked=True,
    )

    assert result.status == "missing_truth"
    assert REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH in result.rejection_reasons
    assert result.payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE
    assert result.payload["universe"] == []


def test_tc3_rejects_market_surface_producer_marker() -> None:
    result = map_futures_packet_sequence(
        source_run_id=SOURCE_RUN_ID,
        source_stage=SOURCE_STAGE,
        generated_at=GENERATED_AT,
        packets=(_packet(),),
        upstream_producer_id="market_surface",
        fixture_marked=True,
    )

    assert result.status == "missing_truth"
    assert REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH in result.rejection_reasons


def test_tc4_missing_upstream_data_returns_missing_truth() -> None:
    result = map_futures_packets_to_universe_selection_readmodel(_input(()))

    assert result.status == "missing_truth"
    assert REASON_UPSTREAM_SOURCE_EMPTY in result.rejection_reasons
    assert result.payload["universe"] == []
    assert result.payload["ranking"] == []
    assert result.payload["selected_future"] == {"truth_status": "NOT_PERSISTED"}
    validate_universe_selection_payload(result.payload)


def test_tc5_ranking_cap_and_eligibility() -> None:
    packets: list[FuturesProducerPacket] = []
    for index in range(1, 23):
        packets.append(
            _packet(
                candidate=_candidate(
                    candidate_id=f"c-fut-{index:02d}",
                    instrument_id=f"inst-fut-{index:02d}",
                    symbol=f"FUT{index:02d}USDT",
                    base_currency=f"FUT{index:02d}",
                ),
                ranking=_ranking(rank=index, score=1.0 - index * 0.01),
            )
        )
    packets.append(
        _packet(
            candidate=_candidate(
                candidate_id="c-spot-btc",
                symbol="BTC/EUR",
                market_type=FuturesMarketType.UNKNOWN,
                exchange="kraken",
                quote_currency="EUR",
            ),
            instrument=_instrument(complete=False),
            ranking=_ranking(rank=0, score=9.99),
        )
    )
    packets.append(
        _packet(
            candidate=_candidate(
                candidate_id="c-incomplete",
                symbol="DOGEUSDT",
                instrument_id="inst-doge",
                base_currency="DOGE",
            ),
            instrument=_instrument(complete=False),
            ranking=_ranking(rank=99, score=0.01),
        )
    )

    result = map_futures_packets_to_universe_selection_readmodel(_input(tuple(packets)))

    assert len(result.payload["ranking"]) == MAX_RANKING_ROWS
    ranking_symbols = {row["symbol"] for row in result.payload["ranking"]}
    assert "BTC/EUR" not in ranking_symbols
    assert "DOGEUSDT" not in ranking_symbols
    assert any(
        item.reason in (REASON_INELIGIBLE_SPOT_SYMBOL, REASON_INELIGIBLE_MARKET_TYPE)
        for item in result.eligibility_exclusions
        if item.symbol == "BTC/EUR"
    )
    assert any(
        item.reason == REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE
        for item in result.eligibility_exclusions
        if item.candidate_id == "c-incomplete"
    )


def test_tc6_selected_not_in_universe_rejected() -> None:
    eligible = _packet(
        candidate=_candidate(candidate_id="c-eth", symbol="ETHUSDT"),
        ranking=_ranking(rank=1),
    )
    result = map_futures_packets_to_universe_selection_readmodel(
        _input((eligible,), selected_candidate_id="c-missing")
    )

    assert result.payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE in result.rejection_reasons
    assert result.payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED


def test_tc7_contract_compatibility() -> None:
    packets = (
        _packet(
            candidate=_candidate(candidate_id="c-sol", symbol="SOLUSDT", base_currency="SOL"),
            ranking=_ranking(rank=1, score=0.95),
        ),
        _packet(
            candidate=_candidate(
                candidate_id="c-eth",
                symbol="ETHUSDT",
            ),
            ranking=_ranking(rank=2, score=0.9),
        ),
    )
    result = map_futures_packets_to_universe_selection_readmodel(_input(packets))
    contract = validate_universe_selection_payload(result.payload)

    assert contract.schema_name == "universe_selection_readmodel.v1"
    assert contract.non_authorizing is True
    assert contract.selected_future is not None
    assert contract.selected_future.symbol == "SOLUSDT"


def test_adapter_module_has_no_forbidden_imports() -> None:
    tree = ast.parse(ADAPTER_MODULE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    forbidden_fragments = (
        "market_ranking_funnel",
        "market_surface",
        "scan_markets",
        "run_market_scan",
        "src.execution",
        "src.risk",
        "src.governance",
    )
    for fragment in forbidden_fragments:
        assert not any(fragment in name for name in imported), fragment


def test_spot_symbol_excluded_from_universe_even_with_perpetual_market_type() -> None:
    """BTC/USD with PERPETUAL market_type still rejected via spot symbol guard."""
    packet = _packet(
        candidate=_candidate(
            candidate_id="c-btc-usd",
            symbol="BTC/USD",
            market_type=FuturesMarketType.PERPETUAL,
        ),
    )
    result = map_futures_packets_to_universe_selection_readmodel(_input((packet,)))

    assert result.status == "missing_truth"
    assert any(
        item.reason == REASON_INELIGIBLE_SPOT_SYMBOL for item in result.eligibility_exclusions
    )
