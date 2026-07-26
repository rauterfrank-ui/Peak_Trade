"""Momentum V2 vol-scaled own-instrument ENTRY/EXIT event emitter v1.

Frozen research-only signal for
``MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1``.

Treatment score:
  vol_scaled_momentum = (close/close.shift(N)-1) / std(one_bar_simple_returns, N)

Events (ENTRY_EXIT_EVENT_V1):
  +1 long entry when score crosses above entry_z from below
  -1 exit when score crosses below exit_z from above
  0 otherwise

No short-entry path. PIT-safe via signal_lag_bars=1. No evaluation/runtime/orders.
Does not mutate registry MomentumStrategy / momentum_1h.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_SIGNAL_V1=true"

STRATEGY_ID = "momentum_v2_volatility_scaled_own_instrument_continuation"
STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
PROGRAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
SIGNAL_FAMILY = "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM"
SIGNAL_FORMULA_VERSION = "vol_scaled_raw_return_over_trailing_realized_vol_v1"
SIGNAL_FORMULA_EXPRESSION = (
    "raw=(close[t-lag]/close[t-lag-N])/close[t-lag-N]; "
    "vol=std(one_bar_simple_returns over N ending at t-lag); "
    "score=raw/vol; entry=+1 on cross above entry_z; exit=-1 on cross below exit_z"
)

# Frozen non-grid parameters from preregistered measurement contract.
DEFAULT_LOOKBACK_PERIOD = 20
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_VOL_SCALED_ENTRY_Z = 1.0
DEFAULT_VOL_SCALED_EXIT_Z = 0.0
BASELINE_RAW_ENTRY_THRESHOLD = 0.02
BASELINE_RAW_EXIT_THRESHOLD = -0.01
BASELINE_ID = "FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1"
OUTPUT_CONTRACT = "ENTRY_EXIT_EVENT_V1"
ENTRY_SIDE = "NONE"
SHORT_ENTRY_FORBIDDEN = True
BTC_EXCLUDED = True
SPOT_EXCLUDED = True
INSTRUMENT_CLASS = "LINEAR_USDT_PERPETUAL"
SIGNAL_ENTRY_LONG = 1
SIGNAL_EXIT = -1
SIGNAL_NONE = 0

# Canonical research cost binding (integration identity only; no evaluation execution).
FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_BPS_PER_SIDE = 5.0
FEE_MODEL_VERSION = "backtest_fee_taker_symmetric_v0"
SLIPPAGE_MODEL_VERSION = "backtest_slippage_symmetric_v0"


@dataclass(frozen=True)
class MomentumV2VolScaledSignalObservationV1:
    instrument_id: str
    epoch_index: int
    raw_momentum: float
    realized_vol: float
    vol_scaled_momentum: float
    signal: int
    warmup_complete: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _is_spot_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return "spot" in lowered or ":spot:" in lowered


def is_eligible_universe_instrument_v1(instrument_id: str) -> bool:
    """Non-BTC OKX linear USDT perpetual universe binding (fail-closed)."""
    if not instrument_id:
        return False
    lowered = instrument_id.lower()
    if BTC_EXCLUDED and _is_bitcoin_instrument(instrument_id):
        return False
    if SPOT_EXCLUDED and _is_spot_instrument(instrument_id):
        return False
    if "linear_perpetual" not in lowered:
        return False
    if "usdt" not in lowered:
        return False
    return True


def _finite_positive(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def compute_raw_simple_return_v1(
    closes: Sequence[float],
    *,
    lookback_period: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """PIT-safe raw lookback simple return ending at epoch_index - lag."""
    if lookback_period <= 0 or signal_lag_bars < 0:
        return None
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lookback_period
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None
    base = float(closes[base_idx])
    current = float(closes[lag_idx])
    if not _finite_positive(base) or not _finite_positive(current):
        return None
    raw = (current / base) - 1.0
    if not math.isfinite(raw):
        return None
    return raw


def compute_trailing_realized_vol_v1(
    closes: Sequence[float],
    *,
    lookback_period: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Std of one-bar simple returns over lookback ending at epoch_index - lag."""
    if lookback_period <= 0 or signal_lag_bars < 0:
        return None
    lag_idx = epoch_index - signal_lag_bars
    start = lag_idx - lookback_period
    if start < 0 or lag_idx < 1 or lag_idx >= len(closes):
        return None
    returns: list[float] = []
    for i in range(start + 1, lag_idx + 1):
        prev = float(closes[i - 1])
        cur = float(closes[i])
        if not _finite_positive(prev) or not _finite_positive(cur):
            return None
        one_bar = (cur / prev) - 1.0
        if not math.isfinite(one_bar):
            return None
        returns.append(one_bar)
    if len(returns) != lookback_period:
        return None
    mean = sum(returns) / float(lookback_period)
    var = sum((r - mean) ** 2 for r in returns) / float(lookback_period)
    if not math.isfinite(var) or var < 0.0:
        return None
    vol = math.sqrt(var)
    if not math.isfinite(vol) or vol <= 0.0:
        # Fail-closed: zero/non-finite vol => no signal
        return None
    return vol


def compute_vol_scaled_momentum_v1(
    closes: Sequence[float],
    *,
    lookback_period: int = DEFAULT_LOOKBACK_PERIOD,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    epoch_index: int,
) -> tuple[float, float, float] | None:
    raw = compute_raw_simple_return_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    vol = compute_trailing_realized_vol_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if raw is None or vol is None:
        return None
    score = raw / vol
    if not math.isfinite(score):
        return None
    return raw, vol, score


def _cross_up(prev: float, cur: float, threshold: float) -> bool:
    return prev < threshold and cur > threshold


def _cross_down(prev: float, cur: float, threshold: float) -> bool:
    return prev > threshold and cur < threshold


def compute_entry_exit_event_v1(
    closes: Sequence[float],
    *,
    instrument_id: str,
    epoch_index: int,
    lookback_period: int = DEFAULT_LOOKBACK_PERIOD,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    entry_z: float = DEFAULT_VOL_SCALED_ENTRY_Z,
    exit_z: float = DEFAULT_VOL_SCALED_EXIT_Z,
) -> MomentumV2VolScaledSignalObservationV1 | None:
    """Emit ENTRY_EXIT_EVENT_V1 at epoch for one eligible instrument."""
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    if entry_z <= exit_z:
        return None
    if SHORT_ENTRY_FORBIDDEN is not True:
        return None
    for value in closes:
        if not math.isfinite(float(value)):
            return None
    current = compute_vol_scaled_momentum_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    previous = compute_vol_scaled_momentum_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index - 1,
    )
    if current is None or previous is None:
        return None
    raw, vol, score = current
    prev_score = previous[2]
    signal = SIGNAL_NONE
    if _cross_up(prev_score, score, entry_z):
        signal = SIGNAL_ENTRY_LONG
    elif _cross_down(prev_score, score, exit_z):
        signal = SIGNAL_EXIT
    # Hard invariant: never emit a short-entry semantic (no -1 reused as short).
    if signal not in (SIGNAL_NONE, SIGNAL_ENTRY_LONG, SIGNAL_EXIT):
        return None
    if signal == SIGNAL_EXIT:
        # Exit event only; cannot be reinterpreted as short entry.
        pass
    return MomentumV2VolScaledSignalObservationV1(
        instrument_id=instrument_id,
        epoch_index=epoch_index,
        raw_momentum=raw,
        realized_vol=vol,
        vol_scaled_momentum=score,
        signal=signal,
        warmup_complete=True,
    )


def compute_baseline_raw_entry_exit_event_v1(
    closes: Sequence[float],
    *,
    instrument_id: str,
    epoch_index: int,
    lookback_period: int = DEFAULT_LOOKBACK_PERIOD,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    entry_threshold: float = BASELINE_RAW_ENTRY_THRESHOLD,
    exit_threshold: float = BASELINE_RAW_EXIT_THRESHOLD,
) -> int | None:
    """Frozen raw momentum_1h baseline EVENT semantics for comparison tests."""
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    cur = compute_raw_simple_return_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    prev = compute_raw_simple_return_v1(
        closes,
        lookback_period=lookback_period,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index - 1,
    )
    if cur is None or prev is None:
        return None
    if _cross_up(prev, cur, entry_threshold):
        return SIGNAL_ENTRY_LONG
    if _cross_down(prev, cur, exit_threshold):
        return SIGNAL_EXIT
    return SIGNAL_NONE


def validate_frozen_parameters_v1(
    *,
    lookback_period: int,
    signal_lag_bars: int,
    entry_z: float,
    exit_z: float,
) -> bool:
    return (
        lookback_period == DEFAULT_LOOKBACK_PERIOD
        and signal_lag_bars == DEFAULT_SIGNAL_LAG_BARS
        and entry_z == DEFAULT_VOL_SCALED_ENTRY_Z
        and exit_z == DEFAULT_VOL_SCALED_EXIT_Z
    )


def canonical_round_trip_cost_bps_v1() -> float:
    """Identity of realistic fee+slippage binding (per side * 2 sides)."""
    return float(FEE_BPS_PER_SIDE + SLIPPAGE_BPS_PER_SIDE) * 2.0
