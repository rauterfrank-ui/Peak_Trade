"""Panel wiring: Momentum V2 vol-scaled treatment + raw-momentum baseline (strategy-emitted).

Both arms emit ENTRY_EXIT_EVENT_V1 (+1 entry / -1 exit). Roundtrips are paired from
those events; productive PnL is realized via the shared VCB evaluator (no second truth).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.binding_v1 import (
    assert_signal_implementation_bound,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1 import (
    BASELINE_RAW_ENTRY_THRESHOLD,
    BASELINE_RAW_EXIT_THRESHOLD,
    DEFAULT_LOOKBACK_PERIOD,
    DEFAULT_SIGNAL_LAG_BARS,
    DEFAULT_VOL_SCALED_ENTRY_Z,
    DEFAULT_VOL_SCALED_EXIT_Z,
    SIGNAL_ENTRY_LONG,
    SIGNAL_EXIT,
    SIGNAL_NONE,
    compute_raw_simple_return_v1,
    compute_vol_scaled_momentum_v1,
    is_eligible_universe_instrument_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
)
from src.research.volatility_compression_breakout_v1_vol_state_v1 import compute_atr20_v1

__all__ = (
    "ArmEventSeriesV1",
    "StrategyEmittedRoundtripHandoffV1",
    "MomentumV2TreatmentBaselineWiringHandoffV1",
    "wire_treatment_and_baseline_panel_events_v1",
    "cost_binding_for_canonical_backtest",
)


@dataclass(frozen=True)
class StrategyEmittedRoundtripHandoffV1:
    """One strategy-emitted (entry, exit) roundtrip; PnL is realized, not reconstructed."""

    instrument_id: str
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: str
    stop_price_at_entry: float


@dataclass(frozen=True)
class MomentumV2TreatmentBaselineWiringHandoffV1:
    """Typed handoff: both arms carry strategy-emitted roundtrips for productive PnL."""

    treatment: tuple[ArmEventSeriesV1, ...]
    baseline: tuple[ArmEventSeriesV1, ...]
    treatment_strategy_roundtrips: tuple[StrategyEmittedRoundtripHandoffV1, ...]
    baseline_strategy_roundtrips: tuple[StrategyEmittedRoundtripHandoffV1, ...]
    time_segment_definition_id: str
    baseline_id: str
    strategy_identity: str
    timestamps_utc: tuple[str, ...]
    strategy_emitted_exits_bound: bool = True
    evaluator_reconstruction_forbidden: bool = True
    holdout_accessed: bool = False

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
    # Keep a RangeIndex so integer fill/exit indices resolve positionally.
    return frame.reset_index(drop=True)


def _pair_entry_exit_roundtrips_v1(
    *,
    instrument_id: str,
    frame: pd.DataFrame,
    signals: Sequence[int],
) -> tuple[tuple[bool, ...], tuple[StrategyEmittedRoundtripHandoffV1, ...]]:
    """Pair +1/+(-1) events into LONG roundtrips; open positions liquidate at series end."""
    n = len(frame)
    if len(signals) != n:
        raise ValueError(f"SIGNAL_LENGTH_MISMATCH:{instrument_id}")
    atr = compute_atr20_v1(frame["high"], frame["low"], frame["close"])
    entry_mask = [False] * n
    roundtrips: list[StrategyEmittedRoundtripHandoffV1] = []
    open_sig: int | None = None
    open_fill: int | None = None
    open_entry_price: float | None = None
    open_stop: float | None = None

    for i, signal in enumerate(signals):
        if signal == SIGNAL_ENTRY_LONG and open_sig is None:
            fill_i = i  # lag already baked into score; fill at signal-bar open
            # Need at least one later bar for exit / end-of-series liquidation.
            if fill_i >= n - 1:
                continue
            entry_price = float(frame.iloc[fill_i]["open"])
            atr_v = float(atr.iloc[fill_i])
            if not (entry_price == entry_price) or entry_price <= 0:
                continue
            if not (atr_v == atr_v) or atr_v <= 0:
                continue
            entry_mask[i] = True
            open_sig = i
            open_fill = fill_i
            open_entry_price = entry_price
            open_stop = entry_price - atr_v
        elif signal == SIGNAL_EXIT and open_sig is not None and open_fill is not None:
            exit_i = i
            if exit_i <= open_fill:
                continue
            exit_price = float(frame.iloc[exit_i]["open"])
            if not (exit_price == exit_price) or exit_price <= 0:
                continue
            roundtrips.append(
                StrategyEmittedRoundtripHandoffV1(
                    instrument_id=instrument_id,
                    side="LONG",
                    signal_index=int(open_sig),
                    fill_index=int(open_fill),
                    exit_index=int(exit_i),
                    entry_price=float(open_entry_price),
                    exit_price=exit_price,
                    exit_reason="SIGNAL_EXIT",
                    stop_price_at_entry=float(open_stop),
                )
            )
            open_sig = None
            open_fill = None
            open_entry_price = None
            open_stop = None

    if open_sig is not None and open_fill is not None and open_entry_price is not None:
        exit_i = n - 1
        if exit_i <= open_fill:
            raise ValueError(f"UNPAIRABLE_ENTRY_NO_EXIT:{instrument_id}")
        exit_price = float(frame.iloc[exit_i]["close"])
        if not (exit_price == exit_price) or exit_price <= 0:
            raise ValueError(f"UNPAIRABLE_ENTRY_INVALID_EXIT_PRICE:{instrument_id}")
        roundtrips.append(
            StrategyEmittedRoundtripHandoffV1(
                instrument_id=instrument_id,
                side="LONG",
                signal_index=int(open_sig),
                fill_index=int(open_fill),
                exit_index=int(exit_i),
                entry_price=float(open_entry_price),
                exit_price=exit_price,
                exit_reason="END_OF_INSTRUMENT_LIQUIDATION",
                stop_price_at_entry=float(open_stop or open_entry_price),
            )
        )
    if sum(entry_mask) != len(roundtrips):
        raise ValueError(f"ENTRY_ROUNDTRIP_COUNT_MISMATCH:{instrument_id}")
    return tuple(entry_mask), tuple(roundtrips)


def _streaming_treatment_signals_v1(
    *,
    instrument_id: str,
    closes: Sequence[float],
) -> list[int]:
    """ENTRY/EXIT events for vol-scaled treatment (frozen params; one score/bar)."""
    n = len(closes)
    out = [SIGNAL_NONE] * n
    if not is_eligible_universe_instrument_v1(instrument_id):
        return out
    lookback = DEFAULT_LOOKBACK_PERIOD
    lag = DEFAULT_SIGNAL_LAG_BARS
    entry_z = DEFAULT_VOL_SCALED_ENTRY_Z
    exit_z = DEFAULT_VOL_SCALED_EXIT_Z
    prev_score: float | None = None
    for i in range(n):
        packed = compute_vol_scaled_momentum_v1(
            closes,
            lookback_period=lookback,
            signal_lag_bars=lag,
            epoch_index=i,
        )
        if packed is None:
            prev_score = None
            continue
        score = packed[2]
        if prev_score is not None:
            if prev_score < entry_z and score > entry_z:
                out[i] = SIGNAL_ENTRY_LONG
            elif prev_score > exit_z and score < exit_z:
                out[i] = SIGNAL_EXIT
        prev_score = score
    return out


def _streaming_baseline_signals_v1(
    *,
    instrument_id: str,
    closes: Sequence[float],
) -> list[int]:
    """ENTRY/EXIT events for frozen raw-return baseline (one score/bar)."""
    n = len(closes)
    out = [SIGNAL_NONE] * n
    if not is_eligible_universe_instrument_v1(instrument_id):
        return out
    lookback = DEFAULT_LOOKBACK_PERIOD
    lag = DEFAULT_SIGNAL_LAG_BARS
    entry_thr = BASELINE_RAW_ENTRY_THRESHOLD
    exit_thr = BASELINE_RAW_EXIT_THRESHOLD
    prev_raw: float | None = None
    for i in range(n):
        raw = compute_raw_simple_return_v1(
            closes,
            lookback_period=lookback,
            signal_lag_bars=lag,
            epoch_index=i,
        )
        if raw is None:
            prev_raw = None
            continue
        if prev_raw is not None:
            if prev_raw < entry_thr and raw > entry_thr:
                out[i] = SIGNAL_ENTRY_LONG
            elif prev_raw > exit_thr and raw < exit_thr:
                out[i] = SIGNAL_EXIT
        prev_raw = raw
    return out


def _emit_signals_for_arm(
    *,
    instrument_id: str,
    closes: Sequence[float],
    n: int,
    treatment: bool,
) -> list[int]:
    _ = n
    if treatment:
        return _streaming_treatment_signals_v1(instrument_id=instrument_id, closes=closes)
    return _streaming_baseline_signals_v1(instrument_id=instrument_id, closes=closes)


def wire_treatment_and_baseline_panel_events_v1(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    repo_root=None,
    time_segment_definition_id: str = TIME_SEGMENT_DEFINITION_ID,
) -> MomentumV2TreatmentBaselineWiringHandoffV1:
    """Bind treatment + baseline ENTRY/EXIT producers to the DEVELOPMENT panel."""
    if time_segment_definition_id != TIME_SEGMENT_DEFINITION_ID:
        raise ValueError("TIME_SEGMENT_BINDING_MISMATCH")
    if not panel_series:
        raise ValueError("EMPTY_PANEL_SERIES")
    if repo_root is not None:
        assert_signal_implementation_bound(repo_root)

    treatment_arms: list[ArmEventSeriesV1] = []
    baseline_arms: list[ArmEventSeriesV1] = []
    treatment_roundtrips: list[StrategyEmittedRoundtripHandoffV1] = []
    baseline_roundtrips: list[StrategyEmittedRoundtripHandoffV1] = []
    reference_timestamps: tuple[str, ...] | None = None

    for series in panel_series:
        if not is_eligible_universe_instrument_v1(series.instrument_id):
            raise ValueError(f"INELIGIBLE_INSTRUMENT:{series.instrument_id}")
        frame = _panel_series_to_frame(series)
        timestamps = tuple(str(ts) for ts in frame["timestamp_utc"].tolist())
        if reference_timestamps is None:
            reference_timestamps = timestamps
        elif timestamps != reference_timestamps:
            raise ValueError(f"TIMESTAMP_ALIGNMENT_DRIFT:{series.instrument_id}")
        closes = tuple(float(x) for x in frame["close"].tolist())
        n = len(closes)

        treatment_signals = _emit_signals_for_arm(
            instrument_id=series.instrument_id, closes=closes, n=n, treatment=True
        )
        baseline_signals = _emit_signals_for_arm(
            instrument_id=series.instrument_id, closes=closes, n=n, treatment=False
        )
        t_mask, t_rts = _pair_entry_exit_roundtrips_v1(
            instrument_id=series.instrument_id, frame=frame, signals=treatment_signals
        )
        b_mask, b_rts = _pair_entry_exit_roundtrips_v1(
            instrument_id=series.instrument_id, frame=frame, signals=baseline_signals
        )

        treatment_arms.append(
            ArmEventSeriesV1(
                arm_id="TREATMENT",
                instrument_id=series.instrument_id,
                timestamps_utc=timestamps,
                entry_sides=tuple("LONG" if m else "NONE" for m in t_mask),
                entry_event_mask=t_mask,
            )
        )
        baseline_arms.append(
            ArmEventSeriesV1(
                arm_id="BASELINE",
                instrument_id=series.instrument_id,
                timestamps_utc=timestamps,
                entry_sides=tuple("LONG" if m else "NONE" for m in b_mask),
                entry_event_mask=b_mask,
            )
        )
        if sum(t_mask) != len(t_rts):
            raise ValueError(f"ENTRY_ROUNDTRIP_COUNT_MISMATCH:{series.instrument_id}")
        treatment_roundtrips.extend(t_rts)
        baseline_roundtrips.extend(b_rts)

    assert reference_timestamps is not None
    return MomentumV2TreatmentBaselineWiringHandoffV1(
        treatment=tuple(treatment_arms),
        baseline=tuple(baseline_arms),
        treatment_strategy_roundtrips=tuple(treatment_roundtrips),
        baseline_strategy_roundtrips=tuple(baseline_roundtrips),
        time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
        baseline_id=BASELINE_ID,
        strategy_identity=STRATEGY_IDENTITY,
        timestamps_utc=reference_timestamps,
    )


def cost_binding_for_canonical_backtest(cost_execution_binding: dict) -> dict:
    return cost_execution_binding
