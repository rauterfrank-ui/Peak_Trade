# src/trading/master_v2/offline_double_play_scenario_replay_v0.py
"""
Offline Master V2 Double Play scenario replay v0 — pure orchestrator only.

Deterministic multi-tick synthetic futures price stream → canonical pure-stack owners
→ decision/state digests → zero-order boundary. No I/O, network, orders, or live authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER,
    MasterV2DecisionStateDigestBinding,
    compute_master_v2_component_state_digest,
    compute_master_v2_decision_digest_from_snapshot,
)
from src.ops.durable_completion_validation.validators.event_stream import (
    MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
    MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
    MasterV2StateEventRecord,
    MasterV2StateEventStreamProofBinding,
    MasterV2StateEventStreamValidationInput,
    build_master_v2_state_event_record,
    default_minimal_master_v2_state_event_proof_binding,
    evaluate_master_v2_state_event_stream_validation,
)
from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
)
from trading.master_v2.double_play_capital_slot import (
    CapitalSlotConfig,
    CapitalSlotReleaseReason,
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
    DoublePlayDashboardDisplaySnapshot,
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
    FuturesReadinessStatus,
    FuturesVolatilityProfile,
    evaluate_futures_input_snapshot,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    derive_active_side,
    transition_state,
    update_dynamic_boundaries,
)
from trading.master_v2.double_play_suitability import (
    SideCompatibility,
    StrategyMetadata,
    SuitabilityProjectionInput,
    project_strategy_suitability,
)
from trading.master_v2.double_play_survival import (
    ArithmeticFingerprint,
    DoublePlaySurvivalEnvelope,
    LayerArithmeticStatus,
    SequenceSurvivalMetrics,
    StateSwitchSurvivalLimits,
    evaluate_survival_envelope,
)
from trading.master_v2.local_evaluator_v1 import evaluate_master_v2_local_flow_v1
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_LAYER_VERSION = "v0"
OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER = (
    "trading.master_v2.offline_double_play_scenario_replay_v0"
)
MASTER_V2_RUNTIME_ADAPTER_PROJECTION_OWNER = OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER
OFFLINE_REPLAY_STATE_EVENT_PROJECTION_LAYER_VERSION = "v0"
SYNTHETIC_FUTURES_INSTRUMENT = "ETH-PERP"

_BTC_SPOT_RE = re.compile(r"(?i)(btc|xbt|bitcoin|/usd|/eur|spot)")

_STATIC_LIMITS = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
_RUNTIME_ENVELOPE = RuntimeEnvelope(static=_STATIC_LIMITS, live_authorization=False)
_DEFAULT_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
_FLAP_RULES = replace(_DEFAULT_RULES, min_switch_cooldown_ticks=5)
_HIGH_VOL_RULES = replace(_DEFAULT_RULES, volatility_estimate=0.08)

_SURVIVAL_LIMITS = StateSwitchSurvivalLimits(
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


class OfflineDoublePlayProofEvent(str, Enum):
    BULL_HOLD = "bull_hold"
    BULL_TO_BEAR = "bull_to_bear"
    BEAR_HOLD = "bear_hold"
    BEAR_TO_BULL = "bear_to_bull"
    FLAPPING_BLOCKED = "flapping_blocked"
    VOLATILITY_SCOPE_ADAPTED = "volatility_scope_adapted"
    KILLSWITCH_BLOCKED = "killswitch_blocked"
    CAPITAL_SLOT_RATCHET_APPLIED = "capital_slot_ratchet_applied"
    INACTIVITY_SLOT_RELEASED = "inactivity_slot_released"


@dataclass(frozen=True)
class OfflineDoublePlayScenarioTickV0:
    tick_index: int
    timestamp_ms: int
    price: float
    scope_event: ScopeEvent
    volatility_estimate: float | None = None
    min_switch_cooldown_ticks: int | None = None
    safety_decision_allowed: bool = True
    realized_or_settled_slot_equity: float | None = None
    time_without_cashflow_step: int | None = None
    opportunity_score: float | None = None


@dataclass(frozen=True)
class OfflineDoublePlayScenarioReplayInputV0:
    selected_future_id: str
    ticks: tuple[OfflineDoublePlayScenarioTickV0, ...]
    correlation_id_prefix: str = "offline-double-play-replay-v0"
    source_revision: str = "offline-replay-v0"
    futures_input_snapshot: FuturesInputSnapshot | None = None


@dataclass(frozen=True)
class OfflineDoublePlayScenarioReplayTickRecordV0:
    tick_index: int
    timestamp_ms: int
    price: float
    selected_future_id: str
    scope_event: ScopeEvent
    side_state: SideState
    bull_layer_state: SideState
    bear_layer_state: SideState
    active_side: ActiveSide
    scope_state: RuntimeScopeState
    dynamic_scope_rules: DynamicScopeRules
    transition_allowed: bool
    transition_reason_code: str
    composition_status: str
    decision_id: str
    decision_snapshot: dict[str, Any] | None
    master_v2_decision_digest: str | None
    bull_layer_state_digest: str
    bear_layer_state_digest: str
    active_side_digest: str
    dynamic_scope_state_digest: str
    hysteresis_cooldown_state_digest: str
    killswitch_state_digest: str
    capital_slot_state_digest: str
    inactivity_exit_state_digest: str
    execution_intent_digest: str
    orders: int
    cancels: int
    fills: int
    positions_opened: int
    proof_events: tuple[OfflineDoublePlayProofEvent, ...]


@dataclass(frozen=True)
class OfflineDoublePlayScenarioReplaySummaryV0:
    tick_count: int
    proof_events: tuple[OfflineDoublePlayProofEvent, ...]
    replay_pass: bool
    fail_reasons: tuple[str, ...]
    orders_total: int
    cancels_total: int
    fills_total: int
    positions_opened_total: int
    final_side_state: SideState
    final_active_side: ActiveSide


@dataclass(frozen=True)
class OfflineDoublePlayScenarioReplayResultV0:
    layer_version: str
    replay_pass: bool
    selected_future_id: str
    tick_records: tuple[OfflineDoublePlayScenarioReplayTickRecordV0, ...]
    summary: OfflineDoublePlayScenarioReplaySummaryV0
    master_v2_decision_state_digest_binding: MasterV2DecisionStateDigestBinding | None
    fail_reasons: tuple[str, ...]
    dashboard_display_snapshot: DoublePlayDashboardDisplaySnapshot | None = None
    dashboard_display_projection_digest: str | None = None


def _layer() -> LayerArithmeticStatus:
    return LayerArithmeticStatus(
        max_effective_leverage=10.0,
        min_liquidation_buffer=0.1,
        fee_breakeven_bps=2.0,
        expected_adverse_fill_loss=0.05,
        funding_cost_profile="flat",
        is_perpetual=True,
    )


def _survival_envelope() -> DoublePlaySurvivalEnvelope:
    fp = ArithmeticFingerprint(
        contract_spec_complete=True,
        fee_model_complete=True,
        slippage_model_complete=True,
        funding_model_complete=True,
        margin_model_complete=True,
        liquidation_model_complete=True,
        rounding_model_complete=True,
    )
    seq = SequenceSurvivalMetrics(
        path_survival_ratio=0.8,
        early_loss_toxicity=0.2,
        margin_buffer_at_risk_99=0.2,
        sequence_fragility_index=0.2,
        liquidation_near_miss_rate=0.05,
        governance_breach_frequency=0.01,
        chop_switch_survival_score=0.7,
    )
    return DoublePlaySurvivalEnvelope(
        fingerprint=fp,
        long_layer=_layer(),
        short_layer=_layer(),
        sequence=seq,
        limits=_SURVIVAL_LIMITS,
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
        max_time_without_cashflow_step=20,
        min_opportunity_score=0.25,
    )


def _default_capital_state(
    *, future: str, base: float = 1000.0, realized: float = 1000.0
) -> CapitalSlotState:
    return CapitalSlotState(
        selected_future=future,
        initial_slot_base=base,
        active_slot_base=base,
        realized_or_settled_slot_equity=realized,
        unrealized_pnl=0.0,
        locked_cashflow=0.0,
        time_without_cashflow_step=0,
        realized_volatility=0.10,
        atr_or_range=0.10,
        opportunity_score=0.80,
        survival_allows_slot=True,
    )


def _bull_layer_state(side: SideState) -> SideState:
    if side in (
        SideState.LONG_ACTIVE,
        SideState.LONG_ARMED,
        SideState.LONG_BLOCKED,
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
    ):
        return side
    if side in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return SideState.LONG_BLOCKED
    return SideState.NEUTRAL_OBSERVE


def _bear_layer_state(side: SideState) -> SideState:
    if side in (
        SideState.SHORT_ACTIVE,
        SideState.SHORT_ARMED,
        SideState.SHORT_BLOCKED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    ):
        return side
    if side in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return SideState.SHORT_BLOCKED
    return SideState.NEUTRAL_OBSERVE


def _requested_side(side: SideState) -> RequestedSide:
    if side in (SideState.LONG_ACTIVE, SideState.LONG_ARMED):
        return RequestedSide.LONG_BULL
    if side in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED):
        return RequestedSide.SHORT_BEAR
    return RequestedSide.NEUTRAL_OBSERVE


def _suitability_input() -> SuitabilityProjectionInput:
    meta = StrategyMetadata(
        strategy_id="offline-replay-v0",
        strategy_family="double_play",
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    from trading.master_v2.double_play_suitability import InstrumentIntelligenceSummary

    inst = InstrumentIntelligenceSummary(
        volatility_profile_present=True,
        liquidity_profile_present=True,
        spread_profile_present=True,
        funding_profile_present=True,
        freshness_profile_present=True,
    )
    return SuitabilityProjectionInput(
        strategy=meta,
        instrument=inst,
        survival_envelope_allows=True,
    )


def _component_digest(component: str, **state: object) -> str:
    return compute_master_v2_component_state_digest(component=component, state=state)


def _dashboard_display_projection_digest(
    snap: DoublePlayDashboardDisplaySnapshot,
) -> str:
    return _component_digest(
        "dashboard_display_projection",
        overall_status=snap.overall_status.value,
        panel_statuses=tuple((p.name, p.status.value) for p in snap.panels),
        display_only=snap.display_only,
        live_authorization=snap.live_authorization,
    )


def _validate_instrument(selected_future_id: str) -> list[str]:
    reasons: list[str] = []
    if not selected_future_id or not selected_future_id.strip():
        reasons.append("selected_future_id required")
        return reasons
    if _BTC_SPOT_RE.search(selected_future_id):
        reasons.append("btc/xbt/spot instrument forbidden")
    if not selected_future_id.upper().endswith("-PERP"):
        reasons.append("futures-only instrument required")
    return reasons


def build_offline_replay_futures_input_snapshot(
    selected_future_id: str,
) -> FuturesInputSnapshot:
    """Deterministic admission-ready snapshot for offline replay (no I/O)."""
    base_currency = (
        selected_future_id.split("-", maxsplit=1)[0]
        if "-" in selected_future_id
        else selected_future_id
    )
    return FuturesInputSnapshot(
        candidate=FuturesCandidateSnapshot(
            candidate_id=f"offline-replay-{selected_future_id.lower()}",
            instrument_id=f"inst-{selected_future_id.lower()}",
            symbol=selected_future_id,
            market_type=FuturesMarketType.PERPETUAL,
            exchange="offline-replay",
            base_currency=base_currency,
            quote_currency="USD",
            live_authorization=False,
        ),
        ranking=FuturesRankingSnapshot(
            source_universe_size=1,
            selected_top_n=1,
            rank=1,
            score=1.0,
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
            dataset_id="offline-replay-v0",
            source="offline-replay",
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        volatility=FuturesVolatilityProfile(
            realized_volatility=0.02,
            atr_or_rolling_range=50.0,
            volatility_regime="medium",
            dynamic_scope_usable=True,
        ),
        liquidity=FuturesLiquidityProfile(
            spread_bps=1.0,
            average_spread_bps=1.2,
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
    )


def resolve_replay_futures_input_snapshot(
    inp: OfflineDoublePlayScenarioReplayInputV0,
) -> FuturesInputSnapshot:
    if inp.futures_input_snapshot is not None:
        return inp.futures_input_snapshot
    return build_offline_replay_futures_input_snapshot(inp.selected_future_id)


def futures_input_admission_fail_reasons(
    snapshot: FuturesInputSnapshot,
) -> list[str]:
    decision = evaluate_futures_input_snapshot(snapshot)
    if decision.status is FuturesReadinessStatus.DATA_READY:
        return []
    blocks = ",".join(reason.value for reason in decision.block_reasons)
    return [f"futures_input_admission_blocked:{blocks or 'blocked'}"]


def validate_offline_double_play_scenario_replay_input_v0(
    inp: OfflineDoublePlayScenarioReplayInputV0,
) -> list[str]:
    reasons = _validate_instrument(inp.selected_future_id)
    if reasons:
        return reasons
    admission_reasons = futures_input_admission_fail_reasons(
        resolve_replay_futures_input_snapshot(inp)
    )
    if admission_reasons:
        return admission_reasons
    if not inp.ticks:
        return ["ticks required"]
    prev_ts: int | None = None
    seen: set[int] = set()
    for tick in inp.ticks:
        if tick.tick_index in seen:
            reasons.append(f"duplicate tick_index {tick.tick_index}")
        seen.add(tick.tick_index)
        if not math.isfinite(tick.price) or tick.price <= 0:
            reasons.append(f"invalid price at tick {tick.tick_index}")
        if prev_ts is not None and tick.timestamp_ms <= prev_ts:
            reasons.append(f"non-monotone timestamp at tick {tick.tick_index}")
        prev_ts = tick.timestamp_ms
    return reasons


def build_default_bull_bear_bull_scenario_ticks() -> tuple[OfflineDoublePlayScenarioTickV0, ...]:
    """Deterministic ETH-PERP Bull→Bear→Bull replay with safety/scope sub-sequences."""
    ticks: list[OfflineDoublePlayScenarioTickV0] = []
    ts = 1_700_000_000_000
    idx = 0

    def add(
        price: float,
        event: ScopeEvent,
        *,
        vol: float | None = None,
        cooldown: int | None = None,
        safety: bool = True,
        realized: float | None = None,
        inactive_steps: int | None = None,
        opp: float | None = None,
    ) -> None:
        nonlocal idx, ts
        ticks.append(
            OfflineDoublePlayScenarioTickV0(
                tick_index=idx,
                timestamp_ms=ts,
                price=price,
                scope_event=event,
                volatility_estimate=vol,
                min_switch_cooldown_ticks=cooldown,
                safety_decision_allowed=safety,
                realized_or_settled_slot_equity=realized,
                time_without_cashflow_step=inactive_steps,
                opportunity_score=opp,
            )
        )
        idx += 1
        ts += 60_000

    # Phase 1 — positive trend → LONG_ACTIVE (bull hold)
    add(100.0, ScopeEvent.UPSCOPE_CONFIRMED)
    add(101.5, ScopeEvent.UPSCOPE_CONFIRMED)
    add(103.0, ScopeEvent.NOOP)
    add(104.5, ScopeEvent.NOOP)
    add(106.0, ScopeEvent.NOOP)

    # Phase 2 — confirmed negative shift → SHORT_ACTIVE
    add(104.0, ScopeEvent.DOWNSCOPE_CONFIRMED)
    add(102.5, ScopeEvent.DOWNSCOPE_CONFIRMED)
    add(101.0, ScopeEvent.DOWNSCOPE_CONFIRMED)
    add(99.5, ScopeEvent.DOWNSCOPE_CONFIRMED)

    # Phase 3 — bear hold in negative trend
    add(98.0, ScopeEvent.NOOP)
    add(96.5, ScopeEvent.NOOP)
    add(95.0, ScopeEvent.NOOP)

    # Phase 4 — flapping attempt within cooldown (candidates + blocked confirmed switch)
    add(95.5, ScopeEvent.UPSCOPE_CANDIDATE, cooldown=5)
    add(96.0, ScopeEvent.DOWNSCOPE_CANDIDATE, cooldown=5)
    add(96.5, ScopeEvent.UPSCOPE_CONFIRMED, cooldown=5)

    # Phase 5 — volatility scope adaptation (reset cooldown)
    add(93.0, ScopeEvent.NOOP, vol=0.08, cooldown=0)

    # Phase 6 — confirmed positive shift → LONG_ACTIVE
    add(95.0, ScopeEvent.UPSCOPE_CONFIRMED, cooldown=0)
    add(97.0, ScopeEvent.UPSCOPE_CONFIRMED, cooldown=0)
    add(99.0, ScopeEvent.UPSCOPE_CONFIRMED, cooldown=0)
    add(101.0, ScopeEvent.UPSCOPE_CONFIRMED, cooldown=0)

    # Phase 7 — capital slot ratchet step then loss-following base reduction (no reserve top-up)
    add(100.0, ScopeEvent.NOOP, realized=1200.0, cooldown=0)
    add(99.0, ScopeEvent.NOOP, realized=850.0, cooldown=0)

    # Phase 8 — inactivity / opportunity-cost slot release
    add(100.0, ScopeEvent.NOOP, inactive_steps=25, opp=0.10)

    # Phase 9 — killswitch fail-closed block
    add(100.0, ScopeEvent.KILL_ALL_REQUIRED, safety=False)

    return tuple(ticks)


def _rules_for_tick(
    tick: OfflineDoublePlayScenarioTickV0, prior: DynamicScopeRules
) -> DynamicScopeRules:
    rules = prior
    if tick.volatility_estimate is not None:
        rules = replace(rules, volatility_estimate=tick.volatility_estimate)
    if tick.min_switch_cooldown_ticks is not None:
        rules = replace(rules, min_switch_cooldown_ticks=tick.min_switch_cooldown_ticks)
    return rules


def _detect_proof_events(
    *,
    prior_side: SideState,
    side: SideState,
    tick: OfflineDoublePlayScenarioTickV0,
    transition_reason: str,
    prior_band: float,
    scope_state: RuntimeScopeState,
    rules: DynamicScopeRules,
    prior_volatility_estimate: float,
    ratchet_applied: bool,
    slot_released: bool,
    killswitch_blocked: bool,
) -> tuple[OfflineDoublePlayProofEvent, ...]:
    events: list[OfflineDoublePlayProofEvent] = []
    if side == SideState.LONG_ACTIVE and tick.scope_event == ScopeEvent.NOOP:
        events.append(OfflineDoublePlayProofEvent.BULL_HOLD)
    if side == SideState.SHORT_ACTIVE and tick.scope_event == ScopeEvent.NOOP:
        events.append(OfflineDoublePlayProofEvent.BEAR_HOLD)
    if prior_side == SideState.LONG_ACTIVE and side == SideState.SWITCH_LONG_TO_SHORT_PENDING:
        events.append(OfflineDoublePlayProofEvent.BULL_TO_BEAR)
    if prior_side == SideState.SHORT_ACTIVE and side == SideState.SWITCH_SHORT_TO_LONG_PENDING:
        events.append(OfflineDoublePlayProofEvent.BEAR_TO_BULL)
    if tick.scope_event in (ScopeEvent.DOWNSCOPE_CANDIDATE, ScopeEvent.UPSCOPE_CANDIDATE):
        events.append(OfflineDoublePlayProofEvent.FLAPPING_BLOCKED)
    if transition_reason == "COOLDOWN_BLOCK":
        events.append(OfflineDoublePlayProofEvent.FLAPPING_BLOCKED)
    if (
        tick.volatility_estimate is not None
        and rules.volatility_estimate != prior_volatility_estimate
    ):
        events.append(OfflineDoublePlayProofEvent.VOLATILITY_SCOPE_ADAPTED)
    if killswitch_blocked or side == SideState.KILL_ALL:
        events.append(OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED)
    if ratchet_applied:
        events.append(OfflineDoublePlayProofEvent.CAPITAL_SLOT_RATCHET_APPLIED)
    if slot_released:
        events.append(OfflineDoublePlayProofEvent.INACTIVITY_SLOT_RELEASED)
    return tuple(events)


def run_offline_double_play_scenario_replay_v0(
    inp: OfflineDoublePlayScenarioReplayInputV0,
) -> OfflineDoublePlayScenarioReplayResultV0:
    validation = validate_offline_double_play_scenario_replay_input_v0(inp)
    if validation:
        summary = OfflineDoublePlayScenarioReplaySummaryV0(
            tick_count=0,
            proof_events=(),
            replay_pass=False,
            fail_reasons=tuple(validation),
            orders_total=0,
            cancels_total=0,
            fills_total=0,
            positions_opened_total=0,
            final_side_state=SideState.NEUTRAL_OBSERVE,
            final_active_side=ActiveSide.NEUTRAL,
        )
        return OfflineDoublePlayScenarioReplayResultV0(
            layer_version=OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_LAYER_VERSION,
            replay_pass=False,
            selected_future_id=inp.selected_future_id,
            tick_records=(),
            summary=summary,
            master_v2_decision_state_digest_binding=None,
            fail_reasons=tuple(validation),
            dashboard_display_snapshot=None,
            dashboard_display_projection_digest=None,
        )

    futures_input_decision = evaluate_futures_input_snapshot(
        resolve_replay_futures_input_snapshot(inp)
    )
    side = SideState.NEUTRAL_OBSERVE
    scope_state = RuntimeScopeState(anchor_price=0.0)
    rules = _DEFAULT_RULES
    capital_state = _default_capital_state(future=inp.selected_future_id)
    survival = evaluate_survival_envelope(_survival_envelope())
    suitability = project_strategy_suitability(_suitability_input())
    records: list[OfflineDoublePlayScenarioReplayTickRecordV0] = []
    all_proof: list[OfflineDoublePlayProofEvent] = []
    fail_reasons: list[str] = []
    prior_volatility_estimate = rules.volatility_estimate
    final_dashboard_display_snapshot: DoublePlayDashboardDisplaySnapshot | None = None

    sorted_ticks = tuple(sorted(inp.ticks, key=lambda t: t.tick_index))

    for tick in sorted_ticks:
        prior_side = side
        prior_band = scope_state.current_hysteresis_band
        rules = _rules_for_tick(tick, rules)
        active = derive_active_side(side)
        scope_state = update_dynamic_boundaries(
            mark_price=tick.price,
            side=active,
            st=scope_state,
            rules=rules,
            env=_RUNTIME_ENVELOPE,
        )

        event = tick.scope_event
        if not tick.safety_decision_allowed and event != ScopeEvent.KILL_ALL_REQUIRED:
            event = ScopeEvent.NOOP

        side_after, scope_after, transition = transition_state(
            side_state=side,
            event=event,
            scope_state=scope_state,
            rules=rules,
            envelope=_RUNTIME_ENVELOPE,
            now_tick=tick.tick_index,
        )
        side = side_after
        scope_state = scope_after
        active = derive_active_side(side)
        scope_state = update_dynamic_boundaries(
            mark_price=tick.price,
            side=active,
            st=scope_state,
            rules=rules,
            env=_RUNTIME_ENVELOPE,
        )

        if tick.realized_or_settled_slot_equity is not None:
            capital_state = replace(
                capital_state,
                realized_or_settled_slot_equity=tick.realized_or_settled_slot_equity,
                active_slot_base=min(
                    capital_state.active_slot_base, tick.realized_or_settled_slot_equity
                ),
            )
        if tick.time_without_cashflow_step is not None:
            capital_state = replace(
                capital_state,
                time_without_cashflow_step=tick.time_without_cashflow_step,
            )
        if tick.opportunity_score is not None:
            capital_state = replace(capital_state, opportunity_score=tick.opportunity_score)

        ratchet = evaluate_capital_slot_ratchet(_capital_config(), capital_state)
        if ratchet.can_ratchet and ratchet.new_active_slot_base is not None:
            capital_state = replace(capital_state, active_slot_base=ratchet.new_active_slot_base)
        release = evaluate_capital_slot_release(_capital_config(), capital_state)

        composition = compose_double_play_decision(
            DoublePlayCompositionInput(
                transition=transition,
                resulting_side_state=side,
                survival=survival,
                suitability=suitability,
                requested_side=_requested_side(side),
                capital_slot_ratchet_decision=ratchet,
                capital_slot_release_decision=release,
            )
        )

        final_dashboard_display_snapshot = build_dashboard_display_snapshot(
            futures_input=futures_input_decision,
            transition=transition,
            survival=survival,
            suitability=suitability,
            capital_slot_ratchet=ratchet,
            capital_slot_release=release,
            composition=composition,
        )

        safety_allowed = tick.safety_decision_allowed and side != SideState.KILL_ALL
        staged = StagedExecutionEnablementInputV1(
            current_stage=ExecutionStageV1.RESEARCH,
            requested_stage=ExecutionStageV1.BACKTEST,
            safety_decision_allowed=safety_allowed,
        )
        decision_id = f"{inp.correlation_id_prefix}-tick-{tick.tick_index}"
        flow = evaluate_master_v2_local_flow_v1(
            decision_id,
            staged,
            universe=UniverseSelectionHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                symbols=(inp.selected_future_id,),
            ),
            doubleplay=DoubleplayResolutionHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                resolution=composition.status.value,
            ),
            scope_envelope=ScopeCapitalEnvelopeHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                within_envelope=True,
            ),
            risk_cap=RiskExposureCapHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                cap_satisfied=True,
            ),
            safety=SafetyKillSwitchHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                safety_decision_allowed=safety_allowed,
            ),
            with_snapshot=True,
        )

        snapshot = flow.snapshot
        decision_digest = (
            compute_master_v2_decision_digest_from_snapshot(snapshot)
            if snapshot is not None
            else None
        )
        bull_state = _bull_layer_state(side)
        bear_state = _bear_layer_state(side)
        active_side = derive_active_side(side)
        release_reason = (
            release.release_reason.value if release.release_reason is not None else "none"
        )

        tick_proof = _detect_proof_events(
            prior_side=prior_side,
            side=side,
            tick=tick,
            transition_reason=transition.reason_code,
            prior_band=prior_band,
            scope_state=scope_state,
            rules=rules,
            prior_volatility_estimate=prior_volatility_estimate,
            ratchet_applied=(
                ratchet.can_ratchet
                or (
                    tick.realized_or_settled_slot_equity is not None
                    and tick.realized_or_settled_slot_equity < capital_state.initial_slot_base
                )
            ),
            slot_released=release.released,
            killswitch_blocked=not tick.safety_decision_allowed or side == SideState.KILL_ALL,
        )
        all_proof.extend(tick_proof)

        record = OfflineDoublePlayScenarioReplayTickRecordV0(
            tick_index=tick.tick_index,
            timestamp_ms=tick.timestamp_ms,
            price=tick.price,
            selected_future_id=inp.selected_future_id,
            scope_event=event,
            side_state=side,
            bull_layer_state=bull_state,
            bear_layer_state=bear_state,
            active_side=active_side,
            scope_state=scope_state,
            dynamic_scope_rules=rules,
            transition_allowed=transition.allowed,
            transition_reason_code=transition.reason_code,
            composition_status=composition.status.value,
            decision_id=decision_id,
            decision_snapshot=snapshot,
            master_v2_decision_digest=decision_digest,
            bull_layer_state_digest=_component_digest(
                "bull_layer_state", side_state=bull_state.value
            ),
            bear_layer_state_digest=_component_digest(
                "bear_layer_state", side_state=bear_state.value
            ),
            active_side_digest=_component_digest("active_side", active_side=active_side.value),
            dynamic_scope_state_digest=_component_digest(
                "dynamic_scope_state",
                anchor_price=scope_state.anchor_price,
                upscope_boundary=scope_state.current_upscope_boundary,
                downscope_boundary=scope_state.current_downscope_boundary,
                hysteresis_band=scope_state.current_hysteresis_band,
            ),
            hysteresis_cooldown_state_digest=_component_digest(
                "hysteresis_cooldown_state",
                last_switch_tick=scope_state.last_switch_tick,
                last_completed_side_switch_tick=scope_state.last_completed_side_switch_tick,
                min_switch_cooldown_ticks=rules.min_switch_cooldown_ticks,
            ),
            killswitch_state_digest=_component_digest(
                "killswitch_state", safety_decision_allowed=safety_allowed
            ),
            capital_slot_state_digest=_component_digest(
                "capital_slot_state",
                active_slot_base=capital_state.active_slot_base,
                allow_auto_top_up=False,
            ),
            inactivity_exit_state_digest=_component_digest(
                "inactivity_exit_state", release_reason=release_reason
            ),
            execution_intent_digest=_component_digest(
                "execution_intent", zero_order=True, orders_allowed=False
            ),
            orders=0,
            cancels=0,
            fills=0,
            positions_opened=0,
            proof_events=tick_proof,
        )
        records.append(record)
        prior_volatility_estimate = rules.volatility_estimate

    display_digest = (
        _dashboard_display_projection_digest(final_dashboard_display_snapshot)
        if final_dashboard_display_snapshot is not None
        else None
    )
    if records and display_digest is None:
        fail_reasons.append("dashboard_display_projection_digest missing")

    binding = build_master_v2_decision_state_digest_binding_from_replay(
        records=tuple(records),
        selected_future_id=inp.selected_future_id,
        source_revision=inp.source_revision,
        dashboard_display_projection_digest=display_digest,
    )

    required_events = {
        OfflineDoublePlayProofEvent.BULL_HOLD,
        OfflineDoublePlayProofEvent.BULL_TO_BEAR,
        OfflineDoublePlayProofEvent.BEAR_HOLD,
        OfflineDoublePlayProofEvent.BEAR_TO_BULL,
        OfflineDoublePlayProofEvent.FLAPPING_BLOCKED,
        OfflineDoublePlayProofEvent.VOLATILITY_SCOPE_ADAPTED,
        OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED,
        OfflineDoublePlayProofEvent.CAPITAL_SLOT_RATCHET_APPLIED,
        OfflineDoublePlayProofEvent.INACTIVITY_SLOT_RELEASED,
    }
    observed = set(all_proof)
    missing = sorted(required_events - observed, key=lambda e: e.value)
    if missing:
        fail_reasons.append(f"missing proof events: {', '.join(m.value for m in missing)}")
    if binding is None:
        fail_reasons.append("master_v2_decision_state_digest_binding missing")
    for rec in records:
        if rec.orders or rec.cancels or rec.fills or rec.positions_opened:
            fail_reasons.append(f"zero-order violated at tick {rec.tick_index}")
        if rec.decision_snapshot is None:
            fail_reasons.append(f"decision snapshot missing at tick {rec.tick_index}")

    final_side = records[-1].side_state if records else SideState.NEUTRAL_OBSERVE
    summary = OfflineDoublePlayScenarioReplaySummaryV0(
        tick_count=len(records),
        proof_events=tuple(dict.fromkeys(all_proof)),
        replay_pass=not fail_reasons,
        fail_reasons=tuple(fail_reasons),
        orders_total=0,
        cancels_total=0,
        fills_total=0,
        positions_opened_total=0,
        final_side_state=final_side,
        final_active_side=derive_active_side(final_side),
    )
    return OfflineDoublePlayScenarioReplayResultV0(
        layer_version=OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_LAYER_VERSION,
        replay_pass=summary.replay_pass,
        selected_future_id=inp.selected_future_id,
        tick_records=tuple(records),
        summary=summary,
        master_v2_decision_state_digest_binding=binding,
        fail_reasons=tuple(fail_reasons),
        dashboard_display_snapshot=final_dashboard_display_snapshot,
        dashboard_display_projection_digest=display_digest,
    )


def build_master_v2_decision_state_digest_binding_from_replay(
    *,
    records: tuple[OfflineDoublePlayScenarioReplayTickRecordV0, ...],
    selected_future_id: str,
    source_revision: str,
    dashboard_display_projection_digest: str | None = None,
) -> MasterV2DecisionStateDigestBinding | None:
    if not records:
        return None
    final = records[-1]
    if final.decision_snapshot is None or final.master_v2_decision_digest is None:
        return None
    if not dashboard_display_projection_digest:
        return None
    return MasterV2DecisionStateDigestBinding(
        binding_owner=MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER,
        source_revision=source_revision,
        master_v2_decision_id=final.decision_id,
        master_v2_decision_digest=final.master_v2_decision_digest,
        selected_future_id=selected_future_id,
        bull_layer_state_digest=final.bull_layer_state_digest,
        bear_layer_state_digest=final.bear_layer_state_digest,
        active_side_digest=final.active_side_digest,
        dynamic_scope_state_digest=final.dynamic_scope_state_digest,
        hysteresis_cooldown_state_digest=final.hysteresis_cooldown_state_digest,
        killswitch_state_digest=final.killswitch_state_digest,
        capital_slot_state_digest=final.capital_slot_state_digest,
        inactivity_exit_state_digest=final.inactivity_exit_state_digest,
        execution_intent_digest=final.execution_intent_digest,
        dashboard_display_projection_digest=dashboard_display_projection_digest,
    )


def replay_result_digest_coherent(result: OfflineDoublePlayScenarioReplayResultV0) -> bool:
    binding = result.master_v2_decision_state_digest_binding
    if binding is None or not result.tick_records:
        return False
    final = result.tick_records[-1]
    pairs: tuple[tuple[str, str], ...] = (
        ("master_v2_decision_id", final.decision_id),
        ("master_v2_decision_digest", final.master_v2_decision_digest or ""),
        ("selected_future_id", result.selected_future_id),
        ("bull_layer_state_digest", final.bull_layer_state_digest),
        ("bear_layer_state_digest", final.bear_layer_state_digest),
        ("active_side_digest", final.active_side_digest),
        ("dynamic_scope_state_digest", final.dynamic_scope_state_digest),
        ("hysteresis_cooldown_state_digest", final.hysteresis_cooldown_state_digest),
        ("killswitch_state_digest", final.killswitch_state_digest),
        ("capital_slot_state_digest", final.capital_slot_state_digest),
        ("inactivity_exit_state_digest", final.inactivity_exit_state_digest),
        ("execution_intent_digest", final.execution_intent_digest),
        (
            "dashboard_display_projection_digest",
            result.dashboard_display_projection_digest or "",
        ),
    )
    for field, expected in pairs:
        if getattr(binding, field) != expected:
            return False
    return True


@dataclass(frozen=True)
class MasterV2ReplayStateEventProjectionResultV0:
    """Offline projection of pure-stack replay ticks into Master-V2 state event records."""

    layer_version: str
    projection_pass: bool
    evidence_chain_profile: str | None
    events: tuple[MasterV2StateEventRecord, ...]
    validation_input: MasterV2StateEventStreamValidationInput | None
    validation_result: dict[str, Any] | None
    proof_binding: MasterV2StateEventStreamProofBinding | None
    projection_digest: str | None
    fail_reasons: tuple[str, ...]


def _replay_timestamp_ms_to_utc(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _canonical_offline_transition_for_projection(
    *,
    side_before: SideState,
    scope_event: ScopeEvent,
    now_tick: int,
) -> tuple[SideState, bool]:
    """Mirror event-stream validator semantics: default offline scope, no accumulation."""
    scope_state = RuntimeScopeState(
        anchor_price=100.0,
        chop_latched=False,
        current_downscope_boundary=95.0,
        current_hysteresis_band=2.0,
        current_upscope_boundary=105.0,
        last_completed_side_switch_tick=-1_000_000,
        last_switch_tick=-1_000_000,
        now_tick=0,
        scope_stability_ticks=0,
        switches_in_window=0,
        window_start_tick=0,
    )
    rules = DynamicScopeRules(
        downscope_band_multiplier=1.0,
        upscope_band_multiplier=1.0,
        min_band_width=0.5,
        max_band_width=100.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=10,
    )
    envelope = RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False)
    side_after, _, decision = transition_state(
        side_state=side_before,
        event=scope_event,
        scope_state=scope_state,
        rules=rules,
        envelope=envelope,
        now_tick=now_tick,
    )
    return side_after, decision.allowed


def _semantic_event_class_for_replay_transition(
    *,
    scope_event: ScopeEvent,
    side_before: SideState,
    side_after: SideState,
) -> str | None:
    if scope_event == ScopeEvent.KILL_ALL_REQUIRED:
        return "kill_all_terminal"
    if scope_event == ScopeEvent.CHOP_DETECTED:
        return "chop_guard"
    if side_before == side_after and scope_event in (
        ScopeEvent.NOOP,
        ScopeEvent.UPSCOPE_CANDIDATE,
        ScopeEvent.DOWNSCOPE_CANDIDATE,
        ScopeEvent.UPSCOPE_CONFIRMED,
        ScopeEvent.DOWNSCOPE_CONFIRMED,
    ):
        return "dynamic_scope"
    if side_after in (
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    ):
        return "state_switch"
    return None


def _profile_allows_semantic_class(*, profile: str, semantic_class: str) -> bool:
    if profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL:
        return semantic_class == "kill_all_terminal"
    if profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH:
        return semantic_class != "kill_all_terminal"
    return False


def _infer_evidence_chain_profile_from_replay(
    records: tuple[OfflineDoublePlayScenarioReplayTickRecordV0, ...],
) -> str | None:
    if not records:
        return None
    if records[-1].side_state == SideState.KILL_ALL:
        return MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL
    return MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH


def compute_master_v2_replay_state_event_projection_digest(
    *,
    events: tuple[MasterV2StateEventRecord, ...],
    evidence_chain_profile: str,
    correlation_id: str,
) -> str:
    payload = {
        "correlation_id": correlation_id,
        "evidence_chain_profile": evidence_chain_profile,
        "events": [
            {
                "event_id": record.event_id,
                "scope_event": record.scope_event,
                "semantic_event_class": record.semantic_event_class,
                "sequence": record.sequence,
                "side_state_after": record.side_state_after,
                "side_state_before": record.side_state_before,
            }
            for record in events
        ],
        "hash_algorithm": "sha256",
        "layer_version": OFFLINE_REPLAY_STATE_EVENT_PROJECTION_LAYER_VERSION,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def project_master_v2_state_events_from_replay_records(
    *,
    records: tuple[OfflineDoublePlayScenarioReplayTickRecordV0, ...],
    correlation_id: str,
    bound_scope_state_digest: str,
    evidence_chain_profile: str,
) -> tuple[tuple[MasterV2StateEventRecord, ...], tuple[str, ...]]:
    """Project replay tick records into canonical Master-V2 state event records (read-only)."""
    fail_reasons: list[str] = []
    if not correlation_id.strip():
        fail_reasons.append("correlation_id required")
    if not bound_scope_state_digest or len(bound_scope_state_digest) != 64:
        fail_reasons.append("bound_scope_state_digest required")
    if evidence_chain_profile not in (
        MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
        MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    ):
        fail_reasons.append("unsupported evidence_chain_profile")
    if not records:
        fail_reasons.append("records required")
    if fail_reasons:
        return (), tuple(fail_reasons)

    projected: list[MasterV2StateEventRecord] = []
    seen_transition_keys: set[tuple[str, str]] = set()
    prior_side = SideState.NEUTRAL_OBSERVE

    for record in records:
        scope_event = record.scope_event
        side_after = record.side_state
        side_before = prior_side
        canonical_after, canonical_allowed = _canonical_offline_transition_for_projection(
            side_before=side_before,
            scope_event=scope_event,
            now_tick=record.tick_index,
        )
        if side_after != canonical_after or record.transition_allowed != canonical_allowed:
            prior_side = side_after
            continue

        semantic_class = _semantic_event_class_for_replay_transition(
            scope_event=scope_event,
            side_before=side_before,
            side_after=side_after,
        )
        if semantic_class is None or not _profile_allows_semantic_class(
            profile=evidence_chain_profile,
            semantic_class=semantic_class,
        ):
            prior_side = side_after
            continue

        transition_key = (scope_event.value, side_before.value)
        if transition_key in seen_transition_keys:
            prior_side = side_after
            continue
        seen_transition_keys.add(transition_key)

        projected.append(
            build_master_v2_state_event_record(
                semantic_event_class=semantic_class,
                event_id=(
                    f"mv2-replay-proj-{correlation_id}-{semantic_class}-{len(projected):04d}"
                ),
                sequence=len(projected),
                correlation_id=correlation_id,
                scope_event=scope_event.value,
                side_state_before=side_before.value,
                side_state_after=side_after.value,
                scope_state_digest=bound_scope_state_digest,
                transition_allowed=record.transition_allowed,
                timestamp_utc=_replay_timestamp_ms_to_utc(record.timestamp_ms),
            )
        )
        prior_side = side_after

    present_classes = {record.semantic_event_class for record in projected}
    if evidence_chain_profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH:
        for required in ("dynamic_scope", "state_switch"):
            if required not in present_classes:
                fail_reasons.append(
                    f"state_switch profile missing required semantic event class {required!r}"
                )
    elif evidence_chain_profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL:
        if "kill_all_terminal" not in present_classes:
            fail_reasons.append(
                "kill_all profile missing required semantic event class 'kill_all_terminal'"
            )

    if not projected:
        fail_reasons.append("no projectable replay transitions for profile")

    return tuple(projected), tuple(fail_reasons)


def build_master_v2_state_event_stream_validation_input_from_replay(
    *,
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    correlation_id: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
    source_revision: str,
    evidence_chain_profile: str | None = None,
) -> tuple[MasterV2StateEventStreamValidationInput | None, tuple[str, ...]]:
    binding = replay_result.master_v2_decision_state_digest_binding
    if binding is None:
        return None, ("master_v2_decision_state_digest_binding required",)
    profile = evidence_chain_profile or _infer_evidence_chain_profile_from_replay(
        replay_result.tick_records
    )
    if profile is None:
        return None, ("evidence_chain_profile not inferable from replay",)

    events, projection_failures = project_master_v2_state_events_from_replay_records(
        records=replay_result.tick_records,
        correlation_id=correlation_id,
        bound_scope_state_digest=binding.dynamic_scope_state_digest,
        evidence_chain_profile=profile,
    )
    fail_reasons = list(projection_failures)
    if fail_reasons:
        return None, tuple(fail_reasons)

    return (
        MasterV2StateEventStreamValidationInput(
            boundary_owner=MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
            source_revision=source_revision,
            completion_identity_digest=completion_identity_digest,
            manifest_identity_digest=manifest_identity_digest,
            run_identity_digest=run_identity_digest,
            correlation_id=correlation_id,
            evidence_chain_profile=profile,
            bound_dynamic_scope_state_digest=binding.dynamic_scope_state_digest,
            events=events,
        ),
        (),
    )


def project_master_v2_state_event_stream_from_replay(
    *,
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    correlation_id: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
    source_revision: str,
    evidence_chain_profile: str | None = None,
) -> MasterV2ReplayStateEventProjectionResultV0:
    """Project offline replay output into event-stream-shaped Master-V2 records (non-authorizing)."""
    validation_input, build_failures = (
        build_master_v2_state_event_stream_validation_input_from_replay(
            replay_result=replay_result,
            correlation_id=correlation_id,
            completion_identity_digest=completion_identity_digest,
            manifest_identity_digest=manifest_identity_digest,
            run_identity_digest=run_identity_digest,
            source_revision=source_revision,
            evidence_chain_profile=evidence_chain_profile,
        )
    )
    if validation_input is None:
        return MasterV2ReplayStateEventProjectionResultV0(
            layer_version=OFFLINE_REPLAY_STATE_EVENT_PROJECTION_LAYER_VERSION,
            projection_pass=False,
            evidence_chain_profile=evidence_chain_profile,
            events=(),
            validation_input=None,
            validation_result=None,
            proof_binding=None,
            projection_digest=None,
            fail_reasons=build_failures,
        )

    validation_result = evaluate_master_v2_state_event_stream_validation(validation_input)
    fail_reasons = list(build_failures)
    if not validation_result.get("validation_pass"):
        fail_reasons.extend(validation_result.get("fail_reasons", ()))

    proof_binding: MasterV2StateEventStreamProofBinding | None = None
    if validation_result.get("validation_pass"):
        proof_binding = default_minimal_master_v2_state_event_proof_binding(
            validation_input,
            validation_result,
        )

    projection_digest = compute_master_v2_replay_state_event_projection_digest(
        events=validation_input.events,
        evidence_chain_profile=validation_input.evidence_chain_profile,
        correlation_id=correlation_id,
    )

    return MasterV2ReplayStateEventProjectionResultV0(
        layer_version=OFFLINE_REPLAY_STATE_EVENT_PROJECTION_LAYER_VERSION,
        projection_pass=not fail_reasons,
        evidence_chain_profile=validation_input.evidence_chain_profile,
        events=validation_input.events,
        validation_input=validation_input,
        validation_result=validation_result,
        proof_binding=proof_binding,
        projection_digest=projection_digest,
        fail_reasons=tuple(fail_reasons),
    )
