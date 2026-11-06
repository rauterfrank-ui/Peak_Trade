"""Typed D5 checkpoint-observation acquisition contract.

Acquires and binds a governed checkpoint observation for exactly one
BoundAccountIdentity. Observation is not reconstructed equity and is
not source authority. No venue GET. Not event-stream acquisition.
Not a reconstruction engine. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractError,
    assert_same_bound_account_identity_v1,
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    CHECKPOINT_CAN_MINT_EQUITY,
    CHECKPOINT_OBSERVATION_ACQUISITION_CREATED,
    CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED,
    C17_CREATED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EQUITY_MINT_STATUS_NOT_MINTED,
    EquityStockCheckpointContractV1,
    assert_checkpoint_cannot_mint_equity_v1,
)

SCHEMA_CLASS = "CHECKPOINT_OBSERVATION_ACQUISITION_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OBSERVATION_SEMANTIC_CLASS = "GOVERNED_CHECKPOINT_OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION = "OBSERVATION"
NETWORK_METHOD_NONE = "NONE"
COMPLETENESS_COMPLETE = "COMPLETE"
FRESHNESS_EVIDENCE_STATUS = "EXPLICIT_TIMESTAMPS_NOT_WITNESS_TTL_POLICY"
EQUITY_VALUE_STATE_ABSENT = "ABSENT"
FALSE_TOKEN = "false"
REQUIRED_FIELDS: Tuple[str, ...] = (
    "observation_id",
    "source_observation_id",
    "observation_semantic_class",
    "authority_owner",
    "bound_account_identity_ref",
    "bound_account_identity_digest",
    "observed_at_as_of",
    "acquired_at",
    "component_completeness",
    "freshness_policy_status",
    "observation_vs_authority_class",
    "network_method",
    "claimed_equity_stock_value",
    "reconstructed_equity_created",
    "event_stream_acquisition_created",
    "eq_reconciliation_executed",
    "raw_eq_source_authority",
    "source_selected",
    "mapping_proven",
    "c17_created",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_FAIL_CLOSED_TOKENS: Tuple[str, ...] = (
    "UNKNOWN",
    "MISSING",
    "STALE",
    "PARTIAL",
    "UNCLASSIFIED",
    "UNPROVEN",
    "UNSPECIFIED",
    "INCOMPLETE",
    "IDENTITY_MISMATCH",
)
_FORBIDDEN_EQUITY_CLAIM_MARKERS: Tuple[str, ...] = (
    "equity_stock",
    "running_account_equity",
    "available_for_sizing",
    "reconstructed_equity",
    "totaleq",
    "availeq",
    "adjeq",
    "availbal",
    "cashbal",
)
_FORBIDDEN_EVENT_STREAM_MARKERS: Tuple[str, ...] = (
    "event_stream",
    "classified_event",
    "equity_affecting_event",
)
_FORBIDDEN_NETWORK_METHODS: Tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE")


class CheckpointObservationAcquisitionContractError(ValueError):
    """Fail-closed checkpoint-observation acquisition contract violation."""


@dataclass(frozen=True)
class CheckpointObservationAcquisitionResultV1:
    observation_id: str
    source_observation_id: str
    observation_semantic_class: str
    authority_owner: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    observed_at_as_of: str
    acquired_at: str
    component_completeness: str
    freshness_policy_status: str
    observation_vs_authority_class: str
    network_method: str
    claimed_equity_stock_value: str
    reconstructed_equity_created: str
    event_stream_acquisition_created: str
    eq_reconciliation_executed: str
    raw_eq_source_authority: str
    source_selected: str
    mapping_proven: str
    c17_created: str
    authority_effect: str
    provenance_digest: str


@dataclass(frozen=True)
class CheckpointObservationCheckpointBindingV1:
    binding_id: str
    checkpoint_id: str
    checkpoint_provenance_digest: str
    checkpoint_observation_ref: str
    checkpoint_observation_digest: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    equity_mint_status: str
    reconstructed_equity_created: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_FIELD_MISSING:{field}"
        )
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_checkpoint_observation_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_iso_z(*, field: str, raw: Any) -> str:
    text = _require_non_empty_str(field=field, raw=raw)
    if _ISO_Z.fullmatch(text) is None:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_TIMESTAMP_NOT_ISO_Z:{field}"
        )
    return text


def _reject_fail_closed_token(*, field: str, raw: str) -> None:
    if raw in _FAIL_CLOSED_TOKENS:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_{raw}_FAIL_CLOSED:{field}"
        )


def _reject_equity_or_event_claim(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    if any(marker in lowered for marker in _FORBIDDEN_EQUITY_CLAIM_MARKERS):
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_EQUITY_CLAIM_FORBIDDEN:{field}"
        )
    if any(marker in lowered for marker in _FORBIDDEN_EVENT_STREAM_MARKERS):
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_EVENT_STREAM_ACQUISITION_FORBIDDEN"
        )


def acquire_checkpoint_observation_v1(
    *,
    observation_id: str,
    source_observation_id: str,
    expected_bound_account_identity_ref: str,
    expected_bound_account_identity_digest: str,
    bound_account_identity_ref: str,
    bound_account_identity_digest: str,
    observed_at_as_of: str,
    acquired_at: str,
    component_completeness: str,
    freshness_policy_status: str,
    observation_vs_authority_class: str = OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION,
    network_method: str = NETWORK_METHOD_NONE,
    claimed_equity_stock_value: str = EQUITY_VALUE_STATE_ABSENT,
) -> CheckpointObservationAcquisitionResultV1:
    expected_ref, expected_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=expected_bound_account_identity_ref,
        bound_account_identity_digest=expected_bound_account_identity_digest,
    )
    observed_ref, observed_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=bound_account_identity_ref,
        bound_account_identity_digest=bound_account_identity_digest,
    )
    try:
        assert_same_bound_account_identity_v1(
            left_ref=expected_ref,
            left_digest=expected_digest,
            right_ref=observed_ref,
            right_digest=observed_digest,
        )
    except BoundAccountIdentityContractError as exc:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_IDENTITY_MISMATCH_CROSS_ACCOUNT"
        ) from exc
    if CHECKPOINT_OBSERVATION_ACQUISITION_CREATED is not True:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_ACQUISITION_NOT_CREATED"
        )
    if CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_NETWORK_GET_NOT_UNAUTHORIZED"
        )
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise CheckpointObservationAcquisitionContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise CheckpointObservationAcquisitionContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if SOURCE_SELECTED is not False:
        raise CheckpointObservationAcquisitionContractError("SOURCE_SELECTED_NOT_FALSE")
    if C17_CREATED is not False:
        raise CheckpointObservationAcquisitionContractError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_AUTHORITY_OWNER_MUTATED"
        )
    observation = _require_non_empty_str(field="observation_id", raw=observation_id)
    source_observation = _require_non_empty_str(
        field="source_observation_id", raw=source_observation_id
    )
    _reject_fail_closed_token(field="observation_id", raw=observation)
    _reject_fail_closed_token(field="source_observation_id", raw=source_observation)
    observed_at = _require_iso_z(field="observed_at_as_of", raw=observed_at_as_of)
    acquired = _require_iso_z(field="acquired_at", raw=acquired_at)
    completeness = _require_non_empty_str(
        field="component_completeness", raw=component_completeness
    )
    freshness = _require_non_empty_str(field="freshness_policy_status", raw=freshness_policy_status)
    authority_class = _require_non_empty_str(
        field="observation_vs_authority_class", raw=observation_vs_authority_class
    )
    method = _require_non_empty_str(field="network_method", raw=network_method)
    claimed = _require_non_empty_str(
        field="claimed_equity_stock_value", raw=claimed_equity_stock_value
    )
    _reject_fail_closed_token(field="component_completeness", raw=completeness)
    _reject_fail_closed_token(field="freshness_policy_status", raw=freshness)
    _reject_fail_closed_token(field="observation_vs_authority_class", raw=authority_class)
    _reject_fail_closed_token(field="network_method", raw=method)
    _reject_fail_closed_token(field="claimed_equity_stock_value", raw=claimed)
    _reject_equity_or_event_claim(field="observation_id", raw=observation)
    _reject_equity_or_event_claim(field="source_observation_id", raw=source_observation)
    _reject_equity_or_event_claim(
        field="observation_semantic_class", raw=OBSERVATION_SEMANTIC_CLASS
    )
    _reject_equity_or_event_claim(field="claimed_equity_stock_value", raw=claimed)
    if completeness != COMPLETENESS_COMPLETE:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_PARTIAL_OR_INCOMPLETE_FAIL_CLOSED"
        )
    if freshness != FRESHNESS_EVIDENCE_STATUS:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_FRESHNESS_NOT_EXPLICIT_TIMESTAMPS"
        )
    if authority_class == "AUTHORITY":
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_AUTHORITY_CLASS_FORBIDDEN"
        )
    if authority_class != OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_OBSERVATION_VS_AUTHORITY_CLASS_UNKNOWN"
        )
    if method in _FORBIDDEN_NETWORK_METHODS:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_NETWORK_METHOD_FORBIDDEN:{method}"
        )
    if method != NETWORK_METHOD_NONE:
        raise CheckpointObservationAcquisitionContractError(
            f"CHECKPOINT_OBSERVATION_NETWORK_METHOD_NOT_NONE:{method}"
        )
    if claimed != EQUITY_VALUE_STATE_ABSENT:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_CANNOT_MINT_EQUITY"
        )
    payload = {
        "observation_id": observation,
        "source_observation_id": source_observation,
        "observation_semantic_class": OBSERVATION_SEMANTIC_CLASS,
        "authority_owner": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "bound_account_identity_ref": observed_ref,
        "bound_account_identity_digest": observed_digest,
        "observed_at_as_of": observed_at,
        "acquired_at": acquired,
        "component_completeness": completeness,
        "freshness_policy_status": freshness,
        "observation_vs_authority_class": authority_class,
        "network_method": method,
        "claimed_equity_stock_value": claimed,
        "reconstructed_equity_created": FALSE_TOKEN,
        "event_stream_acquisition_created": FALSE_TOKEN,
        "eq_reconciliation_executed": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "mapping_proven": FALSE_TOKEN,
        "c17_created": FALSE_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_checkpoint_observation_digest_v1(payload)
    return CheckpointObservationAcquisitionResultV1(
        **payload,
        provenance_digest=digest,
    )


def bind_checkpoint_observation_to_checkpoint_v1(
    *,
    binding_id: str,
    checkpoint: EquityStockCheckpointContractV1,
    acquisition: CheckpointObservationAcquisitionResultV1,
) -> CheckpointObservationCheckpointBindingV1:
    require_bound_account_identity_ref_v1(
        bound_account_identity_ref=checkpoint.bound_account_identity_ref,
        bound_account_identity_digest=checkpoint.bound_account_identity_digest,
    )
    try:
        assert_same_bound_account_identity_v1(
            left_ref=checkpoint.bound_account_identity_ref,
            left_digest=checkpoint.bound_account_identity_digest,
            right_ref=acquisition.bound_account_identity_ref,
            right_digest=acquisition.bound_account_identity_digest,
        )
    except BoundAccountIdentityContractError as exc:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_IDENTITY_MISMATCH_CROSS_ACCOUNT"
        ) from exc
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise CheckpointObservationAcquisitionContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=checkpoint.equity_mint_status,
        running_equity_value_state=checkpoint.running_equity_value_state,
        claimed_equity_stock_value=checkpoint.claimed_equity_stock_value,
        observation_vs_authority_class=checkpoint.observation_vs_authority_class,
    )
    if checkpoint.equity_mint_status != EQUITY_MINT_STATUS_NOT_MINTED:
        raise CheckpointObservationAcquisitionContractError("CHECKPOINT_CANNOT_MINT_EQUITY")
    if acquisition.claimed_equity_stock_value != EQUITY_VALUE_STATE_ABSENT:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_CANNOT_MINT_EQUITY"
        )
    if acquisition.reconstructed_equity_created != FALSE_TOKEN:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_RECONSTRUCTED_EQUITY_FORBIDDEN"
        )
    if acquisition.event_stream_acquisition_created != FALSE_TOKEN:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_EVENT_STREAM_ACQUISITION_FORBIDDEN"
        )
    if acquisition.eq_reconciliation_executed != FALSE_TOKEN:
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_EQ_RECONCILIATION_EXECUTED_FORBIDDEN"
        )
    if not _SHA256_HEX.match(checkpoint.provenance_digest):
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_PROVENANCE_DIGEST_NOT_SHA256"
        )
    if not _SHA256_HEX.match(acquisition.provenance_digest):
        raise CheckpointObservationAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_DIGEST_NOT_SHA256"
        )
    binding = _require_non_empty_str(field="binding_id", raw=binding_id)
    _reject_fail_closed_token(field="binding_id", raw=binding)
    payload = {
        "binding_id": binding,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_provenance_digest": checkpoint.provenance_digest,
        "checkpoint_observation_ref": acquisition.observation_id,
        "checkpoint_observation_digest": acquisition.provenance_digest,
        "bound_account_identity_ref": acquisition.bound_account_identity_ref,
        "bound_account_identity_digest": acquisition.bound_account_identity_digest,
        "equity_mint_status": EQUITY_MINT_STATUS_NOT_MINTED,
        "reconstructed_equity_created": FALSE_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_checkpoint_observation_digest_v1(payload)
    return CheckpointObservationCheckpointBindingV1(
        **payload,
        provenance_digest=digest,
    )
