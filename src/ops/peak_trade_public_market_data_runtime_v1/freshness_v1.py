"""Owner-ratified Public V1 freshness (R1–R3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS,
    PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
    PUBLIC_V1_TRADE_FRESHNESS_POLICY,
    PUBLIC_V1_TRADE_GLOBAL_MAX_AGE_SECONDS,
)


class PublicFreshnessError(ValueError):
    """Fail-closed freshness adjudication."""


@dataclass(frozen=True)
class LiveFreshnessVerdictV1:
    publishable: bool
    stale: bool
    reason: Optional[str]


def classify_live_mark_price_freshness_v1(*, age_seconds: float) -> LiveFreshnessVerdictV1:
    max_age = float(PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS)
    if age_seconds < 0:
        return LiveFreshnessVerdictV1(False, True, "CAPTURE_IN_FUTURE")
    if age_seconds > max_age:
        return LiveFreshnessVerdictV1(False, True, f"STALE_OVER_MAX_AGE_SECONDS:{max_age}")
    return LiveFreshnessVerdictV1(True, False, None)


def classify_live_best_bid_ask_freshness_v1(*, age_seconds: float) -> LiveFreshnessVerdictV1:
    max_age = float(PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS)
    if age_seconds < 0:
        return LiveFreshnessVerdictV1(False, True, "CAPTURE_IN_FUTURE")
    if age_seconds > max_age:
        return LiveFreshnessVerdictV1(False, True, f"STALE_OVER_MAX_AGE_SECONDS:{max_age}")
    return LiveFreshnessVerdictV1(True, False, None)


def assert_no_global_trade_max_age_v1() -> None:
    if PUBLIC_V1_TRADE_FRESHNESS_POLICY != "CONSUMER_SPECIFIC":
        raise PublicFreshnessError("TRADE_FRESHNESS_POLICY_MISMATCH")
    if PUBLIC_V1_TRADE_GLOBAL_MAX_AGE_SECONDS is not None:
        raise PublicFreshnessError("GLOBAL_TRADE_MAX_AGE_FORBIDDEN")


def consumer_trade_freshness_required_v1(
    *, consumer_id: str, max_age_seconds: Optional[float]
) -> bool:
    """Return True when consumer may publish; False / fail closed when numeric bound missing."""
    assert_no_global_trade_max_age_v1()
    if max_age_seconds is None:
        raise PublicFreshnessError(f"CONSUMER_MAX_AGE_UNRATIFIED:{consumer_id}")
    return True
