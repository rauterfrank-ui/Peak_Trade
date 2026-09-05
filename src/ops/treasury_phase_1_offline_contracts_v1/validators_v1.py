"""Typed validators for Treasury Phase-1 offline contracts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal

from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    INTENT_ID_PATTERN,
    MAX_ASSET_LEN,
    MAX_REF_LEN,
    SCHEMA_VERSION,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryPhase1ContractError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    MUTATION_OPERATION_KINDS,
    NON_MUTATION_OPERATION_KINDS,
    TreasuryAuthorizationClassV1,
    TreasuryDestinationRefKindV1,
    TreasuryDestinationRefV1,
    TreasuryIntentDraftV1,
    TreasuryLifecycleStateV1,
    TreasuryOperationKindV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.serialization_v1 import canonical_amount_text_v1


def validate_intent_id_v1(intent_id: str) -> str:
    text = str(intent_id)
    if text != intent_id or text != text.strip():
        raise TreasuryPhase1ContractError("INTENT_ID_WHITESPACE")
    if re.fullmatch(INTENT_ID_PATTERN, text) is None:
        raise TreasuryPhase1ContractError("INTENT_ID_MALFORMED")
    return text


def validate_enum_member_v1(*, value: str, allowed: set[str], reason: str) -> str:
    text = str(value)
    if text != value or text not in allowed:
        raise TreasuryPhase1ContractError(reason)
    return text


def validate_operation_kind_v1(kind: str) -> str:
    allowed = {item.value for item in TreasuryOperationKindV1}
    return validate_enum_member_v1(value=kind, allowed=allowed, reason="OPERATION_KIND_UNKNOWN")


def validate_lifecycle_state_v1(state: str) -> str:
    allowed = {item.value for item in TreasuryLifecycleStateV1}
    return validate_enum_member_v1(value=state, allowed=allowed, reason="LIFECYCLE_STATE_UNKNOWN")


def validate_authorization_class_v1(value: str) -> str:
    allowed = {item.value for item in TreasuryAuthorizationClassV1}
    return validate_enum_member_v1(
        value=value, allowed=allowed, reason="AUTHORIZATION_CLASS_UNKNOWN"
    )


def validate_ref_v1(value: str, *, field: str, allow_empty: bool = False) -> str:
    text = str(value)
    if text != value:
        raise TreasuryPhase1ContractError(f"{field}_NOT_TEXT")
    if text != text.strip():
        raise TreasuryPhase1ContractError(f"{field}_WHITESPACE")
    if text == "":
        if allow_empty:
            return text
        raise TreasuryPhase1ContractError(f"{field}_EMPTY")
    if len(text) > MAX_REF_LEN:
        raise TreasuryPhase1ContractError(f"{field}_TOO_LONG")
    return text


def validate_asset_id_v1(asset_id: str) -> str:
    text = validate_ref_v1(asset_id, field="ASSET_ID")
    if len(text) > MAX_ASSET_LEN:
        raise TreasuryPhase1ContractError("ASSET_ID_TOO_LONG")
    return text


def validate_timezone_aware_timestamp_v1(raw: str, *, field: str, allow_empty: bool = False) -> str:
    text = str(raw)
    if text != raw:
        raise TreasuryPhase1ContractError(f"{field}_NOT_TEXT")
    if text == "":
        if allow_empty:
            return text
        raise TreasuryPhase1ContractError(f"{field}_EMPTY")
    if text.endswith("Z"):
        parseable = text[:-1] + "+00:00"
    else:
        parseable = text
    try:
        parsed = datetime.fromisoformat(parseable)
    except ValueError as exc:
        raise TreasuryPhase1ContractError(f"{field}_TIMESTAMP_MALFORMED") from exc
    if parsed.tzinfo is None:
        raise TreasuryPhase1ContractError(f"{field}_TIMESTAMP_NAIVE")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise TreasuryPhase1ContractError(f"{field}_TIMESTAMP_NOT_UTC")
    if not text.endswith("Z"):
        raise TreasuryPhase1ContractError(f"{field}_TIMESTAMP_NOT_ZULU")
    return text


def validate_amount_for_operation_v1(*, amount_raw: str, operation_kind: str) -> str:
    kind = validate_operation_kind_v1(kind=operation_kind)
    if kind == TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value:
        if str(amount_raw) == "":
            return ""
        raise TreasuryPhase1ContractError("DEPOSIT_ADDRESS_RETRIEVAL_AMOUNT_NOT_ALLOWED")
    if kind == TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value and str(amount_raw) == "":
        return ""
    canonical = canonical_amount_text_v1(amount_raw)
    value = Decimal(canonical)
    if kind in MUTATION_OPERATION_KINDS:
        if value <= 0:
            raise TreasuryPhase1ContractError("MUTATION_AMOUNT_NOT_POSITIVE")
    elif kind == TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value:
        if value < 0:
            raise TreasuryPhase1ContractError("OBSERVATION_AMOUNT_NEGATIVE")
        if not value.is_finite():
            raise TreasuryPhase1ContractError("AMOUNT_NOT_FINITE")
    return canonical


def validate_destination_v1(
    destination: TreasuryDestinationRefV1, *, operation_kind: str
) -> TreasuryDestinationRefV1:
    kind = validate_operation_kind_v1(kind=operation_kind)
    ref_kind = validate_enum_member_v1(
        value=destination.ref_kind,
        allowed={item.value for item in TreasuryDestinationRefKindV1},
        reason="DESTINATION_REF_KIND_UNKNOWN",
    )
    fingerprint = validate_ref_v1(
        destination.fingerprint, field="DESTINATION_FINGERPRINT", allow_empty=True
    )
    scope_id = validate_ref_v1(destination.scope_id, field="DESTINATION_SCOPE", allow_empty=True)
    network_id = validate_ref_v1(destination.network_id, field="NETWORK_ID", allow_empty=True)
    confirmation = validate_ref_v1(
        destination.confirmation_fingerprint, field="CONFIRMATION_FINGERPRINT", allow_empty=True
    )
    if kind == TreasuryOperationKindV1.WITHDRAWAL.value:
        if ref_kind != TreasuryDestinationRefKindV1.DESTINATION_FINGERPRINT.value:
            raise TreasuryPhase1ContractError("WITHDRAWAL_DESTINATION_FINGERPRINT_REQUIRED")
        if fingerprint == "":
            raise TreasuryPhase1ContractError("WITHDRAWAL_DESTINATION_FINGERPRINT_EMPTY")
        if network_id == "":
            raise TreasuryPhase1ContractError("WITHDRAWAL_NETWORK_REQUIRED")
        if confirmation != "" and confirmation != fingerprint:
            raise TreasuryPhase1ContractError("DESTINATION_CONFIRMATION_MISMATCH")
    if kind == TreasuryOperationKindV1.INTERNAL_TRANSFER.value:
        if ref_kind != TreasuryDestinationRefKindV1.ACCOUNT_SCOPE.value:
            raise TreasuryPhase1ContractError("TRANSFER_DESTINATION_SCOPE_REQUIRED")
        if scope_id == "":
            raise TreasuryPhase1ContractError("TRANSFER_DESTINATION_SCOPE_EMPTY")
    if kind == TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value:
        if network_id == "":
            raise TreasuryPhase1ContractError("DEPOSIT_ADDRESS_NETWORK_REQUIRED")
    if kind == TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value:
        if ref_kind not in {
            TreasuryDestinationRefKindV1.NONE.value,
            TreasuryDestinationRefKindV1.ACCOUNT_SCOPE.value,
        }:
            raise TreasuryPhase1ContractError("DEPOSIT_OBSERVATION_DESTINATION_KIND_INVALID")
    return TreasuryDestinationRefV1(
        ref_kind=ref_kind,
        fingerprint=fingerprint,
        scope_id=scope_id,
        network_id=network_id,
        confirmation_fingerprint=confirmation,
    )


def validate_asset_network_binding_v1(
    *, asset_id: str, network_id: str, operation_kind: str
) -> None:
    kind = validate_operation_kind_v1(kind=operation_kind)
    asset = validate_asset_id_v1(asset_id)
    network = validate_ref_v1(network_id, field="NETWORK_ID", allow_empty=True)
    if kind in {
        TreasuryOperationKindV1.WITHDRAWAL.value,
        TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value,
    }:
        if network == "":
            raise TreasuryPhase1ContractError("ASSET_NETWORK_BINDING_REQUIRED")
        _ = asset
    if kind == TreasuryOperationKindV1.INTERNAL_TRANSFER.value and network != "":
        raise TreasuryPhase1ContractError("INTERNAL_TRANSFER_NETWORK_NOT_APPLICABLE")


def validate_draft_v1(draft: TreasuryIntentDraftV1) -> TreasuryIntentDraftV1:
    intent_id = validate_intent_id_v1(draft.intent_id)
    kind = validate_operation_kind_v1(draft.operation_kind)
    if kind not in MUTATION_OPERATION_KINDS | NON_MUTATION_OPERATION_KINDS:
        raise TreasuryPhase1ContractError("OPERATION_KIND_UNKNOWN")
    asset_id = validate_asset_id_v1(draft.asset_id)
    amount = validate_amount_for_operation_v1(amount_raw=draft.amount_raw, operation_kind=kind)
    denomination = validate_ref_v1(draft.denomination, field="DENOMINATION")
    source_scope = validate_ref_v1(draft.source_scope, field="SOURCE_SCOPE")
    destination = validate_destination_v1(draft.destination, operation_kind=kind)
    validate_asset_network_binding_v1(
        asset_id=asset_id, network_id=destination.network_id, operation_kind=kind
    )
    created_at = validate_timezone_aware_timestamp_v1(draft.created_at, field="CREATED_AT")
    local_obs = validate_timezone_aware_timestamp_v1(
        draft.local_observation_at or created_at,
        field="LOCAL_OBSERVATION_AT",
    )
    venue_at = validate_timezone_aware_timestamp_v1(
        draft.venue_source_at, field="VENUE_SOURCE_AT", allow_empty=True
    )
    policy_version = validate_ref_v1(draft.policy_version, field="POLICY_VERSION")
    auth_class = validate_authorization_class_v1(draft.authorization_class)
    auth_ref = validate_ref_v1(
        draft.authorization_evidence_ref,
        field="AUTHORIZATION_EVIDENCE_REF",
        allow_empty=auth_class == TreasuryAuthorizationClassV1.NONE.value,
    )
    if draft.claimed_productive_authority is True:
        raise TreasuryPhase1ContractError("FIXTURE_PRODUCTIVE_AUTHORITY_DENIED")
    if draft.claimed_historical_authority is True:
        raise TreasuryPhase1ContractError("HISTORICAL_EVIDENCE_CURRENT_AUTHORITY_DENIED")
    venue_ref = validate_ref_v1(
        draft.venue_operation_ref, field="VENUE_OPERATION_REF", allow_empty=True
    )
    if venue_ref == intent_id:
        raise TreasuryPhase1ContractError("VENUE_OPERATION_ID_COLLIDES_WITH_LOCAL_INTENT")
    evidence_refs = tuple(
        validate_ref_v1(item, field="EVIDENCE_REF") for item in draft.evidence_refs
    )
    _ = SCHEMA_VERSION
    return TreasuryIntentDraftV1(
        intent_id=intent_id,
        operation_kind=kind,
        asset_id=asset_id,
        amount_raw=amount,
        denomination=denomination,
        source_scope=source_scope,
        destination=destination,
        created_at=created_at,
        policy_version=policy_version,
        authorization_class=auth_class,
        authorization_evidence_ref=auth_ref,
        evidence_refs=evidence_refs,
        venue_operation_ref=venue_ref,
        local_observation_at=local_obs,
        venue_source_at=venue_at,
        claimed_productive_authority=False,
        claimed_historical_authority=False,
    )
