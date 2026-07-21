"""Frozen causal MACD(12,26,9) histogram-sign countertrend eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Uses the SSOT MACD computation from
``src/strategies/macd.py::_calculate_macd`` with defaults from
``config/config.toml`` ``[strategies.macd.defaults]`` (fast_ema=12,
slow_ema=26, signal_ema=9). Side-aware countertrend admission only:
long entries require ``histogram < 0``; short entries require
``histogram > 0``. Does NOT reuse RSI/ADX/ATR/MA features.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import pandas as pd

from src.strategies.macd import _calculate_macd

FEATURE_FORMULA_ID = "macd_histogram_countertrend_mr_eligibility_macd12269_features_v1"
FILTER_ID = "canonical_macd_histogram_countertrend_entry_eligibility_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "fast_ema": 12,
    "slow_ema": 26,
    "signal_ema": 9,
    "eligibility_on": "histogram_sign_side_aware",
    "warmup_bars": 35,
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_close_only",
    "lookahead_forbidden": True,
    "calculator_ssot": "src/strategies/macd.py",
    "calculator_method": "MACD_EMA_HISTOGRAM",
    "definitions": {
        "macd_histogram_12_26_9": (
            "MACD histogram = MACD_line - signal_line with EMA(12)/EMA(26)/EMA(9) "
            "via src/strategies/macd.py::_calculate_macd (config.toml "
            "[strategies.macd.defaults]); first 35 bars are warmup"
        ),
        "eligibility_rule": (
            "For a long entry-candidate (signal==1): ELIGIBLE iff histogram < 0. "
            "For a short entry-candidate (signal==-1): ELIGIBLE iff histogram > 0. "
            "Otherwise STAND_ASIDE. First warmup_bars=35 bars are always STAND_ASIDE. "
            "Side-aware countertrend admission only; does not change direction/side."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_macd_histogram(bars: pd.DataFrame) -> pd.Series:
    """MACD(12,26,9) histogram via SSOT ``src/strategies/macd.py::_calculate_macd``."""
    if int(REQUIRED_FROZEN["fast_ema"]) != 12:
        raise ValueError("FAST_EMA_DRIFT")
    if int(REQUIRED_FROZEN["slow_ema"]) != 26:
        raise ValueError("SLOW_EMA_DRIFT")
    if int(REQUIRED_FROZEN["signal_ema"]) != 9:
        raise ValueError("SIGNAL_EMA_DRIFT")
    close = bars["close"].astype(float)
    _macd_line, _signal_line, histogram = _calculate_macd(
        close,
        fast_period=int(REQUIRED_FROZEN["fast_ema"]),
        slow_period=int(REQUIRED_FROZEN["slow_ema"]),
        signal_period=int(REQUIRED_FROZEN["signal_ema"]),
    )
    histogram = histogram.astype(float)
    histogram.name = "macd_histogram_12_26_9"
    return histogram


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
    """Boolean mask: True iff a long entry-candidate is admissible (histogram < 0)."""
    if str(REQUIRED_FROZEN["eligibility_on"]) != "histogram_sign_side_aware":
        raise ValueError("ELIGIBILITY_ON_DRIFT")
    hist = compute_macd_histogram(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = hist.notna() & (hist < 0)
    eligible = eligible.where(~warmup, False)
    eligible.name = "long_entry_eligibility"
    return eligible.astype(bool)


def short_eligible_mask_from_bars(
    bars: pd.DataFrame, *, warmup_bars: int | None = None
) -> pd.Series:
    """Boolean mask: True iff a short entry-candidate is admissible (histogram > 0)."""
    if str(REQUIRED_FROZEN["eligibility_on"]) != "histogram_sign_side_aware":
        raise ValueError("ELIGIBILITY_ON_DRIFT")
    hist = compute_macd_histogram(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = hist.notna() & (hist > 0)
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


def is_entry_eligible(*, signal: int, histogram: float, in_warmup: bool) -> bool:
    """Side-aware entry-effective eligibility for a single mapped candidate signal.

    ``signal`` is the already-mapped MV2 replay position signal (``1`` for a
    long entry-candidate, ``-1`` for a short entry-candidate, ``0`` for
    flat/exit -- not a new-entry decision). Returns ``False`` unconditionally
    when ``in_warmup`` is True or when ``histogram`` is not finite.
    ``signal == 0`` is never blocked (it is not an entry decision).
    """
    if bool(in_warmup):
        return False
    if not math.isfinite(histogram):
        return False
    sig = int(signal)
    if sig == 1:
        return histogram < 0
    if sig == -1:
        return histogram > 0
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
    "compute_macd_histogram",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_bars",
    "feature_formula_sha256",
    "formula_freeze_payload",
    "is_entry_eligible",
    "long_eligible_mask_from_bars",
    "short_eligible_mask_from_bars",
]
