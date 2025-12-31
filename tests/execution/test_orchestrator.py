"""
Tests for Execution Pipeline Orchestrator (WP0A - Phase 0)

Test Coverage:
- Stage ordering (8 stages executed in sequence)
- Failure propagation (failures at each stage handled correctly)
- Audit trail generation (deterministic ledger entries)
- Risk hook integration (ALLOW/BLOCK/PAUSE decisions)
- Idempotency (same intent → same idempotency_key)
- Default blocked behavior (live mode blocked by governance)
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.execution.orchestrator import (
    ExecutionOrchestrator,
    OrderIntent,
    ExecutionMode,
    ReasonCode,
    ExecutionEvent,
    NullAdapter,
)
from src.execution.contracts import (
    OrderSide,
    OrderType,
    OrderState,
    TimeInForce,
    Fill,
    RiskDecision,
    RiskResult,
)
from src.execution.risk_hook import NullRiskHook, BlockingRiskHook, ConditionalRiskHook


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def orchestrator():
    """Create orchestrator with null risk hook and null adapter"""
    return ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )


@pytest.fixture
def sample_intent():
    """Create sample order intent"""
    return OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
        strategy_id="test_strategy",
    )


# ============================================================================
# Test: Stage Ordering
# ============================================================================


def test_pipeline_stage_ordering_success(orchestrator, sample_intent):
    """Test that all 8 stages execute in order for successful flow"""
    result = orchestrator.submit_intent(sample_intent)

    # Should succeed
    assert result.success is True
    assert result.order is not None
    assert result.stage_reached == "STAGE_8_RECON_HANDOFF"

    # Order should be in ACKNOWLEDGED state (ACK from NullAdapter)
    assert result.order.state == OrderState.ACKNOWLEDGED

    # Should have correlation_id and idempotency_key
    assert result.correlation_id != ""
    assert result.idempotency_key != ""

    # Should have ledger entries
    assert len(result.ledger_entries) > 0


def test_pipeline_stage_ordering_validation_failure(orchestrator):
    """Test pipeline stops at Stage 2 (validation) if invalid order"""
    # Invalid intent: quantity = 0
    invalid_intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0"),  # Invalid
        order_type=OrderType.MARKET,
    )

    result = orchestrator.submit_intent(invalid_intent)

    # Should fail at Stage 2
    assert result.success is False
    assert result.stage_reached == "STAGE_2_CONTRACT_VALIDATION"
    assert result.reason_code == ReasonCode.VALIDATION_INVALID_QUANTITY


def test_pipeline_stage_ordering_risk_block(sample_intent):
    """Test pipeline stops at Stage 3 (risk gate) if risk blocks"""
    # Orchestrator with blocking risk hook
    orchestrator = ExecutionOrchestrator(
        risk_hook=BlockingRiskHook(reason="Test block"),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    # Should fail at Stage 3
    assert result.success is False
    assert result.stage_reached == "STAGE_3_RISK_GATE"
    assert result.reason_code == ReasonCode.RISK_BLOCKED
    assert "Test block" in result.reason_detail


def test_pipeline_stage_ordering_live_blocked(sample_intent):
    """Test pipeline stops at Stage 4 (route selection) if live mode blocked"""
    # Orchestrator with LIVE_BLOCKED mode
    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.LIVE_BLOCKED,
    )

    result = orchestrator.submit_intent(sample_intent)

    # Should fail at Stage 4
    assert result.success is False
    assert result.stage_reached == "STAGE_4_ROUTE_SELECTION"
    assert result.reason_code == ReasonCode.POLICY_LIVE_NOT_ENABLED
    assert "governance-blocked" in result.reason_detail.lower()


# ============================================================================
# Test: Failure Propagation
# ============================================================================


def test_failure_propagation_validation(orchestrator):
    """Test validation failure propagates correctly"""
    # LIMIT order without limit_price
    invalid_intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.LIMIT,
        limit_price=None,  # Missing for LIMIT order
    )

    result = orchestrator.submit_intent(invalid_intent)

    assert result.success is False
    assert result.reason_code == ReasonCode.VALIDATION_INVALID_PRICE
    assert "limit_price" in result.reason_detail.lower()


def test_failure_propagation_risk_pause(sample_intent):
    """Test risk PAUSE decision propagates correctly"""

    # Orchestrator with risk hook that returns PAUSE
    class PauseRiskHook:
        def evaluate_order(self, order, context=None):
            return RiskResult(
                decision=RiskDecision.PAUSE,
                reason="Market volatility too high",
            )

        def check_kill_switch(self):
            return RiskResult(decision=RiskDecision.ALLOW, reason="")

        def evaluate_position_change(self, symbol, quantity, side, context=None):
            return RiskResult(decision=RiskDecision.ALLOW, reason="")

    orchestrator = ExecutionOrchestrator(
        risk_hook=PauseRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    # Phase 0: PAUSE treated as BLOCK
    assert result.success is False
    assert result.reason_code == ReasonCode.RISK_BLOCKED
    assert "PAUSE" in result.reason_detail or "volatility" in result.reason_detail.lower()


def test_failure_propagation_adapter_error(sample_intent):
    """Test adapter error propagates correctly"""

    class ErrorAdapter:
        def execute_order(self, order, idempotency_key):
            raise RuntimeError("Adapter connection failed")

    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=ErrorAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    assert result.success is False
    assert result.stage_reached == "STAGE_5_ADAPTER_DISPATCH"
    assert result.reason_code == ReasonCode.ADAPTER_ERROR
    assert "connection failed" in result.reason_detail.lower()


# ============================================================================
# Test: Audit Trail
# ============================================================================


def test_audit_trail_deterministic(orchestrator, sample_intent):
    """Test audit trail is deterministic and complete"""
    result = orchestrator.submit_intent(sample_intent)

    # Should have audit log entries
    audit_log = orchestrator.audit_log
    entries = audit_log.get_all_entries()

    assert len(entries) > 0

    # Should have ORDER_CREATED, ORDER_SUBMITTED, ORDER_ACKNOWLEDGED
    event_types = [entry.event_type for entry in entries]
    assert "ORDER_CREATED" in event_types
    assert "ORDER_SUBMITTED" in event_types
    assert "ORDER_ACKNOWLEDGED" in event_types

    # Entries should have sequential sequence numbers
    sequences = [entry.sequence for entry in entries]
    assert sequences == sorted(sequences)
    assert sequences == list(range(1, len(sequences) + 1))


def test_audit_trail_risk_blocked(sample_intent):
    """Test audit trail for risk-blocked order"""
    orchestrator = ExecutionOrchestrator(
        risk_hook=BlockingRiskHook(reason="Limit exceeded"),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    # Should have audit log entry for FAILED (risk blocks from CREATED → FAILED)
    audit_log = orchestrator.audit_log
    entries = audit_log.get_all_entries()

    event_types = [entry.event_type for entry in entries]
    assert "ORDER_FAILED" in event_types

    # Should have failure reason in ledger entry
    failed_entry = [e for e in entries if e.event_type == "ORDER_FAILED"][0]
    assert failed_entry.details.get("reason") == "Limit exceeded"


def test_audit_trail_query_by_order_id(orchestrator, sample_intent):
    """Test querying audit log by order ID"""
    result = orchestrator.submit_intent(sample_intent)
    order_id = result.order.client_order_id

    # Query audit log for this order
    entries = orchestrator.audit_log.get_entries_for_order(order_id)

    assert len(entries) > 0
    assert all(entry.client_order_id == order_id for entry in entries)


# ============================================================================
# Test: Risk Hook Integration
# ============================================================================


def test_risk_hook_allow(orchestrator, sample_intent):
    """Test risk hook ALLOW decision"""
    result = orchestrator.submit_intent(sample_intent)

    assert result.success is True
    assert result.order.state == OrderState.ACKNOWLEDGED


def test_risk_hook_block(sample_intent):
    """Test risk hook BLOCK decision"""
    orchestrator = ExecutionOrchestrator(
        risk_hook=BlockingRiskHook(reason="Position limit exceeded"),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    assert result.success is False
    assert result.reason_code == ReasonCode.RISK_BLOCKED
    # Risk blocks from CREATED state result in FAILED (not REJECTED)
    assert result.order.state == OrderState.FAILED


def test_risk_hook_conditional_symbol_whitelist(sample_intent):
    """Test conditional risk hook with symbol whitelist"""
    # Allow only ETH/EUR
    risk_hook = ConditionalRiskHook(allow_symbols={"ETH/EUR"})

    orchestrator = ExecutionOrchestrator(
        risk_hook=risk_hook,
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    # BTC/EUR should be blocked
    result = orchestrator.submit_intent(sample_intent)
    assert result.success is False
    assert result.reason_code == ReasonCode.RISK_BLOCKED

    # ETH/EUR should be allowed
    eth_intent = OrderIntent(
        symbol="ETH/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        order_type=OrderType.MARKET,
    )
    result = orchestrator.submit_intent(eth_intent)
    assert result.success is True


def test_risk_hook_conditional_max_quantity(sample_intent):
    """Test conditional risk hook with max quantity"""
    # Max quantity = 0.005 BTC
    risk_hook = ConditionalRiskHook(max_quantity=Decimal("0.005"))

    orchestrator = ExecutionOrchestrator(
        risk_hook=risk_hook,
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    # 0.01 BTC should be blocked
    result = orchestrator.submit_intent(sample_intent)
    assert result.success is False
    assert result.reason_code == ReasonCode.RISK_BLOCKED

    # 0.003 BTC should be allowed
    small_intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.003"),
        order_type=OrderType.MARKET,
    )
    result = orchestrator.submit_intent(small_intent)
    assert result.success is True


# ============================================================================
# Test: Idempotency
# ============================================================================


def test_idempotency_key_deterministic(orchestrator):
    """Test idempotency key is deterministic for same intent"""
    intent1 = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
        strategy_id="test",
    )

    intent2 = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
        strategy_id="test",
    )

    result1 = orchestrator.submit_intent(intent1)
    result2 = orchestrator.submit_intent(intent2)

    # Same intent → same idempotency key
    assert result1.idempotency_key == result2.idempotency_key


def test_idempotency_key_different_for_different_intents(orchestrator):
    """Test idempotency key is different for different intents"""
    intent1 = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
    )

    intent2 = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.02"),  # Different quantity
        order_type=OrderType.MARKET,
    )

    result1 = orchestrator.submit_intent(intent1)
    result2 = orchestrator.submit_intent(intent2)

    # Different intent → different idempotency key
    assert result1.idempotency_key != result2.idempotency_key


# ============================================================================
# Test: Default Blocked Behavior
# ============================================================================


def test_live_mode_blocked_by_default():
    """Test live mode is blocked by governance (Phase 0 default)"""
    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.LIVE_BLOCKED,
    )

    intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
    )

    result = orchestrator.submit_intent(intent)

    assert result.success is False
    assert result.reason_code == ReasonCode.POLICY_LIVE_NOT_ENABLED
    assert "governance-blocked" in result.reason_detail.lower()
    # Live blocks from CREATED state result in FAILED (not REJECTED)
    assert result.order.state == OrderState.FAILED


def test_paper_mode_allowed():
    """Test paper mode is allowed"""
    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
    )

    result = orchestrator.submit_intent(intent)

    assert result.success is True


def test_shadow_mode_allowed():
    """Test shadow mode is allowed"""
    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=NullAdapter(),
        execution_mode=ExecutionMode.SHADOW,
    )

    intent = OrderIntent(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        order_type=OrderType.MARKET,
    )

    result = orchestrator.submit_intent(intent)

    assert result.success is True


# ============================================================================
# Test: Ledger Integration
# ============================================================================


def test_order_ledger_integration(orchestrator, sample_intent):
    """Test order ledger is updated correctly"""
    result = orchestrator.submit_intent(sample_intent)

    # Order should be in ledger
    order = orchestrator.order_ledger.get_order(result.order.client_order_id)
    assert order is not None
    assert order.state == OrderState.ACKNOWLEDGED

    # Ledger should have order history
    history = orchestrator.order_ledger.get_order_history(result.order.client_order_id)
    assert len(history) > 0


def test_position_ledger_integration(orchestrator, sample_intent):
    """Test position ledger is updated on fill"""

    # Create adapter that returns FILL event
    class FillAdapter:
        def execute_order(self, order, idempotency_key):
            fill = Fill(
                fill_id="fill_001",
                client_order_id=order.client_order_id,
                exchange_order_id="exch_001",
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=Decimal("50000.00"),
                fee=Decimal("5.00"),
                fee_currency="EUR",
            )
            return ExecutionEvent(
                event_type="FILL",
                order_id=order.client_order_id,
                exchange_order_id="exch_001",
                fill=fill,
            )

    orchestrator = ExecutionOrchestrator(
        risk_hook=NullRiskHook(),
        adapter=FillAdapter(),
        execution_mode=ExecutionMode.PAPER,
    )

    result = orchestrator.submit_intent(sample_intent)

    # Position should be updated
    position = orchestrator.position_ledger.get_position(sample_intent.symbol)
    assert position is not None
    assert position.quantity == sample_intent.quantity
    assert position.is_long()


# ============================================================================
# Test: Recon Hand-off
# ============================================================================


def test_recon_handoff_snapshots(orchestrator, sample_intent):
    """Test recon hand-off provides snapshots"""
    result = orchestrator.submit_intent(sample_intent)

    # Should have recon_data in metadata
    assert "recon_data" in result.metadata
    recon_data = result.metadata["recon_data"]

    # Should have snapshots
    assert "order_ledger_snapshot" in recon_data
    assert "position_ledger_snapshot" in recon_data
    assert "audit_log_snapshot" in recon_data

    # Snapshots should have data
    assert recon_data["order_ledger_snapshot"]["total_orders"] > 0
    assert recon_data["audit_log_snapshot"]["total_entries"] > 0


def test_recon_handoff_snapshot_methods(orchestrator, sample_intent):
    """Test recon snapshot methods"""
    orchestrator.submit_intent(sample_intent)

    # Get snapshots via methods
    order_snapshot = orchestrator.get_order_ledger_snapshot()
    position_snapshot = orchestrator.get_position_ledger_snapshot()
    audit_snapshot = orchestrator.get_audit_log_snapshot()

    assert order_snapshot["total_orders"] > 0
    assert "total_positions" in position_snapshot
    assert audit_snapshot["total_entries"] > 0
