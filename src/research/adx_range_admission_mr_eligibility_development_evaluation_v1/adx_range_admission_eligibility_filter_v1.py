"""Frozen causal ADX range-admission eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Uses ``TrendFollowingStrategy._compute_adx``
(Wilder ewm, alpha=1/period, adjust=False).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import pandas as pd

from src.strategies.trend_following import TrendFollowingStrategy

FEATURE_FORMULA_ID = "adx_range_admission_mr_eligibility_adx14_features_v1"
FILTER_ID = "canonical_adx_range_admission_entry_eligibility_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "adx_period": 14,
    "adx_threshold": 25.0,
    "eligibility_comparator": "lt",
    "warmup_bars": 28,
    "calculator": "wilder_ewm_alpha_1_over_period",
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_high_low_close_only",
    "lookahead_forbidden": True,
    "calculator_ssot": "src/strategies/trend_following.py::TrendFollowingStrategy._compute_adx",
    "calculator_method": "WILDER_EWM_ALPHA_1_OVER_PERIOD",
    "definitions": {
        "adx_14h": (
            "ADX(14) via TrendFollowingStrategy._compute_adx over trailing finalized "
            "PT1H OHLC (Wilder ewm alpha=1/14, min_periods=14, adjust=False); "
            "first 28 bars (2*period) are warmup"
        ),
        "eligibility_rule": (
            "ELIGIBLE iff ADX is finite AND ADX < 25.0; otherwise STAND_ASIDE. "
            "First warmup_bars=28 bars are always STAND_ASIDE."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_adx14(bars: pd.DataFrame) -> pd.Series:
    """ADX(14) via SSOT ``TrendFollowingStrategy._compute_adx``."""
    if str(REQUIRED_FROZEN["calculator"]) != "wilder_ewm_alpha_1_over_period":
        raise ValueError("CALCULATOR_DRIFT")
    if str(REQUIRED_FROZEN["eligibility_comparator"]) != "lt":
        raise ValueError("COMPARATOR_DRIFT")
    period = int(REQUIRED_FROZEN["adx_period"])
    threshold = float(REQUIRED_FROZEN["adx_threshold"])
    strategy = TrendFollowingStrategy(
        config={
            "adx_period": period,
            "adx_threshold": threshold,
            "exit_threshold": 20.0,
            "ma_period": 50,
            "use_ma_filter": False,
        }
    )
    adx, _plus_di, _minus_di = strategy._compute_adx(bars)
    adx = adx.astype(float)
    adx.name = "adx_14h"
    return adx


def eligibility_mask_from_adx(adx: pd.Series, *, warmup_bars: int | None = None) -> pd.Series:
    """Boolean eligibility mask from a precomputed ADX series.

    ``eligible = adx.notna() & (adx < 25.0)``. The first ``warmup_bars``
    (default 28) positions are unconditionally ineligible.
    """
    threshold = float(REQUIRED_FROZEN["adx_threshold"])
    if str(REQUIRED_FROZEN["eligibility_comparator"]) != "lt":
        raise ValueError("COMPARATOR_DRIFT")
    eligible = adx.notna() & (adx < threshold)
    wb = int(REQUIRED_FROZEN["warmup_bars"]) if warmup_bars is None else int(warmup_bars)
    if wb > 0:
        warmup = pd.Series(False, index=eligible.index)
        n_warmup = min(wb, len(warmup))
        if n_warmup > 0:
            warmup.iloc[:n_warmup] = True
        eligible = eligible.where(~warmup, False)
    eligible.name = "entry_eligibility"
    return eligible.astype(bool)


def eligibility_mask_from_bars(bars: pd.DataFrame) -> pd.Series:
    """Boolean eligibility mask: True iff ADX range-admission rule holds."""
    adx = compute_adx14(bars)
    return eligibility_mask_from_adx(adx)


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
    "compute_adx14",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_adx",
    "eligibility_mask_from_bars",
    "feature_formula_sha256",
    "formula_freeze_payload",
]
