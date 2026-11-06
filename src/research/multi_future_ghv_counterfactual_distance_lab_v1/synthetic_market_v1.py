from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    ARCHETYPE_TAGS,
    REGIME_IDS,
    VOL_SIGMA_BY_LEVEL,
    VOLATILITY_LEVELS,
)

MODE_A_NORMALIZED_RETURNS: Tuple[float, ...] = (
    0.0,
    0.01,
    -0.005,
    0.02,
    -0.03,
    0.015,
    -0.01,
    0.025,
    -0.02,
    0.005,
)


@dataclass(frozen=True)
class FutureProfileV1:
    future_profile_id: str
    tags: Tuple[str, ...]
    mode_b_vol_multiplier: float
    trend_persistence: float
    mean_reversion_strength: float
    chop_noise: float
    jump_probability: float
    asymmetry_skew: float


def _profile_id(tags: Sequence[str]) -> str:
    material = "|".join(sorted(tags))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"FP_{digest}"


def build_future_profile_catalog_v1() -> Tuple[FutureProfileV1, ...]:
    profiles: List[FutureProfileV1] = []
    price_tags = ("MICRO_PRICE", "LOW_PRICE", "MID_PRICE", "HIGH_PRICE", "VERY_HIGH_PRICE")
    vol_tags = ("VERY_LOW_VOL", "LOW_VOL", "MEDIUM_VOL", "HIGH_VOL", "EXTREME_VOL")
    regime_tags = (
        "TRENDING",
        "MEAN_REVERTING",
        "CHOPPY",
        "BURST_VOL",
        "GAP_JUMP",
        "ASYMMETRIC",
        "MIXED_REGIME",
    )
    for pt in price_tags:
        for vt in vol_tags:
            for rt in regime_tags:
                tags = (pt, vt, rt)
                profiles.append(
                    FutureProfileV1(
                        future_profile_id=_profile_id(tags),
                        tags=tags,
                        mode_b_vol_multiplier={
                            "VERY_LOW_VOL": 0.5,
                            "LOW_VOL": 0.8,
                            "MEDIUM_VOL": 1.0,
                            "HIGH_VOL": 1.4,
                            "EXTREME_VOL": 2.0,
                        }[vt],
                        trend_persistence=0.7 if rt == "TRENDING" else 0.2,
                        mean_reversion_strength=0.6 if rt == "MEAN_REVERTING" else 0.1,
                        chop_noise=0.4 if rt == "CHOPPY" else 0.05,
                        jump_probability=0.15 if rt in ("GAP_JUMP", "BURST_VOL") else 0.02,
                        asymmetry_skew=0.2 if rt == "ASYMMETRIC" else 0.0,
                    )
                )
    return tuple(profiles)


def generalization_future_profile_v1(profile_key: str) -> FutureProfileV1:
    mapping = {
        "MICRO_LOW_VOL": ("MICRO_PRICE", "LOW_VOL", "TRENDING"),
        "MICRO_HIGH_VOL": ("MICRO_PRICE", "HIGH_VOL", "CHOPPY"),
        "MICRO_CHOP": ("MICRO_PRICE", "MEDIUM_VOL", "CHOPPY"),
        "MICRO_TREND": ("MICRO_PRICE", "LOW_VOL", "TRENDING"),
        "MICRO_JUMP": ("MICRO_PRICE", "HIGH_VOL", "GAP_JUMP"),
        "LOW_PRICE_LOW_VOL": ("LOW_PRICE", "LOW_VOL", "TRENDING"),
        "LOW_PRICE_HIGH_VOL": ("LOW_PRICE", "HIGH_VOL", "CHOPPY"),
        "LOW_PRICE_TREND": ("LOW_PRICE", "MEDIUM_VOL", "TRENDING"),
        "LOW_PRICE_JUMP": ("LOW_PRICE", "HIGH_VOL", "GAP_JUMP"),
        "MID_PRICE_MEAN_REVERSION": ("MID_PRICE", "MEDIUM_VOL", "MEAN_REVERTING"),
        "MID_PRICE_TREND": ("MID_PRICE", "LOW_VOL", "TRENDING"),
        "MID_PRICE_CHOP": ("MID_PRICE", "HIGH_VOL", "CHOPPY"),
        "HIGH_PRICE_LOW_VOL": ("HIGH_PRICE", "LOW_VOL", "TRENDING"),
        "HIGH_PRICE_HIGH_VOL": ("HIGH_PRICE", "HIGH_VOL", "BURST_VOL"),
        "HIGH_PRICE_MEAN_REVERSION": ("HIGH_PRICE", "MEDIUM_VOL", "MEAN_REVERTING"),
        "VERY_HIGH_PRICE_CHOP": ("VERY_HIGH_PRICE", "HIGH_VOL", "CHOPPY"),
        "VERY_HIGH_PRICE_BURST_VOL": ("VERY_HIGH_PRICE", "EXTREME_VOL", "BURST_VOL"),
        "VERY_HIGH_PRICE_TREND": ("VERY_HIGH_PRICE", "LOW_VOL", "TRENDING"),
        "MIXED_REGIME": ("MID_PRICE", "MEDIUM_VOL", "MIXED_REGIME"),
    }
    tags = mapping[profile_key]
    return FutureProfileV1(
        future_profile_id=_profile_id(tags),
        tags=tags,
        mode_b_vol_multiplier=1.0,
        trend_persistence=0.5,
        mean_reversion_strength=0.3,
        chop_noise=0.2,
        jump_probability=0.05,
        asymmetry_skew=0.0,
    )


def p0_from_price_tag(tag: str, explicit_p0: float | None = None) -> float:
    if explicit_p0 is not None:
        return float(explicit_p0)
    return {
        "MICRO_PRICE": 0.2,
        "LOW_PRICE": 5.0,
        "MID_PRICE": 100.0,
        "HIGH_PRICE": 5000.0,
        "VERY_HIGH_PRICE": 80000.0,
    }[tag]


def sigma_for_profile(
    *,
    vol_level: str,
    profile: FutureProfileV1,
    mode: str,
) -> float:
    base = VOL_SIGMA_BY_LEVEL[vol_level]
    if mode == "MODE_B":
        return base * profile.mode_b_vol_multiplier
    return base


def generate_price_path_v1(
    *,
    p0: float,
    sigma: float,
    profile: FutureProfileV1,
    regime_id: str,
    seed: int,
    mode: str,
    steps: int,
) -> Tuple[float, ...]:
    rng = random.Random(int(seed))
    prices = [max(p0, 1e-8)]
    returns_mode_a = MODE_A_NORMALIZED_RETURNS
    for i in range(1, steps):
        if mode == "MODE_A":
            r = returns_mode_a[i % len(returns_mode_a)]
        else:
            prev = prices[-1]
            trend = profile.trend_persistence * sigma * (1 if regime_id.endswith("BULL") else -0.3)
            mr = -profile.mean_reversion_strength * (prev / p0 - 1.0) * sigma
            noise = rng.gauss(0, sigma * profile.chop_noise)
            jump = 0.0
            if rng.random() < profile.jump_probability:
                jump = rng.choice([-1, 1]) * sigma * 3.0
            r = trend + mr + noise + jump + profile.asymmetry_skew * sigma * 0.1
        nxt = max(prices[-1] * (1.0 + r), 1e-8)
        prices.append(nxt)
    return tuple(prices)


def iter_stage1_case_ids(
    *,
    models: Sequence[str],
    price_scales: Sequence[float],
    vol_levels: Sequence[str],
    regimes: Sequence[str],
    seeds: Iterable[int],
    profiles: Sequence[FutureProfileV1],
) -> Iterable[dict[str, object]]:
    for model_id in models:
        for p0 in price_scales:
            for vol in vol_levels:
                for regime in regimes:
                    for seed in seeds:
                        for profile in profiles:
                            for mode in ("MODE_A", "MODE_B"):
                                yield {
                                    "model_id": model_id,
                                    "price_scale": p0,
                                    "vol_level": vol,
                                    "regime": regime,
                                    "seed": seed,
                                    "future_profile_id": profile.future_profile_id,
                                    "market_mode": mode,
                                }
