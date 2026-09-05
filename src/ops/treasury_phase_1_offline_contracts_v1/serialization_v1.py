"""Deterministic versioned serialization for Treasury Phase-1 records."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CANONICAL_SERIALIZATION_VERSION,
    SCHEMA_VERSION,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import (
    TreasuryPhase1ContractError,
    TreasuryPersistenceError,
    TreasurySecretHygieneError,
)
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    TreasuryIntentRecordV1,
    intent_record_from_mapping,
    intent_record_to_mapping,
)
from src.ops.treasury_phase_1_offline_contracts_v1.provenance_v1 import (
    assert_no_secret_fields_v1,
    evidence_hash_for_record_v1,
)

KNOWN_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "intent_id",
        "operation_kind",
        "asset_id",
        "amount_canonical",
        "denomination",
        "source_scope",
        "destination_ref_kind",
        "destination_fingerprint",
        "destination_scope_id",
        "network_id",
        "confirmation_fingerprint",
        "created_at",
        "local_observation_at",
        "venue_source_at",
        "policy_version",
        "authorization_class",
        "authorization_evidence_ref",
        "request_fingerprint",
        "evidence_hash",
        "evidence_refs",
        "venue_operation_ref",
        "lifecycle_state",
        "sequence",
        "prior_state",
        "reconciliation_status",
        "durable",
        "remote_attempted",
        "mutation_authorized",
        "risk_admissible",
        "capital_semantic_class",
        "capital_admission_authority",
    }
)


def canonical_dumps_v1(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_amount_text_v1(raw: str) -> str:
    text = str(raw)
    if text != raw:
        raise TreasuryPhase1ContractError("AMOUNT_NOT_CANONICAL_TEXT")
    if text != text.strip() or text == "":
        raise TreasuryPhase1ContractError("AMOUNT_WHITESPACE_OR_EMPTY")
    if any(ch in text for ch in ("+", " ", "\t", "\n", "\r")):
        raise TreasuryPhase1ContractError("AMOUNT_MALFORMED")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise TreasuryPhase1ContractError("AMOUNT_NOT_DECIMAL") from exc
    if not value.is_finite():
        raise TreasuryPhase1ContractError("AMOUNT_NOT_FINITE")
    canonical = format(value, "f")
    if canonical != text:
        raise TreasuryPhase1ContractError("AMOUNT_NOT_CANONICAL_FORM")
    return canonical


def serialize_intent_record_v1(record: TreasuryIntentRecordV1) -> str:
    payload = intent_record_to_mapping(record)
    assert_no_secret_fields_v1(payload)
    if record.schema_version != SCHEMA_VERSION:
        raise TreasuryPersistenceError("UNSUPPORTED_SCHEMA_VERSION")
    if record.mutation_authorized is True:
        raise TreasuryPhase1ContractError("PRODUCTIVE_AUTHORITY_CLAIM_DENIED")
    if record.risk_admissible is True:
        raise TreasuryPhase1ContractError("RISK_ADMISSIBLE_CLAIM_DENIED")
    encoded = canonical_dumps_v1(payload)
    digest = evidence_hash_for_record_v1(record)
    if digest != record.evidence_hash:
        raise TreasuryPhase1ContractError("EVIDENCE_HASH_MISMATCH")
    _ = CANONICAL_SERIALIZATION_VERSION
    return encoded


def deserialize_intent_record_v1(text: str) -> TreasuryIntentRecordV1:
    if not isinstance(text, str) or text == "":
        raise TreasuryPersistenceError("EMPTY_SERIALIZED_RECORD")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TreasuryPersistenceError("CORRUPTED_SERIALIZED_RECORD") from exc
    if not isinstance(payload, dict):
        raise TreasuryPersistenceError("SERIALIZED_RECORD_NOT_OBJECT")
    unknown = set(payload.keys()) - KNOWN_RECORD_FIELDS
    if unknown:
        raise TreasuryPersistenceError("UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))
    assert_no_secret_fields_v1(payload)
    schema = str(payload.get("schema_version", ""))
    if schema != SCHEMA_VERSION:
        raise TreasuryPersistenceError("UNSUPPORTED_SCHEMA_VERSION")
    record = intent_record_from_mapping(payload)
    if record.mutation_authorized is True or record.risk_admissible is True:
        raise TreasuryPhase1ContractError("PRODUCTIVE_AUTHORITY_CLAIM_DENIED")
    expected = evidence_hash_for_record_v1(record)
    if expected != record.evidence_hash:
        raise TreasuryPersistenceError("EVIDENCE_HASH_MISMATCH")
    return record


def round_trip_intent_record_v1(record: TreasuryIntentRecordV1) -> TreasuryIntentRecordV1:
    return deserialize_intent_record_v1(serialize_intent_record_v1(record))
