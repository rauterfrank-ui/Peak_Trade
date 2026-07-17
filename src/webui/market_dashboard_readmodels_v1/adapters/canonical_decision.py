"""Canonical decision adapter: evidence object → CanonicalDecisionSummaryV1."""

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
    CanonicalDecisionStatusV1,
    CanonicalDecisionSummaryV1,
    DashboardAvailabilityStateV1,
    DecisionDirectionV1,
    UnavailableSnapshotV1,
    new_canonical_decision_summary_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "CanonicalTradingDecisionEvidenceV1"
PRODUCER_MODULE = "src.trading.master_v2.canonical_trading_decision_evidence_v1"
EVIDENCE_SCHEMA = "canonical_trading_decision_evidence_v1"

# Explicit equivalent enum projections only — no sign/confidence inference.
_OUTCOME_TO_STATUS: dict[str, CanonicalDecisionStatusV1] = {
    "blocked": CanonicalDecisionStatusV1.BLOCK,
    "hold": CanonicalDecisionStatusV1.HOLD,
    "observe": CanonicalDecisionStatusV1.HOLD,
    "no_action": CanonicalDecisionStatusV1.HOLD,
    "reduce": CanonicalDecisionStatusV1.HOLD,
    "exit": CanonicalDecisionStatusV1.HOLD,
    "enter_long": CanonicalDecisionStatusV1.ALLOW,
    "enter_short": CanonicalDecisionStatusV1.ALLOW,
    "cancel_pending": CanonicalDecisionStatusV1.UNKNOWN,
    "reconcile_only": CanonicalDecisionStatusV1.UNKNOWN,
}

_SIDE_TO_DIRECTION: dict[str, DecisionDirectionV1] = {
    "long": DecisionDirectionV1.LONG,
    "short": DecisionDirectionV1.SHORT,
    "none": DecisionDirectionV1.FLAT,
}


def adapt_canonical_decision_summary_v1(
    source: Any | None,
    *,
    generated_at: datetime,
    effective_at: datetime,
    evidence_reference: str | None = None,
    evidence_status: str | None = None,
) -> CanonicalDecisionSummaryV1 | UnavailableSnapshotV1:
    """Project an already-produced CanonicalTradingDecisionEvidenceV1-like object.

    Does not invoke integrated_offline_trading_logic_replay_v1.
    """

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="CANONICAL_DECISION_SOURCE_ABSENT",
            detail="No canonical trading decision evidence object was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    schema = enum_text(source_get(source, "evidence_schema_version"))
    if schema is not None and schema != EVIDENCE_SCHEMA:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="CANONICAL_DECISION_SCHEMA_MISMATCH",
            detail=f"Unexpected evidence_schema_version={schema!r}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    decision_outcome = enum_text(source_get(source, "decision_outcome"))
    if decision_outcome is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="CANONICAL_DECISION_OUTCOME_MISSING",
            detail="decision_outcome is required on canonical decision evidence.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    decision_status = _OUTCOME_TO_STATUS.get(
        decision_outcome.lower(), CanonicalDecisionStatusV1.UNKNOWN
    )

    selected_side = enum_text(source_get(source, "selected_side"))
    if selected_side is None:
        direction = DecisionDirectionV1.NOT_PROVIDED
    else:
        direction = _SIDE_TO_DIRECTION.get(selected_side.lower(), DecisionDirectionV1.UNKNOWN)

    try:
        digest = require_sha256_or_none(source_get(source, "semantic_digest"))
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="CANONICAL_DECISION_DIGEST_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    decision_id = enum_text(source_get(source, "decision_id"))
    reference = evidence_reference or decision_id
    if digest is None and reference is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="CANONICAL_DECISION_PROVENANCE_MISSING",
            detail="semantic_digest or evidence_reference is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
        )

    status_text = evidence_status or "EVIDENCE_PRESENT"
    reason_codes = as_reason_tuple(source_get(source, "reason_codes"))
    # Precedence trace is diagnostic ordering metadata, not newly derived blockers.
    blockers: tuple[str, ...] = ()

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

    return new_canonical_decision_summary_v1(
        decision_status=decision_status,
        direction=direction,
        confidence=None,
        evidence_status=status_text,
        reason_codes=reason_codes,
        blockers=blockers,
        evidence_digest=digest,
        evidence_reference=reference,
        effective_at=effective_at,
        provenance=provenance,
    )


__all__ = ["adapt_canonical_decision_summary_v1"]
