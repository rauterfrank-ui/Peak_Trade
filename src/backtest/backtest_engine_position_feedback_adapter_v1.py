"""
Narrow adapter: project canonical BacktestEngine bar execution position into MV2 replay inputs.

Offline-only wiring slice — no runtime, authority, order, or economic evaluation effects.
Reuses BacktestEngine legacy realistic bar semantics without duplicating execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional

import pandas as pd

from src.backtest.cost_config_v0 import EffectiveBacktestCostConfigV0
from src.backtest.engine import (
    BacktestEngine,
    Trade,
    _emit_legacy_trade_accounting_fields_v0,
)
from src.backtest.result import BacktestResult
from src.backtest import stats as stats_mod
from src.backtest.cost_config_v0 import append_cost_accounting_fields, build_cost_result_metadata
from src.risk import PositionRequest, calc_position_size
from src.trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
    EntryExitDirectionState,
)
from src.trading.master_v2.double_play_state import SideState

BACKTEST_ENGINE_POSITION_FEEDBACK_ADAPTER_LAYER_VERSION = "v1"
BACKTEST_ENGINE_POSITION_FEEDBACK_ADAPTER_OWNER = (
    "backtest.backtest_engine_position_feedback_adapter_v1"
)
CANONICAL_BACKTEST_POSITION_OWNER = "backtest.engine.BacktestEngine"
BACKTEST_POSITION_FEEDBACK_ROLE = "OBSERVATION_ONLY"
BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE = False

_PARTIAL_REDUCTION_SUPPORTED_BY_CANONICAL_OWNER = False


@dataclass(frozen=True)
class BacktestEnginePositionFeedbackV1:
    """Canonical backtest execution position snapshot consumable by the next MV2 replay bar.

    Position fields are **observation only**. ``side_state`` / ``direction_state`` are
    non-authoritative placeholders (always NEUTRAL) and must not overwrite Double Play
    SideState / Switch authority.
    """

    feedback_source_bar_epoch: int
    position_state: PositionState
    existing_position_side: ExistingPositionSide
    venue_flat: bool
    side_state: SideState
    direction_state: EntryExitDirectionState
    position_management_context: PositionManagementContext
    reconciliation_state: ReconciliationState
    last_bar_exit_reason: str | None = None
    has_open_trade: bool = False
    authority_role: str = BACKTEST_POSITION_FEEDBACK_ROLE


@dataclass
class LegacyRealisticBarLoopStateV1:
    """Mutable single-run state for incremental legacy realistic bar execution."""

    equity: float
    current_trade: Trade | None = None
    trades: list[Trade] = field(default_factory=list)
    blocked_trades: int = 0
    equity_curve: list[float] = field(default_factory=list)
    daily_returns_pct: dict[Any, float] = field(default_factory=dict)
    last_bar_exit_reason: str | None = None
    stop_pct: float = 0.02


def coerce_backtest_position_state_v1(value: object) -> PositionState:
    if isinstance(value, PositionState):
        return value
    if isinstance(value, str):
        try:
            return PositionState(value)
        except ValueError as exc:
            raise ValueError("position_state_coercion_failed") from exc
    raise ValueError("position_state_coercion_failed")


def init_legacy_realistic_bar_loop_state_v1(
    engine: BacktestEngine,
    *,
    strategy_params: Mapping[str, Any],
) -> LegacyRealisticBarLoopStateV1:
    equity = float(engine.config["backtest"]["initial_cash"])
    offline_sizing_bound = isinstance(
        engine.config.get("offline_evaluation_sizing_contract_v1"), Mapping
    )
    if offline_sizing_bound:
        if "stop_pct" not in strategy_params:
            raise ValueError("missing_stop_pct")
        stop_pct = float(strategy_params["stop_pct"])
    else:
        stop_pct = float(strategy_params.get("stop_pct", 0.02))
    if engine.risk_manager is not None:
        engine.risk_manager.reset(start_equity=equity)
    return LegacyRealisticBarLoopStateV1(
        equity=equity,
        equity_curve=[equity],
        stop_pct=stop_pct,
    )


def step_legacy_realistic_bar_v1(
    engine: BacktestEngine,
    state: LegacyRealisticBarLoopStateV1,
    *,
    bar: pd.Series,
    signal: int,
    symbol: str,
    effective_cost: EffectiveBacktestCostConfigV0,
) -> LegacyRealisticBarLoopStateV1:
    """Execute exactly one legacy realistic bar using canonical BacktestEngine helpers."""
    trade_dt = bar.name
    current_trade = state.current_trade
    equity = state.equity
    blocked_trades = state.blocked_trades
    trades = list(state.trades)
    last_bar_exit_reason: str | None = None
    offline_sizing_bound = isinstance(
        engine.config.get("offline_evaluation_sizing_contract_v1"), Mapping
    )

    if current_trade is not None and bar["low"] <= current_trade.stop_price:
        current_trade.exit_time = trade_dt
        current_trade.exit_price = current_trade.stop_price
        current_trade.pnl = current_trade.size * (
            current_trade.exit_price - current_trade.entry_price
        )
        current_trade.pnl_pct = (
            (current_trade.exit_price - current_trade.entry_price)
            / current_trade.entry_price
            * 100.0
        )
        current_trade.exit_reason = "stop_loss"
        _emit_legacy_trade_accounting_fields_v0(
            current_trade,
            side="long",
            effective_cost=effective_cost,
        )
        equity += current_trade.pnl
        trades.append(current_trade)
        engine._register_trade_pnl(trade_dt, current_trade.pnl_pct)
        last_bar_exit_reason = "stop_loss"
        current_trade = None

    if signal == 1 and current_trade is None:
        entry_price = float(bar["close"])
        stop_price = entry_price * (1 - state.stop_pct)
        if engine.core_position_sizer is not None:
            target_units = engine.core_position_sizer.get_target_position(
                signal=int(signal), price=entry_price, equity=equity
            )
            if engine.risk_manager is not None:
                target_units = engine.risk_manager.adjust_target_position(
                    target_units=target_units,
                    price=entry_price,
                    equity=equity,
                    timestamp=trade_dt,
                    symbol=symbol,
                )
            position_value = abs(target_units) * entry_price
            position_size = abs(target_units)
            rejected = target_units == 0 or position_value < engine.config["risk"].get(
                "min_position_value", 50.0
            )
            if not rejected:
                max_pos_pct = engine.config["risk"].get("max_position_size", 0.25)
                if position_value > equity * max_pos_pct:
                    rejected = True
            if rejected:
                blocked_trades += 1
            elif engine._check_risk_limits(
                current_capital=equity,
                proposed_position_value=position_value,
                current_dt=trade_dt,
            ):
                current_trade = Trade(
                    entry_time=trade_dt,
                    entry_price=entry_price,
                    size=position_size,
                    stop_price=stop_price,
                )
            else:
                blocked_trades += 1
        elif offline_sizing_bound:
            from src.backtest.offline_evaluation_sizing_contract_v1 import (
                get_offline_sizing_accounting_v1,
                load_offline_evaluation_sizing_contract_v1,
                size_offline_evaluation_entry_v1,
            )

            contract = load_offline_evaluation_sizing_contract_v1(engine.config)
            accounting = get_offline_sizing_accounting_v1(engine.config)
            sizing_outcome = size_offline_evaluation_entry_v1(
                contract=contract,
                equity=equity,
                entry_price=entry_price,
                cfg=engine.config,
                accounting=accounting,
            )
            if not sizing_outcome.accepted:
                blocked_trades += 1
            elif engine._check_risk_limits(
                current_capital=equity,
                proposed_position_value=sizing_outcome.effective_notional,
                current_dt=trade_dt,
            ):
                current_trade = Trade(
                    entry_time=trade_dt,
                    entry_price=entry_price,
                    size=sizing_outcome.size,
                    stop_price=sizing_outcome.stop_price,
                )
            else:
                blocked_trades += 1
        else:
            req = PositionRequest(
                equity=equity,
                entry_price=entry_price,
                stop_price=stop_price,
                risk_per_trade=engine.config["risk"]["risk_per_trade"],
            )
            pos_result = calc_position_size(
                req,
                max_position_pct=engine.config["risk"]["max_position_size"],
                min_position_value=engine.config["risk"]["min_position_value"],
                min_stop_distance=engine.config["risk"]["min_stop_distance"],
            )
            if pos_result.rejected:
                blocked_trades += 1
            elif engine._check_risk_limits(
                current_capital=equity,
                proposed_position_value=pos_result.value,
                current_dt=trade_dt,
            ):
                current_trade = Trade(
                    entry_time=trade_dt,
                    entry_price=entry_price,
                    size=pos_result.size,
                    stop_price=stop_price,
                )
            else:
                blocked_trades += 1

    elif signal == -1 and current_trade is not None:
        current_trade.exit_time = trade_dt
        current_trade.exit_price = float(bar["close"])
        current_trade.pnl = current_trade.size * (
            current_trade.exit_price - current_trade.entry_price
        )
        current_trade.pnl_pct = (
            (current_trade.exit_price - current_trade.entry_price)
            / current_trade.entry_price
            * 100.0
        )
        current_trade.exit_reason = "signal"
        _emit_legacy_trade_accounting_fields_v0(
            current_trade,
            side="long",
            effective_cost=effective_cost,
        )
        equity += current_trade.pnl
        trades.append(current_trade)
        engine._register_trade_pnl(trade_dt, current_trade.pnl_pct)
        last_bar_exit_reason = "signal"
        current_trade = None

    equity_curve = list(state.equity_curve)
    equity_curve.append(equity)
    return LegacyRealisticBarLoopStateV1(
        equity=equity,
        current_trade=current_trade,
        trades=trades,
        blocked_trades=blocked_trades,
        equity_curve=equity_curve,
        daily_returns_pct=dict(state.daily_returns_pct),
        last_bar_exit_reason=last_bar_exit_reason,
        stop_pct=state.stop_pct,
    )


def capture_backtest_engine_position_feedback_v1(
    *,
    state: LegacyRealisticBarLoopStateV1,
    feedback_source_bar_epoch: int,
) -> BacktestEnginePositionFeedbackV1:
    """Capture position observation only — never invent Bull/Bear SideState authority.

    Open trades are reported as ``ExistingPositionSide`` / ``PositionManagementContext``
    facts. ``side_state`` / ``direction_state`` remain NEUTRAL placeholders and are not
    applied onto the Double Play state machine by the wiring apply hook.
    """
    # Non-authoritative placeholders — must not become Bull/Bear Switch authority.
    neutral_side = SideState.NEUTRAL_OBSERVE
    neutral_direction = EntryExitDirectionState.NEUTRAL
    if state.current_trade is not None:
        # Legacy realistic loop currently opens long-only trades; report as position
        # observation, not as SideState.SHORT/LONG Double Play authority.
        return BacktestEnginePositionFeedbackV1(
            feedback_source_bar_epoch=feedback_source_bar_epoch,
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
            side_state=neutral_side,
            direction_state=neutral_direction,
            position_management_context=PositionManagementContext.LONG_POSITION,
            reconciliation_state=ReconciliationState.RECONCILED,
            last_bar_exit_reason=state.last_bar_exit_reason,
            has_open_trade=True,
            authority_role=BACKTEST_POSITION_FEEDBACK_ROLE,
        )
    return BacktestEnginePositionFeedbackV1(
        feedback_source_bar_epoch=feedback_source_bar_epoch,
        position_state=PositionState.FLAT_RECONCILED,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
        side_state=neutral_side,
        direction_state=neutral_direction,
        position_management_context=PositionManagementContext.FLAT,
        reconciliation_state=ReconciliationState.RECONCILED,
        last_bar_exit_reason=state.last_bar_exit_reason,
        has_open_trade=False,
        authority_role=BACKTEST_POSITION_FEEDBACK_ROLE,
    )


def finalize_legacy_realistic_bar_loop_v1(
    engine: BacktestEngine,
    state: LegacyRealisticBarLoopStateV1,
    *,
    df: pd.DataFrame,
    effective_cost: EffectiveBacktestCostConfigV0,
    symbol: str,
) -> BacktestResult:
    """Finalize incremental loop into canonical BacktestResult without a second full pass."""
    equity = state.equity
    trades = list(state.trades)
    blocked_trades = state.blocked_trades
    current_trade = state.current_trade
    equity_curve = list(state.equity_curve)

    if current_trade is not None:
        last_bar = df.iloc[-1]
        current_trade.exit_time = last_bar.name
        current_trade.exit_price = float(last_bar["close"])
        current_trade.pnl = current_trade.size * (
            current_trade.exit_price - current_trade.entry_price
        )
        current_trade.pnl_pct = (
            (current_trade.exit_price - current_trade.entry_price)
            / current_trade.entry_price
            * 100.0
        )
        current_trade.exit_reason = "end_of_data"
        _emit_legacy_trade_accounting_fields_v0(
            current_trade,
            side="long",
            effective_cost=effective_cost,
        )
        equity += current_trade.pnl
        trades.append(current_trade)
        engine._register_trade_pnl(last_bar.name, current_trade.pnl_pct)
        if equity_curve:
            equity_curve[-1] = equity

    equity_series = pd.Series(equity_curve, index=[df.index[0]] + list(df.index))
    drawdown_series = stats_mod.compute_drawdown(equity_series)
    basic_stats = stats_mod.compute_basic_stats(equity_series)
    from src.backtest.stats import compute_trade_stats

    trade_stats = compute_trade_stats([t.__dict__ for t in trades])
    stats = {
        **basic_stats,
        "total_trades": trade_stats.total_trades,
        "win_rate": trade_stats.win_rate,
        "profit_factor": trade_stats.profit_factor,
        "blocked_trades": blocked_trades,
        "ulcer_index": stats_mod.compute_ulcer_index(equity_series),
        "recovery_factor": stats_mod.compute_recovery_factor(equity_series),
    }
    trades_df = pd.DataFrame([t.__dict__ for t in trades]) if trades else None
    initial_equity = float(engine.config["backtest"]["initial_cash"])
    stats = append_cost_accounting_fields(
        stats,
        initial_equity=initial_equity,
        effective_cost=effective_cost,
        total_fees=0.0,
        total_notional=0.0,
    )
    metadata = build_cost_result_metadata(
        effective_cost,
        extra={
            "mode": "realistic_with_risk_management",
            "strategy_name": "",
            "blocked_trades": blocked_trades,
            "legacy_path_cost_application": False,
            "symbol": symbol,
            "incremental_bar_loop": True,
        },
    )
    return BacktestResult(
        equity_curve=equity_series,
        drawdown=drawdown_series,
        trades=trades_df,
        stats=stats,
        metadata=metadata,
    )
