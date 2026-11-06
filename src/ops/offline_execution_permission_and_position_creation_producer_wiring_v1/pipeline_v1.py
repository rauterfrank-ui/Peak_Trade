"""Compose permission -> prewire -> request candidate -> recording transport."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    OfflineExecutionBoundaryInputV1,
    OfflineExecutionBoundaryResultV1,
    OfflineExecutionPermissionResultV1,
    PermissionDecisionV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.permission_v1 import (
    evaluate_offline_execution_permission_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.prewire_validation_v1 import (
    validate_prewire_snapshots_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
    RecordingTransportError,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.request_producer_v1 import (
    PositionCreationProducerError,
    produce_position_creation_request_candidate_v1,
)


def run_offline_execution_boundary_v1(
    payload: OfflineExecutionBoundaryInputV1,
    *,
    transport: OfflineRecordingTransportV1 | None = None,
) -> OfflineExecutionBoundaryResultV1:
    permission = evaluate_offline_execution_permission_v1(payload)
    if permission.decision is not PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY:
        return OfflineExecutionBoundaryResultV1(
            permission=permission,
            request_candidate=None,
            transport_record=None,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )
    prewire_reasons = validate_prewire_snapshots_v1(
        lineage=payload.lineage,
        evidence=payload.prewire,
    )
    if prewire_reasons:
        denied = OfflineExecutionPermissionResultV1(
            decision=PermissionDecisionV1.DENY,
            reason_codes=prewire_reasons,
            action_identity=permission.action_identity,
            gate_reuse=permission.gate_reuse,
            live_send_allowed=False,
            productive_wire_reachable=False,
            authority_effect=permission.authority_effect,
            environment_bound=permission.environment_bound,
            instrument_id=permission.instrument_id,
            plan_digest=permission.plan_digest,
        )
        return OfflineExecutionBoundaryResultV1(
            permission=denied,
            request_candidate=None,
            transport_record=None,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )
    try:
        candidate = produce_position_creation_request_candidate_v1(
            permission=permission,
            lineage=payload.lineage,
            evidence=payload.prewire,
        )
    except PositionCreationProducerError as exc:
        denied = OfflineExecutionPermissionResultV1(
            decision=PermissionDecisionV1.DENY,
            reason_codes=(str(exc).split(":", 1)[0],),
            action_identity=permission.action_identity,
            gate_reuse=permission.gate_reuse,
            live_send_allowed=False,
            productive_wire_reachable=False,
            authority_effect=permission.authority_effect,
            environment_bound=permission.environment_bound,
            instrument_id=permission.instrument_id,
            plan_digest=permission.plan_digest,
        )
        return OfflineExecutionBoundaryResultV1(
            permission=denied,
            request_candidate=None,
            transport_record=None,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )
    recorder = transport or OfflineRecordingTransportV1()
    try:
        record = recorder.handoff(candidate)
    except RecordingTransportError as exc:
        denied = OfflineExecutionPermissionResultV1(
            decision=(
                PermissionDecisionV1.RECONCILE_REQUIRED
                if "AMBIGUOUS_SUBMIT_NO_RESEND" in str(exc)
                else PermissionDecisionV1.DENY
            ),
            reason_codes=(str(exc).split(":", 1)[0],),
            action_identity=permission.action_identity,
            gate_reuse=permission.gate_reuse,
            live_send_allowed=False,
            productive_wire_reachable=False,
            authority_effect=permission.authority_effect,
            environment_bound=permission.environment_bound,
            instrument_id=permission.instrument_id,
            plan_digest=permission.plan_digest,
        )
        return OfflineExecutionBoundaryResultV1(
            permission=denied,
            request_candidate=candidate,
            transport_record=None,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )
    if record.outcome.value == "UNKNOWN":
        denied = OfflineExecutionPermissionResultV1(
            decision=PermissionDecisionV1.RECONCILE_REQUIRED,
            reason_codes=("AMBIGUOUS_SUBMIT", "RECONCILE_REQUIRED"),
            action_identity=permission.action_identity,
            gate_reuse=permission.gate_reuse,
            live_send_allowed=False,
            productive_wire_reachable=False,
            authority_effect=permission.authority_effect,
            environment_bound=permission.environment_bound,
            instrument_id=permission.instrument_id,
            plan_digest=permission.plan_digest,
        )
        return OfflineExecutionBoundaryResultV1(
            permission=denied,
            request_candidate=candidate,
            transport_record=record,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )
    return OfflineExecutionBoundaryResultV1(
        permission=permission,
        request_candidate=candidate,
        transport_record=record,
        prerequisite_08_closed=False,
        real_position_created=False,
        venue_mutation_performed=False,
    )
