"""Execution/reconciliation adapter from EntryExitPolicyDecisionV0-like sources."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    enum_text,
    require_sha256_or_none,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    ExecutionStateSnapshotV1,
    OperatingModeV1,
    UnavailableSnapshotV1,
    new_execution_state_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
    require_enum,
)

EXPECTED_SOURCE = "EntryExitPolicyDecisionV0"
PRODUCER_MODULE = "src.trading.master_v2.double_play_entry_exit_policy_v0"
_FILL_STATE_NOT_PROVIDED = "NOT_PROVIDED"


def adapt_execution_state_snapshot_v1(
    source: Any | None,
    *,
    generated_at: datetime,
    effective_at: datetime,
    operating_mode: OperatingModeV1 | str = OperatingModeV1.OFFLINE,
    evidence_reference: str | None = None,
) -> ExecutionStateSnapshotV1 | UnavailableSnapshotV1:
    """Project entry/exit offline decision fields; fill remains NOT_PROVIDED.

    Missing source → UNAVAILABLE (not no-order). Does not submit or mutate intents.
    """

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="EXECUTION_SOURCE_ABSENT",
            detail=(
                "No EntryExitPolicyDecisionV0 source was supplied. "
                "Missing execution evidence remains UNAVAILABLE, not no-order."
            ),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    intent_state = enum_text(source_get(source, "decision_outcome"))
    reconciliation_state = enum_text(source_get(source, "reconciliation_state"))
    position_state = enum_text(source_get(source, "position_state"))
    if intent_state is None or reconciliation_state is None or position_state is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="EXECUTION_FIELDS_MISSING",
            detail="decision_outcome, reconciliation_state, and position_state are required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    try:
        mode = require_enum(operating_mode, OperatingModeV1, field="operating_mode")
        digest = require_sha256_or_none(source_get(source, "semantic_digest"))
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="EXECUTION_SOURCE_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    decision_id = enum_text(source_get(source, "policy_decision_id"))
    reference = evidence_reference or decision_id
    if digest is None and reference is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="EXECUTION_PROVENANCE_MISSING",
            detail="semantic_digest or evidence_reference is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
        )

    # Unknown outcome preserves producer position_state text (e.g. submission_unknown).
    unknown_outcome_state = position_state

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=generated_at if generated_at >= effective_at else effective_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.CANONICAL_PRODUCER,
        freshness_state=DashboardFreshnessStateV1.UNKNOWN,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=reference,
        evidence_digest=digest,
    )

    return new_execution_state_snapshot_v1(
        operating_mode=mode,
        intent_state=intent_state,
        fill_state=_FILL_STATE_NOT_PROVIDED,
        reconciliation_state=reconciliation_state,
        unknown_outcome_state=unknown_outcome_state,
        effective_at=effective_at,
        provenance=provenance,
    )


__all__ = ["adapt_execution_state_snapshot_v1"]
