"""Market Dashboard ReadModel contracts v1 — provenance foundation.

Immutable, timezone-aware provenance for available domain snapshots.
Presenter-generated provenance is prohibited; producers must supply identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
    require_aware_datetime,
    require_enum,
    require_non_empty_str,
    require_optional_non_empty_str,
    require_optional_sha256_digest,
    require_producer_module,
    require_schema_id,
    require_schema_version,
    require_timestamp_order,
)

PROVENANCE_SCHEMA_ID = "peak_trade.market_dashboard.snapshot_provenance.v1"
PROVENANCE_SCHEMA_VERSION = 1


class DashboardSourceKindV1(str, Enum):
    """Explicit source classification for dashboard snapshots."""

    CANONICAL_PRODUCER = "CANONICAL_PRODUCER"
    EVIDENCE_BUNDLE = "EVIDENCE_BUNDLE"
    OFFLINE_ARCHIVE = "OFFLINE_ARCHIVE"
    COMPOSITION_RUNTIME = "COMPOSITION_RUNTIME"
    NOT_BOUND = "NOT_BOUND"
    UNKNOWN = "UNKNOWN"


class DashboardFreshnessStateV1(str, Enum):
    """Freshness classification; unknown must remain unknown."""

    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"


@dataclass(frozen=True)
class DashboardSnapshotProvenanceV1:
    """Mandatory provenance for available domain snapshots.

    No implicit current-time default and no implicit producer default.
    At least one of ``source_reference`` or ``evidence_digest`` is required.
    """

    schema_id: str
    schema_version: int
    producer_module: str
    generated_at: datetime
    effective_at: datetime
    source_kind: DashboardSourceKindV1
    freshness_state: DashboardFreshnessStateV1
    producer_version: str | None = None
    producer_git_sha: str | None = None
    source_reference: str | None = None
    evidence_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_schema_id(self.schema_id))
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(self, "producer_module", require_producer_module(self.producer_module))
        object.__setattr__(
            self,
            "generated_at",
            require_aware_datetime(self.generated_at, field="generated_at"),
        )
        object.__setattr__(
            self,
            "effective_at",
            require_aware_datetime(self.effective_at, field="effective_at"),
        )
        require_timestamp_order(
            self.effective_at,
            self.generated_at,
            earlier_field="effective_at",
            later_field="generated_at",
        )
        object.__setattr__(
            self,
            "source_kind",
            require_enum(self.source_kind, DashboardSourceKindV1, field="source_kind"),
        )
        object.__setattr__(
            self,
            "freshness_state",
            require_enum(self.freshness_state, DashboardFreshnessStateV1, field="freshness_state"),
        )
        object.__setattr__(
            self,
            "producer_version",
            require_optional_non_empty_str(self.producer_version, field="producer_version"),
        )
        git_sha = require_optional_non_empty_str(self.producer_git_sha, field="producer_git_sha")
        if git_sha is not None and len(git_sha) < 7:
            raise MarketDashboardReadModelContractError(
                "producer_git_sha must be at least 7 characters when supplied"
            )
        object.__setattr__(self, "producer_git_sha", git_sha)
        object.__setattr__(
            self,
            "source_reference",
            require_optional_non_empty_str(self.source_reference, field="source_reference"),
        )
        object.__setattr__(
            self,
            "evidence_digest",
            require_optional_sha256_digest(self.evidence_digest, field="evidence_digest"),
        )
        if self.source_reference is None and self.evidence_digest is None:
            raise MarketDashboardReadModelContractError(
                "provenance requires source_reference or evidence_digest"
            )
        if self.producer_version is None and self.producer_git_sha is None:
            raise MarketDashboardReadModelContractError(
                "provenance requires producer_version or producer_git_sha"
            )


def new_dashboard_snapshot_provenance_v1(
    *,
    producer_module: str,
    generated_at: datetime,
    effective_at: datetime,
    source_kind: DashboardSourceKindV1 | str,
    freshness_state: DashboardFreshnessStateV1 | str,
    producer_version: str | None = None,
    producer_git_sha: str | None = None,
    source_reference: str | None = None,
    evidence_digest: str | None = None,
) -> DashboardSnapshotProvenanceV1:
    """Construct provenance with canonical schema identity (no invented producers)."""

    return DashboardSnapshotProvenanceV1(
        schema_id=PROVENANCE_SCHEMA_ID,
        schema_version=PROVENANCE_SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=require_enum(source_kind, DashboardSourceKindV1, field="source_kind"),
        freshness_state=require_enum(
            freshness_state, DashboardFreshnessStateV1, field="freshness_state"
        ),
        producer_version=producer_version,
        producer_git_sha=producer_git_sha,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
    )


__all__ = [
    "DashboardFreshnessStateV1",
    "DashboardSnapshotProvenanceV1",
    "DashboardSourceKindV1",
    "PROVENANCE_SCHEMA_ID",
    "PROVENANCE_SCHEMA_VERSION",
    "new_dashboard_snapshot_provenance_v1",
]
