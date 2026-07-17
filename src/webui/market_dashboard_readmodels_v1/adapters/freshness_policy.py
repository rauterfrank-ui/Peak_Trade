"""Versioned dashboard-only freshness policy (PR-C).

Single threshold owner for DashboardFreshnessSnapshotV1 classification.
Evaluation time must be passed explicitly — no wall-clock reads.
"""

from __future__ import annotations

from dataclasses import dataclass

FRESHNESS_POLICY_ID = "market_dashboard_freshness_policy.v1"
FRESHNESS_POLICY_VERSION = 1


@dataclass(frozen=True)
class DashboardFreshnessPolicyV1:
    policy_id: str
    policy_version: int
    fresh_max_age_seconds: float
    stale_max_age_seconds: float

    def __post_init__(self) -> None:
        if self.fresh_max_age_seconds < 0 or self.stale_max_age_seconds < 0:
            raise ValueError("freshness thresholds must be >= 0")
        if self.stale_max_age_seconds < self.fresh_max_age_seconds:
            raise ValueError("stale_max_age_seconds must be >= fresh_max_age_seconds")


DEFAULT_DASHBOARD_FRESHNESS_POLICY_V1 = DashboardFreshnessPolicyV1(
    policy_id=FRESHNESS_POLICY_ID,
    policy_version=FRESHNESS_POLICY_VERSION,
    # 5 minutes fresh / 30 minutes before hard-stale classification.
    fresh_max_age_seconds=300.0,
    stale_max_age_seconds=1800.0,
)


__all__ = [
    "DEFAULT_DASHBOARD_FRESHNESS_POLICY_V1",
    "DashboardFreshnessPolicyV1",
    "FRESHNESS_POLICY_ID",
    "FRESHNESS_POLICY_VERSION",
]
