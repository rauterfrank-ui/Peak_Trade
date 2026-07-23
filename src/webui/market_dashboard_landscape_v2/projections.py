"""Pure field-projection adapters — no decision/risk/sizing recomputation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from .availability import Availability
from .contracts import (
    SCHEMA_FAMILY,
    SCHEMA_VERSION,
    CanonicalDecisionSnapshotV1,
    DoublePlaySnapshotV1,
)
from .provenance import FreshnessV1, SnapshotProvenanceV1


def project_canonical_decision_snapshot_v1(
    *,
    instrument_id: str,
    decision: str,
    direction: str,
    reason_codes: Sequence[str],
    blockers: Sequence[str],
    decision_id: str | None,
    evidence_schema_version: str,
    evidence_digest: str | None,
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_trading_decision_evidence_v1",
) -> CanonicalDecisionSnapshotV1:
    """Project already-computed decision evidence fields into a Landscape snapshot.

    Forbidden: inventing decision/direction, synthesizing reason codes, or
    deriving blockers from non-evidence sources.
    """
    if not instrument_id or not decision or not direction:
        raise ValueError("instrument_id, decision, and direction are required for AVAILABLE")
    if not evidence_schema_version:
        raise ValueError("evidence_schema_version required")
    codes = tuple(str(code) for code in reason_codes)
    block = tuple(str(code) for code in blockers)
    schema_id = f"{SCHEMA_FAMILY}.canonical_decision.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind="canonical_trading_decision_evidence",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=Availability.AVAILABLE,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )
    return CanonicalDecisionSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=Availability.AVAILABLE,
        instrument_id=instrument_id,
        decision=decision,
        direction=direction,
        reason_codes=codes,
        blockers=block,
        decision_id=decision_id,
        evidence_schema_version=evidence_schema_version,
    )


def project_double_play_snapshot_v1(
    *,
    overall_status: str,
    panel_summaries: Sequence[Mapping[str, Any]],
    blockers: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.double_play_dashboard_display",
) -> DoublePlaySnapshotV1:
    """Project an existing Double Play display snapshot into Landscape form."""
    if not overall_status:
        raise ValueError("overall_status required for AVAILABLE")
    schema_id = f"{SCHEMA_FAMILY}.double_play.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at,
        source_kind="double_play_dashboard_display",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=Availability.AVAILABLE,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )
    return DoublePlaySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=Availability.AVAILABLE,
        overall_status=overall_status,
        panel_summaries=tuple(dict(row) for row in panel_summaries),
        blockers=tuple(str(code) for code in blockers),
        display_only=True,
        live_authorization=False,
    )
