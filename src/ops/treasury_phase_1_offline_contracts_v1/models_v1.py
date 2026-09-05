"""Typed Treasury Phase-1 models. No secrets. No productive authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple


class TreasuryOperationKindV1(str, Enum):
    DEPOSIT_OBSERVATION = "DEPOSIT_OBSERVATION"
    DEPOSIT_ADDRESS_RETRIEVAL = "DEPOSIT_ADDRESS_RETRIEVAL"
    WITHDRAWAL = "WITHDRAWAL"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"


MUTATION_OPERATION_KINDS = frozenset(
    {
        TreasuryOperationKindV1.WITHDRAWAL.value,
        TreasuryOperationKindV1.INTERNAL_TRANSFER.value,
    }
)
NON_MUTATION_OPERATION_KINDS = frozenset(
    {
        TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value,
        TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value,
    }
)


class TreasuryLifecycleStateV1(str, Enum):
    """Smallest complete Treasury lifecycle. Names are local, not venue status."""

    INTENT_RECORDED = "INTENT_RECORDED"
    REMOTE_ATTEMPT_RECORDED = "REMOTE_ATTEMPT_RECORDED"
    REMOTE_PENDING = "REMOTE_PENDING"
    REMOTE_TERMINAL_SUCCESS = "REMOTE_TERMINAL_SUCCESS"
    REMOTE_TERMINAL_FAILURE = "REMOTE_TERMINAL_FAILURE"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    ECONOMIC_EFFECT_RECONCILED = "ECONOMIC_EFFECT_RECONCILED"


class TreasuryAuthorizationClassV1(str, Enum):
    NONE = "NONE"
    OBSERVER_CONTRACT = "OBSERVER_CONTRACT"
    MUTATION_PERMIT_TYPED_OFFLINE = "MUTATION_PERMIT_TYPED_OFFLINE"


class TreasuryCapitalSemanticClassV1(str, Enum):
    OBSERVED_CAPITAL = "OBSERVED_CAPITAL"
    RECONCILED_CAPITAL = "RECONCILED_CAPITAL"
    RISK_ADMISSIBLE_CAPITAL = "RISK_ADMISSIBLE_CAPITAL"


class TreasuryCommandClassificationV1(str, Enum):
    NEW_INTENT = "NEW_INTENT"
    DUPLICATE_SAME_INTENT = "DUPLICATE_SAME_INTENT"
    SAME_INTENT_CHANGED_PARAMETERS = "SAME_INTENT_CHANGED_PARAMETERS"
    DISTINCT_INTENT_SAME_PARAMETERS = "DISTINCT_INTENT_SAME_PARAMETERS"
    UNSAFE_RETRY_UNKNOWN_OUTCOME = "UNSAFE_RETRY_UNKNOWN_OUTCOME"
    TERMINAL_EFFECT_ALREADY_APPLIED = "TERMINAL_EFFECT_ALREADY_APPLIED"
    CONFLICT_REQUIRES_SERIALIZATION = "CONFLICT_REQUIRES_SERIALIZATION"


class TreasuryDestinationRefKindV1(str, Enum):
    ACCOUNT_SCOPE = "ACCOUNT_SCOPE"
    DESTINATION_FINGERPRINT = "DESTINATION_FINGERPRINT"
    NONE = "NONE"


TERMINAL_ECONOMIC_STATES = frozenset(
    {
        TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
    }
)
UNKNOWN_OR_PENDING_STATES = frozenset(
    {
        TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        TreasuryLifecycleStateV1.REMOTE_PENDING.value,
        TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value,
        TreasuryLifecycleStateV1.RECONCILIATION_REQUIRED.value,
    }
)
BLOCKING_RETRY_STATES = frozenset(
    {
        *UNKNOWN_OR_PENDING_STATES,
        TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
        TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
    }
)


@dataclass(frozen=True)
class TreasuryDestinationRefV1:
    ref_kind: str
    fingerprint: str = ""
    scope_id: str = ""
    network_id: str = ""
    confirmation_fingerprint: str = ""


@dataclass(frozen=True)
class TreasuryIntentDraftV1:
    intent_id: str
    operation_kind: str
    asset_id: str
    amount_raw: str
    denomination: str
    source_scope: str
    destination: TreasuryDestinationRefV1
    created_at: str
    policy_version: str
    authorization_class: str
    authorization_evidence_ref: str
    evidence_refs: Tuple[str, ...] = ()
    venue_operation_ref: str = ""
    local_observation_at: str = ""
    venue_source_at: str = ""
    claimed_productive_authority: bool = False
    claimed_historical_authority: bool = False


@dataclass(frozen=True)
class TreasuryIntentRecordV1:
    schema_version: str
    intent_id: str
    operation_kind: str
    asset_id: str
    amount_canonical: str
    denomination: str
    source_scope: str
    destination_ref_kind: str
    destination_fingerprint: str
    destination_scope_id: str
    network_id: str
    confirmation_fingerprint: str
    created_at: str
    local_observation_at: str
    venue_source_at: str
    policy_version: str
    authorization_class: str
    authorization_evidence_ref: str
    request_fingerprint: str
    evidence_hash: str
    evidence_refs: Tuple[str, ...]
    venue_operation_ref: str
    lifecycle_state: str
    sequence: int
    prior_state: str
    reconciliation_status: str
    durable: bool
    remote_attempted: bool
    mutation_authorized: bool
    risk_admissible: bool
    capital_semantic_class: str
    capital_admission_authority: str


@dataclass(frozen=True)
class TreasuryLifecycleTransitionV1:
    intent_id: str
    from_state: str
    to_state: str
    local_observation_at: str
    venue_source_at: str = ""
    venue_operation_ref: str = ""
    evidence_refs: Tuple[str, ...] = ()
    reason_code: str = ""
    confirmation_fingerprint: str = ""


@dataclass(frozen=True)
class TreasuryRemoteMutationEligibilityV1:
    eligible: bool
    durable_intent_present: bool
    remote_attempt_permitted: bool
    network_send_permitted: bool
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class TreasuryCommandDecisionV1:
    classification: str
    intent_id: str
    request_fingerprint: str
    reason_codes: Tuple[str, ...]
    existing_state: str = ""


def intent_record_to_mapping(record: TreasuryIntentRecordV1) -> dict[str, Any]:
    return {
        "schema_version": record.schema_version,
        "intent_id": record.intent_id,
        "operation_kind": record.operation_kind,
        "asset_id": record.asset_id,
        "amount_canonical": record.amount_canonical,
        "denomination": record.denomination,
        "source_scope": record.source_scope,
        "destination_ref_kind": record.destination_ref_kind,
        "destination_fingerprint": record.destination_fingerprint,
        "destination_scope_id": record.destination_scope_id,
        "network_id": record.network_id,
        "confirmation_fingerprint": record.confirmation_fingerprint,
        "created_at": record.created_at,
        "local_observation_at": record.local_observation_at,
        "venue_source_at": record.venue_source_at,
        "policy_version": record.policy_version,
        "authorization_class": record.authorization_class,
        "authorization_evidence_ref": record.authorization_evidence_ref,
        "request_fingerprint": record.request_fingerprint,
        "evidence_hash": record.evidence_hash,
        "evidence_refs": list(record.evidence_refs),
        "venue_operation_ref": record.venue_operation_ref,
        "lifecycle_state": record.lifecycle_state,
        "sequence": record.sequence,
        "prior_state": record.prior_state,
        "reconciliation_status": record.reconciliation_status,
        "durable": record.durable,
        "remote_attempted": record.remote_attempted,
        "mutation_authorized": record.mutation_authorized,
        "risk_admissible": record.risk_admissible,
        "capital_semantic_class": record.capital_semantic_class,
        "capital_admission_authority": record.capital_admission_authority,
    }


def intent_record_from_mapping(payload: Mapping[str, Any]) -> TreasuryIntentRecordV1:
    refs = payload.get("evidence_refs", ())
    if isinstance(refs, list):
        evidence_refs = tuple(str(item) for item in refs)
    elif isinstance(refs, tuple):
        evidence_refs = tuple(str(item) for item in refs)
    else:
        evidence_refs = ()
    return TreasuryIntentRecordV1(
        schema_version=str(payload.get("schema_version", "")),
        intent_id=str(payload.get("intent_id", "")),
        operation_kind=str(payload.get("operation_kind", "")),
        asset_id=str(payload.get("asset_id", "")),
        amount_canonical=str(payload.get("amount_canonical", "")),
        denomination=str(payload.get("denomination", "")),
        source_scope=str(payload.get("source_scope", "")),
        destination_ref_kind=str(payload.get("destination_ref_kind", "")),
        destination_fingerprint=str(payload.get("destination_fingerprint", "")),
        destination_scope_id=str(payload.get("destination_scope_id", "")),
        network_id=str(payload.get("network_id", "")),
        confirmation_fingerprint=str(payload.get("confirmation_fingerprint", "")),
        created_at=str(payload.get("created_at", "")),
        local_observation_at=str(payload.get("local_observation_at", "")),
        venue_source_at=str(payload.get("venue_source_at", "")),
        policy_version=str(payload.get("policy_version", "")),
        authorization_class=str(payload.get("authorization_class", "")),
        authorization_evidence_ref=str(payload.get("authorization_evidence_ref", "")),
        request_fingerprint=str(payload.get("request_fingerprint", "")),
        evidence_hash=str(payload.get("evidence_hash", "")),
        evidence_refs=evidence_refs,
        venue_operation_ref=str(payload.get("venue_operation_ref", "")),
        lifecycle_state=str(payload.get("lifecycle_state", "")),
        sequence=int(payload.get("sequence", 0)),
        prior_state=str(payload.get("prior_state", "")),
        reconciliation_status=str(payload.get("reconciliation_status", "")),
        durable=bool(payload.get("durable", False)),
        remote_attempted=bool(payload.get("remote_attempted", False)),
        mutation_authorized=bool(payload.get("mutation_authorized", False)),
        risk_admissible=bool(payload.get("risk_admissible", False)),
        capital_semantic_class=str(payload.get("capital_semantic_class", "")),
        capital_admission_authority=str(payload.get("capital_admission_authority", "")),
    )
