# src/webui/double_play_dashboard_display_json_route_v0.py
"""
Master V2 Double Play — read-only dashboard display JSON route (v0).

GET-only snapshot from pure `build_dashboard_display_snapshot`, using a static in-memory
long/bull + capital-slot fixture (no scanner, exchange, session, or market-data).

See docs/ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Mapping

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotConfig,
    CapitalSlotState,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    RequestedSide,
    compose_double_play_decision,
)
from trading.master_v2.double_play_dashboard_display import (
    DashboardDisplayStatus,
    DoublePlayDashboardDisplaySnapshot,
    DoublePlayDashboardPanel,
    build_dashboard_display_snapshot,
)
from trading.master_v2.double_play_futures_input import (
    FuturesCandidateSnapshot,
    FuturesDerivativesProfile,
    FuturesFreshnessState,
    FuturesInputSnapshot,
    FuturesInstrumentMetadataStatus,
    FuturesLiquidityProfile,
    FuturesMarketDataProvenanceStatus,
    FuturesMarketType,
    FuturesOpportunityProfile,
    FuturesRankingSnapshot,
    FuturesVolatilityProfile,
    evaluate_futures_input_snapshot,
)
from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
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
    SuitabilityProjectionInput,
    project_strategy_suitability,
)

router = APIRouter(
    prefix="/api/master-v2/double-play",
    tags=["master-v2", "double-play", "dashboard-display-readonly"],
)

_DISPLAY_JSON_LAYER_VERSION = "v2"

_DISPLAY_PANEL_GROUP: Mapping[str, str] = {
    "futures_input": "input",
    "state_transition": "state",
    "survival_envelope": "scope",
    "strategy_suitability": "strategy",
    "capital_slot_ratchet": "capital",
    "capital_slot_release": "capital",
    "composition": "composition",
}

_DISPLAY_SEVERITY_RANK: Mapping[DashboardDisplayStatus, int] = {
    DashboardDisplayStatus.DISPLAY_READY: 0,
    DashboardDisplayStatus.DISPLAY_WARNING: 10,
    DashboardDisplayStatus.DISPLAY_MISSING: 20,
    DashboardDisplayStatus.DISPLAY_BLOCKED: 30,
    DashboardDisplayStatus.DISPLAY_ERROR: 40,
}


def _display_severity_rank(status: DashboardDisplayStatus) -> int:
    return _DISPLAY_SEVERITY_RANK[status]


def _assembled_at_iso_utc() -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


_GOOD_LIMITS = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
_GOOD_ENVELOPE = RuntimeEnvelope(static=_GOOD_LIMITS, live_authorization=False)
_GOOD_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
_EMPTY_ST = RuntimeScopeState()

_SURV_LIMITS = StateSwitchSurvivalLimits(
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


def _transition_step(
    side: SideState,
    event: ScopeEvent,
    st: RuntimeScopeState,
    now: int = 0,
):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=_GOOD_RULES,
        envelope=_GOOD_ENVELOPE,
        now_tick=now,
    )


def _layer_arith() -> LayerArithmeticStatus:
    return LayerArithmeticStatus(
        max_effective_leverage=10.0,
        min_liquidation_buffer=0.1,
        fee_breakeven_bps=2.0,
        expected_adverse_fill_loss=0.05,
        funding_cost_profile="flat",
        is_perpetual=True,
    )


def _fingerprint_ok() -> ArithmeticFingerprint:
    return ArithmeticFingerprint(
        contract_spec_complete=True,
        fee_model_complete=True,
        slippage_model_complete=True,
        funding_model_complete=True,
        margin_model_complete=True,
        liquidation_model_complete=True,
        rounding_model_complete=True,
    )


def _sequence_ok() -> SequenceSurvivalMetrics:
    return SequenceSurvivalMetrics(
        path_survival_ratio=0.8,
        early_loss_toxicity=0.2,
        margin_buffer_at_risk_99=0.2,
        sequence_fragility_index=0.2,
        liquidation_near_miss_rate=0.05,
        governance_breach_frequency=0.01,
        chop_switch_survival_score=0.7,
    )


def _survival_envelope_ok() -> DoublePlaySurvivalEnvelope:
    return DoublePlaySurvivalEnvelope(
        fingerprint=_fingerprint_ok(),
        long_layer=_layer_arith(),
        short_layer=_layer_arith(),
        sequence=_sequence_ok(),
        limits=_SURV_LIMITS,
    )


def _instrument_intel() -> InstrumentIntelligenceSummary:
    return InstrumentIntelligenceSummary(
        volatility_profile_present=True,
        liquidity_profile_present=True,
        spread_profile_present=True,
        funding_profile_present=True,
        freshness_profile_present=True,
    )


def _suitability_input(meta: StrategyMetadata, survival_allows: bool) -> SuitabilityProjectionInput:
    return SuitabilityProjectionInput(
        strategy=meta,
        instrument=_instrument_intel(),
        survival_envelope_allows=survival_allows,
    )


def _capital_config() -> CapitalSlotConfig:
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


def _capital_state() -> CapitalSlotState:
    return CapitalSlotState(
        selected_future="ETH-USD-PERP",
        initial_slot_base=300.0,
        active_slot_base=300.0,
        realized_or_settled_slot_equity=340.0,
        unrealized_pnl=0.0,
        locked_cashflow=0.0,
        time_without_cashflow_step=0,
        realized_volatility=0.5,
        atr_or_range=0.5,
        opportunity_score=0.8,
        survival_allows_slot=True,
    )


def _futures_input_snapshot() -> FuturesInputSnapshot:
    return FuturesInputSnapshot(
        candidate=FuturesCandidateSnapshot(
            candidate_id="webui-static-v0",
            instrument_id="inst-btc-perp",
            symbol="BTC-USDT-PERP",
            market_type=FuturesMarketType.PERPETUAL,
            exchange="example",
            base_currency="BTC",
            quote_currency="USDT",
            live_authorization=False,
        ),
        ranking=FuturesRankingSnapshot(
            source_universe_size=200,
            selected_top_n=20,
            rank=3,
            score=0.91,
            score_components_complete=True,
            is_top_n_member=True,
        ),
        instrument=FuturesInstrumentMetadataStatus(
            complete=True,
            contract_size_known=True,
            tick_size_known=True,
            step_size_known=True,
            min_qty_known=True,
            min_notional_known=True,
            margin_asset_known=True,
            settlement_asset_known=True,
            leverage_bounds_known=True,
            missing_fields=(),
        ),
        provenance=FuturesMarketDataProvenanceStatus(
            complete=True,
            freshness_state=FuturesFreshnessState.FRESH,
            dataset_id="ds-webui-static-v0",
            source="fixture",
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        volatility=FuturesVolatilityProfile(
            realized_volatility=0.42,
            atr_or_rolling_range=120.0,
            volatility_regime="medium",
            dynamic_scope_usable=True,
        ),
        liquidity=FuturesLiquidityProfile(
            spread_bps=1.5,
            average_spread_bps=1.8,
            volume=1_000_000.0,
            quote_volume=50_000_000.0,
            liquidity_regime="deep",
            spread_quality="tight",
        ),
        derivatives=FuturesDerivativesProfile(
            funding_available=True,
            funding_rate=0.0001,
            funding_regime="neutral",
            open_interest_available=True,
            open_interest=1e9,
            open_interest_regime="high",
        ),
        opportunity=FuturesOpportunityProfile(
            opportunity_score=0.75,
            inactivity_score=0.1,
            movement_above_fee_slippage_breakeven=True,
            chop_risk="low",
            candidate_is_inactive=False,
        ),
        dashboard_label=None,
        ai_summary=None,
    )


def _build_static_double_play_dashboard_display_snapshot_v0() -> DoublePlayDashboardDisplaySnapshot:
    """
    In-memory long/bull + capital-slot pure stack → display snapshot (representative, no I/O).
    """
    s1, st1, _ = _transition_step(
        SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, _EMPTY_ST, 0
    )
    s2, st2, t2 = _transition_step(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    if s2 != SideState.LONG_ACTIVE:
        raise RuntimeError("static fixture: expected LONG_ACTIVE")

    surv = evaluate_survival_envelope(_survival_envelope_ok())
    if surv.status is not SurvivalEnvelopeStatus.OK or not surv.pre_authorization_eligible:
        raise RuntimeError("static fixture: expected survival OK")

    meta = StrategyMetadata(
        strategy_id="webui-static-v0",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(
        _suitability_input(meta, survival_allows=True),
    )
    cfg = _capital_config()
    cs_st = _capital_state()
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
    fi = evaluate_futures_input_snapshot(_futures_input_snapshot())

    return build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )


def _jsonable_panel(panel: DoublePlayDashboardPanel, ordinal: int) -> Dict[str, Any]:
    st = panel.status
    status_val = st.value if isinstance(st, Enum) else str(st)
    panel_group = _DISPLAY_PANEL_GROUP.get(panel.name, "unknown")
    return {
        "name": panel.name,
        "status": status_val,
        "summary": panel.summary,
        "blockers": list(panel.blockers),
        "missing_inputs": list(panel.missing_inputs),
        "live_authorization": panel.live_authorization,
        "is_authority": panel.is_authority,
        "is_signal": panel.is_signal,
        "ordinal": ordinal,
        "panel_group": panel_group,
        "severity_rank": _display_severity_rank(st),
    }


def snapshot_to_jsonable(snap: DoublePlayDashboardDisplaySnapshot) -> Dict[str, Any]:
    """Convert display snapshot to JSON-serializable dict (enum values as strings)."""
    overall = snap.overall_status
    overall_val = overall.value if isinstance(overall, Enum) else str(overall)
    return {
        "display_layer_version": _DISPLAY_JSON_LAYER_VERSION,
        "display_snapshot_meta": {
            "source_kind": "static_display_v0",
            "source_id": "webui_dashboard_display_static_v0",
            "assembled_at_iso": _assembled_at_iso_utc(),
        },
        "panels": [_jsonable_panel(p, i) for i, p in enumerate(snap.panels)],
        "overall_status": overall_val,
        "no_live_banner_visible": snap.no_live_banner_visible,
        "display_only": snap.display_only,
        "trading_ready": snap.trading_ready,
        "testnet_ready": snap.testnet_ready,
        "live_ready": snap.live_ready,
        "live_authorization": snap.live_authorization,
        "warnings": list(snap.warnings),
    }


def build_static_dashboard_display_dict() -> Dict[str, Any]:
    """Same JSON-shaped dict as GET /dashboard-display.json (SSR helpers; no HTTP)."""
    snap = _build_static_double_play_dashboard_display_snapshot_v0()
    return snapshot_to_jsonable(snap)


@router.get("/dashboard-display.json")
async def get_double_play_dashboard_display_json() -> JSONResponse:
    """Read-only JSON snapshot: representative pure-stack display (fixture-backed)."""
    return JSONResponse(
        content=build_static_dashboard_display_dict(),
        headers={"Cache-Control": "no-store"},
    )
