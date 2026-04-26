# tests/trading/master_v2/test_double_play_pure_stack_contract.py
"""
Cross-module contract tests: State -> Survival -> Suitability -> Composition.

No runtime integration, registry, execution, or exchange (import checks below).
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
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
    compose_double_play_decision,
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
    assert not comp.live_authorization


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

    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok(future="SOL-USD-PERP", realized=340.0, survival_allows_slot=True)
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    assert rat.can_ratchet
    assert not rel.released
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert not rel.authorizes_new_trade


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
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
        )
    )
    cfg = _cs_cfg_ok()
    cs_st = _cs_state_ok()
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)

    assert not t2.live_authorization_granted
    assert not surv.live_authorization
    assert not suit.projection.live_authorization
    assert not suit.live_authorization
    assert not comp.live_authorization
    assert not rat.live_authorization
    assert not rel.live_authorization
    assert GOOD_ENVELOPE.live_authorization is False


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
