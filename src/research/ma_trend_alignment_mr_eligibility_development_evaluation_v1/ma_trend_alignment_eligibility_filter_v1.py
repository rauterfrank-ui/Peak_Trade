"""Frozen causal MA (SMA-50) trend-alignment eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Uses the SSOT SMA computation from
``rsi_reversion.py`` (``price.rolling(window=trend_ma_window).mean()`` with
``trend_ma_window=50`` from ``config/config.toml``
``[strategies.rsi_reversion.defaults]``). Side-aware with-trend admission
only: long entries require ``close > SMA(50)``; short entries require
``close < SMA(50)``. Does NOT use ADX/RSI/ATR features.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import pandas as pd

FEATURE_FORMULA_ID = "ma_trend_alignment_mr_eligibility_sma50_features_v1"
FILTER_ID = "canonical_ma_trend_alignment_entry_eligibility_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "ma_period": 50,
    "ma_type": "SMA",
    "side_aware": True,
    "warmup_bars": 50,
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_high_low_close_only",
    "lookahead_forbidden": True,
    "calculator_ssot": "src/strategies/rsi_reversion.py",
    "calculator_method": "SMA_ROLLING_MEAN",
    "definitions": {
        "sma_50h": (
            "SMA(50) of close via price.rolling(window=50).mean() (rsi_reversion.py "
            "SSOT, config.toml [strategies.rsi_reversion.defaults] trend_ma_window=50) "
            "over trailing finalized PT1H closes; first 50 bars are warmup"
        ),
        "eligibility_rule": (
            "For a long entry-candidate (signal==1): ELIGIBLE iff close > SMA(50). "
            "For a short entry-candidate (signal==-1): ELIGIBLE iff close < SMA(50). "
            "Otherwise STAND_ASIDE. First warmup_bars=50 bars are always STAND_ASIDE. "
            "Side-aware admission only; does not change direction/side."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_sma50(bars: pd.DataFrame) -> pd.Series:
    """SMA(50) of close via SSOT ``rsi_reversion.py`` (``price.rolling(window=50).mean()``)."""
    if int(REQUIRED_FROZEN["ma_period"]) != 50:
        raise ValueError("MA_PERIOD_DRIFT")
    if str(REQUIRED_FROZEN["ma_type"]) != "SMA":
        raise ValueError("MA_TYPE_DRIFT")
    period = int(REQUIRED_FROZEN["ma_period"])
    close = bars["close"].astype(float)
    sma = close.rolling(window=period).mean()
    sma.name = "sma_50h"
    return sma


def _warmup_mask(index: pd.Index, *, warmup_bars: int | None = None) -> pd.Series:
    wb = int(REQUIRED_FROZEN["warmup_bars"]) if warmup_bars is None else int(warmup_bars)
    warmup = pd.Series(False, index=index)
    n_warmup = min(wb, len(warmup))
    if n_warmup > 0:
        warmup.iloc[:n_warmup] = True
    return warmup


def long_eligible_mask_from_bars(
    bars: pd.DataFrame, *, warmup_bars: int | None = None
) -> pd.Series:
    """Boolean mask: True iff a long entry-candidate is admissible (close > SMA50)."""
    if not bool(REQUIRED_FROZEN["side_aware"]):
        raise ValueError("SIDE_AWARE_DRIFT")
    close = bars["close"].astype(float)
    sma = compute_sma50(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = close.notna() & sma.notna() & (close > sma)
    eligible = eligible.where(~warmup, False)
    eligible.name = "long_entry_eligibility"
    return eligible.astype(bool)


def short_eligible_mask_from_bars(
    bars: pd.DataFrame, *, warmup_bars: int | None = None
) -> pd.Series:
    """Boolean mask: True iff a short entry-candidate is admissible (close < SMA50)."""
    if not bool(REQUIRED_FROZEN["side_aware"]):
        raise ValueError("SIDE_AWARE_DRIFT")
    close = bars["close"].astype(float)
    sma = compute_sma50(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = close.notna() & sma.notna() & (close < sma)
    eligible = eligible.where(~warmup, False)
    eligible.name = "short_entry_eligibility"
    return eligible.astype(bool)


def eligibility_mask_from_bars(bars: pd.DataFrame, *, warmup_bars: int | None = None) -> pd.Series:
    """Combined (long OR short) admissibility mask.

    INFORMATIONAL ONLY: used for bar-share attribution (``mean_eligible_bar_share``)
    across the decision segment. It is NOT the side-aware entry-effective gate
    condition — the actual gate (see ``panel_runner_v1.is_entry_eligible``) always
    evaluates eligibility against the specific candidate side (``signal``), never
    against this OR-combined mask.
    """
    long_mask = long_eligible_mask_from_bars(bars, warmup_bars=warmup_bars)
    short_mask = short_eligible_mask_from_bars(bars, warmup_bars=warmup_bars)
    combined = long_mask | short_mask
    combined.name = "entry_eligibility"
    return combined.astype(bool)


def eligibility_labels_from_bars(bars: pd.DataFrame) -> pd.Series:
    """String labels (``ELIGIBLE`` / ``STAND_ASIDE``) from the combined eligibility mask."""
    mask = eligibility_mask_from_bars(bars)
    labels = pd.Series(STAND_ASIDE, index=mask.index, dtype=object)
    labels = labels.where(~mask, ELIGIBLE)
    labels.name = "entry_eligibility_label"
    return labels


def is_entry_eligible(*, signal: int, close: float, sma: float, in_warmup: bool) -> bool:
    """Side-aware entry-effective eligibility for a single mapped candidate signal.

    ``signal`` is the already-mapped MV2 replay position signal (``1`` for a
    long entry-candidate, ``-1`` for a short entry-candidate, ``0`` for
    flat/exit -- not a new-entry decision). Returns ``False`` unconditionally
    when ``in_warmup`` is True or when ``close``/``sma`` are not finite.
    ``signal == 0`` is never blocked (it is not an entry decision).
    """
    if bool(in_warmup):
        return False
    if not (math.isfinite(close) and math.isfinite(sma)):
        return False
    sig = int(signal)
    if sig == 1:
        return close > sma
    if sig == -1:
        return close < sma
    return True


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
    "compute_sma50",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_bars",
    "feature_formula_sha256",
    "formula_freeze_payload",
    "is_entry_eligible",
    "long_eligible_mask_from_bars",
    "short_eligible_mask_from_bars",
]
