"""RV(24) + cross-sectional RV-level rank helpers for CSLRVC v1.

Authority is the preregistered measurement contract admission_mechanism.vol_estimator.
- RV = close-to-close log-return sample stdev over exactly 24 returns
- Cross-sectional rank = WEAK_LEQ empirical CDF of RV levels at the same timestamp
- panel_members_required_min = 10 finite eligible RV observations
- BTC and spot instruments are excluded from the ranking universe
- ATR(14) reused for initial-stop sizing only (exit), not admission
- No look-ahead; no forward-fill; incomplete history → NaN
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from src.research.volatility_contraction_expansion_breakout_v1_vol_state_v1 import (
    ATR_NORMALIZATION_V1,
    ATR_PERIOD_V1,
    ATR_SMOOTHING_V1,
    PERCENTILE_TIE_METHOD_V1,
    RV_METHOD_V1,
    RV_NORMALIZATION_V1,
    RV_PERIOD_V1,
    compute_atr14_v1,
    compute_close_to_close_log_returns_v1,
    compute_normalized_atr14_v1,
    compute_realized_volatility_24_v1,
)
from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    percentile_rank_weak_leq_empirical_cdf_v1,
)

PANEL_MEMBERS_REQUIRED_MIN_V1 = 10
SHORT_HORIZON_RETURN_LOOKBACK_COMPLETED_BARS_V1 = 8
VOL_ESTIMATOR_FAMILY_V1 = "REALIZED_VOLATILITY_CROSS_SECTIONAL_RANK"
CS_RANK_METRIC_V1 = "CROSS_SECTIONAL_PERCENTILE_RANK_OF_RV_LEVEL"
VOL_STATE_OWNER = "research.cross_sectional_low_realized_volatility_continuation_v1_vol_state_v1"

_BTC_TOKENS = ("btc", "xbt", "bitcoin")
_SPOT_TOKENS = ("-spot", "_spot", "/spot", " spot")


def is_bitcoin_instrument_v1(instrument_id: str) -> bool:
    lowered = str(instrument_id).lower()
    return any(token in lowered for token in _BTC_TOKENS)


def is_spot_instrument_v1(instrument_id: str) -> bool:
    lowered = str(instrument_id).lower()
    if lowered.endswith("-spot") or lowered.endswith("_spot"):
        return True
    if any(token in lowered for token in _SPOT_TOKENS):
        return True
    # OKX linear perpetuals are *-SWAP; bare *-USDT without SWAP is treated as spot.
    if lowered.endswith("-usdt") and "swap" not in lowered and "perp" not in lowered:
        return True
    return False


def is_cslrvc_eligible_instrument_v1(instrument_id: str) -> bool:
    """BTC and spot excluded; only SWAP/perp-like IDs remain eligible."""
    if is_bitcoin_instrument_v1(instrument_id):
        return False
    if is_spot_instrument_v1(instrument_id):
        return False
    return True


def filter_eligible_instrument_ids_v1(instrument_ids: Sequence[str]) -> list[str]:
    return [iid for iid in instrument_ids if is_cslrvc_eligible_instrument_v1(iid)]


def compute_cross_sectional_rv_level_rank_at_timestamp_v1(
    panel_rv_by_instrument: Mapping[str, float],
    *,
    panel_members_required_min: int = PANEL_MEMBERS_REQUIRED_MIN_V1,
) -> dict[str, Optional[float]]:
    """WEAK_LEQ CS percentile of RV level at one timestamp.

    Ineligible instruments (BTC/spot) are omitted from the ranking universe and
    receive ``None``. Instruments with non-finite RV receive ``None``. If fewer
    than ``panel_members_required_min`` finite eligible RVs exist, all ranks are
    ``None`` (fail-closed insufficient cross-section).
    """
    if panel_members_required_min != PANEL_MEMBERS_REQUIRED_MIN_V1:
        raise ValueError("panel_members_required_min_must_match_preregistration")

    eligible_finite: list[tuple[str, float]] = []
    out: dict[str, Optional[float]] = {}
    for instrument_id, raw in panel_rv_by_instrument.items():
        if not is_cslrvc_eligible_instrument_v1(instrument_id):
            out[instrument_id] = None
            continue
        value = float(raw)
        if not np.isfinite(value):
            out[instrument_id] = None
            continue
        eligible_finite.append((instrument_id, value))

    if len(eligible_finite) < panel_members_required_min:
        for instrument_id, _ in eligible_finite:
            out[instrument_id] = None
        return out

    window_values = [v for _, v in eligible_finite]
    for instrument_id, value in eligible_finite:
        out[instrument_id] = percentile_rank_weak_leq_empirical_cdf_v1(
            window_values, current_value=value
        )
    return out


def compute_cross_sectional_rv_rank_wide_panel_v1(
    rv_wide: pd.DataFrame,
    *,
    panel_members_required_min: int = PANEL_MEMBERS_REQUIRED_MIN_V1,
) -> pd.DataFrame:
    """Row-wise same-timestamp CS RV-level ranks; columns = instruments.

    No forward-fill. Incomplete / ineligible / undersized rows → NaN ranks.
    Future rows are never used (row-local only).

    Vectorized WEAK_LEQ empirical-CDF ranks matching
    ``compute_cross_sectional_rv_level_rank_at_timestamp_v1`` semantics
    (BTC/spot columns are omitted from the ranking universe and receive NaN).
    """
    if panel_members_required_min != PANEL_MEMBERS_REQUIRED_MIN_V1:
        raise ValueError("panel_members_required_min_must_match_preregistration")
    if rv_wide.ndim != 2:
        raise ValueError("rv_wide_must_be_2d")

    eligible_mask = np.array(
        [is_cslrvc_eligible_instrument_v1(str(col)) for col in rv_wide.columns],
        dtype=bool,
    )
    values = rv_wide.to_numpy(dtype=np.float64, copy=False)
    n_rows, n_cols = values.shape
    out = np.full((n_rows, n_cols), np.nan, dtype=np.float64)
    for row_i in range(n_rows):
        row = values[row_i]
        finite_eligible = eligible_mask & np.isfinite(row)
        finite_count = int(finite_eligible.sum())
        if finite_count < panel_members_required_min:
            continue
        finite_vals = row[finite_eligible]
        sorted_vals = np.sort(finite_vals)
        leq_counts = np.searchsorted(sorted_vals, finite_vals, side="right")
        ranks_finite = leq_counts.astype(np.float64) / float(finite_count)
        out[row_i, finite_eligible] = ranks_finite
    return pd.DataFrame(out, index=rv_wide.index, columns=rv_wide.columns, dtype=float)


def compute_vol_state_instrument_column_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    cs_rv_rank: pd.Series | None = None,
) -> pd.DataFrame:
    """Per-instrument RV(24)+ATR14; optional precomputed CS rank column."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    close = data[close_col]
    rv = compute_realized_volatility_24_v1(close)
    atr = compute_atr14_v1(data[high_col], data[low_col], close)
    if cs_rv_rank is None:
        rank = pd.Series(np.nan, index=data.index, dtype=float)
    else:
        if len(cs_rv_rank) != len(data) or not cs_rv_rank.index.equals(data.index):
            raise ValueError("CS_RV_RANK_INDEX_MISMATCH")
        rank = cs_rv_rank.astype(float)
    return pd.DataFrame(
        {
            "realized_volatility_24": rv,
            "cs_rv_rank": rank,
            "atr14": atr,
        },
        index=data.index,
    )


__all__ = [
    "ATR_NORMALIZATION_V1",
    "ATR_PERIOD_V1",
    "ATR_SMOOTHING_V1",
    "CS_RANK_METRIC_V1",
    "PANEL_MEMBERS_REQUIRED_MIN_V1",
    "PERCENTILE_TIE_METHOD_V1",
    "RV_METHOD_V1",
    "RV_NORMALIZATION_V1",
    "RV_PERIOD_V1",
    "SHORT_HORIZON_RETURN_LOOKBACK_COMPLETED_BARS_V1",
    "VOL_ESTIMATOR_FAMILY_V1",
    "VOL_STATE_OWNER",
    "compute_atr14_v1",
    "compute_close_to_close_log_returns_v1",
    "compute_cross_sectional_rv_level_rank_at_timestamp_v1",
    "compute_cross_sectional_rv_rank_wide_panel_v1",
    "compute_normalized_atr14_v1",
    "compute_realized_volatility_24_v1",
    "compute_vol_state_instrument_column_v1",
    "filter_eligible_instrument_ids_v1",
    "is_bitcoin_instrument_v1",
    "is_cslrvc_eligible_instrument_v1",
    "is_spot_instrument_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]
