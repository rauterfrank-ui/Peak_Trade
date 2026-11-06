"""Route-C submit composition: Z2DM candidate → gated submit surface, fail-closed.

Consumes already-authoritative upstream values only. Does not invent Side,
Qty, Instrument, Price, posSide, tdMode, ordType, execution eligibility, or
submission authorization. Does not invoke HTTP.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.composition_v1 import (
    CanonicalOfflinePositionCreationPathInputV1,
    CanonicalOfflinePositionCreationPathResultV1,
    run_canonical_offline_position_creation_path_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    STANDING_CANARY_AUTHORIZED,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.gated_entry_submit_surface_v1 import (
    GatedEntrySubmitSurfaceBindingV1,
    bind_gated_entry_submit_surface_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    EvidenceFreshnessV1,
    PermissionDecisionV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    EXIT_DECISION_OUTCOMES,
    HOLD_DECISION_OUTCOMES,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.position_mode_submit_body_contract_v1 import (
    evaluate_position_mode_submit_body_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    CANARY_OPERATIVE_ORDER_SZ,
    CREATE_PATH_CURRENTLY_AUTHORIZED,
    CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
    CURRENT_PRODUCTIVE_WIRE_REACHABLE,
    FORBIDDEN_QUANTITY_AUTHORITY_SOURCES,
    FORBIDDEN_SIDE_AUTHORITY_SOURCES,
    HOST_GRAPH_ACTIVATION,
    MAX_POSITIONS_EFFECTIVE,
    NONZERO_POSITION_STATES,
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    PREREQUISITE_08_CLOSED,
    QUANTITY_AUTHORITY_SOURCE_REQUIRED,
    ROUTE_C_FUTURE_EXECUTION_PERMIT_KIND,
    ROUTE_C_OWNER_GO,
    SIDE_AUTHORITY_SOURCE_REQUIRED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
)


def _same_qty(left: object, right: object) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, ValueError, TypeError):
        return str(left) == str(right)


class RouteCSubmitCompositionStatusV1(str, Enum):
    CANDIDATE = "CANDIDATE"
    DENY = "DENY"
    HALT = "HALT"


@dataclass(frozen=True)
class RouteCFutureExecutionPermitV1:
    owner_go: str
    permit_id: str
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go": self.owner_go,
            "permit_id": self.permit_id,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class RouteCSubmitCompositionInputV1:
    path: CanonicalOfflinePositionCreationPathInputV1
    quantity_authority_source: str
    side_authority_source: str
    quantity_provenance_digest: str
    quantity_provenance_final: str
    credential_identity_ref: str = ""
    execution_permit: RouteCFutureExecutionPermitV1 | None = None
    canary_plan_builder_invoked: bool = False
    host_activation_requested: bool = False
    secret_materialized: bool = False


@dataclass(frozen=True)
class RouteCSubmitCompositionResultV1:
    status: RouteCSubmitCompositionStatusV1
    reason_codes: tuple[str, ...]
    path: CanonicalOfflinePositionCreationPathResultV1 | None
    gated_surface: GatedEntrySubmitSurfaceBindingV1 | None
    submission_ready: bool
    position_mode_semantics: str
    position_mode_fail_closed: bool
    host_graph_activated: bool
    productive_wire_reachable: bool
    create_path_productively_wire_capable: bool
    create_path_currently_authorized: bool
    prerequisite_08_closed: bool
    http_invoked: bool
    secret_materialized: bool
    recording_is_live_transport: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "path": None if self.path is None else self.path.boundary.permission.to_dict(),
            "gated_surface": None if self.gated_surface is None else self.gated_surface.to_dict(),
            "submission_ready": self.submission_ready,
            "position_mode_semantics": self.position_mode_semantics,
            "position_mode_fail_closed": self.position_mode_fail_closed,
            "host_graph_activated": self.host_graph_activated,
            "productive_wire_reachable": self.productive_wire_reachable,
            "create_path_productively_wire_capable": self.create_path_productively_wire_capable,
            "create_path_currently_authorized": self.create_path_currently_authorized,
            "prerequisite_08_closed": self.prerequisite_08_closed,
            "http_invoked": self.http_invoked,
            "secret_materialized": self.secret_materialized,
            "recording_is_live_transport": self.recording_is_live_transport,
        }


def _result(
    *,
    status: RouteCSubmitCompositionStatusV1,
    reasons: tuple[str, ...],
    path: CanonicalOfflinePositionCreationPathResultV1 | None = None,
    gated_surface: GatedEntrySubmitSurfaceBindingV1 | None = None,
    submission_ready: bool = False,
) -> RouteCSubmitCompositionResultV1:
    if submission_ready:
        raise RuntimeError("SUBMISSION_READY_STRUCTURALLY_FORBIDDEN_THIS_SLICE")
    return RouteCSubmitCompositionResultV1(
        status=status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        path=path,
        gated_surface=gated_surface,
        submission_ready=False,
        position_mode_semantics=POSITION_MODE_SUBMIT_BODY_SEMANTICS,
        position_mode_fail_closed=POSITION_MODE_FAIL_CLOSED,
        host_graph_activated=False,
        productive_wire_reachable=False,
        create_path_productively_wire_capable=CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
        create_path_currently_authorized=CREATE_PATH_CURRENTLY_AUTHORIZED,
        prerequisite_08_closed=PREREQUISITE_08_CLOSED,
        http_invoked=False,
        secret_materialized=False,
        recording_is_live_transport=False,
    )


def _preflight_reasons(payload: RouteCSubmitCompositionInputV1) -> tuple[str, ...]:
    reasons: list[str] = []
    if payload.secret_materialized:
        reasons.append("SECRET_MATERIALIZATION_FORBIDDEN")
    if payload.canary_plan_builder_invoked:
        reasons.append("CANARY_PLAN_BUILDER_FORBIDDEN")
    if payload.host_activation_requested or HOST_GRAPH_ACTIVATION:
        reasons.append("HOST_GRAPH_ACTIVATION_FORBIDDEN")
    qty_source = str(payload.quantity_authority_source or "").strip()
    if qty_source != QUANTITY_AUTHORITY_SOURCE_REQUIRED:
        reasons.append("QUANTITY_AUTHORITY_SOURCE_NOT_STEP_29P")
        if (
            qty_source in FORBIDDEN_QUANTITY_AUTHORITY_SOURCES
            or qty_source == "SUI_OPERATIVE_ORDER_SZ"
        ):
            reasons.append("CANARY_QTY_DEFAULT_REJECTED")
    side_source = str(payload.side_authority_source or "").strip()
    if side_source != SIDE_AUTHORITY_SOURCE_REQUIRED:
        reasons.append("SIDE_AUTHORITY_SOURCE_NOT_MAPPER_FROM_PLAN")
        if side_source in FORBIDDEN_SIDE_AUTHORITY_SOURCES or side_source == "DEFAULT_SIDE":
            reasons.append("CANARY_SIDE_DEFAULT_REJECTED")
    digest = str(payload.quantity_provenance_digest or "").strip()
    if digest == "" or digest.upper() in {"UNKNOWN", "MISSING"}:
        reasons.append("QUANTITY_PROVENANCE_MISSING")
    final_qty = str(payload.quantity_provenance_final or "").strip()
    if final_qty == "" or final_qty.upper() in {"UNKNOWN", "MISSING"}:
        reasons.append("QUANTITY_PROVENANCE_FINAL_MISSING")
    if qty_source != QUANTITY_AUTHORITY_SOURCE_REQUIRED and final_qty == CANARY_OPERATIVE_ORDER_SZ:
        reasons.append("CANARY_QTY_DEFAULT_REJECTED")
    credential_ref = str(payload.credential_identity_ref or "")
    lowered = credential_ref.lower()
    if lowered.startswith("plaintext:") or lowered.startswith("sk-") or "secret=" in lowered:
        reasons.append("IMPLICIT_CREDENTIAL_MATERIALIZATION_FORBIDDEN")
    auth = payload.path.authority
    if any(
        [
            auth.live_authorized,
            auth.testnet_authorized,
            auth.canary_authorized,
            auth.orders_allowed,
            auth.live_enabled,
            auth.live_armed,
            auth.submit_unlocked,
            auth.general_live_submit_unlocked,
            payload.path.assembly.live_send_allowed,
        ]
    ):
        reasons.append("AUTHORITY_SNAPSHOT_UNLOCKED")
    if LIVE_ENABLED:
        reasons.append("LIVE_ENABLED_BLOCKS")
    if LIVE_ARMED:
        reasons.append("LIVE_ARMED_BLOCKS")
    if LIVE_AUTHORIZED:
        reasons.append("LIVE_AUTHORIZED_BLOCKS")
    if STANDING_CANARY_AUTHORIZED or auth.canary_authorized:
        reasons.append("CANARY_AUTHORIZED_BLOCKS")
    if SUBMIT_UNLOCKED or auth.submit_unlocked:
        reasons.append("SUBMIT_UNLOCKED_BLOCKS")
    if CURRENT_PRODUCTIVE_WIRE_REACHABLE:
        reasons.append("PRODUCTIVE_WIRE_REACHABLE_STRUCTURALLY_FORBIDDEN")
    prewire = payload.path.prewire
    if prewire.freshness_status is EvidenceFreshnessV1.STALE:
        reasons.append("PREWIRE_EVIDENCE_STALE")
    elif prewire.freshness_status is EvidenceFreshnessV1.MISSING:
        reasons.append("PREWIRE_EVIDENCE_MISSING")
    elif prewire.freshness_status is EvidenceFreshnessV1.UNKNOWN:
        reasons.append("PREWIRE_EVIDENCE_UNKNOWN")
    if not str(prewire.limit_px or "").strip() or str(prewire.limit_px).strip().upper() in {
        "UNKNOWN",
        "MISSING",
        "0",
        "0.0",
    }:
        reasons.append("MISSING_PRICE")
    if str(prewire.instrument_id) != CANONICAL_INSTRUMENT_ID:
        reasons.append("INCONSISTENT_INSTRUMENT")
    if str(payload.path.assembly.selection_instrument_id) != CANONICAL_INSTRUMENT_ID:
        reasons.append("INCONSISTENT_INSTRUMENT")
    if str(prewire.position_observation_state or "").strip().upper() in {
        token.upper() for token in NONZERO_POSITION_STATES
    }:
        reasons.append("MAX_POSITIONS_VIOLATION")
    if MAX_POSITIONS_EFFECTIVE != 1:
        reasons.append("MAX_POSITIONS_CONTRACT_DRIFT")
    evidence = payload.path.assembly.evidence
    if evidence is not None:
        outcome = str(evidence.decision_outcome or "").strip().lower()
        if outcome in HOLD_DECISION_OUTCOMES:
            reasons.append("HOLD")
        elif outcome in EXIT_DECISION_OUTCOMES:
            if outcome == "reduce":
                reasons.append("REDUCE")
            else:
                reasons.append("EXIT")
        if str(evidence.instrument_id) != CANONICAL_INSTRUMENT_ID:
            reasons.append("INCONSISTENT_INSTRUMENT")
    intent = payload.path.assembly.intent
    if intent is not None:
        action = str(intent.intent_action or "").strip()
        if action in {"HOLD", "NO_ACTION"}:
            reasons.append("HOLD")
        elif action == "EXIT":
            reasons.append("EXIT")
        elif action == "REDUCE":
            reasons.append("REDUCE")
        if intent.execution_eligible or intent.adapter_compatible or intent.submission_authorized:
            reasons.append("STEP_29Q_DIRECT_SUBMIT_FORBIDDEN")
        if final_qty and not _same_qty(intent.quantity, final_qty):
            reasons.append("INCONSISTENT_QUANTITY_PROVENANCE")
    mapper = payload.path.assembly.mapper_action
    if mapper is not None and str(mapper.intended_side or "").strip().upper() == "HOLD":
        reasons.append("HOLD")
    permit = payload.execution_permit
    if permit is None:
        reasons.append("MISSING_FUTURE_EXECUTION_PERMIT")
    else:
        if str(permit.kind) != ROUTE_C_FUTURE_EXECUTION_PERMIT_KIND:
            reasons.append("EXECUTION_PERMIT_KIND_INVALID")
        if not str(permit.permit_id or "").strip():
            reasons.append("EXECUTION_PERMIT_ID_MISSING")
        if not str(permit.owner_go or "").strip():
            reasons.append("EXECUTION_PERMIT_OWNER_GO_MISSING")
        if str(permit.owner_go) == ROUTE_C_OWNER_GO:
            reasons.append("IMPLEMENTATION_GO_CANNOT_BE_EXECUTION_PERMIT")
    return tuple(dict.fromkeys(reasons))


def run_route_c_submit_composition_v1(
    payload: RouteCSubmitCompositionInputV1,
    *,
    transport: OfflineRecordingTransportV1 | None = None,
) -> RouteCSubmitCompositionResultV1:
    """Compose Route-C lineage to a non-submission-ready gated candidate."""
    preflight = _preflight_reasons(payload)
    halt_codes = {
        "SECRET_MATERIALIZATION_FORBIDDEN",
        "HOST_GRAPH_ACTIVATION_FORBIDDEN",
        "AUTHORITY_SNAPSHOT_UNLOCKED",
        "LIVE_ENABLED_BLOCKS",
        "LIVE_ARMED_BLOCKS",
        "LIVE_AUTHORIZED_BLOCKS",
        "CANARY_AUTHORIZED_BLOCKS",
        "SUBMIT_UNLOCKED_BLOCKS",
        "PRODUCTIVE_WIRE_REACHABLE_STRUCTURALLY_FORBIDDEN",
        "IMPLICIT_CREDENTIAL_MATERIALIZATION_FORBIDDEN",
        "STEP_29Q_DIRECT_SUBMIT_FORBIDDEN",
        "IMPLEMENTATION_GO_CANNOT_BE_EXECUTION_PERMIT",
    }
    deny_without_path = {
        "CANARY_PLAN_BUILDER_FORBIDDEN",
        "CANARY_QTY_DEFAULT_REJECTED",
        "CANARY_SIDE_DEFAULT_REJECTED",
        "QUANTITY_AUTHORITY_SOURCE_NOT_STEP_29P",
        "SIDE_AUTHORITY_SOURCE_NOT_MAPPER_FROM_PLAN",
        "QUANTITY_PROVENANCE_MISSING",
        "QUANTITY_PROVENANCE_FINAL_MISSING",
        "INCONSISTENT_QUANTITY_PROVENANCE",
        "INCONSISTENT_INSTRUMENT",
        "MISSING_PRICE",
        "PREWIRE_EVIDENCE_STALE",
        "PREWIRE_EVIDENCE_MISSING",
        "PREWIRE_EVIDENCE_UNKNOWN",
        "MAX_POSITIONS_VIOLATION",
        "MAX_POSITIONS_CONTRACT_DRIFT",
        "HOLD",
        "EXIT",
        "REDUCE",
        "EXECUTION_PERMIT_KIND_INVALID",
        "EXECUTION_PERMIT_ID_MISSING",
        "EXECUTION_PERMIT_OWNER_GO_MISSING",
    }
    if any(code in halt_codes for code in preflight):
        return _result(
            status=RouteCSubmitCompositionStatusV1.HALT,
            reasons=preflight,
        )
    if any(code in deny_without_path for code in preflight):
        return _result(
            status=RouteCSubmitCompositionStatusV1.DENY,
            reasons=preflight,
        )

    recorder = transport or OfflineRecordingTransportV1()
    path = run_canonical_offline_position_creation_path_v1(payload.path, transport=recorder)
    reasons = list(preflight)
    if path.assembly.status.value != "PASS" or path.boundary.request_candidate is None:
        reasons.extend(path.assembly.reason_codes)
        reasons.extend(path.boundary.permission.reason_codes)
        status = (
            RouteCSubmitCompositionStatusV1.HALT
            if path.boundary.permission.decision is PermissionDecisionV1.HALT
            else RouteCSubmitCompositionStatusV1.DENY
        )
        return _result(status=status, reasons=tuple(reasons) or ("DENIED",), path=path)

    candidate = path.boundary.request_candidate
    if not _same_qty(candidate.quantity, payload.quantity_provenance_final):
        reasons.append("INCONSISTENT_QUANTITY_PROVENANCE")
    lineage = path.assembly.lineage
    if lineage is not None and str(lineage.risk_digest) != str(payload.quantity_provenance_digest):
        reasons.append("INCONSISTENT_QUANTITY_PROVENANCE")
    if lineage is not None and not _same_qty(
        lineage.plan_quantity, payload.quantity_provenance_final
    ):
        reasons.append("INCONSISTENT_QUANTITY_PROVENANCE")

    semantics, pos_reasons, submission_allowed = evaluate_position_mode_submit_body_v1(
        venue_native_body=candidate.venue_native_body,
        pos_mode=str(payload.path.prewire.pos_mode or ""),
    )
    del semantics
    del submission_allowed
    reasons.extend(pos_reasons)

    gated = bind_gated_entry_submit_surface_v1()
    if gated.http_invoked or gated.secret_materialized or gated.productive_wire_reachable:
        return _result(
            status=RouteCSubmitCompositionStatusV1.HALT,
            reasons=tuple(reasons) + ("GATED_SURFACE_WIRE_FENCE",),
            path=path,
            gated_surface=gated,
        )
    if recorder.PRODUCTIVE_WIRE_REACHABLE or recorder.wire_send_enabled:
        return _result(
            status=RouteCSubmitCompositionStatusV1.HALT,
            reasons=tuple(reasons) + ("RECORDING_TRANSPORT_WIRE_FENCE",),
            path=path,
            gated_surface=gated,
        )

    unique = tuple(dict.fromkeys(reasons))
    blocking = {
        "INCONSISTENT_QUANTITY_PROVENANCE",
        "POSSIDE_EMITTED_WHILE_SEMANTICS_UNPROVEN",
        "POSSIDE_NET_MANUFACTURED_FORBIDDEN",
    }
    if any(code in blocking for code in unique):
        return _result(
            status=RouteCSubmitCompositionStatusV1.DENY,
            reasons=unique,
            path=path,
            gated_surface=gated,
        )
    return _result(
        status=RouteCSubmitCompositionStatusV1.CANDIDATE,
        reasons=unique or ("ROUTE_C_SUBMIT_COMPOSER_CANDIDATE_ONLY",),
        path=path,
        gated_surface=gated,
    )
