"""Offline position-creation request producer. Reuses venue-native body mapping."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_TD_MODE,
    ENDPOINT_SUBMIT,
    ENTER_LONG_MAPPER_SIDE,
    ENTER_SHORT_MAPPER_SIDE,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    CanonicalLineageSnapshotV1,
    OfflineExecutionPermissionResultV1,
    PermissionDecisionV1,
    PositionCreationRequestCandidateV1,
    PrewireEvidenceSnapshotV1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)


class PositionCreationProducerError(RuntimeError):
    """Fail-closed position-creation request producer violation."""


def produce_position_creation_request_candidate_v1(
    *,
    permission: OfflineExecutionPermissionResultV1,
    lineage: CanonicalLineageSnapshotV1,
    evidence: PrewireEvidenceSnapshotV1,
) -> PositionCreationRequestCandidateV1:
    if permission.decision is not PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY:
        raise PositionCreationProducerError("PERMISSION_NOT_GRANT_FOR_NON_LIVE_BOUNDARY")
    if permission.live_send_allowed:
        raise PositionCreationProducerError("LIVE_SEND_ALLOWED_FORBIDDEN")
    if permission.action_identity is None:
        raise PositionCreationProducerError("ACTION_IDENTITY_REQUIRED")
    identity = permission.action_identity
    if lineage.instrument_id != CANONICAL_INSTRUMENT_ID:
        raise PositionCreationProducerError("INSTRUMENT_MUTATION_FORBIDDEN")
    if evidence.instrument_id != lineage.instrument_id:
        raise PositionCreationProducerError("EVIDENCE_INSTRUMENT_DRIFT")
    if identity.instrument_id != lineage.instrument_id:
        raise PositionCreationProducerError("IDENTITY_INSTRUMENT_DRIFT")
    if identity.plan_digest != lineage.plan_digest:
        raise PositionCreationProducerError("PLAN_DIGEST_DRIFT")
    if str(lineage.plan_quantity) != str(lineage.mapper_intended_quantity):
        raise PositionCreationProducerError("QUANTITY_DRIFT")
    if str(evidence.quantity) != str(lineage.plan_quantity):
        raise PositionCreationProducerError("PREWIRE_QUANTITY_DRIFT")
    expected_side = (
        ENTER_LONG_MAPPER_SIDE
        if lineage.plan_intent_action == "ENTER_LONG"
        else ENTER_SHORT_MAPPER_SIDE
    )
    if lineage.mapper_intended_side != expected_side:
        raise PositionCreationProducerError("SIDE_DRIFT")
    order_type = str(evidence.order_type or DEFAULT_ORDER_TYPE).strip().lower()
    td_mode = str(evidence.td_mode or DEFAULT_TD_MODE).strip().lower()
    try:
        body = build_venue_native_order_body_v1(
            client_order_id=identity.client_order_id,
            instrument=lineage.instrument_id,
            order_type=order_type,
            side=expected_side.lower(),
            quantity=str(lineage.plan_quantity),
            td_mode=td_mode,
            px=str(evidence.limit_px),
            reduce_only=False,
        )
    except OkxResponseMapperError as exc:
        raise PositionCreationProducerError(f"VENUE_BODY_FAIL_CLOSED:{exc}") from exc
    if body.get("instId") != lineage.instrument_id:
        raise PositionCreationProducerError("BODY_INSTRUMENT_MUTATION")
    if str(body.get("side") or "") != expected_side.lower():
        raise PositionCreationProducerError("BODY_SIDE_MUTATION")
    if str(body.get("sz") or "") != str(lineage.plan_quantity):
        raise PositionCreationProducerError("BODY_SIZE_MUTATION")
    if "reduceOnly" in body:
        raise PositionCreationProducerError("ENTRY_REDUCE_ONLY_FORBIDDEN")
    return PositionCreationRequestCandidateV1(
        action_identity=identity,
        instrument_id=lineage.instrument_id,
        side=expected_side.lower(),
        quantity=str(lineage.plan_quantity),
        order_type=order_type,
        td_mode=td_mode,
        limit_px=str(evidence.limit_px),
        reduce_only=False,
        venue_native_body=body,
        endpoint=ENDPOINT_SUBMIT,
        plan_digest=lineage.plan_digest,
        permission_decision=permission.decision.value,
    )
