"""Order-Capability payload builder contract (v1).

Pure offline deterministic payload construction for bounded testnet order-capability
candidates. Does not authorize orders, network, live, preflight lift, or execute.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT

PACKAGE_MARKER = "ORDER_CAPABILITY_PAYLOAD_BUILDER_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_payload_build_result.v1"

CANONICAL_VENUE = "kraken_futures_demo"
DEFAULT_ORDER_TYPE = "limit"
DEFAULT_MAX_NOTIONAL_EUR = 10.0
DEFAULT_MAX_LOSS_CAP_EUR = 1.0
DEFAULT_SESSION_DURATION_SECONDS = 60
DEFAULT_ABORT_ACK_MARKER = "CONFIRMED"
DEFAULT_KILL_SWITCH_BINDING_MARKER = "RUNTIME_BINDING_PLACEHOLDER_NOT_VALIDATED"
DEFAULT_CLEANUP_CANCEL_CORRELATION_MARKER = "CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED"
DEFAULT_STATUS = "BLOCKED_NOT_AUTHORIZED"

ALLOWED_ORDER_TYPES = frozenset({DEFAULT_ORDER_TYPE})
ALLOWED_SIDES = frozenset({"buy", "sell"})
ALLOWED_ENVIRONMENTS = frozenset(
    {
        "kraken_futures_demo",
        "demo",
        "testnet",
        "demo_testnet_only",
    }
)
FORBIDDEN_ENVIRONMENT_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
    }
)
FORBIDDEN_SERIALIZATION_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "password",
        "token",
        "credential",
        "credentials",
        "private_key",
    }
)


class PayloadBuildError(ValueError):
    """Fail-closed payload build or validation error."""


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class OrderCapabilityPayloadInput:
    instrument: str
    venue: str
    environment: str
    side: str
    order_type: str
    limit_price: float
    quantity: float
    max_notional_eur: float
    max_loss_cap_eur: float
    session_duration_seconds: int
    operator_go_token_binding: str
    abort_ack_marker: str
    time_in_force: str
    post_only: bool
    reduce_only: bool
    kill_switch_binding_marker: str
    cleanup_cancel_correlation_marker: str
    evidence_correlation_id: str = ""


@dataclass(frozen=True)
class OrderCapabilityPayload:
    instrument: str
    venue: str
    environment: str
    side: str
    order_type: str
    limit_price: float
    quantity: float
    computed_notional_eur: float
    max_notional_eur: float
    max_loss_cap_eur: float
    session_duration_seconds: int
    time_in_force: str
    post_only: bool
    reduce_only: bool
    client_order_id: str
    idempotency_key: str
    evidence_correlation_id: str
    operator_go_token_binding: str
    abort_ack_marker: str
    kill_switch_binding_marker: str
    cleanup_cancel_correlation_marker: str
    status: str
    no_submit: bool
    no_network: bool
    execute_authorized: bool
    order_submission_executed: bool
    cancel_executed: bool
    trade_position_mutation_executed: bool
    no_authority_change: bool
    preflight_remains_blocked: bool
    live_ready: bool
    dashboard_truth_granted: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _validate_environment(environment: str) -> None:
    normalized = _normalize(environment)
    if not normalized:
        raise PayloadBuildError("environment must be non-empty")
    for marker in FORBIDDEN_ENVIRONMENT_MARKERS:
        if marker in normalized:
            raise PayloadBuildError(f"environment must not include forbidden marker {marker!r}")
    if normalized not in ALLOWED_ENVIRONMENTS:
        raise PayloadBuildError(f"environment must be one of {sorted(ALLOWED_ENVIRONMENTS)!r}")


def _validate_venue(venue: str) -> None:
    normalized = _normalize(venue).replace(" ", "_")
    if normalized != CANONICAL_VENUE:
        raise PayloadBuildError(f"venue must be canonical {CANONICAL_VENUE!r}")


def _deterministic_digest(*parts: str) -> str:
    material = "|".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _deterministic_client_order_id(
    inp: OrderCapabilityPayloadInput,
    evidence_correlation_id: str,
) -> str:
    digest = _deterministic_digest(
        inp.instrument,
        inp.venue,
        inp.environment,
        inp.side,
        inp.order_type,
        f"{inp.limit_price:.8f}",
        f"{inp.quantity:.8f}",
        inp.operator_go_token_binding,
        evidence_correlation_id,
    )
    return f"ocpb-{digest[:32]}"


def _resolve_evidence_correlation_id(inp: OrderCapabilityPayloadInput) -> str:
    if inp.evidence_correlation_id.strip():
        return inp.evidence_correlation_id.strip()
    digest = _deterministic_digest(
        "evidence-correlation",
        inp.instrument,
        inp.venue,
        inp.side,
        inp.operator_go_token_binding,
    )
    return f"evcorr-{digest[:24]}"


def _validate_input(inp: OrderCapabilityPayloadInput) -> float:
    if not inp.instrument.strip():
        raise PayloadBuildError("instrument must be non-empty")
    _validate_venue(inp.venue)
    _validate_environment(inp.environment)
    side = _normalize(inp.side)
    if side not in ALLOWED_SIDES:
        raise PayloadBuildError(f"side must be one of {sorted(ALLOWED_SIDES)!r}")
    order_type = _normalize(inp.order_type)
    if order_type not in ALLOWED_ORDER_TYPES:
        raise PayloadBuildError(f"order_type must be one of {sorted(ALLOWED_ORDER_TYPES)!r}")
    if inp.limit_price <= 0:
        raise PayloadBuildError("limit_price must be > 0")
    if inp.quantity <= 0:
        raise PayloadBuildError("quantity must be > 0")
    if inp.max_notional_eur <= 0:
        raise PayloadBuildError("max_notional_eur must be > 0")
    if inp.max_loss_cap_eur <= 0:
        raise PayloadBuildError("max_loss_cap_eur must be > 0")
    if inp.max_loss_cap_eur > inp.max_notional_eur:
        raise PayloadBuildError("max_loss_cap_eur must be <= max_notional_eur")
    if inp.session_duration_seconds <= 0:
        raise PayloadBuildError("session_duration_seconds must be > 0")
    if inp.session_duration_seconds > DEFAULT_SESSION_DURATION_SECONDS:
        raise PayloadBuildError(
            f"session_duration_seconds must be <= {DEFAULT_SESSION_DURATION_SECONDS}"
        )
    if not inp.operator_go_token_binding.strip():
        raise PayloadBuildError("operator_go_token_binding must be non-empty")
    if _normalize(inp.abort_ack_marker) != _normalize(DEFAULT_ABORT_ACK_MARKER):
        raise PayloadBuildError(f"abort_ack_marker must be {DEFAULT_ABORT_ACK_MARKER!r}")
    if not inp.time_in_force.strip():
        raise PayloadBuildError("time_in_force must be explicitly set")
    if not inp.kill_switch_binding_marker.strip():
        raise PayloadBuildError("kill_switch_binding_marker must be non-empty")
    if not inp.cleanup_cancel_correlation_marker.strip():
        raise PayloadBuildError("cleanup_cancel_correlation_marker must be non-empty")

    computed_notional = inp.limit_price * inp.quantity
    if computed_notional > inp.max_notional_eur:
        raise PayloadBuildError("computed notional exceeds max_notional_eur cap")
    return computed_notional


def build_order_capability_payload(inp: OrderCapabilityPayloadInput) -> OrderCapabilityPayload:
    computed_notional = _validate_input(inp)
    evidence_correlation_id = _resolve_evidence_correlation_id(inp)
    client_order_id = _deterministic_client_order_id(inp, evidence_correlation_id)
    return OrderCapabilityPayload(
        instrument=inp.instrument,
        venue=CANONICAL_VENUE,
        environment=_normalize(inp.environment),
        side=_normalize(inp.side),
        order_type=_normalize(inp.order_type),
        limit_price=inp.limit_price,
        quantity=inp.quantity,
        computed_notional_eur=computed_notional,
        max_notional_eur=inp.max_notional_eur,
        max_loss_cap_eur=inp.max_loss_cap_eur,
        session_duration_seconds=inp.session_duration_seconds,
        time_in_force=inp.time_in_force,
        post_only=inp.post_only,
        reduce_only=inp.reduce_only,
        client_order_id=client_order_id,
        idempotency_key=client_order_id,
        evidence_correlation_id=evidence_correlation_id,
        operator_go_token_binding=inp.operator_go_token_binding.strip(),
        abort_ack_marker=DEFAULT_ABORT_ACK_MARKER,
        kill_switch_binding_marker=inp.kill_switch_binding_marker.strip(),
        cleanup_cancel_correlation_marker=inp.cleanup_cancel_correlation_marker.strip(),
        status=DEFAULT_STATUS,
        no_submit=True,
        no_network=True,
        execute_authorized=False,
        order_submission_executed=False,
        cancel_executed=False,
        trade_position_mutation_executed=False,
        no_authority_change=True,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
    )


def serialize_order_capability_payload(payload: OrderCapabilityPayload) -> dict[str, Any]:
    data = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "instrument": payload.instrument,
        "venue": payload.venue,
        "environment": payload.environment,
        "side": payload.side,
        "order_type": payload.order_type,
        "limit_price": payload.limit_price,
        "quantity": payload.quantity,
        "computed_notional_eur": payload.computed_notional_eur,
        "max_notional_eur": payload.max_notional_eur,
        "max_loss_cap_eur": payload.max_loss_cap_eur,
        "session_duration_seconds": payload.session_duration_seconds,
        "time_in_force": payload.time_in_force,
        "post_only": payload.post_only,
        "reduce_only": payload.reduce_only,
        "client_order_id": payload.client_order_id,
        "idempotency_key": payload.idempotency_key,
        "evidence_correlation_id": payload.evidence_correlation_id,
        "operator_go_token_binding": payload.operator_go_token_binding,
        "abort_ack_marker": payload.abort_ack_marker,
        "kill_switch_binding_marker": payload.kill_switch_binding_marker,
        "cleanup_cancel_correlation_marker": payload.cleanup_cancel_correlation_marker,
        "status": payload.status,
        "no_submit": payload.no_submit,
        "no_network": payload.no_network,
        "execute_authorized": payload.execute_authorized,
        "order_submission_executed": payload.order_submission_executed,
        "cancel_executed": payload.cancel_executed,
        "trade_position_mutation_executed": payload.trade_position_mutation_executed,
        "no_authority_change": payload.no_authority_change,
        "preflight_remains_blocked": payload.preflight_remains_blocked,
        "live_ready": payload.live_ready,
        "dashboard_truth_granted": payload.dashboard_truth_granted,
    }
    validate_order_capability_payload(payload)
    _validate_serialized_keys(data)
    return data


def _validate_serialized_keys(data: dict[str, Any]) -> None:
    for key in data:
        normalized = key.lower()
        if normalized in FORBIDDEN_SERIALIZATION_KEYS:
            raise PayloadBuildError(f"serialized payload must not include forbidden key {key!r}")


def validate_order_capability_payload(payload: OrderCapabilityPayload) -> None:
    if payload.status != DEFAULT_STATUS:
        raise PayloadBuildError(f"status must be {DEFAULT_STATUS!r}")
    if not payload.no_submit or not payload.no_network:
        raise PayloadBuildError("no_submit and no_network must remain true")
    if payload.execute_authorized:
        raise PayloadBuildError("execute_authorized must remain false")
    if payload.order_submission_executed or payload.cancel_executed:
        raise PayloadBuildError("order_submission_executed and cancel_executed must remain false")
    if payload.trade_position_mutation_executed:
        raise PayloadBuildError("trade_position_mutation_executed must remain false")
    if not payload.no_authority_change or not payload.preflight_remains_blocked:
        raise PayloadBuildError("authority and preflight safety flags must remain blocked")
    if payload.live_ready or payload.dashboard_truth_granted:
        raise PayloadBuildError("live_ready and dashboard_truth_granted must remain false")
    if payload.computed_notional_eur > payload.max_notional_eur:
        raise PayloadBuildError("computed_notional_eur exceeds max_notional_eur")
    if payload.max_loss_cap_eur > payload.max_notional_eur:
        raise PayloadBuildError("max_loss_cap_eur exceeds max_notional_eur")
