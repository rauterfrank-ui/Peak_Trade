# src/trading/master_v2/double_play_futures_input.py
"""
Pure Double Play futures input snapshot model: data-only readiness evaluation.

No I/O, scanners, exchanges, market-data fetch, selection, allocation, or Live authority.
Aligned with docs/ops/specs/MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

DOUBLE_PLAY_FUTURES_INPUT_LAYER_VERSION = "v0"


class FuturesMarketType(str, Enum):
    FUTURES = "futures"
    PERPETUAL = "perpetual"
    SWAP = "swap"
    UNKNOWN = "unknown"


class FuturesFreshnessState(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class FuturesReadinessStatus(str, Enum):
    """Data-only readiness label; non-authority."""

    DATA_READY = "data_ready"
    BLOCKED = "blocked"


class FuturesInputBlockReason(str, Enum):
    INSTRUMENT_METADATA_INCOMPLETE = "instrument_metadata_incomplete"
    MARKET_DATA_PROVENANCE_INCOMPLETE = "market_data_provenance_incomplete"
    FRESHNESS_STALE = "freshness_stale"
    FRESHNESS_UNKNOWN = "freshness_unknown"
    MARKET_TYPE_UNKNOWN = "market_type_unknown"
    VOLATILITY_INCOMPLETE = "volatility_incomplete"
    LIQUIDITY_INCOMPLETE = "liquidity_incomplete"
    PERPETUAL_FUNDING_INCOMPLETE = "perpetual_funding_incomplete"


@dataclass(frozen=True)
class FuturesCandidateSnapshot:
    candidate_id: str
    instrument_id: str
    symbol: str
    market_type: FuturesMarketType
    exchange: str
    base_currency: str
    quote_currency: str
    live_authorization: bool = False


@dataclass(frozen=True)
class FuturesRankingSnapshot:
    source_universe_size: Optional[int]
    selected_top_n: Optional[int]
    rank: Optional[int]
    score: Optional[float]
    score_components_complete: bool
    is_top_n_member: bool


@dataclass(frozen=True)
class FuturesInstrumentMetadataStatus:
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
class FuturesMarketDataProvenanceStatus:
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
class FuturesVolatilityProfile:
    realized_volatility: Optional[float]
    atr_or_rolling_range: Optional[float]
    volatility_regime: Optional[str]
    dynamic_scope_usable: bool


@dataclass(frozen=True)
class FuturesLiquidityProfile:
    spread_bps: Optional[float]
    average_spread_bps: Optional[float]
    volume: Optional[float]
    quote_volume: Optional[float]
    liquidity_regime: Optional[str]
    spread_quality: Optional[str]


@dataclass(frozen=True)
class FuturesDerivativesProfile:
    funding_available: bool
    funding_rate: Optional[float]
    funding_regime: Optional[str]
    open_interest_available: bool
    open_interest: Optional[float]
    open_interest_regime: Optional[str]


@dataclass(frozen=True)
class FuturesOpportunityProfile:
    opportunity_score: Optional[float]
    inactivity_score: Optional[float]
    movement_above_fee_slippage_breakeven: Optional[bool]
    chop_risk: Optional[str]
    candidate_is_inactive: bool


@dataclass(frozen=True)
class FuturesInputSnapshot:
    candidate: FuturesCandidateSnapshot
    ranking: FuturesRankingSnapshot
    instrument: FuturesInstrumentMetadataStatus
    provenance: FuturesMarketDataProvenanceStatus
    volatility: FuturesVolatilityProfile
    liquidity: FuturesLiquidityProfile
    derivatives: FuturesDerivativesProfile
    opportunity: FuturesOpportunityProfile
    dashboard_label: Optional[str] = None
    ai_summary: Optional[str] = None


@dataclass(frozen=True)
class FuturesInputReadinessDecision:
    status: FuturesReadinessStatus
    ready_for_downstream_model_use: bool
    ready_for_dynamic_scope: bool
    ready_for_capital_slot: bool
    ready_for_suitability: bool
    ready_for_survival_envelope: bool
    block_reasons: Tuple[FuturesInputBlockReason, ...]
    missing_inputs: Tuple[str, ...]
    is_authority: bool = False
    is_signal: bool = False
    live_authorization: bool = False


def instrument_metadata_complete(status: FuturesInstrumentMetadataStatus) -> bool:
    return bool(status.complete)


def market_data_provenance_complete(status: FuturesMarketDataProvenanceStatus) -> bool:
    return bool(status.complete)


def volatility_profile_complete(profile: FuturesVolatilityProfile) -> bool:
    return (
        profile.realized_volatility is not None
        and profile.atr_or_rolling_range is not None
        and profile.dynamic_scope_usable
    )


def liquidity_profile_complete(profile: FuturesLiquidityProfile) -> bool:
    if profile.spread_bps is None:
        return False
    return profile.volume is not None or profile.quote_volume is not None


def perpetual_derivatives_profile_complete(profile: FuturesDerivativesProfile) -> bool:
    return profile.funding_available and profile.funding_rate is not None


def _perpetual_like(market_type: FuturesMarketType) -> bool:
    return market_type in (FuturesMarketType.PERPETUAL, FuturesMarketType.SWAP)


def evaluate_futures_input_snapshot(
    snapshot: FuturesInputSnapshot,
) -> FuturesInputReadinessDecision:
    """
    Fail-closed, data-only readiness over a precomputed futures input snapshot.

    Display fields (dashboard_label, ai_summary, ranking context, opportunity scalars)
    never confer authority. Candidate ``live_authorization`` is ignored.
    """
    blocks: list[FuturesInputBlockReason] = []
    missing: list[str] = []

    if not instrument_metadata_complete(snapshot.instrument):
        blocks.append(FuturesInputBlockReason.INSTRUMENT_METADATA_INCOMPLETE)
        missing.extend(list(snapshot.instrument.missing_fields))

    if not market_data_provenance_complete(snapshot.provenance):
        blocks.append(FuturesInputBlockReason.MARKET_DATA_PROVENANCE_INCOMPLETE)
        missing.extend(list(snapshot.provenance.missing_fields))

    if snapshot.provenance.freshness_state is FuturesFreshnessState.STALE:
        blocks.append(FuturesInputBlockReason.FRESHNESS_STALE)
    elif snapshot.provenance.freshness_state is FuturesFreshnessState.UNKNOWN:
        blocks.append(FuturesInputBlockReason.FRESHNESS_UNKNOWN)

    if snapshot.candidate.market_type is FuturesMarketType.UNKNOWN:
        blocks.append(FuturesInputBlockReason.MARKET_TYPE_UNKNOWN)

    downstream_ok = (
        instrument_metadata_complete(snapshot.instrument)
        and market_data_provenance_complete(snapshot.provenance)
        and snapshot.provenance.freshness_state is FuturesFreshnessState.FRESH
        and snapshot.candidate.market_type is not FuturesMarketType.UNKNOWN
    )

    vol_ok = volatility_profile_complete(snapshot.volatility)
    if not vol_ok:
        blocks.append(FuturesInputBlockReason.VOLATILITY_INCOMPLETE)

    liq_ok = liquidity_profile_complete(snapshot.liquidity)
    if not liq_ok:
        blocks.append(FuturesInputBlockReason.LIQUIDITY_INCOMPLETE)

    perp_need = _perpetual_like(snapshot.candidate.market_type)
    perp_ok = perpetual_derivatives_profile_complete(snapshot.derivatives) if perp_need else True
    if perp_need and not perp_ok:
        blocks.append(FuturesInputBlockReason.PERPETUAL_FUNDING_INCOMPLETE)

    ready_downstream = downstream_ok
    ready_dynamic = downstream_ok and vol_ok
    ready_capital = downstream_ok and liq_ok and perp_ok
    ready_suitability = downstream_ok and vol_ok and liq_ok and perp_ok
    ready_survival = downstream_ok

    unique_blocks = tuple(dict.fromkeys(blocks))
    unique_missing = tuple(dict.fromkeys(m for m in missing if m))

    all_clear = (
        ready_downstream
        and ready_dynamic
        and ready_capital
        and ready_suitability
        and ready_survival
    )
    status = FuturesReadinessStatus.DATA_READY if all_clear else FuturesReadinessStatus.BLOCKED

    return FuturesInputReadinessDecision(
        status=status,
        ready_for_downstream_model_use=ready_downstream,
        ready_for_dynamic_scope=ready_dynamic,
        ready_for_capital_slot=ready_capital,
        ready_for_suitability=ready_suitability,
        ready_for_survival_envelope=ready_survival,
        block_reasons=unique_blocks,
        missing_inputs=unique_missing,
        is_authority=False,
        is_signal=False,
        live_authorization=False,
    )
