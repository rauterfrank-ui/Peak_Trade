"""Frozen causal RSI-exhaustion eligibility filter v1.

Sole causal interpretation used for the single preregistered DEVELOPMENT
evaluation (no post-hoc retune). Uses ``src.strategies.rsi.calculate_rsi``
(EWM causal, span=period, adjust=False) — Wilder smoothing excluded.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import pandas as pd

from src.strategies.rsi import calculate_rsi

FEATURE_FORMULA_ID = "rsi_exhaustion_mr_eligibility_rsi14_features_v1"
FILTER_ID = "canonical_rsi_exhaustion_entry_eligibility_v1"
ELIGIBLE = "ELIGIBLE"
STAND_ASIDE = "STAND_ASIDE"

# Frozen from preregistration contract (do not retune).
REQUIRED_FROZEN: dict[str, Any] = {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70,
    "use_wilder": False,
    "calculator": "ewm_causal_span",
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "filter_id": FILTER_ID,
    "source": "finalized_pt1h_ohlcv_close_only",
    "lookahead_forbidden": True,
    "calculator_ssot": "src/strategies/rsi.py::calculate_rsi",
    "calculator_method": "EWM_CAUSAL_SPAN_ADJUST_FALSE",
    "wilder_smoothing_excluded": True,
    "definitions": {
        "rsi_14h": (
            "RSI(14) over trailing finalized PT1H close prices via "
            "src.strategies.rsi.calculate_rsi (EWM causal, span=14, adjust=False); "
            "first 14 bars are warmup"
        ),
        "eligibility_rule": (
            "ELIGIBLE iff RSI is finite AND (RSI <= 30 OR RSI >= 70); otherwise "
            "STAND_ASIDE. First rsi_period=14 bars are always STAND_ASIDE."
        ),
    },
    "frozen_parameters": dict(REQUIRED_FROZEN),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_rsi14(bars: pd.DataFrame) -> pd.Series:
    """RSI(14) via SSOT ``calculate_rsi`` (EWM causal; Wilder excluded)."""
    close = bars["close"].astype(float)
    period = int(REQUIRED_FROZEN["rsi_period"])
    if bool(REQUIRED_FROZEN["use_wilder"]):
        raise ValueError("WILDER_SMOOTHING_EXCLUDED")
    if str(REQUIRED_FROZEN["calculator"]) != "ewm_causal_span":
        raise ValueError("CALCULATOR_DRIFT")
    rsi = calculate_rsi(close, period=period)
    rsi.name = "rsi_14h"
    return rsi


def eligibility_mask_from_rsi(rsi: pd.Series, *, warmup_bars: int | None = None) -> pd.Series:
    """Boolean eligibility mask from a precomputed RSI series.

    ``eligible = rsi.notna() & ((rsi <= 30) | (rsi >= 70))``. The first
    ``warmup_bars`` (default ``rsi_period``) positions are unconditionally
    ineligible (warmup, stand aside).
    """
    oversold = float(REQUIRED_FROZEN["oversold"])
    overbought = float(REQUIRED_FROZEN["overbought"])
    eligible = rsi.notna() & ((rsi <= oversold) | (rsi >= overbought))
    wb = int(REQUIRED_FROZEN["rsi_period"]) if warmup_bars is None else int(warmup_bars)
    if wb > 0:
        warmup = pd.Series(False, index=eligible.index)
        n_warmup = min(wb, len(warmup))
        if n_warmup > 0:
            warmup.iloc[:n_warmup] = True
        eligible = eligible.where(~warmup, False)
    eligible.name = "entry_eligibility"
    return eligible.astype(bool)


def eligibility_mask_from_bars(bars: pd.DataFrame) -> pd.Series:
    """Boolean eligibility mask: True iff RSI exhaustion rule holds."""
    rsi = compute_rsi14(bars)
    return eligibility_mask_from_rsi(rsi)


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
    "compute_rsi14",
    "eligibility_labels_from_bars",
    "eligibility_mask_from_bars",
    "eligibility_mask_from_rsi",
    "feature_formula_sha256",
    "formula_freeze_payload",
]
