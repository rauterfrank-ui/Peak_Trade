from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class OutlookV0:
    regime: str
    no_trade: bool
    no_trade_reasons: List[str]


def _get_feature_map(features: Dict[str, Any], key: str) -> Dict[str, float]:
    v = features.get(key, {})
    if not isinstance(v, dict):
        return {}
    out: Dict[str, float] = {}
    for k, x in v.items():
        try:
            out[str(k)] = float(x)
        except Exception:
            continue
    return out


def compute_outlook_v0(features: Dict[str, Any]) -> OutlookV0:
    """
    v0 rules (deterministic, explicit):
    - Aggregate volatility/trend over universe by mean of provided values.
    - Regime:
        * HIGH_VOL if mean_vol >= 0.75
        * RISK_OFF if mean_trend <= -0.10
        * RISK_ON if mean_trend >= +0.10 and mean_vol < 0.75
        * NEUTRAL otherwise
    - NO-TRADE triggers:
        * HIGH_VOL (mean_vol >= 0.90)  -> "VOL_EXTREME"
        * Missing features (no vol or no trend) -> "MISSING_FEATURES"
    """
    reasons: List[str] = []

    vol = _get_feature_map(features, "volatility_14d")
    tr = _get_feature_map(features, "trend_7d")

    if not vol or not tr:
        reasons.append("MISSING_FEATURES")

    mean_vol = sum(vol.values()) / max(1, len(vol)) if vol else 0.0
    mean_tr = sum(tr.values()) / max(1, len(tr)) if tr else 0.0

    if mean_vol >= 0.75:
        regime = "HIGH_VOL"
    elif mean_tr <= -0.10:
        regime = "RISK_OFF"
    elif mean_tr >= 0.10 and mean_vol < 0.75:
        regime = "RISK_ON"
    else:
        regime = "NEUTRAL"

    if mean_vol >= 0.90:
        reasons.append("VOL_EXTREME")

    no_trade = len(reasons) > 0 and ("VOL_EXTREME" in reasons or "MISSING_FEATURES" in reasons)

    # Stable ordering
    reasons_sorted = sorted(set(reasons))
    return OutlookV0(regime=regime, no_trade=no_trade, no_trade_reasons=reasons_sorted)
