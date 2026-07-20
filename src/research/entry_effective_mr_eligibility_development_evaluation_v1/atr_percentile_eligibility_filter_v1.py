"""Frozen causal ATR-percentile mid-band eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Reuses the repo-canonical ATR and rolling
percentile-rank formulas from ``VolRegimeFilter`` / ``vol_breakout`` (SSOT
per config/config.toml [strategy.vol_regime_filter] defaults), but applies a
STRICT (exclusive) mid-band eligibility rule: eligible iff
``25 < rank < 75`` — NOT the inclusive ``>=``/``<=`` bounds used by
``VolRegimeFilter.generate_signals``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import pandas as pd

from src.strategies.vol_breakout import _rolling_last_pct_rank

FEATURE_FORMULA_ID = "entry_effective_mr_eligibility_atr_percentile_midband_features_v1"
FILTER_ID = "canonical_vol_regime_filter_atr_percentile_midband_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "vol_window": 14,
    "vol_method": "atr",
    "vol_percentile_low": 25,
    "vol_percentile_high": 75,
    "lookback_percentile": 100,
    "min_bars": 30,
    "regime_mode": False,
    "invert": False,
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_high_low_close_only",
    "lookahead_forbidden": True,
    "definitions": {
        "atr_14h": (
            "True Range (max(high-low, |high-prev_close|, |low-prev_close|)) "
            "ewm(span=14, min_periods=14, adjust=False).mean(); identical to "
            "VolRegimeFilter._compute_atr / VolBreakoutStrategy._compute_atr"
        ),
        "atr_14h_rolling_percentile_rank_100h": (
            "_rolling_last_pct_rank(atr_14h, window=100, min_periods=14) from "
            "src.strategies.vol_breakout; causal rolling percentile rank in [0,100] "
            "of the last value in each trailing 100-bar window"
        ),
        "eligibility_rule": (
            "ELIGIBLE iff rank is finite (notna) AND rank > 25.0 AND rank < 75.0 "
            "(STRICT / exclusive bounds); otherwise STAND_ASIDE. First min_bars=30 "
            "bars are always STAND_ASIDE regardless of rank."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
    "strict_bounds": True,
    "bounds_comparator": "eligible = rank.notna() & (rank > 25.0) & (rank < 75.0)",
    "distinction_from_vol_regime_filter_generate_signals": (
        "VolRegimeFilter.generate_signals uses inclusive >= / <= bounds; this "
        "eligibility rule uses STRICT (exclusive) > / < bounds instead."
    ),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_atr14(bars: pd.DataFrame) -> pd.Series:
    """ATR(14) via True Range + ewm(span=14, min_periods=14, adjust=False).

    Identical formula to ``VolRegimeFilter._compute_atr`` /
    ``VolBreakoutStrategy._compute_atr``.
    """
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    close = bars["close"].astype(float)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    vol_window = int(REQUIRED_FROZEN["vol_window"])
    atr = tr.ewm(span=vol_window, min_periods=vol_window, adjust=False).mean()
    atr.name = "atr_14h"
    return atr


def compute_percentile_rank(atr: pd.Series) -> pd.Series:
    """Causal rolling percentile rank (0-100) of ``atr`` over trailing 100 bars."""
    rank = _rolling_last_pct_rank(
        atr,
        window=int(REQUIRED_FROZEN["lookback_percentile"]),
        min_periods=int(REQUIRED_FROZEN["vol_window"]),
    )
    rank.name = "atr_14h_rolling_percentile_rank_100h"
    return rank


def eligibility_mask_from_rank(rank: pd.Series, *, min_bars: int | None = None) -> pd.Series:
    """Boolean eligibility mask from a precomputed percentile-rank series.

    ``eligible = rank.notna() & (rank > 25.0) & (rank < 75.0)`` — STRICT
    (exclusive) bounds; rank values exactly equal to 25 or 75 are NOT
    eligible. The first ``min_bars`` positions are unconditionally
    ineligible (warmup, stand aside). Exposed separately from
    :func:`eligibility_mask_from_bars` so the boundary rule can be unit
    tested directly on synthetic rank series.
    """
    low = float(REQUIRED_FROZEN["vol_percentile_low"])
    high = float(REQUIRED_FROZEN["vol_percentile_high"])
    eligible = rank.notna() & (rank > low) & (rank < high)
    mb = int(REQUIRED_FROZEN["min_bars"]) if min_bars is None else int(min_bars)
    if mb > 0:
        warmup = pd.Series(False, index=eligible.index)
        n_warmup = min(mb, len(warmup))
        if n_warmup > 0:
            warmup.iloc[:n_warmup] = True
        eligible = eligible.where(~warmup, False)
    eligible.name = "entry_eligibility"
    return eligible.astype(bool)


def eligibility_mask_from_bars(bars: pd.DataFrame) -> pd.Series:
    """Boolean eligibility mask: True iff STRICT mid-band rule holds.

    ``eligible = rank.notna() & (rank > 25.0) & (rank < 75.0)``; the first
    ``min_bars`` bars are unconditionally ineligible (warmup, stand aside).
    """
    atr = compute_atr14(bars)
    rank = compute_percentile_rank(atr)
    return eligibility_mask_from_rank(rank)


def eligibility_labels_from_bars(bars: pd.DataFrame) -> pd.Series:
    """String labels (``ELIGIBLE`` / ``STAND_ASIDE``) from the eligibility mask."""
    mask = eligibility_mask_from_bars(bars)
    labels = pd.Series(STAND_ASIDE, index=mask.index, dtype=object)
    labels = labels.where(~mask, ELIGIBLE)
    labels.name = "entry_eligibility_label"
    return labels


def formula_freeze_payload() -> dict[str, Any]:
    return {
        **FORMULA_SPEC,
        "feature_formula_sha256": feature_formula_sha256(),
        "threshold_adjustment_forbidden": True,
        "post_hoc_retune_forbidden": True,
    }


def assert_frozen_parameters_match_contract(contract: Mapping[str, Any]) -> None:
    eligibility = contract.get("eligibility_filter") or {}
    if str(eligibility.get("filter_id") or "") != FILTER_ID:
        raise ValueError("FILTER_ID_DRIFT")
    frozen = eligibility.get("frozen_parameters") or {}
    for key, expected in REQUIRED_FROZEN.items():
        if frozen.get(key) != expected:
            raise ValueError(f"FROZEN_PARAMETER_DRIFT:{key}")


__all__ = [
    "ELIGIBLE",
    "FEATURE_FORMULA_ID",
    "FILTER_ID",
    "FORMULA_SPEC",
    "REQUIRED_FROZEN",
    "STAND_ASIDE",
    "assert_frozen_parameters_match_contract",
    "compute_atr14",
    "compute_percentile_rank",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_bars",
    "eligibility_mask_from_rank",
    "feature_formula_sha256",
    "formula_freeze_payload",
]
