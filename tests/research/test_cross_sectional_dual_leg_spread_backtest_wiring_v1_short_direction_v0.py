"""Regression tests for dual-leg spread v1 backtest wiring SHORT direction sign."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.research.cross_sectional_dual_leg_spread_backtest_wiring_v1 import (
    _close_leg,
    run_dual_leg_spread_panel_backtest_v1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_research_orchestrator_v1 import (
    DualLegOrchestratorEpochResultV1,
    DualLegOrchestratorRunResultV1,
    DualLegSelectionEventV1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
    build_cost_execution_binding_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

INST_LONG = "okx:linear_perpetual:ETH:USDT:USDT:perp"
INST_SHORT = "okx:linear_perpetual:SOL:USDT:USDT:perp"


def _panel_bar(instrument_id: str, ts: str, close: float) -> PanelBarV1:
    return PanelBarV1(
        instrument_id=instrument_id,
        timestamp_utc=ts,
        open=str(close - 0.01),
        high=str(close + 0.02),
        low=str(close - 0.02),
        close=str(close),
        volume="1000",
        is_final=True,
    )


def _minimal_dual_leg_panel_v0() -> tuple[InstrumentPanelSeriesV1, ...]:
    start = datetime(2024, 5, 1, 0, 0, tzinfo=timezone.utc)
    bars_long = tuple(
        _panel_bar(
            INST_LONG, (start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"), 100.0 + i
        )
        for i in range(3)
    )
    bars_short = tuple(
        _panel_bar(
            INST_SHORT,
            (start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            50.0 + i * 2.0,
        )
        for i in range(3)
    )
    return (
        InstrumentPanelSeriesV1(
            instrument_id=INST_LONG,
            native_instrument_id=INST_LONG,
            bars=bars_long,
            series_digest="fixture-long",
        ),
        InstrumentPanelSeriesV1(
            instrument_id=INST_SHORT,
            native_instrument_id=INST_SHORT,
            bars=bars_short,
            series_digest="fixture-short",
        ),
    )


def _selection(
    *,
    epoch_index: int,
    ts: str,
    active: bool,
    long_id: str | None = None,
    short_id: str | None = None,
) -> DualLegSelectionEventV1:
    return DualLegSelectionEventV1(
        epoch_index=epoch_index,
        timestamp_utc=ts,
        ranked_instrument_ids=(long_id, short_id) if long_id and short_id else (),
        spread_bps=1.0 if active else None,
        long_instrument_id=long_id,
        short_instrument_id=short_id,
        active=active,
        pending_switch=False,
        eligible_member_count=2,
    )


def _epoch(
    *,
    epoch_index: int,
    ts: str,
    active: bool,
    long_id: str | None = None,
    short_id: str | None = None,
) -> DualLegOrchestratorEpochResultV1:
    return DualLegOrchestratorEpochResultV1(
        epoch_index=epoch_index,
        timestamp_utc=ts,
        selection=_selection(
            epoch_index=epoch_index,
            ts=ts,
            active=active,
            long_id=long_id,
            short_id=short_id,
        ),
        error_codes=(),
    )


@pytest.fixture(name="cost_binding")
def fixture_cost_binding() -> dict:
    return build_cost_execution_binding_v1()


def test_close_leg_short_direction_is_numeric_negative_v0() -> None:
    trades: list[dict] = []
    fee_drag = [0.0]
    slippage = [0.0]
    new_equity = _close_leg(
        side="SHORT",
        instrument_id=INST_SHORT,
        entry_price=100.0,
        entry_ts="2024-05-01T00:00:00Z",
        equity_at_entry=5_000.0,
        exit_price=110.0,
        exit_ts="2024-05-01T01:00:00Z",
        equity=10_000.0,
        exit_bps=20.0,
        fee_bps=10.0,
        entry_bps=20.0,
        slip_bps=10.0,
        trades=trades,
        total_fee_drag=fee_drag,
        total_slippage=slippage,
    )
    assert isinstance(new_equity, float)
    assert len(trades) == 1
    gross_pnl_frac = trades[0]["gross_pnl_frac"]
    assert isinstance(gross_pnl_frac, float)
    assert gross_pnl_frac == pytest.approx(-0.1)
    assert gross_pnl_frac < 0.0


def test_close_leg_long_direction_positive_on_price_rise_v0() -> None:
    trades: list[dict] = []
    fee_drag = [0.0]
    slippage = [0.0]
    _close_leg(
        side="LONG",
        instrument_id=INST_LONG,
        entry_price=100.0,
        entry_ts="2024-05-01T00:00:00Z",
        equity_at_entry=5_000.0,
        exit_price=110.0,
        exit_ts="2024-05-01T01:00:00Z",
        equity=10_000.0,
        exit_bps=20.0,
        fee_bps=10.0,
        entry_bps=20.0,
        slip_bps=10.0,
        trades=trades,
        total_fee_drag=fee_drag,
        total_slippage=slippage,
    )
    assert trades[0]["gross_pnl_frac"] == pytest.approx(0.1)


def test_backtest_short_leg_close_path_completes_without_type_error_v0(
    cost_binding: dict,
) -> None:
    panel = _minimal_dual_leg_panel_v0()
    orchestrator = DualLegOrchestratorRunResultV1(
        orchestrator_version="test",
        score_formula_version="test",
        epochs=(
            _epoch(
                epoch_index=0,
                ts="2024-05-01T00:00:00Z",
                active=True,
                long_id=INST_LONG,
                short_id=INST_SHORT,
            ),
            _epoch(
                epoch_index=1,
                ts="2024-05-01T01:00:00Z",
                active=False,
            ),
        ),
        final_long_instrument_id=None,
        final_short_instrument_id=None,
        final_active=False,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )
    result = run_dual_leg_spread_panel_backtest_v1(
        orchestrator,
        panel,
        cost_execution_binding=cost_binding,
    )
    short_trades = result.trades[result.trades["side"] == "SHORT"]
    assert not short_trades.empty
    assert float(short_trades.iloc[0]["gross_pnl_frac"]) < 0.0
