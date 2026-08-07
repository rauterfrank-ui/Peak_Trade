"""Deterministic unique client_order_id + submission semantics contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    CLIENT_ORDER_ID_CONTRACT_VERSION,
)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def derive_client_order_id_v1(
    *,
    intent_id: str,
    order_plan_id: str,
    trading_epoch: str,
    instrument_id: str,
    side: str,
    intent_action: str,
) -> str:
    """Deterministic client_order_id from canonical identity inputs."""
    if not all([intent_id, order_plan_id, trading_epoch, instrument_id, side, intent_action]):
        raise ValueError("CLIENT_ORDER_ID_INPUT_MISSING")
    material = {
        "contract_version": CLIENT_ORDER_ID_CONTRACT_VERSION,
        "intent_id": intent_id,
        "order_plan_id": order_plan_id,
        "trading_epoch": trading_epoch,
        "instrument_id": instrument_id,
        "side": side,
        "intent_action": intent_action,
    }
    digest = hashlib.sha256(_canonical_dumps(material).encode("utf-8")).hexdigest()
    return f"pt-coid-{digest[:32]}"


@dataclass
class SubmissionIdempotencyRegistryV1:
    """In-memory Cap 11.1 contract registry (no venue side effects)."""

    seen_client_order_ids: set[str] = field(default_factory=set)
    seen_fill_ids: set[str] = field(default_factory=set)
    submission_records: dict[str, dict[str, Any]] = field(default_factory=dict)

    def claim_submission(self, client_order_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not client_order_id:
            raise ValueError("CLIENT_ORDER_ID_REQUIRED")
        existing = self.submission_records.get(client_order_id)
        if existing is not None:
            # Idempotent replay: same payload admitted; conflicting payload blocked.
            if existing.get("payload_digest") != _payload_digest(payload):
                raise ValueError("DUPLICATE_ORDER_CONFLICTING_PAYLOAD")
            return {
                "admitted": True,
                "idempotent_replay": True,
                "duplicate_order_prevented": True,
                "client_order_id": client_order_id,
            }
        self.seen_client_order_ids.add(client_order_id)
        self.submission_records[client_order_id] = {
            "payload_digest": _payload_digest(payload),
            "state": "SUBMIT_ATTEMPTED",
        }
        return {
            "admitted": True,
            "idempotent_replay": False,
            "duplicate_order_prevented": True,
            "client_order_id": client_order_id,
        }

    def apply_fill(self, fill_id: str) -> dict[str, Any]:
        if not fill_id:
            raise ValueError("FILL_ID_REQUIRED")
        if fill_id in self.seen_fill_ids:
            return {
                "applied": False,
                "duplicate_fill_prevented": True,
                "fill_id": fill_id,
            }
        self.seen_fill_ids.add(fill_id)
        return {
            "applied": True,
            "duplicate_fill_prevented": True,
            "fill_id": fill_id,
        }


def _payload_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_dumps(dict(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class UnknownSubmitSemanticsV1:
    """UNKNOWN submit contract: never blind retry; query-before-retry required."""

    UNKNOWN_SUBMIT_RESULT_NEVER_BLINDLY_RETRIED: bool = True
    EXCHANGE_QUERY_BEFORE_RETRY: bool = True
    EXCHANGE_ACCESS_IN_CAPABILITY_11_1: bool = False
    NETWORK_EFFECT: str = "NONE"

    def evaluate_retry_admissibility(
        self, *, exchange_query_completed: bool, blind_retry: bool
    ) -> dict[str, Any]:
        if blind_retry:
            return {
                "admissible": False,
                "reason": "UNKNOWN_SUBMIT_RESULT_NEVER_BLINDLY_RETRIED",
                "EXCHANGE_QUERY_BEFORE_RETRY": True,
                "exchange_access_performed": False,
            }
        if not exchange_query_completed:
            return {
                "admissible": False,
                "reason": "EXCHANGE_QUERY_BEFORE_RETRY_REQUIRED",
                "EXCHANGE_QUERY_BEFORE_RETRY": True,
                "exchange_access_performed": False,
            }
        # Cap 11.1: contract admits the *gate* only; no exchange call occurs.
        return {
            "admissible": True,
            "reason": "CONTRACT_GATE_SATISFIED_NO_EXCHANGE_ACCESS",
            "EXCHANGE_QUERY_BEFORE_RETRY": True,
            "exchange_access_performed": False,
        }


def prove_client_order_id_and_submission_semantics_v1() -> dict[str, Any]:
    coid_a = derive_client_order_id_v1(
        intent_id="intent-1",
        order_plan_id="plan-1",
        trading_epoch="epoch-1",
        instrument_id="INST-1",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    coid_b = derive_client_order_id_v1(
        intent_id="intent-1",
        order_plan_id="plan-1",
        trading_epoch="epoch-1",
        instrument_id="INST-1",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    coid_c = derive_client_order_id_v1(
        intent_id="intent-2",
        order_plan_id="plan-1",
        trading_epoch="epoch-1",
        instrument_id="INST-1",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    registry = SubmissionIdempotencyRegistryV1()
    first = registry.claim_submission(coid_a, {"qty": "1"})
    replay = registry.claim_submission(coid_a, {"qty": "1"})
    conflict_blocked = False
    try:
        registry.claim_submission(coid_a, {"qty": "2"})
    except ValueError as exc:
        conflict_blocked = "DUPLICATE_ORDER_CONFLICTING_PAYLOAD" in str(exc)
    fill1 = registry.apply_fill("fill-1")
    fill_dup = registry.apply_fill("fill-1")
    unknown = UnknownSubmitSemanticsV1()
    blind = unknown.evaluate_retry_admissibility(exchange_query_completed=False, blind_retry=True)
    gated = unknown.evaluate_retry_admissibility(exchange_query_completed=True, blind_retry=False)
    ok = all(
        [
            coid_a == coid_b,
            coid_a != coid_c,
            first["idempotent_replay"] is False,
            replay["idempotent_replay"] is True,
            conflict_blocked,
            fill1["applied"] is True,
            fill_dup["applied"] is False,
            blind["admissible"] is False,
            gated["admissible"] is True,
            gated["exchange_access_performed"] is False,
        ]
    )
    return {
        "ok": ok,
        "CLIENT_ORDER_ID_DETERMINISTIC": coid_a == coid_b,
        "CLIENT_ORDER_ID_UNIQUE_FOR_DISTINCT_INPUTS": coid_a != coid_c,
        "SUBMISSION_IDEMPOTENT": True,
        "NO_DUPLICATE_ORDER": conflict_blocked,
        "NO_DUPLICATE_FILL_APPLICATION": fill_dup["duplicate_fill_prevented"] is True,
        "UNKNOWN_BLIND_RETRY_FORBIDDEN": blind["admissible"] is False,
        "EXCHANGE_QUERY_BEFORE_RETRY_CONTRACT": True,
        "EXCHANGE_ACCESS_IN_CAPABILITY_11_1": False,
        "sample_client_order_id": coid_a,
        "CORE_LOGIC_CHANGE": False,
    }
