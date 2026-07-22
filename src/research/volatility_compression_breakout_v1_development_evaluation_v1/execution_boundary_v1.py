"""Execution boundary for VCB v1 development evaluation.

Separates authorization/orchestration from panel IO and treatment/baseline wiring.
Tests inject FakeExecutionBoundaryV1; production uses RealExecutionBoundaryV1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    TreatmentBaselineWiringHandoffV1,
    wire_treatment_and_baseline_panel_events_v1,
)


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
    """Canonical metrics bundle for treatment arm (+ baseline comparison fields)."""

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
    """Injectable boundary: real panel/wiring or fake for tests."""

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
        expected_dataset_id: str = DATASET_ID,
        expected_dataset_digest: str | None = None,
        time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
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
    ) -> TreatmentBaselineWiringHandoffV1: ...


class RealExecutionBoundaryV1:
    """Production boundary: load DEVELOPMENT panel and wire treatment/baseline producers."""

    def load_development_panel(
        self,
        *,
        repo_root: Path,
        archive_root: Path | None,
        expected_dataset_id: str = DATASET_ID,
        expected_dataset_digest: str | None = None,
        time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
    ) -> PanelLoadResultV1:
        _ = repo_root
        if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
            raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
        if expected_dataset_id != DATASET_ID:
            raise ValueError("DATASET_ID_NOT_BOUND")

        from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
            REQUIRED_DATASET_ID,
            resolve_development_archive_root,
            verify_development_panel_hashes,
        )
        from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_loader_v1 import (
            load_instrument_panel_series_from_development_archive_v1,
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
        return PanelLoadResultV1(
            dataset_id=DATASET_ID,
            dataset_digest=str(digest or hashes.get("content_hash") or ""),
            panel_series=tuple(panel_series),
            timestamps_utc=tuple(timestamps),
            instrument_count=len(panel_series),
            holdout_accessed=False,
        )

    def wire_treatment_baseline(self, panel: PanelLoadResultV1) -> TreatmentBaselineWiringHandoffV1:
        if panel.dataset_id != DATASET_ID:
            raise ValueError("DATASET_ID_MISMATCH")
        if panel.holdout_accessed:
            raise ValueError("HOLDOUT_ACCESSED_TRUE")
        return wire_treatment_and_baseline_panel_events_v1(panel.panel_series)

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        """Wire treatment/baseline, then realize PnL via productive exit evaluator."""
        from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
            evaluate_treatment_and_baseline_productive_pnl_v1,
            productive_exit_pnl_evaluator_is_bound,
        )

        if not productive_exit_pnl_evaluator_is_bound():
            raise ValueError("PRODUCTIVE_EXIT_PNL_EVALUATOR_NOT_BOUND")
        handoff = self.wire_treatment_baseline(panel)
        treatment, baseline = evaluate_treatment_and_baseline_productive_pnl_v1(
            dataset_id=panel.dataset_id,
            panel_series=panel.panel_series,
            handoff=handoff,
            cost_execution_binding=cost_execution_binding,
            cost_multiplier=cost_multiplier,
        )
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
                "treatment_trade_count": treatment.trade_count,
            },
        )


@dataclass
class FakeExecutionBoundaryV1:
    """Test-only boundary. Never opens holdout or real archives."""

    panel: PanelLoadResultV1
    canonical_metrics: BacktestMetricsBundleV1
    stress_metrics: BacktestMetricsBundleV1
    wiring_handoff: TreatmentBaselineWiringHandoffV1 | None = None
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
        return self.panel

    def wire_treatment_baseline(self, panel: PanelLoadResultV1) -> TreatmentBaselineWiringHandoffV1:
        self.wire_calls += 1
        if self.wiring_handoff is None:
            raise ValueError("FAKE_WIRING_HANDOFF_MISSING")
        _ = panel
        return self.wiring_handoff

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        self.backtest_calls += 1
        # Prove evaluator handoff is reached via wiring before returning canned metrics.
        _ = self.wire_treatment_baseline(panel)
        _ = cost_execution_binding
        if abs(float(cost_multiplier) - 1.5) < 1e-12:
            return self.stress_metrics
        return self.canonical_metrics
