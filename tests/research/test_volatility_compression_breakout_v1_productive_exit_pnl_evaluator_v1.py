"""Focused tests for VCB productive exit/PnL evaluator binding (no evaluation run)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    FEE_BPS_PER_SIDE,
    SLIPPAGE_BPS_PER_SIDE,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.execution_boundary_v1 import (
    PanelLoadResultV1,
    RealExecutionBoundaryV1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
    TreatmentBaselineWiringHandoffV1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
    CANONICAL_PNL_PRIMITIVE_OWNER,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_OWNER,
    assert_development_dataset_only,
    build_effective_cost_config_from_binding_v1,
    evaluate_arm_productive_pnl_v1,
    evaluate_treatment_and_baseline_productive_pnl_v1,
    productive_exit_pnl_evaluator_is_bound,
    simulate_arm_roundtrips_v1,
)
from src.backtest.engine import (
    _compute_directional_gross_pnl_v0,
    _compute_roundtrip_fee_slippage_components_v0,
)

REPO = Path(__file__).resolve().parents[2]
FAIL_CLOSED_REPORT = (
    REPO
    / "docs/evidence/evaluate_volatility_compression_breakout_development_v1/fail_closed_report.json"
)


def _cost_binding() -> dict:
    return {
        "binding_version": "v1",
        "implicit_zero_cost_forbidden": True,
        "fee_model_binding": {
            "fee_bps_per_side": FEE_BPS_PER_SIDE,
            "fee_model_version": "backtest_fee_taker_symmetric_v0",
        },
        "slippage_model_binding": {
            "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
            "slippage_model_version": "backtest_slippage_symmetric_v0",
        },
        "spread_model_binding": {
            "conservative_half_spread_bps": 5.0,
            "spread_model_version": "research_conservative_bps_v1",
        },
    }


def _bars_trending(
    *,
    n: int = 200,
    start: float = 100.0,
    drift: float = 0.2,
    instrument_id: str = "INST_A",
) -> InstrumentPanelSeriesV1:
    bars = []
    px = start
    for i in range(n):
        o = px
        c = px + drift
        h = max(o, c) + 0.5
        l = min(o, c) - 0.5
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=f"2022-06-01T{i % 24:02d}:00:00Z",
                open=str(o),
                high=str(h),
                low=str(l),
                close=str(c),
                volume="1",
                is_final=True,
            )
        )
        px = c
    return InstrumentPanelSeriesV1(
        instrument_id=instrument_id,
        native_instrument_id=instrument_id,
        bars=tuple(bars),
        series_digest="synthetic",
    )


def _arm(
    *,
    arm_id: str,
    instrument_id: str,
    n: int,
    entry_indexes: list[int],
    side: str = "LONG",
) -> ArmEventSeriesV1:
    mask = [False] * n
    sides = ["NONE"] * n
    for idx in entry_indexes:
        mask[idx] = True
        sides[idx] = side
    ts = tuple(f"2022-06-01T{i % 24:02d}:00:00Z" for i in range(n))
    return ArmEventSeriesV1(
        arm_id=arm_id,
        instrument_id=instrument_id,
        timestamps_utc=ts,
        entry_sides=tuple(sides),
        entry_event_mask=tuple(mask),
    )


def test_import_safe_no_runner_no_counter_mutation() -> None:
    before = read_run_counters(REPO)
    mod = importlib.import_module(
        "src.research.volatility_compression_breakout_v1_development_evaluation_v1."
        "productive_exit_pnl_evaluator_v1"
    )
    importlib.reload(mod)
    assert productive_exit_pnl_evaluator_is_bound() is True
    assert PRODUCTIVE_EXIT_PNL_EVALUATOR_OWNER
    assert CANONICAL_PNL_PRIMITIVE_OWNER.endswith("_compute_directional_gross_pnl_v0")
    after = read_run_counters(REPO)
    assert after == before
    assert after["contract_runner_start_count"] == 1
    assert after["contract_development_run_count"] == 1


def test_productive_evaluator_bound_and_reuses_engine_primitives() -> None:
    assert productive_exit_pnl_evaluator_is_bound() is True
    cost = build_effective_cost_config_from_binding_v1(_cost_binding(), cost_multiplier=1.0)
    gross = _compute_directional_gross_pnl_v0(
        size=1.0, entry_price=100.0, exit_price=110.0, side="long"
    )
    assert gross == pytest.approx(10.0)
    fees = _compute_roundtrip_fee_slippage_components_v0(
        size=1.0, entry_price=100.0, exit_price=110.0, effective_cost=cost
    )
    assert fees[0] > 0 and fees[1] > 0 and fees[2] > 0 and fees[3] > 0


def test_long_and_short_roundtrip_pnl_and_costs() -> None:
    series = _bars_trending(n=220, drift=0.3)
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    long_arm = _arm(arm_id="T", instrument_id="INST_A", n=220, entry_indexes=[150], side="LONG")
    short_series = _bars_trending(n=220, drift=-0.3)
    short_arm = _arm(arm_id="T", instrument_id="INST_A", n=220, entry_indexes=[150], side="SHORT")
    long_trades = simulate_arm_roundtrips_v1(
        panel_series=(series,), arm=long_arm, effective_cost=cost
    )
    short_trades = simulate_arm_roundtrips_v1(
        panel_series=(short_series,), arm=short_arm, effective_cost=cost
    )
    assert len(long_trades) == 1
    assert len(short_trades) == 1
    assert long_trades[0].side == "long"
    assert short_trades[0].side == "short"
    assert long_trades[0].entry_fee > 0
    assert long_trades[0].exit_fee > 0
    assert long_trades[0].entry_slippage > 0
    assert long_trades[0].exit_slippage > 0
    assert long_trades[0].stop_price_at_entry < long_trades[0].entry_price
    assert short_trades[0].stop_price_at_entry > short_trades[0].entry_price
    assert long_trades[0].size > 0
    assert short_trades[0].size > 0


def test_baseline_treatment_identical_pnl_semantics() -> None:
    series = _bars_trending(n=220, drift=0.25)
    arm_t = _arm(arm_id="TREATMENT", instrument_id="INST_A", n=220, entry_indexes=[160])
    arm_b = _arm(arm_id="BASELINE", instrument_id="INST_A", n=220, entry_indexes=[160])
    handoff = TreatmentBaselineWiringHandoffV1(
        treatment=(arm_t,),
        baseline=(arm_b,),
        shared_channel_core_bound=True,
        time_segment_definition_id="CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1",
        baseline_id="UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1",
        strategy_identity="VOLATILITY_COMPRESSION_BREAKOUT_V1",
        timestamps_utc=arm_t.timestamps_utc,
    )
    treatment, baseline = evaluate_treatment_and_baseline_productive_pnl_v1(
        dataset_id=DATASET_ID,
        panel_series=(series,),
        handoff=handoff,
        cost_execution_binding=_cost_binding(),
        cost_multiplier=1.0,
    )
    assert treatment.trade_count == baseline.trade_count == 1
    assert treatment.net_profit_factor == pytest.approx(baseline.net_profit_factor)
    assert treatment.gross_pnl == pytest.approx(baseline.gross_pnl)


def test_unpairable_entry_fail_closed() -> None:
    series = _bars_trending(n=180, drift=0.1)
    # Entry too late for lag+exit window → unpairable.
    arm = _arm(arm_id="T", instrument_id="INST_A", n=180, entry_indexes=[179])
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    with pytest.raises(ValueError, match="UNPAIRABLE_ENTRY"):
        simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)


def test_holdout_and_wrong_dataset_rejected() -> None:
    with pytest.raises(ValueError, match="HOLDOUT_DATASET_REJECTED|DATASET_ID_NOT_BOUND"):
        assert_development_dataset_only("offline_economic_reevaluation_sealed_long_panel_v1")
    with pytest.raises(ValueError, match="DATASET_ID_NOT_BOUND"):
        assert_development_dataset_only("some_other_dataset")
    assert_development_dataset_only(DATASET_ID)


def test_development_only_enforced_on_evaluator() -> None:
    series = _bars_trending(n=220)
    arm = _arm(arm_id="T", instrument_id="INST_A", n=220, entry_indexes=[160])
    handoff = TreatmentBaselineWiringHandoffV1(
        treatment=(arm,),
        baseline=(arm,),
        shared_channel_core_bound=True,
        time_segment_definition_id="CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1",
        baseline_id="UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1",
        strategy_identity="VOLATILITY_COMPRESSION_BREAKOUT_V1",
        timestamps_utc=arm.timestamps_utc,
    )
    with pytest.raises(ValueError, match="DATASET_ID_NOT_BOUND"):
        evaluate_treatment_and_baseline_productive_pnl_v1(
            dataset_id="wrong",
            panel_series=(series,),
            handoff=handoff,
            cost_execution_binding=_cost_binding(),
        )


def test_prior_125_treatment_events_recognized_without_evaluation() -> None:
    before = read_run_counters(REPO)
    payload = json.loads(FAIL_CLOSED_REPORT.read_text(encoding="utf-8"))
    assert payload["evaluable_treatment_events_observed_before_fail_closed"] == 125
    assert payload["evaluation_executed"] is False
    # Principally evaluable count is a wiring property, not an evaluation run.
    arm = _arm(arm_id="T", instrument_id="INST_A", n=125, entry_indexes=list(range(125)))
    assert arm.evaluable_entry_event_count == 125
    assert read_run_counters(REPO) == before
    assert before["contract_runner_start_count"] == 1


def test_real_boundary_no_longer_raises_unbound() -> None:
    series = _bars_trending(n=220, drift=0.2)
    arm = _arm(arm_id="TREATMENT", instrument_id="INST_A", n=220, entry_indexes=[155])
    panel = PanelLoadResultV1(
        dataset_id=DATASET_ID,
        dataset_digest="synthetic",
        panel_series=(series,),
        timestamps_utc=arm.timestamps_utc,
        instrument_count=1,
        holdout_accessed=False,
    )
    real = RealExecutionBoundaryV1()

    def _fake_wire(p: PanelLoadResultV1) -> TreatmentBaselineWiringHandoffV1:
        a = _arm(arm_id="TREATMENT", instrument_id="INST_A", n=220, entry_indexes=[155])
        b = _arm(arm_id="BASELINE", instrument_id="INST_A", n=220, entry_indexes=[155])
        return TreatmentBaselineWiringHandoffV1(
            treatment=(a,),
            baseline=(b,),
            shared_channel_core_bound=True,
            time_segment_definition_id="CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1",
            baseline_id="UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1",
            strategy_identity="VOLATILITY_COMPRESSION_BREAKOUT_V1",
            timestamps_utc=a.timestamps_utc,
        )

    real.wire_treatment_baseline = _fake_wire  # type: ignore[method-assign]
    before = read_run_counters(REPO)
    bundle = real.run_canonical_backtest(
        panel, cost_execution_binding=_cost_binding(), cost_multiplier=1.0
    )
    assert bundle.trade_count >= 1
    assert bundle.evaluable_treatment_breakout_events == 1
    assert bundle.extras.get("productive_exit_pnl_evaluator_bound") is True
    assert read_run_counters(REPO) == before
