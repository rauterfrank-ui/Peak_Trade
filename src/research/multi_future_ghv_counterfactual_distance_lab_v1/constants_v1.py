from __future__ import annotations

EXPERIMENT_ID = "multi_future_ghv_counterfactual_distance_lab_v1"
LAB_OWNER = "research.multi_future_ghv_counterfactual_distance_lab_v1"

PRICE_SCALES_P0 = (
    0.10,
    0.20,
    1.0,
    10.0,
    100.0,
    1000.0,
    5000.0,
    50000.0,
    100000.0,
)

VOLATILITY_LEVELS = (
    "VERY_LOW",
    "LOW",
    "MEDIUM",
    "HIGH",
    "EXTREME",
)

# Volatility as fraction of price (σ) — aligned with CMC volatility_estimate semantics.
VOL_SIGMA_BY_LEVEL = {
    "VERY_LOW": 0.005,
    "LOW": 0.015,
    "MEDIUM": 0.04,
    "HIGH": 0.10,
    "EXTREME": 0.25,
}

REGIME_IDS = tuple(f"R{i:02d}" for i in range(1, 18))

ARCHETYPE_TAGS = (
    "MICRO_PRICE",
    "LOW_PRICE",
    "MID_PRICE",
    "HIGH_PRICE",
    "VERY_HIGH_PRICE",
    "VERY_LOW_VOL",
    "LOW_VOL",
    "MEDIUM_VOL",
    "HIGH_VOL",
    "EXTREME_VOL",
    "TRENDING",
    "MEAN_REVERTING",
    "CHOPPY",
    "BURST_VOL",
    "GAP_JUMP",
    "ASYMMETRIC",
    "MIXED_REGIME",
)

STAGE2_GENERALIZATION_PROFILES = (
    "MICRO_LOW_VOL",
    "MICRO_HIGH_VOL",
    "MICRO_CHOP",
    "MICRO_TREND",
    "MICRO_JUMP",
    "LOW_PRICE_LOW_VOL",
    "LOW_PRICE_HIGH_VOL",
    "LOW_PRICE_TREND",
    "LOW_PRICE_JUMP",
    "MID_PRICE_MEAN_REVERSION",
    "MID_PRICE_TREND",
    "MID_PRICE_CHOP",
    "HIGH_PRICE_LOW_VOL",
    "HIGH_PRICE_HIGH_VOL",
    "HIGH_PRICE_MEAN_REVERSION",
    "VERY_HIGH_PRICE_CHOP",
    "VERY_HIGH_PRICE_BURST_VOL",
    "VERY_HIGH_PRICE_TREND",
    "MIXED_REGIME",
)

REAL_CONTRACT_PROFILE_IDS = (
    "SUB_DOLLAR_PERP_PROFILE",
    "LOW_PRICE_PERP_PROFILE",
    "MID_PRICE_PERP_PROFILE",
    "HIGH_PRICE_PERP_PROFILE",
)

STAGE1_SEED_COUNT = 2
STAGE2_CYCLES_PER_FLIGHT = 60
TARGET_STAGE1_CASES = 600_000
TARGET_STAGE2_FLIGHTS = 720
