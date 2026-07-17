"""Safety/authority adapter — no consolidated owner → explicit NOT_BOUND/unavailable.

Does not combine kill-switch, risk, and authority producers into a new owner.
Accepts only a single pre-consolidated mapping that already carries all TriState
fields; otherwise returns UnavailableSnapshotV1.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    as_reason_tuple,
    enum_text,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    AuthorityClassificationV1,
    DashboardAvailabilityStateV1,
    SafetyAuthoritySnapshotV1,
    TriStateV1,
    UnavailableSnapshotV1,
    new_safety_authority_snapshot_v1,
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

EXPECTED_SOURCE = "consolidated.safety_authority.snapshot.not_bound"
PRODUCER_MODULE = "src.webui.market_dashboard_readmodels_v1.adapters.safety_authority"


def adapt_safety_authority_snapshot_v1(
    source: Mapping[str, Any] | None,
    *,
    generated_at: datetime,
    effective_at: datetime | None = None,
    source_reference: str | None = None,
) -> SafetyAuthoritySnapshotV1 | UnavailableSnapshotV1:
    """Project a single pre-consolidated safety/authority payload, or NOT_BOUND.

    Missing source → NOT_BOUND (not false/inactive). Does not invent TriState
    values from LIVE_AUTHORIZED constants or UI read-only capability.
    """

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.NOT_BOUND,
            reason_code="SAFETY_AUTHORITY_PRODUCER_NOT_BOUND",
            detail=(
                "No consolidated canonical SafetyAuthority producer is bound. "
                "Missing authority evidence remains UNKNOWN/UNAVAILABLE, not false."
            ),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if not isinstance(source, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="SAFETY_AUTHORITY_SOURCE_TYPE_INVALID",
            detail="SafetyAuthority source must be a single consolidated mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    required = (
        "authority_classification",
        "kill_switch_state",
        "risk_gate_state",
        "execution_permission_state",
    )
    missing = [key for key in required if source_get(source, key) is None]
    if missing:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="SAFETY_AUTHORITY_FIELDS_INCOMPLETE",
            detail=f"Consolidated source missing required fields: {', '.join(missing)}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    try:
        authority = require_enum(
            source_get(source, "authority_classification"),
            AuthorityClassificationV1,
            field="authority_classification",
        )
        kill_switch = require_enum(
            source_get(source, "kill_switch_state"), TriStateV1, field="kill_switch_state"
        )
        risk_gate = require_enum(
            source_get(source, "risk_gate_state"), TriStateV1, field="risk_gate_state"
        )
        execution_permission = require_enum(
            source_get(source, "execution_permission_state"),
            TriStateV1,
            field="execution_permission_state",
        )
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="SAFETY_AUTHORITY_ENUM_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    eff = effective_at or generated_at
    producer_module = enum_text(source_get(source, "producer_module")) or PRODUCER_MODULE
    producer_version = enum_text(source_get(source, "producer_version")) or ADAPTER_PRODUCER_VERSION
    reference = source_reference or enum_text(source_get(source, "source_reference"))
    if reference is None:
        reference = "consolidated.safety_authority.explicit"

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=producer_module,
        generated_at=generated_at if generated_at >= eff else eff,
        effective_at=eff,
        source_kind=DashboardSourceKindV1.CANONICAL_PRODUCER,
        freshness_state=DashboardFreshnessStateV1.UNKNOWN,
        producer_version=producer_version,
        source_reference=reference,
    )

    return new_safety_authority_snapshot_v1(
        authority_classification=authority,
        kill_switch_state=kill_switch,
        risk_gate_state=risk_gate,
        execution_permission_state=execution_permission,
        fail_closed_reason_codes=as_reason_tuple(source_get(source, "fail_closed_reason_codes")),
        effective_at=eff,
        provenance=provenance,
    )


__all__ = ["adapt_safety_authority_snapshot_v1"]
