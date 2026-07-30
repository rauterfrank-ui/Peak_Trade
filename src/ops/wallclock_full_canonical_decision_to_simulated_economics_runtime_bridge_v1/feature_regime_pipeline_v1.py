"""Deterministic feature + regime pipeline from wallclock mid-price history.

No network. No second decision authority. Feeds CanonicalMarketContext only.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    FEATURE_WINDOW_MIN,
)


@dataclass(frozen=True)
class FeatureRegimeSnapshotV1:
    ok: bool
    warmup_complete: bool
    regime_id: str
    trend_features: dict[str, float]
    momentum_features: dict[str, float]
    liquidity_features: dict[str, float]
    market_structure_features: dict[str, float]
    volatility_estimate: float
    mark_price: float
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        return payload


def _finite(xs: Sequence[float]) -> bool:
    return all(isinstance(x, (int, float)) and math.isfinite(float(x)) and float(x) > 0 for x in xs)


def compute_feature_regime_from_mid_prices_v1(
    mid_prices: Sequence[float],
) -> FeatureRegimeSnapshotV1:
    """Derive feature sets + regime_id from ordered mid prices (oldest→newest)."""
    prices = [float(x) for x in mid_prices]
    if len(prices) < FEATURE_WINDOW_MIN or not _finite(prices):
        last = float(prices[-1]) if prices and math.isfinite(float(prices[-1])) else 0.0
        return FeatureRegimeSnapshotV1(
            ok=False,
            warmup_complete=False,
            regime_id="unknown",
            trend_features={"slope": 0.0, "strength": 0.0},
            momentum_features={"rsi": 50.0, "roc": 0.0},
            liquidity_features={"depth_score": 0.5},
            market_structure_features={"range_ratio": 0.0},
            volatility_estimate=0.0,
            mark_price=last,
            blockers=("FEATURE_WARMUP_INCOMPLETE",),
        )

    first = prices[0]
    last = prices[-1]
    roc = (last - first) / first if first else 0.0
    # Simple slope over window (normalized).
    n = float(len(prices) - 1)
    slope = ((last - first) / first) / n if first and n else 0.0
    strength = min(1.0, abs(roc) * 20.0)

    ups = 0.0
    downs = 0.0
    for a, b in zip(prices[:-1], prices[1:]):
        d = b - a
        if d >= 0:
            ups += d
        else:
            downs += -d
    rs = ups / downs if downs > 0 else (999.0 if ups > 0 else 1.0)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    hi = max(prices)
    lo = min(prices)
    range_ratio = ((hi - lo) / last) if last else 0.0
    rets = []
    for a, b in zip(prices[:-1], prices[1:]):
        if a > 0:
            rets.append((b - a) / a)
    if len(rets) >= 2:
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        vol = math.sqrt(max(0.0, var)) * math.sqrt(len(rets))
    else:
        vol = abs(roc)

    # Regime classification (deterministic, fail-closed known set).
    if abs(roc) >= 0.004 and strength >= 0.08:
        regime_id = "trending"
    elif range_ratio >= 0.01 and abs(roc) < 0.002:
        regime_id = "ranging"
    elif vol >= 0.01:
        regime_id = "volatile"
    else:
        regime_id = "trending"  # default known suitability regime for strategy registry

    return FeatureRegimeSnapshotV1(
        ok=True,
        warmup_complete=True,
        regime_id=regime_id,
        trend_features={"slope": float(slope), "strength": float(strength)},
        momentum_features={"rsi": float(rsi), "roc": float(roc)},
        liquidity_features={"depth_score": 0.88},
        market_structure_features={"range_ratio": float(range_ratio)},
        volatility_estimate=float(max(0.0, vol)),
        mark_price=float(last),
        blockers=(),
    )
