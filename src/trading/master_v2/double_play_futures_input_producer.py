# src/trading/master_v2/double_play_futures_input_producer.py
"""
Pure Double Play futures input producer adapter: static packet -> FuturesInputSnapshot.

No scanners, exchanges, registry/evidence writers, sessions, or Live authority.
Aligned with docs/ops/specs/MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from trading.master_v2.double_play_futures_input import (
    FuturesCandidateSnapshot,
    FuturesDerivativesProfile,
    FuturesInputReadinessDecision,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesLiquidityProfile,
    FuturesMarketDataProvenanceStatus,
    FuturesMarketType,
    FuturesOpportunityProfile,
    FuturesRankingSnapshot,
    FuturesFreshnessState,
    FuturesVolatilityProfile,
    evaluate_futures_input_snapshot,
)

DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_LAYER_VERSION = "v0"


class FuturesProducerAdapterStatus(str, Enum):
    OK = "ok"
    BLOCKED = "blocked"


class FuturesProducerAdapterBlockReason(str, Enum):
    """Adapter-level block before or instead of snapshot consumption."""

    RUNTIME_HANDLE_DETECTED = "runtime_handle_detected"


@dataclass(frozen=True)
class FuturesProducerCandidate:
    candidate_id: str
    instrument_id: str
    symbol: str
    market_type: FuturesMarketType
    exchange: str
    base_currency: str
    quote_currency: str
    live_authorization: bool = False


@dataclass(frozen=True)
class FuturesProducerRanking:
    source_universe_size: Optional[int]
    selected_top_n: Optional[int]
    rank: Optional[int]
    score: Optional[float]
    score_components_complete: bool
    is_top_n_member: bool


@dataclass(frozen=True)
class FuturesProducerInstrumentMetadata:
    complete: bool
    contract_size_known: bool
    tick_size_known: bool
    step_size_known: bool
    min_qty_known: bool
    min_notional_known: bool
    margin_asset_known: bool
    settlement_asset_known: bool
    leverage_bounds_known: bool
    missing_fields: Tuple[str, ...]


@dataclass(frozen=True)
class FuturesProducerMarketDataProvenance:
    complete: bool
    freshness_state: FuturesFreshnessState
    dataset_id: Optional[str]
    source: Optional[str]
    mark_available: bool
    index_available: bool
    last_available: bool
    ohlcv_available: bool
    funding_available: bool
    open_interest_available: bool
    missing_fields: Tuple[str, ...]


@dataclass(frozen=True)
class FuturesProducerVolatility:
    realized_volatility: Optional[float]
    atr_or_rolling_range: Optional[float]
    volatility_regime: Optional[str]
    dynamic_scope_usable: bool


@dataclass(frozen=True)
class FuturesProducerLiquidity:
    spread_bps: Optional[float]
    average_spread_bps: Optional[float]
    volume: Optional[float]
    quote_volume: Optional[float]
    liquidity_regime: Optional[str]
    spread_quality: Optional[str]


@dataclass(frozen=True)
class FuturesProducerDerivatives:
    funding_available: bool
    funding_rate: Optional[float]
    funding_regime: Optional[str]
    open_interest_available: bool
    open_interest: Optional[float]
    open_interest_regime: Optional[str]


@dataclass(frozen=True)
class FuturesProducerOpportunity:
    opportunity_score: Optional[float]
    inactivity_score: Optional[float]
    movement_above_fee_slippage_breakeven: Optional[bool]
    chop_risk: Optional[str]
    candidate_is_inactive: bool


@dataclass(frozen=True)
class FuturesProducerPacket:
    candidate: FuturesProducerCandidate
    ranking: FuturesProducerRanking
    instrument: FuturesProducerInstrumentMetadata
    provenance: FuturesProducerMarketDataProvenance
    volatility: FuturesProducerVolatility
    liquidity: FuturesProducerLiquidity
    derivatives: FuturesProducerDerivatives
    opportunity: FuturesProducerOpportunity
    dashboard_label: Optional[str] = None
    ai_summary: Optional[str] = None


@dataclass(frozen=True)
class FuturesProducerAdapterDecision:
    adapter_status: FuturesProducerAdapterStatus
    adapter_block_reasons: Tuple[FuturesProducerAdapterBlockReason, ...]
    snapshot: Optional[FuturesInputSnapshot]
    readiness: Optional[FuturesInputReadinessDecision]


def producer_packet_has_runtime_handles(obj: object, *, _seen: set[int] | None = None) -> bool:
    """
    Return True if ``obj`` embeds a non-data value (potential runtime handle).

    Allowed: ``None``, primitives, ``FuturesMarketType``, ``FuturesFreshnessState``,
    tuples of allowed values, and frozen dataclasses composed only of allowed values.
    """
    if _seen is None:
        _seen = set()
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return False
    if isinstance(obj, (FuturesMarketType, FuturesFreshnessState)):
        return False
    oid = id(obj)
    if oid in _seen:
        return False
    if isinstance(obj, tuple):
        _seen.add(oid)
        return any(producer_packet_has_runtime_handles(item, _seen=_seen) for item in obj)
    fields = getattr(obj, "__dataclass_fields__", None)
    if fields is not None:
        _seen.add(oid)
        for f in fields.values():
            if producer_packet_has_runtime_handles(getattr(obj, f.name), _seen=_seen):
                return True
        return False
    return True


def producer_packet_complete_enough_for_snapshot(packet: FuturesProducerPacket) -> bool:
    """True when the packet is safe static data and can be mapped to a snapshot structurally."""
    return not producer_packet_has_runtime_handles(packet)


def _to_candidate(p: FuturesProducerCandidate) -> FuturesCandidateSnapshot:
    return FuturesCandidateSnapshot(
        candidate_id=p.candidate_id,
        instrument_id=p.instrument_id,
        symbol=p.symbol,
        market_type=p.market_type,
        exchange=p.exchange,
        base_currency=p.base_currency,
        quote_currency=p.quote_currency,
        live_authorization=False,
    )


def _to_ranking(p: FuturesProducerRanking) -> FuturesRankingSnapshot:
    return FuturesRankingSnapshot(
        source_universe_size=p.source_universe_size,
        selected_top_n=p.selected_top_n,
        rank=p.rank,
        score=p.score,
        score_components_complete=p.score_components_complete,
        is_top_n_member=p.is_top_n_member,
    )


def _to_instrument(p: FuturesProducerInstrumentMetadata) -> FuturesInstrumentMetadataStatus:
    return FuturesInstrumentMetadataStatus(
        complete=p.complete,
        contract_size_known=p.contract_size_known,
        tick_size_known=p.tick_size_known,
        step_size_known=p.step_size_known,
        min_qty_known=p.min_qty_known,
        min_notional_known=p.min_notional_known,
        margin_asset_known=p.margin_asset_known,
        settlement_asset_known=p.settlement_asset_known,
        leverage_bounds_known=p.leverage_bounds_known,
        missing_fields=p.missing_fields,
    )


def _to_provenance(p: FuturesProducerMarketDataProvenance) -> FuturesMarketDataProvenanceStatus:
    return FuturesMarketDataProvenanceStatus(
        complete=p.complete,
        freshness_state=p.freshness_state,
        dataset_id=p.dataset_id,
        source=p.source,
        mark_available=p.mark_available,
        index_available=p.index_available,
        last_available=p.last_available,
        ohlcv_available=p.ohlcv_available,
        funding_available=p.funding_available,
        open_interest_available=p.open_interest_available,
        missing_fields=p.missing_fields,
    )


def _to_volatility(p: FuturesProducerVolatility) -> FuturesVolatilityProfile:
    return FuturesVolatilityProfile(
        realized_volatility=p.realized_volatility,
        atr_or_rolling_range=p.atr_or_rolling_range,
        volatility_regime=p.volatility_regime,
        dynamic_scope_usable=p.dynamic_scope_usable,
    )


def _to_liquidity(p: FuturesProducerLiquidity) -> FuturesLiquidityProfile:
    return FuturesLiquidityProfile(
        spread_bps=p.spread_bps,
        average_spread_bps=p.average_spread_bps,
        volume=p.volume,
        quote_volume=p.quote_volume,
        liquidity_regime=p.liquidity_regime,
        spread_quality=p.spread_quality,
    )


def _to_derivatives(p: FuturesProducerDerivatives) -> FuturesDerivativesProfile:
    return FuturesDerivativesProfile(
        funding_available=p.funding_available,
        funding_rate=p.funding_rate,
        funding_regime=p.funding_regime,
        open_interest_available=p.open_interest_available,
        open_interest=p.open_interest,
        open_interest_regime=p.open_interest_regime,
    )


def _to_opportunity(p: FuturesProducerOpportunity) -> FuturesOpportunityProfile:
    return FuturesOpportunityProfile(
        opportunity_score=p.opportunity_score,
        inactivity_score=p.inactivity_score,
        movement_above_fee_slippage_breakeven=p.movement_above_fee_slippage_breakeven,
        chop_risk=p.chop_risk,
        candidate_is_inactive=p.candidate_is_inactive,
    )


def producer_packet_to_snapshot(packet: FuturesProducerPacket) -> FuturesInputSnapshot:
    """
    Map a static producer packet to ``FuturesInputSnapshot``.

    ``live_authorization`` on the producer candidate is ignored and forced to False
    on the snapshot. Raises ``ValueError`` if runtime handles are detected.
    """
    if producer_packet_has_runtime_handles(packet):
        msg = "producer packet contains runtime handles or disallowed values"
        raise ValueError(msg)
    return FuturesInputSnapshot(
        candidate=_to_candidate(packet.candidate),
        ranking=_to_ranking(packet.ranking),
        instrument=_to_instrument(packet.instrument),
        provenance=_to_provenance(packet.provenance),
        volatility=_to_volatility(packet.volatility),
        liquidity=_to_liquidity(packet.liquidity),
        derivatives=_to_derivatives(packet.derivatives),
        opportunity=_to_opportunity(packet.opportunity),
        dashboard_label=packet.dashboard_label,
        ai_summary=packet.ai_summary,
    )


def adapt_producer_packet_to_futures_input_snapshot(
    packet: FuturesProducerPacket,
) -> FuturesProducerAdapterDecision:
    """
    Adapt a static producer packet to a ``FuturesInputSnapshot`` and evaluate readiness.

    Returns a ``FuturesProducerAdapterDecision`` with optional ``snapshot`` and ``readiness``.
    When runtime handles are detected, ``adapter_status`` is ``BLOCKED`` and both are None.
    """
    if producer_packet_has_runtime_handles(packet):
        return FuturesProducerAdapterDecision(
            adapter_status=FuturesProducerAdapterStatus.BLOCKED,
            adapter_block_reasons=(FuturesProducerAdapterBlockReason.RUNTIME_HANDLE_DETECTED,),
            snapshot=None,
            readiness=None,
        )
    snapshot = producer_packet_to_snapshot(packet)
    readiness = evaluate_futures_input_snapshot(snapshot)
    return FuturesProducerAdapterDecision(
        adapter_status=FuturesProducerAdapterStatus.OK,
        adapter_block_reasons=(),
        snapshot=snapshot,
        readiness=readiness,
    )
