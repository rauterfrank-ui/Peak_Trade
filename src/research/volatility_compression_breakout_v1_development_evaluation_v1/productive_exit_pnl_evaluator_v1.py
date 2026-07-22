"""Productive exit/PnL evaluator for VCB v1 development evaluation.

Consumes panel wiring handoffs and applies preregistered declarative exit
semantics, then realizes roundtrip PnL via the canonical BacktestEngine
fee/slippage/gross-PnL primitives. No second PnL truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

import pandas as pd

from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EXECUTION_MODEL_VERSION,
    FEE_MODEL_VERSION,
    FUNDING_MODEL_VERSION,
    SLIPPAGE_MODEL_VERSION,
    SPREAD_MODEL_VERSION,
    EffectiveBacktestCostConfigV0,
    compute_cost_config_digest,
)
from src.backtest.engine import (
    _compute_directional_gross_pnl_v0,
    _compute_roundtrip_fee_slippage_components_v0,
)
from src.backtest.stats import compute_backtest_stats
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    FEE_BPS_PER_SIDE,
    SLIPPAGE_BPS_PER_SIDE,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
    TreatmentBaselineWiringHandoffV1,
)
from src.research.volatility_compression_breakout_v1_strategy_v1 import (
    EXIT_PARAMS_DECLARATIVE_V1,
    SIGNAL_LAG_BARS_V1,
)
from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    compute_atr20_v1,
    compute_vol_state_panel_column_v1,
)

PRODUCTIVE_EXIT_PNL_EVALUATOR_OWNER = (
    "research.volatility_compression_breakout_v1_development_evaluation_v1."
    "productive_exit_pnl_evaluator_v1"
)
CANONICAL_PNL_PRIMITIVE_OWNER = "backtest.engine._compute_directional_gross_pnl_v0"
UNIT_RISK_NOTIONAL_V1 = 1.0

ExitReasonV1 = Literal[
    "INITIAL_STOP",
    "TRAILING_STOP",
    "REGIME_EXIT",
    "TIME_EXIT",
]


@dataclass(frozen=True)
class RoundtripTradeV1:
    instrument_id: str
    side: str
    entry_index: int
    exit_index: int
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    size: float
    stop_price_at_entry: float
    exit_reason: ExitReasonV1
    gross_pnl: float
    entry_fee: float
    exit_fee: float
    entry_slippage: float
    exit_slippage: float
    pnl: float

    def to_stats_record(self) -> dict[str, Any]:
        return {
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "pnl": self.pnl,
            "gross_pnl": self.gross_pnl,
            "entry_cost": self.entry_fee + self.entry_slippage,
            "exit_cost": self.exit_fee + self.exit_slippage,
            "gross_pnl_frac": (self.gross_pnl / abs(self.size * self.entry_price))
            if self.size and self.entry_price
            else 0.0,
            "pnl_unit": "absolute_quote_currency",
            "exit_reason": self.exit_reason,
        }


@dataclass(frozen=True)
class ArmPnLResultV1:
    arm_id: str
    trades: tuple[RoundtripTradeV1, ...]
    evaluable_entry_events: int
    gross_return: float
    net_return: float
    gross_profit_factor: float
    net_profit_factor: float
    gross_pnl: float
    net_expectancy: float
    sharpe: float
    max_drawdown: float
    trade_count: int


def productive_exit_pnl_evaluator_is_bound() -> bool:
    return True


def assert_development_dataset_only(dataset_id: str) -> None:
    if dataset_id != DATASET_ID:
        raise ValueError(f"DATASET_ID_NOT_BOUND:{dataset_id}")
    if "holdout" in dataset_id.lower() and "pre_holdout" not in dataset_id.lower():
        raise ValueError(f"HOLDOUT_DATASET_REJECTED:{dataset_id}")


def build_effective_cost_config_from_binding_v1(
    cost_execution_binding: Mapping[str, Any],
    *,
    cost_multiplier: float = 1.0,
) -> EffectiveBacktestCostConfigV0:
    fee = float(cost_execution_binding["fee_model_binding"]["fee_bps_per_side"])
    slip = float(cost_execution_binding["slippage_model_binding"]["slippage_bps_per_side"])
    if abs(fee - FEE_BPS_PER_SIDE) > 1e-12:
        raise ValueError("FEE_BPS_BINDING_DRIFT")
    if abs(slip - SLIPPAGE_BPS_PER_SIDE) > 1e-12:
        raise ValueError("SLIPPAGE_BPS_BINDING_DRIFT")
    mult = float(cost_multiplier)
    if mult <= 0 or not (mult == mult):
        raise ValueError("COST_MULTIPLIER_INVALID")
    fee_eff = fee * mult
    slip_eff = slip * mult
    fields = {
        "cost_model_version": COST_MODEL_VERSION,
        "fee_model_version": FEE_MODEL_VERSION,
        "slippage_model_version": SLIPPAGE_MODEL_VERSION,
        "funding_model_version": FUNDING_MODEL_VERSION,
        "spread_model_version": SPREAD_MODEL_VERSION,
        "execution_model_version": EXECUTION_MODEL_VERSION,
        "maker_fee_bps": fee_eff,
        "taker_fee_bps": fee_eff,
        "entry_slippage_bps": slip_eff,
        "exit_slippage_bps": slip_eff,
        "funding_rate_source": "NOT_BOUND",
        "funding_application_policy": "DEFERRED_TO_LATER_STEP",
        "spread_application_policy": "NOT_APPLICABLE",
        "latency_assumption": "NOT_BOUND",
        "partial_fill_assumption": "NOT_BOUND",
        "config_source": "vcb_development_evaluation_cost_binding_v1",
    }
    digest = compute_cost_config_digest(fields)
    return EffectiveBacktestCostConfigV0(
        **fields,
        config_digest=digest,
        override_source=None,
        override_digest=None,
        economic_interpretation_allowed=True,
        zero_cost_explicitly_requested=False,
        reason_codes=["VCB_DEVELOPMENT_EVALUATION_COST_BINDING"],
    )


def _panel_to_frame(series: InstrumentPanelSeriesV1) -> pd.DataFrame:
    rows = [
        {
            "timestamp_utc": bar.timestamp_utc,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        for bar in series.bars
    ]
    if not rows:
        raise ValueError(f"EMPTY_INSTRUMENT_SERIES:{series.instrument_id}")
    frame = pd.DataFrame(rows)
    frame.index = pd.RangeIndex(len(frame))
    return frame


def _position_size_from_atr_stop_v1(*, entry_price: float, atr_at_entry: float) -> float:
    multiple = float(EXIT_PARAMS_DECLARATIVE_V1["initial_stop_atr_multiple"])
    if entry_price <= 0 or atr_at_entry <= 0 or not (entry_price == entry_price):
        raise ValueError("INVALID_ENTRY_OR_ATR_FOR_SIZING")
    stop_distance = atr_at_entry * multiple
    if stop_distance <= 0:
        raise ValueError("NON_POSITIVE_STOP_DISTANCE")
    return UNIT_RISK_NOTIONAL_V1 / stop_distance


def _realize_roundtrip_v1(
    *,
    instrument_id: str,
    side: str,
    entry_index: int,
    exit_index: int,
    entry_time: str,
    exit_time: str,
    entry_price: float,
    exit_price: float,
    size: float,
    stop_price_at_entry: float,
    exit_reason: ExitReasonV1,
    effective_cost: EffectiveBacktestCostConfigV0,
) -> RoundtripTradeV1:
    side_l = side.lower()
    if side_l not in {"long", "short"}:
        raise ValueError(f"UNSUPPORTED_SIDE:{side}")
    gross = _compute_directional_gross_pnl_v0(
        size=size,
        entry_price=entry_price,
        exit_price=exit_price,
        side=side_l,
    )
    entry_fee, exit_fee, entry_slip, exit_slip = _compute_roundtrip_fee_slippage_components_v0(
        size=size,
        entry_price=entry_price,
        exit_price=exit_price,
        effective_cost=effective_cost,
    )
    net = gross - entry_fee - exit_fee - entry_slip - exit_slip
    return RoundtripTradeV1(
        instrument_id=instrument_id,
        side=side_l,
        entry_index=entry_index,
        exit_index=exit_index,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_price=entry_price,
        exit_price=exit_price,
        size=size,
        stop_price_at_entry=stop_price_at_entry,
        exit_reason=exit_reason,
        gross_pnl=float(gross),
        entry_fee=float(entry_fee),
        exit_fee=float(exit_fee),
        entry_slippage=float(entry_slip),
        exit_slippage=float(exit_slip),
        pnl=float(net),
    )


def simulate_arm_roundtrips_v1(
    *,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    arm: ArmEventSeriesV1,
    effective_cost: EffectiveBacktestCostConfigV0,
) -> tuple[RoundtripTradeV1, ...]:
    """Pair entry events with first-event-wins exits; fail-closed if unpairable."""
    by_id = {s.instrument_id: s for s in panel_series}
    if arm.instrument_id not in by_id:
        raise ValueError(f"ARM_INSTRUMENT_MISSING:{arm.instrument_id}")
    frame = _panel_to_frame(by_id[arm.instrument_id])
    atr = compute_atr20_v1(frame["high"], frame["low"], frame["close"])
    vol = compute_vol_state_panel_column_v1(frame)
    percentile = vol["percentile_rank_120"]
    lag = int(SIGNAL_LAG_BARS_V1)
    init_mult = float(EXIT_PARAMS_DECLARATIVE_V1["initial_stop_atr_multiple"])
    trail_mult = float(EXIT_PARAMS_DECLARATIVE_V1["trailing_stop_atr_multiple"])
    regime_lt = float(EXIT_PARAMS_DECLARATIVE_V1["regime_exit_percentile_rank_lt"])
    max_bars = int(EXIT_PARAMS_DECLARATIVE_V1["time_exit_max_bars"])
    if not EXIT_PARAMS_DECLARATIVE_V1["first_event_wins"]:
        raise ValueError("FIRST_EVENT_WINS_REQUIRED")

    trades: list[RoundtripTradeV1] = []
    n = len(frame)
    i = 0
    while i < len(arm.entry_event_mask):
        if not arm.entry_event_mask[i]:
            i += 1
            continue
        side = str(arm.entry_sides[i]).upper()
        if side not in {"LONG", "SHORT"}:
            raise ValueError(f"ENTRY_SIDE_INVALID:{side}")
        fill_i = i + lag
        if fill_i >= n:
            raise ValueError(f"UNPAIRABLE_ENTRY_NO_FILL_BAR:{arm.instrument_id}:{i}")
        entry_price = float(frame.loc[fill_i, "open"])
        atr_entry = float(atr.iloc[fill_i])
        if not (atr_entry == atr_entry) or atr_entry <= 0:
            raise ValueError(f"ATR_INVALID_AT_ENTRY:{arm.instrument_id}:{fill_i}")
        size = _position_size_from_atr_stop_v1(entry_price=entry_price, atr_at_entry=atr_entry)
        if side == "LONG":
            stop = entry_price - init_mult * atr_entry
            peak = entry_price
        else:
            stop = entry_price + init_mult * atr_entry
            peak = entry_price
        exit_i: int | None = None
        exit_reason: ExitReasonV1 | None = None
        exit_price = 0.0
        for j in range(fill_i + 1, min(n, fill_i + 1 + max_bars)):
            high = float(frame.loc[j, "high"])
            low = float(frame.loc[j, "low"])
            close = float(frame.loc[j, "close"])
            atr_j = float(atr.iloc[j])
            pct = float(percentile.iloc[j]) if percentile.iloc[j] == percentile.iloc[j] else None
            candidates: list[tuple[int, ExitReasonV1, float]] = []
            if side == "LONG":
                peak = max(peak, high)
                trail = peak - trail_mult * atr_j if atr_j == atr_j and atr_j > 0 else None
                if low <= stop:
                    candidates.append((0, "INITIAL_STOP", stop))
                if trail is not None and low <= trail:
                    candidates.append((1, "TRAILING_STOP", trail))
            else:
                peak = min(peak, low)
                trail = peak + trail_mult * atr_j if atr_j == atr_j and atr_j > 0 else None
                if high >= stop:
                    candidates.append((0, "INITIAL_STOP", stop))
                if trail is not None and high >= trail:
                    candidates.append((1, "TRAILING_STOP", trail))
            if pct is not None and pct < regime_lt:
                candidates.append((2, "REGIME_EXIT", close))
            held = j - fill_i
            if held >= max_bars:
                candidates.append((3, "TIME_EXIT", close))
            if candidates:
                candidates.sort(key=lambda t: t[0])
                _, exit_reason, exit_price = candidates[0]
                exit_i = j
                break
        if exit_i is None or exit_reason is None:
            raise ValueError(f"UNPAIRABLE_ENTRY_NO_EXIT:{arm.instrument_id}:{i}")
        trades.append(
            _realize_roundtrip_v1(
                instrument_id=arm.instrument_id,
                side=side.lower(),
                entry_index=fill_i,
                exit_index=exit_i,
                entry_time=str(frame.loc[fill_i, "timestamp_utc"]),
                exit_time=str(frame.loc[exit_i, "timestamp_utc"]),
                entry_price=entry_price,
                exit_price=float(exit_price),
                size=size,
                stop_price_at_entry=float(stop),
                exit_reason=exit_reason,
                effective_cost=effective_cost,
            )
        )
        # No overlapping positions / pyramiding: resume after exit.
        i = exit_i + 1
    return tuple(trades)


def _metrics_from_trades(trades: Sequence[RoundtripTradeV1]) -> dict[str, float]:
    if not trades:
        return {
            "gross_return": 0.0,
            "net_return": 0.0,
            "gross_profit_factor": 0.0,
            "net_profit_factor": 0.0,
            "gross_pnl": 0.0,
            "net_expectancy": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "trade_count": 0.0,
        }
    records = [t.to_stats_record() for t in trades]
    equity = pd.Series(
        [UNIT_RISK_NOTIONAL_V1]
        + [
            UNIT_RISK_NOTIONAL_V1 + sum(tr.pnl for tr in trades[: idx + 1])
            for idx in range(len(trades))
        ]
    )
    stats = compute_backtest_stats(records, equity, periods_per_year=24 * 365)
    gross_pnls = [t.gross_pnl for t in trades]
    gross_wins = sum(x for x in gross_pnls if x > 0)
    gross_losses = sum(-x for x in gross_pnls if x < 0)
    gpf = (gross_wins / gross_losses) if gross_losses > 0 else (999.0 if gross_wins > 0 else 0.0)
    net_pnls = [t.pnl for t in trades]
    return {
        "gross_return": float(stats.get("total_return") or 0.0),
        "net_return": float(stats.get("total_return") or 0.0),
        "gross_profit_factor": float(gpf),
        "net_profit_factor": float(stats.get("profit_factor") or 0.0),
        "gross_pnl": float(sum(gross_pnls)),
        "net_expectancy": float(sum(net_pnls) / len(net_pnls)),
        "sharpe": float(stats.get("sharpe") or 0.0),
        "max_drawdown": float(abs(stats.get("max_drawdown") or 0.0)),
        "trade_count": float(len(trades)),
    }


def evaluate_arm_productive_pnl_v1(
    *,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    arm: ArmEventSeriesV1,
    effective_cost: EffectiveBacktestCostConfigV0,
) -> ArmPnLResultV1:
    trades = simulate_arm_roundtrips_v1(
        panel_series=panel_series, arm=arm, effective_cost=effective_cost
    )
    metrics = _metrics_from_trades(trades)
    return ArmPnLResultV1(
        arm_id=arm.arm_id,
        trades=trades,
        evaluable_entry_events=arm.evaluable_entry_event_count,
        gross_return=metrics["gross_return"],
        net_return=metrics["net_return"],
        gross_profit_factor=metrics["gross_profit_factor"],
        net_profit_factor=metrics["net_profit_factor"],
        gross_pnl=metrics["gross_pnl"],
        net_expectancy=metrics["net_expectancy"],
        sharpe=metrics["sharpe"],
        max_drawdown=metrics["max_drawdown"],
        trade_count=int(metrics["trade_count"]),
    )


def evaluate_treatment_and_baseline_productive_pnl_v1(
    *,
    dataset_id: str,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    handoff: TreatmentBaselineWiringHandoffV1,
    cost_execution_binding: Mapping[str, Any],
    cost_multiplier: float = 1.0,
) -> tuple[ArmPnLResultV1, ArmPnLResultV1]:
    """Identical productive PnL semantics for treatment and baseline arms."""
    assert_development_dataset_only(dataset_id)
    if handoff.holdout_accessed if hasattr(handoff, "holdout_accessed") else False:
        raise ValueError("HOLDOUT_ACCESSED_TRUE")
    effective = build_effective_cost_config_from_binding_v1(
        cost_execution_binding, cost_multiplier=cost_multiplier
    )
    if not handoff.treatment:
        raise ValueError("EMPTY_TREATMENT_ARMS")
    if not handoff.baseline:
        raise ValueError("EMPTY_BASELINE_ARMS")

    # Aggregate multi-instrument arms with identical evaluator.
    def _agg(arms: tuple[ArmEventSeriesV1, ...], arm_id: str) -> ArmPnLResultV1:
        all_trades: list[RoundtripTradeV1] = []
        events = 0
        for arm in arms:
            one = evaluate_arm_productive_pnl_v1(
                panel_series=panel_series, arm=arm, effective_cost=effective
            )
            all_trades.extend(one.trades)
            events += one.evaluable_entry_events
        metrics = _metrics_from_trades(all_trades)
        return ArmPnLResultV1(
            arm_id=arm_id,
            trades=tuple(all_trades),
            evaluable_entry_events=events,
            gross_return=metrics["gross_return"],
            net_return=metrics["net_return"],
            gross_profit_factor=metrics["gross_profit_factor"],
            net_profit_factor=metrics["net_profit_factor"],
            gross_pnl=metrics["gross_pnl"],
            net_expectancy=metrics["net_expectancy"],
            sharpe=metrics["sharpe"],
            max_drawdown=metrics["max_drawdown"],
            trade_count=int(metrics["trade_count"]),
        )

    treatment = _agg(handoff.treatment, "TREATMENT")
    baseline = _agg(handoff.baseline, "BASELINE")
    return treatment, baseline
