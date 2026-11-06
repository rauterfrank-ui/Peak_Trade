"""Forensic regression: baseline UNPAIRABLE near panel end + durable run-state claim.

Does not re-execute the canonical development evaluation against the real panel.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
    EXIT_PARAMS_DECLARATIVE_V1,
    SIGNAL_LAG_BARS_V1,
    build_effective_cost_config_from_binding_v1,
    evaluate_arm_productive_pnl_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.binding_v1 import (
    resolve_cost_execution_binding,
    resolve_measurement_contract,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    HYPOTHESIS_ID,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.evaluate_path_v1 import (
    run_authorized_development_evaluation_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.guards_v1 import (
    assert_no_slot_reuse,
    slot_already_consumed,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.panel_wiring_v1 import (
    VepcTreatmentBaselineWiringHandoffV1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
)

REPO = Path(__file__).resolve().parents[2]

# Forensic reproduction constants matching the authorized VEPC attempt.
FORENSIC_INSTRUMENT_ID = "okx:linear_perpetual:AGLD:USDT:USDT:perp"
FORENSIC_ENTRY_INDEX = 10575
FORENSIC_SERIES_LENGTH = 10586
FORENSIC_ENTRY_SIDE = "SHORT"


def _authorized_decision() -> AuthorizationDecisionV1:
    return AuthorizationDecisionV1(
        authorized=True,
        authorize_token_valid=True,
        repo_development_evaluation_authorized=True,
        program_development_evaluation_authorized=True,
        entry_point_binding_authorized=True,
        reason_codes=(),
    )


def _effective_cost():
    contract = resolve_measurement_contract(REPO)
    return build_effective_cost_config_from_binding_v1(
        resolve_cost_execution_binding(contract),
        cost_multiplier=1.0,
    )


def _synthetic_agld_geometry_panel() -> tuple[InstrumentPanelSeriesV1, int]:
    """Compact series with the same end-of-panel geometry as AGLD@10575.

    Real panel: n=10586, entry_i=10575, fill_i=10576, only 9 post-fill bars,
    TIME_EXIT requires 48 bars; SHORT never hits stop/trail/regime before EOI.
    """
    max_bars = int(EXIT_PARAMS_DECLARATIVE_V1["time_exit_max_bars"])
    lag = int(SIGNAL_LAG_BARS_V1)
    # Warmup for ATR20 + percentile_rank_120, then late entry with 9 post-fill bars.
    warmup = 160
    post_fill = 9
    entry_i = warmup
    fill_i = entry_i + lag
    n = fill_i + 1 + post_fill
    assert n - (fill_i + 1) == post_fill
    assert fill_i + max_bars >= n  # TIME_EXIT geometrically unreachable

    bars: list[PanelBarV1] = []
    # Calm path after SHORT fill: price drifts down (no stop hit for SHORT).
    start = pd.Timestamp("2023-01-01T00:00:00Z")
    for i in range(n):
        base = 0.58
        px = base - 0.0001 * max(0, i - fill_i)
        ts = (start + pd.Timedelta(hours=i)).isoformat().replace("+00:00", "Z")
        bars.append(
            PanelBarV1(
                instrument_id=FORENSIC_INSTRUMENT_ID,
                timestamp_utc=ts,
                open=f"{px:.6f}",
                high=f"{px + 0.001:.6f}",
                low=f"{px - 0.001:.6f}",
                close=f"{px:.6f}",
                volume="1",
                is_final=True,
            )
        )
    series = InstrumentPanelSeriesV1(
        instrument_id=FORENSIC_INSTRUMENT_ID,
        native_instrument_id="AGLD",
        bars=tuple(bars),
        series_digest="forensic_agld_geometry_v1",
    )
    return series, entry_i


def test_baseline_declarative_pairing_eoi_closes_agld_end_of_series_geometry() -> None:
    """Canonical EOI pairs late SHORT entry when TIME_EXIT is unreachable (no retry)."""
    series, entry_i = _synthetic_agld_geometry_panel()
    n = len(series.bars)
    lag = int(SIGNAL_LAG_BARS_V1)
    fill_i = entry_i + lag
    max_bars = int(EXIT_PARAMS_DECLARATIVE_V1["time_exit_max_bars"])
    assert FORENSIC_ENTRY_SIDE == "SHORT"
    assert n - (fill_i + 1) == 9
    assert fill_i + max_bars >= n

    mask = tuple(i == entry_i for i in range(n))
    sides = tuple(FORENSIC_ENTRY_SIDE if i == entry_i else "NONE" for i in range(n))
    timestamps = tuple(b.timestamp_utc for b in series.bars)
    arm = ArmEventSeriesV1(
        arm_id="BASELINE",
        instrument_id=FORENSIC_INSTRUMENT_ID,
        timestamps_utc=timestamps,
        entry_sides=sides,
        entry_event_mask=mask,
    )
    result = evaluate_arm_productive_pnl_v1(
        panel_series=[series],
        arm=arm,
        effective_cost=_effective_cost(),
    )
    assert result.trade_count == 1
    tr = result.trades[0]
    assert tr.exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert tr.exit_index == n - 1
    assert tr.entry_index == fill_i
    assert tr.side == "short"
    assert tr.instrument_id == FORENSIC_INSTRUMENT_ID


class _RaisingBoundary(FakeExecutionBoundaryV1):
    """Raises the forensic UNPAIRABLE reason during productive backtest."""

    def run_canonical_backtest(
        self,
        panel: PanelLoadResultV1,
        *,
        cost_execution_binding: Mapping[str, Any],
        cost_multiplier: float = 1.0,
    ) -> BacktestMetricsBundleV1:
        _ = panel, cost_execution_binding, cost_multiplier
        self.backtest_calls += 1
        raise ValueError(
            f"UNPAIRABLE_ENTRY_NO_EXIT:{FORENSIC_INSTRUMENT_ID}:{FORENSIC_ENTRY_INDEX}"
        )


def _panel_for_boundary() -> PanelLoadResultV1:
    segments = partition_chronological_equal_duration_quarters_v1()
    timestamps = tuple(seg.start_inclusive for seg in segments)
    bars = tuple(
        PanelBarV1(
            instrument_id="INST_A",
            timestamp_utc=ts,
            open="100",
            high="101",
            low="99",
            close="100.5",
            volume="1",
            is_final=True,
        )
        for ts in timestamps
    )
    series = InstrumentPanelSeriesV1(
        instrument_id="INST_A",
        native_instrument_id="INST_A",
        bars=bars,
        series_digest="fake_dataset_digest",
    )
    return PanelLoadResultV1(
        dataset_id=DATASET_ID,
        dataset_digest="fake_dataset_digest",
        panel_series=(series,),
        timestamps_utc=timestamps,
        instrument_count=1,
        holdout_accessed=False,
    )


def test_technical_fail_after_runner_start_persists_durable_slot_claim(tmp_path: Path) -> None:
    """CONSUMED_NO_RETRY: exhausted SSOT slot rejects any further authorized evaluate."""
    panel = _panel_for_boundary()
    n = len(panel.timestamps_utc)
    arm = ArmEventSeriesV1(
        arm_id="TREATMENT",
        instrument_id="INST_A",
        timestamps_utc=panel.timestamps_utc,
        entry_sides=tuple("LONG" if i == 0 else "NONE" for i in range(n)),
        entry_event_mask=tuple(i == 0 for i in range(n)),
    )
    handoff = VepcTreatmentBaselineWiringHandoffV1(
        treatment=(arm,),
        baseline=(arm,),
        treatment_strategy_roundtrips=(),
        shared_channel_core_bound=True,
        time_segment_definition_id="CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1",
        baseline_id="UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1",
        strategy_identity="VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1",
        timestamps_utc=panel.timestamps_utc,
    )
    boundary = _RaisingBoundary(
        panel=panel,
        canonical_metrics=BacktestMetricsBundleV1(
            gross_return=0.0,
            net_return=0.0,
            gross_profit_factor=0.0,
            net_profit_factor=0.0,
            gross_pnl=0.0,
            net_expectancy=0.0,
            sharpe=0.0,
            max_drawdown=0.0,
            trade_count=0,
            evaluable_treatment_breakout_events=0,
            baseline_net_profit_factor=0.0,
            baseline_gross_profit_factor=0.0,
            baseline_trade_count=0,
            cost_multiplier=1.0,
        ),
        stress_metrics=BacktestMetricsBundleV1(
            gross_return=0.0,
            net_return=0.0,
            gross_profit_factor=0.0,
            net_profit_factor=0.0,
            gross_pnl=0.0,
            net_expectancy=0.0,
            sharpe=0.0,
            max_drawdown=0.0,
            trade_count=0,
            evaluable_treatment_breakout_events=0,
            baseline_net_profit_factor=0.0,
            baseline_gross_profit_factor=0.0,
            baseline_trade_count=0,
            cost_multiplier=1.5,
        ),
        wiring_handoff=handoff,
    )
    with pytest.raises(Exception, match="RUN_LIMIT_EXHAUSTED|RETRY_OR_SLOT_REUSE_REJECTED"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=tmp_path,
            execution_boundary=boundary,
            authorization_decision=_authorized_decision(),
            persist_evidence=True,
        )
    assert slot_already_consumed(tmp_path) is False
    assert boundary.backtest_calls == 0


def test_forensic_index_constants_match_observed_incident() -> None:
    """Pin the observed AGLD incident coordinates for governance continuity."""
    assert FORENSIC_ENTRY_INDEX == 10575
    assert FORENSIC_SERIES_LENGTH == 10586
    assert FORENSIC_SERIES_LENGTH - FORENSIC_ENTRY_INDEX == 11
    lag = int(SIGNAL_LAG_BARS_V1)
    fill_i = FORENSIC_ENTRY_INDEX + lag
    assert FORENSIC_SERIES_LENGTH - (fill_i + 1) == 9
    assert int(EXIT_PARAMS_DECLARATIVE_V1["time_exit_max_bars"]) == 48


def test_historical_vepc_slot_consumed_no_retry_governance_recorded() -> None:
    """Historical VEPC slot remains CONSUMED_NO_RETRY; no eval retry authorized."""
    import json

    decision = (
        REPO / "docs/governance/"
        "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_HISTORICAL_SLOT_"
        "CONSUMED_NO_RETRY_AND_BASELINE_END_OF_SERIES_PAIRING_V1.md"
    )
    text = decision.read_text(encoding="utf-8")
    assert "CONSUMED_NO_RETRY" in text
    assert "NO Development evaluation re-execution" in text
    binding = json.loads(
        (
            REPO / "config/research/"
            "volatility_expansion_pullback_continuation_v1_development_evaluation_"
            "entry_point_binding_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["status"] == "RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT"
    assert binding["development_evaluation_executed"] is False
    assert binding["retry_forbidden"] is True
