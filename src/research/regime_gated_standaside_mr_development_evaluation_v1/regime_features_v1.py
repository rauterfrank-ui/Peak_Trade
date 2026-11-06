"""Frozen causal regime features for preregistered standaside MR evaluation v1.

Feature IDs and thresholds are locked in the preregistration contract. Exact
close-path formulas were IDs-only there; this module freezes the sole causal
interpretation used for the single DEVELOPMENT evaluation (no post-hoc retune).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import pandas as pd

FEATURE_FORMULA_ID = "regime_gated_standaside_mr_close_path_features_v1"
REGIME_RANGE = "RANGE_BOUND"
REGIME_TREND = "TREND_STRONG"

# Locked thresholds from preregistration contract (do not retune).
THRESHOLDS = {
    "realized_vol_168h_max_for_range": 0.02,
    "range_compression_72h_min_for_range": 0.55,
    "trend_strength_168h_max_for_range": 0.35,
}

FORMULA_SPEC: dict[str, Any] = {
    "feature_formula_id": FEATURE_FORMULA_ID,
    "source": "finalized_pt1h_ohlcv_close_path_only",
    "lookahead_forbidden": True,
    "definitions": {
        "realized_vol_168h": (
            "sample_std_ddof1 of close.pct_change() over trailing 168 finalized "
            "hourly bars; no annualization"
        ),
        "range_compression_72h": (
            "1.0 - (rolling_max(close,72) - rolling_min(close,72)) / "
            "rolling_max(close,72); clipped to [0,1]; higher = more compressed"
        ),
        "trend_strength_168h": "abs(close / close.shift(168) - 1.0)",
        "label_rule": (
            "RANGE_BOUND iff all three threshold conditions hold with finite "
            "features; else TREND_STRONG; NaN/warmup => TREND_STRONG (stand aside)"
        ),
    },
    "thresholds": dict(THRESHOLDS),
}


def feature_formula_sha256() -> str:
    blob = json.dumps(FORMULA_SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_regime_features(close: pd.Series) -> pd.DataFrame:
    """Causal close-path features; index aligned to ``close``."""
    c = close.astype(float)
    rets = c.pct_change()
    realized_vol = rets.rolling(168, min_periods=168).std(ddof=1)
    roll_max = c.rolling(72, min_periods=72).max()
    roll_min = c.rolling(72, min_periods=72).min()
    width = (roll_max - roll_min) / roll_max.replace(0.0, pd.NA)
    compression = (1.0 - width).clip(lower=0.0, upper=1.0)
    trend = (c / c.shift(168) - 1.0).abs()
    return pd.DataFrame(
        {
            "realized_vol_168h": realized_vol,
            "range_compression_72h": compression,
            "trend_strength_168h": trend,
        },
        index=c.index,
    )


def classify_regime_labels(features: pd.DataFrame) -> pd.Series:
    thr = THRESHOLDS
    ok = (
        features["realized_vol_168h"].le(thr["realized_vol_168h_max_for_range"])
        & features["range_compression_72h"].ge(thr["range_compression_72h_min_for_range"])
        & features["trend_strength_168h"].le(thr["trend_strength_168h_max_for_range"])
        & features["realized_vol_168h"].notna()
        & features["range_compression_72h"].notna()
        & features["trend_strength_168h"].notna()
    )
    labels = pd.Series(REGIME_TREND, index=features.index, dtype=object)
    labels = labels.where(~ok, REGIME_RANGE)
    return labels


def regime_labels_from_close(close: pd.Series) -> pd.Series:
    return classify_regime_labels(compute_regime_features(close))


def formula_freeze_payload() -> dict[str, Any]:
    return {
        **FORMULA_SPEC,
        "feature_formula_sha256": feature_formula_sha256(),
        "threshold_adjustment_forbidden": True,
        "post_hoc_retune_forbidden": True,
    }


def assert_thresholds_match_contract(contract: Mapping[str, Any]) -> None:
    frozen = (contract.get("regime_features") or {}).get("frozen_thresholds") or {}
    for key, expected in THRESHOLDS.items():
        if float(frozen.get(key)) != float(expected):
            raise ValueError(f"THRESHOLD_DRIFT:{key}")


__all__ = [
    "FEATURE_FORMULA_ID",
    "FORMULA_SPEC",
    "REGIME_RANGE",
    "REGIME_TREND",
    "THRESHOLDS",
    "assert_thresholds_match_contract",
    "classify_regime_labels",
    "compute_regime_features",
    "feature_formula_sha256",
    "formula_freeze_payload",
    "regime_labels_from_close",
]
