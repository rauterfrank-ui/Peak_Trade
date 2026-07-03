"""Contract tests for cross-sectional trade-record schema and backtest wiring v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.backtest.stats import TradeRecordContractError, compute_trade_stats
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v2 import (
    GO_TOKEN,
    run_full_offline_economic_evaluation_v2,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorEpochResultV0,
    OrchestratorRunResultV0,
    SingleSlotSelectionEventV0,
    SlotSide,
    default_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from src.research.cross_sectional_trade_record_schema_v0 import (
    CANONICAL_PNL_FIELD,
    PNL_UNIT,
    TradeRecordContractError as AdapterTradeRecordContractError,
    compute_roundtrip_net_pnl_v0,
    normalize_trades_for_stats_v0,
    validate_trade_record_for_stats_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    materialize_panel_staging_source_manifests_v1,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _cost_binding() -> dict:
    binding = materialize_versioned_research_binding_v0()
    return binding["cost_execution_binding"]


def _rotation_orchestrator(
    panel: tuple,
    *,
    instrument_id: str = "okx:linear_perpetual:ETH-USDT",
) -> OrchestratorRunResultV0:
    ts0 = panel[0].bars[0].timestamp_utc
    ts1 = panel[0].bars[1].timestamp_utc
    return OrchestratorRunResultV0(
        orchestrator_version="test.orchestrator",
        score_formula_version="test.score",
        epochs=(
            OrchestratorEpochResultV0(
                epoch_index=0,
                timestamp_utc=ts0,
                scores=(),
                selection=SingleSlotSelectionEventV0(
                    epoch_index=0,
                    timestamp_utc=ts0,
                    ranked_instrument_ids=(instrument_id,),
                    top_score=1.0,
                    selected_instrument_id=instrument_id,
                    slot_side=SlotSide.LONG,
                    pending_switch=False,
                    eligible_member_count=len(panel),
                ),
                error_codes=(),
            ),
            OrchestratorEpochResultV0(
                epoch_index=1,
                timestamp_utc=ts1,
                scores=(),
                selection=SingleSlotSelectionEventV0(
                    epoch_index=1,
                    timestamp_utc=ts1,
                    ranked_instrument_ids=(),
                    top_score=None,
                    selected_instrument_id=None,
                    slot_side=SlotSide.FLAT,
                    pending_switch=True,
                    eligible_member_count=len(panel),
                ),
                error_codes=(),
            ),
        ),
        final_slot_side=SlotSide.FLAT,
        final_instrument_id=None,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def _run_backtest(*, bar_count: int = 31, with_rotation: bool = True) -> object:
    panel = build_synthetic_panel_series_v0(bar_count=bar_count, end="2024-06-01T02:00:00Z")
    if with_rotation:
        orchestrator = _rotation_orchestrator(panel)
    else:
        orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
            binding=default_operator_binding_v0(),
            panel_series=panel,
        )
    return run_single_slot_panel_backtest_v0(
        orchestrator,
        panel,
        cost_execution_binding=_cost_binding(),
    )


def test_a_canonical_trade_record_processed_by_compute_trade_stats() -> None:
    trade = {
        "entry_time": "2024-05-30T20:00:00Z",
        "exit_time": "2024-05-30T21:00:00Z",
        "instrument_id": "okx:linear_perpetual:ETH-USDT",
        "side": "LONG",
        "entry_price": 100.0,
        "exit_price": 110.0,
        "gross_pnl_frac": 0.1,
        "gross_pnl": 100.0,
        "entry_cost": 5.0,
        "exit_cost": 5.0,
        CANONICAL_PNL_FIELD: 90.0,
        "pnl_unit": PNL_UNIT,
    }
    validate_trade_record_for_stats_v0(trade)
    stats = compute_trade_stats([trade])
    assert stats.total_trades == 1
    assert stats.winning_trades == 1
    assert stats.profit_factor == 0.0


def test_b_missing_pnl_fail_closed_in_compute_trade_stats() -> None:
    malformed = {"side": "LONG", "gross_pnl_frac": 0.01}
    with pytest.raises(TradeRecordContractError, match="trade_record_missing_canonical_pnl_field"):
        compute_trade_stats([malformed])


def test_b_missing_pnl_fail_closed_in_adapter() -> None:
    with pytest.raises(
        AdapterTradeRecordContractError,
        match="trade_record_missing_canonical_pnl_field",
    ):
        validate_trade_record_for_stats_v0({"gross_pnl_frac": 0.01})


def test_c_producer_consumer_parity() -> None:
    result = _run_backtest()
    records = result.trades.to_dict(orient="records")
    assert records, "expected at least one trade from synthetic panel"
    for record in records:
        assert CANONICAL_PNL_FIELD in record
        assert record["pnl_unit"] == PNL_UNIT
        assert "entry_cost" in record
        assert "exit_cost" in record
        assert "gross_pnl" in record
    normalized = normalize_trades_for_stats_v0(records)
    stats = compute_trade_stats(normalized)
    assert stats.total_trades == len(records)


def test_d_gross_net_semantics_no_double_cost() -> None:
    equity_at_entry = 10_000.0
    equity_before_exit = 10_500.0
    gross_pnl_frac = 0.02
    exit_cost = 10.0
    gross_abs, net_abs = compute_roundtrip_net_pnl_v0(
        equity_at_entry=equity_at_entry,
        equity_before_exit=equity_before_exit,
        gross_pnl_frac=gross_pnl_frac,
        exit_cost=exit_cost,
    )
    assert gross_abs == pytest.approx(equity_before_exit * gross_pnl_frac)
    expected_after = equity_before_exit * (1.0 + gross_pnl_frac) - exit_cost
    assert net_abs == pytest.approx(expected_after - equity_at_entry)

    result = _run_backtest()
    for row in result.trades.to_dict(orient="records"):
        assert row["entry_cost"] > 0
        assert row["exit_cost"] > 0
        assert row["gross_pnl_frac"] != 0.0
        assert row[CANONICAL_PNL_FIELD] == pytest.approx(
            row["gross_pnl"] - row["entry_cost"] - row["exit_cost"],
            rel=0.02,
            abs=25.0,
        )


def test_e_empty_trades_explicit_state() -> None:
    stats = compute_trade_stats([])
    assert stats.total_trades == 0
    assert stats.win_rate == 0.0
    assert stats.profit_factor == 0.0


def test_f_long_short_symmetry() -> None:
    long_trade = {
        CANONICAL_PNL_FIELD: 100.0,
        "side": SlotSide.LONG.value,
    }
    short_trade = {
        CANONICAL_PNL_FIELD: -100.0,
        "side": SlotSide.SHORT.value,
    }
    long_stats = compute_trade_stats([long_trade])
    short_stats = compute_trade_stats([short_trade])
    assert long_stats.winning_trades == 1
    assert short_stats.losing_trades == 1
    assert long_stats.avg_win == pytest.approx(abs(short_stats.avg_loss))


def test_g_serialization_roundtrip_preserves_pnl_fields() -> None:
    result = _run_backtest()
    payload = json.dumps(result.trades.to_dict(orient="records"), sort_keys=True)
    restored = json.loads(payload)
    for record in restored:
        validate_trade_record_for_stats_v0(record)
        assert record["pnl_unit"] == PNL_UNIT
    stats = compute_trade_stats(restored)
    assert stats.total_trades == len(restored)


def test_h_execution_v2_integration_no_key_error() -> None:
    complete_binding = materialize_versioned_research_binding_v0()
    scope_ratification = (
        materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
    )
    tmp = Path(tempfile.mkdtemp(prefix="cs_rs_trade_schema_e2e_"))
    panel = build_synthetic_panel_series_v0(bar_count=31, end="2024-06-01T02:00:00Z")
    staging = write_bound_period_staging_v0(tmp, panel_series=panel)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    (lifecycle / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "source_snapshot_ref": "test:trade_schema",
                "source_snapshot_digest": "d" * 64,
                "registered": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    materialize_panel_staging_source_manifests_v1(staging)
    result = run_full_offline_economic_evaluation_v2(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.economic_evaluation_executed is True
    assert result.backtest is not None
    if not result.backtest.trades.empty:
        assert CANONICAL_PNL_FIELD in result.backtest.trades.columns
