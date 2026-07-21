"""Composite side-aware midband-cross OR max-holding exit-efficiency mechanism v6.

Research-local only. Reuses V1 midband helpers by import; does not mutate
``midband_exit_mechanism_v1.py``. Max-holding horizon frozen at 48 PT1H bars.
"""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    MidbandExitMechanismError,
    compute_middle_band,
    force_exit_signal_for_open_side,
    long_exit_mask_from_bars,
    midband_exit_triggered,
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.constants_v6 import (
    MAX_HOLDING_BARS,
    MAX_HOLDING_FREQUENCY,
    MAX_HOLDING_HORIZON_HOURS,
    MAX_HOLDING_SOURCE_FIELD,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
)

MECHANISM_ID = "canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1"


def assert_frozen_parameters_match_contract(contract: Mapping[str, Any]) -> None:
    frozen = (contract.get("exit_mechanism") or {}).get("frozen_parameters") or {}
    if frozen != REQUIRED_FROZEN_EXIT_PARAMETERS:
        raise MidbandExitMechanismError("FROZEN_EXIT_PARAMETERS_MISMATCH")


def max_holding_exit_triggered(
    *,
    entry_fill_index: int | None,
    bar_index: int,
    max_holding_bars: int = MAX_HOLDING_BARS,
) -> bool:
    if entry_fill_index is None:
        return False
    return (bar_index - entry_fill_index) >= max_holding_bars


def composite_exit_triggered(
    *,
    open_side: str | None,
    ts: pd.Timestamp,
    long_mask: pd.Series,
    short_mask: pd.Series,
    entry_fill_index: int | None,
    bar_index: int,
    max_holding_bars: int = MAX_HOLDING_BARS,
) -> tuple[bool, str | None]:
    midband = midband_exit_triggered(
        open_side=open_side,
        ts=ts,
        long_mask=long_mask,
        short_mask=short_mask,
    )
    max_hold = max_holding_exit_triggered(
        entry_fill_index=entry_fill_index,
        bar_index=bar_index,
        max_holding_bars=max_holding_bars,
    )
    if midband and max_hold:
        return True, "midband_and_max_holding"
    if midband:
        return True, "midband"
    if max_hold:
        return True, "max_holding"
    return False, None


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
        "composite_exit_efficiency": True,
        "includes_max_holding_horizon_exit": True,
        "max_holding_horizon_hours": MAX_HOLDING_HORIZON_HOURS,
        "max_holding_bars": MAX_HOLDING_BARS,
        "max_holding_frequency": MAX_HOLDING_FREQUENCY,
        "max_holding_source_field": MAX_HOLDING_SOURCE_FIELD,
    }


__all__ = [
    "MECHANISM_ID",
    "MidbandExitMechanismError",
    "assert_frozen_parameters_match_contract",
    "composite_exit_triggered",
    "compute_middle_band",
    "force_exit_signal_for_open_side",
    "long_exit_mask_from_bars",
    "max_holding_exit_triggered",
    "mechanism_freeze_payload",
    "midband_exit_triggered",
    "short_exit_mask_from_bars",
]
