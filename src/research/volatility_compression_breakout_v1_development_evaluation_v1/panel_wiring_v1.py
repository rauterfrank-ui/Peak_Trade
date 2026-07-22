"""Panel wiring: bind VCB treatment + unconditional baseline to panel series.

Does not invent metrics or exit PnL. Maps each instrument panel into the existing
strategy/baseline event producers and returns a typed handoff for the evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.research.unconditional_20_bar_price_channel_breakout_v1 import (
    generate_unconditional_20_bar_price_channel_breakout_events_v1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.binding_v1 import (
    assert_shared_channel_core_bound,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_compression_breakout_v1_strategy_v1 import (
    VolatilityCompressionBreakoutEventV1,
    generate_volatility_compression_breakout_events_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)


@dataclass(frozen=True)
class ArmEventSeriesV1:
    arm_id: str
    instrument_id: str
    timestamps_utc: tuple[str, ...]
    entry_sides: tuple[str, ...]
    entry_event_mask: tuple[bool, ...]

    @property
    def evaluable_entry_event_count(self) -> int:
        return sum(1 for flag in self.entry_event_mask if flag)


@dataclass(frozen=True)
class TreatmentBaselineWiringHandoffV1:
    """Typed handoff from panel wiring to the existing evaluator boundary."""

    treatment: tuple[ArmEventSeriesV1, ...]
    baseline: tuple[ArmEventSeriesV1, ...]
    shared_channel_core_bound: bool
    time_segment_definition_id: str
    baseline_id: str
    strategy_identity: str
    timestamps_utc: tuple[str, ...]

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
) -> TreatmentBaselineWiringHandoffV1:
    """Bind treatment + baseline event producers to the loaded DEVELOPMENT panel."""
    if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
        raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
    if not panel_series:
        raise ValueError("EMPTY_PANEL_SERIES")
    assert_shared_channel_core_bound()

    treatment_arms: list[ArmEventSeriesV1] = []
    baseline_arms: list[ArmEventSeriesV1] = []
    reference_timestamps: tuple[str, ...] | None = None

    for series in panel_series:
        frame = _panel_series_to_frame(series)
        timestamps = tuple(str(ts) for ts in frame["timestamp_utc"].tolist())
        if reference_timestamps is None:
            reference_timestamps = timestamps
        elif timestamps != reference_timestamps:
            raise ValueError(f"TIMESTAMP_ALIGNMENT_DRIFT:{series.instrument_id}")

        treatment_rows = generate_volatility_compression_breakout_events_v1(frame)
        baseline_rows = generate_unconditional_20_bar_price_channel_breakout_events_v1(frame)
        if len(treatment_rows) != len(timestamps) or len(baseline_rows) != len(timestamps):
            raise ValueError(f"EVENT_LENGTH_MISMATCH:{series.instrument_id}")

        treatment_arms.append(
            ArmEventSeriesV1(
                arm_id="TREATMENT",
                instrument_id=series.instrument_id,
                timestamps_utc=timestamps,
                entry_sides=tuple(_side_label(r.entry_side) for r in treatment_rows),
                entry_event_mask=tuple(
                    r.event is VolatilityCompressionBreakoutEventV1.ENTRY_EVENT
                    for r in treatment_rows
                ),
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

    assert reference_timestamps is not None
    return TreatmentBaselineWiringHandoffV1(
        treatment=tuple(treatment_arms),
        baseline=tuple(baseline_arms),
        shared_channel_core_bound=True,
        time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
        baseline_id=BASELINE_ID,
        strategy_identity=STRATEGY_IDENTITY,
        timestamps_utc=reference_timestamps,
    )


def cost_binding_for_canonical_backtest(cost_execution_binding: dict) -> dict:
    """Pass-through documenting reuse of canonical cost-binding shape."""
    return cost_execution_binding
