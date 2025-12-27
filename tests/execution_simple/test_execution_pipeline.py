# tests/execution_simple/test_execution_pipeline.py
"""
Tests for Simplified Execution Pipeline.

Tests gates, adapters, and pipeline orchestration.
"""

from datetime import datetime

import pytest

from src.execution_simple import (
    ExecutionContext,
    ExecutionMode,
    SimulatedBrokerAdapter,
    build_execution_pipeline_from_config,
)
from src.execution_simple.gates import (
    LotSizeGate,
    MinNotionalGate,
    PriceSanityGate,
    ResearchOnlyGate,
)
from src.execution_simple.pipeline import ExecutionPipeline


class DummyConfig:
    """Minimal config for testing."""

    def __init__(self, d: dict):
        self.d = d

    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self.d
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val


# =============================================================================
# Gate Tests
# =============================================================================


def test_price_sanity_gate_blocks_invalid_price():
    """PriceSanityGate blocks orders with invalid price."""
    gate = PriceSanityGate()
    pipeline = ExecutionPipeline(gates=[gate])

    # Invalid price (0)
    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=0.0,
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert result.blocked
    assert "Invalid price" in result.block_reason
    assert len(result.orders) == 0


def test_price_sanity_gate_allows_valid_price():
    """PriceSanityGate allows orders with valid price."""
    gate = PriceSanityGate()
    pipeline = ExecutionPipeline(gates=[gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.gate_decisions) > 0
    assert result.gate_decisions[0].passed


def test_blocks_research_only_in_live():
    """ResearchOnlyGate blocks LIVE execution with research_only tag."""
    gate = ResearchOnlyGate(block_research_in_live=True)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.LIVE,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
        tags={"research_only"},
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert result.blocked
    assert "ResearchOnly" in result.block_reason
    assert "LIVE mode" in result.block_reason
    assert len(result.orders) == 0


def test_allows_research_only_in_paper():
    """ResearchOnlyGate allows PAPER execution with research_only tag."""
    gate = ResearchOnlyGate(block_research_in_live=True)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
        tags={"research_only"},
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.orders) == 1


def test_allows_research_only_in_backtest():
    """ResearchOnlyGate allows BACKTEST execution with research_only tag."""
    gate = ResearchOnlyGate(block_research_in_live=True)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.BACKTEST,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
        tags={"research_only"},
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.orders) == 1


def test_rounds_to_lot_size_and_blocks_min_notional():
    """LotSizeGate rounds quantity and MinNotionalGate blocks small orders."""
    lot_gate = LotSizeGate(lot_size=0.1, min_qty=0.1)
    notional_gate = MinNotionalGate(min_notional=50.0)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), lot_gate, notional_gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    # Test 1: delta=0.4 → rounds to 0.4, notional 40 → blocked
    result = pipeline.execute(target_position=0.4, current_position=0.0, context=ctx)

    assert result.blocked
    assert "MinNotional" in result.block_reason
    assert len(result.orders) == 0

    # Test 2: delta=0.6 → rounds to 0.6, notional 60 → allowed
    result = pipeline.execute(target_position=0.6, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.orders) == 1
    assert result.orders[0].quantity == pytest.approx(0.6, rel=0.01)


def test_lot_size_rounds_down():
    """LotSizeGate rounds down to nearest lot_size."""
    gate = LotSizeGate(lot_size=0.1, min_qty=0.1)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    # delta=0.75 → should round to 0.7
    result = pipeline.execute(target_position=0.75, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.orders) == 1
    assert result.orders[0].quantity == pytest.approx(0.7, rel=0.01)


def test_lot_size_blocks_below_min_qty():
    """LotSizeGate blocks orders below min_qty after rounding."""
    gate = LotSizeGate(lot_size=0.1, min_qty=0.1)
    pipeline = ExecutionPipeline(gates=[PriceSanityGate(), gate])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    # delta=0.05 → rounds to 0.0 → blocked
    result = pipeline.execute(target_position=0.05, current_position=0.0, context=ctx)

    assert result.blocked
    assert "LotSize" in result.block_reason


# =============================================================================
# Adapter Tests
# =============================================================================


def test_simulated_fill_applies_slippage():
    """SimulatedBrokerAdapter applies slippage correctly."""
    adapter = SimulatedBrokerAdapter(slippage_bps=10.0, fee_bps=5.0)
    pipeline = ExecutionPipeline(
        gates=[PriceSanityGate(), LotSizeGate(0.1, 0.1), MinNotionalGate(10.0)],
        adapter=adapter,
    )

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    # BUY: fill price should be > mid price
    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.fills) == 1
    fill = result.fills[0]

    # BUY with 0.1% slippage: fill_price = 100 * 1.001 = 100.1
    assert fill.price > ctx.price
    assert fill.price == pytest.approx(100.1, rel=0.001)

    # Fee: notional * 0.05% = 100.1 * 1.0 * 0.0005 = 0.05005
    assert fill.fee == pytest.approx(0.05005, rel=0.01)

    # SELL: fill price should be < mid price
    result = pipeline.execute(target_position=0.0, current_position=1.0, context=ctx)

    assert not result.blocked
    assert len(result.fills) == 1
    fill = result.fills[0]

    # SELL with 0.1% slippage: fill_price = 100 * 0.999 = 99.9
    assert fill.price < ctx.price
    assert fill.price == pytest.approx(99.9, rel=0.001)


# =============================================================================
# Pipeline Integration Tests
# =============================================================================


def test_pipeline_no_change_returns_empty():
    """Pipeline returns empty result when no position change needed."""
    pipeline = ExecutionPipeline(gates=[PriceSanityGate()])

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    result = pipeline.execute(target_position=1.0, current_position=1.0, context=ctx)

    assert not result.blocked
    assert result.desired_delta == 0
    assert len(result.orders) == 0
    assert len(result.fills) == 0


def test_pipeline_applies_gates_in_order():
    """Pipeline applies gates in specified order."""
    gates = [
        PriceSanityGate(),
        ResearchOnlyGate(block_research_in_live=True),
        LotSizeGate(lot_size=0.1, min_qty=0.1),
        MinNotionalGate(min_notional=10.0),
    ]
    pipeline = ExecutionPipeline(gates=gates)

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=100.0,
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    # Should have 4 gate decisions
    assert len(result.gate_decisions) == 4
    assert result.gate_decisions[0].gate_name == "PriceSanity"
    assert result.gate_decisions[1].gate_name == "ResearchOnly"
    assert result.gate_decisions[2].gate_name == "LotSize"
    assert result.gate_decisions[3].gate_name == "MinNotional"


# =============================================================================
# Builder Tests
# =============================================================================


def test_builder_creates_pipeline_from_config():
    """Builder creates pipeline from config with defaults."""
    cfg = DummyConfig(
        {
            "execution": {
                "mode": "paper",
                "slippage_bps": 2.0,
                "min_notional": 10.0,
                "lot_size": 0.0001,
                "min_qty": 0.0001,
                "gates": {"block_research_in_live": True},
            }
        }
    )

    pipeline = build_execution_pipeline_from_config(cfg)

    assert pipeline is not None
    assert len(pipeline.gates) == 4
    assert pipeline.adapter is not None


def test_builder_raises_on_invalid_mode():
    """Builder raises ValueError on invalid mode."""
    cfg = DummyConfig(
        {
            "execution": {
                "mode": "invalid_mode",
            }
        }
    )

    with pytest.raises(ValueError) as excinfo:
        build_execution_pipeline_from_config(cfg)

    assert "Invalid execution mode" in str(excinfo.value)
    assert "invalid_mode" in str(excinfo.value)


def test_builder_uses_defaults():
    """Builder uses default values for missing config."""
    cfg = DummyConfig({"execution": {}})

    pipeline = build_execution_pipeline_from_config(cfg)

    assert pipeline is not None
    assert len(pipeline.gates) == 4
    # Default mode is "paper", so adapter should be present
    assert pipeline.adapter is not None


# =============================================================================
# End-to-End Tests
# =============================================================================


def test_e2e_paper_execution_with_fills():
    """End-to-end test: paper execution with fills."""
    cfg = DummyConfig(
        {
            "execution": {
                "mode": "paper",
                "slippage_bps": 5.0,
                "fee_bps": 10.0,
                "min_notional": 50.0,
                "lot_size": 0.1,
                "min_qty": 0.1,
                "gates": {"block_research_in_live": True},
            }
        }
    )

    pipeline = build_execution_pipeline_from_config(cfg)

    ctx = ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=1000.0,
    )

    # Execute: buy 1.0 BTC
    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert not result.blocked
    assert len(result.orders) == 1
    assert len(result.fills) == 1

    # Verify fill
    fill = result.fills[0]
    assert fill.quantity == 1.0
    assert fill.price > ctx.price  # BUY has positive slippage
    assert fill.fee > 0

    # Verify result properties
    assert result.success
    assert result.total_filled_qty == 1.0
    assert result.total_notional > 1000.0
    assert result.total_fees > 0


def test_e2e_research_blocked_in_live():
    """End-to-end test: research code blocked in LIVE."""
    cfg = DummyConfig(
        {
            "execution": {
                "mode": "live",
                "gates": {"block_research_in_live": True},
            }
        }
    )

    pipeline = build_execution_pipeline_from_config(cfg)

    ctx = ExecutionContext(
        mode=ExecutionMode.LIVE,
        ts=datetime.now(),
        symbol="BTC-USD",
        price=1000.0,
        tags={"research_only"},
    )

    result = pipeline.execute(target_position=1.0, current_position=0.0, context=ctx)

    assert result.blocked
    assert "Research code blocked in LIVE mode" in result.block_reason
    assert not result.success
