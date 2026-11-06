"""Deterministic derived economic, trade, cost, funnel, and drawdown metrics v1.

Derives registry-bound observability metrics exclusively from canonical persisted
owners (stats, cost_config, engine trades, trade ledger, equity curve, decision funnel).
No new trading, strategy, runtime, or economic evaluation semantics.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.backtest.cost_config_v0 import (
    EffectiveBacktestCostConfigV0,
    compute_effective_roundtrip_cost_bps,
)
from src.backtest.decision_funnel_v0 import (
    DECISION_FUNNEL_OWNER,
    DecisionFunnelPersistenceV0,
    FUNNEL_STAGE_ORDER,
)
from src.backtest.economic_observability_registry_v1 import (
    EconomicObservabilityMetricRegistryV1,
    MetricRegistryEntryV1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    CanonicalEconomicObservabilitySnapshotV1,
    MetricMaterializationStatus,
    MetricValueV1,
    REASON_REQUIRED_STATUSES,
    SnapshotContractError,
)
from src.backtest.stats import compute_drawdown
from src.backtest.trade_ledger_equity_curve_persistence_v0 import TradeLedgerRowV0
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    RUNBOOK_FUNNEL_FIELDS,
)

DERIVED_METRICS_OWNER = "backtest.economic_observability_derived_metrics_v1"
CANONICAL_DERIVED_METRICS_OWNER = DERIVED_METRICS_OWNER
FORMULA_DERIVED_V1 = "derived_economic_trade_metrics_v1"
FORMULA_DRAWDOWN_RECONSTRUCT_V1 = "drawdown_episode_reconstruction_v1"
FORMULA_FUNNEL_CONVERSION_V1 = "funnel_stage_conversion_v1"
FORMULA_BREAK_EVEN_EDGE_V1 = "proportional_roundtrip_cost_break_even_edge_v1"

RECONCILIATION_TOLERANCE = 1e-9

# Scope alias -> canonical registry metric_id (registry is SSOT).
SCOPE_METRIC_ALIASES: dict[str, str] = {
    "avg_win": "average_winner",
    "avg_loss": "average_loser",
    "best_trade": "largest_winner",
    "worst_trade": "largest_loser",
    "consecutive_wins_max": "consecutive_wins",
    "consecutive_losses_max": "consecutive_losses",
    "median_trade_pnl": "median_winner",
    "holding_time": "holding_time_mean",
    "conversion_rate_between_stages": "conversion_rate_per_stage",
    "cost_to_gross_profit_ratio": "cost_share_of_gross_profit",
    "max_drawdown_duration": "drawdown_duration",
    "drawdown_recovery_time": "recovery_duration",
    "pnl_by_instrument": "instrument_breakdown",
    "pnl_by_regime": "regime_breakdown",
    "roundtrip_cost_bps": "break_even_cost_bps",
}


@dataclass(frozen=True)
class DerivedMetricResultV1:
    metric_id: str
    value: Optional[float]
    status: MetricMaterializationStatus
    owner: str
    source: str
    formula_version: str
    sample_count: Optional[int]
    quality_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class DerivedMetricsBundleV1:
    trade_aggregates: dict[str, DerivedMetricResultV1]
    cost_ratios: dict[str, DerivedMetricResultV1]
    drawdown_metrics: dict[str, DerivedMetricResultV1]
    funnel_metrics: dict[str, DerivedMetricResultV1]
    breakdown_metrics: dict[str, DerivedMetricResultV1]
    pnl_by_side: dict[str, float]
    pnl_by_instrument: dict[str, float]
    pnl_by_regime: dict[str, float]
    pnl_by_exit_reason: dict[str, float]
    exit_reason_counts: dict[str, int]
    entry_reason_counts: dict[str, int]
    stage_conversion_rates: dict[str, float]


@dataclass(frozen=True)
class DerivedMetricsSummaryV1:
    computed_metric_count: int
    reconstructed_metric_count: int
    not_computed_metric_count: int
    not_applicable_metric_count: int
    insufficient_data_metric_count: int
    source_missing_metric_count: int


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _trade_pnls(trades: Sequence[Mapping[str, Any]]) -> list[float]:
    pnls: list[float] = []
    for index, trade in enumerate(trades):
        if "pnl" not in trade:
            raise SnapshotContractError(f"trade_missing_pnl index={index}")
        pnl_value = trade["pnl"]
        if pnl_value is None:
            raise SnapshotContractError(f"trade_null_pnl index={index}")
        pnls.append(float(pnl_value))
    return pnls


def _trade_gross_pnls(trades: Sequence[Mapping[str, Any]]) -> list[float]:
    gross_values: list[float] = []
    for index, trade in enumerate(trades):
        if "gross_pnl" in trade and trade["gross_pnl"] is not None:
            gross_values.append(float(trade["gross_pnl"]))
            continue
        if "pnl" not in trade:
            raise SnapshotContractError(f"trade_missing_gross_or_net_pnl index={index}")
        gross_values.append(float(trade["pnl"]))
    return gross_values


def _holding_time_seconds(trade: Mapping[str, Any]) -> Optional[float]:
    entry_time = trade.get("entry_time")
    exit_time = trade.get("exit_time")
    if entry_time is None or exit_time is None:
        return None
    try:
        delta = pd.Timestamp(exit_time) - pd.Timestamp(entry_time)
        return float(delta.total_seconds())
    except (TypeError, ValueError):
        return None


def _computed_result(
    *,
    metric_id: str,
    value: float,
    owner: str,
    source: str,
    formula_version: str,
    sample_count: Optional[int] = None,
    status: MetricMaterializationStatus = MetricMaterializationStatus.COMPUTED,
    quality_flags: tuple[str, ...] = (),
) -> DerivedMetricResultV1:
    return DerivedMetricResultV1(
        metric_id=metric_id,
        value=float(value),
        status=status,
        owner=owner,
        source=source,
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=quality_flags,
        reason_codes=(),
    )


def _status_result(
    *,
    metric_id: str,
    status: MetricMaterializationStatus,
    owner: str,
    source: str,
    formula_version: str,
    reason_codes: tuple[str, ...],
    sample_count: Optional[int] = None,
) -> DerivedMetricResultV1:
    if status in REASON_REQUIRED_STATUSES and not reason_codes:
        raise SnapshotContractError(f"status {status.value} requires reason_codes for {metric_id}")
    return DerivedMetricResultV1(
        metric_id=metric_id,
        value=None,
        status=status,
        owner=owner,
        source=source,
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=(),
        reason_codes=reason_codes,
    )


def derive_trade_aggregates_v1(
    trades: Sequence[Mapping[str, Any]],
    *,
    stats: Optional[Mapping[str, Any]] = None,
) -> dict[str, DerivedMetricResultV1]:
    """Derive trade-level economic and strategy-quality metrics from engine trades."""
    owner = DERIVED_METRICS_OWNER
    source = f"{DERIVED_METRICS_OWNER}:derive_trade_aggregates_v1"
    formula = FORMULA_DERIVED_V1

    if not trades:
        zero_status = MetricMaterializationStatus.INSUFFICIENT_DATA
        reason = ("NO_TRADES",)
        zero_fields = (
            "gross_profit",
            "gross_loss",
            "profit_factor_gross",
            "expectancy_gross",
            "expectancy_net",
            "payoff_ratio",
            "average_winner",
            "average_loser",
            "median_winner",
            "median_loser",
            "largest_winner",
            "largest_loser",
            "consecutive_wins",
            "consecutive_losses",
            "flat_trade_count",
            "holding_time_mean",
            "holding_time_median",
            "holding_time_distribution",
        )
        return {
            field: _status_result(
                metric_id=field,
                status=zero_status,
                owner=owner,
                source=source,
                formula_version=formula,
                reason_codes=reason,
                sample_count=0,
            )
            for field in zero_fields
        }

    pnls = _trade_pnls(trades)
    gross_pnls = _trade_gross_pnls(trades)
    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p < 0]
    flats = [p for p in pnls if p == 0]
    gross_winners = [p for p in gross_pnls if p > 0]
    gross_losers = [p for p in gross_pnls if p < 0]

    gross_profit = sum(gross_winners) if gross_winners else 0.0
    gross_loss = sum(gross_losers) if gross_losers else 0.0
    net_profit = sum(winners) if winners else 0.0
    net_loss = sum(losers) if losers else 0.0

    gross_loss_abs = abs(gross_loss)
    net_loss_abs = abs(net_loss)

    if gross_loss_abs > 0:
        profit_factor_gross = gross_profit / gross_loss_abs
        pf_gross_status = MetricMaterializationStatus.RECONSTRUCTED
    else:
        profit_factor_gross = 0.0
        pf_gross_status = MetricMaterializationStatus.COMPUTED

    if net_loss_abs > 0:
        profit_factor_net_derived = net_profit / net_loss_abs if net_profit > 0 else 0.0
    else:
        profit_factor_net_derived = 0.0

    expectancy_gross = float(sum(gross_pnls) / len(gross_pnls))
    expectancy_net = float(sum(pnls) / len(pnls))

    avg_win = float(statistics.mean(winners)) if winners else 0.0
    avg_loss = float(statistics.mean(losers)) if losers else 0.0
    if stats is not None:
        if _is_finite_number(stats.get("avg_win")):
            avg_win = float(stats["avg_win"])
        if _is_finite_number(stats.get("avg_loss")):
            avg_loss = float(stats["avg_loss"])

    payoff_ratio = (
        (abs(sum(winners) / len(winners)) / abs(sum(losers) / len(losers)))
        if (winners and losers and sum(losers) != 0)
        else 0.0
    )

    median_winner = float(statistics.median(winners)) if winners else 0.0
    median_loser = float(statistics.median(losers)) if losers else 0.0
    trade_pnl_std = float(statistics.pstdev(pnls)) if len(pnls) > 1 else 0.0

    holding_times = [
        value for value in (_holding_time_seconds(t) for t in trades) if value is not None
    ]
    holding_mean = float(statistics.mean(holding_times)) if holding_times else None
    holding_median = float(statistics.median(holding_times)) if holding_times else None
    holding_distribution = float(len(holding_times))

    max_consecutive_wins = 0
    max_consecutive_losses = 0
    streak_wins = 0
    streak_losses = 0
    for pnl in pnls:
        if pnl > 0:
            streak_wins += 1
            streak_losses = 0
        elif pnl < 0:
            streak_losses += 1
            streak_wins = 0
        else:
            streak_wins = 0
            streak_losses = 0
        max_consecutive_wins = max(max_consecutive_wins, streak_wins)
        max_consecutive_losses = max(max_consecutive_losses, streak_losses)

    sample_count = len(trades)
    results: dict[str, DerivedMetricResultV1] = {
        "gross_profit": _computed_result(
            metric_id="gross_profit",
            value=gross_profit,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        ),
        "gross_loss": _computed_result(
            metric_id="gross_loss",
            value=gross_loss,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        ),
        "profit_factor_gross": _computed_result(
            metric_id="profit_factor_gross",
            value=profit_factor_gross,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
            status=pf_gross_status,
            quality_flags=("DERIVED_FROM_GROSS_PNL",),
        ),
        "profit_factor_net_derived": _computed_result(
            metric_id="profit_factor_net",
            value=profit_factor_net_derived,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "expectancy_gross": _computed_result(
            metric_id="expectancy_gross",
            value=expectancy_gross,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        ),
        "expectancy_net_derived": _computed_result(
            metric_id="expectancy_net",
            value=expectancy_net,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "average_winner": _computed_result(
            metric_id="average_winner",
            value=avg_win,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(winners) or sample_count,
        ),
        "average_loser": _computed_result(
            metric_id="average_loser",
            value=avg_loss,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(losers) or sample_count,
        ),
        "payoff_ratio": _computed_result(
            metric_id="payoff_ratio",
            value=float(payoff_ratio),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "median_winner": _computed_result(
            metric_id="median_winner",
            value=median_winner,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(winners),
        ),
        "median_loser": _computed_result(
            metric_id="median_loser",
            value=median_loser,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(losers),
        ),
        "largest_winner": _computed_result(
            metric_id="largest_winner",
            value=float(max(pnls)),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "largest_loser": _computed_result(
            metric_id="largest_loser",
            value=float(min(pnls)),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "consecutive_wins": _computed_result(
            metric_id="consecutive_wins",
            value=float(max_consecutive_wins),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "consecutive_losses": _computed_result(
            metric_id="consecutive_losses",
            value=float(max_consecutive_losses),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "flat_trade_count": _computed_result(
            metric_id="flat_trade_count",
            value=float(len(flats)),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
        "trade_pnl_std_internal": _computed_result(
            metric_id="trade_pnl_std",
            value=trade_pnl_std,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=sample_count,
        ),
    }

    if holding_mean is not None:
        results["holding_time_mean"] = _computed_result(
            metric_id="holding_time_mean",
            value=holding_mean,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(holding_times),
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        results["holding_time_mean"] = _status_result(
            metric_id="holding_time_mean",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("ENTRY_OR_EXIT_TIME_MISSING",),
            sample_count=sample_count,
        )

    if holding_median is not None:
        results["holding_time_median"] = _computed_result(
            metric_id="holding_time_median",
            value=holding_median,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(holding_times),
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        results["holding_time_median"] = results["holding_time_mean"]

    if holding_times:
        results["holding_time_distribution"] = _computed_result(
            metric_id="holding_time_distribution",
            value=holding_distribution,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(holding_times),
            status=MetricMaterializationStatus.RECONSTRUCTED,
            quality_flags=("HOLDING_TIME_SAMPLE_COUNT",),
        )
    else:
        results["holding_time_distribution"] = _status_result(
            metric_id="holding_time_distribution",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("HOLDING_TIME_UNAVAILABLE",),
            sample_count=sample_count,
        )

    # Internal reconciliation helpers (not registry-bound when absent from registry).
    results["_net_profit_internal"] = _computed_result(
        metric_id="_net_profit_internal",
        value=net_profit,
        owner=owner,
        source=source,
        formula_version=formula,
        sample_count=sample_count,
    )
    results["_net_loss_internal"] = _computed_result(
        metric_id="_net_loss_internal",
        value=net_loss,
        owner=owner,
        source=source,
        formula_version=formula,
        sample_count=sample_count,
    )
    return results


def derive_cost_ratio_metrics_v1(
    *,
    gross_profit: float,
    gross_pnl: float,
    net_pnl: float,
    total_cost: float,
    effective_cost: Optional[EffectiveBacktestCostConfigV0] = None,
    spread_half_bps: Optional[float] = None,
) -> dict[str, DerivedMetricResultV1]:
    owner = DERIVED_METRICS_OWNER
    source = f"{DERIVED_METRICS_OWNER}:derive_cost_ratio_metrics_v1"
    formula = FORMULA_DERIVED_V1
    results: dict[str, DerivedMetricResultV1] = {}

    if gross_profit > 0:
        results["cost_share_of_gross_profit"] = _computed_result(
            metric_id="cost_share_of_gross_profit",
            value=total_cost / gross_profit,
            owner=owner,
            source=source,
            formula_version=formula,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        results["cost_share_of_gross_profit"] = _status_result(
            metric_id="cost_share_of_gross_profit",
            status=MetricMaterializationStatus.INSUFFICIENT_DATA,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("ZERO_DENOMINATOR_GROSS_PROFIT",),
        )

    if gross_pnl != 0:
        results["gross_to_net_conversion"] = _computed_result(
            metric_id="gross_to_net_conversion",
            value=net_pnl / gross_pnl,
            owner=owner,
            source=source,
            formula_version=formula,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        results["gross_to_net_conversion"] = _status_result(
            metric_id="gross_to_net_conversion",
            status=MetricMaterializationStatus.INSUFFICIENT_DATA,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("ZERO_DENOMINATOR_GROSS_PNL",),
        )

    if effective_cost is not None:
        roundtrip_bps = compute_effective_roundtrip_cost_bps(
            fee_bps=effective_cost.taker_fee_bps,
            slippage_bps=effective_cost.entry_slippage_bps,
            half_spread_bps=spread_half_bps or 0.0,
        )
        results["required_gross_edge_for_break_even"] = _computed_result(
            metric_id="required_gross_edge_for_break_even",
            value=roundtrip_bps,
            owner=owner,
            source=source,
            formula_version=FORMULA_BREAK_EVEN_EDGE_V1,
            status=MetricMaterializationStatus.RECONSTRUCTED,
            quality_flags=("PROPORTIONAL_COST_MODEL_ONLY",),
        )
        results["break_even_cost_bps"] = _computed_result(
            metric_id="break_even_cost_bps",
            value=roundtrip_bps,
            owner=owner,
            source=source,
            formula_version=FORMULA_BREAK_EVEN_EDGE_V1,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        missing = ("EFFECTIVE_COST_CONFIG_MISSING",)
        results["required_gross_edge_for_break_even"] = _status_result(
            metric_id="required_gross_edge_for_break_even",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=FORMULA_BREAK_EVEN_EDGE_V1,
            reason_codes=missing,
        )
        results["break_even_cost_bps"] = _status_result(
            metric_id="break_even_cost_bps",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=FORMULA_BREAK_EVEN_EDGE_V1,
            reason_codes=missing,
        )

    results["break_even_cost"] = _status_result(
        metric_id="break_even_cost",
        status=MetricMaterializationStatus.NOT_APPLICABLE,
        owner=owner,
        source=source,
        formula_version=FORMULA_BREAK_EVEN_EDGE_V1,
        reason_codes=("BREAK_EVEN_CAPITAL_NOT_DERIVABLE_PROPORTIONAL_COST_MODEL_ONLY",),
    )
    return results


def derive_trade_breakdowns_v1(
    trades: Sequence[Mapping[str, Any]],
    *,
    default_instrument_id: str = "UNKNOWN",
) -> tuple[
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, int],
    dict[str, int],
]:
    pnl_by_side: dict[str, float] = {}
    pnl_by_instrument: dict[str, float] = {}
    pnl_by_regime: dict[str, float] = {}
    pnl_by_exit_reason: dict[str, float] = {}
    exit_reason_counts: dict[str, int] = {}
    entry_reason_counts: dict[str, int] = {}

    for trade in trades:
        pnl = float(trade["pnl"])
        size = trade.get("size")
        side = (
            "long"
            if isinstance(size, (int, float)) and float(size) > 0
            else ("short" if isinstance(size, (int, float)) and float(size) < 0 else "unknown")
        )
        pnl_by_side[side] = pnl_by_side.get(side, 0.0) + pnl

        instrument = str(trade.get("instrument_id", default_instrument_id))
        pnl_by_instrument[instrument] = pnl_by_instrument.get(instrument, 0.0) + pnl

        regime = trade.get("regime")
        if regime is not None and str(regime).strip():
            regime_key = str(regime)
            pnl_by_regime[regime_key] = pnl_by_regime.get(regime_key, 0.0) + pnl

        exit_reason = trade.get("exit_reason")
        if exit_reason is not None and str(exit_reason).strip():
            reason_key = str(exit_reason)
            exit_reason_counts[reason_key] = exit_reason_counts.get(reason_key, 0) + 1
            pnl_by_exit_reason[reason_key] = pnl_by_exit_reason.get(reason_key, 0.0) + pnl

        entry_reason = trade.get("entry_reason")
        if entry_reason is not None and str(entry_reason).strip():
            entry_key = str(entry_reason)
            entry_reason_counts[entry_key] = entry_reason_counts.get(entry_key, 0) + 1

    return (
        pnl_by_side,
        pnl_by_instrument,
        pnl_by_regime,
        pnl_by_exit_reason,
        exit_reason_counts,
        entry_reason_counts,
    )


def derive_breakdown_registry_metrics_v1(
    trades: Sequence[Mapping[str, Any]],
    *,
    default_instrument_id: str = "UNKNOWN",
) -> dict[str, DerivedMetricResultV1]:
    owner = DERIVED_METRICS_OWNER
    source = f"{DERIVED_METRICS_OWNER}:derive_breakdown_registry_metrics_v1"
    formula = FORMULA_DERIVED_V1
    (
        _side,
        pnl_by_instrument,
        pnl_by_regime,
        _exit_pnl,
        _exit_counts,
        _entry_counts,
    ) = derive_trade_breakdowns_v1(trades, default_instrument_id=default_instrument_id)

    results: dict[str, DerivedMetricResultV1] = {}
    if trades:
        results["instrument_breakdown"] = _computed_result(
            metric_id="instrument_breakdown",
            value=float(len(pnl_by_instrument)),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(trades),
            status=MetricMaterializationStatus.RECONSTRUCTED,
            quality_flags=("INSTRUMENT_BUCKET_COUNT",),
        )
    else:
        results["instrument_breakdown"] = _status_result(
            metric_id="instrument_breakdown",
            status=MetricMaterializationStatus.INSUFFICIENT_DATA,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("NO_TRADES",),
            sample_count=0,
        )

    if pnl_by_regime:
        results["regime_breakdown"] = _computed_result(
            metric_id="regime_breakdown",
            value=float(len(pnl_by_regime)),
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(trades),
            status=MetricMaterializationStatus.RECONSTRUCTED,
            quality_flags=("REGIME_BUCKET_COUNT",),
        )
    else:
        results["regime_breakdown"] = _status_result(
            metric_id="regime_breakdown",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("REGIME_FIELD_NOT_AVAILABLE",),
            sample_count=len(trades),
        )
    return results


def derive_stage_conversion_rates_v1(
    stage_counts: Mapping[str, int],
) -> dict[str, float]:
    rates: dict[str, float] = {}
    ordered = list(FUNNEL_STAGE_ORDER)
    for index in range(1, len(ordered)):
        prior_stage = ordered[index - 1]
        stage = ordered[index]
        prior = int(stage_counts.get(prior_stage, 0))
        current = int(stage_counts.get(stage, 0))
        if prior > 0:
            rates[f"{prior_stage}->{stage}"] = current / prior
    return rates


def derive_funnel_conversion_metric_v1(
    funnel: DecisionFunnelPersistenceV0,
) -> DerivedMetricResultV1:
    owner = DECISION_FUNNEL_OWNER
    source = f"{DECISION_FUNNEL_OWNER}:derive_funnel_conversion_metric_v1"
    formula = FORMULA_FUNNEL_CONVERSION_V1
    if funnel.unavailable_stages:
        return _status_result(
            metric_id="conversion_rate_per_stage",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("FUNNEL_COUNTS_UNAVAILABLE",),
        )
    stage_counts = funnel.stage_counts
    rates = derive_stage_conversion_rates_v1(stage_counts)
    if not rates:
        return _status_result(
            metric_id="conversion_rate_per_stage",
            status=MetricMaterializationStatus.INSUFFICIENT_DATA,
            owner=owner,
            source=source,
            formula_version=formula,
            reason_codes=("NO_FUNNEL_STAGES",),
        )
    overall = rates.get("market_epochs_total->directional_candidate_count")
    if overall is None:
        market = int(stage_counts.get("market_epochs_total", 0))
        trades = int(stage_counts.get("trades_opened_count", 0))
        overall = (trades / market) if market > 0 else 0.0
    return _computed_result(
        metric_id="conversion_rate_per_stage",
        value=float(min(rates.values()) if rates else overall),
        owner=owner,
        source=source,
        formula_version=formula,
        sample_count=int(stage_counts.get("market_epochs_total", 0)),
        status=MetricMaterializationStatus.RECONSTRUCTED,
        quality_flags=("MIN_STAGE_CONVERSION_RATE",),
    )


def _max_consecutive_true(series: pd.Series) -> int:
    max_run = 0
    current = 0
    for value in series:
        if bool(value):
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run


def derive_drawdown_episode_metrics_v1(
    equity_curve: pd.Series,
) -> dict[str, DerivedMetricResultV1]:
    owner = DERIVED_METRICS_OWNER
    source = f"{DERIVED_METRICS_OWNER}:derive_drawdown_episode_metrics_v1"
    formula = FORMULA_DRAWDOWN_RECONSTRUCT_V1

    if equity_curve is None or len(equity_curve) < 2:
        missing = ("EQUITY_CURVE_INSUFFICIENT",)
        return {
            "drawdown_duration": _status_result(
                metric_id="drawdown_duration",
                status=MetricMaterializationStatus.INSUFFICIENT_DATA,
                owner=owner,
                source=source,
                formula_version=formula,
                reason_codes=missing,
            ),
            "recovery_duration": _status_result(
                metric_id="recovery_duration",
                status=MetricMaterializationStatus.INSUFFICIENT_DATA,
                owner=owner,
                source=source,
                formula_version=formula,
                reason_codes=missing,
            ),
        }

    dd = compute_drawdown(equity_curve.astype(float))
    in_drawdown = dd < 0
    max_dd_duration = float(_max_consecutive_true(in_drawdown))

    recovery_duration = 0.0
    if in_drawdown.any():
        trough_pos = int(dd.values.argmin())
        post = dd.iloc[trough_pos:]
        recovered = post[post >= -RECONCILIATION_TOLERANCE]
        if not recovered.empty:
            recovery_pos = equity_curve.index.get_loc(recovered.index[0])
            if isinstance(recovery_pos, slice):
                recovery_duration = float(
                    (recovery_pos.stop - 1 if recovery_pos.stop else trough_pos) - trough_pos
                )
            elif isinstance(recovery_pos, (list, pd.Index)):
                recovery_duration = float(int(recovery_pos[0]) - trough_pos)
            else:
                recovery_duration = float(int(recovery_pos) - trough_pos)
        else:
            recovery_duration = float(len(post) - 1)

    return {
        "drawdown_duration": _computed_result(
            metric_id="drawdown_duration",
            value=max_dd_duration,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(equity_curve),
            status=MetricMaterializationStatus.RECONSTRUCTED,
        ),
        "recovery_duration": _computed_result(
            metric_id="recovery_duration",
            value=recovery_duration,
            owner=owner,
            source=source,
            formula_version=formula,
            sample_count=len(equity_curve),
            status=MetricMaterializationStatus.RECONSTRUCTED,
        ),
    }


def derive_all_metrics_v1(
    *,
    trades: Sequence[Mapping[str, Any]],
    stats: Mapping[str, Any],
    gross_profit: float,
    gross_pnl: float,
    net_pnl: float,
    total_cost: float,
    effective_cost: Optional[EffectiveBacktestCostConfigV0] = None,
    spread_half_bps: Optional[float] = None,
    equity_curve: Optional[pd.Series] = None,
    funnel: Optional[DecisionFunnelPersistenceV0] = None,
    default_instrument_id: str = "UNKNOWN",
) -> DerivedMetricsBundleV1:
    trade_aggregates = derive_trade_aggregates_v1(trades, stats=stats)
    cost_ratios = derive_cost_ratio_metrics_v1(
        gross_profit=gross_profit,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        total_cost=total_cost,
        effective_cost=effective_cost,
        spread_half_bps=spread_half_bps,
    )
    breakdown_metrics = derive_breakdown_registry_metrics_v1(
        trades,
        default_instrument_id=default_instrument_id,
    )
    (
        pnl_by_side,
        pnl_by_instrument,
        pnl_by_regime,
        pnl_by_exit_reason,
        exit_reason_counts,
        entry_reason_counts,
    ) = derive_trade_breakdowns_v1(trades, default_instrument_id=default_instrument_id)

    drawdown_metrics: dict[str, DerivedMetricResultV1] = {}
    if equity_curve is not None:
        drawdown_metrics = derive_drawdown_episode_metrics_v1(equity_curve)

    funnel_metrics: dict[str, DerivedMetricResultV1] = {}
    if funnel is not None:
        funnel_metrics["conversion_rate_per_stage"] = derive_funnel_conversion_metric_v1(funnel)

    stage_conversion_rates = (
        derive_stage_conversion_rates_v1(funnel.stage_counts) if funnel is not None else {}
    )

    return DerivedMetricsBundleV1(
        trade_aggregates=trade_aggregates,
        cost_ratios=cost_ratios,
        drawdown_metrics=drawdown_metrics,
        funnel_metrics=funnel_metrics,
        breakdown_metrics=breakdown_metrics,
        pnl_by_side=pnl_by_side,
        pnl_by_instrument=pnl_by_instrument,
        pnl_by_regime=pnl_by_regime,
        pnl_by_exit_reason=pnl_by_exit_reason,
        exit_reason_counts=exit_reason_counts,
        entry_reason_counts=entry_reason_counts,
        stage_conversion_rates=stage_conversion_rates,
    )


def _result_to_metric_value(result: DerivedMetricResultV1, *, unit: str) -> MetricValueV1:
    return MetricValueV1(
        value=result.value,
        unit=unit,
        status=result.status,
        owner=result.owner,
        source=result.source,
        formula_version=result.formula_version,
        sample_count=result.sample_count,
        quality_flags=result.quality_flags,
        reason_codes=result.reason_codes,
    )


def _set_metric_from_result(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    entry: MetricRegistryEntryV1,
    result: DerivedMetricResultV1,
    *,
    overwrite: bool = False,
) -> bool:
    existing_status = snapshot.metric_statuses.get(entry.metric_id)
    if (
        not overwrite
        and existing_status == MetricMaterializationStatus.COMPUTED.value
        and result.status is not MetricMaterializationStatus.COMPUTED
    ):
        return False
    if entry.domain == "provenance":
        bucket = snapshot.provenance.setdefault("metrics", {})
    else:
        bucket = getattr(snapshot, entry.domain)
    bucket[entry.metric_id] = _result_to_metric_value(result, unit=entry.unit)
    snapshot.metric_statuses[entry.metric_id] = result.status.value
    return True


def bind_derived_metrics_to_snapshot_v1(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    bundle: DerivedMetricsBundleV1,
    *,
    registry: EconomicObservabilityMetricRegistryV1,
    prefer_stats_for: Optional[frozenset[str]] = None,
) -> DerivedMetricsSummaryV1:
    """Bind derived metric results onto snapshot buckets using registry domains."""
    prefer = prefer_stats_for or frozenset({"profit_factor_net", "expectancy_net"})
    computed = 0
    reconstructed = 0
    not_computed = 0
    not_applicable = 0
    insufficient = 0
    source_missing = 0

    merged: dict[str, DerivedMetricResultV1] = {}
    for bucket in (
        bundle.trade_aggregates,
        bundle.cost_ratios,
        bundle.drawdown_metrics,
        bundle.funnel_metrics,
        bundle.breakdown_metrics,
    ):
        merged.update(bucket)

    alias_to_result = {
        "profit_factor_net": merged.get("profit_factor_net_derived"),
        "expectancy_net": merged.get("expectancy_net_derived"),
    }

    for entry in registry.entries:
        result = merged.get(entry.metric_id)
        if result is None and entry.metric_id in alias_to_result:
            alias_result = alias_to_result[entry.metric_id]
            if alias_result is not None:
                result = alias_result
        if result is None or result.metric_id.startswith("_"):
            continue
        if (
            entry.metric_id in prefer
            and snapshot.metric_statuses.get(entry.metric_id) == "COMPUTED"
        ):
            continue
        overwrite = entry.metric_id not in prefer
        bound = _set_metric_from_result(snapshot, entry, result, overwrite=overwrite)
        if not bound:
            continue
        if result.status is MetricMaterializationStatus.COMPUTED:
            computed += 1
        elif result.status is MetricMaterializationStatus.RECONSTRUCTED:
            reconstructed += 1
        elif result.status is MetricMaterializationStatus.NOT_APPLICABLE:
            not_applicable += 1
        elif result.status is MetricMaterializationStatus.INSUFFICIENT_DATA:
            insufficient += 1
        elif result.status is MetricMaterializationStatus.SOURCE_MISSING:
            source_missing += 1
        else:
            not_computed += 1

    return DerivedMetricsSummaryV1(
        computed_metric_count=computed,
        reconstructed_metric_count=reconstructed,
        not_computed_metric_count=not_computed,
        not_applicable_metric_count=not_applicable,
        insufficient_data_metric_count=insufficient,
        source_missing_metric_count=source_missing,
    )


def validate_gross_cost_net_trade_reconciliation_v1(
    *,
    gross_profit: float,
    gross_loss: float,
    trade_gross_pnl: float,
    gross_pnl: float,
    net_pnl: float,
    total_cost: float,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> None:
    if abs((gross_profit + gross_loss) - trade_gross_pnl) > tolerance * max(
        1.0, abs(trade_gross_pnl)
    ):
        raise SnapshotContractError(
            "gross_profit_plus_gross_loss_reconciliation_failed:"
            f"profit={gross_profit}:loss={gross_loss}:trade_gross_pnl={trade_gross_pnl}"
        )
    if abs((gross_pnl - total_cost) - net_pnl) > tolerance * max(1.0, abs(net_pnl)):
        raise SnapshotContractError(
            "gross_minus_costs_reconciliation_failed:"
            f"gross_pnl={gross_pnl}:total_cost={total_cost}:net_pnl={net_pnl}"
        )


def validate_pnl_breakdown_reconciliation_v1(
    *,
    pnl_by_side: Mapping[str, float],
    pnl_by_instrument: Mapping[str, float],
    total_net_pnl: float,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> None:
    side_sum = float(sum(pnl_by_side.values()))
    instrument_sum = float(sum(pnl_by_instrument.values()))
    if abs(side_sum - total_net_pnl) > tolerance * max(1.0, abs(total_net_pnl)):
        raise SnapshotContractError(
            f"pnl_by_side_reconciliation_failed:side={side_sum}:total={total_net_pnl}"
        )
    if abs(instrument_sum - total_net_pnl) > tolerance * max(1.0, abs(total_net_pnl)):
        raise SnapshotContractError(
            f"pnl_by_instrument_reconciliation_failed:instrument={instrument_sum}:total={total_net_pnl}"
        )


def validate_exit_reason_counts_v1(
    *,
    exit_reason_counts: Mapping[str, int],
    trade_count: int,
) -> None:
    if sum(exit_reason_counts.values()) > trade_count:
        raise SnapshotContractError(
            "exit_reason_counts_exceed_trade_count:"
            f"counts={sum(exit_reason_counts.values())}:trades={trade_count}"
        )
