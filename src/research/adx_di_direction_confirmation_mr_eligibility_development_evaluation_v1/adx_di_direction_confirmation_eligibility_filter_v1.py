"""Frozen causal Wilder ADX(14) +DI/−DI direction-confirmation eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Uses ``TrendFollowingStrategy._compute_adx``
with defaults from ``config/config.toml`` ``[strategies.trend_following.defaults]``
(``adx_period=14``). Side-aware DI-order admission only: long entries require
``minus_DI > plus_DI``; short entries require ``plus_DI > minus_DI``. ADX level
is intentionally unused. Does NOT reuse RSI/ATR/MA/MACD or ADX-level features.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import pandas as pd

from src.strategies.trend_following import TrendFollowingStrategy

FEATURE_FORMULA_ID = "adx_di_direction_confirmation_mr_eligibility_di14_features_v1"
FILTER_ID = "canonical_adx_di_direction_confirmation_entry_eligibility_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "adx_period": 14,
    "uses_adx_level": False,
    "uses_di_order_only": True,
    "side_aware": True,
    "warmup_bars": 28,
    "tie_policy": "STAND_ASIDE_WHEN_PLUS_DI_EQUALS_MINUS_DI",
    "nan_policy": "STAND_ASIDE_WHEN_DI_NONFINITE",
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_high_low_close_only",
    "lookahead_forbidden": True,
    "calculator_ssot": "src/strategies/trend_following.py",
    "calculator_method": "WILDER_ADX_PLUS_DI_MINUS_DI",
    "definitions": {
        "plus_di_14h": (
            "Wilder +DI(14) via TrendFollowingStrategy._compute_adx over trailing "
            "finalized PT1H high/low/close; ewm(alpha=1/14, min_periods=14, "
            "adjust=False); plus_di = 100 * smoothed_plus_dm / atr (atr==0 -> NaN)"
        ),
        "minus_di_14h": (
            "Wilder −DI(14) via TrendFollowingStrategy._compute_adx (same SSOT); "
            "minus_di = 100 * smoothed_minus_dm / atr (atr==0 -> NaN)"
        ),
        "eligibility_rule": (
            "For a long entry-candidate (signal==1): ELIGIBLE iff both DI finite "
            "AND minus_DI > plus_DI. For a short entry-candidate (signal==-1): "
            "ELIGIBLE iff both DI finite AND plus_DI > minus_DI. Tie "
            "(plus_DI == minus_DI) or non-finite DI -> STAND_ASIDE. First "
            "warmup_bars=28 bars are always STAND_ASIDE. ADX level unused. "
            "Side-aware direction-confirmation admission only; does not change "
            "direction/side."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_plus_minus_di(bars: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Wilder +DI/−DI(14) via SSOT ``TrendFollowingStrategy._compute_adx``."""
    if int(REQUIRED_FROZEN["adx_period"]) != 14:
        raise ValueError("ADX_PERIOD_DRIFT")
    if REQUIRED_FROZEN["uses_adx_level"] is not False:
        raise ValueError("USES_ADX_LEVEL_DRIFT")
    if REQUIRED_FROZEN["uses_di_order_only"] is not True:
        raise ValueError("USES_DI_ORDER_ONLY_DRIFT")
    period = int(REQUIRED_FROZEN["adx_period"])
    strategy = TrendFollowingStrategy(
        config={
            "adx_period": period,
            "adx_threshold": 25.0,
            "exit_threshold": 20.0,
            "ma_period": 50,
            "use_ma_filter": False,
        }
    )
    _adx, plus_di, minus_di = strategy._compute_adx(bars)
    plus_di = plus_di.astype(float)
    minus_di = minus_di.astype(float)
    plus_di.name = "plus_di_14h"
    minus_di.name = "minus_di_14h"
    return plus_di, minus_di


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
    """Boolean mask: True iff a long entry-candidate is admissible (minus_DI > plus_DI)."""
    if REQUIRED_FROZEN["side_aware"] is not True:
        raise ValueError("SIDE_AWARE_DRIFT")
    plus_di, minus_di = compute_plus_minus_di(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = plus_di.notna() & minus_di.notna() & (minus_di > plus_di)
    eligible = eligible.where(~warmup, False)
    eligible.name = "long_entry_eligibility"
    return eligible.astype(bool)


def short_eligible_mask_from_bars(
    bars: pd.DataFrame, *, warmup_bars: int | None = None
) -> pd.Series:
    """Boolean mask: True iff a short entry-candidate is admissible (plus_DI > minus_DI)."""
    if REQUIRED_FROZEN["side_aware"] is not True:
        raise ValueError("SIDE_AWARE_DRIFT")
    plus_di, minus_di = compute_plus_minus_di(bars)
    warmup = _warmup_mask(bars.index, warmup_bars=warmup_bars)
    eligible = plus_di.notna() & minus_di.notna() & (plus_di > minus_di)
    eligible = eligible.where(~warmup, False)
    eligible.name = "short_entry_eligibility"
    return eligible.astype(bool)


def eligibility_mask_from_bars(bars: pd.DataFrame, *, warmup_bars: int | None = None) -> pd.Series:
    """Combined (long OR short) admissibility mask.

    INFORMATIONAL ONLY: used for bar-share attribution. The actual gate always
    evaluates eligibility against the specific candidate side (``signal``).
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


def is_entry_eligible(*, signal: int, plus_di: float, minus_di: float, in_warmup: bool) -> bool:
    """Side-aware entry-effective eligibility for a single mapped candidate signal.

    ``signal`` is the already-mapped MV2 replay position signal (``1`` long,
    ``-1`` short, ``0`` flat/exit). Returns ``False`` when ``in_warmup`` or when
    either DI is non-finite. Tie (``plus_di == minus_di``) is STAND_ASIDE.
    ``signal == 0`` is never blocked.
    """
    if bool(in_warmup):
        return False
    if not math.isfinite(plus_di) or not math.isfinite(minus_di):
        return False
    sig = int(signal)
    if sig == 1:
        return minus_di > plus_di
    if sig == -1:
        return plus_di > minus_di
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
    "compute_plus_minus_di",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_bars",
    "feature_formula_sha256",
    "formula_freeze_payload",
    "is_entry_eligible",
    "long_eligible_mask_from_bars",
    "short_eligible_mask_from_bars",
]
