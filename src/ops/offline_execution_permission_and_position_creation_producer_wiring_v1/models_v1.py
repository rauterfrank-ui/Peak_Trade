"""Immutable input and result contracts for the offline execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class EvidenceFreshnessV1(str, Enum):
    PASS = "PASS"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"


class PermissionDecisionV1(str, Enum):
    GRANT_FOR_NON_LIVE_BOUNDARY = "GRANT_FOR_NON_LIVE_BOUNDARY"
    DENY = "DENY"
    WAIT = "WAIT"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    HALT = "HALT"


class TransportOutcomeKindV1(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    RECORDED = "RECORDED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"


class ReconObligationV1(str, Enum):
    NONE = "NONE"
    QUERY_BEFORE_RETRY = "QUERY_BEFORE_RETRY"
    RESTART_RECOVERY_REQUIRED = "RESTART_RECOVERY_REQUIRED"


@dataclass(frozen=True)
class AuthoritySnapshotV1:
    live_authorized: bool
    testnet_authorized: bool
    canary_authorized: bool
    orders_allowed: bool
    live_enabled: bool
    live_armed: bool
    submit_unlocked: bool
    general_live_submit_unlocked: bool
    environment: str
    owner_go: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "live_authorized": self.live_authorized,
            "testnet_authorized": self.testnet_authorized,
            "canary_authorized": self.canary_authorized,
            "orders_allowed": self.orders_allowed,
            "live_enabled": self.live_enabled,
            "live_armed": self.live_armed,
            "submit_unlocked": self.submit_unlocked,
            "general_live_submit_unlocked": self.general_live_submit_unlocked,
            "environment": self.environment,
            "owner_go": self.owner_go,
        }


@dataclass(frozen=True)
class CanonicalLineageSnapshotV1:
    instrument_id: str
    decision_id: str
    correlation_id: str
    cycle_index: int
    trading_epoch: str
    risk_outcome: str
    risk_digest: str
    safety_hard_blocked: bool | None
    safety_digest: str
    plan_intent_action: str
    plan_side: str
    plan_quantity: str
    plan_digest: str
    plan_execution_eligible: bool
    plan_adapter_compatible: bool
    plan_submission_authorized: bool
    mapper_intended_side: str
    mapper_intended_quantity: str
    mapper_decision_outcome: str
    mapper_intent_action: str
    mapper_safety_blocked: bool
    mapper_reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "decision_id": self.decision_id,
            "correlation_id": self.correlation_id,
            "cycle_index": self.cycle_index,
            "trading_epoch": self.trading_epoch,
            "risk_outcome": self.risk_outcome,
            "risk_digest": self.risk_digest,
            "safety_hard_blocked": self.safety_hard_blocked,
            "safety_digest": self.safety_digest,
            "plan_intent_action": self.plan_intent_action,
            "plan_side": self.plan_side,
            "plan_quantity": self.plan_quantity,
            "plan_digest": self.plan_digest,
            "plan_execution_eligible": self.plan_execution_eligible,
            "plan_adapter_compatible": self.plan_adapter_compatible,
            "plan_submission_authorized": self.plan_submission_authorized,
            "mapper_intended_side": self.mapper_intended_side,
            "mapper_intended_quantity": self.mapper_intended_quantity,
            "mapper_decision_outcome": self.mapper_decision_outcome,
            "mapper_intent_action": self.mapper_intent_action,
            "mapper_safety_blocked": self.mapper_safety_blocked,
            "mapper_reason_codes": list(self.mapper_reason_codes),
        }


@dataclass(frozen=True)
class PrewireEvidenceSnapshotV1:
    freshness_status: EvidenceFreshnessV1
    source_kind: str
    get_performed_this_workpackage: bool
    instrument_id: str
    instrument_state: str
    order_type: str
    td_mode: str
    limit_px: str
    quantity: str
    max_lmt_sz: str
    avail_buy: str
    avail_sell: str
    leverage: str
    mgn_mode: str
    pos_mode: str
    account_mode: str
    position_observation_state: str
    recon_state: str
    prior_action_identity: str
    prior_transport_outcome: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "freshness_status": self.freshness_status.value,
            "source_kind": self.source_kind,
            "get_performed_this_workpackage": self.get_performed_this_workpackage,
            "instrument_id": self.instrument_id,
            "instrument_state": self.instrument_state,
            "order_type": self.order_type,
            "td_mode": self.td_mode,
            "limit_px": self.limit_px,
            "quantity": self.quantity,
            "max_lmt_sz": self.max_lmt_sz,
            "avail_buy": self.avail_buy,
            "avail_sell": self.avail_sell,
            "leverage": self.leverage,
            "mgn_mode": self.mgn_mode,
            "pos_mode": self.pos_mode,
            "account_mode": self.account_mode,
            "position_observation_state": self.position_observation_state,
            "recon_state": self.recon_state,
            "prior_action_identity": self.prior_action_identity,
            "prior_transport_outcome": self.prior_transport_outcome,
        }


@dataclass(frozen=True)
class OfflineExecutionBoundaryInputV1:
    contract_version: str
    authority: AuthoritySnapshotV1
    lineage: CanonicalLineageSnapshotV1
    prewire: PrewireEvidenceSnapshotV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "authority": self.authority.to_dict(),
            "lineage": self.lineage.to_dict(),
            "prewire": self.prewire.to_dict(),
        }


@dataclass(frozen=True)
class ActionIdentityV1:
    action_identity: str
    correlation_id: str
    cycle_index: int
    client_order_id: str
    plan_digest: str
    instrument_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_identity": self.action_identity,
            "correlation_id": self.correlation_id,
            "cycle_index": self.cycle_index,
            "client_order_id": self.client_order_id,
            "plan_digest": self.plan_digest,
            "instrument_id": self.instrument_id,
        }


@dataclass(frozen=True)
class ExistingGateReuseProofV1:
    canary_submit_allowed: bool
    canary_submit_reasons: tuple[str, ...]
    standing_live_flags_false: bool
    flatten_live_wire_enabled: bool
    canary_permit_owns_general_decision: bool
    flatten_pre_send_owns_entry_decision: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "canary_submit_allowed": self.canary_submit_allowed,
            "canary_submit_reasons": list(self.canary_submit_reasons),
            "standing_live_flags_false": self.standing_live_flags_false,
            "flatten_live_wire_enabled": self.flatten_live_wire_enabled,
            "canary_permit_owns_general_decision": self.canary_permit_owns_general_decision,
            "flatten_pre_send_owns_entry_decision": self.flatten_pre_send_owns_entry_decision,
        }


@dataclass(frozen=True)
class OfflineExecutionPermissionResultV1:
    decision: PermissionDecisionV1
    reason_codes: tuple[str, ...]
    action_identity: ActionIdentityV1 | None
    gate_reuse: ExistingGateReuseProofV1
    live_send_allowed: bool
    productive_wire_reachable: bool
    authority_effect: str
    environment_bound: str
    instrument_id: str
    plan_digest: str

    def __post_init__(self) -> None:
        if self.live_send_allowed is not False:
            raise ValueError("LIVE_SEND_ALLOWED_STRUCTURALLY_FORBIDDEN")
        if self.productive_wire_reachable is not False:
            raise ValueError("PRODUCTIVE_WIRE_REACHABLE_STRUCTURALLY_FORBIDDEN")
        if self.authority_effect != "NONE":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "action_identity": (
                None if self.action_identity is None else self.action_identity.to_dict()
            ),
            "gate_reuse": self.gate_reuse.to_dict(),
            "live_send_allowed": self.live_send_allowed,
            "productive_wire_reachable": self.productive_wire_reachable,
            "authority_effect": self.authority_effect,
            "environment_bound": self.environment_bound,
            "instrument_id": self.instrument_id,
            "plan_digest": self.plan_digest,
        }


@dataclass(frozen=True)
class PositionCreationRequestCandidateV1:
    action_identity: ActionIdentityV1
    instrument_id: str
    side: str
    quantity: str
    order_type: str
    td_mode: str
    limit_px: str
    reduce_only: bool
    venue_native_body: Mapping[str, Any]
    endpoint: str
    plan_digest: str
    permission_decision: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_identity": self.action_identity.to_dict(),
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "td_mode": self.td_mode,
            "limit_px": self.limit_px,
            "reduce_only": self.reduce_only,
            "venue_native_body": dict(self.venue_native_body),
            "endpoint": self.endpoint,
            "plan_digest": self.plan_digest,
            "permission_decision": self.permission_decision,
        }


@dataclass(frozen=True)
class RecordingTransportRecordV1:
    outcome: TransportOutcomeKindV1
    action_identity: str
    client_order_id: str
    instrument_id: str
    side: str
    quantity: str
    body_sha256: str
    lifecycle_state: str
    recon_obligation: ReconObligationV1
    duplicate_suppressed: bool
    productive_wire_reachable: bool
    network_call_performed: bool
    secret_materialized: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.productive_wire_reachable is not False:
            raise ValueError("PRODUCTIVE_WIRE_REACHABLE_STRUCTURALLY_FORBIDDEN")
        if self.network_call_performed is not False:
            raise ValueError("NETWORK_CALL_STRUCTURALLY_FORBIDDEN")
        if self.secret_materialized is not False:
            raise ValueError("SECRET_MATERIALIZATION_STRUCTURALLY_FORBIDDEN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "action_identity": self.action_identity,
            "client_order_id": self.client_order_id,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": self.quantity,
            "body_sha256": self.body_sha256,
            "lifecycle_state": self.lifecycle_state,
            "recon_obligation": self.recon_obligation.value,
            "duplicate_suppressed": self.duplicate_suppressed,
            "productive_wire_reachable": self.productive_wire_reachable,
            "network_call_performed": self.network_call_performed,
            "secret_materialized": self.secret_materialized,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class OfflineExecutionBoundaryResultV1:
    permission: OfflineExecutionPermissionResultV1
    request_candidate: PositionCreationRequestCandidateV1 | None
    transport_record: RecordingTransportRecordV1 | None
    prerequisite_08_closed: bool
    real_position_created: bool
    venue_mutation_performed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission": self.permission.to_dict(),
            "request_candidate": (
                None if self.request_candidate is None else self.request_candidate.to_dict()
            ),
            "transport_record": (
                None if self.transport_record is None else self.transport_record.to_dict()
            ),
            "prerequisite_08_closed": self.prerequisite_08_closed,
            "real_position_created": self.real_position_created,
            "venue_mutation_performed": self.venue_mutation_performed,
        }
