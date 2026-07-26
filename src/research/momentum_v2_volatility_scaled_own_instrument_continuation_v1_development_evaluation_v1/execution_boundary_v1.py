"""Execution boundary for Momentum V2 vol-scaled development evaluation.

Treatment and baseline both use strategy-emitted ENTRY/EXIT roundtrips; PnL is
realized via the shared productive evaluator primitives (no second PnL truth).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.panel_wiring_v1 import (
    MomentumV2TreatmentBaselineWiringHandoffV1,
    StrategyEmittedRoundtripHandoffV1,
    wire_treatment_and_baseline_panel_events_v1,
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
    trade_count: int
    evaluable_treatment_breakout_events: int
    baseline_net_profit_factor: float
    baseline_gross_profit_factor: float
    baseline_trade_count: int
    cost_multiplier: float
    extras: dict[str, Any] = field(default_factory=dict)


class ExecutionBoundaryV1(Protocol):
    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
        expected_dataset_id: str = DATASET_ID,
        expected_dataset_digest: str | None = None,
        time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
        expected_config_digest: str | None = None,
    ) -> PanelLoadResultV1: ...

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1: ...

    def wire_treatment_baseline(
        self, panel: PanelLoadResultV1
    ) -> MomentumV2TreatmentBaselineWiringHandoffV1: ...


def _exit_reason_attribution(trades: Sequence[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for tr in trades:
        key = str(getattr(tr, "exit_reason", "UNKNOWN"))
        out[key] = out.get(key, 0) + 1
    return out


def _max_single_instrument_positive_gross_pnl_share(trades: Sequence[Any]) -> float:
    positive_by_instrument: dict[str, float] = {}
    total_positive = 0.0
    for tr in trades:
        gp = float(getattr(tr, "gross_pnl", 0.0))
        if gp <= 0:
            continue
        iid = str(getattr(tr, "instrument_id", ""))
        positive_by_instrument[iid] = positive_by_instrument.get(iid, 0.0) + gp
        total_positive += gp
    if total_positive <= 0:
        return 0.0
    return max(positive_by_instrument.values()) / total_positive


def _realize_roundtrips_atr_cached_v1(
    *,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    strategy_roundtrips: Sequence[StrategyEmittedRoundtripHandoffV1],
    effective_cost,
):
    """Same productive PnL primitives as VCB realize_*, with ATR cached per instrument.

    Avoids O(trades * bars) ATR recomputation inside the shared loop while keeping
    ``_realize_roundtrip_v1`` / ATR20 sizing as the sole PnL truth.
    """
    from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
        RoundtripTradeV1,
        _panel_to_frame,
        _position_size_from_atr_stop_v1,
        _realize_roundtrip_v1,
    )
    from src.research.volatility_compression_breakout_v1_vol_state_v1 import compute_atr20_v1

    by_id = {s.instrument_id: s for s in panel_series}
    frames: dict[str, Any] = {}
    atrs: dict[str, Any] = {}
    trades: list[RoundtripTradeV1] = []
    for rt in strategy_roundtrips:
        instrument_id = str(rt.instrument_id)
        if instrument_id not in by_id:
            raise ValueError(f"ROUNDTRIP_INSTRUMENT_MISSING:{instrument_id}")
        if instrument_id not in frames:
            frame = _panel_to_frame(by_id[instrument_id])
            frames[instrument_id] = frame
            atrs[instrument_id] = compute_atr20_v1(frame["high"], frame["low"], frame["close"])
        frame = frames[instrument_id]
        atr = atrs[instrument_id]
        n = len(frame)
        fill_i = int(rt.fill_index)
        exit_i = int(rt.exit_index)
        if not (0 <= fill_i < n) or not (0 <= exit_i < n) or exit_i <= fill_i:
            raise ValueError(f"STRATEGY_ROUNDTRIP_INDEX_INVALID:{instrument_id}:{fill_i}:{exit_i}")
        side = str(rt.side).upper()
        if side not in {"LONG", "SHORT"}:
            raise ValueError(f"ENTRY_SIDE_INVALID:{side}")
        atr_entry = float(atr.iloc[fill_i])
        entry_price = float(rt.entry_price)
        if not (atr_entry == atr_entry) or atr_entry <= 0:
            raise ValueError(f"ATR_INVALID_AT_ENTRY:{instrument_id}:{fill_i}")
        size = _position_size_from_atr_stop_v1(entry_price=entry_price, atr_at_entry=atr_entry)
        stop_price_at_entry = float(getattr(rt, "stop_price_at_entry", entry_price))
        trades.append(
            _realize_roundtrip_v1(
                instrument_id=instrument_id,
                side=side.lower(),
                entry_index=fill_i,
                exit_index=exit_i,
                entry_time=str(frame.loc[fill_i, "timestamp_utc"]),
                exit_time=str(frame.loc[exit_i, "timestamp_utc"]),
                entry_price=entry_price,
                exit_price=float(rt.exit_price),
                size=size,
                stop_price_at_entry=stop_price_at_entry,
                exit_reason=str(rt.exit_reason),  # type: ignore[arg-type]
                effective_cost=effective_cost,
            )
        )
    return tuple(trades)


def _arm_metrics_from_roundtrips(
    *,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    roundtrips: Sequence[StrategyEmittedRoundtripHandoffV1],
    cost_execution_binding: Mapping[str, Any],
    cost_multiplier: float,
    sleeve_instrument_ids: Sequence[str],
    evaluable_entry_events: int,
):
    from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
        ArmPnLResultV1,
        _metrics_from_trades,
        build_effective_cost_config_from_binding_v1,
    )

    effective = build_effective_cost_config_from_binding_v1(
        cost_execution_binding, cost_multiplier=cost_multiplier
    )
    trades = _realize_roundtrips_atr_cached_v1(
        panel_series=panel_series,
        strategy_roundtrips=roundtrips,
        effective_cost=effective,
    )
    metrics = _metrics_from_trades(trades, sleeve_instrument_ids=sleeve_instrument_ids)
    return ArmPnLResultV1(
        arm_id="ARM",
        trades=trades,
        evaluable_entry_events=evaluable_entry_events,
        gross_return=metrics["gross_return"],
        net_return=metrics["net_return"],
        gross_profit_factor=metrics["gross_profit_factor"],
        net_profit_factor=metrics["net_profit_factor"],
        gross_pnl=metrics["gross_pnl"],
        net_expectancy=metrics["net_expectancy"],
        sharpe=metrics["sharpe"],
        max_drawdown=metrics["max_drawdown"],
        trade_count=int(metrics["trade_count"]),
    ), trades


class RealExecutionBoundaryV1:
    """Production boundary: load DEVELOPMENT panel and wire treatment/baseline producers."""

    def __init__(self) -> None:
        self._cached_handoff: MomentumV2TreatmentBaselineWiringHandoffV1 | None = None
        self._cached_panel_id: int | None = None

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
        expected_dataset_id: str = DATASET_ID,
        expected_dataset_digest: str | None = None,
        time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
        expected_config_digest: str | None = None,
    ) -> PanelLoadResultV1:
        from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.binding_v1 import (
            compute_config_digest,
        )

        if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
            raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
        if expected_dataset_id != DATASET_ID:
            raise ValueError("DATASET_ID_NOT_BOUND")
        if expected_config_digest is not None:
            live_digest = compute_config_digest(repo_root)
            if expected_config_digest != live_digest:
                raise ValueError("CONFIG_DIGEST_MISMATCH")

        from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.panel_loader_v1 import (
            load_instrument_panel_series_from_development_archive_v1,
        )
        from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
            REQUIRED_DATASET_ID,
            resolve_development_archive_root,
            verify_development_panel_hashes,
        )

        root = resolve_development_archive_root(archive_root)
        hashes = verify_development_panel_hashes(root)
        if REQUIRED_DATASET_ID != DATASET_ID:
            raise ValueError("DATASET_ID_OWNER_MISMATCH")
        panel_series, timestamps, digest = load_instrument_panel_series_from_development_archive_v1(
            root,
            expected_dataset_id=expected_dataset_id,
            expected_dataset_digest=expected_dataset_digest,
        )
        if not panel_series:
            raise ValueError("EMPTY_PANEL_MATERIALIZATION")
        return PanelLoadResultV1(
            dataset_id=DATASET_ID,
            dataset_digest=str(digest or hashes.get("content_hash") or ""),
            panel_series=tuple(panel_series),
            timestamps_utc=tuple(timestamps),
            instrument_count=len(panel_series),
            holdout_accessed=False,
        )

    def wire_treatment_baseline(
        self, panel: PanelLoadResultV1, *, repo_root: Path | None = None
    ) -> MomentumV2TreatmentBaselineWiringHandoffV1:
        if panel.dataset_id != DATASET_ID:
            raise ValueError("DATASET_ID_MISMATCH")
        if panel.holdout_accessed:
            raise ValueError("HOLDOUT_ACCESSED_TRUE")
        if not panel.panel_series:
            raise ValueError("EMPTY_PANEL_MATERIALIZATION")
        panel_key = id(panel.panel_series)
        if self._cached_handoff is not None and self._cached_panel_id == panel_key:
            return self._cached_handoff
        handoff = wire_treatment_and_baseline_panel_events_v1(
            panel.panel_series, repo_root=repo_root
        )
        self._cached_handoff = handoff
        self._cached_panel_id = panel_key
        return handoff

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
            assert_development_dataset_only,
            productive_exit_pnl_evaluator_is_bound,
        )

        if not productive_exit_pnl_evaluator_is_bound():
            raise ValueError("PRODUCTIVE_EXIT_PNL_EVALUATOR_NOT_BOUND")
        assert_development_dataset_only(panel.dataset_id)
        handoff = self.wire_treatment_baseline(panel)
        if not handoff.treatment_strategy_roundtrips:
            raise ValueError("EMPTY_TREATMENT_STRATEGY_ROUNDTRIPS")
        if not handoff.baseline_strategy_roundtrips:
            raise ValueError("EMPTY_BASELINE_STRATEGY_ROUNDTRIPS")

        sleeve_ids = [str(a.instrument_id) for a in handoff.treatment]
        treatment, treatment_trades = _arm_metrics_from_roundtrips(
            panel_series=panel.panel_series,
            roundtrips=handoff.treatment_strategy_roundtrips,
            cost_execution_binding=cost_execution_binding,
            cost_multiplier=cost_multiplier,
            sleeve_instrument_ids=sleeve_ids,
            evaluable_entry_events=handoff.evaluable_treatment_breakout_events,
        )
        baseline, _baseline_trades = _arm_metrics_from_roundtrips(
            panel_series=panel.panel_series,
            roundtrips=handoff.baseline_strategy_roundtrips,
            cost_execution_binding=cost_execution_binding,
            cost_multiplier=cost_multiplier,
            sleeve_instrument_ids=[str(a.instrument_id) for a in handoff.baseline],
            evaluable_entry_events=sum(a.evaluable_entry_event_count for a in handoff.baseline),
        )
        long_trade_count = sum(1 for t in treatment_trades if str(t.side).lower() == "long")
        short_trade_count = sum(1 for t in treatment_trades if str(t.side).lower() == "short")
        fee_drag = sum(float(t.entry_fee) + float(t.exit_fee) for t in treatment_trades)
        slip_drag = sum(float(t.entry_slippage) + float(t.exit_slippage) for t in treatment_trades)
        return BacktestMetricsBundleV1(
            gross_return=treatment.gross_return,
            net_return=treatment.net_return,
            gross_profit_factor=treatment.gross_profit_factor,
            net_profit_factor=treatment.net_profit_factor,
            gross_pnl=treatment.gross_pnl,
            net_expectancy=treatment.net_expectancy,
            sharpe=treatment.sharpe,
            max_drawdown=treatment.max_drawdown,
            trade_count=treatment.trade_count,
            evaluable_treatment_breakout_events=treatment.evaluable_entry_events,
            baseline_net_profit_factor=baseline.net_profit_factor,
            baseline_gross_profit_factor=baseline.gross_profit_factor,
            baseline_trade_count=baseline.trade_count,
            cost_multiplier=float(cost_multiplier),
            extras={
                "productive_exit_pnl_evaluator_bound": True,
                "baseline_trade_count": baseline.trade_count,
                "baseline_net_return": baseline.net_return,
                "baseline_max_drawdown": baseline.max_drawdown,
                "treatment_trade_count": treatment.trade_count,
                "long_trade_count": long_trade_count,
                "short_trade_count": short_trade_count,
                "fee_drag": fee_drag,
                "slippage_drag": slip_drag,
                "total_cost_drag": fee_drag + slip_drag,
                "instrument_coverage": len(sleeve_ids),
                "max_single_instrument_positive_gross_pnl_share": (
                    _max_single_instrument_positive_gross_pnl_share(treatment_trades)
                ),
                "exit_reason_attribution": _exit_reason_attribution(treatment_trades),
                "strategy_emitted_exits_used_for_treatment": True,
                "strategy_emitted_exits_used_for_baseline": True,
                "evaluator_reconstruction_used_for_treatment": False,
            },
        )


@dataclass
class FakeExecutionBoundaryV1:
    """Test-only boundary. Never opens holdout or real archives."""

    panel: PanelLoadResultV1
    canonical_metrics: BacktestMetricsBundleV1
    stress_metrics: BacktestMetricsBundleV1
    wiring_handoff: MomentumV2TreatmentBaselineWiringHandoffV1 | None = None
    bound_config_digest: str | None = None
    load_calls: int = 0
    backtest_calls: int = 0
    wire_calls: int = 0

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
        expected_dataset_id: str = DATASET_ID,
        expected_dataset_digest: str | None = None,
        time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
        expected_config_digest: str | None = None,
    ) -> PanelLoadResultV1:
        self.load_calls += 1
        _ = repo_root
        if archive_root is not None and "holdout" in str(archive_root).lower():
            raise ValueError(f"HOLDOUT_PATH_REJECTED:{archive_root}")
        if expected_dataset_id != DATASET_ID or expected_dataset_id != self.panel.dataset_id:
            raise ValueError("DATASET_ID_NOT_BOUND")
        if (
            expected_dataset_digest is not None
            and expected_dataset_digest != self.panel.dataset_digest
        ):
            raise ValueError("DATASET_DIGEST_DRIFT")
        if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
            raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
        if expected_config_digest is not None and self.bound_config_digest is not None:
            if expected_config_digest != self.bound_config_digest:
                raise ValueError("CONFIG_DIGEST_MISMATCH")
        if not self.panel.panel_series:
            raise ValueError("EMPTY_PANEL_MATERIALIZATION")
        return self.panel

    def wire_treatment_baseline(
        self, panel: PanelLoadResultV1, *, repo_root: Path | None = None
    ) -> MomentumV2TreatmentBaselineWiringHandoffV1:
        self.wire_calls += 1
        _ = repo_root
        if not panel.panel_series:
            raise ValueError("EMPTY_PANEL_MATERIALIZATION")
        if self.wiring_handoff is None:
            raise ValueError("FAKE_WIRING_HANDOFF_MISSING")
        return self.wiring_handoff

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        self.backtest_calls += 1
        _ = self.wire_treatment_baseline(panel)
        _ = cost_execution_binding
        if abs(float(cost_multiplier) - 1.5) < 1e-12:
            return self.stress_metrics
        return self.canonical_metrics
