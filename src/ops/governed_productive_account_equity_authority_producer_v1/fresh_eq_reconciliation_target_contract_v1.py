"""Fresh venue `eq` reconciliation-target contract.

`eq` is a typed target observation only. It is never source authority.
Reconstructed EQUITY_STOCK and venue `eq` keep separate provenance.
Mismatch, unknown, or unspecified tolerance cannot mint a valid sample
and cannot overwrite either fact. No venue GET. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    DIMENSION_EQUITY_STOCK,
    EQ_RECONCILIATION_TARGET_ONLY,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
)

SCHEMA_CLASS = "FRESH_EQ_RECONCILIATION_TARGET_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
VENUE_FIELD_NAME = "eq"
OBSERVATION_SEMANTIC_CLASS = "FRESH_EQ_RECONCILIATION_TARGET_OBSERVATION"
RECONSTRUCTED_FACT_CLASS = "RECONSTRUCTED_EQUITY_STOCK_FACT"
VENUE_EQ_FACT_CLASS = "VENUE_EQ_TARGET_OBSERVATION_FACT"
TOLERANCE_POLICY_EXACT = "EXACT_DECIMAL_EQUALITY"
TOLERANCE_POLICY_UNSPECIFIED = "UNSPECIFIED_FAIL_CLOSED"
STATUS_MATCH = "MATCH"
STATUS_MISMATCH = "MISMATCH"
STATUS_UNKNOWN = "UNKNOWN"
REQUIRED_FIELDS: Tuple[str, ...] = (
    "reconciliation_record_id",
    "target_dimension_id",
    "venue_field_name",
    "reconstructed_equity_fact_id",
    "reconstructed_equity_provenance_digest",
    "reconstructed_equity_value_state",
    "venue_eq_fact_id",
    "venue_eq_provenance_digest",
    "venue_eq_value_state",
    "tolerance_policy",
    "reconciliation_status",
    "governed_sample_valid",
    "raw_eq_source_authority",
    "eq_reconciliation_target_only",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
_TRUE = "true"
_FALSE = "false"


class FreshEqReconciliationTargetContractError(ValueError):
    """Fail-closed fresh-eq reconciliation-target contract violation."""


@dataclass(frozen=True)
class FreshEqReconciliationTargetContractV1:
    reconciliation_record_id: str
    target_dimension_id: str
    venue_field_name: str
    reconstructed_equity_fact_id: str
    reconstructed_equity_provenance_digest: str
    reconstructed_equity_value_state: str
    reconstructed_equity_value: str
    venue_eq_fact_id: str
    venue_eq_provenance_digest: str
    venue_eq_value_state: str
    venue_eq_value: str
    tolerance_policy: str
    reconciliation_status: str
    governed_sample_valid: str
    reconstructed_fact_retained: str
    venue_eq_fact_retained: str
    eq_promoted_to_source: str
    reconstructed_stock_overwritten: str
    raw_eq_source_authority: str
    eq_reconciliation_target_only: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise FreshEqReconciliationTargetContractError(f"EQ_TARGET_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise FreshEqReconciliationTargetContractError(f"EQ_TARGET_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise FreshEqReconciliationTargetContractError(f"EQ_TARGET_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_eq_reconciliation_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _parse_decimal(raw: str) -> Decimal | None:
    if raw in {"UNKNOWN", "ABSENT", "MALFORMED"}:
        return None
    if _SCIENTIFIC_NOTATION.match(raw):
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite():
        return None
    return value


def evaluate_fresh_eq_reconciliation_v1(
    *,
    reconstructed_equity_value_state: str,
    reconstructed_equity_value: str,
    venue_eq_value_state: str,
    venue_eq_value: str,
    tolerance_policy: str,
) -> str:
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise FreshEqReconciliationTargetContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise FreshEqReconciliationTargetContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if tolerance_policy == TOLERANCE_POLICY_UNSPECIFIED:
        raise FreshEqReconciliationTargetContractError("EQ_TOLERANCE_UNSPECIFIED_FAIL_CLOSED")
    if tolerance_policy != TOLERANCE_POLICY_EXACT:
        raise FreshEqReconciliationTargetContractError("EQ_TOLERANCE_POLICY_NOT_RATIFIED")
    if reconstructed_equity_value_state != "PRESENT" or venue_eq_value_state != "PRESENT":
        return STATUS_UNKNOWN
    reconstructed = _parse_decimal(reconstructed_equity_value)
    venue_eq = _parse_decimal(venue_eq_value)
    if reconstructed is None or venue_eq is None:
        return STATUS_UNKNOWN
    if reconstructed != venue_eq:
        return STATUS_MISMATCH
    return STATUS_MATCH


def build_fresh_eq_reconciliation_target_contract_v1(
    *,
    reconciliation_record_id: str,
    reconstructed_equity_fact_id: str,
    reconstructed_equity_provenance_digest: str,
    reconstructed_equity_value_state: str,
    reconstructed_equity_value: str,
    venue_eq_fact_id: str,
    venue_eq_provenance_digest: str,
    venue_eq_value_state: str,
    venue_eq_value: str,
    tolerance_policy: str = TOLERANCE_POLICY_EXACT,
) -> FreshEqReconciliationTargetContractV1:
    payload = {
        "reconciliation_record_id": _require_non_empty_str(
            field="reconciliation_record_id", raw=reconciliation_record_id
        ),
        "target_dimension_id": DIMENSION_EQUITY_STOCK,
        "venue_field_name": VENUE_FIELD_NAME,
        "reconstructed_equity_fact_id": _require_non_empty_str(
            field="reconstructed_equity_fact_id", raw=reconstructed_equity_fact_id
        ),
        "reconstructed_equity_provenance_digest": _require_non_empty_str(
            field="reconstructed_equity_provenance_digest",
            raw=reconstructed_equity_provenance_digest,
        ),
        "reconstructed_equity_value_state": _require_non_empty_str(
            field="reconstructed_equity_value_state", raw=reconstructed_equity_value_state
        ),
        "reconstructed_equity_value": _require_non_empty_str(
            field="reconstructed_equity_value", raw=reconstructed_equity_value
        ),
        "venue_eq_fact_id": _require_non_empty_str(field="venue_eq_fact_id", raw=venue_eq_fact_id),
        "venue_eq_provenance_digest": _require_non_empty_str(
            field="venue_eq_provenance_digest", raw=venue_eq_provenance_digest
        ),
        "venue_eq_value_state": _require_non_empty_str(
            field="venue_eq_value_state", raw=venue_eq_value_state
        ),
        "venue_eq_value": _require_non_empty_str(field="venue_eq_value", raw=venue_eq_value),
        "tolerance_policy": _require_non_empty_str(field="tolerance_policy", raw=tolerance_policy),
    }
    if payload["reconstructed_equity_fact_id"] == payload["venue_eq_fact_id"]:
        raise FreshEqReconciliationTargetContractError("EQ_FACT_IDS_NOT_DISTINCT")
    if payload["reconstructed_equity_provenance_digest"] == payload["venue_eq_provenance_digest"]:
        raise FreshEqReconciliationTargetContractError("EQ_PROVENANCE_DIGESTS_NOT_DISTINCT")
    if not _SHA256_HEX.match(payload["reconstructed_equity_provenance_digest"]):
        raise FreshEqReconciliationTargetContractError("RECONSTRUCTED_PROVENANCE_DIGEST_NOT_SHA256")
    if not _SHA256_HEX.match(payload["venue_eq_provenance_digest"]):
        raise FreshEqReconciliationTargetContractError("VENUE_EQ_PROVENANCE_DIGEST_NOT_SHA256")
    status = evaluate_fresh_eq_reconciliation_v1(
        reconstructed_equity_value_state=payload["reconstructed_equity_value_state"],
        reconstructed_equity_value=payload["reconstructed_equity_value"],
        venue_eq_value_state=payload["venue_eq_value_state"],
        venue_eq_value=payload["venue_eq_value"],
        tolerance_policy=payload["tolerance_policy"],
    )
    if status in {STATUS_MISMATCH, STATUS_UNKNOWN}:
        sample_valid = _FALSE
    elif RECONSTRUCTION_ENGINE_CREATED is not False or SOURCE_SELECTED is not False:
        raise FreshEqReconciliationTargetContractError("RECONSTRUCTION_OR_SOURCE_NOT_FALSE")
    else:
        sample_valid = _FALSE
    if status == STATUS_MISMATCH and sample_valid == _TRUE:
        raise FreshEqReconciliationTargetContractError("MISMATCH_CANNOT_PRODUCE_VALID_SAMPLE")
    payload["reconciliation_status"] = status
    payload["governed_sample_valid"] = sample_valid
    payload["reconstructed_fact_retained"] = _TRUE
    payload["venue_eq_fact_retained"] = _TRUE
    payload["eq_promoted_to_source"] = _FALSE
    payload["reconstructed_stock_overwritten"] = _FALSE
    payload["raw_eq_source_authority"] = _FALSE
    payload["eq_reconciliation_target_only"] = _TRUE
    payload["reconstructed_fact_class"] = RECONSTRUCTED_FACT_CLASS
    payload["venue_eq_fact_class"] = VENUE_EQ_FACT_CLASS
    payload["observation_semantic_class"] = OBSERVATION_SEMANTIC_CLASS
    payload["authority_effect"] = AUTHORITY_EFFECT
    digest = compute_eq_reconciliation_digest_v1(payload)
    return FreshEqReconciliationTargetContractV1(
        reconciliation_record_id=payload["reconciliation_record_id"],
        target_dimension_id=payload["target_dimension_id"],
        venue_field_name=payload["venue_field_name"],
        reconstructed_equity_fact_id=payload["reconstructed_equity_fact_id"],
        reconstructed_equity_provenance_digest=payload["reconstructed_equity_provenance_digest"],
        reconstructed_equity_value_state=payload["reconstructed_equity_value_state"],
        reconstructed_equity_value=payload["reconstructed_equity_value"],
        venue_eq_fact_id=payload["venue_eq_fact_id"],
        venue_eq_provenance_digest=payload["venue_eq_provenance_digest"],
        venue_eq_value_state=payload["venue_eq_value_state"],
        venue_eq_value=payload["venue_eq_value"],
        tolerance_policy=payload["tolerance_policy"],
        reconciliation_status=payload["reconciliation_status"],
        governed_sample_valid=sample_valid,
        reconstructed_fact_retained=_TRUE,
        venue_eq_fact_retained=_TRUE,
        eq_promoted_to_source=_FALSE,
        reconstructed_stock_overwritten=_FALSE,
        raw_eq_source_authority=_FALSE,
        eq_reconciliation_target_only=_TRUE,
        authority_effect=AUTHORITY_EFFECT,
        provenance_digest=digest,
    )
