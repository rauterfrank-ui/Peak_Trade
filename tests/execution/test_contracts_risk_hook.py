"""
Tests for risk hook interface (WP0E)

Test Coverage:
- RiskHook protocol implementations
- Null/Blocking/Conditional hooks
- Integration with Order contracts
- No cyclic imports
"""

from decimal import Decimal

import pytest

from src.execution.contracts import (
    Order,
    OrderSide,
    OrderType,
    RiskDecision,
)
from src.execution.risk_hook import (
    NullRiskHook,
    BlockingRiskHook,
    ConditionalRiskHook,
    create_null_hook,
    create_blocking_hook,
    create_conditional_hook,
)


# ============================================================================
# NullRiskHook Tests
# ============================================================================


def test_null_hook_evaluate_order_allow():
    """Test NullRiskHook always allows orders"""
    hook = NullRiskHook()

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.ALLOW
    assert "NullRiskHook" in result.reason


def test_null_hook_check_kill_switch_inactive():
    """Test NullRiskHook kill switch always inactive"""
    hook = NullRiskHook()

    result = hook.check_kill_switch()

    assert result.decision == RiskDecision.ALLOW
    assert "inactive" in result.reason


def test_null_hook_evaluate_position_change_allow():
    """Test NullRiskHook allows position changes"""
    hook = NullRiskHook()

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.01"),
        side="BUY",
    )

    assert result.decision == RiskDecision.ALLOW


def test_null_hook_factory():
    """Test null hook factory"""
    hook = create_null_hook()

    assert isinstance(hook, NullRiskHook)


# ============================================================================
# BlockingRiskHook Tests
# ============================================================================


def test_blocking_hook_evaluate_order_block():
    """Test BlockingRiskHook always blocks orders"""
    hook = BlockingRiskHook(reason="Emergency block")

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK
    assert "Emergency block" in result.reason


def test_blocking_hook_check_kill_switch_active():
    """Test BlockingRiskHook kill switch always active"""
    hook = BlockingRiskHook()

    result = hook.check_kill_switch()

    assert result.decision == RiskDecision.PAUSE


def test_blocking_hook_evaluate_position_change_block():
    """Test BlockingRiskHook blocks position changes"""
    hook = BlockingRiskHook(reason="All trading blocked")

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.01"),
        side="BUY",
    )

    assert result.decision == RiskDecision.BLOCK
    assert "All trading blocked" in result.reason


def test_blocking_hook_factory():
    """Test blocking hook factory"""
    hook = create_blocking_hook(reason="Test block")

    assert isinstance(hook, BlockingRiskHook)
    assert "Test block" in hook.reason


# ============================================================================
# ConditionalRiskHook Tests - Symbol Whitelist
# ============================================================================


def test_conditional_hook_allow_whitelisted_symbol():
    """Test ConditionalRiskHook allows whitelisted symbols"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR", "ETH-EUR"},
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.ALLOW


def test_conditional_hook_block_non_whitelisted_symbol():
    """Test ConditionalRiskHook blocks non-whitelisted symbols"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR"},
    )

    order = Order(
        client_order_id="test_001",
        symbol="ETH-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK
    assert "not in whitelist" in result.reason


# ============================================================================
# ConditionalRiskHook Tests - Quantity Limit
# ============================================================================


def test_conditional_hook_allow_within_quantity_limit():
    """Test ConditionalRiskHook allows orders within quantity limit"""
    hook = ConditionalRiskHook(
        max_quantity=Decimal("0.01"),
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.005"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.ALLOW


def test_conditional_hook_block_exceeds_quantity_limit():
    """Test ConditionalRiskHook blocks orders exceeding quantity limit"""
    hook = ConditionalRiskHook(
        max_quantity=Decimal("0.01"),
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.02"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK
    assert "exceeds max" in result.reason


# ============================================================================
# ConditionalRiskHook Tests - Kill Switch
# ============================================================================


def test_conditional_hook_block_when_kill_switch_active():
    """Test ConditionalRiskHook blocks when kill switch is active"""
    hook = ConditionalRiskHook(
        kill_switch_active=True,
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK
    assert "Kill switch" in result.reason


def test_conditional_hook_check_kill_switch_active():
    """Test ConditionalRiskHook kill switch check when active"""
    hook = ConditionalRiskHook(
        kill_switch_active=True,
    )

    result = hook.check_kill_switch()

    assert result.decision == RiskDecision.PAUSE
    assert "active" in result.reason


def test_conditional_hook_check_kill_switch_inactive():
    """Test ConditionalRiskHook kill switch check when inactive"""
    hook = ConditionalRiskHook(
        kill_switch_active=False,
    )

    result = hook.check_kill_switch()

    assert result.decision == RiskDecision.ALLOW
    assert "inactive" in result.reason


# ============================================================================
# ConditionalRiskHook Tests - Position Change
# ============================================================================


def test_conditional_hook_position_change_allow():
    """Test ConditionalRiskHook allows position changes"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR"},
        max_quantity=Decimal("0.01"),
    )

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.005"),
        side="BUY",
    )

    assert result.decision == RiskDecision.ALLOW


def test_conditional_hook_position_change_block_symbol():
    """Test ConditionalRiskHook blocks position change for non-whitelisted symbol"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR"},
    )

    result = hook.evaluate_position_change(
        symbol="ETH-EUR",
        quantity=Decimal("0.001"),
        side="BUY",
    )

    assert result.decision == RiskDecision.BLOCK
    assert "not in whitelist" in result.reason


def test_conditional_hook_position_change_block_quantity():
    """Test ConditionalRiskHook blocks position change exceeding quantity limit"""
    hook = ConditionalRiskHook(
        max_quantity=Decimal("0.01"),
    )

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.02"),
        side="BUY",
    )

    assert result.decision == RiskDecision.BLOCK
    assert "exceeds max" in result.reason


def test_conditional_hook_position_change_block_kill_switch():
    """Test ConditionalRiskHook blocks position change when kill switch active"""
    hook = ConditionalRiskHook(
        kill_switch_active=True,
    )

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.001"),
        side="BUY",
    )

    assert result.decision == RiskDecision.BLOCK
    assert "Kill switch" in result.reason


# ============================================================================
# ConditionalRiskHook Tests - Combined Conditions
# ============================================================================


def test_conditional_hook_combined_conditions_allow():
    """Test ConditionalRiskHook with multiple conditions - all pass"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR", "ETH-EUR"},
        max_quantity=Decimal("0.01"),
        kill_switch_active=False,
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.005"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.ALLOW


def test_conditional_hook_combined_conditions_block():
    """Test ConditionalRiskHook with multiple conditions - one fails"""
    hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR"},
        max_quantity=Decimal("0.01"),
        kill_switch_active=False,
    )

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.02"),  # Exceeds limit
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK


def test_conditional_hook_factory():
    """Test conditional hook factory"""
    hook = create_conditional_hook(
        allow_symbols={"BTC-EUR"},
        max_quantity=Decimal("0.01"),
    )

    assert isinstance(hook, ConditionalRiskHook)
    assert "BTC-EUR" in hook.allow_symbols
    assert hook.max_quantity == Decimal("0.01")


# ============================================================================
# Integration Tests - Order with Hook
# ============================================================================


def test_order_evaluation_workflow():
    """Test complete order evaluation workflow"""
    # Create order
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    # Test with null hook (should allow)
    null_hook = NullRiskHook()
    result = null_hook.evaluate_order(order)
    assert result.decision == RiskDecision.ALLOW

    # Test with blocking hook (should block)
    blocking_hook = BlockingRiskHook()
    result = blocking_hook.evaluate_order(order)
    assert result.decision == RiskDecision.BLOCK

    # Test with conditional hook (should allow)
    conditional_hook = ConditionalRiskHook(
        allow_symbols={"BTC-EUR"},
        max_quantity=Decimal("0.01"),
    )
    result = conditional_hook.evaluate_order(order)
    assert result.decision == RiskDecision.ALLOW


def test_no_cyclic_imports():
    """Test that risk_hook can be imported without importing risk_layer"""
    # This test verifies the contract design: execution -> contracts <- risk
    # NO: execution -> risk_layer (would create cycle)

    from src.execution import risk_hook
    from src.execution import contracts

    # These imports should work without error
    assert hasattr(risk_hook, "RiskHook")
    assert hasattr(contracts, "Order")
    assert hasattr(contracts, "RiskResult")
