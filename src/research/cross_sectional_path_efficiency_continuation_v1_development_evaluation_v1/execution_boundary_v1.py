"""Execution boundary for CS RS momentum v1 development evaluation.

Separates authorization/orchestration from panel IO and canonical backtest owners.
Tests inject a fake boundary; production uses the real boundary without inventing metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from src.research.cross_sectional_path_efficiency_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
)
from src.research.cross_sectional_path_efficiency_continuation_v1_development_evaluation_v1.panel_wiring_v1 import (
    wire_selection_intents_to_orchestrator_result_v1,
)
from src.research.cross_sectional_path_efficiency_continuation_v1_development_evaluation_v1.rebalance_observations_v1 import (
    collect_valid_evaluable_rebalance_observations,
    count_valid_evaluable_rebalance_observations,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
    run_single_slot_panel_backtest_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1


@dataclass(frozen=True)
class PanelLoadResultV1:
    dataset_id: str
    dataset_digest: str
    panel_series: tuple[InstrumentPanelSeriesV1, ...]
    timestamps_utc: tuple[str, ...]
    instrument_count: int
    holdout_accessed: bool = False


@dataclass(frozen=True)
class BacktestMetricsBundleV1:
    gross_return: float
    net_return: float
    gross_profit_factor: float
    net_profit_factor: float
    gross_pnl: float
    net_expectancy: float
    sharpe: float
    max_drawdown: float
    turnover: float
    fees: float
    slippage: float
    total_cost_drag: float
    trade_count: int
    worst1_abs_net_share: float
    cost_multiplier: float
    extras: dict[str, Any] = field(default_factory=dict)


class ExecutionBoundaryV1(Protocol):
    """Injectable boundary: real panel/backtest or fake for tests."""

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
    ) -> PanelLoadResultV1: ...

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        lookback_n: int,
        rebalance_interval_bars: int,
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1: ...


def _scale_cost_binding(
    cost_execution_binding: Mapping[str, Any], *, cost_multiplier: float
) -> dict[str, Any]:
    import copy

    binding = copy.deepcopy(dict(cost_execution_binding))
    fee = binding.setdefault("fee_model_binding", {})
    slip = binding.setdefault("slippage_model_binding", {})
    spread = binding.setdefault("spread_model_binding", {})
    exec_b = binding.setdefault("execution_model_binding", {})
    for container, key in (
        (fee, "fee_bps_per_side"),
        (slip, "slippage_bps_per_side"),
        (spread, "conservative_half_spread_bps"),
        (exec_b, "effective_entry_cost_bps"),
        (exec_b, "effective_exit_cost_bps"),
        (exec_b, "roundtrip_cost_bps"),
    ):
        if key in container:
            container[key] = float(container[key]) * float(cost_multiplier)
    binding["cost_multiplier"] = float(cost_multiplier)
    return binding


def _metrics_from_backtest(
    result: SingleSlotBacktestResultV0, *, cost_multiplier: float
) -> BacktestMetricsBundleV1:
    stats = dict(result.stats or {})
    trades = result.trades
    gross_pnl = float(trades["gross_pnl"].sum()) if len(trades) and "gross_pnl" in trades else 0.0
    net_pnls = trades["pnl"].astype(float).tolist() if len(trades) and "pnl" in trades else []
    worst1 = 0.0
    if net_pnls:
        abs_total = sum(abs(x) for x in net_pnls) or 1.0
        worst1 = max(abs(x) for x in net_pnls) / abs_total
    net_exp = float(sum(net_pnls) / len(net_pnls)) if net_pnls else 0.0
    # Prefer explicit gross PF from wins/losses when available.
    gpf = float(stats.get("profit_factor") or 0.0)
    # When only net PF is in stats, approximate gross via gross/net relationship is forbidden;
    # use trade gross wins/losses if present.
    if "gross_pnl" in trades.columns and len(trades):
        wins = float(trades.loc[trades["gross_pnl"] > 0, "gross_pnl"].sum())
        losses = float(-trades.loc[trades["gross_pnl"] < 0, "gross_pnl"].sum())
        gpf = (wins / losses) if losses > 0 else (float("inf") if wins > 0 else 0.0)
    npf = float(stats.get("profit_factor") or 0.0)
    return BacktestMetricsBundleV1(
        gross_return=float(result.gross_return),
        net_return=float(result.net_return),
        gross_profit_factor=float(gpf) if gpf != float("inf") else 999.0,
        net_profit_factor=float(npf),
        gross_pnl=gross_pnl,
        net_expectancy=net_exp,
        sharpe=float(stats.get("sharpe") or 0.0),
        max_drawdown=float(result.stats.get("max_drawdown", stats.get("max_drawdown", 0.0))),
        turnover=float(result.turnover),
        fees=float(result.fee_drag),
        slippage=float(result.slippage_impact),
        total_cost_drag=float(result.fee_drag) + float(result.slippage_impact),
        trade_count=int(result.trade_count),
        worst1_abs_net_share=float(worst1),
        cost_multiplier=float(cost_multiplier),
    )


class RealExecutionBoundaryV1:
    """Production boundary: load DEVELOPMENT panel and reuse single-slot backtest owner."""

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
    ) -> PanelLoadResultV1:
        # Reuse sealed DEVELOPMENT panel loader (holdout rejected inside).
        from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
            REQUIRED_DATASET_ID,
            resolve_development_archive_root,
            verify_development_panel_hashes,
        )

        root = resolve_development_archive_root(archive_root)
        hashes = verify_development_panel_hashes(root)
        if REQUIRED_DATASET_ID != DATASET_ID:
            raise ValueError("DATASET_ID_OWNER_MISMATCH")
        # Convert research bars to InstrumentPanelSeriesV1 via existing helper if available.
        # Fail-closed deferred load path: require explicit panel materializer for this strategy.
        from src.research.cross_sectional_path_efficiency_continuation_v1_development_evaluation_v1.panel_loader_v1 import (
            load_instrument_panel_series_from_development_archive_v1,
        )

        panel_series, timestamps, digest = load_instrument_panel_series_from_development_archive_v1(
            root
        )
        return PanelLoadResultV1(
            dataset_id=DATASET_ID,
            dataset_digest=str(digest or hashes.get("content_hash") or ""),
            panel_series=tuple(panel_series),
            timestamps_utc=tuple(timestamps),
            instrument_count=len(panel_series),
            holdout_accessed=False,
        )

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        lookback_n: int,
        rebalance_interval_bars: int,
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        scaled = _scale_cost_binding(cost_execution_binding, cost_multiplier=cost_multiplier)
        orchestrator = wire_selection_intents_to_orchestrator_result_v1(
            panel.panel_series,
            lookback_n=lookback_n,
            signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
            rebalance_interval_bars=rebalance_interval_bars,
            min_eligible_members_for_rank=DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
        )
        result = run_single_slot_panel_backtest_v0(
            orchestrator,
            panel.panel_series,
            cost_execution_binding=scaled,
        )
        return _metrics_from_backtest(result, cost_multiplier=cost_multiplier)


@dataclass
class FakeExecutionBoundaryV1:
    """Test-only boundary. Never opens holdout or real archives."""

    panel: PanelLoadResultV1
    canonical_metrics: BacktestMetricsBundleV1
    stress_metrics: BacktestMetricsBundleV1
    load_calls: int = 0
    backtest_calls: int = 0

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
    ) -> PanelLoadResultV1:
        self.load_calls += 1
        if archive_root is not None and "holdout" in str(archive_root).lower():
            raise ValueError(f"HOLDOUT_PATH_REJECTED:{archive_root}")
        return self.panel

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        lookback_n: int = DEFAULT_LOOKBACK_N,
        rebalance_interval_bars: int = DEFAULT_REBALANCE_INTERVAL_BARS,
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        self.backtest_calls += 1
        _ = (panel, cost_execution_binding, lookback_n, rebalance_interval_bars)
        if abs(float(cost_multiplier) - 1.5) < 1e-12:
            return self.stress_metrics
        return self.canonical_metrics


def count_panel_rebalance_observations(
    panel: PanelLoadResultV1,
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    rebalance_interval_bars: int = DEFAULT_REBALANCE_INTERVAL_BARS,
) -> int:
    closes = {s.instrument_id: tuple(float(b.close) for b in s.bars) for s in panel.panel_series}
    obs = collect_valid_evaluable_rebalance_observations(
        closes,
        panel.timestamps_utc,
        lookback_n=lookback_n,
        rebalance_interval_bars=rebalance_interval_bars,
    )
    return count_valid_evaluable_rebalance_observations(obs)
