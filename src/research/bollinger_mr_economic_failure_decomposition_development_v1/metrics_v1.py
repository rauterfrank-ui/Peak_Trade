"""Diagnostic metric helpers: PF, MFE/MAE, cost stress, side/instrument attribution."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from src.research.bollinger_mr_economic_failure_decomposition_development_v1.binding_v1 import (
    DecompositionBindingError,
    assert_trade_ledger_fields,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.constants_v1 import (
    COST_STRESS_MULTIPLIERS,
)


def profit_factor(values: Iterable[float]) -> float | None:
    xs = [float(v) for v in values]
    wins = sum(v for v in xs if v > 0.0)
    losses = abs(sum(v for v in xs if v < 0.0))
    if losses <= 0.0:
        return None if wins <= 0.0 else float("inf")
    return float(wins / losses)


def _finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return float(value)


def compute_mfe_mae_from_bars(
    *,
    side: str,
    entry_price: float,
    entry_time: pd.Timestamp,
    exit_time: pd.Timestamp,
    bars: pd.DataFrame,
) -> dict[str, Any]:
    """Path MFE/MAE from OHLC bars between entry and exit (inclusive). Fail-closed on gaps."""
    if entry_price <= 0.0:
        raise DecompositionBindingError("ENTRY_PRICE_INVALID")
    if "high" not in bars.columns or "low" not in bars.columns:
        raise DecompositionBindingError("BARS_MISSING_HIGH_LOW")
    idx = bars.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise DecompositionBindingError("BARS_INDEX_NOT_DATETIME")
    window = bars[(idx >= entry_time) & (idx <= exit_time)]
    if window.empty:
        return {
            "mfe": None,
            "mae": None,
            "mfe_bps": None,
            "mae_bps": None,
            "status": "SOURCE_MISSING",
            "reason": "MISSING_PRICE_PATH",
        }
    highs = window["high"].astype(float)
    lows = window["low"].astype(float)
    if side == "long":
        mfe = float(highs.max() - entry_price)
        mae = float(entry_price - lows.min())
    elif side == "short":
        mfe = float(entry_price - lows.min())
        mae = float(highs.max() - entry_price)
    else:
        raise DecompositionBindingError(f"TRADE_SIDE_UNKNOWN:{side}")
    mfe = max(mfe, 0.0)
    mae = max(mae, 0.0)
    return {
        "mfe": mfe,
        "mae": mae,
        "mfe_bps": (mfe / entry_price) * 10_000.0,
        "mae_bps": (mae / entry_price) * 10_000.0,
        "status": "COMPUTED",
        "reason": None,
    }


def enrich_trade_excursions(
    trades: Sequence[Mapping[str, Any]],
    bars_by_instrument: Mapping[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for trade in trades:
        assert_trade_ledger_fields(trade)
        row = dict(trade)
        instrument = str(trade["instrument_id"])
        bars = bars_by_instrument.get(instrument)
        if bars is None:
            raise DecompositionBindingError(f"BARS_MISSING_FOR_INSTRUMENT:{instrument}")
        entry_px = trade.get("entry_price")
        if entry_px is None:
            raise DecompositionBindingError("ENTRY_PRICE_MISSING")
        entry_t = pd.Timestamp(trade["entry_time"])
        exit_t = pd.Timestamp(trade["exit_time"])
        if entry_t.tzinfo is None:
            entry_t = entry_t.tz_localize("UTC")
        else:
            entry_t = entry_t.tz_convert("UTC")
        if exit_t.tzinfo is None:
            exit_t = exit_t.tz_localize("UTC")
        else:
            exit_t = exit_t.tz_convert("UTC")
        hold_h = (exit_t - entry_t).total_seconds() / 3600.0
        excursion = compute_mfe_mae_from_bars(
            side=str(trade["side"]).lower(),
            entry_price=float(entry_px),
            entry_time=entry_t,
            exit_time=exit_t,
            bars=bars,
        )
        size = abs(float(trade.get("size") or 0.0))
        mfe = excursion["mfe"]
        mae = excursion["mae"]
        # Convert price excursion to PnL units via absolute size when available.
        mfe_pnl = (float(mfe) * size) if mfe is not None else None
        mae_pnl = (float(mae) * size) if mae is not None else None
        gross = float(trade["gross_pnl"])
        capture = None
        leakage = None
        if mfe_pnl is not None and mfe_pnl > 0.0:
            capture = gross / mfe_pnl
            leakage = max(mfe_pnl - gross, 0.0)
        row.update(
            {
                "holding_period_hours": hold_h,
                "mfe": mfe,
                "mae": mae,
                "mfe_bps": excursion["mfe_bps"],
                "mae_bps": excursion["mae_bps"],
                "mfe_pnl": mfe_pnl,
                "mae_pnl": mae_pnl,
                "realized_pnl_over_mfe_capture_ratio": capture,
                "mfe_to_exit_leakage": leakage,
                "excursion_status": excursion["status"],
                "excursion_reason": excursion["reason"],
            }
        )
        out.append(row)
    return out


def cost_stress_table(
    trades: Sequence[Mapping[str, Any]],
    *,
    multipliers: Sequence[float] = COST_STRESS_MULTIPLIERS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mult in multipliers:
        gross_values: list[float] = []
        net_values: list[float] = []
        fees_total = 0.0
        slip_total = 0.0
        for t in trades:
            assert_trade_ledger_fields(t)
            gross = float(t["gross_pnl"])
            fees = float(t["fees"]) * float(mult)
            slip = float(t["slippage"]) * float(mult)
            net = gross - fees - slip
            gross_values.append(gross)
            net_values.append(net)
            fees_total += fees
            slip_total += slip
        gpf = profit_factor(gross_values)
        npf = profit_factor(net_values)
        rows.append(
            {
                "cost_multiplier": float(mult),
                "trade_count": len(trades),
                "gross_pnl": float(sum(gross_values)),
                "fees": fees_total,
                "slippage": slip_total,
                "net_pnl": float(sum(net_values)),
                "gross_profit_factor": _finite_or_none(gpf),
                "net_profit_factor": _finite_or_none(npf),
            }
        )
    return rows


def side_attribution(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[Mapping[str, Any]]] = {"long": [], "short": []}
    for t in trades:
        assert_trade_ledger_fields(t)
        side = str(t["side"]).lower()
        if side not in buckets:
            raise DecompositionBindingError(f"TRADE_SIDE_UNKNOWN:{side}")
        buckets[side].append(t)

    def _side_metrics(side_trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        gross = [float(t["gross_pnl"]) for t in side_trades]
        net = [float(t["net_pnl"]) for t in side_trades]
        fees = sum(float(t["fees"]) for t in side_trades)
        slip = sum(float(t["slippage"]) for t in side_trades)
        return {
            "trade_count": len(side_trades),
            "gross_pnl": float(sum(gross)),
            "fees": float(fees),
            "slippage": float(slip),
            "net_pnl": float(sum(net)),
            "gross_profit_factor": _finite_or_none(profit_factor(gross)),
            "net_profit_factor": _finite_or_none(profit_factor(net)),
        }

    return {
        "long": _side_metrics(buckets["long"]),
        "short": _side_metrics(buckets["short"]),
    }


def instrument_attribution(trades: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_inst: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for t in trades:
        assert_trade_ledger_fields(t)
        by_inst[str(t["instrument_id"])].append(t)
    rows: list[dict[str, Any]] = []
    for instrument_id, items in sorted(by_inst.items()):
        gross = [float(t["gross_pnl"]) for t in items]
        net = [float(t["net_pnl"]) for t in items]
        rows.append(
            {
                "instrument_id": instrument_id,
                "trade_count": len(items),
                "gross_pnl": float(sum(gross)),
                "fees": float(sum(float(t["fees"]) for t in items)),
                "slippage": float(sum(float(t["slippage"]) for t in items)),
                "net_pnl": float(sum(net)),
                "gross_profit_factor": _finite_or_none(profit_factor(gross)),
                "net_profit_factor": _finite_or_none(profit_factor(net)),
            }
        )
    rows.sort(key=lambda r: float(r["net_pnl"]))
    return rows


def aggregate_core_metrics(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    for t in trades:
        assert_trade_ledger_fields(t)
    gross = [float(t["gross_pnl"]) for t in trades]
    net = [float(t["net_pnl"]) for t in trades]
    fees = sum(float(t["fees"]) for t in trades)
    slip = sum(float(t["slippage"]) for t in trades)
    holds = [
        float(t["holding_period_hours"])
        for t in trades
        if t.get("holding_period_hours") is not None
    ]
    captures = [
        float(t["realized_pnl_over_mfe_capture_ratio"])
        for t in trades
        if t.get("realized_pnl_over_mfe_capture_ratio") is not None
    ]
    leakages = [
        float(t["mfe_to_exit_leakage"]) for t in trades if t.get("mfe_to_exit_leakage") is not None
    ]
    mfe_ok = sum(1 for t in trades if t.get("excursion_status") == "COMPUTED")
    return {
        "trade_count": len(trades),
        "gross_pnl": float(sum(gross)),
        "fees": float(fees),
        "slippage": float(slip),
        "net_pnl": float(sum(net)),
        "gross_profit_factor": _finite_or_none(profit_factor(gross)),
        "net_profit_factor": _finite_or_none(profit_factor(net)),
        "mean_holding_period_hours": float(sum(holds) / len(holds)) if holds else None,
        "median_holding_period_hours": float(pd.Series(holds).median()) if holds else None,
        "mean_realized_pnl_over_mfe_capture_ratio": (
            float(sum(captures) / len(captures)) if captures else None
        ),
        "mean_mfe_to_exit_leakage": float(sum(leakages) / len(leakages)) if leakages else None,
        "trades_with_computed_mfe_mae": mfe_ok,
        "trades_missing_mfe_mae": len(trades) - mfe_ok,
    }


def concentration_stats(instrument_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not instrument_rows:
        return {
            "worst1_abs_net_share": None,
            "worst5_abs_net_share": None,
            "dominated_by_single": False,
        }
    nets = [float(r["net_pnl"]) for r in instrument_rows]
    total_abs = sum(abs(x) for x in nets)
    if total_abs <= 0.0:
        return {
            "worst1_abs_net_share": 0.0,
            "worst5_abs_net_share": 0.0,
            "dominated_by_single": False,
        }
    sorted_abs = sorted((abs(x) for x in nets), reverse=True)
    worst1 = sorted_abs[0] / total_abs
    worst5 = sum(sorted_abs[:5]) / total_abs
    return {
        "worst1_abs_net_share": float(worst1),
        "worst5_abs_net_share": float(worst5),
        "dominated_by_single": bool(worst1 >= 0.50),
    }
