from __future__ import annotations

from dataclasses import replace

from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType


def spread_consistent_quotes_v2(mark_price: float) -> tuple[float, float, float]:
    mark = float(mark_price)
    if mark >= 1.0:
        best_bid = mark * 0.9999
        best_ask = mark * 1.0001
    else:
        tick = max(mark * 1e-4, 1e-8)
        best_bid = mark - tick
        best_ask = mark + tick
    spread = best_ask - best_bid
    return best_bid, best_ask, spread


def build_finalized_cmc_v2(
    *,
    instrument_id: str,
    mark_price: float,
    volatility_estimate: float,
    trading_epoch: int,
) -> CanonicalMarketContextV1:
    mark = float(mark_price)
    best_bid, best_ask, spread = spread_consistent_quotes_v2(mark)
    ctx = CanonicalMarketContextV1(
        context_id=f"ctx-v2-{instrument_id}-e{trading_epoch}",
        instrument_id=instrument_id,
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=trading_epoch,
        market_event_time="2026-06-30T12:00:00+00:00",
        decision_time="2026-06-30T12:00:01+00:00",
        bar_interval="1m",
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=mark,
        index_price=mark * 0.999,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        volume=1_250_000.0,
        open_interest=85_000_000.0,
        funding_rate=0.00012,
        volatility_estimate=float(volatility_estimate),
        trend_feature_set={"slope": 0.02, "strength": 0.71},
        momentum_feature_set={"rsi": 55.0, "roc": 0.015},
        liquidity_feature_set={"depth_score": 0.88},
        market_structure_feature_set={"range_ratio": 0.42},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_COMPLETE,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
        input_digest="",
    )
    return with_computed_input_digest(ctx)


def refresh_cmc_mark_v2(
    ctx: CanonicalMarketContextV1,
    *,
    mark_price: float,
    trading_epoch: int,
) -> CanonicalMarketContextV1:
    mark = float(mark_price)
    best_bid, best_ask, spread = spread_consistent_quotes_v2(mark)
    return with_computed_input_digest(
        replace(
            ctx,
            mark_price=mark,
            index_price=mark * 0.999,
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            trading_epoch=trading_epoch,
            context_id=f"ctx-v2-{ctx.instrument_id}-e{trading_epoch}",
        )
    )
