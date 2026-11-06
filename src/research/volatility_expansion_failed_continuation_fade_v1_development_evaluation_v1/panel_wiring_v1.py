"""Panel wiring: bind VEFCF treatment (strategy-emitted exits) + unconditional baseline.

Does not invent metrics or exit PnL. Treatment roundtrips are produced entirely by the
strategy's own exit state machine (`generate_vefcf_events_and_roundtrips_v1`); the
evaluator boundary must realize PnL directly from these strategy-emitted roundtrips
and must never reconstruct a missing exit (`simulate_arm_roundtrips_v1` is baseline-only
in this package). Reuses VCB's `ArmEventSeriesV1` typed handoff for both arms' event
masks (used for admission-gate event counting and baseline PnL realization).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.research.unconditional_20_bar_price_channel_breakout_v1 import (
    generate_unconditional_20_bar_price_channel_breakout_events_v1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_development_evaluation_v1.binding_v1 import (
    assert_exit_state_machine_bound,
    assert_shared_channel_core_bound,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_exit_state_machine_v1 import (
    open_position_from_fill_v1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_strategy_v1 import (
    VefcfEventV1,
    generate_vefcf_events_and_roundtrips_v1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_vol_state_v1 import (
    compute_atr14_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

__all__ = (
    "ArmEventSeriesV1",
    "StrategyEmittedRoundtripHandoffV1",
    "VefcfTreatmentBaselineWiringHandoffV1",
    "wire_treatment_and_baseline_panel_events_v1",
    "cost_binding_for_canonical_backtest",
)


@dataclass(frozen=True)
class StrategyEmittedRoundtripHandoffV1:
    """One strategy-emitted (entry, exit) roundtrip; PnL is realized, not reconstructed."""

    instrument_id: str
    side: str  # LONG/SHORT
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: str
    stop_price_at_entry: float


@dataclass(frozen=True)
class VefcfTreatmentBaselineWiringHandoffV1:
    """Typed handoff from panel wiring to the productive evaluator boundary.

    Treatment PnL truth is carried exclusively via ``treatment_strategy_roundtrips``
    (strategy-emitted exits). ``treatment`` event-series are retained only for
    admission-gate event counting (evaluable_treatment_breakout_events) and time-segment
    assignment; they are not used to re-derive treatment exits/PnL.
    """

    treatment: tuple[ArmEventSeriesV1, ...]
    baseline: tuple[ArmEventSeriesV1, ...]
    treatment_strategy_roundtrips: tuple[StrategyEmittedRoundtripHandoffV1, ...]
    shared_channel_core_bound: bool
    time_segment_definition_id: str
    baseline_id: str
    strategy_identity: str
    timestamps_utc: tuple[str, ...]
    strategy_emitted_exits_bound: bool = True
    evaluator_reconstruction_forbidden: bool = True

    @property
    def evaluable_treatment_breakout_events(self) -> int:
        return sum(arm.evaluable_entry_event_count for arm in self.treatment)


def _panel_series_to_frame(series: InstrumentPanelSeriesV1) -> pd.DataFrame:
    rows = [
        {
            "timestamp_utc": bar.timestamp_utc,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        for bar in series.bars
    ]
    if not rows:
        raise ValueError(f"EMPTY_INSTRUMENT_SERIES:{series.instrument_id}")
    frame = pd.DataFrame(rows)
    frame.index = pd.to_datetime(frame["timestamp_utc"], utc=True)
    return frame


def _side_label(side: StrategyEntrySideCarrierV1 | object) -> str:
    if side is StrategyEntrySideCarrierV1.LONG:
        return "LONG"
    if side is StrategyEntrySideCarrierV1.SHORT:
        return "SHORT"
    return "NONE"


def wire_treatment_and_baseline_panel_events_v1(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
) -> VefcfTreatmentBaselineWiringHandoffV1:
    """Bind treatment (strategy-emitted) + baseline event producers to the DEVELOPMENT panel."""
    if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
        raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
    if not panel_series:
        raise ValueError("EMPTY_PANEL_SERIES")
    assert_shared_channel_core_bound()
    assert_exit_state_machine_bound()

    treatment_arms: list[ArmEventSeriesV1] = []
    baseline_arms: list[ArmEventSeriesV1] = []
    strategy_roundtrips: list[StrategyEmittedRoundtripHandoffV1] = []
    reference_timestamps: tuple[str, ...] | None = None

    for series in panel_series:
        frame = _panel_series_to_frame(series)
        timestamps = tuple(str(ts) for ts in frame["timestamp_utc"].tolist())
        if reference_timestamps is None:
            reference_timestamps = timestamps
        elif timestamps != reference_timestamps:
            raise ValueError(f"TIMESTAMP_ALIGNMENT_DRIFT:{series.instrument_id}")

        bar_results, roundtrips = generate_vefcf_events_and_roundtrips_v1(frame)
        baseline_rows = generate_unconditional_20_bar_price_channel_breakout_events_v1(frame)
        if len(bar_results) != len(timestamps) or len(baseline_rows) != len(timestamps):
            raise ValueError(f"EVENT_LENGTH_MISMATCH:{series.instrument_id}")

        entry_event_mask = tuple(r.event is VefcfEventV1.ENTRY_EVENT for r in bar_results)
        if sum(entry_event_mask) != len(roundtrips):
            raise ValueError(f"ENTRY_ROUNDTRIP_COUNT_MISMATCH:{series.instrument_id}")

        treatment_arms.append(
            ArmEventSeriesV1(
                arm_id="TREATMENT",
                instrument_id=series.instrument_id,
                timestamps_utc=timestamps,
                entry_sides=tuple(_side_label(r.entry_side) for r in bar_results),
                entry_event_mask=entry_event_mask,
            )
        )
        baseline_arms.append(
            ArmEventSeriesV1(
                arm_id="BASELINE",
                instrument_id=series.instrument_id,
                timestamps_utc=timestamps,
                entry_sides=tuple(_side_label(r.entry_side) for r in baseline_rows),
                entry_event_mask=tuple(str(r.event) == "ENTRY_EVENT" for r in baseline_rows),
            )
        )

        if roundtrips:
            atr14 = compute_atr14_v1(frame["high"], frame["low"], frame["close"])
            for rt in roundtrips:
                atr_at_fill = float(atr14.iloc[rt.fill_index])
                position = open_position_from_fill_v1(
                    side=rt.side,  # type: ignore[arg-type]
                    fill_index=rt.fill_index,
                    entry_price=float(rt.entry_price),
                    atr_at_fill=atr_at_fill,
                    failed_impulse_extreme=float(rt.failed_impulse_extreme),
                )
                strategy_roundtrips.append(
                    StrategyEmittedRoundtripHandoffV1(
                        instrument_id=series.instrument_id,
                        side=rt.side,
                        signal_index=rt.signal_index,
                        fill_index=rt.fill_index,
                        exit_index=rt.exit_index,
                        entry_price=float(rt.entry_price),
                        exit_price=float(rt.exit_price),
                        exit_reason=rt.exit_reason.value,
                        stop_price_at_entry=float(position.stop_price),
                    )
                )

    assert reference_timestamps is not None
    return VefcfTreatmentBaselineWiringHandoffV1(
        treatment=tuple(treatment_arms),
        baseline=tuple(baseline_arms),
        treatment_strategy_roundtrips=tuple(strategy_roundtrips),
        shared_channel_core_bound=True,
        time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
        baseline_id=BASELINE_ID,
        strategy_identity=STRATEGY_IDENTITY,
        timestamps_utc=reference_timestamps,
    )


def cost_binding_for_canonical_backtest(cost_execution_binding: dict) -> dict:
    """Pass-through documenting reuse of canonical cost-binding shape."""
    return cost_execution_binding
