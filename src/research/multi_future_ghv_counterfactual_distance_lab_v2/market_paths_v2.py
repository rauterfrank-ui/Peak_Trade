from __future__ import annotations

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import VOL_SIGMA_BY_LEVEL
from research.multi_future_ghv_counterfactual_distance_lab_v1.synthetic_market_v1 import (
    FutureProfileV1,
    generate_price_path_v1,
    generalization_future_profile_v1,
    p0_from_price_tag,
)

_REGIME_FOR_PROFILE = {
    "MICRO_LOW_VOL": "R01",
    "MICRO_HIGH_VOL": "R07",
    "MICRO_CHOP": "R07",
    "MICRO_TREND": "R02",
    "MICRO_JUMP": "R10",
    "LOW_PRICE_LOW_VOL": "R02",
    "LOW_PRICE_HIGH_VOL": "R05",
    "LOW_PRICE_TREND": "R16",
    "LOW_PRICE_JUMP": "R10",
    "MID_PRICE_MEAN_REVERSION": "R06",
    "MID_PRICE_TREND": "R16",
    "MID_PRICE_CHOP": "R07",
    "HIGH_PRICE_LOW_VOL": "R02",
    "HIGH_PRICE_HIGH_VOL": "R05",
    "HIGH_PRICE_MEAN_REVERSION": "R06",
    "VERY_HIGH_PRICE_CHOP": "R07",
    "VERY_HIGH_PRICE_BURST_VOL": "R09",
    "VERY_HIGH_PRICE_TREND": "R16",
    "MIXED_REGIME": "R17",
}


def regime_for_generalization_profile_v2(gp: str) -> str:
    return _REGIME_FOR_PROFILE.get(gp, "R17")


def vol_level_for_profile_v2(gp: str) -> str:
    if "LOW_VOL" in gp:
        return "LOW"
    if "HIGH_VOL" in gp or "BURST" in gp:
        return "HIGH"
    if "EXTREME" in gp:
        return "EXTREME"
    return "MEDIUM"


def price_class_tag_v2(gp: str) -> str:
    for prefix in (
        "VERY_HIGH_PRICE",
        "LOW_PRICE",
        "MID_PRICE",
        "HIGH_PRICE",
        "MICRO",
    ):
        if gp.startswith(prefix):
            return prefix.replace("_PRICE", "") if "MICRO" not in prefix else "MICRO"
    return "MIXED"


def build_flight_market_path_v2(
    *,
    generalization_profile: str,
    seed: int,
    steps: int,
) -> tuple[FutureProfileV1, float, float, str, tuple[float, ...]]:
    profile = generalization_future_profile_v1(generalization_profile)
    price_tag = next(t for t in profile.tags if t.endswith("_PRICE"))
    p0 = p0_from_price_tag(price_tag)
    vol_level = vol_level_for_profile_v2(generalization_profile)
    sigma = VOL_SIGMA_BY_LEVEL[vol_level] * profile.mode_b_vol_multiplier
    regime = regime_for_generalization_profile_v2(generalization_profile)
    path = generate_price_path_v1(
        p0=p0,
        sigma=sigma,
        profile=profile,
        regime_id=regime,
        seed=seed,
        mode="MODE_B",
        steps=steps,
    )
    return profile, p0, sigma, regime, path
