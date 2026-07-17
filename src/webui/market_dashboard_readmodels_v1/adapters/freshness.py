"""Freshness projection over already-created snapshot metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    source_get,
)
from src.webui.market_dashboard_readmodels_v1.adapters.freshness_policy import (
    DEFAULT_DASHBOARD_FRESHNESS_POLICY_V1,
    DashboardFreshnessPolicyV1,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardFreshnessSnapshotV1,
    SourceFreshnessEntryV1,
    UnavailableSnapshotV1,
    new_dashboard_freshness_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)


def _classify_age(
    age_seconds: float | None,
    *,
    missing: bool,
    policy: DashboardFreshnessPolicyV1,
) -> tuple[DashboardFreshnessStateV1, bool]:
    if missing:
        return DashboardFreshnessStateV1.MISSING, False
    if age_seconds is None:
        return DashboardFreshnessStateV1.UNKNOWN, False
    if age_seconds <= policy.fresh_max_age_seconds:
        return DashboardFreshnessStateV1.FRESH, False
    if age_seconds <= policy.stale_max_age_seconds:
        # Beyond fresh window but within soft-stale observation band → STALE.
        return DashboardFreshnessStateV1.STALE, True
    return DashboardFreshnessStateV1.STALE, True


def _source_effective_at(snapshot: Any) -> datetime | None:
    if isinstance(snapshot, UnavailableSnapshotV1):
        return None
    value = source_get(snapshot, "effective_at")
    if isinstance(value, datetime):
        return value
    provenance = source_get(snapshot, "provenance")
    if provenance is not None:
        value = source_get(provenance, "effective_at")
        if isinstance(value, datetime):
            return value
    return None


def adapt_dashboard_freshness_snapshot_v1(
    *,
    page_generated_at: datetime,
    sources: Mapping[str, Any] | Iterable[tuple[str, Any]],
    policy: DashboardFreshnessPolicyV1 = DEFAULT_DASHBOARD_FRESHNESS_POLICY_V1,
    source_reference: str | None = None,
) -> DashboardFreshnessSnapshotV1:
    """Classify per-source age against an explicitly passed evaluation time.

    Does not infer trading eligibility from freshness.
    """

    if isinstance(sources, Mapping):
        items = list(sources.items())
    else:
        items = list(sources)

    entries: list[SourceFreshnessEntryV1] = []
    for source_key, snapshot in items:
        missing = snapshot is None or isinstance(snapshot, UnavailableSnapshotV1)
        effective_at = None if missing else _source_effective_at(snapshot)
        age: float | None = None
        if effective_at is not None:
            age = max(0.0, (page_generated_at - effective_at).total_seconds())
        freshness_state, stale = _classify_age(age, missing=missing, policy=policy)
        if missing:
            age = None
        entries.append(
            SourceFreshnessEntryV1(
                source_key=str(source_key),
                freshness_state=freshness_state,
                source_age_seconds=age,
                missing=missing,
                stale=stale,
            )
        )

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module="src.webui.market_dashboard_readmodels_v1.adapters.freshness",
        generated_at=page_generated_at,
        effective_at=page_generated_at,
        source_kind=DashboardSourceKindV1.COMPOSITION_RUNTIME,
        freshness_state=DashboardFreshnessStateV1.FRESH,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=source_reference or policy.policy_id,
    )

    return new_dashboard_freshness_snapshot_v1(
        page_generated_at=page_generated_at,
        source_entries=tuple(entries),
        provenance=provenance,
    )


__all__ = ["adapt_dashboard_freshness_snapshot_v1"]
