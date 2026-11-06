"""Feature + regime pipeline v2 — no default trending fallback.

``volatility_estimate`` here is a regime-classification proxy only
(sample variance ddof=1 × sqrt(n)). It is quarantined from productive
Double-Play / CMC volatility authority — see hot-path contract closure.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    DEFAULT_REGIME_FALLBACK_ACTIVE,
    FEATURE_CONFIG_VERSION,
    FEATURE_WINDOW_MIN,
    REGIME_CONFIG_VERSION,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
    digest_mapping,
)

# Quarantine: not the productive volatility producer / CMC authority.
VOLATILITY_ESTIMATE_PRODUCTIVE_AUTHORITY = False
VOLATILITY_ESTIMATE_SEMANTICS = "REGIME_CLASSIFICATION_PROXY_SAMPLE_VAR_DDOF1_SQRT_N_QUARANTINED"
VOLATILITY_ESTIMATE_IDENTITY = "feature_regime_pipeline_v2.sample_variance_ddof_1_times_sqrt_n"


@dataclass(frozen=True)
class FeatureRegimeSnapshotV2:
    ok: bool
    warmup_complete: bool
    regime_id: str
    regime_state_source: str
    trend_features: dict[str, float]
    momentum_features: dict[str, float]
    liquidity_features: dict[str, float]
    market_structure_features: dict[str, float]
    volatility_estimate: float
    mark_price: float
    feature_digest: str
    regime_digest: str
    feature_config_version: str
    regime_config_version: str
    default_regime_fallback_active: bool
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["volatility_estimate_productive_authority"] = (
            VOLATILITY_ESTIMATE_PRODUCTIVE_AUTHORITY
        )
        payload["volatility_estimate_semantics"] = VOLATILITY_ESTIMATE_SEMANTICS
        payload["volatility_estimate_identity"] = VOLATILITY_ESTIMATE_IDENTITY
        return payload


def _finite(xs: Sequence[float]) -> bool:
    return all(isinstance(x, (int, float)) and math.isfinite(float(x)) and float(x) > 0 for x in xs)


def compute_feature_regime_from_mid_prices_v2(
    mid_prices: Sequence[float],
) -> FeatureRegimeSnapshotV2:
    prices = [float(x) for x in mid_prices]
    feature_cfg = {
        "feature_config_version": FEATURE_CONFIG_VERSION,
        "feature_window_min": FEATURE_WINDOW_MIN,
    }
    regime_cfg = {
        "regime_config_version": REGIME_CONFIG_VERSION,
        "default_regime_fallback_active": DEFAULT_REGIME_FALLBACK_ACTIVE,
        "known_regimes": ["trending", "ranging", "volatile"],
    }
    feature_digest = digest_mapping(feature_cfg)
    if len(prices) < FEATURE_WINDOW_MIN or not _finite(prices):
        last = float(prices[-1]) if prices and math.isfinite(float(prices[-1])) else 0.0
        regime_digest = digest_mapping({**regime_cfg, "regime_id": "insufficient_history"})
        return FeatureRegimeSnapshotV2(
            ok=False,
            warmup_complete=False,
            regime_id="insufficient_history",
            regime_state_source="CANONICAL_RUNTIME_PIPELINE",
            trend_features={"slope": 0.0, "strength": 0.0},
            momentum_features={"rsi": 50.0, "roc": 0.0},
            liquidity_features={"depth_score": 0.0},
            market_structure_features={"range_ratio": 0.0},
            volatility_estimate=0.0,
            mark_price=last,
            feature_digest=feature_digest,
            regime_digest=regime_digest,
            feature_config_version=FEATURE_CONFIG_VERSION,
            regime_config_version=REGIME_CONFIG_VERSION,
            default_regime_fallback_active=DEFAULT_REGIME_FALLBACK_ACTIVE,
            blockers=("FEATURE_WARMUP_INCOMPLETE", "REGIME_INSUFFICIENT_HISTORY"),
        )

    first = prices[0]
    last = prices[-1]
    roc = (last - first) / first if first else 0.0
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

    # Fail-closed classification: no silent trending default.
    if abs(roc) >= 0.004 and strength >= 0.08:
        regime_id = "trending"
    elif range_ratio >= 0.01 and abs(roc) < 0.002:
        regime_id = "ranging"
    elif vol >= 0.01:
        regime_id = "volatile"
    else:
        regime_id = "unclassified"
        regime_digest = digest_mapping({**regime_cfg, "regime_id": regime_id})
        return FeatureRegimeSnapshotV2(
            ok=False,
            warmup_complete=True,
            regime_id=regime_id,
            regime_state_source="CANONICAL_RUNTIME_PIPELINE",
            trend_features={"slope": float(slope), "strength": float(strength)},
            momentum_features={"rsi": float(rsi), "roc": float(roc)},
            liquidity_features={"depth_score": 0.0},
            market_structure_features={"range_ratio": float(range_ratio)},
            volatility_estimate=float(max(0.0, vol)),
            mark_price=float(last),
            feature_digest=digest_mapping({**feature_cfg, "mark_price": last, "roc": roc}),
            regime_digest=regime_digest,
            feature_config_version=FEATURE_CONFIG_VERSION,
            regime_config_version=REGIME_CONFIG_VERSION,
            default_regime_fallback_active=DEFAULT_REGIME_FALLBACK_ACTIVE,
            blockers=("REGIME_UNCLASSIFIED_FAIL_CLOSED",),
        )

    feature_digest = digest_mapping(
        {**feature_cfg, "mark_price": last, "roc": roc, "slope": slope, "rsi": rsi}
    )
    regime_digest = digest_mapping({**regime_cfg, "regime_id": regime_id, "roc": roc, "vol": vol})
    return FeatureRegimeSnapshotV2(
        ok=True,
        warmup_complete=True,
        regime_id=regime_id,
        regime_state_source="CANONICAL_RUNTIME_PIPELINE",
        trend_features={"slope": float(slope), "strength": float(strength)},
        momentum_features={"rsi": float(rsi), "roc": float(roc)},
        liquidity_features={"depth_score": 0.0},
        market_structure_features={"range_ratio": float(range_ratio)},
        volatility_estimate=float(max(0.0, vol)),
        mark_price=float(last),
        feature_digest=feature_digest,
        regime_digest=regime_digest,
        feature_config_version=FEATURE_CONFIG_VERSION,
        regime_config_version=REGIME_CONFIG_VERSION,
        default_regime_fallback_active=DEFAULT_REGIME_FALLBACK_ACTIVE,
        blockers=(),
    )
