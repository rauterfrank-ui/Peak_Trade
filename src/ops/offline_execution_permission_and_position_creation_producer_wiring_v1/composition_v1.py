"""Canonical offline composition: assembler → existing Z2DB boundary → recording.

This is the offline composition entrypoint. It does not activate Cap 7.2
host orchestration and does not mint a second trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXECUTION_PERMISSION_AUTHORITY_EFFECT,
    PRODUCTIVE_WIRE_REACHABLE,
    REQUIRED_ENVIRONMENT,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.existing_gate_reuse_v1 import (
    prove_existing_gates_deny_live_submit_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.lineage_assembler_v1 import (
    AssembledCanonicalLineageV1,
    CanonicalLineageAssemblyInputV1,
    CanonicalLineageAssemblyResultV1,
    LineageAssemblyStatusV1,
    assemble_canonical_lineage_snapshot_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    AuthoritySnapshotV1,
    OfflineExecutionBoundaryInputV1,
    OfflineExecutionBoundaryResultV1,
    OfflineExecutionPermissionResultV1,
    PermissionDecisionV1,
    PrewireEvidenceSnapshotV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    ALLOWED_PERMISSION_OWNER_GOS,
    LINEAGE_PROVENANCE_PRODUCTIVE,
    Z2DB_PERMISSION_OWNER_GO,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.pipeline_v1 import (
    run_offline_execution_boundary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
)


@dataclass(frozen=True)
class CanonicalOfflinePositionCreationPathInputV1:
    assembly: CanonicalLineageAssemblyInputV1
    authority: AuthoritySnapshotV1
    prewire: PrewireEvidenceSnapshotV1


@dataclass(frozen=True)
class CanonicalOfflinePositionCreationPathResultV1:
    assembly: CanonicalLineageAssemblyResultV1
    boundary: OfflineExecutionBoundaryResultV1
    host_graph_activated: bool
    productive_wire_reachable: bool
    live_send_allowed: bool
    prerequisite_08_closed: bool
    real_position_created: bool
    venue_mutation_performed: bool


def _permission_decision_for_assembly(
    status: LineageAssemblyStatusV1,
) -> PermissionDecisionV1:
    if status is LineageAssemblyStatusV1.HALT:
        return PermissionDecisionV1.HALT
    return PermissionDecisionV1.DENY


def _denied_boundary(
    *,
    payload: CanonicalOfflinePositionCreationPathInputV1,
    reasons: tuple[str, ...],
    decision: PermissionDecisionV1,
) -> OfflineExecutionBoundaryResultV1:
    gate_reuse = prove_existing_gates_deny_live_submit_v1(payload.authority)
    permission = OfflineExecutionPermissionResultV1(
        decision=decision,
        reason_codes=reasons,
        action_identity=None,
        gate_reuse=gate_reuse,
        live_send_allowed=False,
        productive_wire_reachable=PRODUCTIVE_WIRE_REACHABLE,
        authority_effect=EXECUTION_PERMISSION_AUTHORITY_EFFECT,
        environment_bound=REQUIRED_ENVIRONMENT,
        instrument_id=str(payload.prewire.instrument_id or ""),
        plan_digest="",
    )
    return OfflineExecutionBoundaryResultV1(
        permission=permission,
        request_candidate=None,
        transport_record=None,
        prerequisite_08_closed=False,
        real_position_created=False,
        venue_mutation_performed=False,
    )


def _bind_z2db_permission_owner_go(authority: AuthoritySnapshotV1) -> AuthoritySnapshotV1:
    if authority.owner_go == Z2DB_PERMISSION_OWNER_GO:
        return authority
    return replace(authority, owner_go=Z2DB_PERMISSION_OWNER_GO)


def accept_assembled_canonical_lineage_v1(
    assembled: AssembledCanonicalLineageV1,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if assembled.provenance != LINEAGE_PROVENANCE_PRODUCTIVE:
        reasons.append("FIXTURE_LINEAGE_NOT_PRODUCTIVE")
    if assembled.assembler_id == "" or assembled.assembly_digest == "":
        reasons.append("FIXTURE_LINEAGE_NOT_PRODUCTIVE")
    return tuple(reasons)


def run_canonical_offline_position_creation_path_v1(
    payload: CanonicalOfflinePositionCreationPathInputV1,
    *,
    transport: OfflineRecordingTransportV1 | None = None,
    assembled_override: AssembledCanonicalLineageV1 | None = None,
) -> CanonicalOfflinePositionCreationPathResultV1:
    """Compose typed upstream outputs through Z2DB offline recording.

    `assembled_override` exists only so fail-closed tests can present a
    fixture-marked lineage. Productive callers must leave it None.
    """
    if payload.authority.owner_go not in ALLOWED_PERMISSION_OWNER_GOS:
        assembly = CanonicalLineageAssemblyResultV1(
            status=LineageAssemblyStatusV1.DENY,
            lineage=None,
            assembled=None,
            reason_codes=("OWNER_GO_MISMATCH",),
            provenance=None,
        )
        boundary = _denied_boundary(
            payload=payload,
            reasons=("OWNER_GO_MISMATCH",),
            decision=PermissionDecisionV1.DENY,
        )
        return CanonicalOfflinePositionCreationPathResultV1(
            assembly=assembly,
            boundary=boundary,
            host_graph_activated=False,
            productive_wire_reachable=False,
            live_send_allowed=False,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )

    if any(
        [
            payload.authority.live_authorized,
            payload.authority.testnet_authorized,
            payload.authority.canary_authorized,
            payload.authority.orders_allowed,
            payload.authority.live_enabled,
            payload.authority.live_armed,
            payload.authority.submit_unlocked,
            payload.authority.general_live_submit_unlocked,
            payload.assembly.live_send_allowed,
        ]
    ):
        assembly = CanonicalLineageAssemblyResultV1(
            status=LineageAssemblyStatusV1.HALT,
            lineage=None,
            assembled=None,
            reason_codes=("LIVE_SEND_ALLOWED",),
            provenance=None,
        )
        boundary = _denied_boundary(
            payload=payload,
            reasons=("LIVE_SEND_ALLOWED",),
            decision=PermissionDecisionV1.HALT,
        )
        return CanonicalOfflinePositionCreationPathResultV1(
            assembly=assembly,
            boundary=boundary,
            host_graph_activated=False,
            productive_wire_reachable=False,
            live_send_allowed=False,
            prerequisite_08_closed=False,
            real_position_created=False,
            venue_mutation_performed=False,
        )

    if assembled_override is not None:
        override_reasons = accept_assembled_canonical_lineage_v1(assembled_override)
        if override_reasons:
            assembly = CanonicalLineageAssemblyResultV1(
                status=LineageAssemblyStatusV1.HALT,
                lineage=None,
                assembled=None,
                reason_codes=override_reasons,
                provenance=assembled_override.provenance,
            )
            boundary = _denied_boundary(
                payload=payload,
                reasons=override_reasons,
                decision=PermissionDecisionV1.HALT,
            )
            return CanonicalOfflinePositionCreationPathResultV1(
                assembly=assembly,
                boundary=boundary,
                host_graph_activated=False,
                productive_wire_reachable=False,
                live_send_allowed=False,
                prerequisite_08_closed=False,
                real_position_created=False,
                venue_mutation_performed=False,
            )
        assembly = CanonicalLineageAssemblyResultV1(
            status=LineageAssemblyStatusV1.PASS,
            lineage=assembled_override.lineage,
            assembled=assembled_override,
            reason_codes=("CANONICAL_LINEAGE_ASSEMBLED",),
            provenance=assembled_override.provenance,
        )
        assembled = assembled_override
    else:
        assembly = assemble_canonical_lineage_snapshot_v1(payload.assembly)
        if (
            assembly.status is not LineageAssemblyStatusV1.PASS
            or assembly.assembled is None
            or assembly.lineage is None
        ):
            boundary = _denied_boundary(
                payload=payload,
                reasons=assembly.reason_codes,
                decision=_permission_decision_for_assembly(assembly.status),
            )
            return CanonicalOfflinePositionCreationPathResultV1(
                assembly=assembly,
                boundary=boundary,
                host_graph_activated=False,
                productive_wire_reachable=False,
                live_send_allowed=False,
                prerequisite_08_closed=False,
                real_position_created=False,
                venue_mutation_performed=False,
            )
        assembled = assembly.assembled
        override_reasons = accept_assembled_canonical_lineage_v1(assembled)
        if override_reasons:
            halted = CanonicalLineageAssemblyResultV1(
                status=LineageAssemblyStatusV1.HALT,
                lineage=None,
                assembled=None,
                reason_codes=override_reasons,
                provenance=assembled.provenance,
            )
            boundary = _denied_boundary(
                payload=payload,
                reasons=override_reasons,
                decision=PermissionDecisionV1.HALT,
            )
            return CanonicalOfflinePositionCreationPathResultV1(
                assembly=halted,
                boundary=boundary,
                host_graph_activated=False,
                productive_wire_reachable=False,
                live_send_allowed=False,
                prerequisite_08_closed=False,
                real_position_created=False,
                venue_mutation_performed=False,
            )

    boundary_input = OfflineExecutionBoundaryInputV1(
        contract_version=CONTRACT_VERSION,
        authority=_bind_z2db_permission_owner_go(payload.authority),
        lineage=assembled.lineage,
        prewire=payload.prewire,
    )
    boundary = run_offline_execution_boundary_v1(boundary_input, transport=transport)
    return CanonicalOfflinePositionCreationPathResultV1(
        assembly=assembly,
        boundary=boundary,
        host_graph_activated=False,
        productive_wire_reachable=False,
        live_send_allowed=False,
        prerequisite_08_closed=False,
        real_position_created=False,
        venue_mutation_performed=False,
    )
