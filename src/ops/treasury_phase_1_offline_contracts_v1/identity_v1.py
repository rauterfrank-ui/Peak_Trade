"""Local Treasury intent identity and economic fingerprint. Not a venue ID."""

from __future__ import annotations

from decimal import Decimal

from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryIdempotencyError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    TreasuryIntentDraftV1,
    TreasuryIntentRecordV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.provenance_v1 import evidence_hash_v1
from src.ops.treasury_phase_1_offline_contracts_v1.validators_v1 import validate_draft_v1


def economic_fingerprint_material_v1(draft: TreasuryIntentDraftV1) -> dict[str, str]:
    return {
        "operation_kind": draft.operation_kind,
        "asset_id": draft.asset_id,
        "amount_canonical": draft.amount_raw,
        "denomination": draft.denomination,
        "source_scope": draft.source_scope,
        "destination_ref_kind": draft.destination.ref_kind,
        "destination_fingerprint": draft.destination.fingerprint,
        "destination_scope_id": draft.destination.scope_id,
        "network_id": draft.destination.network_id,
        "policy_version": draft.policy_version,
    }


def request_fingerprint_v1(draft: TreasuryIntentDraftV1) -> str:
    validated = validate_draft_v1(draft)
    return evidence_hash_v1(economic_fingerprint_material_v1(validated))


def economic_parameters_equal_v1(
    existing: TreasuryIntentRecordV1, draft: TreasuryIntentDraftV1
) -> bool:
    validated = validate_draft_v1(draft)
    amount_equal = True
    if existing.amount_canonical == "" and validated.amount_raw == "":
        amount_equal = True
    elif existing.amount_canonical == "" or validated.amount_raw == "":
        amount_equal = False
    else:
        amount_equal = Decimal(existing.amount_canonical) == Decimal(validated.amount_raw)
    return (
        existing.operation_kind == validated.operation_kind
        and existing.asset_id == validated.asset_id
        and amount_equal
        and existing.denomination == validated.denomination
        and existing.source_scope == validated.source_scope
        and existing.destination_ref_kind == validated.destination.ref_kind
        and existing.destination_fingerprint == validated.destination.fingerprint
        and existing.destination_scope_id == validated.destination.scope_id
        and existing.network_id == validated.destination.network_id
    )


def assert_same_intent_same_fingerprint_v1(
    existing: TreasuryIntentRecordV1, draft: TreasuryIntentDraftV1
) -> None:
    validated = validate_draft_v1(draft)
    incoming = request_fingerprint_v1(validated)
    if existing.intent_id != validated.intent_id:
        return
    if not economic_parameters_equal_v1(existing, validated):
        raise TreasuryIdempotencyError("SAME_INTENT_CHANGED_ECONOMIC_PARAMETERS")
    if existing.request_fingerprint != incoming:
        raise TreasuryIdempotencyError("SAME_INTENT_FINGERPRINT_CONTRADICTION")
