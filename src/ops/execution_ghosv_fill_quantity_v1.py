"""Execution GHOSV fill-integrity semantics for bound Reconciliation evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    SIMULATION_OFFLINE,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_HALTED_UNRESOLVED,
    REASON_FILL_EXCEEDS_ORDER,
    REASON_NEGATIVE_REMAINING,
    RECONCILIATION_PROVIDER_OFFLINE_STUB,
    EvidenceLayer,
    ExchangeReconciliationIdentity,
    FullCoreExchangeReconciliationDecisionV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
)


@dataclass(frozen=True)
class ExecutionFillQuantityIncidentV1:
    session_id: str
    observed_at: datetime
    identity_digest: str
    venue_order_id: str
    snapshot_sha256: str
    evidence_refs: tuple[str, ...]
    local_submit_outcome: LocalSubmitOutcome
    reconciliation_reason: str

    check_id = "FILL_QUANTITY_INTEGRITY"
    traffic = "RED"
    outcome = "FAIL"
    incident_type = "CONFIRMED_FILL_QUANTITY_VIOLATION"


def build_offline_execution_fill_quantity_incident_v1(
    *,
    session_id: str,
    observed_at: datetime,
    identity: ExchangeReconciliationIdentity,
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    decision: FullCoreExchangeReconciliationDecisionV1,
    local_submit_outcome: LocalSubmitOutcome,
) -> ExecutionFillQuantityIncidentV1 | None:
    if (
        identity.execution_environment != "SHADOW"
        or snapshot.simulation_mode != SIMULATION_OFFLINE
        or snapshot.provider != RECONCILIATION_PROVIDER_OFFLINE_STUB
    ):
        return None
    return build_execution_fill_quantity_incident_v1(
        session_id=session_id,
        observed_at=observed_at,
        identity=identity,
        snapshot=snapshot,
        decision=decision,
        local_submit_outcome=local_submit_outcome,
    )


def build_execution_fill_quantity_incident_v1(
    *,
    session_id: str,
    observed_at: datetime,
    identity: ExchangeReconciliationIdentity,
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    decision: FullCoreExchangeReconciliationDecisionV1,
    local_submit_outcome: LocalSubmitOutcome,
) -> ExecutionFillQuantityIncidentV1 | None:
    """Map an unambiguously bound quantity violation after source validation."""
    if (
        snapshot.transport_failures
        or local_submit_outcome is LocalSubmitOutcome.NOT_SUBMITTED
        or decision.outcome != OUTCOME_HALTED_UNRESOLVED
        or decision.reasons not in {(REASON_FILL_EXCEEDS_ORDER,), (REASON_NEGATIVE_REMAINING,)}
        or any(item.response_status != "200" for item in snapshot.evidence_items)
    ):
        return None

    orders = [
        item for item in snapshot.evidence_items if item.layer is EvidenceLayer.EXCHANGE_ORDER_STATE
    ]
    fills = [
        item for item in snapshot.evidence_items if item.layer is EvidenceLayer.EXCHANGE_FILL_STATE
    ]
    if not orders:
        return None
    venue_order_id = orders[0].payload.get("ordId")
    if (
        not isinstance(venue_order_id, str)
        or not venue_order_id
        or venue_order_id.strip() != venue_order_id
        or (identity.exchange_ord_id is not None and venue_order_id != identity.exchange_ord_id)
        or any(
            item.payload.get("ordId") != venue_order_id
            or item.payload.get("clOrdId") != identity.clordid
            or item.payload.get("instId") != identity.native_id
            or item.account != identity.account_identity
            or item.environment != identity.execution_environment
            or item.instrument != identity.instrument_id
            for item in (*orders, *fills)
        )
    ):
        return None

    reason = decision.reasons[0]
    if any(not item.payload.get("sz") for item in orders):
        return None
    if reason == REASON_NEGATIVE_REMAINING:
        if any(not item.payload.get("accFillSz") for item in orders):
            return None
        witnesses = orders
    else:
        if not fills or any(
            not item.payload.get("fillSz")
            or not (item.payload.get("fillId") or item.payload.get("tradeId"))
            for item in fills
        ):
            return None
        witnesses = orders + fills

    return ExecutionFillQuantityIncidentV1(
        session_id=session_id,
        observed_at=observed_at,
        identity_digest=identity.identity_digest(),
        venue_order_id=venue_order_id,
        snapshot_sha256=hashlib.sha256(
            canonical_json_dumps(snapshot.to_dict()).encode()
        ).hexdigest(),
        evidence_refs=tuple(
            sorted(
                {
                    hashlib.sha256(canonical_json_dumps(item.to_dict()).encode()).hexdigest()
                    for item in witnesses
                }
            )
        ),
        local_submit_outcome=local_submit_outcome,
        reconciliation_reason=reason,
    )
