"""
Execution Pipeline Orchestrator (WP0A - Phase 0 Foundation)

Implements the 8-stage execution pipeline from Intent to Recon Hand-off.

Pipeline Stages:
1. Intent Intake - Receive trading decision from strategy
2. Contract Validation - Validate order against WP0E invariants
3. Pre-Trade Risk Gate - Risk evaluation via RiskHook
4. Route Selection - Select adapter based on execution mode (paper/shadow/testnet/live_blocked)
5. Adapter Dispatch - Execute order via selected adapter
6. Execution Event Handling - Process ACK/REJECT/FILL events
7. Post-Trade Hooks - Update ledgers, emit events
8. Recon Hand-off - Prepare data for reconciliation

Design Goals:
- Stage sequencing with clear boundaries
- Correlation tracking (correlation_id stable across all stages)
- Idempotency enforcement (idempotency_key prevents duplicate processing)
- Stop criteria enforcement (BLOCK → halt, TIMEOUT → controlled failure)
- No live enablement (default blocked/gated)
- Deterministic audit trail

IMPORTANT: NO live execution. Default remains blocked/gated.
           All live routing raises GovernanceViolationError.
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from datetime import timezone
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from decimal import Decimal
import hashlib

from src.execution.contracts import (
    Order,
    OrderState,
    OrderSide,
    OrderType,
    TimeInForce,
    Fill,
    LedgerEntry,
    RiskResult,
    RiskDecision,
    validate_order,
)
from src.execution.risk_hook import RiskHook, NullRiskHook
from src.execution.order_state_machine import OrderStateMachine, StateMachineResult
from src.execution.order_ledger import OrderLedger
from src.execution.position_ledger import PositionLedger
from src.execution.audit_log import AuditLog
from src.execution.retry_policy import RetryPolicy, RetryConfig
from src.execution.ledger_mapper import EventToLedgerMapper
from src.execution.reconciliation import ReconciliationEngine
from src.execution.determinism import SimClock, seed_u64, stable_id
from src.execution.telemetry import FixedJsonlAppendOnlyWriter

logger = logging.getLogger(__name__)


# ============================================================================
# Execution Mode & Reason Codes
# ============================================================================


class ExecutionMode(str, Enum):
    """
    Execution mode for pipeline routing.

    Values:
        PAPER: Paper trading (simulated)
        SHADOW: Shadow mode (dry-run, no real execution)
        TESTNET: Testnet orders (sandbox environment)
        LIVE_BLOCKED: Live mode (BLOCKED by governance - Phase 0 default)
    """

    PAPER = "paper"
    SHADOW = "shadow"
    TESTNET = "testnet"
    LIVE_BLOCKED = "live_blocked"


class ReasonCode(str, Enum):
    """
    Standardized reason codes for pipeline decisions.

    Categories:
    - VALIDATION_*: Contract validation failures
    - RISK_*: Risk gate blocks
    - POLICY_*: Governance/policy blocks
    - ADAPTER_*: Adapter execution failures
    - TIMEOUT_*: Timeout failures
    """

    # Validation
    VALIDATION_INVALID_QUANTITY = "VALIDATION_INVALID_QUANTITY"
    VALIDATION_INVALID_PRICE = "VALIDATION_INVALID_PRICE"
    VALIDATION_INVALID_SYMBOL = "VALIDATION_INVALID_SYMBOL"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"

    # Risk
    RISK_LIMIT_EXCEEDED = "RISK_LIMIT_EXCEEDED"
    RISK_KILL_SWITCH_ACTIVE = "RISK_KILL_SWITCH_ACTIVE"
    RISK_EVALUATION_FAILED = "RISK_EVALUATION_FAILED"
    RISK_BLOCKED = "RISK_BLOCKED"

    # Policy/Governance
    POLICY_BLOCKED = "POLICY_BLOCKED"
    POLICY_LIVE_NOT_ENABLED = "POLICY_LIVE_NOT_ENABLED"
    POLICY_NO_EXECUTOR = "POLICY_NO_EXECUTOR"

    # Adapter
    ADAPTER_REJECTED = "ADAPTER_REJECTED"
    ADAPTER_TIMEOUT = "ADAPTER_TIMEOUT"
    ADAPTER_ERROR = "ADAPTER_ERROR"

    # Timeout
    TIMEOUT_SUBMISSION = "TIMEOUT_SUBMISSION"
    TIMEOUT_ACKNOWLEDGMENT = "TIMEOUT_ACKNOWLEDGMENT"


# ============================================================================
# Intent & Pipeline Result
# ============================================================================


@dataclass
class OrderIntent:
    """
    Order intent (trading decision before order creation).

    Represents strategy/operator intention before validation and risk checks.

    Attributes:
        symbol: Trading symbol (e.g., "BTC/EUR")
        side: Order side (BUY/SELL)
        quantity: Order quantity (Decimal)
        order_type: Order type (MARKET/LIMIT)
        limit_price: Limit price (required if LIMIT)
        strategy_id: Strategy identifier
        metadata: Additional metadata
    """

    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[Decimal] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    strategy_id: Optional[str] = None
    session_id: Optional[str] = None
    # RUNBOOK B (Slice 1): Optional stable identifiers
    run_id: Optional[str] = None
    intent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """
    Result of pipeline execution.

    Attributes:
        success: True if order successfully processed
        order: Order object (may be in various states)
        reason_code: Reason code if blocked/failed
        reason_detail: Human-readable reason
        stage_reached: Last stage reached in pipeline
        correlation_id: Correlation ID for tracking
        idempotency_key: Idempotency key
        ledger_entries: Audit trail entries generated
        metadata: Additional metadata
    """

    success: bool
    order: Optional[Order] = None
    reason_code: Optional[ReasonCode] = None
    reason_detail: str = ""
    stage_reached: str = ""
    correlation_id: str = ""
    idempotency_key: str = ""
    ledger_entries: List[LedgerEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Adapter Protocol (WP0C placeholder)
# ============================================================================


class OrderAdapter(Protocol):
    """
    Protocol for order execution adapters (WP0C).

    Adapters encapsulate external interaction (exchange API, paper simulation, etc.).
    """

    def execute_order(self, order: Order, idempotency_key: str) -> "ExecutionEvent":
        """
        Execute order and return execution event.

        Args:
            order: Order to execute
            idempotency_key: Idempotency key (prevents duplicate submission)

        Returns:
            ExecutionEvent (ACK/REJECT/FILL)
        """
        ...


@dataclass
class ExecutionEvent:
    """
    Execution event from adapter (ACK/REJECT/FILL/CANCEL_ACK).

    Attributes:
        event_type: Event type (ACK/REJECT/FILL/CANCEL_ACK)
        order_id: Client order ID
        exchange_order_id: Exchange order ID (if ACK)
        fill: Fill details (if FILL)
        reject_reason: Rejection reason (if REJECT)
        timestamp: Event timestamp
    """

    event_type: str  # ACK, REJECT, FILL, CANCEL_ACK
    order_id: str
    exchange_order_id: Optional[str] = None
    fill: Optional[Fill] = None
    reject_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Null Adapter (Default/Testing)
# ============================================================================


class NullAdapter:
    """
    Null adapter (no-op, for testing).

    Always returns ACK immediately (simulates instant execution).
    """

    def execute_order(self, order: Order, idempotency_key: str) -> ExecutionEvent:
        """Execute order (no-op, return ACK)"""
        return ExecutionEvent(
            event_type="ACK",
            order_id=order.client_order_id,
            exchange_order_id=f"null_exch_{order.client_order_id}",
        )


# ============================================================================
# Execution Pipeline Orchestrator
# ============================================================================


class ExecutionOrchestrator:
    """
    Execution pipeline orchestrator (WP0A - Phase 0).

    Orchestrates the 8-stage execution pipeline:
    1. Intent Intake
    2. Contract Validation
    3. Pre-Trade Risk Gate
    4. Route Selection
    5. Adapter Dispatch
    6. Execution Event Handling
    7. Post-Trade Hooks
    8. Recon Hand-off

    Features:
    - Stage sequencing with clear boundaries
    - Correlation tracking (correlation_id)
    - Idempotency enforcement (idempotency_key)
    - Stop criteria enforcement (BLOCK → halt)
    - Deterministic audit trail
    - No live enablement (default blocked)

    IMPORTANT: NO live execution. Default remains blocked/gated.
    """

    def __init__(
        self,
        risk_hook: Optional[RiskHook] = None,
        adapter: Optional[OrderAdapter] = None,
        adapter_registry: Optional[Any] = None,  # AdapterRegistry (avoid circular import)
        execution_mode: ExecutionMode = ExecutionMode.PAPER,
        retry_policy: Optional[RetryPolicy] = None,
        enable_audit: bool = True,
        *,
        # RUNBOOK B / Slice 1: Minimal risk rails (stubs, testable)
        kill_switch_active: bool = False,
        max_position_qty: Optional[Decimal] = None,
        # RUNBOOK B / Slice 1: Contract log
        execution_events_log_path: str = "logs/execution/execution_events.jsonl",
    ):
        """
        Initialize execution orchestrator.

        Args:
            risk_hook: Risk evaluation hook (defaults to NullRiskHook)
            adapter: Order execution adapter (defaults to NullAdapter)
                    Ignored if adapter_registry is provided.
            adapter_registry: Adapter registry for mode-based routing (WP0C)
                             If provided, adapters are selected via registry.get_adapter(mode).
                             If None, uses fixed adapter parameter (backwards compatible).
            execution_mode: Execution mode (paper/shadow/testnet/live_blocked)
            retry_policy: Retry policy for transient failures
            enable_audit: Enable audit log generation
        """
        # Components
        self.risk_hook = risk_hook or NullRiskHook()
        self.adapter = adapter or NullAdapter()
        self.adapter_registry = adapter_registry  # WP0C: Optional registry for mode-based routing
        self.execution_mode = execution_mode
        self.retry_policy = retry_policy or RetryPolicy(RetryConfig(max_retries=3))
        self.enable_audit = enable_audit

        # RUNBOOK B / Slice 1
        self.kill_switch_active = kill_switch_active
        self.max_position_qty = max_position_qty
        self._beta_log_writer = FixedJsonlAppendOnlyWriter(Path(execution_events_log_path))
        self._beta_clocks: Dict[tuple[str, str], SimClock] = {}
        self._beta_context: Optional[Dict[str, str]] = None
        self._beta_events: Optional[List[Dict[str, Any]]] = None

        # State machines & ledgers
        self.state_machine = OrderStateMachine(
            risk_hook=self.risk_hook,
            enable_audit=enable_audit,
        )
        self.order_ledger = OrderLedger()
        self.position_ledger = PositionLedger()
        self.audit_log = AuditLog()

        # WP0D: Ledger mapping & reconciliation
        self.ledger_mapper = EventToLedgerMapper()
        self.recon_engine = ReconciliationEngine(
            position_ledger=self.position_ledger,
            order_ledger=self.order_ledger,
        )

        # Counters
        self._order_counter = 0

    # ============================================================================
    # RUNBOOK B / Slice 1: Deterministic event logging (execution_events.jsonl)
    # ============================================================================

    def _get_clock(self, run_id: str, session_id: str) -> SimClock:
        key = (run_id, session_id)
        if key not in self._beta_clocks:
            self._beta_clocks[key] = SimClock()
        return self._beta_clocks[key]

    def _emit_beta_event(
        self,
        *,
        run_id: str,
        session_id: str,
        intent_id: str,
        symbol: str,
        event_type: str,
        request_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        reason_code: Optional[str] = None,
        reason_detail: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clock = self._get_clock(run_id, session_id)
        ts_sim = clock.tick()

        payload = payload or {}

        canonical_fields = {
            "run_id": run_id,
            "session_id": session_id,
            "intent_id": intent_id,
            "symbol": symbol,
            "event_type": event_type,
            "ts_sim": ts_sim,
            "request_id": request_id,
            "client_order_id": client_order_id,
            "reason_code": reason_code,
            "payload": payload,
        }
        event_id = stable_id(kind="execution_event", fields=canonical_fields)

        obj: Dict[str, Any] = {
            "schema_version": "BETA_EXEC_V1",
            "event_id": event_id,
            "run_id": run_id,
            "session_id": session_id,
            "intent_id": intent_id,
            "symbol": symbol,
            "event_type": event_type,
            "ts_sim": ts_sim,
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "client_order_id": client_order_id,
            "reason_code": reason_code,
            "reason_detail": reason_detail,
            "payload": payload,
        }

        # Append-only write + in-memory capture for tests
        self._beta_log_writer.append(obj)
        if self._beta_events is not None:
            self._beta_events.append(obj)

        return obj

    def submit_intent(self, intent: OrderIntent) -> PipelineResult:
        """
        Submit order intent through the 8-stage pipeline.

        Pipeline stages:
        1. Intent Intake - Generate correlation_id, idempotency_key
        2. Contract Validation - Validate against WP0E invariants
        3. Pre-Trade Risk Gate - Risk evaluation via RiskHook
        4. Route Selection - Select adapter based on execution mode
        5. Adapter Dispatch - Execute order via adapter
        6. Execution Event Handling - Process ACK/REJECT/FILL
        7. Post-Trade Hooks - Update ledgers, emit events
        8. Recon Hand-off - Prepare data for reconciliation

        Args:
            intent: Order intent

        Returns:
            PipelineResult with success/failure and audit trail
        """
        # RUNBOOK B / Slice 1: resolve stable identifiers (no randomness)
        session_id = intent.session_id or "default"
        run_id = intent.run_id or session_id
        intent_id = intent.intent_id or stable_id(
            kind="intent",
            fields={
                "run_id": run_id,
                "session_id": session_id,
                "symbol": intent.symbol,
                "side": intent.side.value,
                "quantity": str(intent.quantity),
                "order_type": intent.order_type.value,
                "limit_price": str(intent.limit_price) if intent.limit_price is not None else None,
                "time_in_force": intent.time_in_force.value,
                "strategy_id": intent.strategy_id or None,
            },
        )

        beta_events: List[Dict[str, Any]] = []

        # Stage 1: Intent Intake (keep correlation_id as internal only)
        correlation_id = self._generate_correlation_id()
        idempotency_key = self._generate_idempotency_key(intent, run_id=run_id, session_id=session_id, intent_id=intent_id)

        logger.info(
            f"[STAGE 1: INTENT INTAKE] correlation_id={correlation_id}, "
            f"symbol={intent.symbol}, side={intent.side.value}, qty={intent.quantity}"
        )

        # RUNBOOK B / Slice 1: attach beta context for downstream stages
        self._beta_context = {"run_id": run_id, "session_id": session_id, "intent_id": intent_id}
        self._beta_events = beta_events
        try:
            # Emit INTENT event (always first)
            self._emit_beta_event(
                run_id=run_id,
                session_id=session_id,
                intent_id=intent_id,
                symbol=intent.symbol,
                event_type="INTENT",
                payload={
                    "side": intent.side.value,
                    "quantity": str(intent.quantity),
                    "order_type": intent.order_type.value,
                    "limit_price": str(intent.limit_price) if intent.limit_price is not None else None,
                },
            )

            if self.kill_switch_active:
                self._emit_beta_event(
                    run_id=run_id,
                    session_id=session_id,
                    intent_id=intent_id,
                    symbol=intent.symbol,
                    event_type="RISK_REJECT",
                    reason_code="RISK_REJECT_KILL_SWITCH",
                    reason_detail="kill switch active",
                )
                return PipelineResult(
                    success=False,
                    order=None,
                    reason_code=ReasonCode.RISK_KILL_SWITCH_ACTIVE,
                    reason_detail="Kill switch active",
                    stage_reached="STAGE_1_INTENT_INTAKE",
                    correlation_id=correlation_id,
                    idempotency_key=idempotency_key,
                    metadata={"beta_events": beta_events},
                )

            if self.max_position_qty is not None and abs(intent.quantity) > self.max_position_qty:
                self._emit_beta_event(
                    run_id=run_id,
                    session_id=session_id,
                    intent_id=intent_id,
                    symbol=intent.symbol,
                    event_type="RISK_REJECT",
                    reason_code="RISK_REJECT_MAX_POSITION",
                    reason_detail="max_position_qty exceeded",
                    payload={
                        "max_position_qty": str(self.max_position_qty),
                        "quantity": str(intent.quantity),
                    },
                )
                return PipelineResult(
                    success=False,
                    order=None,
                    reason_code=ReasonCode.RISK_LIMIT_EXCEEDED,
                    reason_detail="Max position exceeded",
                    stage_reached="STAGE_1_INTENT_INTAKE",
                    correlation_id=correlation_id,
                    idempotency_key=idempotency_key,
                    metadata={"beta_events": beta_events},
                )

            # Stage 2: Contract Validation
            validation_result = self._stage_2_contract_validation(intent, correlation_id)
            if not validation_result.success:
                validation_result.metadata.setdefault("beta_events", beta_events)
                return validation_result

            order = validation_result.order
            assert order is not None

            # Stage 3: Pre-Trade Risk Gate
            risk_result = self._stage_3_risk_gate(order, correlation_id)
            if not risk_result.success:
                risk_result.metadata.setdefault("beta_events", beta_events)
                return risk_result

            # Stage 4: Route Selection
            route_result = self._stage_4_route_selection(order, correlation_id)
            if not route_result.success:
                route_result.metadata.setdefault("beta_events", beta_events)
                return route_result

            # Stage 5: Adapter Dispatch
            dispatch_result = self._stage_5_adapter_dispatch(order, idempotency_key, correlation_id)
            if not dispatch_result.success:
                dispatch_result.metadata.setdefault("beta_events", beta_events)
                return dispatch_result

            execution_event = dispatch_result.metadata.get("execution_event")
            assert execution_event is not None

            # Stage 6: Execution Event Handling
            event_result = self._stage_6_event_handling(order, execution_event, correlation_id)
            if not event_result.success:
                event_result.metadata.setdefault("beta_events", beta_events)
                return event_result

            # Stage 7: Post-Trade Hooks (pass event_result metadata for fill info)
            post_trade_result = self._stage_7_post_trade_hooks(
                order, execution_event, correlation_id, event_result.metadata
            )
            if not post_trade_result.success:
                post_trade_result.metadata.setdefault("beta_events", beta_events)
                return post_trade_result

            # Stage 8: Recon Hand-off
            recon_result = self._stage_8_recon_handoff(order, correlation_id)
            recon_result.idempotency_key = idempotency_key  # Add idempotency_key to final result
            recon_result.metadata.setdefault("beta_events", beta_events)

            # Collect all ledger entries from all stages
            all_ledger_entries = []
            all_ledger_entries.extend(validation_result.ledger_entries)
            all_ledger_entries.extend(dispatch_result.ledger_entries)
            all_ledger_entries.extend(event_result.ledger_entries)
            recon_result.ledger_entries = all_ledger_entries

            logger.info(
                f"[PIPELINE COMPLETE] correlation_id={correlation_id}, "
                f"order_id={order.client_order_id}, state={order.state.value}"
            )

            return recon_result
        finally:
            self._beta_context = None
            self._beta_events = None

    def _stage_2_contract_validation(
        self, intent: OrderIntent, correlation_id: str
    ) -> PipelineResult:
        """
        Stage 2: Contract Validation.

        Validate order against WP0E invariants:
        - quantity > 0
        - LIMIT → limit_price set
        - symbol not empty
        - etc.

        Args:
            intent: Order intent
            correlation_id: Correlation ID

        Returns:
            PipelineResult
        """
        logger.info(f"[STAGE 2: CONTRACT VALIDATION] correlation_id={correlation_id}")

        beta = self._beta_context or {}
        run_id = beta.get("run_id", intent.run_id or intent.session_id or "default")
        session_id = beta.get("session_id", intent.session_id or "default")
        intent_id = beta.get("intent_id", intent.intent_id or "unknown")

        # Generate deterministic client_order_id (no uuid)
        self._order_counter += 1  # keep legacy counter semantics (not used for ID)
        client_order_id = f"order_{stable_id(kind='order', fields={'run_id': run_id, 'session_id': session_id, 'intent_id': intent_id})[:16]}"

        # Create order from intent
        order = Order(
            client_order_id=client_order_id,
            symbol=intent.symbol,
            side=intent.side,
            order_type=intent.order_type,
            quantity=intent.quantity,
            price=intent.limit_price,
            time_in_force=intent.time_in_force,
            state=OrderState.CREATED,
            strategy_id=intent.strategy_id,
            session_id=intent.session_id,
            metadata=intent.metadata,
        )

        # Validate order
        if not validate_order(order):
            reason_code = ReasonCode.VALIDATION_MISSING_FIELD
            reason_detail = "Order validation failed (check quantity, price, symbol)"

            if order.quantity <= 0:
                reason_code = ReasonCode.VALIDATION_INVALID_QUANTITY
                reason_detail = f"Invalid quantity: {order.quantity} (must be > 0)"
            elif order.order_type == OrderType.LIMIT and order.price is None:
                reason_code = ReasonCode.VALIDATION_INVALID_PRICE
                reason_detail = "LIMIT order requires limit_price"
            elif not order.symbol:
                reason_code = ReasonCode.VALIDATION_INVALID_SYMBOL
                reason_detail = "Symbol is required"

            logger.warning(
                f"[STAGE 2: VALIDATION FAILED] correlation_id={correlation_id}, "
                f"reason={reason_code.value}"
            )

            # RUNBOOK B / Slice 1: Emit validation reject (MVP mapping)
            beta = self._beta_context or {}
            if beta and reason_code == ReasonCode.VALIDATION_INVALID_QUANTITY:
                self._emit_beta_event(
                    run_id=beta["run_id"],
                    session_id=beta["session_id"],
                    intent_id=beta["intent_id"],
                    symbol=order.symbol or intent.symbol,
                    event_type="VALIDATION_REJECT",
                    client_order_id=order.client_order_id,
                    reason_code="VALIDATION_REJECT_BAD_QTY",
                    reason_detail="quantity must be > 0",
                    payload={"quantity": str(order.quantity)},
                )

            return PipelineResult(
                success=False,
                order=order,
                reason_code=reason_code,
                reason_detail=reason_detail,
                stage_reached="STAGE_2_CONTRACT_VALIDATION",
                correlation_id=correlation_id,
            )

        # Validation passed - create order via state machine to get ORDER_CREATED event
        sm_result = self.state_machine.create_order(
            client_order_id=client_order_id,
            symbol=intent.symbol,
            side=intent.side.value,
            quantity=intent.quantity,
            order_type=intent.order_type,
            price=intent.limit_price,
            time_in_force=intent.time_in_force,
            strategy_id=intent.strategy_id,
            session_id=intent.session_id,
            metadata=intent.metadata,
        )

        if not sm_result.success:
            return PipelineResult(
                success=False,
                order=sm_result.order,
                reason_code=ReasonCode.VALIDATION_MISSING_FIELD,
                reason_detail=sm_result.message,
                stage_reached="STAGE_2_CONTRACT_VALIDATION",
                correlation_id=correlation_id,
            )

        # Add to audit log
        self.audit_log.append_many(sm_result.ledger_entries)

        logger.info(
            f"[STAGE 2: VALIDATION PASSED] correlation_id={correlation_id}, "
            f"order_id={client_order_id}"
        )

        return PipelineResult(
            success=True,
            order=sm_result.order,
            stage_reached="STAGE_2_CONTRACT_VALIDATION",
            correlation_id=correlation_id,
            ledger_entries=sm_result.ledger_entries,
        )

    def _stage_3_risk_gate(self, order: Order, correlation_id: str) -> PipelineResult:
        """
        Stage 3: Pre-Trade Risk Gate.

        Call RiskHook.evaluate_order() to check if order is allowed.

        Decision flow:
        - ALLOW → proceed to Stage 4
        - BLOCK → reject order, emit REJECTED event
        - PAUSE → hold order, retry later (bounded retries)

        Args:
            order: Order to evaluate
            correlation_id: Correlation ID

        Returns:
            PipelineResult
        """
        logger.info(f"[STAGE 3: RISK GATE] correlation_id={correlation_id}")

        # Evaluate order via risk hook
        risk_result: RiskResult = self.risk_hook.evaluate_order(order)

        if risk_result.decision == RiskDecision.ALLOW:
            logger.info(
                f"[STAGE 3: RISK ALLOWED] correlation_id={correlation_id}, "
                f"reason={risk_result.reason}"
            )
            return PipelineResult(
                success=True,
                order=order,
                stage_reached="STAGE_3_RISK_GATE",
                correlation_id=correlation_id,
                metadata={"risk_result": risk_result.to_dict()},
            )

        elif risk_result.decision == RiskDecision.BLOCK:
            logger.warning(
                f"[STAGE 3: RISK BLOCKED] correlation_id={correlation_id}, "
                f"reason={risk_result.reason}"
            )

            # Mark order as FAILED (CREATED → FAILED is valid transition)
            # Note: REJECTED is only valid from SUBMITTED, so we use FAILED for pre-submission blocks
            sm_result = self.state_machine.fail_order(order, reason=risk_result.reason)

            if sm_result.success:
                # Add to ledger (includes ORDER_CREATED from create_order in Stage 2)
                self.order_ledger.add_order(sm_result.order)
                # Append failure ledger entries
                self.audit_log.append_many(sm_result.ledger_entries)

            return PipelineResult(
                success=False,
                order=sm_result.order,  # Use updated order from state machine
                reason_code=ReasonCode.RISK_BLOCKED,
                reason_detail=risk_result.reason,
                stage_reached="STAGE_3_RISK_GATE",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries if sm_result.success else [],
                metadata={"risk_result": risk_result.to_dict()},
            )

        else:  # RiskDecision.PAUSE
            logger.warning(
                f"[STAGE 3: RISK PAUSED] correlation_id={correlation_id}, "
                f"reason={risk_result.reason}"
            )

            # For Phase 0: treat PAUSE as BLOCK (no retry logic yet)
            # Use FAILED state (CREATED → FAILED is valid transition)
            sm_result = self.state_machine.fail_order(order, reason=risk_result.reason)

            if sm_result.success:
                # Add to ledger
                self.order_ledger.add_order(sm_result.order)
                # Append failure ledger entries
                self.audit_log.append_many(sm_result.ledger_entries)

            return PipelineResult(
                success=False,
                order=sm_result.order,  # Use updated order from state machine
                reason_code=ReasonCode.RISK_BLOCKED,
                reason_detail=f"Risk PAUSE (treated as BLOCK in Phase 0): {risk_result.reason}",
                stage_reached="STAGE_3_RISK_GATE",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries if sm_result.success else [],
                metadata={"risk_result": risk_result.to_dict()},
            )

    def _stage_4_route_selection(self, order: Order, correlation_id: str) -> PipelineResult:
        """
        Stage 4: Route Selection.

        Select adapter based on execution mode and policy.

        WP0C routing (if adapter_registry provided):
        - PAPER → SimulatedVenueAdapter (from registry)
        - SHADOW → SimulatedVenueAdapter (from registry)
        - TESTNET → SimulatedVenueAdapter (from registry)
        - LIVE_BLOCKED → REJECT (governance block)

        Legacy routing (if no adapter_registry):
        - All modes → use fixed adapter from constructor (backwards compatible)

        Args:
            order: Order to route
            correlation_id: Correlation ID

        Returns:
            PipelineResult
        """
        logger.info(
            f"[STAGE 4: ROUTE SELECTION] correlation_id={correlation_id}, "
            f"mode={self.execution_mode.value}"
        )

        # Check if live mode is blocked (Phase 0 default)
        if self.execution_mode == ExecutionMode.LIVE_BLOCKED:
            logger.error(
                f"[STAGE 4: LIVE BLOCKED] correlation_id={correlation_id}, "
                f"Live execution is governance-blocked in Phase 0"
            )

            # Mark order as FAILED (CREATED → FAILED is valid transition)
            sm_result = self.state_machine.fail_order(
                order, reason="Live execution not enabled (Phase 0)"
            )

            if sm_result.success:
                # Add to ledger
                self.order_ledger.add_order(sm_result.order)
                # Append failure ledger entries
                self.audit_log.append_many(sm_result.ledger_entries)

            return PipelineResult(
                success=False,
                order=sm_result.order,  # Use updated order from state machine
                reason_code=ReasonCode.POLICY_LIVE_NOT_ENABLED,
                reason_detail="Live execution is governance-blocked (Phase 0 default)",
                stage_reached="STAGE_4_ROUTE_SELECTION",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries if sm_result.success else [],
            )

        # WP0C: Use adapter_registry if available
        if self.adapter_registry is not None:
            try:
                selected_adapter = self.adapter_registry.get_adapter(self.execution_mode)
                logger.info(
                    f"[STAGE 4: ROUTE SELECTED (REGISTRY)] correlation_id={correlation_id}, "
                    f"mode={self.execution_mode.value}, "
                    f"adapter={type(selected_adapter).__name__}"
                )
                # Temporarily store selected adapter for Stage 5
                self._selected_adapter = selected_adapter
            except Exception as e:
                logger.error(
                    f"[STAGE 4: ROUTE FAILED] correlation_id={correlation_id}, "
                    f"Adapter selection failed: {e}"
                )

                # Mark order as FAILED
                sm_result = self.state_machine.fail_order(order, reason=str(e))
                if sm_result.success:
                    self.order_ledger.add_order(sm_result.order)
                    self.audit_log.append_many(sm_result.ledger_entries)

                return PipelineResult(
                    success=False,
                    order=sm_result.order,
                    reason_code=ReasonCode.ADAPTER_ERROR,
                    reason_detail=f"Adapter selection failed: {e}",
                    stage_reached="STAGE_4_ROUTE_SELECTION",
                    correlation_id=correlation_id,
                    ledger_entries=sm_result.ledger_entries if sm_result.success else [],
                )
        else:
            # Legacy: use fixed adapter (backwards compatible)
            selected_adapter = self.adapter
            self._selected_adapter = selected_adapter
            logger.info(
                f"[STAGE 4: ROUTE SELECTED (LEGACY)] correlation_id={correlation_id}, "
                f"adapter={type(self.adapter).__name__}"
            )

        return PipelineResult(
            success=True,
            order=order,
            stage_reached="STAGE_4_ROUTE_SELECTION",
            correlation_id=correlation_id,
            metadata={"adapter": type(selected_adapter).__name__},
        )

    def _stage_5_adapter_dispatch(
        self, order: Order, idempotency_key: str, correlation_id: str
    ) -> PipelineResult:
        """
        Stage 5: Adapter Dispatch.

        Execute order via selected adapter.

        Timeout: 30s default (configurable per adapter)
        Idempotency: idempotency_key prevents duplicate submission on retry

        Args:
            order: Order to execute
            idempotency_key: Idempotency key
            correlation_id: Correlation ID

        Returns:
            PipelineResult with execution_event in metadata
        """
        logger.info(f"[STAGE 5: ADAPTER DISPATCH] correlation_id={correlation_id}")

        # Submit order via state machine (CREATED → SUBMITTED)
        sm_result = self.state_machine.submit_order(order)
        if not sm_result.success:
            logger.error(
                f"[STAGE 5: SUBMIT FAILED] correlation_id={correlation_id}, "
                f"reason={sm_result.message}"
            )

            return PipelineResult(
                success=False,
                order=order,
                reason_code=ReasonCode.ADAPTER_ERROR,
                reason_detail=sm_result.message,
                stage_reached="STAGE_5_ADAPTER_DISPATCH",
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                ledger_entries=sm_result.ledger_entries,
            )

        # Add order to ledger
        self.order_ledger.add_order(order)
        self.audit_log.append_many(sm_result.ledger_entries)

        # RUNBOOK B / Slice 1: Emit SUBMIT event
        beta = self._beta_context or {}
        if beta:
            self._emit_beta_event(
                run_id=beta["run_id"],
                session_id=beta["session_id"],
                intent_id=beta["intent_id"],
                symbol=order.symbol,
                event_type="SUBMIT",
                client_order_id=order.client_order_id,
                payload={"idempotency_key": idempotency_key},
            )

        # Execute order via adapter (use selected adapter from Stage 4)
        adapter = getattr(self, "_selected_adapter", self.adapter)  # WP0C: use selected adapter
        try:
            execution_event = adapter.execute_order(order, idempotency_key)

            logger.info(
                f"[STAGE 5: ADAPTER EXECUTED] correlation_id={correlation_id}, "
                f"adapter={type(adapter).__name__}, "
                f"event_type={execution_event.event_type}"
            )

            return PipelineResult(
                success=True,
                order=order,
                stage_reached="STAGE_5_ADAPTER_DISPATCH",
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                ledger_entries=sm_result.ledger_entries,
                metadata={"execution_event": execution_event},
            )

        except Exception as e:
            logger.error(f"[STAGE 5: ADAPTER ERROR] correlation_id={correlation_id}, error={e}")

            # Mark order as FAILED
            fail_result = self.state_machine.fail_order(order, reason=str(e))
            if fail_result.success:
                self.order_ledger.update_order(order, event="ORDER_FAILED")
                self.audit_log.append_many(fail_result.ledger_entries)

            return PipelineResult(
                success=False,
                order=order,
                reason_code=ReasonCode.ADAPTER_ERROR,
                reason_detail=str(e),
                stage_reached="STAGE_5_ADAPTER_DISPATCH",
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                ledger_entries=fail_result.ledger_entries if fail_result.success else [],
            )

    def _stage_6_event_handling(
        self, order: Order, execution_event: ExecutionEvent, correlation_id: str
    ) -> PipelineResult:
        """
        Stage 6: Execution Event Handling.

        Process execution event from adapter:
        - ACK: Order accepted → SUBMITTED → ACKNOWLEDGED
        - REJECT: Order rejected → REJECTED
        - FILL: Order filled → PARTIALLY_FILLED or FILLED
        - CANCEL_ACK: Order cancelled → CANCELLED

        Args:
            order: Order
            execution_event: Execution event from adapter
            correlation_id: Correlation ID

        Returns:
            PipelineResult
        """
        logger.info(
            f"[STAGE 6: EVENT HANDLING] correlation_id={correlation_id}, "
            f"event_type={execution_event.event_type}"
        )

        event_type = execution_event.event_type

        if event_type == "ACK":
            # Acknowledge order (SUBMITTED → ACKNOWLEDGED)
            sm_result = self.state_machine.acknowledge_order(
                order, exchange_order_id=execution_event.exchange_order_id or "unknown"
            )

            if sm_result.success:
                self.order_ledger.update_order(order, event="ORDER_ACKNOWLEDGED")
                self.audit_log.append_many(sm_result.ledger_entries)

                # RUNBOOK B / Slice 1: Emit ACK event
                beta = self._beta_context or {}
                if beta:
                    self._emit_beta_event(
                        run_id=beta["run_id"],
                        session_id=beta["session_id"],
                        intent_id=beta["intent_id"],
                        symbol=order.symbol,
                        event_type="ACK",
                        client_order_id=order.client_order_id,
                        payload={"exchange_order_id": execution_event.exchange_order_id or "unknown"},
                    )

            return PipelineResult(
                success=sm_result.success,
                order=order,
                stage_reached="STAGE_6_EVENT_HANDLING",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries,
            )

        elif event_type == "REJECT":
            # Reject order
            sm_result = self.state_machine.reject_order(
                order, reason=execution_event.reject_reason or "Rejected by adapter"
            )

            if sm_result.success:
                self.order_ledger.update_order(order, event="ORDER_REJECTED")
                self.audit_log.append_many(sm_result.ledger_entries)

                # RUNBOOK B / Slice 1: Emit REJECT event
                beta = self._beta_context or {}
                if beta:
                    self._emit_beta_event(
                        run_id=beta["run_id"],
                        session_id=beta["session_id"],
                        intent_id=beta["intent_id"],
                        symbol=order.symbol,
                        event_type="REJECT",
                        client_order_id=order.client_order_id,
                        reason_code="ADAPTER_REJECTED",
                        reason_detail=(execution_event.reject_reason or "Rejected by adapter")[:256],
                    )

            return PipelineResult(
                success=False,
                order=order,
                reason_code=ReasonCode.ADAPTER_REJECTED,
                reason_detail=execution_event.reject_reason or "Rejected by adapter",
                stage_reached="STAGE_6_EVENT_HANDLING",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries,
            )

        elif event_type == "FILL":
            # Apply fill
            fill = execution_event.fill
            if fill is None:
                logger.error(f"[STAGE 6: FILL EVENT WITHOUT FILL] correlation_id={correlation_id}")
                return PipelineResult(
                    success=False,
                    order=order,
                    reason_code=ReasonCode.ADAPTER_ERROR,
                    reason_detail="FILL event without fill details",
                    stage_reached="STAGE_6_EVENT_HANDLING",
                    correlation_id=correlation_id,
                )

            # If order is SUBMITTED, acknowledge it first (implicit ACK before FILL)
            if order.state == OrderState.SUBMITTED:
                ack_result = self.state_machine.acknowledge_order(
                    order, exchange_order_id=execution_event.exchange_order_id or "unknown"
                )
                if ack_result.success:
                    self.order_ledger.update_order(order, event="ORDER_ACKNOWLEDGED")
                    self.audit_log.append_many(ack_result.ledger_entries)

                    # RUNBOOK B / Slice 1: Emit ACK event (implicit)
                    beta = self._beta_context or {}
                    if beta:
                        self._emit_beta_event(
                            run_id=beta["run_id"],
                            session_id=beta["session_id"],
                            intent_id=beta["intent_id"],
                            symbol=order.symbol,
                            event_type="ACK",
                            client_order_id=order.client_order_id,
                            payload={"exchange_order_id": execution_event.exchange_order_id or "unknown"},
                        )

            # Now apply fill
            sm_result = self.state_machine.apply_fill(order, fill)

            if sm_result.success:
                self.order_ledger.update_order(order, event="ORDER_FILLED")
                self.audit_log.append_many(sm_result.ledger_entries)

            # RUNBOOK B / Slice 1: Emit FILL event
            beta = self._beta_context or {}
            if beta:
                self._emit_beta_event(
                    run_id=beta["run_id"],
                    session_id=beta["session_id"],
                    intent_id=beta["intent_id"],
                    symbol=order.symbol,
                    event_type="FILL",
                    client_order_id=order.client_order_id,
                    payload={
                        "fill_id": fill.fill_id,
                        "quantity": str(fill.quantity),
                        "price": str(fill.price),
                        "fee": str(fill.fee),
                        "fee_currency": fill.fee_currency,
                    },
                )

            return PipelineResult(
                success=sm_result.success,
                order=order,
                stage_reached="STAGE_6_EVENT_HANDLING",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries,
                metadata={"fill": fill.to_dict()},
            )

        elif event_type == "CANCEL_ACK":
            # Cancel order
            sm_result = self.state_machine.cancel_order(order, reason="Cancelled by adapter")

            if sm_result.success:
                self.order_ledger.update_order(order, event="ORDER_CANCELLED")
                self.audit_log.append_many(sm_result.ledger_entries)

            return PipelineResult(
                success=sm_result.success,
                order=order,
                stage_reached="STAGE_6_EVENT_HANDLING",
                correlation_id=correlation_id,
                ledger_entries=sm_result.ledger_entries,
            )

        else:
            logger.error(
                f"[STAGE 6: UNKNOWN EVENT TYPE] correlation_id={correlation_id}, "
                f"event_type={event_type}"
            )
            return PipelineResult(
                success=False,
                order=order,
                reason_code=ReasonCode.ADAPTER_ERROR,
                reason_detail=f"Unknown event type: {event_type}",
                stage_reached="STAGE_6_EVENT_HANDLING",
                correlation_id=correlation_id,
            )

    def _stage_7_post_trade_hooks(
        self,
        order: Order,
        execution_event: ExecutionEvent,
        correlation_id: str,
        event_metadata: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Stage 7: Post-Trade Hooks.

        Process after ExecutionEvent received:
        - Update Position Ledger (apply fill → position, PnL, cash)
        - Emit Fill event to WP0D (Position Accounting Bridge)
        - Generate Audit Log entry

        Args:
            order: Order
            execution_event: Execution event
            correlation_id: Correlation ID
            event_metadata: Metadata from Stage 6 (may contain fill info)

        Returns:
            PipelineResult
        """
        logger.info(f"[STAGE 7: POST-TRADE HOOKS] correlation_id={correlation_id}")

        # If FILL event, update position ledger and create ledger entries
        if execution_event.event_type == "FILL":
            # Get fill from execution event
            fill = execution_event.fill

            if fill is None:
                logger.warning(
                    f"[STAGE 7: NO FILL] correlation_id={correlation_id}, "
                    f"FILL event but no fill details"
                )
                return PipelineResult(
                    success=True,
                    order=order,
                    stage_reached="STAGE_7_POST_TRADE_HOOKS",
                    correlation_id=correlation_id,
                )

            try:
                # Update position ledger
                position = self.position_ledger.apply_fill(fill)

                logger.info(
                    f"[STAGE 7: POSITION UPDATED] correlation_id={correlation_id}, "
                    f"symbol={position.symbol}, qty={position.quantity}, "
                    f"realized_pnl={position.realized_pnl}"
                )

                # WP0D: Map ExecutionEvent to LedgerEntry for audit trail
                ledger_entries = self.ledger_mapper.map_event_to_ledger_entries(
                    execution_event=execution_event,
                    correlation_id=correlation_id,
                )

                # Add ledger entries to audit log
                if ledger_entries:
                    self.audit_log.append_many(ledger_entries)

                logger.info(
                    f"[STAGE 7: LEDGER ENTRIES CREATED] correlation_id={correlation_id}, "
                    f"count={len(ledger_entries)}"
                )

            except Exception as e:
                logger.error(
                    f"[STAGE 7: POSITION UPDATE FAILED] correlation_id={correlation_id}, error={e}"
                )
                return PipelineResult(
                    success=False,
                    order=order,
                    reason_code=ReasonCode.ADAPTER_ERROR,
                    reason_detail=f"Position ledger update failed: {e}",
                    stage_reached="STAGE_7_POST_TRADE_HOOKS",
                    correlation_id=correlation_id,
                )

        return PipelineResult(
            success=True,
            order=order,
            stage_reached="STAGE_7_POST_TRADE_HOOKS",
            correlation_id=correlation_id,
        )

    def _stage_8_recon_handoff(self, order: Order, correlation_id: str) -> PipelineResult:
        """
        Stage 8: Recon Hand-off.

        Prepare data for WP0D ReconciliationEngine:
        - Order Ledger snapshot
        - Position Ledger snapshot
        - Audit Log snapshot
        - Run reconciliation (Phase 0: mocked external data)
        - Generate ReconDiff list

        Phase 0: Conceptual/smoke test (no real exchange data)

        Args:
            order: Order
            correlation_id: Correlation ID

        Returns:
            PipelineResult
        """
        logger.info(f"[STAGE 8: RECON HAND-OFF] correlation_id={correlation_id}")

        # Prepare recon data (snapshots)
        recon_data = {
            "order_ledger_snapshot": self.order_ledger.to_dict(),
            "position_ledger_snapshot": self.position_ledger.to_dict(),
            "audit_log_snapshot": self.audit_log.to_dict(),
        }

        logger.info(
            f"[STAGE 8: RECON DATA PREPARED] correlation_id={correlation_id}, "
            f"total_orders={recon_data['order_ledger_snapshot']['total_orders']}, "
            f"total_positions={recon_data['position_ledger_snapshot']['total_positions']}"
        )

        # WP0D: Run reconciliation (Phase 0: mocked external snapshot)
        try:
            recon_diffs = self.recon_engine.reconcile()

            recon_data["recon_diffs"] = [d.to_dict() for d in recon_diffs]
            recon_data["recon_summary"] = {
                "total_diffs": len(recon_diffs),
                "severity_counts": {
                    "INFO": sum(1 for d in recon_diffs if d.severity == "INFO"),
                    "WARN": sum(1 for d in recon_diffs if d.severity == "WARN"),
                    "FAIL": sum(1 for d in recon_diffs if d.severity == "FAIL"),
                },
            }

            logger.info(
                f"[STAGE 8: RECON COMPLETED] correlation_id={correlation_id}, "
                f"diffs={len(recon_diffs)}, "
                f"severity={recon_data['recon_summary']['severity_counts']}"
            )

        except Exception as e:
            logger.error(f"[STAGE 8: RECON FAILED] correlation_id={correlation_id}, error={e}")
            # Reconciliation failure is not critical (does not block order execution)
            recon_data["recon_error"] = str(e)

        return PipelineResult(
            success=True,
            order=order,
            stage_reached="STAGE_8_RECON_HANDOFF",
            correlation_id=correlation_id,
            metadata={"recon_data": recon_data},
        )

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID"""
        return f"corr_{uuid.uuid4().hex[:16]}"

    def _generate_idempotency_key(
        self, intent: OrderIntent, *, run_id: str, session_id: str, intent_id: str
    ) -> str:
        """
        Generate idempotency key from intent.

        Same intent → same key (prevents duplicate processing)
        """
        # Deterministic (no Python hash()).
        key_fields = {
            "run_id": run_id,
            "session_id": session_id,
            "intent_id": intent_id,
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "order_type": intent.order_type.value,
            "limit_price": str(intent.limit_price) if intent.limit_price else None,
            "strategy_id": intent.strategy_id or None,
        }
        canonical = json.dumps(key_fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"idem_{digest[:32]}"

    def get_order_ledger_snapshot(self) -> Dict[str, Any]:
        """Get order ledger snapshot for reconciliation"""
        return self.order_ledger.to_dict()

    def get_position_ledger_snapshot(
        self, mark_prices: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Any]:
        """Get position ledger snapshot for reconciliation"""
        return self.position_ledger.to_dict(mark_prices=mark_prices)

    def get_audit_log_snapshot(self) -> Dict[str, Any]:
        """Get audit log snapshot for reconciliation"""
        return self.audit_log.to_dict()
