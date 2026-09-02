"""Deterministic action identity and OKX-safe client-order identity."""

from __future__ import annotations

import hashlib
import json

from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    CLIENT_ORDER_ID_ALLOWED_PATTERN,
    CLIENT_ORDER_ID_MAX_LENGTH,
    build_client_order_id,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CLORDID_ENVIRONMENT,
    CONTRACT_VERSION,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    ActionIdentityV1,
    CanonicalLineageSnapshotV1,
)


class ActionIdentityError(RuntimeError):
    """Fail-closed action-identity violation."""


def _canonical_payload(lineage: CanonicalLineageSnapshotV1) -> str:
    payload = {
        "contract_version": CONTRACT_VERSION,
        "instrument_id": lineage.instrument_id,
        "decision_id": lineage.decision_id,
        "correlation_id": lineage.correlation_id,
        "cycle_index": int(lineage.cycle_index),
        "trading_epoch": lineage.trading_epoch,
        "plan_digest": lineage.plan_digest,
        "plan_intent_action": lineage.plan_intent_action,
        "plan_side": lineage.plan_side,
        "plan_quantity": lineage.plan_quantity,
        "mapper_intended_side": lineage.mapper_intended_side,
        "mapper_intended_quantity": lineage.mapper_intended_quantity,
        "risk_digest": lineage.risk_digest,
        "safety_digest": lineage.safety_digest,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_action_identity_v1(lineage: CanonicalLineageSnapshotV1) -> ActionIdentityV1:
    if not str(lineage.correlation_id or "").strip():
        raise ActionIdentityError("CORRELATION_ID_REQUIRED")
    if int(lineage.cycle_index) < 0:
        raise ActionIdentityError("CYCLE_INDEX_MUST_BE_NON_NEGATIVE")
    if not str(lineage.plan_digest or "").strip():
        raise ActionIdentityError("PLAN_DIGEST_REQUIRED")
    if not str(lineage.decision_id or "").strip():
        raise ActionIdentityError("DECISION_ID_REQUIRED")
    material = hashlib.sha256(_canonical_payload(lineage).encode("utf-8")).hexdigest()
    client_order_id = build_client_order_id(
        run_id=material,
        session_id=hashlib.sha256(lineage.correlation_id.encode("utf-8")).hexdigest(),
        intent_id=lineage.plan_digest
        if all(ch in "0123456789abcdef" for ch in lineage.plan_digest.lower())
        else material,
        environment=CLORDID_ENVIRONMENT,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        sequence=int(lineage.cycle_index) % 256,
    )
    if not client_order_id or len(client_order_id) > CLIENT_ORDER_ID_MAX_LENGTH:
        raise ActionIdentityError("CLORDID_LENGTH_VIOLATION")
    if not CLIENT_ORDER_ID_ALLOWED_PATTERN.fullmatch(client_order_id):
        raise ActionIdentityError("CLORDID_ALPHANUMERIC_VIOLATION")
    return ActionIdentityV1(
        action_identity=material,
        correlation_id=str(lineage.correlation_id),
        cycle_index=int(lineage.cycle_index),
        client_order_id=client_order_id,
        plan_digest=str(lineage.plan_digest),
        instrument_id=str(lineage.instrument_id),
    )
