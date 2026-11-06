"""Offline Treasury contract engine. Records intents and transitions. Sends nothing."""

from __future__ import annotations

from dataclasses import replace

from src.ops.treasury_phase_1_offline_contracts_v1.authority_v1 import (
    trading_authority_cannot_mint_treasury_authority_v1,
    treasury_authorization_cannot_mint_wire_or_live_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.capital_boundary_v1 import (
    treasury_lifecycle_cannot_mint_risk_admissible_v1,
    treasury_state_to_capital_semantic_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    SCHEMA_VERSION,
    TREASURY_MUTATION_AUTHORIZED,
    TREASURY_PHASE_1_CAN_SEND_NETWORK_REQUEST,
    VENUE_IDEMPOTENCY_GUARANTEE,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import (
    TreasuryIdempotencyError,
    TreasuryPhase1ContractError,
)
from src.ops.treasury_phase_1_offline_contracts_v1.identity_v1 import (
    assert_same_intent_same_fingerprint_v1,
    economic_parameters_equal_v1,
    request_fingerprint_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.lifecycle_v1 import (
    assert_transition_allowed_v1,
    reconciliation_status_for_state_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    BLOCKING_RETRY_STATES,
    MUTATION_OPERATION_KINDS,
    TreasuryCommandClassificationV1,
    TreasuryCommandDecisionV1,
    TreasuryIntentDraftV1,
    TreasuryIntentRecordV1,
    TreasuryLifecycleStateV1,
    TreasuryLifecycleTransitionV1,
    TreasuryRemoteMutationEligibilityV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.persistence_v1 import TreasuryIntentStoreV1
from src.ops.treasury_phase_1_offline_contracts_v1.provenance_v1 import evidence_hash_for_record_v1
from src.ops.treasury_phase_1_offline_contracts_v1.validators_v1 import validate_draft_v1


def _build_record(
    *,
    draft: TreasuryIntentDraftV1,
    sequence: int,
    lifecycle_state: str,
    prior_state: str,
    remote_attempted: bool,
) -> TreasuryIntentRecordV1:
    validated = validate_draft_v1(draft)
    fingerprint = request_fingerprint_v1(validated)
    trading_authority_cannot_mint_treasury_authority_v1()
    treasury_authorization_cannot_mint_wire_or_live_v1(validated.authorization_class)
    placeholder = TreasuryIntentRecordV1(
        schema_version=SCHEMA_VERSION,
        intent_id=validated.intent_id,
        operation_kind=validated.operation_kind,
        asset_id=validated.asset_id,
        amount_canonical=validated.amount_raw,
        denomination=validated.denomination,
        source_scope=validated.source_scope,
        destination_ref_kind=validated.destination.ref_kind,
        destination_fingerprint=validated.destination.fingerprint,
        destination_scope_id=validated.destination.scope_id,
        network_id=validated.destination.network_id,
        confirmation_fingerprint=validated.destination.confirmation_fingerprint,
        created_at=validated.created_at,
        local_observation_at=validated.local_observation_at,
        venue_source_at=validated.venue_source_at,
        policy_version=validated.policy_version,
        authorization_class=validated.authorization_class,
        authorization_evidence_ref=validated.authorization_evidence_ref,
        request_fingerprint=fingerprint,
        evidence_hash="",
        evidence_refs=validated.evidence_refs,
        venue_operation_ref=validated.venue_operation_ref,
        lifecycle_state=lifecycle_state,
        sequence=sequence,
        prior_state=prior_state,
        reconciliation_status=reconciliation_status_for_state_v1(lifecycle_state),
        durable=True,
        remote_attempted=remote_attempted,
        mutation_authorized=False,
        risk_admissible=False,
        capital_semantic_class=treasury_state_to_capital_semantic_v1(lifecycle_state),
        capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
    )
    hashed = replace(placeholder, evidence_hash=evidence_hash_for_record_v1(placeholder))
    treasury_lifecycle_cannot_mint_risk_admissible_v1(hashed)
    return hashed


def classify_treasury_command_v1(
    store: TreasuryIntentStoreV1, draft: TreasuryIntentDraftV1
) -> TreasuryCommandDecisionV1:
    validated = validate_draft_v1(draft)
    fingerprint = request_fingerprint_v1(validated)
    existing = store.get(validated.intent_id)
    if existing is None:
        concurrent = classify_concurrent_treasury_intents_v1(store, validated)
        if (
            concurrent.classification
            == TreasuryCommandClassificationV1.CONFLICT_REQUIRES_SERIALIZATION.value
        ):
            return concurrent
        return TreasuryCommandDecisionV1(
            classification=TreasuryCommandClassificationV1.NEW_INTENT.value,
            intent_id=validated.intent_id,
            request_fingerprint=fingerprint,
            reason_codes=("NEW_LOCAL_INTENT",),
        )
    if existing.lifecycle_state in BLOCKING_RETRY_STATES:
        if existing.lifecycle_state == TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value:
            return TreasuryCommandDecisionV1(
                classification=TreasuryCommandClassificationV1.UNSAFE_RETRY_UNKNOWN_OUTCOME.value,
                intent_id=validated.intent_id,
                request_fingerprint=fingerprint,
                reason_codes=("OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY",),
                existing_state=existing.lifecycle_state,
            )
        if existing.lifecycle_state == TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value:
            return TreasuryCommandDecisionV1(
                classification=TreasuryCommandClassificationV1.TERMINAL_EFFECT_ALREADY_APPLIED.value,
                intent_id=validated.intent_id,
                request_fingerprint=fingerprint,
                reason_codes=("MONOTONIC_ECONOMIC_EFFECT",),
                existing_state=existing.lifecycle_state,
            )
    try:
        assert_same_intent_same_fingerprint_v1(existing, validated)
    except TreasuryIdempotencyError as exc:
        return TreasuryCommandDecisionV1(
            classification=TreasuryCommandClassificationV1.SAME_INTENT_CHANGED_PARAMETERS.value,
            intent_id=validated.intent_id,
            request_fingerprint=fingerprint,
            reason_codes=(str(exc),),
            existing_state=existing.lifecycle_state,
        )
    return TreasuryCommandDecisionV1(
        classification=TreasuryCommandClassificationV1.DUPLICATE_SAME_INTENT.value,
        intent_id=validated.intent_id,
        request_fingerprint=fingerprint,
        reason_codes=("DETERMINISTIC_DUPLICATE",),
        existing_state=existing.lifecycle_state,
    )


def classify_distinct_same_parameters_v1(
    store: TreasuryIntentStoreV1, draft: TreasuryIntentDraftV1
) -> TreasuryCommandDecisionV1:
    validated = validate_draft_v1(draft)
    fingerprint = request_fingerprint_v1(validated)
    for existing in store.list_all():
        if existing.intent_id == validated.intent_id:
            continue
        if economic_parameters_equal_v1(existing, validated):
            return TreasuryCommandDecisionV1(
                classification=TreasuryCommandClassificationV1.DISTINCT_INTENT_SAME_PARAMETERS.value,
                intent_id=validated.intent_id,
                request_fingerprint=fingerprint,
                reason_codes=("NOT_AUTOMATICALLY_SAME_OPERATION",),
                existing_state=existing.lifecycle_state,
            )
    return TreasuryCommandDecisionV1(
        classification=TreasuryCommandClassificationV1.NEW_INTENT.value,
        intent_id=validated.intent_id,
        request_fingerprint=fingerprint,
        reason_codes=("NEW_LOCAL_INTENT",),
    )


def classify_concurrent_treasury_intents_v1(
    store: TreasuryIntentStoreV1, draft: TreasuryIntentDraftV1
) -> TreasuryCommandDecisionV1:
    validated = validate_draft_v1(draft)
    fingerprint = request_fingerprint_v1(validated)
    if validated.operation_kind not in MUTATION_OPERATION_KINDS:
        return TreasuryCommandDecisionV1(
            classification=TreasuryCommandClassificationV1.NEW_INTENT.value,
            intent_id=validated.intent_id,
            request_fingerprint=fingerprint,
            reason_codes=("NON_MUTATION_CONCURRENCY_ALLOWED",),
        )
    for existing in store.list_all():
        if existing.intent_id == validated.intent_id:
            continue
        if existing.operation_kind not in MUTATION_OPERATION_KINDS:
            continue
        if existing.source_scope != validated.source_scope:
            continue
        if existing.lifecycle_state == TreasuryLifecycleStateV1.REMOTE_TERMINAL_FAILURE.value:
            continue
        if existing.lifecycle_state == TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value:
            continue
        return TreasuryCommandDecisionV1(
            classification=TreasuryCommandClassificationV1.CONFLICT_REQUIRES_SERIALIZATION.value,
            intent_id=validated.intent_id,
            request_fingerprint=fingerprint,
            reason_codes=("CONCURRENT_MUTATION_INTENTS_REQUIRE_SERIALIZATION",),
            existing_state=existing.lifecycle_state,
        )
    return TreasuryCommandDecisionV1(
        classification=TreasuryCommandClassificationV1.NEW_INTENT.value,
        intent_id=validated.intent_id,
        request_fingerprint=fingerprint,
        reason_codes=("NO_CONCURRENT_MUTATION_CONFLICT",),
    )


def record_treasury_intent_v1(
    store: TreasuryIntentStoreV1, draft: TreasuryIntentDraftV1
) -> TreasuryIntentRecordV1:
    decision = classify_treasury_command_v1(store, draft)
    if decision.classification == TreasuryCommandClassificationV1.DUPLICATE_SAME_INTENT.value:
        existing = store.get(draft.intent_id)
        if existing is None:
            raise TreasuryPhase1ContractError("DUPLICATE_WITHOUT_EXISTING")
        return existing
    if (
        decision.classification
        == TreasuryCommandClassificationV1.SAME_INTENT_CHANGED_PARAMETERS.value
    ):
        raise TreasuryIdempotencyError("SAME_INTENT_CHANGED_ECONOMIC_PARAMETERS")
    if (
        decision.classification
        == TreasuryCommandClassificationV1.UNSAFE_RETRY_UNKNOWN_OUTCOME.value
    ):
        raise TreasuryIdempotencyError("OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY")
    if (
        decision.classification
        == TreasuryCommandClassificationV1.TERMINAL_EFFECT_ALREADY_APPLIED.value
    ):
        raise TreasuryIdempotencyError("TERMINAL_EFFECT_ALREADY_APPLIED")
    if (
        decision.classification
        == TreasuryCommandClassificationV1.CONFLICT_REQUIRES_SERIALIZATION.value
    ):
        raise TreasuryPhase1ContractError("CONCURRENT_MUTATION_INTENTS_REQUIRE_SERIALIZATION")
    record = _build_record(
        draft=draft,
        sequence=store.next_sequence(),
        lifecycle_state=TreasuryLifecycleStateV1.INTENT_RECORDED.value,
        prior_state="",
        remote_attempted=False,
    )
    store.put(record)
    return record


def evaluate_remote_mutation_eligibility_v1(
    record: TreasuryIntentRecordV1,
) -> TreasuryRemoteMutationEligibilityV1:
    reasons: list[str] = []
    durable = record.durable is True and record.lifecycle_state in {
        TreasuryLifecycleStateV1.INTENT_RECORDED.value,
        TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value,
        TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        TreasuryLifecycleStateV1.REMOTE_PENDING.value,
        TreasuryLifecycleStateV1.RECONCILIATION_REQUIRED.value,
        TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
        TreasuryLifecycleStateV1.REMOTE_TERMINAL_FAILURE.value,
        TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
    }
    if record.durable is not True:
        reasons.append("DURABLE_INTENT_MISSING")
    if record.operation_kind not in MUTATION_OPERATION_KINDS:
        reasons.append("NON_MUTATION_OPERATION")
    if TREASURY_MUTATION_AUTHORIZED is True:
        raise TreasuryPhase1ContractError("PHASE_1_MUTATION_AUTHORIZED_DRIFT")
    reasons.append("PHASE_1_NETWORK_SEND_FORBIDDEN")
    if VENUE_IDEMPOTENCY_GUARANTEE != "NOT_PROVEN":
        raise TreasuryPhase1ContractError("VENUE_IDEMPOTENCY_MUST_REMAIN_NOT_PROVEN")
    if TREASURY_PHASE_1_CAN_SEND_NETWORK_REQUEST is True:
        raise TreasuryPhase1ContractError("PHASE_1_NETWORK_FLAG_DRIFT")
    if record.lifecycle_state == TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value:
        reasons.append("OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY")
    if record.lifecycle_state == TreasuryLifecycleStateV1.INTENT_RECORDED.value and durable:
        reasons.append("DURABLE_INTENT_PRESENT_BUT_PHASE_1_CANNOT_SEND")
    return TreasuryRemoteMutationEligibilityV1(
        eligible=False,
        durable_intent_present=record.durable is True,
        remote_attempt_permitted=False,
        network_send_permitted=False,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def apply_treasury_lifecycle_transition_v1(
    store: TreasuryIntentStoreV1,
    transition: TreasuryLifecycleTransitionV1,
) -> TreasuryIntentRecordV1:
    existing = store.get(transition.intent_id)
    if existing is None:
        raise TreasuryPhase1ContractError("INTENT_NOT_RECORDED")
    assert_transition_allowed_v1(record=existing, transition=transition)
    eligibility = evaluate_remote_mutation_eligibility_v1(existing)
    if transition.to_state == TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value:
        if existing.durable is not True:
            raise TreasuryPhase1ContractError("DURABLE_INTENT_REQUIRED_BEFORE_REMOTE")
        if eligibility.network_send_permitted is True:
            raise TreasuryPhase1ContractError("PHASE_1_NETWORK_SEND_FORBIDDEN")
    remote_attempted = existing.remote_attempted or (
        transition.to_state
        in {
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_PENDING.value,
            TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_FAILURE.value,
        }
    )
    updated = replace(
        existing,
        lifecycle_state=transition.to_state,
        prior_state=existing.lifecycle_state,
        sequence=store.next_sequence(),
        local_observation_at=transition.local_observation_at,
        venue_source_at=transition.venue_source_at or existing.venue_source_at,
        venue_operation_ref=transition.venue_operation_ref or existing.venue_operation_ref,
        evidence_refs=existing.evidence_refs + transition.evidence_refs,
        confirmation_fingerprint=(
            transition.confirmation_fingerprint or existing.confirmation_fingerprint
        ),
        reconciliation_status=reconciliation_status_for_state_v1(transition.to_state),
        remote_attempted=remote_attempted,
        capital_semantic_class=treasury_state_to_capital_semantic_v1(transition.to_state),
        mutation_authorized=False,
        risk_admissible=False,
        evidence_hash="",
    )
    hashed = replace(updated, evidence_hash=evidence_hash_for_record_v1(updated))
    treasury_lifecycle_cannot_mint_risk_admissible_v1(hashed)
    store.put(hashed)
    return hashed


def restore_treasury_records_v1(
    store: TreasuryIntentStoreV1,
) -> tuple[TreasuryIntentRecordV1, ...]:
    restored = store.list_all()
    for record in restored:
        if record.durable is not True:
            raise TreasuryPhase1ContractError("RESTART_LOST_DURABLE_INTENT")
        treasury_lifecycle_cannot_mint_risk_admissible_v1(record)
    return restored
