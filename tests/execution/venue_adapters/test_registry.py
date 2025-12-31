"""
Tests for AdapterRegistry (WP0C - Phase 0 Foundation)

Tests:
- Adapter registration and lookup
- Mode-based routing
- Live mode blocked (governance)
- Error handling (unknown modes)
"""

import pytest

from src.execution.orchestrator import ExecutionMode
from src.execution.venue_adapters.registry import AdapterRegistry
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter
from src.execution.venue_adapters.base import VenueAdapterError


class TestAdapterRegistryBasics:
    """Test basic registry operations."""

    def test_register_and_get_adapter(self):
        """Register adapter and retrieve it."""
        registry = AdapterRegistry()
        adapter = SimulatedVenueAdapter()

        registry.register(ExecutionMode.PAPER, adapter)

        retrieved = registry.get_adapter(ExecutionMode.PAPER)
        assert retrieved is adapter

    def test_register_duplicate_mode_raises_error(self):
        """Registering same mode twice should raise ValueError."""
        registry = AdapterRegistry()
        adapter1 = SimulatedVenueAdapter()
        adapter2 = SimulatedVenueAdapter()

        registry.register(ExecutionMode.PAPER, adapter1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(ExecutionMode.PAPER, adapter2)

    def test_get_unregistered_mode_raises_error(self):
        """Getting unregistered mode should raise VenueAdapterError."""
        registry = AdapterRegistry()

        with pytest.raises(VenueAdapterError, match="No adapter registered"):
            registry.get_adapter(ExecutionMode.PAPER)

    def test_has_adapter_returns_correct_status(self):
        """has_adapter should return True/False correctly."""
        registry = AdapterRegistry()
        adapter = SimulatedVenueAdapter()

        assert not registry.has_adapter(ExecutionMode.PAPER)

        registry.register(ExecutionMode.PAPER, adapter)

        assert registry.has_adapter(ExecutionMode.PAPER)
        assert not registry.has_adapter(ExecutionMode.SHADOW)

    def test_list_modes_returns_registered_modes(self):
        """list_modes should return all registered modes."""
        registry = AdapterRegistry()
        adapter = SimulatedVenueAdapter()

        registry.register(ExecutionMode.PAPER, adapter)
        registry.register(ExecutionMode.SHADOW, adapter)

        modes = registry.list_modes()
        assert ExecutionMode.PAPER in modes
        assert ExecutionMode.SHADOW in modes
        assert len(modes) == 2


class TestAdapterRegistryDefaultFactory:
    """Test create_default() factory."""

    def test_create_default_has_paper_shadow_testnet(self):
        """Default registry should have PAPER/SHADOW/TESTNET adapters."""
        registry = AdapterRegistry.create_default()

        assert registry.has_adapter(ExecutionMode.PAPER)
        assert registry.has_adapter(ExecutionMode.SHADOW)
        assert registry.has_adapter(ExecutionMode.TESTNET)

    def test_create_default_does_not_have_live_blocked(self):
        """Default registry should NOT register LIVE_BLOCKED."""
        registry = AdapterRegistry.create_default()

        assert not registry.has_adapter(ExecutionMode.LIVE_BLOCKED)

    def test_create_default_adapters_are_simulated(self):
        """Default adapters should be SimulatedVenueAdapter."""
        registry = AdapterRegistry.create_default()

        paper_adapter = registry.get_adapter(ExecutionMode.PAPER)
        assert isinstance(paper_adapter, SimulatedVenueAdapter)

        shadow_adapter = registry.get_adapter(ExecutionMode.SHADOW)
        assert isinstance(shadow_adapter, SimulatedVenueAdapter)


class TestAdapterRegistryLiveBlocked:
    """Test live mode governance block."""

    def test_get_live_blocked_mode_raises_error(self):
        """Getting LIVE_BLOCKED mode should raise VenueAdapterError (governance block)."""
        registry = AdapterRegistry.create_default()

        with pytest.raises(VenueAdapterError, match="Live execution is governance-blocked"):
            registry.get_adapter(ExecutionMode.LIVE_BLOCKED)

    def test_cannot_register_live_blocked_mode(self):
        """Registering LIVE_BLOCKED should succeed, but get_adapter should still block."""
        registry = AdapterRegistry()
        adapter = SimulatedVenueAdapter()

        # Registration succeeds
        registry.register(ExecutionMode.LIVE_BLOCKED, adapter)

        # But get_adapter should still block (governance override)
        with pytest.raises(VenueAdapterError, match="governance-blocked"):
            registry.get_adapter(ExecutionMode.LIVE_BLOCKED)


class TestAdapterRegistryTestingFactory:
    """Test create_for_testing() factory."""

    def test_create_for_testing_with_fills_disabled(self):
        """Testing factory should support fills disabled."""
        registry = AdapterRegistry.create_for_testing(enable_fills=False)

        adapter = registry.get_adapter(ExecutionMode.PAPER)
        assert isinstance(adapter, SimulatedVenueAdapter)
        assert not adapter.enable_fills

    def test_create_for_testing_with_custom_market_prices(self):
        """Testing factory should support custom market prices."""
        custom_prices = {"BTC/EUR": pytest.importorskip("decimal").Decimal("100000.00")}
        registry = AdapterRegistry.create_for_testing(market_prices=custom_prices)

        adapter = registry.get_adapter(ExecutionMode.PAPER)
        assert adapter.market_prices["BTC/EUR"] == custom_prices["BTC/EUR"]
