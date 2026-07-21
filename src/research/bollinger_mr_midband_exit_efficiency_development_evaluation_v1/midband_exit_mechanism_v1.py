"""Frozen causal Bollinger side-aware middle-band exit-efficiency mechanism v1.

Research-local only. Reuses ``_calculate_bollinger_bands`` read-only; does not mutate
``src/strategies/bollinger.py``. No lookahead / future MFE. Fail-closed on missing bars.
"""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.constants_v1 import (
    BB_PERIOD,
    BB_STD,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
)
from src.strategies.bollinger import _calculate_bollinger_bands

MECHANISM_ID = "canonical_bollinger_side_aware_middle_band_exit_v1"


class MidbandExitMechanismError(ValueError):
    """Fail-closed midband exit mechanism error."""


def assert_frozen_parameters_match_contract(contract: Mapping[str, Any]) -> None:
    frozen = (contract.get("exit_mechanism") or {}).get("frozen_parameters") or {}
    if frozen != REQUIRED_FROZEN_EXIT_PARAMETERS:
        raise MidbandExitMechanismError("FROZEN_EXIT_PARAMETERS_MISMATCH")


def compute_middle_band(
    bars: pd.DataFrame, *, bb_period: int = BB_PERIOD, bb_std: float = BB_STD
) -> pd.Series:
    if bars is None or bars.empty:
        raise MidbandExitMechanismError("BARS_REQUIRED")
    if "close" not in bars.columns:
        raise MidbandExitMechanismError("BARS_MISSING_CLOSE")
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise MidbandExitMechanismError("BARS_INDEX_NOT_DATETIME")
    close = bars["close"].astype(float)
    _upper, middle, _lower = _calculate_bollinger_bands(
        close, period=int(bb_period), num_std=float(bb_std)
    )
    return middle


def long_exit_mask_from_bars(bars: pd.DataFrame) -> pd.Series:
    """LONG: close[t-1] < middle[t-1] AND close[t] >= middle[t]."""
    middle = compute_middle_band(bars)
    close = bars["close"].astype(float)
    mask = (close.shift(1) < middle.shift(1)) & (close >= middle)
    return mask.fillna(False).astype(bool)


def short_exit_mask_from_bars(bars: pd.DataFrame) -> pd.Series:
    """SHORT: close[t-1] > middle[t-1] AND close[t] <= middle[t]."""
    middle = compute_middle_band(bars)
    close = bars["close"].astype(float)
    mask = (close.shift(1) > middle.shift(1)) & (close <= middle)
    return mask.fillna(False).astype(bool)


def midband_exit_triggered(
    *, open_side: str | None, ts: pd.Timestamp, long_mask: pd.Series, short_mask: pd.Series
) -> bool:
    if open_side is None:
        return False
    if ts is None or len(long_mask) == 0:
        raise MidbandExitMechanismError("MISSING_STATE_OR_INDEX_BINDING")
    if open_side == "long":
        val = long_mask.asof(ts)
        if pd.isna(val):
            raise MidbandExitMechanismError("MISSING_LONG_EXIT_MASK_AT_TS")
        return bool(val)
    if open_side == "short":
        val = short_mask.asof(ts)
        if pd.isna(val):
            raise MidbandExitMechanismError("MISSING_SHORT_EXIT_MASK_AT_TS")
        return bool(val)
    raise MidbandExitMechanismError(f"OPEN_SIDE_UNKNOWN:{open_side}")


def force_exit_signal_for_open_side(open_side: str | None) -> int | None:
    """Return mapped exit/cover signal for an open side, or None if flat."""
    if open_side == "long":
        return -1
    if open_side == "short":
        return 1
    return None


def mechanism_freeze_payload() -> dict[str, Any]:
    return {
        "mechanism_id": MECHANISM_ID,
        "mechanism_class": "EXIT_EFFICIENCY",
        "frozen_parameters": dict(REQUIRED_FROZEN_EXIT_PARAMETERS),
        "lookahead_forbidden": True,
        "future_mfe_forbidden": True,
        "acts_after_entry_fill_only": True,
        "no_new_entry_authority": True,
        "no_new_side_selection_authority": True,
        "stop_loss_remains_active_if_hit_first": True,
    }


__all__ = [
    "MECHANISM_ID",
    "MidbandExitMechanismError",
    "assert_frozen_parameters_match_contract",
    "compute_middle_band",
    "force_exit_signal_for_open_side",
    "long_exit_mask_from_bars",
    "mechanism_freeze_payload",
    "midband_exit_triggered",
    "short_exit_mask_from_bars",
]
