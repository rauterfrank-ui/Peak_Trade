# tests/trading/master_v2/test_double_play_pure_stack_contract.py
"""
Cross-module contract tests:
Futures Input (upstream, hand-built or producer-adapter) -> State -> Survival -> Suitability
-> Capital Slot -> Composition -> Dashboard Display snapshot (read-only aggregate).

Futures input is data-only context; composition does not consume it — scenario tests gate
eligibility explicitly. No runtime integration, registry, execution, or exchange
(import checks below).
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotBlockReason,
    CapitalSlotConfig,
    CapitalSlotReleaseReason,
    CapitalSlotState,
    CapitalSlotStatus,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionInput,
    DoublePlayCompositionDecision,
    DoublePlayCompositionStatus,
    RequestedSide,
    compose_double_play_decision,
)
from trading.master_v2.double_play_dashboard_display import (
    DashboardDisplayStatus,
    build_dashboard_display_snapshot,
)
from trading.master_v2.double_play_futures_input import (
    FuturesCandidateSnapshot,
    FuturesDerivativesProfile,
    FuturesFreshnessState,
    FuturesInputReadinessDecision,
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
from trading.master_v2.double_play_futures_input_producer import (
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
)
from trading.master_v2.double_play_state import (
    ScopeEvent,
    SideState,
    RuntimeScopeState,
    transition_state,
)
from trading.master_v2.double_play_survival import (
    ArithmeticFingerprint,
    DoublePlaySurvivalEnvelope,
    LayerArithmeticStatus,
    SequenceSurvivalMetrics,
    StateSwitchSurvivalLimits,
    SurvivalEnvelopeStatus,
    evaluate_survival_envelope,
)
from trading.master_v2.double_play_suitability import (
    InstrumentIntelligenceSummary,
    SideCompatibility,
    StrategyMetadata,
    SuitabilityClass,
    SuitabilityProjectionInput,
    project_strategy_suitability,
)

# --- state fixtures (aligned with test_double_play_state) ---
from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    StaticHardLimits,
)

GOOD = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
GOOD_ENVELOPE = RuntimeEnvelope(static=GOOD, live_authorization=False)
GOOD_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
EMPTY_ST = RuntimeScopeState()


def _ts(
    side: SideState,
    event: ScopeEvent,
    st: RuntimeScopeState,
    now: int = 0,
):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=GOOD_RULES,
        envelope=GOOD_ENVELOPE,
        now_tick=now,
    )


# --- survival fixtures (aligned with test_double_play_survival) ---
GOOD_LIM = StateSwitchSurvivalLimits(
    min_path_survival_ratio=0.5,
    max_early_loss_toxicity=0.9,
    min_margin_buffer_at_risk_99=0.1,
    max_sequence_fragility_index=0.5,
    max_liquidation_near_miss_rate=0.2,
    max_governance_breach_frequency=0.05,
    min_chop_switch_survival_score=0.4,
    max_effective_leverage=20.0,
    min_liquidation_buffer=0.05,
    max_adverse_fill_loss=0.15,
    live_authorization=False,
)


def _layer() -> LayerArithmeticStatus:
    return LayerArithmeticStatus(
        max_effective_leverage=10.0,
        min_liquidation_buffer=0.1,
        fee_breakeven_bps=2.0,
        expected_adverse_fill_loss=0.05,
        funding_cost_profile="flat",
        is_perpetual=True,
    )


def _fp_ok() -> ArithmeticFingerprint:
    return ArithmeticFingerprint(
        contract_spec_complete=True,
        fee_model_complete=True,
        slippage_model_complete=True,
        funding_model_complete=True,
        margin_model_complete=True,
        liquidation_model_complete=True,
        rounding_model_complete=True,
    )


def _seq_ok() -> SequenceSurvivalMetrics:
    return SequenceSurvivalMetrics(
        path_survival_ratio=0.8,
        early_loss_toxicity=0.2,
        margin_buffer_at_risk_99=0.2,
        sequence_fragility_index=0.2,
        liquidation_near_miss_rate=0.05,
        governance_breach_frequency=0.01,
        chop_switch_survival_score=0.7,
    )


def _env_ok() -> DoublePlaySurvivalEnvelope:
    return DoublePlaySurvivalEnvelope(
        fingerprint=_fp_ok(),
        long_layer=_layer(),
        short_layer=_layer(),
        sequence=_seq_ok(),
        limits=GOOD_LIM,
    )


def _ii_all() -> InstrumentIntelligenceSummary:
    return InstrumentIntelligenceSummary(
        volatility_profile_present=True,
        liquidity_profile_present=True,
        spread_profile_present=True,
        funding_profile_present=True,
        freshness_profile_present=True,
    )


def _suit_in(
    meta: StrategyMetadata,
    surv_ok: bool,
) -> SuitabilityProjectionInput:
    return SuitabilityProjectionInput(
        strategy=meta,
        instrument=_ii_all(),
        survival_envelope_allows=surv_ok,
    )


def _suit_allows_from_envelope(surv) -> bool:
    return surv.status == SurvivalEnvelopeStatus.OK and surv.pre_authorization_eligible


def _cs_cfg_ok() -> CapitalSlotConfig:
    return CapitalSlotConfig(
        profit_step_pct=0.10,
        cashflow_lock_fraction=0.30,
        reinvest_fraction=0.70,
        allow_auto_top_up=False,
        live_authorization=False,
        min_realized_volatility=0.05,
        min_atr_or_range=0.05,
        max_time_without_cashflow_step=10_000,
        min_opportunity_score=0.2,
    )


def _cs_state_ok(
    *,
    future: str = "BTC-USD-PERP",
    base: float = 300.0,
    realized: float = 340.0,
    survival_allows_slot: bool = True,
) -> CapitalSlotState:
    return CapitalSlotState(
        selected_future=future,
        initial_slot_base=base,
        active_slot_base=base,
        realized_or_settled_slot_equity=realized,
        unrealized_pnl=0.0,
        locked_cashflow=0.0,
        time_without_cashflow_step=0,
        realized_volatility=0.5,
        atr_or_range=0.5,
        opportunity_score=0.8,
        survival_allows_slot=survival_allows_slot,
    )


# --- futures input fixtures (aligned with test_double_play_futures_input) ---
def _fi_candidate(**overrides: object) -> FuturesCandidateSnapshot:
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


def _fi_ranking(**overrides: object) -> FuturesRankingSnapshot:
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


def _fi_instrument(**overrides: object) -> FuturesInstrumentMetadataStatus:
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


def _fi_provenance(**overrides: object) -> FuturesMarketDataProvenanceStatus:
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


def _fi_volatility(**overrides: object) -> FuturesVolatilityProfile:
    d: dict = {
        "realized_volatility": 0.42,
        "atr_or_rolling_range": 120.0,
        "volatility_regime": "medium",
        "dynamic_scope_usable": True,
    }
    d.update(overrides)
    return FuturesVolatilityProfile(**d)


def _fi_liquidity(**overrides: object) -> FuturesLiquidityProfile:
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


def _fi_derivatives(**overrides: object) -> FuturesDerivativesProfile:
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


def _fi_opportunity(**overrides: object) -> FuturesOpportunityProfile:
    d: dict = {
        "opportunity_score": 0.75,
        "inactivity_score": 0.1,
        "movement_above_fee_slippage_breakeven": True,
        "chop_risk": "low",
        "candidate_is_inactive": False,
    }
    d.update(overrides)
    return FuturesOpportunityProfile(**d)


def _fi_snapshot(**overrides: object) -> FuturesInputSnapshot:
    parts: dict = {
        "candidate": _fi_candidate(),
        "ranking": _fi_ranking(),
        "instrument": _fi_instrument(),
        "provenance": _fi_provenance(),
        "volatility": _fi_volatility(),
        "liquidity": _fi_liquidity(),
        "derivatives": _fi_derivatives(),
        "opportunity": _fi_opportunity(),
        "dashboard_label": None,
        "ai_summary": None,
    }
    parts.update(overrides)
    return FuturesInputSnapshot(**parts)


# --- producer packet fixtures (mirror _fi_* for adapter/stack contract) ---
def _prod_candidate(**overrides: object) -> FuturesProducerCandidate:
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
    return FuturesProducerCandidate(**d)


def _prod_ranking(**overrides: object) -> FuturesProducerRanking:
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


def _prod_instrument(**overrides: object) -> FuturesProducerInstrumentMetadata:
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


def _prod_provenance(**overrides: object) -> FuturesProducerMarketDataProvenance:
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
    return FuturesProducerMarketDataProvenance(**d)


def _prod_volatility(**overrides: object) -> FuturesProducerVolatility:
    d: dict = {
        "realized_volatility": 0.42,
        "atr_or_rolling_range": 120.0,
        "volatility_regime": "medium",
        "dynamic_scope_usable": True,
    }
    d.update(overrides)
    return FuturesProducerVolatility(**d)


def _prod_liquidity(**overrides: object) -> FuturesProducerLiquidity:
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


def _prod_derivatives(**overrides: object) -> FuturesProducerDerivatives:
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


def _prod_opportunity(**overrides: object) -> FuturesProducerOpportunity:
    d: dict = {
        "opportunity_score": 0.75,
        "inactivity_score": 0.1,
        "movement_above_fee_slippage_breakeven": True,
        "chop_risk": "low",
        "candidate_is_inactive": False,
    }
    d.update(overrides)
    return FuturesProducerOpportunity(**d)


def _prod_packet(**overrides: object) -> FuturesProducerPacket:
    parts: dict = {
        "candidate": _prod_candidate(),
        "ranking": _prod_ranking(),
        "instrument": _prod_instrument(),
        "provenance": _prod_provenance(),
        "volatility": _prod_volatility(),
        "liquidity": _prod_liquidity(),
        "derivatives": _prod_derivatives(),
        "opportunity": _prod_opportunity(),
        "dashboard_label": None,
        "ai_summary": None,
    }
    parts.update(overrides)
    return FuturesProducerPacket(**parts)


def _full_long_bull_stack_with_capital():
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-long",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="ETH-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    return fi, t2, surv, suit, rat, rel, comp


def _full_short_bear_stack_with_capital():
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.DOWNSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.SHORT_ACTIVE
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-short",
        strategy_family="m",
        declared_side=SideCompatibility.SHORT_BEAR,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="SOL-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.SHORT_BEAR,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    return fi, t2, surv, suit, rat, rel, comp


def _assert_dashboard_snapshot_invariants(snap) -> None:
    assert snap.display_only is True
    assert snap.no_live_banner_visible is True
    assert snap.trading_ready is False
    assert snap.testnet_ready is False
    assert snap.live_ready is False
    assert snap.live_authorization is False
    assert all(not p.live_authorization for p in snap.panels)
    assert all(not p.is_authority for p in snap.panels)
    assert all(not p.is_signal for p in snap.panels)


def _assert_no_live_authorization_pure_stack(
    *,
    fi: FuturesInputReadinessDecision,
    transition,
    surv,
    suit,
    rat=None,
    rel=None,
    comp: DoublePlayCompositionDecision,
    snap,
) -> None:
    assert not fi.live_authorization
    assert not transition.live_authorization_granted
    assert not surv.live_authorization
    assert not suit.live_authorization
    assert not suit.projection.live_authorization
    if rat is not None:
        assert not rat.live_authorization
    if rel is not None:
        assert not rel.live_authorization
    assert not comp.live_authorization
    assert not snap.live_authorization


def _stack_eligible_with_futures_gate(
    fi: FuturesInputReadinessDecision,
    comp: DoublePlayCompositionDecision,
) -> bool:
    """
    Scenario-level gate: pure composition may pass while futures input is blocked.
    Downstream eligibility in this contract requires both.
    """
    return (
        fi.status is FuturesReadinessStatus.DATA_READY
        and fi.ready_for_downstream_model_use
        and comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    )


def test_contract_1_valid_long_bull_path_eligible_model_only() -> None:
    s1, st1, t1 = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    assert s1 == SideState.LONG_ARMED
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    assert surv.status == SurvivalEnvelopeStatus.OK
    assert surv.pre_authorization_eligible
    assert surv.live_authorization is False

    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    assert suit.projection.suitability_class is SuitabilityClass.LONG_ONLY_CANDIDATE
    assert suit.projection.live_authorization is False
    assert suit.can_enter_long_bull_pool

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert comp.live_authorization is False
    assert t1.live_authorization_granted is False
    assert t2.live_authorization_granted is False

    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    assert fi.status is FuturesReadinessStatus.DATA_READY
    assert fi.ready_for_downstream_model_use
    assert not fi.is_authority
    assert not fi.is_signal
    assert not fi.live_authorization
    assert _stack_eligible_with_futures_gate(fi, comp)


def test_contract_2_valid_short_bear_path_eligible_model_only() -> None:
    s1, st1, t1 = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    assert s1 == SideState.SHORT_ARMED
    s2, st2, t2 = _ts(s1, ScopeEvent.DOWNSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.SHORT_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    assert surv.status == SurvivalEnvelopeStatus.OK

    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.SHORT_BEAR,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    assert suit.projection.suitability_class is SuitabilityClass.SHORT_ONLY_CANDIDATE
    assert suit.can_enter_short_bear_pool

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.SHORT_BEAR,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert comp.live_authorization is False

    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    assert fi.status is FuturesReadinessStatus.DATA_READY
    assert _stack_eligible_with_futures_gate(fi, comp)


def test_contract_3_survival_blocker_prevents_composition() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    bad_fp = replace(_fp_ok(), contract_spec_complete=False)
    bad_env = replace(_env_ok(), fingerprint=bad_fp)
    surv = evaluate_survival_envelope(bad_env)
    assert surv.status == SurvivalEnvelopeStatus.BLOCKED

    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    allow = _suit_allows_from_envelope(surv)
    suit = project_strategy_suitability(_suit_in(meta, allow))
    assert suit.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED


def test_contract_4_unknown_suitability_prevents_composition() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.UNKNOWN,
        explicit_side_evidence=False,
        registry_label="x",
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    assert suit.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED


def test_contract_5_kill_all_blocks_despite_valid_survival_and_suit() -> None:
    _s, _st, t_kill = _ts(SideState.LONG_ACTIVE, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 0)
    assert _s == SideState.KILL_ALL

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    assert suit.projection.suitability_class is SuitabilityClass.LONG_ONLY_CANDIDATE

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t_kill,
            resulting_side_state=SideState.KILL_ALL,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.KILL_ALL
    assert comp.live_authorization is False


def test_contract_6_chop_guard_blocks_despite_valid_survival_and_suit() -> None:
    s_chop, st_chop, t_chop = _ts(SideState.SHORT_ARMED, ScopeEvent.CHOP_DETECTED, EMPTY_ST, 0)
    assert s_chop == SideState.CHOP_GUARD_BLOCK

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    assert suit.projection.suitability_class is SuitabilityClass.BOTH_SIDES_CANDIDATE
    assert suit.can_enter_long_bull_pool and suit.can_enter_short_bear_pool

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t_chop,
            resulting_side_state=s_chop,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.CHOP_GUARD
    assert comp.live_authorization is False


def test_contract_7_live_authorization_false_all_layers() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert not t2.live_authorization_granted
    assert not surv.live_authorization
    assert not suit.projection.live_authorization
    assert not suit.live_authorization
    assert not comp.live_authorization
    assert GOOD_ENVELOPE.live_authorization is False


def test_contract_10_long_bull_stack_with_capital_slot_ratchet_context_eligible_model_only() -> (
    None
):
    s1, st1, t1 = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-long",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="ETH-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rat.can_ratchet
    assert rat.ratchet_target == 330.0
    assert rat.new_active_slot_base == 340.0
    assert not rel.released
    assert rel.status is CapitalSlotStatus.ACTIVE
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert not rel.authorizes_new_future_selection
    assert not rel.authorizes_new_trade

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert not comp.live_authorization
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    assert _stack_eligible_with_futures_gate(fi, comp)


def test_contract_11_short_bear_stack_with_capital_slot_ratchet_context_eligible_model_only() -> (
    None
):
    s1, st1, t1 = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.DOWNSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.SHORT_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-short",
        strategy_family="m",
        declared_side=SideCompatibility.SHORT_BEAR,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="SOL-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rat.can_ratchet
    assert not rel.released
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert not rel.authorizes_new_trade

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.SHORT_BEAR,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    assert _stack_eligible_with_futures_gate(fi, comp)


def test_contract_12_capital_slot_survival_blocks_ratchet_without_trade_or_release_authority() -> (
    None
):
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-surv-slot",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY

    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(realized=400.0, survival_allows_slot=False)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    assert not rat.can_ratchet
    assert CapitalSlotBlockReason.SURVIVAL_NOT_ALLOWED in rat.block_reasons
    assert not rat.live_authorization

    comp_cs = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
        )
    )
    assert comp_cs.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.CAPITAL_SLOT_RATCHET_BLOCKED in comp_cs.block_reasons

    rel_ok = evaluate_capital_slot_release(cfg, cs_st)
    assert not rel_ok.authorizes_new_trade
    assert not rel_ok.authorizes_new_future_selection

    rel_inact = evaluate_capital_slot_release(
        cfg,
        replace(cs_st, realized_volatility=0.01, atr_or_range=0.01),
    )
    assert rel_inact.released
    assert rel_inact.release_reason is CapitalSlotReleaseReason.INACTIVITY
    assert not rel_inact.authorizes_new_trade
    assert not rel_inact.authorizes_new_future_selection


def test_contract_13_inactivity_release_is_data_only_no_new_future_or_trade() -> None:
    cfg = _cs_cfg_ok()
    cs_st = replace(
        _cs_state_ok(),
        realized_volatility=0.01,
        atr_or_range=0.01,
    )
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rel.released
    assert rel.status is CapitalSlotStatus.RELEASED
    assert rel.release_reason is CapitalSlotReleaseReason.INACTIVITY
    assert not rel.live_authorization
    assert not rel.authorizes_new_future_selection
    assert not rel.authorizes_new_trade


def test_contract_14_opportunity_release_is_data_only_no_new_future_or_trade() -> None:
    cfg = _cs_cfg_ok()
    cs_st = replace(_cs_state_ok(), opportunity_score=0.05)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rel.released
    assert rel.release_reason is CapitalSlotReleaseReason.OPPORTUNITY_COST
    assert not rel.authorizes_new_future_selection
    assert not rel.authorizes_new_trade
    assert not rel.live_authorization


def test_contract_15_live_authorization_false_all_layers_including_capital_slot() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-live",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok()
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )

    assert not t2.live_authorization_granted
    assert not surv.live_authorization
    assert not suit.projection.live_authorization
    assert not suit.live_authorization
    assert not comp.live_authorization
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert GOOD_ENVELOPE.live_authorization is False
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_contract_16_pure_stack_blocked_when_capital_slot_inactivity_released() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-inact",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))

    cfg = _cs_cfg_ok()
    cs_st = replace(
        _cs_state_ok(),
        realized_volatility=0.01,
        atr_or_range=0.01,
    )
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rel.released

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_release_decision=rel,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.CAPITAL_SLOT_RELEASED in comp.block_reasons


def test_contract_17_pure_stack_blocked_when_capital_slot_opportunity_released() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE

    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="cs-opp",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))

    cfg = _cs_cfg_ok()
    cs_st = replace(_cs_state_ok(), opportunity_score=0.05)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rel.released
    assert rel.release_reason is CapitalSlotReleaseReason.OPPORTUNITY_COST

    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_release_decision=rel,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.CAPITAL_SLOT_RELEASED in comp.block_reasons


def test_contract_18_futures_input_missing_metadata_blocks_scenario_eligibility() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-meta",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY

    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(instrument=_fi_instrument(complete=False, missing_fields=("tick_size",)))
    )
    assert fi.status is FuturesReadinessStatus.BLOCKED
    assert not fi.ready_for_downstream_model_use
    assert not _stack_eligible_with_futures_gate(fi, comp)


def test_contract_19_futures_input_stale_provenance_blocks_scenario_eligibility() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-stale",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(provenance=_fi_provenance(freshness_state=FuturesFreshnessState.STALE))
    )
    assert fi.status is FuturesReadinessStatus.BLOCKED
    assert not _stack_eligible_with_futures_gate(fi, comp)


def test_contract_20_futures_input_unknown_freshness_blocks_scenario_eligibility() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-fresh-unknown",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(provenance=_fi_provenance(freshness_state=FuturesFreshnessState.UNKNOWN))
    )
    assert fi.status is FuturesReadinessStatus.BLOCKED
    assert not _stack_eligible_with_futures_gate(fi, comp)


def test_contract_21_futures_input_missing_perp_funding_blocks_scenario_eligibility() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-fund",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(
            candidate=_fi_candidate(market_type=FuturesMarketType.PERPETUAL),
            derivatives=_fi_derivatives(funding_available=False, funding_rate=None),
        )
    )
    assert fi.status is FuturesReadinessStatus.BLOCKED
    assert not fi.ready_for_capital_slot
    assert not _stack_eligible_with_futures_gate(fi, comp)


def test_contract_22_futures_input_top_rank_alone_non_authority() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-rank",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(
            ranking=_fi_ranking(rank=1, is_top_n_member=True, score=0.99),
            instrument=_fi_instrument(complete=False, missing_fields=("contract_size",)),
            dashboard_label="Top-20 official selection",
        )
    )
    assert fi.status is FuturesReadinessStatus.BLOCKED
    assert not fi.is_authority
    assert not _stack_eligible_with_futures_gate(fi, comp)
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_contract_23_futures_input_live_authorization_false_full_stack_with_capital_slot() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="fi-live",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok()
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    fi = evaluate_futures_input_snapshot(
        _fi_snapshot(candidate=_fi_candidate(live_authorization=True)),
    )
    assert not t2.live_authorization_granted
    assert not surv.live_authorization
    assert not suit.projection.live_authorization
    assert not suit.live_authorization
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert not comp.live_authorization
    assert not fi.live_authorization
    assert fi.status is FuturesReadinessStatus.DATA_READY
    assert _stack_eligible_with_futures_gate(fi, comp)


def test_contract_24_dashboard_display_full_long_bull_with_capital_slot() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_long_bull_stack_with_capital()
    assert _stack_eligible_with_futures_gate(fi, comp)
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert len(snap.panels) == 7
    assert [p.name for p in snap.panels] == [
        "futures_input",
        "state_transition",
        "survival_envelope",
        "strategy_suitability",
        "capital_slot_ratchet",
        "capital_slot_release",
        "composition",
    ]
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_READY
    for p in snap.panels:
        assert p.status is DashboardDisplayStatus.DISPLAY_READY
    assert "ELIGIBLE_MODEL_ONLY" in snap.panels[-1].summary
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        rat=rat,
        rel=rel,
        comp=comp,
        snap=snap,
    )


def test_contract_25_dashboard_display_full_short_bear_with_capital_slot() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_short_bear_stack_with_capital()
    assert _stack_eligible_with_futures_gate(fi, comp)
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_READY
    for p in snap.panels:
        assert p.status is DashboardDisplayStatus.DISPLAY_READY
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        rat=rat,
        rel=rel,
        comp=comp,
        snap=snap,
    )


def test_contract_26_dashboard_display_blocked_futures_input_panel() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_long_bull_stack_with_capital()
    fi_blocked = evaluate_futures_input_snapshot(
        _fi_snapshot(instrument=_fi_instrument(complete=False, missing_fields=("tick_size",)))
    )
    assert fi_blocked.status is FuturesReadinessStatus.BLOCKED
    snap = build_dashboard_display_snapshot(
        futures_input=fi_blocked,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert snap.panels[0].name == "futures_input"
    assert snap.panels[0].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi_blocked,
        transition=t2,
        surv=surv,
        suit=suit,
        rat=rat,
        rel=rel,
        comp=comp,
        snap=snap,
    )


def test_contract_27_dashboard_display_blocked_survival_envelope() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    bad_fp = replace(_fp_ok(), contract_spec_complete=False)
    bad_env = replace(_env_ok(), fingerprint=bad_fp)
    surv = evaluate_survival_envelope(bad_env)
    meta = StrategyMetadata(
        strategy_id="dash-surv",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        composition=comp,
    )
    assert snap.panels[2].name == "survival_envelope"
    assert snap.panels[2].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.panels[3].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.panels[6].name == "composition"
    assert snap.panels[6].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        comp=comp,
        snap=snap,
    )


def test_contract_28_dashboard_display_blocked_suitability() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-suit",
        strategy_family="m",
        declared_side=SideCompatibility.UNKNOWN,
        explicit_side_evidence=False,
        registry_label="x",
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        composition=comp,
    )
    assert snap.panels[3].name == "strategy_suitability"
    assert snap.panels[3].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.panels[6].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        comp=comp,
        snap=snap,
    )


def test_contract_29_dashboard_display_blocked_capital_slot_ratchet() -> None:
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-cs-rat",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp_ok = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp_ok.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(realized=400.0, survival_allows_slot=False)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    assert not rat.can_ratchet
    assert CapitalSlotBlockReason.SURVIVAL_NOT_ALLOWED in rat.block_reasons
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.BLOCKED
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        composition=comp,
    )
    assert snap.panels[4].name == "capital_slot_ratchet"
    assert snap.panels[4].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.panels[6].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        rat=rat,
        comp=comp,
        snap=snap,
    )


def test_contract_30_dashboard_display_composition_kill_all() -> None:
    _s, _st, t_kill = _ts(SideState.LONG_ACTIVE, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 0)
    assert _s == SideState.KILL_ALL
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-kill",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t_kill,
            resulting_side_state=SideState.KILL_ALL,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    assert comp.status is DoublePlayCompositionStatus.KILL_ALL
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t_kill,
        survival=surv,
        suitability=suit,
        composition=comp,
    )
    assert snap.panels[6].name == "composition"
    assert snap.panels[6].status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert "kill_all" in snap.panels[6].summary.lower()
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t_kill,
        surv=surv,
        suit=suit,
        comp=comp,
        snap=snap,
    )


def test_contract_31_dashboard_display_missing_composition_is_display_warning() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_long_bull_stack_with_capital()
    assert comp.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=None,
    )
    assert snap.panels[-1].name == "composition"
    assert snap.panels[-1].status is DashboardDisplayStatus.DISPLAY_MISSING
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_WARNING
    assert "one_or_more_panels_missing_optional_pure_inputs" in snap.warnings
    _assert_dashboard_snapshot_invariants(snap)


def test_contract_32_producer_adapter_packet_full_stack_dashboard_long_bull_capital() -> None:
    """
    Adapter-produced futures input flows through the same pure stack + dashboard path as
    hand-built snapshots. Tests-only: no WebUI route or fixture provider changes.
    """
    packet = _prod_packet()
    adapter_dec = adapt_producer_packet_to_futures_input_snapshot(packet)
    assert adapter_dec.adapter_status is FuturesProducerAdapterStatus.OK
    assert adapter_dec.adapter_block_reasons == ()
    assert adapter_dec.snapshot is not None
    fi = adapter_dec.readiness
    assert fi is not None
    assert fi.status is FuturesReadinessStatus.DATA_READY
    assert fi.ready_for_downstream_model_use
    assert not fi.live_authorization

    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    assert s2 == SideState.LONG_ACTIVE
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="dash-adapter-long",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="ETH-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    assert _stack_eligible_with_futures_gate(fi, comp)
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert len(snap.panels) == 7
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_READY
    for p in snap.panels:
        assert p.status is DashboardDisplayStatus.DISPLAY_READY
    _assert_dashboard_snapshot_invariants(snap)
    _assert_no_live_authorization_pure_stack(
        fi=fi,
        transition=t2,
        surv=surv,
        suit=suit,
        rat=rat,
        rel=rel,
        comp=comp,
        snap=snap,
    )


def _forbidden_toplevels() -> frozenset[str]:
    return frozenset(
        {
            "strategies",
            "execution",
            "ccxt",
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "socket",
            "backtest",
            "shadow",
            "fastapi",
            "starlette",
        }
    )


def test_contract_8_test_file_imports_stay_in_allowed_surface() -> None:
    p = Path(__file__).resolve()
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = _forbidden_toplevels()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                top = n.name.split(".")[0]
                if top in bad:
                    raise AssertionError(f"unexpected import: {n.name}")
        if isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top in bad:
                raise AssertionError(f"unexpected from-import: {node.module}")


def test_contract_9_ast_no_bad_imports_in_pure_modules() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    files = (
        "double_play_state.py",
        "double_play_survival.py",
        "double_play_suitability.py",
        "double_play_composition.py",
        "double_play_capital_slot.py",
        "double_play_futures_input.py",
        "double_play_futures_input_producer.py",
        "double_play_dashboard_display.py",
    )
    bad = {"requests", "urllib3", "ccxt", "httpx", "socket", "aiohttp"}
    for name in files:
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    assert n.name.split(".")[0] not in bad
            if isinstance(node, ast.ImportFrom) and node.module:
                mod0 = node.module.split(".")[0]
                if mod0 in ("trading",):
                    continue
                assert mod0 not in bad
