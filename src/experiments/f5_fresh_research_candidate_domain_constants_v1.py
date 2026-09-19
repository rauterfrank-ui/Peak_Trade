"""Operator-bound discrete domain for F5-FRESH futures input freshness shadow research.

Distinct from M9/F1 volatility numeric max-age (different token, clock, consumer).
PRODUCTIVE_ACTIVATION=false; thresholds are research candidates only.
"""

from __future__ import annotations

from typing import Final

CANDIDATE_DOMAIN_SCHEMA_VERSION: Final[str] = (
    "canonical_f5_fresh_futures_input_freshness_candidate_domain/v1"
)
OWNER_VALUE_TOKEN: Final[str] = "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS"
AGE_UNIT: Final[str] = "SECONDS"
AGE_REFERENCE_CLOCK: Final[str] = "BAR_EVENT_TIME"
AGE_SEMANTIC: Final[str] = "FUTURES_INPUT_READINESS_SAFETY_FRESHNESS_STATE"
F1_M9_DEDUPLICATION_FORBIDDEN: Final[bool] = True
CMC_VOLATILITY_MAX_AGE_ALPHA_REUSE_FORBIDDEN: Final[bool] = True

OPERATOR_BOUND_CANDIDATE_FRESHNESS_MAX_AGE_SECONDS: Final[tuple[int, ...]] = (
    30,
    45,
    90,
    180,
    240,
    450,
    1200,
    2400,
)
