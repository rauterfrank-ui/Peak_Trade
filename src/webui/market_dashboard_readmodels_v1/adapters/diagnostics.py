"""Diagnostics adapter: support-bundle artifacts → DiagnosticsSummarySnapshotV1."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    enum_text,
    require_sha256_or_none,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    DiagnosticsSummarySnapshotV1,
    UnavailableSnapshotV1,
    new_diagnostics_summary_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "offline_productive_linear_diagnostics_support_bundle.v0"
PRODUCER_MODULE = (
    "src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0"
)
SCHEMA_VERSION = "offline_productive_linear_diagnostics_support_bundle.v0"


def adapt_diagnostics_summary_snapshot_v1(
    source: Mapping[str, Any] | None,
    *,
    generated_at: datetime,
    effective_at: datetime,
    bundle_reference: str | None = None,
) -> DiagnosticsSummarySnapshotV1 | UnavailableSnapshotV1:
    """Project diagnostic statuses only; always non-authoritative.

    Accepts only the canonical support-bundle artifacts mapping. Display-only
    layout JSONs are rejected as schema mismatch (SOURCE ambiguity resolved by
    selecting the sole canonical owner).
    """

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="DIAGNOSTICS_SOURCE_ABSENT",
            detail="No diagnostics support-bundle artifacts mapping was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=bundle_reference,
        )

    if not isinstance(source, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_SOURCE_TYPE_INVALID",
            detail="Diagnostics source must be a support-bundle artifacts mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=bundle_reference,
        )

    schema = enum_text(source_get(source, "schema_version"))
    if schema is not None and schema != SCHEMA_VERSION:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_SCHEMA_MISMATCH",
            detail=f"Expected schema_version={SCHEMA_VERSION!r}, got {schema!r}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=bundle_reference,
        )

    aggregate_status = enum_text(source_get(source, "aggregate_status"))
    source_statuses = source_get(source, "source_statuses")
    statuses: list[str] = []
    if aggregate_status:
        statuses.append(f"aggregate:{aggregate_status}")
    if isinstance(source_statuses, Mapping):
        for key in sorted(source_statuses):
            value = enum_text(source_statuses[key])
            if value:
                statuses.append(f"{key}:{value}")
    if not statuses:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_STATUSES_MISSING",
            detail="aggregate_status or source_statuses required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=bundle_reference,
        )

    try:
        digest = require_sha256_or_none(source_get(source, "output_digest"))
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_DIGEST_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=bundle_reference,
        )

    evidence_id = enum_text(source_get(source, "diagnostic_evidence_id"))
    reference = bundle_reference or evidence_id
    if digest is None and reference is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_PROVENANCE_MISSING",
            detail="output_digest or bundle_reference is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
        )

    # Preserve non-authority: authority_effect must be NONE when present.
    authority_effect = enum_text(source_get(source, "authority_effect"))
    if authority_effect is not None and authority_effect.upper() != "NONE":
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DIAGNOSTICS_AUTHORITY_EFFECT_FORBIDDEN",
            detail="Diagnostics bundle must declare authority_effect=NONE.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=reference,
        )

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=generated_at if generated_at >= effective_at else effective_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.EVIDENCE_BUNDLE,
        freshness_state=DashboardFreshnessStateV1.UNKNOWN,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=reference,
        evidence_digest=digest,
    )

    return new_diagnostics_summary_snapshot_v1(
        diagnostic_statuses=tuple(statuses),
        bundle_digest=digest,
        bundle_reference=reference,
        effective_at=effective_at,
        provenance=provenance,
        non_authoritative=True,
        diagnostic_only=True,
    )


__all__ = ["adapt_diagnostics_summary_snapshot_v1"]
