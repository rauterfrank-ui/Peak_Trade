"""Canonical advanced economic capability pack v0 (offline diagnostics only).

Closes observability-contract capability gaps using existing stats, cost, ledger,
derived-metrics, and funnel owners. No runtime rewire, economic evaluation, or verdict
semantics.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.backtest.cost_config_v0 import (
    EffectiveBacktestCostConfigV0,
    compute_effective_roundtrip_cost_bps,
)
from src.backtest.economic_observability_derived_metrics_v1 import (
    DERIVED_METRICS_OWNER,
    DerivedMetricsBundleV1,
    FORMULA_BREAK_EVEN_EDGE_V1,
)
from src.backtest.economic_observability_registry_v1 import (
    EconomicObservabilityMetricRegistryV1,
    MetricRegistryEntryV1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    CanonicalEconomicObservabilitySnapshotV1,
    MetricMaterializationStatus,
    MetricValueV1,
    SnapshotContractError,
)

ADVANCED_CAPABILITIES_OWNER = "backtest.economic_observability_advanced_capabilities_v1"
CANONICAL_ADVANCED_CAPABILITIES_OWNER = ADVANCED_CAPABILITIES_OWNER

SCHEMA_VERSION = "advanced_economic_capabilities.v0"
FORMULA_BREAK_EVEN_DIAGNOSTICS_V1 = "break_even_diagnostics_v1"
FORMULA_TRADE_EXCURSION_V1 = "trade_excursion_analytics_v1"
FORMULA_CAPITAL_EFFICIENCY_V1 = "capital_efficiency_v1"
FORMULA_CAPACITY_DIAGNOSTICS_V1 = "capacity_diagnostics_v1"
FORMULA_COST_FRONTIER_V1 = "cost_frontier_v1"
FORMULA_EDGE_DECAY_V1 = "edge_decay_diagnostics_v1"
FORMULA_LIQUIDITY_STRESS_V1 = "liquidity_stress_diagnostics_v1"

BAR_INCLUSION_VERSION = "entry_bar_inclusive_exit_bar_exclusive_v1"
PRICE_FIELD_HIGH = "high"
PRICE_FIELD_LOW = "low"
CAPITAL_DENOMINATOR_VERSION = "average_entry_notional_v1"
COST_FRONTIER_SCENARIO_VERSION = "cost_frontier_scenarios_v1"
EDGE_DECAY_BUCKET_VERSION = "edge_decay_time_buckets_v1"
LIQUIDITY_STRESS_SCENARIO_VERSION = "liquidity_stress_scenarios_v1"

EDGE_DECAY_MIN_TRADES = 4
EDGE_DECAY_MIN_TRADES_PER_BUCKET = 2

COST_FRONTIER_SCENARIOS_V1: tuple[tuple[str, dict[str, float]], ...] = (
    ("baseline", {"fee_multiplier": 1.0, "slippage_multiplier": 1.0, "funding_multiplier": 1.0}),
    (
        "fee_stress_1p5x",
        {"fee_multiplier": 1.5, "slippage_multiplier": 1.0, "funding_multiplier": 1.0},
    ),
    (
        "slippage_stress_1p5x",
        {"fee_multiplier": 1.0, "slippage_multiplier": 1.5, "funding_multiplier": 1.0},
    ),
    (
        "combined_stress_1p25x",
        {"fee_multiplier": 1.25, "slippage_multiplier": 1.25, "funding_multiplier": 1.25},
    ),
)

LIQUIDITY_STRESS_SCENARIOS_V1: tuple[tuple[str, dict[str, float]], ...] = (
    (
        "baseline",
        {
            "fee_multiplier": 1.0,
            "slippage_multiplier": 1.0,
            "spread_multiplier": 1.0,
            "funding_multiplier": 1.0,
            "volume_reduction_factor": 1.0,
            "participation_rate_multiplier": 1.0,
        },
    ),
    (
        "fee_multiplier_2x",
        {
            "fee_multiplier": 2.0,
            "slippage_multiplier": 1.0,
            "spread_multiplier": 1.0,
            "funding_multiplier": 1.0,
            "volume_reduction_factor": 1.0,
            "participation_rate_multiplier": 1.0,
        },
    ),
    (
        "slippage_multiplier_2x",
        {
            "fee_multiplier": 1.0,
            "slippage_multiplier": 2.0,
            "spread_multiplier": 1.0,
            "funding_multiplier": 1.0,
            "volume_reduction_factor": 1.0,
            "participation_rate_multiplier": 1.0,
        },
    ),
    (
        "spread_multiplier_1p5x",
        {
            "fee_multiplier": 1.0,
            "slippage_multiplier": 1.0,
            "spread_multiplier": 1.5,
            "funding_multiplier": 1.0,
            "volume_reduction_factor": 1.0,
            "participation_rate_multiplier": 1.0,
        },
    ),
    (
        "volume_reduction_0p5x",
        {
            "fee_multiplier": 1.0,
            "slippage_multiplier": 1.0,
            "spread_multiplier": 1.0,
            "funding_multiplier": 1.0,
            "volume_reduction_factor": 0.5,
            "participation_rate_multiplier": 1.0,
        },
    ),
)

ADVANCED_METRIC_IDS: frozenset[str] = frozenset(
    {
        "realized_cost_bps",
        "cost_to_gross_edge_ratio",
        "mae_bps",
        "mfe_bps",
        "capital_efficiency",
        "return_on_used_capital",
        "net_pnl_per_unit_exposure",
        "gross_pnl_per_unit_exposure",
        "capacity_proxy",
        "liquidity_usage",
        "notional_to_volume_ratio",
        "participation_rate",
        "estimated_market_impact",
        "capacity_constraint_status",
        "cost_frontier_status",
        "maximum_tolerable_total_cost_bps",
        "fee_headroom_bps",
        "slippage_headroom_bps",
        "funding_headroom_bps",
        "net_edge_at_cost_scenario",
        "break_even_cost_multiplier",
        "edge_decay_status",
        "gross_expectancy_by_time_bucket",
        "net_expectancy_by_time_bucket",
        "profit_factor_by_time_bucket",
        "rolling_expectancy",
        "first_half_vs_second_half_gap",
        "recent_vs_prior_edge_ratio",
        "decay_slope",
        "decay_confidence_flags",
    }
)

REBOUND_METRIC_IDS: frozenset[str] = frozenset({"MAE", "MFE"})


@dataclass(frozen=True)
class FixedCostComponentV1:
    """Optional non-proportional cost input for break-even capital diagnostics."""

    fixed_cost: float = 0.0
    minimum_order_cost: float = 0.0
    minimum_notional: float = 0.0


@dataclass(frozen=True)
class AdvancedCapabilitiesInputsV1:
    trades: Sequence[Mapping[str, Any]]
    stats: Mapping[str, Any]
    gross_profit: float
    gross_pnl: float
    net_pnl: float
    total_cost: float
    initial_equity: float
    total_notional: float = 0.0
    effective_cost: Optional[EffectiveBacktestCostConfigV0] = None
    spread_half_bps: Optional[float] = None
    equity_curve: Optional[pd.Series] = None
    offline_market_volume: Optional[float] = None
    fixed_cost_components: Optional[FixedCostComponentV1] = None
    derived_bundle: Optional[DerivedMetricsBundleV1] = None


@dataclass(frozen=True)
class AdvancedMetricResultV1:
    metric_id: str
    value: Optional[float]
    status: MetricMaterializationStatus
    owner: str
    source: str
    formula_version: str
    sample_count: Optional[int]
    quality_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass
class AdvancedEconomicCapabilitiesBundleV1:
    schema_version: str = SCHEMA_VERSION
    owner: str = ADVANCED_CAPABILITIES_OWNER
    capability_statuses: dict[str, str] = field(default_factory=dict)
    capability_reason_codes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    break_even_diagnostics: dict[str, Any] = field(default_factory=dict)
    trade_excursion_analytics: dict[str, Any] = field(default_factory=dict)
    capital_efficiency: dict[str, Any] = field(default_factory=dict)
    capacity_diagnostics: dict[str, Any] = field(default_factory=dict)
    cost_frontier: dict[str, Any] = field(default_factory=dict)
    edge_decay: dict[str, Any] = field(default_factory=dict)
    liquidity_stress: dict[str, Any] = field(default_factory=dict)
    metric_results: dict[str, AdvancedMetricResultV1] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "owner": self.owner,
            "capability_statuses": dict(sorted(self.capability_statuses.items())),
            "capability_reason_codes": {
                key: list(value) for key, value in sorted(self.capability_reason_codes.items())
            },
            "break_even_diagnostics": self.break_even_diagnostics,
            "trade_excursion_analytics": self.trade_excursion_analytics,
            "capital_efficiency": self.capital_efficiency,
            "capacity_diagnostics": self.capacity_diagnostics,
            "cost_frontier": self.cost_frontier,
            "edge_decay": self.edge_decay,
            "liquidity_stress": self.liquidity_stress,
        }


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _computed(
    *,
    metric_id: str,
    value: float,
    formula_version: str,
    sample_count: Optional[int] = None,
    quality_flags: tuple[str, ...] = (),
    status: MetricMaterializationStatus = MetricMaterializationStatus.COMPUTED,
) -> AdvancedMetricResultV1:
    return AdvancedMetricResultV1(
        metric_id=metric_id,
        value=float(value),
        status=status,
        owner=ADVANCED_CAPABILITIES_OWNER,
        source=f"{ADVANCED_CAPABILITIES_OWNER}:{metric_id}",
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=quality_flags,
        reason_codes=(),
    )


def _status(
    *,
    metric_id: str,
    status: MetricMaterializationStatus,
    formula_version: str,
    reason_codes: tuple[str, ...],
    sample_count: Optional[int] = None,
    quality_flags: tuple[str, ...] = (),
) -> AdvancedMetricResultV1:
    return AdvancedMetricResultV1(
        metric_id=metric_id,
        value=None,
        status=status,
        owner=ADVANCED_CAPABILITIES_OWNER,
        source=f"{ADVANCED_CAPABILITIES_OWNER}:{metric_id}",
        formula_version=formula_version,
        sample_count=sample_count,
        quality_flags=quality_flags,
        reason_codes=reason_codes,
    )


def _trade_side(trade: Mapping[str, Any]) -> str:
    size = trade.get("size")
    if isinstance(size, (int, float)):
        if float(size) > 0:
            return "long"
        if float(size) < 0:
            return "short"
    side = trade.get("side")
    if isinstance(side, str) and side.strip():
        return side.strip().lower()
    return "unknown"


def _extract_intratrade_bars(trade: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = trade.get("intratrade_bars") or trade.get("price_path")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    bars: list[Mapping[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping):
            bars.append(item)
    return bars


def _compute_trade_excursion_v1(
    trade: Mapping[str, Any],
) -> tuple[
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[float],
    MetricMaterializationStatus,
    tuple[str, ...],
]:
    entry_price = trade.get("entry_price")
    if entry_price is None or not _is_finite_number(entry_price):
        return (
            None,
            None,
            None,
            None,
            MetricMaterializationStatus.INVALID_INPUT,
            ("MISSING_ENTRY_PRICE",),
        )
    entry = float(entry_price)
    if entry <= 0:
        return (
            None,
            None,
            None,
            None,
            MetricMaterializationStatus.INVALID_INPUT,
            ("NON_POSITIVE_ENTRY_PRICE",),
        )

    bars = _extract_intratrade_bars(trade)
    if not bars:
        return (
            None,
            None,
            None,
            None,
            MetricMaterializationStatus.SOURCE_MISSING,
            ("MISSING_PRICE_PATH",),
        )

    highs: list[float] = []
    lows: list[float] = []
    for bar in bars:
        high = bar.get(PRICE_FIELD_HIGH, bar.get("high"))
        low = bar.get(PRICE_FIELD_LOW, bar.get("low"))
        if high is None or low is None:
            continue
        if not _is_finite_number(high) or not _is_finite_number(low):
            continue
        highs.append(float(high))
        lows.append(float(low))
    if not highs or not lows:
        return (
            None,
            None,
            None,
            None,
            MetricMaterializationStatus.SOURCE_MISSING,
            ("MISSING_PRICE_PATH",),
        )

    side = _trade_side(trade)
    if side == "long":
        mae = entry - min(lows)
        mfe = max(highs) - entry
    elif side == "short":
        mae = max(highs) - entry
        mfe = entry - min(lows)
    else:
        return (
            None,
            None,
            None,
            None,
            MetricMaterializationStatus.INVALID_INPUT,
            ("UNKNOWN_TRADE_SIDE",),
        )

    mae = max(mae, 0.0)
    mfe = max(mfe, 0.0)
    mae_bps = (mae / entry) * 10_000.0
    mfe_bps = (mfe / entry) * 10_000.0
    return mae, mfe, mae_bps, mfe_bps, MetricMaterializationStatus.COMPUTED, ()


def derive_break_even_diagnostics_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    owner = ADVANCED_CAPABILITIES_OWNER
    formula = FORMULA_BREAK_EVEN_DIAGNOSTICS_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}
    derived = inputs.derived_bundle

    required_edge: Optional[float] = None
    break_even_bps: Optional[float] = None
    if derived is not None:
        edge_result = derived.cost_ratios.get("required_gross_edge_for_break_even")
        bps_result = derived.cost_ratios.get("break_even_cost_bps")
        if edge_result is not None and edge_result.value is not None:
            required_edge = float(edge_result.value)
        if bps_result is not None and bps_result.value is not None:
            break_even_bps = float(bps_result.value)

    if inputs.effective_cost is not None:
        roundtrip_bps = compute_effective_roundtrip_cost_bps(
            fee_bps=inputs.effective_cost.taker_fee_bps,
            slippage_bps=inputs.effective_cost.entry_slippage_bps,
            half_spread_bps=inputs.spread_half_bps or 0.0,
        )
        metrics["realized_cost_bps"] = _computed(
            metric_id="realized_cost_bps",
            value=roundtrip_bps,
            formula_version=formula,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    elif inputs.total_notional > 0 and inputs.total_cost >= 0:
        realized = (inputs.total_cost / inputs.total_notional) * 10_000.0
        metrics["realized_cost_bps"] = _computed(
            metric_id="realized_cost_bps",
            value=realized,
            formula_version=formula,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    else:
        metrics["realized_cost_bps"] = _status(
            metric_id="realized_cost_bps",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            formula_version=formula,
            reason_codes=("COST_SOURCE_MISSING",),
        )

    gross_edge = inputs.gross_pnl
    if gross_edge > 0:
        ratio = inputs.total_cost / gross_edge
        metrics["cost_to_gross_edge_ratio"] = _computed(
            metric_id="cost_to_gross_edge_ratio",
            value=ratio,
            formula_version=formula,
            status=MetricMaterializationStatus.RECONSTRUCTED,
        )
    elif gross_edge < 0:
        metrics["cost_to_gross_edge_ratio"] = _status(
            metric_id="cost_to_gross_edge_ratio",
            status=MetricMaterializationStatus.NOT_APPLICABLE,
            formula_version=formula,
            reason_codes=("NEGATIVE_GROSS_EDGE",),
        )
    else:
        metrics["cost_to_gross_edge_ratio"] = _status(
            metric_id="cost_to_gross_edge_ratio",
            status=MetricMaterializationStatus.INSUFFICIENT_DATA,
            formula_version=formula,
            reason_codes=("ZERO_GROSS_EDGE",),
        )

    capital_status = MetricMaterializationStatus.NOT_COMPUTED
    capital_reason = ("BREAK_EVEN_CAPITAL_NOT_DERIVABLE_PROPORTIONAL_COST_MODEL_ONLY",)
    capital_value: Optional[float] = None
    fixed = inputs.fixed_cost_components
    if fixed is not None and (
        fixed.fixed_cost > 0 or fixed.minimum_order_cost > 0 or fixed.minimum_notional > 0
    ):
        net_edge_per_trade = inputs.net_pnl / len(inputs.trades) if inputs.trades else 0.0
        if net_edge_per_trade > 0 and fixed.fixed_cost > 0:
            capital_value = fixed.fixed_cost / net_edge_per_trade
            capital_status = MetricMaterializationStatus.COMPUTED
            capital_reason = ()
        elif fixed.minimum_notional > 0:
            capital_value = fixed.minimum_notional
            capital_status = MetricMaterializationStatus.COMPUTED
            capital_reason = ("MINIMUM_NOTIONAL_BINDING",)

    payload = {
        "status": MetricMaterializationStatus.RECONSTRUCTED.value
        if required_edge is not None
        else MetricMaterializationStatus.SOURCE_MISSING.value,
        "owner": owner,
        "formula_version": formula,
        "required_gross_edge_for_break_even": required_edge,
        "break_even_cost_bps": break_even_bps,
        "realized_cost_bps": metrics["realized_cost_bps"].value,
        "cost_to_gross_edge_ratio": metrics.get(
            "cost_to_gross_edge_ratio",
            _status(
                metric_id="cost_to_gross_edge_ratio",
                status=MetricMaterializationStatus.NOT_COMPUTED,
                formula_version=formula,
                reason_codes=("NOT_COMPUTED",),
            ),
        ).value,
        "cost_to_gross_profit_ratio": (
            derived.cost_ratios["cost_share_of_gross_profit"].value
            if derived and "cost_share_of_gross_profit" in derived.cost_ratios
            else None
        ),
        "break_even_capital": {
            "value": capital_value,
            "status": capital_status.value,
            "reason_codes": list(capital_reason),
        },
        "derived_owner": DERIVED_METRICS_OWNER,
        "derived_formula_version": FORMULA_BREAK_EVEN_EDGE_V1,
        "quality_flags": ["PROPORTIONAL_COST_MODEL_ONLY"]
        if capital_status is MetricMaterializationStatus.NOT_COMPUTED
        else [],
    }
    return payload, metrics


def derive_trade_excursion_analytics_v1(
    trades: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_TRADE_EXCURSION_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}
    trade_records: list[dict[str, Any]] = []
    valid_mae: list[float] = []
    valid_mfe: list[float] = []
    valid_mae_bps: list[float] = []
    valid_mfe_bps: list[float] = []

    for index, trade in enumerate(trades):
        mae, mfe, mae_bps, mfe_bps, status, reasons = _compute_trade_excursion_v1(trade)
        trade_records.append(
            {
                "trade_index": index,
                "trade_id": trade.get("trade_id", f"trade-{index}"),
                "side": _trade_side(trade),
                "mae": mae,
                "mfe": mfe,
                "mae_bps": mae_bps,
                "mfe_bps": mfe_bps,
                "status": status.value,
                "reason_codes": list(reasons),
            }
        )
        if status is MetricMaterializationStatus.COMPUTED and mae is not None and mfe is not None:
            valid_mae.append(mae)
            valid_mfe.append(mfe)
            if mae_bps is not None:
                valid_mae_bps.append(mae_bps)
            if mfe_bps is not None:
                valid_mfe_bps.append(mfe_bps)

    if valid_mae:
        metrics["MAE"] = _computed(
            metric_id="MAE",
            value=float(statistics.mean(valid_mae)),
            formula_version=formula,
            sample_count=len(valid_mae),
        )
        metrics["mae_bps"] = _computed(
            metric_id="mae_bps",
            value=float(statistics.mean(valid_mae_bps)),
            formula_version=formula,
            sample_count=len(valid_mae_bps),
        )
    else:
        metrics["MAE"] = _status(
            metric_id="MAE",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            formula_version=formula,
            reason_codes=("MISSING_PRICE_PATH",),
            sample_count=len(trades),
        )
        metrics["mae_bps"] = _status(
            metric_id="mae_bps",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            formula_version=formula,
            reason_codes=("MISSING_PRICE_PATH",),
            sample_count=len(trades),
        )

    if valid_mfe:
        metrics["MFE"] = _computed(
            metric_id="MFE",
            value=float(statistics.mean(valid_mfe)),
            formula_version=formula,
            sample_count=len(valid_mfe),
        )
        metrics["mfe_bps"] = _computed(
            metric_id="mfe_bps",
            value=float(statistics.mean(valid_mfe_bps)),
            formula_version=formula,
            sample_count=len(valid_mfe_bps),
        )
    else:
        metrics["MFE"] = _status(
            metric_id="MFE",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            formula_version=formula,
            reason_codes=("MISSING_PRICE_PATH",),
            sample_count=len(trades),
        )
        metrics["mfe_bps"] = _status(
            metric_id="mfe_bps",
            status=MetricMaterializationStatus.SOURCE_MISSING,
            formula_version=formula,
            reason_codes=("MISSING_PRICE_PATH",),
            sample_count=len(trades),
        )

    capture_ratio: Optional[float] = None
    if valid_mae and valid_mfe and sum(valid_mae) > 0:
        capture_ratio = sum(valid_mfe) / sum(valid_mae)

    payload = {
        "status": metrics["MAE"].status.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "bar_inclusion_version": BAR_INCLUSION_VERSION,
        "price_fields": {"high": PRICE_FIELD_HIGH, "low": PRICE_FIELD_LOW},
        "trade_level": trade_records,
        "aggregates": {
            "median_mae": float(statistics.median(valid_mae)) if valid_mae else None,
            "median_mfe": float(statistics.median(valid_mfe)) if valid_mfe else None,
            "mfe_to_mae_ratio": capture_ratio,
            "valid_trade_count": len(valid_mae),
            "total_trade_count": len(trades),
        },
        "diagnostic_only": True,
        "runtime_effect": "NONE",
    }
    return payload, metrics


def _average_entry_notional(trades: Sequence[Mapping[str, Any]]) -> Optional[float]:
    notionals: list[float] = []
    for trade in trades:
        entry_notional = trade.get("entry_notional")
        if entry_notional is not None and _is_finite_number(entry_notional):
            notionals.append(abs(float(entry_notional)))
            continue
        entry_price = trade.get("entry_price")
        size = trade.get("size")
        if (
            entry_price is not None
            and size is not None
            and _is_finite_number(entry_price)
            and _is_finite_number(size)
        ):
            notionals.append(abs(float(entry_price) * float(size)))
    if not notionals:
        return None
    return float(statistics.mean(notionals))


def derive_capital_efficiency_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_CAPITAL_EFFICIENCY_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}
    denominator = _average_entry_notional(inputs.trades)
    if denominator is None or denominator <= 0:
        for metric_id in (
            "capital_efficiency",
            "return_on_used_capital",
            "net_pnl_per_unit_exposure",
            "gross_pnl_per_unit_exposure",
        ):
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.INVALID_INPUT,
                formula_version=formula,
                reason_codes=("INVALID_CAPITAL_DENOMINATOR",),
            )
        payload = {
            "status": MetricMaterializationStatus.INVALID_INPUT.value,
            "owner": ADVANCED_CAPABILITIES_OWNER,
            "formula_version": formula,
            "denominator_version": CAPITAL_DENOMINATOR_VERSION,
            "denominator": denominator,
            "reason_codes": ["INVALID_CAPITAL_DENOMINATOR"],
            "diagnostic_only": True,
        }
        return payload, metrics

    net_eff = inputs.net_pnl / denominator
    gross_eff = inputs.gross_pnl / denominator
    return_on_used = net_eff
    capital_eff = net_eff
    for metric_id, value in (
        ("capital_efficiency", capital_eff),
        ("return_on_used_capital", return_on_used),
        ("net_pnl_per_unit_exposure", net_eff),
        ("gross_pnl_per_unit_exposure", gross_eff),
    ):
        metrics[metric_id] = _computed(
            metric_id=metric_id,
            value=value,
            formula_version=formula,
            sample_count=len(inputs.trades),
        )

    payload = {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "denominator_version": CAPITAL_DENOMINATOR_VERSION,
        "denominator": denominator,
        "denominator_definition": "average_entry_notional",
        "capital_efficiency": capital_eff,
        "return_on_used_capital": return_on_used,
        "net_pnl_per_unit_exposure": net_eff,
        "gross_pnl_per_unit_exposure": gross_eff,
        "diagnostic_only": True,
        "runtime_effect": "NONE",
    }
    return payload, metrics


def derive_capacity_diagnostics_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_CAPACITY_DIAGNOSTICS_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}

    if inputs.offline_market_volume is None or inputs.offline_market_volume <= 0:
        for metric_id in (
            "capacity_proxy",
            "liquidity_usage",
            "notional_to_volume_ratio",
            "participation_rate",
            "estimated_market_impact",
            "capacity_constraint_status",
        ):
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.SOURCE_MISSING,
                formula_version=formula,
                reason_codes=("MISSING_OFFLINE_LIQUIDITY_INPUT",),
            )
        return {
            "status": MetricMaterializationStatus.SOURCE_MISSING.value,
            "owner": ADVANCED_CAPABILITIES_OWNER,
            "formula_version": formula,
            "reason_codes": ["MISSING_OFFLINE_LIQUIDITY_INPUT"],
            "diagnostic_only": True,
            "capacity_proxy_is_not_order_limit": True,
            "runtime_effect": "NONE",
        }, metrics

    volume = float(inputs.offline_market_volume)
    notional = float(inputs.total_notional)
    participation = notional / volume if volume > 0 else None
    notional_to_volume = participation
    liquidity_usage = participation
    capacity_proxy = participation
    estimated_impact = participation * 10_000.0 if participation is not None else None
    constraint_status = 1.0 if participation is not None and participation > 0.05 else 0.0

    metric_values = {
        "capacity_proxy": capacity_proxy,
        "liquidity_usage": liquidity_usage,
        "notional_to_volume_ratio": notional_to_volume,
        "participation_rate": participation,
        "estimated_market_impact": estimated_impact,
        "capacity_constraint_status": constraint_status,
    }
    for metric_id, value in metric_values.items():
        if value is None:
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.NOT_COMPUTED,
                formula_version=formula,
                reason_codes=("NOT_COMPUTABLE",),
            )
        else:
            metrics[metric_id] = _computed(
                metric_id=metric_id,
                value=float(value),
                formula_version=formula,
                quality_flags=("CAPACITY_PROXY_DIAGNOSTIC_ONLY",),
            )

    payload = {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "offline_market_volume": volume,
        "total_notional": notional,
        **{key: metric_values[key] for key in metric_values},
        "capacity_proxy_is_not_order_limit": True,
        "diagnostic_only": True,
        "runtime_effect": "NONE",
    }
    return payload, metrics


def _baseline_cost_bps(inputs: AdvancedCapabilitiesInputsV1) -> Optional[float]:
    if inputs.effective_cost is not None:
        return compute_effective_roundtrip_cost_bps(
            fee_bps=inputs.effective_cost.taker_fee_bps,
            slippage_bps=inputs.effective_cost.entry_slippage_bps,
            half_spread_bps=inputs.spread_half_bps or 0.0,
        )
    if inputs.total_notional > 0:
        return (inputs.total_cost / inputs.total_notional) * 10_000.0
    return None


def derive_cost_frontier_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_COST_FRONTIER_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}
    baseline_bps = _baseline_cost_bps(inputs)
    if baseline_bps is None:
        for metric_id in (
            "cost_frontier_status",
            "maximum_tolerable_total_cost_bps",
            "fee_headroom_bps",
            "slippage_headroom_bps",
            "funding_headroom_bps",
            "net_edge_at_cost_scenario",
            "break_even_cost_multiplier",
        ):
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.SOURCE_MISSING,
                formula_version=formula,
                reason_codes=("COST_SOURCE_MISSING",),
            )
        return {
            "status": MetricMaterializationStatus.SOURCE_MISSING.value,
            "owner": ADVANCED_CAPABILITIES_OWNER,
            "formula_version": formula,
            "scenario_version": COST_FRONTIER_SCENARIO_VERSION,
            "reason_codes": ["COST_SOURCE_MISSING"],
            "diagnostic_only": True,
            "economic_verdict_source": "EconomicViabilityEvidenceV1",
        }, metrics

    gross_edge_bps = (
        (inputs.gross_pnl / inputs.total_notional) * 10_000.0 if inputs.total_notional > 0 else None
    )
    scenarios: list[dict[str, Any]] = []
    for name, multipliers in COST_FRONTIER_SCENARIOS_V1:
        fee_mult = multipliers["fee_multiplier"]
        slip_mult = multipliers["slippage_multiplier"]
        fund_mult = multipliers["funding_multiplier"]
        if inputs.effective_cost is not None:
            fee_part = 2.0 * inputs.effective_cost.taker_fee_bps * fee_mult
            slip_part = 2.0 * inputs.effective_cost.entry_slippage_bps * slip_mult
            spread_part = 2.0 * (inputs.spread_half_bps or 0.0)
            scenario_bps = fee_part + slip_part + spread_part
        else:
            scenario_bps = baseline_bps * max(fee_mult, slip_mult, fund_mult)
        net_edge = None
        if gross_edge_bps is not None:
            net_edge = gross_edge_bps - scenario_bps
        scenarios.append(
            {
                "scenario_id": name,
                "multipliers": multipliers,
                "total_cost_bps": scenario_bps,
                "net_edge_bps": net_edge,
            }
        )

    baseline_scenario = scenarios[0]
    max_tolerable = gross_edge_bps
    fee_headroom = (
        gross_edge_bps
        - (
            baseline_scenario["total_cost_bps"]
            - 2.0 * (inputs.effective_cost.taker_fee_bps if inputs.effective_cost else 0.0)
        )
        if gross_edge_bps is not None and inputs.effective_cost is not None
        else None
    )
    slippage_headroom = (
        gross_edge_bps
        - (
            baseline_scenario["total_cost_bps"]
            - 2.0 * (inputs.effective_cost.entry_slippage_bps if inputs.effective_cost else 0.0)
        )
        if gross_edge_bps is not None and inputs.effective_cost is not None
        else None
    )
    funding_headroom = None
    break_even_multiplier = (
        gross_edge_bps / baseline_bps if gross_edge_bps is not None and baseline_bps > 0 else None
    )

    metric_map = {
        "cost_frontier_status": 1.0,
        "maximum_tolerable_total_cost_bps": max_tolerable,
        "fee_headroom_bps": fee_headroom,
        "slippage_headroom_bps": slippage_headroom,
        "funding_headroom_bps": funding_headroom,
        "net_edge_at_cost_scenario": baseline_scenario.get("net_edge_bps"),
        "break_even_cost_multiplier": break_even_multiplier,
    }
    for metric_id, raw_value in metric_map.items():
        if raw_value is None:
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.NOT_COMPUTED,
                formula_version=formula,
                reason_codes=("NOT_DERIVABLE",),
            )
        else:
            metrics[metric_id] = _computed(
                metric_id=metric_id,
                value=float(raw_value),
                formula_version=formula,
                quality_flags=("DIAGNOSTIC_ONLY_NO_VERDICT",),
            )

    payload = {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "scenario_version": COST_FRONTIER_SCENARIO_VERSION,
        "baseline_cost_bps": baseline_bps,
        "scenarios": scenarios,
        "diagnostic_only": True,
        "economic_verdict_source": "EconomicViabilityEvidenceV1",
        "runtime_effect": "NONE",
    }
    return payload, metrics


def _trade_exit_timestamp(trade: Mapping[str, Any]) -> Optional[pd.Timestamp]:
    exit_time = trade.get("exit_time")
    if exit_time is None:
        return None
    try:
        return pd.Timestamp(exit_time)
    except (TypeError, ValueError):
        return None


def derive_edge_decay_diagnostics_v1(
    trades: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_EDGE_DECAY_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}

    if len(trades) < EDGE_DECAY_MIN_TRADES:
        for metric_id in (
            "edge_decay_status",
            "gross_expectancy_by_time_bucket",
            "net_expectancy_by_time_bucket",
            "profit_factor_by_time_bucket",
            "rolling_expectancy",
            "first_half_vs_second_half_gap",
            "recent_vs_prior_edge_ratio",
            "decay_slope",
            "decay_confidence_flags",
        ):
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.INSUFFICIENT_DATA,
                formula_version=formula,
                reason_codes=("INSUFFICIENT_TRADE_SAMPLE",),
                sample_count=len(trades),
            )
        return {
            "status": MetricMaterializationStatus.INSUFFICIENT_DATA.value,
            "owner": ADVANCED_CAPABILITIES_OWNER,
            "formula_version": formula,
            "bucket_version": EDGE_DECAY_BUCKET_VERSION,
            "min_trades": EDGE_DECAY_MIN_TRADES,
            "sample_count": len(trades),
            "reason_codes": ["INSUFFICIENT_TRADE_SAMPLE"],
            "diagnostic_only": True,
        }, metrics

    ordered = sorted(
        enumerate(trades),
        key=lambda item: (_trade_exit_timestamp(item[1]) or pd.Timestamp.min, item[0]),
    )
    mid = len(ordered) // 2
    first_half = [trade for _, trade in ordered[:mid]]
    second_half = [trade for _, trade in ordered[mid:]]

    def _expectancy(trade_list: Sequence[Mapping[str, Any]], *, gross: bool) -> Optional[float]:
        if not trade_list:
            return None
        key = "gross_pnl" if gross else "pnl"
        values = [float(t[key]) for t in trade_list if t.get(key) is not None]
        if not values:
            return None
        return sum(values) / len(values)

    gross_first = _expectancy(first_half, gross=True)
    gross_second = _expectancy(second_half, gross=True)
    net_first = _expectancy(first_half, gross=False)
    net_second = _expectancy(second_half, gross=False)
    gap = None
    if gross_first is not None and gross_second is not None:
        gap = gross_second - gross_first
    recent_ratio = None
    if gross_first not in (None, 0.0) and gross_second is not None:
        recent_ratio = gross_second / gross_first

    gross_wins = sum(
        float(t.get("gross_pnl", t.get("pnl", 0.0)))
        for t in second_half
        if float(t.get("gross_pnl", t.get("pnl", 0.0))) > 0
    )
    gross_losses = abs(
        sum(
            float(t.get("gross_pnl", t.get("pnl", 0.0)))
            for t in second_half
            if float(t.get("gross_pnl", t.get("pnl", 0.0))) < 0
        )
    )
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else None

    bucket_payload = {
        "first_half_gross_expectancy": gross_first,
        "second_half_gross_expectancy": gross_second,
        "first_half_net_expectancy": net_first,
        "second_half_net_expectancy": net_second,
    }

    metric_map = {
        "edge_decay_status": 1.0,
        "gross_expectancy_by_time_bucket": gross_second,
        "net_expectancy_by_time_bucket": net_second,
        "profit_factor_by_time_bucket": profit_factor,
        "rolling_expectancy": net_second,
        "first_half_vs_second_half_gap": gap,
        "recent_vs_prior_edge_ratio": recent_ratio,
        "decay_slope": gap,
        "decay_confidence_flags": 1.0 if len(trades) >= EDGE_DECAY_MIN_TRADES else 0.0,
    }
    for metric_id, raw_value in metric_map.items():
        if raw_value is None:
            metrics[metric_id] = _status(
                metric_id=metric_id,
                status=MetricMaterializationStatus.NOT_COMPUTED,
                formula_version=formula,
                reason_codes=("NOT_DERIVABLE",),
                sample_count=len(trades),
            )
        else:
            metrics[metric_id] = _computed(
                metric_id=metric_id,
                value=float(raw_value),
                formula_version=formula,
                sample_count=len(trades),
            )

    payload = {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "bucket_version": EDGE_DECAY_BUCKET_VERSION,
        "time_buckets": bucket_payload,
        "sample_count": len(trades),
        "diagnostic_only": True,
        "economic_verdict_source": "EconomicViabilityEvidenceV1",
    }
    return payload, metrics


def derive_liquidity_stress_diagnostics_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> tuple[dict[str, Any], dict[str, AdvancedMetricResultV1]]:
    formula = FORMULA_LIQUIDITY_STRESS_V1
    metrics: dict[str, AdvancedMetricResultV1] = {}
    baseline_bps = _baseline_cost_bps(inputs)
    if baseline_bps is None:
        return {
            "status": MetricMaterializationStatus.SOURCE_MISSING.value,
            "owner": ADVANCED_CAPABILITIES_OWNER,
            "formula_version": formula,
            "scenario_version": LIQUIDITY_STRESS_SCENARIO_VERSION,
            "reason_codes": ["COST_SOURCE_MISSING"],
            "diagnostic_only": True,
            "economic_verdict_source": "EconomicViabilityEvidenceV1",
            "execution_model_unchanged": True,
        }, metrics

    gross_edge_bps = (
        (inputs.gross_pnl / inputs.total_notional) * 10_000.0 if inputs.total_notional > 0 else None
    )
    scenarios: list[dict[str, Any]] = []
    for name, multipliers in LIQUIDITY_STRESS_SCENARIOS_V1:
        fee_mult = multipliers["fee_multiplier"]
        slip_mult = multipliers["slippage_multiplier"]
        spread_mult = multipliers["spread_multiplier"]
        if inputs.effective_cost is not None:
            fee_part = 2.0 * inputs.effective_cost.taker_fee_bps * fee_mult
            slip_part = 2.0 * inputs.effective_cost.entry_slippage_bps * slip_mult
            spread_part = 2.0 * (inputs.spread_half_bps or 0.0) * spread_mult
            stressed_bps = fee_part + slip_part + spread_part
        else:
            stressed_bps = baseline_bps * max(fee_mult, slip_mult, spread_mult)
        net_edge = gross_edge_bps - stressed_bps if gross_edge_bps is not None else None
        scenarios.append(
            {
                "scenario_id": name,
                "multipliers": multipliers,
                "stressed_cost_bps": stressed_bps,
                "net_edge_bps": net_edge,
            }
        )

    payload = {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "formula_version": formula,
        "scenario_version": LIQUIDITY_STRESS_SCENARIO_VERSION,
        "baseline_cost_bps": baseline_bps,
        "scenarios": scenarios,
        "diagnostic_only": True,
        "economic_verdict_source": "EconomicViabilityEvidenceV1",
        "execution_model_unchanged": True,
        "runtime_effect": "NONE",
    }
    return payload, metrics


def materialize_advanced_economic_capabilities_v1(
    inputs: AdvancedCapabilitiesInputsV1,
) -> AdvancedEconomicCapabilitiesBundleV1:
    bundle = AdvancedEconomicCapabilitiesBundleV1()
    all_metrics: dict[str, AdvancedMetricResultV1] = {}

    break_even, break_even_metrics = derive_break_even_diagnostics_v1(inputs)
    bundle.break_even_diagnostics = break_even
    all_metrics.update(break_even_metrics)

    excursion, excursion_metrics = derive_trade_excursion_analytics_v1(inputs.trades)
    bundle.trade_excursion_analytics = excursion
    all_metrics.update(excursion_metrics)

    capital, capital_metrics = derive_capital_efficiency_v1(inputs)
    bundle.capital_efficiency = capital
    all_metrics.update(capital_metrics)

    capacity, capacity_metrics = derive_capacity_diagnostics_v1(inputs)
    bundle.capacity_diagnostics = capacity
    all_metrics.update(capacity_metrics)

    frontier, frontier_metrics = derive_cost_frontier_v1(inputs)
    bundle.cost_frontier = frontier
    all_metrics.update(frontier_metrics)

    decay, decay_metrics = derive_edge_decay_diagnostics_v1(inputs.trades)
    bundle.edge_decay = decay
    all_metrics.update(decay_metrics)

    stress, stress_metrics = derive_liquidity_stress_diagnostics_v1(inputs)
    bundle.liquidity_stress = stress
    all_metrics.update(stress_metrics)

    bundle.metric_results = all_metrics
    bundle.capability_statuses = {
        "break_even_edge": break_even.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
        "break_even_capital": break_even.get("break_even_capital", {}).get(
            "status", MetricMaterializationStatus.NOT_COMPUTED.value
        ),
        "mae_mfe": excursion.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
        "capital_efficiency": capital.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
        "capacity_diagnostics": capacity.get(
            "status", MetricMaterializationStatus.NOT_COMPUTED.value
        ),
        "cost_frontier": frontier.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
        "edge_decay": decay.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
        "liquidity_stress": stress.get("status", MetricMaterializationStatus.NOT_COMPUTED.value),
    }
    bundle.capability_reason_codes = {
        key: tuple(value) if isinstance(value, list) else (str(value),)
        for key, value in {
            "break_even_capital": break_even.get("break_even_capital", {}).get("reason_codes", ()),
            "capacity_diagnostics": capacity.get("reason_codes", ()),
            "mae_mfe": excursion.get("aggregates", {}).get("reason_codes", ()),
        }.items()
        if value
    }
    return bundle


def _result_to_metric_value(result: AdvancedMetricResultV1, *, unit: str) -> MetricValueV1:
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


def bind_advanced_capabilities_to_snapshot_v1(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    bundle: AdvancedEconomicCapabilitiesBundleV1,
    *,
    registry: EconomicObservabilityMetricRegistryV1,
) -> int:
    """Bind advanced capability metrics onto snapshot buckets. Returns bound count."""
    bound = 0
    entry_by_id = {entry.metric_id: entry for entry in registry.entries}
    for metric_id, result in bundle.metric_results.items():
        entry = entry_by_id.get(metric_id)
        if entry is None:
            continue
        bucket = getattr(snapshot, entry.domain)
        bucket[metric_id] = _result_to_metric_value(result, unit=entry.unit)
        snapshot.metric_statuses[metric_id] = result.status.value
        bound += 1
    return bound


def advanced_capability_artifact_payloads_v1(
    bundle: AdvancedEconomicCapabilitiesBundleV1,
) -> dict[str, dict[str, Any]]:
    """Return canonical advanced capability JSON artifacts for observability bundle."""
    index = {
        "schema_version": SCHEMA_VERSION,
        "owner": ADVANCED_CAPABILITIES_OWNER,
        "capability_statuses": bundle.capability_statuses,
        "capability_reason_codes": {
            key: list(value) for key, value in bundle.capability_reason_codes.items()
        },
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
        "economic_verdict_source": "EconomicViabilityEvidenceV1",
    }
    return {
        "ADVANCED_ECONOMIC_CAPABILITIES.json": index,
        "BREAK_EVEN_DIAGNOSTICS.json": bundle.break_even_diagnostics,
        "TRADE_EXCURSION_ANALYTICS.json": bundle.trade_excursion_analytics,
        "CAPITAL_EFFICIENCY.json": bundle.capital_efficiency,
        "CAPACITY_DIAGNOSTICS.json": bundle.capacity_diagnostics,
        "COST_FRONTIER.json": bundle.cost_frontier,
        "EDGE_DECAY.json": bundle.edge_decay,
        "LIQUIDITY_STRESS.json": bundle.liquidity_stress,
    }


def validate_no_post_exit_lookahead_v1(
    trade: Mapping[str, Any],
    *,
    exit_time: Any,
) -> bool:
    """Return True when intratrade bars do not extend beyond canonical exit."""
    bars = _extract_intratrade_bars(trade)
    if not bars:
        return True
    exit_ts = pd.Timestamp(exit_time) if exit_time is not None else None
    if exit_ts is None:
        return True
    for bar in bars:
        ts = bar.get("timestamp")
        if ts is None:
            continue
        try:
            bar_ts = pd.Timestamp(ts)
        except (TypeError, ValueError):
            continue
        if bar_ts > exit_ts:
            return False
    return True
