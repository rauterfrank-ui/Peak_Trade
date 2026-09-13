"""Governed EQUITY_STOCK checkpoint contract.

Checkpoint is a reconstruction anchor / provenance state. It does not
mint Running Equity or EQUITY_STOCK. Unknown required facts fail closed.
Not event acquisition. Not a reconstruction engine. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    CHECKPOINT_CAN_MINT_EQUITY,
    DIMENSION_EQUITY_STOCK,
)

SCHEMA_CLASS = "EQUITY_STOCK_CHECKPOINT_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
CHECKPOINT_KIND = "GOVERNED_RECONSTRUCTION_ANCHOR_PROVENANCE_STATE"
OBSERVATION_VS_AUTHORITY_CLASS = "NON_AUTHORITATIVE_ANCHOR"
EQUITY_MINT_STATUS_NOT_MINTED = "NOT_MINTED"
RUNNING_EQUITY_VALUE_STATE_ABSENT = "ABSENT"
BOUND_ACCOUNT_IDENTITY_STATUS_UNPROVEN = "UNPROVEN_FAIL_CLOSED"
ORDERING_BOUNDARY_CLASS = "CHECKPOINT_PRECEDES_SUBSEQUENT_CLASSIFIED_EVENTS"
REQUIRED_FIELDS: Tuple[str, ...] = (
    "checkpoint_id",
    "checkpoint_schema_version",
    "checkpoint_kind",
    "authority_owner",
    "target_dimension_id",
    "observation_vs_authority_class",
    "equity_mint_status",
    "running_equity_value_state",
    "bound_account_identity_status",
    "ordering_boundary_class",
    "schema_digest",
    "input_set_digest",
    "checkpoint_version",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_EQUITY_CLAIM_MARKERS: Tuple[str, ...] = (
    "equity_stock",
    "running_account_equity",
    "available_for_sizing",
    "authority",
)


class EquityStockCheckpointContractError(ValueError):
    """Fail-closed checkpoint contract violation."""


@dataclass(frozen=True)
class EquityStockCheckpointContractV1:
    checkpoint_id: str
    checkpoint_schema_version: str
    checkpoint_kind: str
    authority_owner: str
    target_dimension_id: str
    observation_vs_authority_class: str
    equity_mint_status: str
    running_equity_value_state: str
    bound_account_identity_status: str
    ordering_boundary_class: str
    schema_digest: str
    input_set_digest: str
    checkpoint_version: str
    claimed_equity_stock_value: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise EquityStockCheckpointContractError(f"CHECKPOINT_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise EquityStockCheckpointContractError(f"CHECKPOINT_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise EquityStockCheckpointContractError(f"CHECKPOINT_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_checkpoint_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def assert_checkpoint_cannot_mint_equity_v1(
    *,
    equity_mint_status: str,
    running_equity_value_state: str,
    claimed_equity_stock_value: str,
    observation_vs_authority_class: str,
) -> None:
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise EquityStockCheckpointContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if equity_mint_status != EQUITY_MINT_STATUS_NOT_MINTED:
        raise EquityStockCheckpointContractError("CHECKPOINT_CANNOT_MINT_EQUITY")
    if running_equity_value_state != RUNNING_EQUITY_VALUE_STATE_ABSENT:
        raise EquityStockCheckpointContractError("CHECKPOINT_CANNOT_MINT_EQUITY")
    if claimed_equity_stock_value != "ABSENT":
        raise EquityStockCheckpointContractError("CHECKPOINT_CANNOT_MINT_EQUITY")
    if observation_vs_authority_class == "AUTHORITY":
        raise EquityStockCheckpointContractError("CHECKPOINT_CANNOT_MINT_EQUITY")
    lowered = claimed_equity_stock_value.lower()
    if any(marker in lowered for marker in _FORBIDDEN_EQUITY_CLAIM_MARKERS):
        raise EquityStockCheckpointContractError("CHECKPOINT_CANNOT_MINT_EQUITY")


def build_equity_stock_checkpoint_contract_v1(
    *,
    checkpoint_id: str,
    schema_digest: str,
    input_set_digest: str,
    checkpoint_version: str,
    claimed_equity_stock_value: str = "ABSENT",
) -> EquityStockCheckpointContractV1:
    payload = {
        "checkpoint_id": _require_non_empty_str(field="checkpoint_id", raw=checkpoint_id),
        "checkpoint_schema_version": CONTRACT_VERSION,
        "checkpoint_kind": CHECKPOINT_KIND,
        "authority_owner": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "target_dimension_id": DIMENSION_EQUITY_STOCK,
        "observation_vs_authority_class": OBSERVATION_VS_AUTHORITY_CLASS,
        "equity_mint_status": EQUITY_MINT_STATUS_NOT_MINTED,
        "running_equity_value_state": RUNNING_EQUITY_VALUE_STATE_ABSENT,
        "bound_account_identity_status": BOUND_ACCOUNT_IDENTITY_STATUS_UNPROVEN,
        "ordering_boundary_class": ORDERING_BOUNDARY_CLASS,
        "schema_digest": _require_non_empty_str(field="schema_digest", raw=schema_digest),
        "input_set_digest": _require_non_empty_str(field="input_set_digest", raw=input_set_digest),
        "checkpoint_version": _require_non_empty_str(
            field="checkpoint_version", raw=checkpoint_version
        ),
        "claimed_equity_stock_value": _require_non_empty_str(
            field="claimed_equity_stock_value", raw=claimed_equity_stock_value
        ),
    }
    if not _SHA256_HEX.match(payload["schema_digest"]):
        raise EquityStockCheckpointContractError("CHECKPOINT_SCHEMA_DIGEST_NOT_SHA256")
    if not _SHA256_HEX.match(payload["input_set_digest"]):
        raise EquityStockCheckpointContractError("CHECKPOINT_INPUT_SET_DIGEST_NOT_SHA256")
    if payload["authority_owner"] != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise EquityStockCheckpointContractError("CHECKPOINT_AUTHORITY_OWNER_MUTATED")
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=payload["equity_mint_status"],
        running_equity_value_state=payload["running_equity_value_state"],
        claimed_equity_stock_value=payload["claimed_equity_stock_value"],
        observation_vs_authority_class=payload["observation_vs_authority_class"],
    )
    digest_payload = dict(payload)
    digest_payload["authority_effect"] = AUTHORITY_EFFECT
    digest = compute_checkpoint_digest_v1(digest_payload)
    return EquityStockCheckpointContractV1(
        **payload,
        authority_effect=AUTHORITY_EFFECT,
        provenance_digest=digest,
    )
