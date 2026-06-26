"""OKX Europe adapter lifecycle offline contract (v0, Package E / INV-033 E2).

Pure offline, fixture-evaluable contracts for auth capabilities, order/cancel/fill/position
normalization, client-order-id semantics, reconciliation FSM, and durable evidence.

Does not authorize network, credentials, private API, orders, runtime, or promotion.
PE-12 and PE-9 remain Kraken-scoped — this module is the OKX-Europe Success-SSOT for
adapter lifecycle semantics only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    DEMO_REFERENCE_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_TYPE,
    PRODUCTION_RULE_TYPE,
    REGULATORY_ENTITY_OKX_EUROPE_MARKETS,
    REGULATORY_MAX_RETAIL_LEVERAGE,
    VENUE_OKX_EUROPE,
    VENUE_REPORTED_LEVERAGE_CAPABILITY,
    effective_operational_leverage_cap,
    LeverageSemantics,
)
from src.ops.aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0 import (
    FORBIDDEN_SERIALIZATION_KEYS,
    SIMULATION_HEADER_NAME,
)

PACKAGE_MARKER = "OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_V0=true"
CONTRACT_VERSION = "okx_europe_adapter_lifecycle.v0"

RUNTIME_GO_READY = False
RUNTIME_EXECUTED = False
PROMOTION_ALLOWED = False
ORDER_ATTEMPT_COUNT = 0
CANCEL_ATTEMPT_COUNT = 0
NETWORK_CALL_COUNT = 0
AWS_RUNTIME_EXECUTED = False
AUTOMATIC_ORDER_RESEND_ALLOWED = False
AUTOMATIC_INSTRUMENT_ROLLOVER_ALLOWED = False
UNKNOWN_REMOTE_STATE_FAIL_CLOSED = True

CLIENT_ORDER_ID_MAX_LENGTH = 32
CLIENT_ORDER_ID_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9]+$")

OKX_DOCUMENTED_ORDER_STATES: frozenset[str] = frozenset(
    {
        "live",
        "partially_filled",
        "filled",
        "canceled",
        "mmp_canceled",
    }
)

_BITCOIN_FRAGMENTS = frozenset({"BTC", "XBT", "BITCOIN"})
_FORBIDDEN_SPOT_MARKERS = frozenset({"SPOT", "SWAP"})

OPERATOR_IDENTITY_DEFAULT = "Frank Rauter"


class AuthCapabilityKind(str, Enum):
    PUBLIC_CAPABILITY = "PUBLIC_CAPABILITY"
    READONLY_PRIVATE_CAPABILITY = "READONLY_PRIVATE_CAPABILITY"
    TRADE_CAPABILITY = "TRADE_CAPABILITY"


class NormalizedOrderState(str, Enum):
    LOCAL_INTENT_CREATED = "LOCAL_INTENT_CREATED"
    REQUEST_PREPARED = "REQUEST_PREPARED"
    REQUEST_SENT = "REQUEST_SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    LIVE = "LIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN_REMOTE_STATE = "UNKNOWN_REMOTE_STATE"


class ReconciliationTrigger(str, Enum):
    STARTUP = "STARTUP"
    NORMAL_POLL = "NORMAL_POLL"
    WEBSOCKET_DISCONNECT = "WEBSOCKET_DISCONNECT"
    REST_TIMEOUT = "REST_TIMEOUT"
    ORDER_REQUEST_TIMEOUT = "ORDER_REQUEST_TIMEOUT"
    CANCEL_REQUEST_TIMEOUT = "CANCEL_REQUEST_TIMEOUT"
    RECONNECT = "RECONNECT"
    PROCESS_RESTART = "PROCESS_RESTART"
    AWS_TASK_RESTART = "AWS_TASK_RESTART"
    CLOCK_DRIFT = "CLOCK_DRIFT"
    RATE_LIMIT = "RATE_LIMIT"
    PARTIAL_FILL = "PARTIAL_FILL"
    ORDER_STATE_CONFLICT = "ORDER_STATE_CONFLICT"
    POSITION_STATE_CONFLICT = "POSITION_STATE_CONFLICT"
    INSTRUMENT_EXPIRY = "INSTRUMENT_EXPIRY"
    UNKNOWN_REMOTE_STATE = "UNKNOWN_REMOTE_STATE"


class ReconciliationResult(str, Enum):
    RECONCILED = "reconciled"
    PARTIAL = "partial"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class SettlementState(str, Enum):
    ACTIVE = "ACTIVE"
    APPROACHING_EXPIRY = "APPROACHING_EXPIRY"
    SETTLING = "SETTLING"
    SETTLED = "SETTLED"
    UNKNOWN = "UNKNOWN"


_TERMINAL_ORDER_STATES: frozenset[NormalizedOrderState] = frozenset(
    {
        NormalizedOrderState.FILLED,
        NormalizedOrderState.CANCELED,
        NormalizedOrderState.REJECTED,
        NormalizedOrderState.EXPIRED,
    }
)

_ALLOWED_ORDER_TRANSITIONS: dict[NormalizedOrderState, frozenset[NormalizedOrderState]] = {
    NormalizedOrderState.LOCAL_INTENT_CREATED: frozenset({NormalizedOrderState.REQUEST_PREPARED}),
    NormalizedOrderState.REQUEST_PREPARED: frozenset({NormalizedOrderState.REQUEST_SENT}),
    NormalizedOrderState.REQUEST_SENT: frozenset(
        {
            NormalizedOrderState.ACKNOWLEDGED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
            NormalizedOrderState.REJECTED,
        }
    ),
    NormalizedOrderState.ACKNOWLEDGED: frozenset(
        {
            NormalizedOrderState.LIVE,
            NormalizedOrderState.PARTIALLY_FILLED,
            NormalizedOrderState.FILLED,
            NormalizedOrderState.REJECTED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        }
    ),
    NormalizedOrderState.LIVE: frozenset(
        {
            NormalizedOrderState.PARTIALLY_FILLED,
            NormalizedOrderState.FILLED,
            NormalizedOrderState.CANCEL_PENDING,
            NormalizedOrderState.CANCELED,
            NormalizedOrderState.EXPIRED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        }
    ),
    NormalizedOrderState.PARTIALLY_FILLED: frozenset(
        {
            NormalizedOrderState.PARTIALLY_FILLED,
            NormalizedOrderState.FILLED,
            NormalizedOrderState.CANCEL_PENDING,
            NormalizedOrderState.CANCELED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        }
    ),
    NormalizedOrderState.CANCEL_PENDING: frozenset(
        {
            NormalizedOrderState.PARTIALLY_FILLED,
            NormalizedOrderState.CANCELED,
            NormalizedOrderState.FILLED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        }
    ),
    NormalizedOrderState.UNKNOWN_REMOTE_STATE: frozenset(
        {
            NormalizedOrderState.LIVE,
            NormalizedOrderState.PARTIALLY_FILLED,
            NormalizedOrderState.FILLED,
            NormalizedOrderState.CANCELED,
            NormalizedOrderState.REJECTED,
            NormalizedOrderState.EXPIRED,
            NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        }
    ),
}


@dataclass(frozen=True)
class AuthCapabilityContract:
    capability_name: AuthCapabilityKind
    authentication_required: bool
    api_key_reference_required: bool
    passphrase_reference_required: bool
    secret_reference_required: bool
    timestamp_required: bool
    signature_required: bool
    simulated_trading_header_required: bool
    rest_supported: bool
    private_websocket_supported: bool
    order_authority: bool
    account_read_authority: bool
    runtime_go_required: bool


@dataclass(frozen=True)
class ClientOrderIdContract:
    client_order_id: str
    run_id: str
    session_id: str
    intent_id: str
    venue: str
    environment: str
    instrument_id: str
    uniqueness_scope: str
    maximum_length: int
    allowed_character_contract: str
    deterministic_derivation: bool
    reusable_after_terminal_state: bool
    resend_allowed: bool
    reconciliation_required_before_resend: bool


@dataclass(frozen=True)
class CancelStateContract:
    cancel_requested: bool
    cancel_acknowledged: bool
    canceled_confirmed: bool
    cancel_by_exchange_order_id: str | None
    cancel_by_client_order_id: str | None
    order_state_before_cancel: NormalizedOrderState
    order_state_after_cancel: NormalizedOrderState
    concurrent_fill_detected: bool
    reconciliation_required: bool
    final_state_confirmed: bool


@dataclass(frozen=True)
class NormalizedFill:
    exchange_fill_id: str
    exchange_order_id: str
    client_order_id: str
    instrument_id: str
    fill_timestamp: str
    fill_price: float
    fill_size: float
    fee: float | None
    fee_asset: str | None
    liquidity_role: str | None
    cumulative_filled_size: float
    remaining_size: float
    normalized_order_state_after_fill: NormalizedOrderState


@dataclass(frozen=True)
class NormalizedPosition:
    instrument_id: str
    environment: str
    position_mode: str
    margin_mode: str
    position_size: float
    average_entry_price: float | None
    mark_price: float | None
    unrealized_pnl: float | None
    realized_pnl: float | None
    liquidation_price: float | None
    margin: float | None
    leverage_reported: float
    effective_operational_leverage_cap: float
    funding_state: str | None
    expiry: str
    settlement_state: SettlementState
    source_timestamp: str | None
    normalized_position_state: str
    instrument_type: str
    rule_type: str
    has_fixed_expiry: bool
    has_funding_mechanism: bool
    is_classic_perpetual_swap: bool


@dataclass(frozen=True)
class ReconciliationPolicy:
    trigger: ReconciliationTrigger
    authoritative_source: str
    secondary_source: str
    required_identifiers: tuple[str, ...]
    retry_allowed: bool
    retry_limit: int
    reconciliation_required: bool
    fail_closed_state: NormalizedOrderState | None
    promotion_allowed: bool
    operator_escalation_required: bool
    durable_evidence_required: bool


@dataclass(frozen=True)
class DurableEvidenceRecord:
    run_id: str
    session_id: str
    intent_id: str
    client_order_id: str
    exchange_order_id: str | None
    instrument_id: str
    environment: str
    venue: str
    regulatory_entity: str
    request_timestamp: str
    exchange_timestamp: str | None
    receive_timestamp: str
    order_state_before: str
    order_state_after: str
    position_state_before: Mapping[str, Any] | None
    position_state_after: Mapping[str, Any] | None
    reconciliation_reason: str | None
    reconciliation_result: ReconciliationResult
    source_endpoint: str | None
    source_channel: str | None
    retry_count: int
    rate_limit_state: str
    credential_scope_used: str
    secret_redaction_proven: bool
    production_demo_separation_proven: bool
    runtime_go_token: str | None
    operator_identity: str


def default_auth_capability(kind: AuthCapabilityKind) -> AuthCapabilityContract:
    if kind == AuthCapabilityKind.PUBLIC_CAPABILITY:
        return AuthCapabilityContract(
            capability_name=kind,
            authentication_required=False,
            api_key_reference_required=False,
            passphrase_reference_required=False,
            secret_reference_required=False,
            timestamp_required=False,
            signature_required=False,
            simulated_trading_header_required=False,
            rest_supported=True,
            private_websocket_supported=False,
            order_authority=False,
            account_read_authority=False,
            runtime_go_required=False,
        )
    if kind == AuthCapabilityKind.READONLY_PRIVATE_CAPABILITY:
        return AuthCapabilityContract(
            capability_name=kind,
            authentication_required=True,
            api_key_reference_required=True,
            passphrase_reference_required=True,
            secret_reference_required=True,
            timestamp_required=True,
            signature_required=True,
            simulated_trading_header_required=True,
            rest_supported=True,
            private_websocket_supported=True,
            order_authority=False,
            account_read_authority=True,
            runtime_go_required=False,
        )
    return AuthCapabilityContract(
        capability_name=AuthCapabilityKind.TRADE_CAPABILITY,
        authentication_required=True,
        api_key_reference_required=True,
        passphrase_reference_required=True,
        secret_reference_required=True,
        timestamp_required=True,
        signature_required=True,
        simulated_trading_header_required=True,
        rest_supported=True,
        private_websocket_supported=True,
        order_authority=True,
        account_read_authority=True,
        runtime_go_required=False,
    )


def validate_auth_capability(contract: AuthCapabilityContract) -> list[str]:
    reasons: list[str] = []
    if contract.runtime_go_required or RUNTIME_GO_READY:
        reasons.append("runtime_go_required must remain false")
    if contract.capability_name == AuthCapabilityKind.PUBLIC_CAPABILITY:
        if contract.authentication_required:
            reasons.append("PUBLIC_CAPABILITY must not require authentication")
        if (
            contract.api_key_reference_required
            or contract.secret_reference_required
            or contract.passphrase_reference_required
        ):
            reasons.append("PUBLIC_CAPABILITY must not require credential references")
        if contract.order_authority or contract.account_read_authority:
            reasons.append("PUBLIC_CAPABILITY must not grant private authority")
    if contract.capability_name == AuthCapabilityKind.READONLY_PRIVATE_CAPABILITY:
        if contract.order_authority:
            reasons.append("READONLY_PRIVATE_CAPABILITY must not grant order authority")
        if not contract.account_read_authority:
            reasons.append("READONLY_PRIVATE_CAPABILITY requires account_read_authority")
    if contract.capability_name == AuthCapabilityKind.TRADE_CAPABILITY:
        if not contract.order_authority:
            reasons.append("TRADE_CAPABILITY requires order_authority flag")
        if contract.runtime_go_required:
            reasons.append("TRADE_CAPABILITY must not imply runtime GO")
    return reasons


def environment_namespace(environment: str) -> str:
    normalized = environment.strip().lower()
    if normalized in {"production", "prod", "live"}:
        return "prod"
    if normalized in {"shadow", "paper", "testnet", "demo"}:
        return "demo"
    return normalized or "unknown"


def build_client_order_id(
    *,
    run_id: str,
    session_id: str,
    intent_id: str,
    environment: str,
    instrument_id: str,
    sequence: int = 0,
) -> str:
    run_short = re.sub(r"[^a-f0-9]", "", run_id.lower())[:8] or "00000000"
    intent_short = re.sub(r"[^a-f0-9]", "", intent_id.lower())[:8] or "00000000"
    env_ns = environment_namespace(environment)
    seq = format(sequence, "02x")[-2:]
    candidate = f"ptokxe{env_ns}{run_short}{intent_short}{seq}"
    if len(candidate) > CLIENT_ORDER_ID_MAX_LENGTH:
        overflow = len(candidate) - CLIENT_ORDER_ID_MAX_LENGTH
        candidate = candidate[overflow:]
    return candidate[:CLIENT_ORDER_ID_MAX_LENGTH]


def validate_client_order_id_contract(contract: ClientOrderIdContract) -> list[str]:
    reasons: list[str] = []
    if not contract.client_order_id:
        reasons.append("client_order_id required")
    if len(contract.client_order_id) > CLIENT_ORDER_ID_MAX_LENGTH:
        reasons.append("client_order_id exceeds maximum_length")
    if not CLIENT_ORDER_ID_ALLOWED_PATTERN.match(contract.client_order_id):
        reasons.append("client_order_id violates allowed_character_contract")
    if not contract.run_id or not contract.session_id or not contract.intent_id:
        reasons.append("run_id, session_id, and intent_id required")
    if contract.venue != VENUE_OKX_EUROPE:
        reasons.append(f"venue must be {VENUE_OKX_EUROPE!r}")
    if contract.resend_allowed and contract.reconciliation_required_before_resend is False:
        reasons.append("resend requires reconciliation_required_before_resend")
    if contract.reusable_after_terminal_state:
        reasons.append("client_order_id must not be reusable_after_terminal_state")
    prod_env = environment_namespace(contract.environment) == "prod"
    demo_inst = contract.instrument_id == DEMO_REFERENCE_INSTRUMENT_ID
    prod_inst = contract.instrument_id == PRODUCTION_INSTRUMENT_ID
    if prod_env and demo_inst:
        reasons.append("production environment must not use demo instrument_id namespace")
    if not prod_env and prod_inst:
        reasons.append("non-production environment must not use production instrument_id")
    return reasons


def normalize_okx_order_state(raw_state: str) -> NormalizedOrderState:
    normalized = raw_state.strip().lower()
    if not normalized or normalized not in OKX_DOCUMENTED_ORDER_STATES:
        return NormalizedOrderState.UNKNOWN_REMOTE_STATE
    mapping = {
        "live": NormalizedOrderState.LIVE,
        "partially_filled": NormalizedOrderState.PARTIALLY_FILLED,
        "filled": NormalizedOrderState.FILLED,
        "canceled": NormalizedOrderState.CANCELED,
        "mmp_canceled": NormalizedOrderState.CANCELED,
    }
    return mapping[normalized]


def validate_order_state_transition(
    before: NormalizedOrderState,
    after: NormalizedOrderState,
) -> list[str]:
    if before == after:
        return []
    allowed = _ALLOWED_ORDER_TRANSITIONS.get(before, frozenset())
    if after not in allowed:
        return [f"transition {before.value} -> {after.value} not allowed"]
    if before == NormalizedOrderState.UNKNOWN_REMOTE_STATE and after in {
        NormalizedOrderState.REQUEST_SENT,
        NormalizedOrderState.REQUEST_PREPARED,
        NormalizedOrderState.LOCAL_INTENT_CREATED,
    }:
        return ["UNKNOWN_REMOTE_STATE cannot authorize new local intent without reconciliation"]
    return []


def validate_cancel_state(contract: CancelStateContract) -> list[str]:
    reasons: list[str] = []
    if contract.cancel_acknowledged and not contract.reconciliation_required:
        reasons.append("cancel_acknowledged requires reconciliation_required")
    if contract.cancel_acknowledged and not contract.canceled_confirmed:
        if contract.final_state_confirmed:
            reasons.append("CANCEL_ACK cannot set final_state_confirmed without canceled_confirmed")
        if contract.order_state_after_cancel == NormalizedOrderState.CANCELED:
            reasons.append("CANCEL_ACK alone must not set order_state_after_cancel to CANCELED")
    if contract.canceled_confirmed:
        if contract.order_state_after_cancel not in {
            NormalizedOrderState.CANCELED,
            NormalizedOrderState.FILLED,
        }:
            reasons.append("canceled_confirmed requires terminal canceled or filled state")
        if not contract.final_state_confirmed:
            reasons.append("canceled_confirmed requires final_state_confirmed")
    if (
        contract.cancel_requested
        and not contract.cancel_by_exchange_order_id
        and not contract.cancel_by_client_order_id
    ):
        reasons.append("cancel request requires exchange or client order identifier")
    return reasons


def cancel_ack_implies_canceled_confirmed(contract: CancelStateContract) -> bool:
    """True when cancel ACK is incorrectly treated as terminal cancel confirmation."""
    return (
        contract.cancel_acknowledged
        and not contract.canceled_confirmed
        and (
            contract.final_state_confirmed
            or contract.order_state_after_cancel == NormalizedOrderState.CANCELED
        )
    )


def validate_fill(fill: NormalizedFill) -> list[str]:
    reasons: list[str] = []
    if fill.fill_size < 0:
        reasons.append("fill_size must not be negative")
    if fill.cumulative_filled_size < 0:
        reasons.append("cumulative_filled_size must not be negative")
    if fill.remaining_size < 0:
        reasons.append("remaining_size must not be negative")
    if fill.cumulative_filled_size < fill.fill_size:
        reasons.append("cumulative_filled_size must be >= fill_size for single fill event")
    total = fill.cumulative_filled_size + fill.remaining_size
    if (
        fill.normalized_order_state_after_fill == NormalizedOrderState.FILLED
        and fill.remaining_size != 0
    ):
        reasons.append("FILLED state requires remaining_size == 0")
    if (
        fill.normalized_order_state_after_fill == NormalizedOrderState.PARTIALLY_FILLED
        and fill.remaining_size == 0
    ):
        reasons.append("PARTIALLY_FILLED requires remaining_size > 0")
    if total <= 0 and fill.fill_size > 0:
        reasons.append("fill quantity inconsistency")
    return reasons


def _instrument_forbidden(instrument_id: str, instrument_type: str) -> list[str]:
    reasons: list[str] = []
    upper = instrument_id.upper()
    if any(fragment in upper for fragment in _BITCOIN_FRAGMENTS):
        reasons.append("bitcoin-direction instrument forbidden")
    if instrument_type.upper() in _FORBIDDEN_SPOT_MARKERS:
        reasons.append(f"instrument_type {instrument_type!r} forbidden for X-Perp contract")
    if "SPOT" in upper and "XPERP" not in upper:
        reasons.append("spot instrument forbidden")
    return reasons


def validate_position(position: NormalizedPosition, *, environment: str) -> list[str]:
    reasons: list[str] = []
    reasons.extend(_instrument_forbidden(position.instrument_id, position.instrument_type))
    if position.instrument_type != PRODUCTION_INSTRUMENT_TYPE:
        reasons.append(f"instrument_type must be {PRODUCTION_INSTRUMENT_TYPE!r}")
    if position.rule_type != PRODUCTION_RULE_TYPE:
        reasons.append(f"rule_type must be {PRODUCTION_RULE_TYPE!r}")
    if not position.has_fixed_expiry:
        reasons.append("has_fixed_expiry must be true")
    if not position.has_funding_mechanism:
        reasons.append("has_funding_mechanism must be true")
    if position.is_classic_perpetual_swap:
        reasons.append("is_classic_perpetual_swap must be false")
    if position.effective_operational_leverage_cap > REGULATORY_MAX_RETAIL_LEVERAGE:
        reasons.append("effective_operational_leverage_cap exceeds retail limit")
    if position.leverage_reported == VENUE_REPORTED_LEVERAGE_CAPABILITY:
        if position.effective_operational_leverage_cap != REGULATORY_MAX_RETAIL_LEVERAGE:
            reasons.append("venue leverage 50 must not raise operative cap above 10")
    prod_active = environment_namespace(environment) == "prod"
    if not prod_active and position.instrument_id == PRODUCTION_INSTRUMENT_ID:
        reasons.append("production instrument forbidden in non-production environment")
    if position.settlement_state == SettlementState.SETTLED and position.position_size != 0:
        reasons.append("SETTLED requires flat position")
    return reasons


def default_xperp_demo_position(*, environment: str = "testnet") -> NormalizedPosition:
    leverage = LeverageSemantics(
        venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
        regulatory_retail_leverage_limit=REGULATORY_MAX_RETAIL_LEVERAGE,
        runtime_leverage=None,
        runtime_leverage_authorized=False,
    )
    return NormalizedPosition(
        instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        environment=environment,
        position_mode="net",
        margin_mode="isolated",
        position_size=0.0,
        average_entry_price=None,
        mark_price=None,
        unrealized_pnl=None,
        realized_pnl=None,
        liquidation_price=None,
        margin=None,
        leverage_reported=VENUE_REPORTED_LEVERAGE_CAPABILITY,
        effective_operational_leverage_cap=effective_operational_leverage_cap(leverage),
        funding_state="accruing",
        expiry="2031-03-28",
        settlement_state=SettlementState.ACTIVE,
        source_timestamp=None,
        normalized_position_state="flat",
        instrument_type=PRODUCTION_INSTRUMENT_TYPE,
        rule_type=PRODUCTION_RULE_TYPE,
        has_fixed_expiry=True,
        has_funding_mechanism=True,
        is_classic_perpetual_swap=False,
    )


_RECONCILIATION_POLICIES: dict[ReconciliationTrigger, ReconciliationPolicy] = {
    ReconciliationTrigger.STARTUP: ReconciliationPolicy(
        trigger=ReconciliationTrigger.STARTUP,
        authoritative_source="GET /api/v5/trade/orders-pending",
        secondary_source="GET /api/v5/account/positions",
        required_identifiers=("instId", "clOrdId", "ordId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.ORDER_REQUEST_TIMEOUT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.ORDER_REQUEST_TIMEOUT,
        authoritative_source="GET /api/v5/trade/order",
        secondary_source="GET /api/v5/trade/orders-pending",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.CANCEL_REQUEST_TIMEOUT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.CANCEL_REQUEST_TIMEOUT,
        authoritative_source="GET /api/v5/trade/order",
        secondary_source="WS orders channel",
        required_identifiers=("instId", "ordId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.WEBSOCKET_DISCONNECT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.WEBSOCKET_DISCONNECT,
        authoritative_source="GET /api/v5/trade/orders-pending",
        secondary_source="GET /api/v5/trade/fills",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.PROCESS_RESTART: ReconciliationPolicy(
        trigger=ReconciliationTrigger.PROCESS_RESTART,
        authoritative_source="durable evidence clOrdId map",
        secondary_source="GET /api/v5/trade/orders-pending",
        required_identifiers=("run_id", "session_id", "clOrdId"),
        retry_allowed=True,
        retry_limit=1,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.AWS_TASK_RESTART: ReconciliationPolicy(
        trigger=ReconciliationTrigger.AWS_TASK_RESTART,
        authoritative_source="durable evidence clOrdId map",
        secondary_source="GET /api/v5/trade/orders-pending",
        required_identifiers=("run_id", "session_id", "clOrdId"),
        retry_allowed=True,
        retry_limit=1,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.RATE_LIMIT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.RATE_LIMIT,
        authoritative_source="rate_limit_state",
        secondary_source="GET /api/v5/public/time",
        required_identifiers=(),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=False,
        fail_closed_state=None,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.CLOCK_DRIFT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.CLOCK_DRIFT,
        authoritative_source="GET /api/v5/public/time",
        secondary_source="",
        required_identifiers=(),
        retry_allowed=False,
        retry_limit=0,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.INSTRUMENT_EXPIRY: ReconciliationPolicy(
        trigger=ReconciliationTrigger.INSTRUMENT_EXPIRY,
        authoritative_source="GET /api/v5/public/instruments",
        secondary_source="GET /api/v5/account/positions",
        required_identifiers=("instId",),
        retry_allowed=False,
        retry_limit=0,
        reconciliation_required=True,
        fail_closed_state=None,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.UNKNOWN_REMOTE_STATE: ReconciliationPolicy(
        trigger=ReconciliationTrigger.UNKNOWN_REMOTE_STATE,
        authoritative_source="GET /api/v5/trade/order",
        secondary_source="GET /api/v5/trade/orders-history",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.ORDER_STATE_CONFLICT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.ORDER_STATE_CONFLICT,
        authoritative_source="GET /api/v5/trade/order (newer uTime)",
        secondary_source="GET /api/v5/trade/fills",
        required_identifiers=("ordId", "clOrdId"),
        retry_allowed=False,
        retry_limit=0,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.POSITION_STATE_CONFLICT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.POSITION_STATE_CONFLICT,
        authoritative_source="GET /api/v5/account/positions",
        secondary_source="GET /api/v5/trade/fills",
        required_identifiers=("instId", "posId"),
        retry_allowed=False,
        retry_limit=0,
        reconciliation_required=True,
        fail_closed_state=None,
        promotion_allowed=False,
        operator_escalation_required=True,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.PARTIAL_FILL: ReconciliationPolicy(
        trigger=ReconciliationTrigger.PARTIAL_FILL,
        authoritative_source="GET /api/v5/trade/fills",
        secondary_source="WS orders channel",
        required_identifiers=("ordId", "tradeId"),
        retry_allowed=True,
        retry_limit=1,
        reconciliation_required=True,
        fail_closed_state=None,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.NORMAL_POLL: ReconciliationPolicy(
        trigger=ReconciliationTrigger.NORMAL_POLL,
        authoritative_source="GET /api/v5/trade/order",
        secondary_source="WS orders channel",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=1,
        reconciliation_required=False,
        fail_closed_state=None,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=False,
    ),
    ReconciliationTrigger.REST_TIMEOUT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.REST_TIMEOUT,
        authoritative_source="GET /api/v5/trade/order",
        secondary_source="GET /api/v5/trade/orders-pending",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
    ReconciliationTrigger.RECONNECT: ReconciliationPolicy(
        trigger=ReconciliationTrigger.RECONNECT,
        authoritative_source="GET /api/v5/trade/orders-pending",
        secondary_source="WS orders channel after re-login",
        required_identifiers=("instId", "clOrdId"),
        retry_allowed=True,
        retry_limit=3,
        reconciliation_required=True,
        fail_closed_state=NormalizedOrderState.UNKNOWN_REMOTE_STATE,
        promotion_allowed=False,
        operator_escalation_required=False,
        durable_evidence_required=True,
    ),
}


def get_reconciliation_policy(trigger: ReconciliationTrigger) -> ReconciliationPolicy:
    policy = _RECONCILIATION_POLICIES.get(trigger)
    if policy is None:
        raise ValueError(f"unsupported reconciliation trigger: {trigger}")
    return policy


def validate_reconciliation_policy(policy: ReconciliationPolicy) -> list[str]:
    reasons: list[str] = []
    if policy.trigger == ReconciliationTrigger.UNKNOWN_REMOTE_STATE and policy.promotion_allowed:
        reasons.append("UNKNOWN_REMOTE_STATE must have promotion_allowed=false")
    if (
        policy.trigger
        in {
            ReconciliationTrigger.ORDER_REQUEST_TIMEOUT,
            ReconciliationTrigger.CANCEL_REQUEST_TIMEOUT,
        }
        and not policy.reconciliation_required
    ):
        reasons.append(f"{policy.trigger.value} requires reconciliation_required=true")
    if policy.retry_limit < 0 or (
        policy.retry_limit > 5 and policy.trigger != ReconciliationTrigger.RATE_LIMIT
    ):
        reasons.append("unbounded retry limit")
    if policy.trigger == ReconciliationTrigger.CLOCK_DRIFT and policy.retry_allowed:
        reasons.append("CLOCK_DRIFT must not allow mutating retry")
    if policy.trigger in {
        ReconciliationTrigger.PROCESS_RESTART,
        ReconciliationTrigger.AWS_TASK_RESTART,
    }:
        if (
            "run_id" not in policy.required_identifiers
            or "session_id" not in policy.required_identifiers
        ):
            reasons.append("restart triggers require durable run_id and session_id")
    if policy.trigger == ReconciliationTrigger.INSTRUMENT_EXPIRY and policy.promotion_allowed:
        reasons.append("INSTRUMENT_EXPIRY must not allow promotion")
    return reasons


def validate_durable_evidence(record: DurableEvidenceRecord) -> list[str]:
    reasons: list[str] = []
    if not record.secret_redaction_proven:
        reasons.append("secret_redaction_proven must be true")
    if not record.production_demo_separation_proven:
        reasons.append("production_demo_separation_proven must be true")
    if record.runtime_go_token:
        reasons.append("runtime_go_token must not be set for offline contracts")
    if not record.run_id or not record.session_id or not record.intent_id:
        reasons.append("run_id, session_id, intent_id required")
    if record.venue != VENUE_OKX_EUROPE:
        reasons.append(f"venue must be {VENUE_OKX_EUROPE!r}")
    if record.regulatory_entity != REGULATORY_ENTITY_OKX_EUROPE_MARKETS:
        reasons.append("regulatory_entity mismatch")
    payload = {
        "run_id": record.run_id,
        "client_order_id": record.client_order_id,
        "credential_scope_used": record.credential_scope_used,
    }
    for key in payload:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            reasons.append(f"forbidden key {key}")
    for forbidden in FORBIDDEN_SERIALIZATION_KEYS:
        if forbidden in str(record.client_order_id).lower():
            continue
    return reasons


def reject_secret_payload(payload: Mapping[str, Any]) -> list[str]:
    return [
        f"forbidden key {key!r}" for key in payload if key.lower() in FORBIDDEN_SERIALIZATION_KEYS
    ]


def allows_automatic_order_resend(state: NormalizedOrderState) -> bool:
    return state != NormalizedOrderState.UNKNOWN_REMOTE_STATE and AUTOMATIC_ORDER_RESEND_ALLOWED


def evaluate_offline_contract_invariants() -> dict[str, Any]:
    """Aggregate offline invariant self-check (no I/O)."""
    fail_reasons: list[str] = []
    for kind in AuthCapabilityKind:
        fail_reasons.extend(validate_auth_capability(default_auth_capability(kind)))
    for trigger in ReconciliationTrigger:
        fail_reasons.extend(validate_reconciliation_policy(get_reconciliation_policy(trigger)))
    demo_pos = default_xperp_demo_position()
    fail_reasons.extend(validate_position(demo_pos, environment="testnet"))
    return {
        "contract_pass": not fail_reasons,
        "fail_reasons": fail_reasons,
        "runtime_go_ready": RUNTIME_GO_READY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "unknown_remote_state_fail_closed": UNKNOWN_REMOTE_STATE_FAIL_CLOSED,
        "automatic_order_resend_allowed": AUTOMATIC_ORDER_RESEND_ALLOWED,
        "automatic_instrument_rollover_allowed": AUTOMATIC_INSTRUMENT_ROLLOVER_ALLOWED,
        "simulation_header_name": SIMULATION_HEADER_NAME,
        "contract_version": CONTRACT_VERSION,
    }


def assert_contract_inert() -> None:
    if RUNTIME_GO_READY or RUNTIME_EXECUTED or PROMOTION_ALLOWED:
        raise RuntimeError("OKX Europe adapter lifecycle contract must remain offline-inert")
    if ORDER_ATTEMPT_COUNT or CANCEL_ATTEMPT_COUNT or NETWORK_CALL_COUNT:
        raise RuntimeError("OKX Europe adapter lifecycle contract must not perform I/O")
