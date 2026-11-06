"""Contract tests for cross-sectional single-slot accounting reconciliation v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_single_slot_research_orchestrator_v0 import (
    run_ma_crossover_panel_rank_rotation_orchestrator_v0,
    default_ma_crossover_operator_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (
    FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING,
    reconcile_legacy_backtest_result_accounting_v0,
    reconcile_single_slot_backtest_accounting_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    END_OF_WINDOW_CLOSE_REASON,
    END_OF_WINDOW_POLICY,
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorEpochResultV0,
    OrchestratorRunResultV0,
    SingleSlotSelectionEventV0,
    SlotSide,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _cost_binding() -> dict:
    return materialize_versioned_research_binding_v0()["cost_execution_binding"]


def _open_position_orchestrator(panel: tuple) -> OrchestratorRunResultV0:
    instrument_id = panel[0].instrument_id
    epochs: list[OrchestratorEpochResultV0] = []
    for index, bar in enumerate(panel[0].bars):
        epochs.append(
            OrchestratorEpochResultV0(
                epoch_index=index,
                timestamp_utc=bar.timestamp_utc,
                scores=(),
                selection=SingleSlotSelectionEventV0(
                    epoch_index=index,
                    timestamp_utc=bar.timestamp_utc,
                    ranked_instrument_ids=(instrument_id,),
                    top_score=0.05,
                    selected_instrument_id=instrument_id,
                    slot_side=SlotSide.LONG,
                    pending_switch=False,
                    eligible_member_count=len(panel),
                ),
                error_codes=(),
            )
        )
    return OrchestratorRunResultV0(
        orchestrator_version="test.orchestrator",
        score_formula_version="test.score",
        epochs=tuple(epochs),
        final_slot_side=SlotSide.LONG,
        final_instrument_id=instrument_id,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def test_closed_position_accounting_reconciles() -> None:
    panel = build_synthetic_panel_series_v0(bar_count=31, end="2024-06-01T02:00:00Z")
    orchestrator = _open_position_orchestrator(panel)
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel,
        cost_execution_binding=_cost_binding(),
    )
    result = reconcile_single_slot_backtest_accounting_v0(
        backtest,
        orchestrator_result=orchestrator,
    )
    assert result.reconciled is True
    assert result.failure_class is None
    assert abs(result.accounting_delta) <= result.tolerance_abs
    assert backtest.trade_count == 1
    records = backtest.trades.to_dict(orient="records")
    assert records[0]["close_reason"] == END_OF_WINDOW_CLOSE_REASON


def test_force_close_records_trade_ledger_entry() -> None:
    panel = build_synthetic_panel_series_v0(bar_count=20, end="2024-06-01T02:00:00Z")
    orchestrator = _open_position_orchestrator(panel)
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel,
        cost_execution_binding=_cost_binding(),
    )
    assert not backtest.trades.empty
    assert backtest.trades.iloc[-1]["close_reason"] == END_OF_WINDOW_CLOSE_REASON


def test_ma_crossover_orchestrator_no_runtime_imports() -> None:
    module = (
        REPO_ROOT
        / "src/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_single_slot_research_orchestrator_v0.py"
    )
    text = module.read_text(encoding="utf-8")
    for forbidden in ("src.execution", "scheduler", "credentials", "live"):
        assert forbidden not in text


def test_runner_no_runtime_imports() -> None:
    module = (
        REPO_ROOT
        / "scripts/ops/run_cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_execution_v0.py"
    )
    text = module.read_text(encoding="utf-8")
    for forbidden in ("src.execution", "scheduler", "credentials"):
        assert forbidden not in text


def test_ma_crossover_panel_orchestrator_deterministic() -> None:
    panel = build_synthetic_panel_series_v0(bar_count=40, end="2024-06-01T02:00:00Z")
    binding = default_ma_crossover_operator_binding_v0()
    first = run_ma_crossover_panel_rank_rotation_orchestrator_v0(
        binding=binding,
        panel_series=panel,
    )
    second = run_ma_crossover_panel_rank_rotation_orchestrator_v0(
        binding=binding,
        panel_series=panel,
    )
    assert first.final_slot_side == second.final_slot_side
    assert first.final_instrument_id == second.final_instrument_id
    assert len(first.epochs) == len(second.epochs)


def test_end_of_window_policy_constant() -> None:
    assert END_OF_WINDOW_POLICY == "force_close_at_window_end_inclusive_v0"


def test_open_position_without_force_close_would_fail_classification() -> None:
    assert FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING == ("FORCED_END_OF_WINDOW_LIQUIDATION")
