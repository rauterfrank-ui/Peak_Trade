"""Materialize canonical economic observability snapshots from existing stats/cost owners.

Rewires ``compute_backtest_stats``, ``append_cost_accounting_fields``, and deterministic
trade aggregates into ``CanonicalEconomicObservabilitySnapshotV1`` without introducing new
formula owners or runtime semantics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EffectiveBacktestCostConfigV0,
    append_cost_accounting_fields,
)
from src.backtest.economic_observability_registry_v1 import (
    EconomicObservabilityMetricRegistryV1,
    MetricRegistryEntryV1,
    get_canonical_metric_registry_v1,
)
from src.backtest.decision_funnel_v0 import (
    DECISION_FUNNEL_OWNER,
    DecisionFunnelPersistenceV0,
    materialize_decision_funnel_persistence_v0,
)
from src.backtest.economic_observability_advanced_capabilities_v1 import (
    ADVANCED_CAPABILITIES_OWNER,
    AdvancedCapabilitiesInputsV1,
    advanced_capability_artifact_payloads_v1,
    bind_advanced_capabilities_to_snapshot_v1,
    materialize_advanced_economic_capabilities_v1,
)
from src.backtest.economic_observability_derived_metrics_v1 import (
    DERIVED_METRICS_OWNER,
    bind_derived_metrics_to_snapshot_v1,
    derive_all_metrics_v1,
    validate_gross_cost_net_trade_reconciliation_v1,
    validate_pnl_breakdown_reconciliation_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    SNAPSHOT_OWNER,
    CanonicalEconomicObservabilitySnapshotV1,
    MetricMaterializationStatus,
    MetricValueV1,
    REASON_REQUIRED_STATUSES,
    SnapshotContractError,
    compute_snapshot_digest,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.backtest.trade_ledger_equity_curve_persistence_v0 import (
    TRADE_LEDGER_OWNER,
    CanonicalObservabilityBundleV0,
    DrawdownCurveStatus,
    EquityCurvePersistenceV0,
    materialize_drawdown_curve_v0,
    materialize_equity_curve_rows_v0,
    materialize_trade_ledger_rows_v0,
    serialize_drawdown_curve_csv,
    serialize_equity_curve_csv,
    serialize_trade_ledger_jsonl,
    validate_drawdown_reconciliation_v0,
    validate_equity_final_value_reconciliation_v0,
    validate_trade_ledger_reconciliation_v0,
)
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    FUNNEL_OWNER as RESEARCH_FUNNEL_OWNER,
    RUNBOOK_FUNNEL_FIELDS,
)

STATS_OWNER = "backtest.stats"
COST_OWNER = "backtest.cost_config_v0"
ENGINE_OWNER = "backtest.engine"
FUNDING_OWNER = "backtest.funding_model_v1"
MATERIALIZATION_OWNER = "backtest.economic_observability_materialization_v1"
CANONICAL_DERIVED_METRICS_OWNER = DERIVED_METRICS_OWNER
FORMULA_STATS_V0 = "compute_backtest_stats_v0"
FORMULA_COST_V0 = "append_cost_accounting_fields_v0"
FORMULA_ENGINE_AGGREGATE_V0 = "engine_trade_aggregate_v0"

RECONCILIATION_TOLERANCE = 1e-9

# Registry metric_id -> stats dict key produced by compute_backtest_stats / engine stats merge.
_STATS_FIELD_BY_METRIC_ID: dict[str, str] = {
    "annualized_return": "cagr",
    "average_winner": "avg_win",
    "average_loser": "avg_loss",
    "calmar": "calmar",
    "expectancy_net": "expectancy",
    "expectancy_per_trade": "expectancy",
    "max_drawdown_percent": "max_drawdown",
    "profit_factor_net": "profit_factor",
    "sharpe": "sharpe",
    "sortino": "sortino",
    "trade_count": "total_trades",
    "win_rate": "win_rate",
    "losing_trade_count": "losing_trades",
    "profitable_trade_count": "winning_trades",
    "net_return": "net_return",
    "gross_return": "gross_return",
    "fee_drag": "fee_drag",
    "slippage_drag": "slippage_impact",
    "total_fees": "total_fees",
}

# Scope aliases used in operator contracts -> canonical registry metric_id.
SCOPE_METRIC_ALIASES: dict[str, str] = {
    "total_trades": "trade_count",
    "winning_trades": "profitable_trade_count",
    "losing_trades": "losing_trade_count",
    "breakeven_trades": "flat_trade_count",
    "profit_factor_net": "profit_factor_net",
    "expectancy_net": "expectancy_net",
    "avg_win": "average_winner",
    "avg_loss": "average_loser",
    "median_trade_pnl": "median_winner",
    "best_trade": "largest_winner",
}


class ReconciliationError(SnapshotContractError):
    """Raised when gross/net/cost reconciliation fails closed."""


@dataclass(frozen=True)
class BacktestObservabilityInputsV1:
    stats: Mapping[str, Any]
    initial_equity: float
    trades: Optional[Sequence[Mapping[str, Any]]] = None
    effective_cost: Optional[EffectiveBacktestCostConfigV0] = None
    total_notional: float = 0.0
    funding_drag: Optional[float] = None
    funding_bound: bool = False
    spread_half_bps: Optional[float] = None
    equity_curve: Optional[pd.Series] = None
    drawdown_curve: Optional[pd.Series] = None
    instrument_id: str = "UNKNOWN"
    run_id: str = "offline-run-v0"
    strategy_ref: Optional[str] = None
    funnel_counts: Optional[Mapping[str, int]] = None
    block_reason_counts: Optional[Mapping[str, int]] = None
    offline_market_volume: Optional[float] = None


@dataclass(frozen=True)
class MaterializationSummaryV1:
    bound_stats_field_count: int
    bound_cost_field_count: int
    unresolved_stats_field_count: int
    unresolved_cost_field_count: int
    gross_net_alias_removed: bool
    cost_component_double_counting: bool
    gross_cost_net_reconciliation_pass: bool
    reconciliation_tolerance: float


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _is_numeric_value(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        numeric = float(value)
        return math.isfinite(numeric) or numeric in {float("inf"), float("-inf")}
    return False


def _computed_metric(
    *,
    value: float,
    unit: str,
    owner: str,
    source: str,
    formula_version: str,
    sample_count: Optional[int] = None,
    quality_flags: tuple[str, ...] = (),
) -> MetricValueV1:
    return MetricValueV1(
        value=float(value),
        unit=unit,
        status=MetricMaterializationStatus.COMPUTED,
        owner=owner,
        source=source,
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=quality_flags,
        reason_codes=(),
    )


def _status_metric(
    *,
    unit: str,
    status: MetricMaterializationStatus,
    owner: str,
    source: str,
    formula_version: str,
    reason_codes: tuple[str, ...],
    sample_count: Optional[int] = None,
) -> MetricValueV1:
    if status in REASON_REQUIRED_STATUSES and not reason_codes:
        raise SnapshotContractError(f"status {status.value} requires reason_codes")
    return MetricValueV1(
        value=None,
        unit=unit,
        status=status,
        owner=owner,
        source=source,
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=(),
        reason_codes=reason_codes,
    )


def ensure_cost_accounting_stats(
    stats: Mapping[str, Any],
    *,
    initial_equity: float,
    effective_cost: EffectiveBacktestCostConfigV0,
    total_fees: float = 0.0,
    total_notional: float = 0.0,
) -> dict[str, Any]:
    """Reuse append_cost_accounting_fields as the sole cost decomposition owner."""
    return append_cost_accounting_fields(
        dict(stats),
        initial_equity=initial_equity,
        effective_cost=effective_cost,
        total_fees=total_fees,
        total_notional=total_notional,
    )


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


def _aggregate_trade_metrics(trades: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    pnls = _trade_pnls(trades)
    gross_pnls = _trade_gross_pnls(trades)
    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p < 0]
    flats = [p for p in pnls if p == 0]
    gross_winners = [p for p in gross_pnls if p > 0]
    gross_losers = [p for p in gross_pnls if p < 0]
    gross_profit = sum(gross_winners) if gross_winners else 0.0
    gross_loss = sum(gross_losers) if gross_losers else 0.0
    entry_fees = sum(float(t.get("entry_cost", 0.0) or 0.0) for t in trades)
    exit_fees = sum(float(t.get("exit_cost", 0.0) or 0.0) for t in trades)
    max_win = max(pnls) if pnls else 0.0
    min_loss = min(pnls) if pnls else 0.0
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
    median_winner = float(sorted(winners)[len(winners) // 2]) if winners else 0.0
    median_loser = float(sorted(losers)[len(losers) // 2]) if losers else 0.0
    payoff_ratio = (
        (abs(sum(winners) / len(winners)) / abs(sum(losers) / len(losers)))
        if (winners and losers and sum(losers) != 0)
        else 0.0
    )
    return {
        "gross_pnl": float(sum(gross_pnls)),
        "net_pnl": float(sum(pnls)),
        "gross_profit": float(gross_profit),
        "gross_loss": float(gross_loss),
        "flat_trade_count": float(len(flats)),
        "largest_winner": float(max_win),
        "largest_loser": float(min_loss),
        "consecutive_wins": float(max_consecutive_wins),
        "consecutive_losses": float(max_consecutive_losses),
        "median_winner": median_winner,
        "median_loser": median_loser,
        "payoff_ratio": float(payoff_ratio),
        "entry_fees": float(entry_fees),
        "exit_fees": float(exit_fees),
        "loss_rate": float(len(losers) / len(pnls)) if pnls else 0.0,
    }


def _derive_equity_economics(
    stats: Mapping[str, Any],
    *,
    initial_equity: float,
) -> dict[str, float]:
    net_return = float(stats.get("net_return", stats.get("total_return", 0.0)))
    gross_return = float(stats.get("gross_return", net_return))
    final_equity = initial_equity * (1.0 + net_return)
    net_pnl = final_equity - initial_equity
    gross_pnl = initial_equity * gross_return
    return {
        "final_equity": final_equity,
        "net_pnl": net_pnl,
        "gross_pnl": gross_pnl,
        "net_return": net_return,
        "gross_return": gross_return,
    }


def _derive_cost_components(
    stats: Mapping[str, Any],
    *,
    initial_equity: float,
    inputs: BacktestObservabilityInputsV1,
) -> dict[str, Any]:
    fee_drag = float(stats.get("fee_drag", 0.0))
    slippage_drag = float(stats.get("slippage_impact", stats.get("slippage_drag", 0.0)))
    total_fees = float(stats.get("total_fees", fee_drag * initial_equity))
    total_slippage = slippage_drag * initial_equity
    spread_drag: Optional[float] = None
    spread_cost_abs = 0.0
    if inputs.spread_half_bps is not None and inputs.total_notional > 0:
        spread_cost_abs = inputs.total_notional * (2.0 * inputs.spread_half_bps) / 10000.0
        spread_drag = spread_cost_abs / initial_equity if initial_equity > 0 else 0.0
    total_cost_drag = fee_drag + slippage_drag + (spread_drag or 0.0)
    # Return-level decomposition is authoritative for economic reconciliation.
    total_cost_abs = initial_equity * total_cost_drag if initial_equity > 0 else 0.0
    roundtrip_cost_bps = None
    if inputs.effective_cost is not None:
        roundtrip_cost_bps = (
            2.0 * inputs.effective_cost.taker_fee_bps
            + 2.0 * inputs.effective_cost.entry_slippage_bps
            + (2.0 * inputs.spread_half_bps if inputs.spread_half_bps is not None else 0.0)
        )
    return {
        "fee_drag": fee_drag,
        "slippage_drag": slippage_drag,
        "spread_drag": spread_drag,
        "spread_cost": spread_cost_abs,
        "total_slippage": total_slippage,
        "total_cost": total_cost_abs,
        "total_cost_drag": total_cost_drag,
        "total_fees": total_fees,
        "roundtrip_cost_bps": roundtrip_cost_bps,
        "realized_cost_bps": (
            (total_cost_abs / inputs.total_notional) * 10000.0
            if inputs.total_notional > 0
            else None
        ),
    }


def validate_gross_net_cost_reconciliation_v1(
    *,
    initial_equity: float,
    stats: Mapping[str, Any],
    derived: Mapping[str, Any],
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> None:
    net_return = float(stats.get("net_return", stats.get("total_return", 0.0)))
    gross_return = float(stats.get("gross_return", net_return))
    fee_drag = float(stats.get("fee_drag", 0.0))
    slippage_drag = float(stats.get("slippage_impact", stats.get("slippage_drag", 0.0)))
    spread_drag = derived.get("spread_drag")
    spread_component = float(spread_drag) if spread_drag is not None else 0.0
    return_residual = gross_return - fee_drag - slippage_drag - spread_component - net_return
    if abs(return_residual) > tolerance:
        raise ReconciliationError(
            "return_reconciliation_failed:"
            f"gross={gross_return}:fee={fee_drag}:slippage={slippage_drag}:"
            f"spread={spread_component}:net={net_return}:residual={return_residual}"
        )
    gross_pnl = float(derived.get("gross_pnl", initial_equity * gross_return))
    net_pnl = float(derived.get("net_pnl", initial_equity * net_return))
    total_cost = float(
        derived.get("total_cost", initial_equity * (fee_drag + slippage_drag + spread_component))
    )
    pnl_residual = gross_pnl - total_cost - net_pnl
    if abs(pnl_residual) > tolerance * max(1.0, abs(initial_equity)):
        raise ReconciliationError(
            "pnl_reconciliation_failed:"
            f"gross_pnl={gross_pnl}:total_cost={total_cost}:net_pnl={net_pnl}:residual={pnl_residual}"
        )


def _set_metric(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    entry: MetricRegistryEntryV1,
    metric: MetricValueV1,
) -> None:
    if entry.domain == "provenance":
        bucket = snapshot.provenance.setdefault("metrics", {})
    else:
        bucket = getattr(snapshot, entry.domain)
    bucket[entry.metric_id] = metric
    snapshot.metric_statuses[entry.metric_id] = metric.status.value


def _bind_stats_metric(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    entry: MetricRegistryEntryV1,
    stats: Mapping[str, Any],
    *,
    sample_count: Optional[int],
) -> bool:
    stats_key = _STATS_FIELD_BY_METRIC_ID.get(entry.metric_id)
    if stats_key is None:
        return False
    raw = stats.get(stats_key)
    if not _is_numeric_value(raw):
        return False
    owner = entry.canonical_owner
    formula = FORMULA_STATS_V0 if owner == STATS_OWNER else FORMULA_COST_V0
    if entry.metric_id in {"fee_drag", "slippage_drag", "gross_return", "net_return", "total_fees"}:
        formula = FORMULA_COST_V0
        owner = (
            COST_OWNER
            if entry.metric_id != "gross_return" and entry.metric_id != "net_return"
            else owner
        )
    _set_metric(
        snapshot,
        entry,
        _computed_metric(
            value=float(raw),
            unit=entry.unit,
            owner=owner,
            source=entry.source_field_or_formula,
            formula_version=formula,
            sample_count=sample_count,
        ),
    )
    return True


def _bind_derived_metric(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    entry: MetricRegistryEntryV1,
    value: float,
    *,
    owner: str,
    source: str,
    formula_version: str,
    sample_count: Optional[int] = None,
) -> None:
    _set_metric(
        snapshot,
        entry,
        _computed_metric(
            value=value,
            unit=entry.unit,
            owner=owner,
            source=source,
            formula_version=formula_version,
            sample_count=sample_count,
        ),
    )


def materialize_snapshot_from_backtest_stats_v1(
    inputs: BacktestObservabilityInputsV1,
    *,
    registry: EconomicObservabilityMetricRegistryV1 | None = None,
    run_identity: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
    validate_reconciliation: bool = True,
) -> tuple[CanonicalEconomicObservabilitySnapshotV1, MaterializationSummaryV1]:
    """Materialize a registry-complete snapshot from existing stats/cost owners."""
    resolved_registry = registry or get_canonical_metric_registry_v1()
    stats = dict(inputs.stats)
    if inputs.effective_cost is not None and "gross_return" not in stats:
        stats = ensure_cost_accounting_stats(
            stats,
            initial_equity=inputs.initial_equity,
            effective_cost=inputs.effective_cost,
            total_fees=float(stats.get("total_fees", 0.0)),
            total_notional=inputs.total_notional,
        )

    equity_derived = _derive_equity_economics(stats, initial_equity=inputs.initial_equity)
    cost_derived = _derive_cost_components(
        stats, initial_equity=inputs.initial_equity, inputs=inputs
    )
    trade_derived: dict[str, float] = {}
    trade_sample_count: Optional[int] = None
    if inputs.trades:
        trade_derived = _aggregate_trade_metrics(inputs.trades)
        trade_sample_count = len(inputs.trades)

    if validate_reconciliation:
        validate_gross_net_cost_reconciliation_v1(
            initial_equity=inputs.initial_equity,
            stats=stats,
            derived={**equity_derived, **cost_derived},
        )

    snapshot = materialize_empty_snapshot_v1(
        registry=resolved_registry,
        run_identity={
            **dict(run_identity or {}),
            "snapshot_owner": SNAPSHOT_OWNER,
            "materialization_owner": MATERIALIZATION_OWNER,
        },
        source_refs=list(source_refs or []),
    )

    sample_count = trade_sample_count
    if sample_count is None and _is_finite_number(stats.get("total_trades")):
        sample_count = int(stats["total_trades"])

    bound_stats = 0
    bound_cost = 0
    for entry in resolved_registry.entries:
        if _bind_stats_metric(snapshot, entry, stats, sample_count=sample_count):
            if entry.domain in {"economic", "strategy_quality", "risk", "trade_analytics"}:
                bound_stats += 1
            if entry.domain == "costs":
                bound_cost += 1
            continue

        if entry.metric_id == "final_equity":
            _bind_derived_metric(
                snapshot,
                entry,
                equity_derived["final_equity"],
                owner=ENGINE_OWNER,
                source="backtest.engine:final_equity",
                formula_version=FORMULA_ENGINE_AGGREGATE_V0,
                sample_count=1,
            )
            bound_stats += 1
            continue
        if entry.metric_id == "gross_pnl":
            _bind_derived_metric(
                snapshot,
                entry,
                equity_derived["gross_pnl"],
                owner=ENGINE_OWNER,
                source="backtest.engine:gross_pnl",
                formula_version=FORMULA_ENGINE_AGGREGATE_V0,
                sample_count=sample_count,
            )
            bound_stats += 1
            continue
        if entry.metric_id == "net_pnl":
            _bind_derived_metric(
                snapshot,
                entry,
                equity_derived["net_pnl"],
                owner=ENGINE_OWNER,
                source="backtest.engine:net_pnl",
                formula_version=FORMULA_ENGINE_AGGREGATE_V0,
                sample_count=sample_count,
            )
            bound_stats += 1
            continue

        trade_value = trade_derived.get(entry.metric_id)
        if trade_value is not None and _is_finite_number(trade_value):
            _bind_derived_metric(
                snapshot,
                entry,
                float(trade_value),
                owner=entry.canonical_owner,
                source=entry.source_field_or_formula,
                formula_version=FORMULA_ENGINE_AGGREGATE_V0,
                sample_count=sample_count,
            )
            bound_stats += 1
            continue

        cost_value = cost_derived.get(entry.metric_id)
        if cost_value is not None and _is_finite_number(cost_value):
            _bind_derived_metric(
                snapshot,
                entry,
                float(cost_value),
                owner=COST_OWNER,
                source=f"backtest.cost_config_v0:{entry.metric_id}",
                formula_version=FORMULA_COST_V0,
                sample_count=sample_count,
            )
            bound_cost += 1
            continue

        if entry.metric_id == "spread_drag":
            if inputs.spread_half_bps is None:
                _set_metric(
                    snapshot,
                    entry,
                    _status_metric(
                        unit=entry.unit,
                        status=MetricMaterializationStatus.NOT_APPLICABLE,
                        owner=COST_OWNER,
                        source=entry.source_field_or_formula,
                        formula_version=FORMULA_COST_V0,
                        reason_codes=("SPREAD_NOT_BOUND_IN_STANDARD_PATH",),
                    ),
                )
            continue

        if entry.metric_id == "funding_drag":
            if inputs.funding_bound and inputs.funding_drag is not None:
                _bind_derived_metric(
                    snapshot,
                    entry,
                    float(inputs.funding_drag),
                    owner=FUNDING_OWNER,
                    source="backtest.funding_model_v1:funding_drag",
                    formula_version="compute_funding_drag_v1",
                    sample_count=sample_count,
                )
                bound_cost += 1
            else:
                funding_status_raw = stats.get("funding_drag_or_status")
                reason = ("FUNDING_NOT_BOUND_IN_OFFLINE_PATH",)
                status = MetricMaterializationStatus.SOURCE_MISSING
                if funding_status_raw == "NOT_BOUND":
                    status = MetricMaterializationStatus.NOT_APPLICABLE
                    reason = ("FUNDING_MODEL_NOT_BOUND",)
                _set_metric(
                    snapshot,
                    entry,
                    _status_metric(
                        unit=entry.unit,
                        status=status,
                        owner=FUNDING_OWNER,
                        source=entry.source_field_or_formula,
                        formula_version="compute_funding_drag_v1",
                        reason_codes=reason,
                    ),
                )
            continue

        if (
            entry.metric_id in {"total_cost", "total_cost_drag", "total_cost_bps"}
            and cost_derived.get("total_cost", 0.0) == 0.0
            and float(stats.get("fee_drag", 0.0)) == 0.0
        ):
            # Zero cost is valid when explicitly zero — materialize as 0 if net path used zero fees.
            if entry.metric_id == "total_cost":
                _bind_derived_metric(
                    snapshot,
                    entry,
                    0.0,
                    owner=COST_OWNER,
                    source=entry.source_field_or_formula,
                    formula_version=FORMULA_COST_V0,
                    sample_count=sample_count,
                )
                bound_cost += 1

    gross_return_metric = snapshot.economic.get("gross_return") or snapshot.economic.get(
        "net_return"
    )
    net_return_metric = snapshot.economic.get("net_return")
    gross_net_alias_removed = bool(
        gross_return_metric
        and net_return_metric
        and gross_return_metric.status is MetricMaterializationStatus.COMPUTED
        and net_return_metric.status is MetricMaterializationStatus.COMPUTED
        and (
            gross_return_metric.value != net_return_metric.value
            or (
                float(stats.get("fee_drag", 0.0)) == 0.0
                and float(stats.get("slippage_impact", 0.0)) == 0.0
            )
        )
    )

    trades = list(inputs.trades or [])
    if trades:
        derived_bundle = derive_all_metrics_v1(
            trades=trades,
            stats=stats,
            gross_profit=float(trade_derived.get("gross_profit", 0.0)),
            gross_pnl=float(equity_derived["gross_pnl"]),
            net_pnl=float(equity_derived["net_pnl"]),
            total_cost=float(cost_derived.get("total_cost", 0.0)),
            effective_cost=inputs.effective_cost,
            spread_half_bps=inputs.spread_half_bps,
            equity_curve=inputs.equity_curve,
            default_instrument_id=inputs.instrument_id,
        )
        gross_profit_value = float(derived_bundle.trade_aggregates["gross_profit"].value or 0.0)
        gross_loss_value = float(derived_bundle.trade_aggregates["gross_loss"].value or 0.0)
        trade_gross_pnl = float(trade_derived.get("gross_pnl", 0.0))
        validate_gross_cost_net_trade_reconciliation_v1(
            gross_profit=gross_profit_value,
            gross_loss=gross_loss_value,
            trade_gross_pnl=trade_gross_pnl,
            gross_pnl=float(equity_derived["gross_pnl"]),
            net_pnl=float(equity_derived["net_pnl"]),
            total_cost=float(cost_derived.get("total_cost", 0.0)),
        )
        if derived_bundle.pnl_by_side and "unknown" not in derived_bundle.pnl_by_side:
            validate_pnl_breakdown_reconciliation_v1(
                pnl_by_side=derived_bundle.pnl_by_side,
                pnl_by_instrument=derived_bundle.pnl_by_instrument,
                total_net_pnl=float(sum(float(trade["pnl"]) for trade in trades)),
            )
        bind_derived_metrics_to_snapshot_v1(
            snapshot,
            derived_bundle,
            registry=resolved_registry,
        )

    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)

    stats_domains = {"economic", "strategy_quality", "risk", "trade_analytics"}
    unresolved_stats = sum(
        1
        for entry in resolved_registry.entries
        if entry.domain in stats_domains
        and snapshot.metric_statuses.get(entry.metric_id)
        in {s.value for s in REASON_REQUIRED_STATUSES}
    )
    unresolved_cost = sum(
        1
        for entry in resolved_registry.entries
        if entry.domain == "costs"
        and snapshot.metric_statuses.get(entry.metric_id)
        in {s.value for s in REASON_REQUIRED_STATUSES}
    )

    summary = MaterializationSummaryV1(
        bound_stats_field_count=bound_stats,
        bound_cost_field_count=bound_cost,
        unresolved_stats_field_count=unresolved_stats,
        unresolved_cost_field_count=unresolved_cost,
        gross_net_alias_removed=gross_net_alias_removed,
        cost_component_double_counting=False,
        gross_cost_net_reconciliation_pass=True,
        reconciliation_tolerance=RECONCILIATION_TOLERANCE,
    )
    return snapshot, summary


def project_legacy_economic_evidence_metrics_v1(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
) -> dict[str, Optional[float]]:
    """Compatibility projection for legacy economic evidence consumers."""

    def _value(metric_id: str) -> Optional[float]:
        for domain in (
            snapshot.economic,
            snapshot.costs,
            snapshot.strategy_quality,
            snapshot.risk,
            snapshot.trade_analytics,
        ):
            metric = domain.get(metric_id)
            if metric is not None and metric.status is MetricMaterializationStatus.COMPUTED:
                return metric.value
        return None

    return {
        "gross_return": _value("gross_return"),
        "net_return": _value("net_return"),
        "fee_drag": _value("fee_drag"),
        "slippage_impact": _value("slippage_drag"),
        "profit_factor": _value("profit_factor_net"),
        "expectancy": _value("expectancy_net"),
        "sharpe": _value("sharpe"),
        "sortino": _value("sortino"),
        "max_drawdown": _value("max_drawdown_percent"),
        "calmar": _value("calmar"),
    }


def existing_stats_field_keys_v0() -> tuple[str, ...]:
    return (
        "total_return",
        "cagr",
        "max_drawdown",
        "sharpe",
        "sortino",
        "calmar",
        "ulcer_index",
        "recovery_factor",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "profit_factor",
        "avg_win",
        "avg_loss",
        "expectancy",
        "gross_return",
        "net_return",
        "fee_drag",
        "slippage_impact",
    )


def existing_cost_field_keys_v0() -> tuple[str, ...]:
    return (
        "gross_return",
        "net_return",
        "fee_drag",
        "slippage_impact",
        "funding_drag_or_status",
    )


_FUNNEL_METRIC_IDS: frozenset[str] = frozenset(RUNBOOK_FUNNEL_FIELDS)


def _bind_funnel_metrics_v1(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    *,
    funnel: DecisionFunnelPersistenceV0,
    registry: EconomicObservabilityMetricRegistryV1,
) -> None:
    for entry in registry.entries:
        if entry.metric_id not in _FUNNEL_METRIC_IDS:
            continue
        if entry.metric_id in funnel.unavailable_stages:
            snapshot.decision_funnel[entry.metric_id] = _status_metric(
                unit=entry.unit,
                status=MetricMaterializationStatus.SOURCE_MISSING,
                owner=RESEARCH_FUNNEL_OWNER,
                source=entry.source_field_or_formula,
                formula_version="decision_funnel_persistence_v0",
                reason_codes=(funnel.unavailable_stages[entry.metric_id],),
            )
            snapshot.metric_statuses[entry.metric_id] = (
                MetricMaterializationStatus.SOURCE_MISSING.value
            )
            continue
        value = float(funnel.stage_counts.get(entry.metric_id, 0))
        snapshot.decision_funnel[entry.metric_id] = _computed_metric(
            value=value,
            unit=entry.unit,
            owner=RESEARCH_FUNNEL_OWNER,
            source=entry.source_field_or_formula,
            formula_version="decision_funnel_persistence_v0",
            sample_count=int(funnel.stage_counts.get("market_epochs_total", 0)),
        )
        snapshot.metric_statuses[entry.metric_id] = MetricMaterializationStatus.COMPUTED.value

    for metric_id, source, owner in (
        ("top_block_reasons", f"{RESEARCH_FUNNEL_OWNER}:top_block_reasons", RESEARCH_FUNNEL_OWNER),
        (
            "zero_trade_causal_classification",
            f"{RESEARCH_FUNNEL_OWNER}:zero_trade_causal_classification",
            RESEARCH_FUNNEL_OWNER,
        ),
    ):
        entry = next((item for item in registry.entries if item.metric_id == metric_id), None)
        if entry is None:
            continue
        if metric_id == "top_block_reasons":
            if funnel.top_block_reasons:
                snapshot.decision_funnel[metric_id] = _computed_metric(
                    value=float(len(funnel.top_block_reasons)),
                    unit=entry.unit,
                    owner=owner,
                    source=source,
                    formula_version="decision_funnel_persistence_v0",
                )
            else:
                snapshot.decision_funnel[metric_id] = _status_metric(
                    unit=entry.unit,
                    status=MetricMaterializationStatus.SOURCE_MISSING,
                    owner=owner,
                    source=source,
                    formula_version="decision_funnel_persistence_v0",
                    reason_codes=("NO_BLOCK_REASONS",),
                )
        else:
            zero_status = funnel.zero_trade_causal_classification.get("status")
            if zero_status == MetricMaterializationStatus.COMPUTED.value:
                snapshot.decision_funnel[metric_id] = _computed_metric(
                    value=1.0,
                    unit=entry.unit,
                    owner=owner,
                    source=source,
                    formula_version="decision_funnel_persistence_v0",
                )
            elif zero_status == MetricMaterializationStatus.NOT_APPLICABLE.value:
                snapshot.decision_funnel[metric_id] = _status_metric(
                    unit=entry.unit,
                    status=MetricMaterializationStatus.NOT_APPLICABLE,
                    owner=owner,
                    source=source,
                    formula_version="decision_funnel_persistence_v0",
                    reason_codes=tuple(
                        funnel.zero_trade_causal_classification.get("reason_codes", ())
                    ),
                )
            else:
                snapshot.decision_funnel[metric_id] = _status_metric(
                    unit=entry.unit,
                    status=MetricMaterializationStatus.SOURCE_MISSING,
                    owner=owner,
                    source=source,
                    formula_version="decision_funnel_persistence_v0",
                    reason_codes=tuple(
                        funnel.zero_trade_causal_classification.get(
                            "reason_codes", ("FUNNEL_UNAVAILABLE",)
                        )
                    ),
                )
        snapshot.metric_statuses[metric_id] = snapshot.decision_funnel[metric_id].status.value


def _metric_numeric_value(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    domain: str,
    metric_id: str,
    default: float = 0.0,
) -> float:
    bucket = getattr(snapshot, domain)
    metric = bucket.get(metric_id)
    if metric is not None and metric.value is not None:
        return float(metric.value)
    return default


def materialize_observability_bundle_v1(
    inputs: BacktestObservabilityInputsV1,
    *,
    registry: EconomicObservabilityMetricRegistryV1 | None = None,
    run_identity: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
    validate_reconciliation: bool = True,
    final_report: str = "",
) -> tuple[CanonicalObservabilityBundleV0, MaterializationSummaryV1]:
    """Materialize snapshot plus deterministic offline observability bundle artifacts."""
    resolved_registry = registry or get_canonical_metric_registry_v1()
    snapshot, summary = materialize_snapshot_from_backtest_stats_v1(
        inputs,
        registry=resolved_registry,
        run_identity=run_identity,
        source_refs=source_refs,
        validate_reconciliation=validate_reconciliation,
    )

    funnel = materialize_decision_funnel_persistence_v0(
        funnel_counts=inputs.funnel_counts,
        block_reason_counts=inputs.block_reason_counts,
    )
    _bind_funnel_metrics_v1(snapshot, funnel=funnel, registry=resolved_registry)
    trades = list(inputs.trades or [])
    derived_bundle = None
    advanced_payloads: dict[str, dict[str, Any]] = {}
    if trades:
        trade_agg = _aggregate_trade_metrics(trades)
        derived_bundle = derive_all_metrics_v1(
            trades=trades,
            stats=dict(inputs.stats),
            gross_profit=float(trade_agg.get("gross_profit", 0.0)),
            gross_pnl=_metric_numeric_value(snapshot, "economic", "gross_pnl"),
            net_pnl=_metric_numeric_value(snapshot, "economic", "net_pnl"),
            total_cost=_metric_numeric_value(snapshot, "costs", "total_cost"),
            effective_cost=inputs.effective_cost,
            spread_half_bps=inputs.spread_half_bps,
            equity_curve=inputs.equity_curve,
            funnel=funnel,
            default_instrument_id=inputs.instrument_id,
        )
        bind_derived_metrics_to_snapshot_v1(
            snapshot,
            derived_bundle,
            registry=resolved_registry,
        )
        advanced_inputs = AdvancedCapabilitiesInputsV1(
            trades=trades,
            stats=dict(inputs.stats),
            gross_profit=float(trade_agg.get("gross_profit", 0.0)),
            gross_pnl=_metric_numeric_value(snapshot, "economic", "gross_pnl"),
            net_pnl=_metric_numeric_value(snapshot, "economic", "net_pnl"),
            total_cost=_metric_numeric_value(snapshot, "costs", "total_cost"),
            initial_equity=inputs.initial_equity,
            total_notional=inputs.total_notional,
            effective_cost=inputs.effective_cost,
            spread_half_bps=inputs.spread_half_bps,
            equity_curve=inputs.equity_curve,
            offline_market_volume=inputs.offline_market_volume,
            derived_bundle=derived_bundle,
        )
        advanced_bundle = materialize_advanced_economic_capabilities_v1(advanced_inputs)
        bind_advanced_capabilities_to_snapshot_v1(
            snapshot,
            advanced_bundle,
            registry=resolved_registry,
        )
        advanced_payloads = advanced_capability_artifact_payloads_v1(advanced_bundle)
    else:
        empty_advanced = materialize_advanced_economic_capabilities_v1(
            AdvancedCapabilitiesInputsV1(
                trades=[],
                stats=dict(inputs.stats),
                gross_profit=0.0,
                gross_pnl=0.0,
                net_pnl=0.0,
                total_cost=0.0,
                initial_equity=inputs.initial_equity,
                total_notional=inputs.total_notional,
                effective_cost=inputs.effective_cost,
                spread_half_bps=inputs.spread_half_bps,
                offline_market_volume=inputs.offline_market_volume,
            )
        )
        advanced_payloads = advanced_capability_artifact_payloads_v1(empty_advanced)
    snapshot_payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(snapshot_payload)
    snapshot_payload["manifest_digest"] = snapshot.manifest_digest

    trades = list(inputs.trades or [])
    trade_rows = materialize_trade_ledger_rows_v0(
        trades,
        instrument_id=inputs.instrument_id,
        run_id=inputs.run_id,
        strategy_ref=inputs.strategy_ref,
    )
    trade_ledger_jsonl = serialize_trade_ledger_jsonl(trade_rows)

    equity_series = (
        inputs.equity_curve if inputs.equity_curve is not None else pd.Series(dtype=float)
    )
    equity_rows = materialize_equity_curve_rows_v0(equity_series)
    equity_curve_csv = serialize_equity_curve_csv(equity_rows)
    equity_persistence = EquityCurvePersistenceV0(
        owner=TRADE_LEDGER_OWNER,
        point_count=len(equity_rows),
        final_value=float(equity_rows[-1]["equity"]) if equity_rows else 0.0,
        rows=equity_rows,
    )

    drawdown = materialize_drawdown_curve_v0(
        equity_curve=equity_series,
        drawdown_curve=inputs.drawdown_curve,
    )
    drawdown_not_applicable_payload: Optional[dict[str, Any]] = None
    drawdown_curve_csv = ""
    if drawdown.status is DrawdownCurveStatus.SOURCE_MISSING and drawdown.point_count == 0:
        drawdown_not_applicable_payload = {
            "status": drawdown.status.value,
            "reason_codes": list(drawdown.reason_codes),
            "owner": drawdown.owner,
        }
    else:
        drawdown_curve_csv = serialize_drawdown_curve_csv(drawdown.rows)
        if equity_series is not None and not equity_series.empty:
            validate_drawdown_reconciliation_v0(equity_curve=equity_series, drawdown=drawdown)

    canonical_trade_count = int(
        snapshot.trade_analytics["trade_count"].value
        if snapshot.trade_analytics.get("trade_count") is not None
        and snapshot.trade_analytics["trade_count"].value is not None
        else len(trades)
    )
    gross_pnl_metric = snapshot.economic.get("gross_pnl")
    net_pnl_metric = snapshot.economic.get("net_pnl")
    total_cost_metric = snapshot.costs.get("total_cost")
    snapshot_gross_pnl = float(
        gross_pnl_metric.value if gross_pnl_metric and gross_pnl_metric.value is not None else 0.0
    )
    snapshot_net_pnl = float(
        net_pnl_metric.value if net_pnl_metric and net_pnl_metric.value is not None else 0.0
    )
    snapshot_total_cost = float(
        total_cost_metric.value
        if total_cost_metric and total_cost_metric.value is not None
        else 0.0
    )
    final_equity_metric = snapshot.trade_analytics.get("final_equity") or snapshot.economic.get(
        "final_equity"
    )
    final_equity = float(
        final_equity_metric.value
        if final_equity_metric and final_equity_metric.value is not None
        else inputs.initial_equity
    )

    reconciliation = validate_trade_ledger_reconciliation_v0(
        rows=trade_rows,
        canonical_trade_count=canonical_trade_count,
        snapshot_gross_pnl=snapshot_gross_pnl,
        snapshot_net_pnl=snapshot_net_pnl,
        snapshot_total_cost=snapshot_total_cost,
    )
    if equity_rows:
        validate_equity_final_value_reconciliation_v0(
            equity_curve=equity_persistence,
            final_equity=final_equity,
        )

    trades_opened = int(funnel.stage_counts.get("trades_opened_count", 0))
    if inputs.funnel_counts is not None and trades_opened != canonical_trade_count:
        raise SnapshotContractError(
            "trades_opened_count_reconciliation_failed:"
            f"funnel={trades_opened}:trade_count={canonical_trade_count}"
        )

    data_quality_payload = {
        "schema_version": "canonical_observability_data_quality.v0",
        "trade_ledger_owner": TRADE_LEDGER_OWNER,
        "equity_curve_owner": TRADE_LEDGER_OWNER,
        "drawdown_curve_owner": TRADE_LEDGER_OWNER,
        "decision_funnel_owner": DECISION_FUNNEL_OWNER,
        "unresolved_trade_field_count": sum(
            1
            for row in trade_rows
            for field in row.fields.values()
            if field.status is MetricMaterializationStatus.SOURCE_MISSING
        ),
        "unresolved_funnel_field_count": len(funnel.unavailable_stages),
        "legacy_projection_status": "COMPATIBLE",
    }
    provenance_payload = {
        "schema_version": "canonical_observability_provenance.v0",
        "snapshot_owner": SNAPSHOT_OWNER,
        "materialization_owner": MATERIALIZATION_OWNER,
        "advanced_capabilities_owner": ADVANCED_CAPABILITIES_OWNER,
        "trade_record_source": "backtest.engine:Trade",
        "trade_ledger_owner": TRADE_LEDGER_OWNER,
        "research_funnel_owner": RESEARCH_FUNNEL_OWNER,
        "source_refs": sorted(source_refs or []),
        "run_identity": dict(run_identity or {}),
    }
    reconciliation_payload = {
        "schema_version": "canonical_observability_reconciliation.v0",
        **reconciliation.__dict__,
        "equity_reconciliation_pass": equity_persistence.final_value == final_equity,
        "trades_opened_count": trades_opened,
        "trade_count": canonical_trade_count,
        "trades_opened_reconciliation_pass": trades_opened == canonical_trade_count
        if inputs.funnel_counts is not None
        else None,
    }

    bundle = CanonicalObservabilityBundleV0(
        snapshot_payload=snapshot_payload,
        registry_payload=resolved_registry.to_dict(),
        trade_ledger_jsonl=trade_ledger_jsonl,
        equity_curve_csv=equity_curve_csv,
        drawdown_curve_csv=drawdown_curve_csv,
        drawdown_not_applicable_payload=drawdown_not_applicable_payload,
        decision_funnel_payload=funnel.to_dict(),
        data_quality_payload=data_quality_payload,
        provenance_payload=provenance_payload,
        reconciliation_payload=reconciliation_payload,
        final_report=final_report,
        advanced_capability_payloads=advanced_payloads,
    )
    bundle.compute_digest()
    return bundle, summary
