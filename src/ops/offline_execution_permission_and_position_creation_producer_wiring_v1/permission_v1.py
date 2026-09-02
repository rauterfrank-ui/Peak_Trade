"""Deterministic per-action execution permission. GRANT never means live send."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.action_identity_v1 import (
    ActionIdentityError,
    compute_action_identity_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CONTRACT_VERSION,
    ENTER_LONG_MAPPER_SIDE,
    ENTER_SHORT_MAPPER_SIDE,
    EXECUTION_PERMISSION_AUTHORITY_EFFECT,
    FORBIDDEN_LIVE_ENVIRONMENTS,
    OWNER_GO,
    POSITION_CREATION_INTENT_ACTIONS,
    PRODUCTIVE_WIRE_REACHABLE,
    REQUIRED_ENVIRONMENT,
    STANDING_CANARY_AUTHORIZED,
    STANDING_GENERAL_LIVE_SUBMIT_UNLOCKED,
    STANDING_LIVE_ARMED,
    STANDING_LIVE_AUTHORIZED,
    STANDING_LIVE_ENABLED,
    STANDING_ORDERS_ALLOWED,
    STANDING_SUBMIT_UNLOCKED,
    STANDING_TESTNET_AUTHORIZED,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.existing_gate_reuse_v1 import (
    prove_existing_gates_deny_live_submit_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    ActionIdentityV1,
    EvidenceFreshnessV1,
    ExistingGateReuseProofV1,
    OfflineExecutionBoundaryInputV1,
    OfflineExecutionPermissionResultV1,
    PermissionDecisionV1,
    TransportOutcomeKindV1,
)


def _qty(raw: str) -> Decimal | None:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return value


def _deny(
    *,
    decision: PermissionDecisionV1,
    reasons: tuple[str, ...],
    input_payload: OfflineExecutionBoundaryInputV1,
    gate_reuse: ExistingGateReuseProofV1,
    action_identity: ActionIdentityV1 | None = None,
) -> OfflineExecutionPermissionResultV1:
    return OfflineExecutionPermissionResultV1(
        decision=decision,
        reason_codes=reasons,
        action_identity=action_identity,
        gate_reuse=gate_reuse,
        live_send_allowed=False,
        productive_wire_reachable=PRODUCTIVE_WIRE_REACHABLE,
        authority_effect=EXECUTION_PERMISSION_AUTHORITY_EFFECT,
        environment_bound=REQUIRED_ENVIRONMENT,
        instrument_id=input_payload.lineage.instrument_id,
        plan_digest=input_payload.lineage.plan_digest,
    )


def evaluate_offline_execution_permission_v1(
    payload: OfflineExecutionBoundaryInputV1,
) -> OfflineExecutionPermissionResultV1:
    """Evaluate one logical action. Structurally cannot imply live send."""
    if payload.contract_version != CONTRACT_VERSION:
        gate_reuse = prove_existing_gates_deny_live_submit_v1(payload.authority)
        return _deny(
            decision=PermissionDecisionV1.HALT,
            reasons=("CONTRACT_VERSION_MISMATCH",),
            input_payload=payload,
            gate_reuse=gate_reuse,
        )

    gate_reuse = prove_existing_gates_deny_live_submit_v1(payload.authority)
    reasons: list[str] = []
    decision = PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY

    standing_unlocked = any(
        [
            STANDING_LIVE_AUTHORIZED,
            STANDING_TESTNET_AUTHORIZED,
            STANDING_CANARY_AUTHORIZED,
            STANDING_ORDERS_ALLOWED,
            STANDING_LIVE_ENABLED,
            STANDING_LIVE_ARMED,
            STANDING_SUBMIT_UNLOCKED,
            STANDING_GENERAL_LIVE_SUBMIT_UNLOCKED,
        ]
    )
    if standing_unlocked:
        return _deny(
            decision=PermissionDecisionV1.HALT,
            reasons=("STANDING_AUTHORITY_FLAGS_UNLOCKED",),
            input_payload=payload,
            gate_reuse=gate_reuse,
        )

    auth = payload.authority
    if auth.owner_go != OWNER_GO:
        reasons.append("OWNER_GO_MISMATCH")
        decision = PermissionDecisionV1.DENY
    if auth.environment.strip().upper() in FORBIDDEN_LIVE_ENVIRONMENTS:
        reasons.append("ENVIRONMENT_FORBIDDEN_FOR_THIS_WORKPACKAGE")
        decision = PermissionDecisionV1.HALT
    if auth.environment.strip().upper() != REQUIRED_ENVIRONMENT:
        reasons.append("ENVIRONMENT_NOT_NON_LIVE_BOUNDARY")
        decision = PermissionDecisionV1.DENY
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
        ]
    ):
        reasons.append("AUTHORITY_SNAPSHOT_UNLOCKED")
        decision = PermissionDecisionV1.HALT
    if gate_reuse.canary_submit_allowed:
        reasons.append("EXISTING_CANARY_SUBMIT_GATE_UNEXPECTEDLY_ALLOWED")
        decision = PermissionDecisionV1.HALT
    if not gate_reuse.standing_live_flags_false:
        reasons.append("EXISTING_STANDING_FLAGS_NOT_FALSE")
        decision = PermissionDecisionV1.HALT
    if gate_reuse.flatten_live_wire_enabled:
        reasons.append("FLATTEN_LIVE_WIRE_ENABLED")
        decision = PermissionDecisionV1.HALT
    if gate_reuse.canary_permit_owns_general_decision:
        reasons.append("SECOND_PERMISSION_AUTHORITY")
        decision = PermissionDecisionV1.HALT

    lineage = payload.lineage
    if not lineage.instrument_id or lineage.instrument_id == "UNKNOWN":
        reasons.append("INSTRUMENT_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    elif lineage.instrument_id != CANONICAL_INSTRUMENT_ID:
        reasons.append("INSTRUMENT_BINDING_MISMATCH")
        decision = PermissionDecisionV1.DENY
    if not lineage.decision_id or lineage.decision_id == "UNKNOWN":
        reasons.append("DECISION_ID_MISSING_OR_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    if not lineage.correlation_id:
        reasons.append("CORRELATION_ID_MISSING")
        decision = PermissionDecisionV1.DENY
    if lineage.risk_outcome == "UNKNOWN" or not lineage.risk_outcome:
        reasons.append("RISK_OUTCOME_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    elif lineage.risk_outcome != "PASS":
        reasons.append("RISK_29P_NOT_PASS")
        decision = PermissionDecisionV1.DENY
    if not lineage.risk_digest or lineage.risk_digest == "UNKNOWN":
        reasons.append("RISK_DIGEST_MISSING_OR_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    if lineage.safety_hard_blocked is None:
        reasons.append("SAFETY_STATE_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    elif lineage.safety_hard_blocked:
        reasons.append("SAFETY_HARD_BLOCK")
        decision = PermissionDecisionV1.DENY
    if not lineage.safety_digest or lineage.safety_digest == "UNKNOWN":
        reasons.append("SAFETY_DIGEST_MISSING_OR_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    if lineage.plan_intent_action in {"", "UNKNOWN", "MISSING"}:
        reasons.append("PLAN_INTENT_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    elif lineage.plan_intent_action not in POSITION_CREATION_INTENT_ACTIONS:
        reasons.append("PLAN_NOT_POSITION_CREATION")
        decision = PermissionDecisionV1.DENY
    elif lineage.plan_intent_action == "ENTER_LONG" and lineage.plan_side != "LONG":
        reasons.append("PLAN_SIDE_MISMATCH")
        decision = PermissionDecisionV1.DENY
    elif lineage.plan_intent_action == "ENTER_SHORT" and lineage.plan_side != "SHORT":
        reasons.append("PLAN_SIDE_MISMATCH")
        decision = PermissionDecisionV1.DENY
    if lineage.plan_execution_eligible or lineage.plan_adapter_compatible:
        reasons.append("PLAN_ONLY_BOUNDARY_VIOLATION")
        decision = PermissionDecisionV1.HALT
    if lineage.plan_submission_authorized:
        reasons.append("PLAN_SUBMISSION_AUTHORIZED_TRUE")
        decision = PermissionDecisionV1.HALT
    if not lineage.plan_digest or lineage.plan_digest == "UNKNOWN":
        reasons.append("PLAN_DIGEST_MISSING_OR_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    if lineage.mapper_safety_blocked:
        reasons.append("MAPPER_SAFETY_BLOCKED")
        decision = PermissionDecisionV1.DENY
    expected_side = (
        ENTER_LONG_MAPPER_SIDE
        if lineage.plan_intent_action == "ENTER_LONG"
        else ENTER_SHORT_MAPPER_SIDE
        if lineage.plan_intent_action == "ENTER_SHORT"
        else ""
    )
    if expected_side and lineage.mapper_intended_side != expected_side:
        reasons.append("MAPPER_SIDE_MISMATCH")
        decision = PermissionDecisionV1.DENY
    if lineage.mapper_intent_action and lineage.mapper_intent_action not in {
        lineage.plan_intent_action,
        f"SIZING::{lineage.mapper_decision_outcome}",
        "",
    }:
        if lineage.mapper_intent_action != lineage.plan_intent_action:
            reasons.append("MAPPER_INTENT_MISMATCH")
            decision = PermissionDecisionV1.DENY
    plan_qty = _qty(lineage.plan_quantity)
    mapper_qty = _qty(lineage.mapper_intended_quantity)
    if plan_qty is None or mapper_qty is None:
        reasons.append("QUANTITY_UNKNOWN_OR_INVALID")
        decision = PermissionDecisionV1.DENY
    elif plan_qty <= 0 or mapper_qty <= 0:
        reasons.append("QUANTITY_NOT_POSITIVE")
        decision = PermissionDecisionV1.DENY
    elif plan_qty != mapper_qty:
        reasons.append("PLAN_MAPPER_QUANTITY_MISMATCH")
        decision = PermissionDecisionV1.DENY

    prewire = payload.prewire
    if prewire.get_performed_this_workpackage:
        reasons.append("GET_PERFORMED_THIS_WORKPACKAGE_FORBIDDEN")
        decision = PermissionDecisionV1.HALT
    if prewire.freshness_status is EvidenceFreshnessV1.MISSING:
        reasons.append("PREWIRE_EVIDENCE_MISSING")
        decision = PermissionDecisionV1.DENY
    elif prewire.freshness_status is EvidenceFreshnessV1.UNKNOWN:
        reasons.append("PREWIRE_EVIDENCE_UNKNOWN")
        decision = PermissionDecisionV1.DENY
    elif prewire.freshness_status is EvidenceFreshnessV1.STALE:
        reasons.append("PREWIRE_EVIDENCE_STALE")
        decision = PermissionDecisionV1.DENY
    elif prewire.freshness_status is not EvidenceFreshnessV1.PASS:
        reasons.append("PREWIRE_FRESHNESS_INVALID")
        decision = PermissionDecisionV1.DENY
    if prewire.source_kind != "CALLER_SUPPLIED_SNAPSHOT":
        reasons.append("PREWIRE_SOURCE_NOT_CALLER_SNAPSHOT")
        decision = PermissionDecisionV1.DENY
    if prewire.instrument_id != lineage.instrument_id:
        reasons.append("PREWIRE_INSTRUMENT_MISMATCH")
        decision = PermissionDecisionV1.DENY
    if prewire.recon_state in {"UNKNOWN", "AMBIGUOUS_SUBMIT", "UNKNOWN_SUBMIT"}:
        reasons.append("AMBIGUOUS_RECON_STATE")
        decision = PermissionDecisionV1.RECONCILE_REQUIRED
    if prewire.prior_transport_outcome == TransportOutcomeKindV1.UNKNOWN.value:
        reasons.append("PRIOR_TRANSPORT_UNKNOWN")
        decision = PermissionDecisionV1.RECONCILE_REQUIRED

    identity = None
    try:
        identity = compute_action_identity_v1(lineage)
    except ActionIdentityError as exc:
        reasons.append(str(exc).split(":", 1)[0] or "ACTION_IDENTITY_FAILED")
        if decision is PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY:
            decision = PermissionDecisionV1.DENY

    if reasons and decision is PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY:
        decision = PermissionDecisionV1.DENY
    if decision is not PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY:
        return _deny(
            decision=decision,
            reasons=tuple(dict.fromkeys(reasons)) or ("DENIED",),
            input_payload=payload,
            gate_reuse=gate_reuse,
            action_identity=identity,
        )
    return OfflineExecutionPermissionResultV1(
        decision=PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY,
        reason_codes=("GRANT_FOR_NON_LIVE_BOUNDARY",),
        action_identity=identity,
        gate_reuse=gate_reuse,
        live_send_allowed=False,
        productive_wire_reachable=False,
        authority_effect=EXECUTION_PERMISSION_AUTHORITY_EFFECT,
        environment_bound=REQUIRED_ENVIRONMENT,
        instrument_id=lineage.instrument_id,
        plan_digest=lineage.plan_digest,
    )
