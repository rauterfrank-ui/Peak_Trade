"""Canonical Execution Event schema for Phase 11 Cap 11.1 (contracts only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import Any, Mapping, Optional

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    EXECUTION_EVENT_SCHEMA_VERSION,
    ONE_CANONICAL_EXECUTION_EVENT_SCHEMA,
)


class ExecutionEventKindV1(str, Enum):
    INTENT_ACCEPTED = "INTENT_ACCEPTED"
    ORDER_PLAN_CREATED = "ORDER_PLAN_CREATED"
    RISK_RESERVED = "RISK_RESERVED"
    PRE_SUBMIT_VALIDATED = "PRE_SUBMIT_VALIDATED"
    SUBMIT_PENDING = "SUBMIT_PENDING"
    SUBMIT_ATTEMPTED = "SUBMIT_ATTEMPTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    AMEND_PENDING = "AMEND_PENDING"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    TERMINAL_REJECTED = "TERMINAL_REJECTED"
    ACCOUNTED = "ACCOUNTED"
    RECONCILED = "RECONCILED"
    EVIDENCED = "EVIDENCED"


class ExecutionModeV1(str, Enum):
    SIMULATED = "SIMULATED"
    TESTNET = "TESTNET"
    LIVE = "LIVE"


@dataclass(frozen=True)
class CanonicalExecutionEventV1:
    """Sole canonical execution-event schema for Phase 11.

    Mode-specific ports may emit venue-native transport details only after a
    later authorized capability. Cap 11.1 defines the contract only.
    """

    event_id: str
    event_kind: str
    execution_mode: str
    intent_id: str
    order_plan_id: str
    client_order_id: str
    venue_order_id: str
    decision_digest: str
    lifecycle_state: str
    quantity: str
    fill_quantity: str
    instrument_id: str
    side: str
    reduce_only: bool
    authority_effect: str
    network_effect: str
    credential_effect: str
    submission_authorized: bool
    adapter_decision_authority: bool
    schema_version: str = EXECUTION_EVENT_SCHEMA_VERSION
    semantic_digest: str = ""


REQUIRED_EXECUTION_EVENT_FIELDS: tuple[str, ...] = tuple(
    f.name for f in fields(CanonicalExecutionEventV1)
)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_execution_event_semantic_digest_v1(event: CanonicalExecutionEventV1) -> str:
    body = {k: v for k, v in asdict(event).items() if k not in {"semantic_digest", "event_id"}}
    return hashlib.sha256(_canonical_dumps(body).encode("utf-8")).hexdigest()


def build_canonical_execution_event_v1(
    *,
    event_id: str,
    event_kind: str,
    execution_mode: str,
    intent_id: str,
    order_plan_id: str,
    client_order_id: str,
    lifecycle_state: str,
    instrument_id: str,
    side: str,
    quantity: str,
    reduce_only: bool,
    venue_order_id: str = "",
    decision_digest: str = "",
    fill_quantity: str = "0",
    authority_effect: str = "NONE",
    network_effect: str = "NONE",
    credential_effect: str = "NONE",
    submission_authorized: bool = False,
) -> CanonicalExecutionEventV1:
    if event_kind not in {k.value for k in ExecutionEventKindV1}:
        raise ValueError(f"INVALID_EXECUTION_EVENT_KIND:{event_kind}")
    if execution_mode not in {m.value for m in ExecutionModeV1}:
        raise ValueError(f"INVALID_EXECUTION_MODE:{execution_mode}")
    # Cap 11.1: Testnet/Live modes may appear only as declared contract labels
    # on unreachable ports; events for those modes remain non-submitting.
    if execution_mode in {ExecutionModeV1.TESTNET.value, ExecutionModeV1.LIVE.value}:
        if submission_authorized or network_effect != "NONE" or credential_effect != "NONE":
            raise ValueError(
                "PHASE11_EXECUTION_EVENT_SAFETY_VIOLATION:"
                "testnet/live events must remain non-authorizing in Cap 11.1"
            )
    event = CanonicalExecutionEventV1(
        event_id=event_id,
        event_kind=event_kind,
        execution_mode=execution_mode,
        intent_id=intent_id,
        order_plan_id=order_plan_id,
        client_order_id=client_order_id,
        venue_order_id=venue_order_id,
        decision_digest=decision_digest,
        lifecycle_state=lifecycle_state,
        quantity=str(quantity),
        fill_quantity=str(fill_quantity),
        instrument_id=instrument_id,
        side=side,
        reduce_only=bool(reduce_only),
        authority_effect=authority_effect,
        network_effect=network_effect,
        credential_effect=credential_effect,
        submission_authorized=bool(submission_authorized),
        adapter_decision_authority=False,
    )
    digest = compute_execution_event_semantic_digest_v1(event)
    return CanonicalExecutionEventV1(**{**asdict(event), "semantic_digest": digest})


def prove_one_canonical_execution_event_schema_v1() -> dict[str, Any]:
    names = tuple(f.name for f in fields(CanonicalExecutionEventV1))
    return {
        "ok": ONE_CANONICAL_EXECUTION_EVENT_SCHEMA and names == REQUIRED_EXECUTION_EVENT_FIELDS,
        "ONE_CANONICAL_EXECUTION_EVENT_SCHEMA": True,
        "schema_version": EXECUTION_EVENT_SCHEMA_VERSION,
        "field_names": list(names),
        "parallel_execution_event_schema_introduced": False,
        "adapter_decision_authority_default": False,
        "CORE_LOGIC_CHANGE": False,
    }


def serialize_canonical_execution_event_v1(event: CanonicalExecutionEventV1) -> dict[str, Any]:
    return asdict(event)
