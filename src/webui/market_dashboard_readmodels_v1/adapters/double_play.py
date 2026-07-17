"""Double-Play adapter: composition + side assessments → DoublePlayDecisionSnapshotV1."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    as_reason_tuple,
    enum_text,
    require_sha256_or_none,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    DoublePlayDecisionSnapshotV1,
    SideAssessmentV1,
    UnavailableSnapshotV1,
    new_double_play_decision_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "DoublePlayCompositionResultV1"
PRODUCER_MODULE = "src.trading.master_v2.double_play_composition_matrix_v1"


def _side_assessment(source: Any | None, *, side: str) -> SideAssessmentV1 | None:
    if source is None:
        return None
    status = enum_text(source_get(source, "status"))
    if status is None:
        return None
    confidence = source_get(source, "confidence")
    score: float | None
    if confidence is None:
        score = None
    elif isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return None
    else:
        score = float(confidence)
    return SideAssessmentV1(
        status=status,
        score=score,
        reason_codes=as_reason_tuple(source_get(source, "reason_codes")),
    )


def adapt_double_play_decision_snapshot_v1(
    composition: Any | None,
    *,
    generated_at: datetime,
    effective_at: datetime,
    bull_assessment: Any | None = None,
    bear_assessment: Any | None = None,
    evidence_reference: str | None = None,
) -> DoublePlayDecisionSnapshotV1 | UnavailableSnapshotV1:
    """Project composition_matrix result fields only — no arbitration recomputation."""

    if composition is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="DOUBLE_PLAY_COMPOSITION_ABSENT",
            detail="No DoublePlayCompositionResultV1 object was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    composition_result = enum_text(source_get(composition, "composition_status"))
    arbitration_status = enum_text(source_get(composition, "conflict_status"))
    if composition_result is None or arbitration_status is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DOUBLE_PLAY_FIELDS_MISSING",
            detail="composition_status and conflict_status are required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    bull = _side_assessment(bull_assessment, side="bull")
    bear = _side_assessment(bear_assessment, side="bear")
    if bull is None or bear is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="DOUBLE_PLAY_SIDE_ASSESSMENT_ABSENT",
            detail="bull_assessment and bear_assessment sources are required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    try:
        digest = require_sha256_or_none(source_get(composition, "semantic_digest"))
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DOUBLE_PLAY_DIGEST_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    composition_id = enum_text(source_get(composition, "composition_id"))
    reference = evidence_reference or composition_id
    if digest is None and reference is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="DOUBLE_PLAY_PROVENANCE_MISSING",
            detail="semantic_digest or evidence_reference is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
        )

    blockers = as_reason_tuple(source_get(composition, "reason_codes"))

    prov_generated_at = generated_at if generated_at >= effective_at else effective_at
    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=prov_generated_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.CANONICAL_PRODUCER,
        freshness_state=DashboardFreshnessStateV1.UNKNOWN,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=reference,
        evidence_digest=digest,
    )

    return new_double_play_decision_snapshot_v1(
        bull_assessment=bull,
        bear_assessment=bear,
        composition_result=composition_result,
        arbitration_status=arbitration_status,
        blockers=blockers,
        evidence_digest=digest,
        evidence_reference=reference,
        effective_at=effective_at,
        provenance=provenance,
    )


__all__ = ["adapt_double_play_decision_snapshot_v1"]
