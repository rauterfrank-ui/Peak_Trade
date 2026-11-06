# tests/test_phase71_live_execution_design.py
"""
Peak_Trade: Tests für Phase 71 - Live-Execution-Design & Gating
================================================================

Testet das Design und die Gating-Mechanismen für Live-Execution,
ohne echte Live-Orders zu aktivieren.

Phase 71: Live-Execution-Path existiert als Design/Dry-Run.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
    create_default_environment,
)
from src.live.safety import (
    SafetyGuard,
    LiveTradingDisabledError,
    LiveNotImplementedError,
    ConfirmTokenInvalidError,
    is_live_execution_allowed,
)
from src.orders.base import OrderRequest
from src.orders.exchange import (
    LiveOrderExecutor,
    TestnetOrderExecutor,
    create_order_executor,
)
from src.orders.paper import PaperOrderExecutor


class TestLiveExecutionDesign:
    """Tests für Live-Execution-Design (Phase 71)."""

    def test_live_environment_config_has_new_fields(self):
        """Test: EnvironmentConfig hat Phase-71-Felder."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_mode_armed=False,
            live_dry_run_mode=True,
            max_live_notional_per_order=1000.0,
            max_live_notional_total=5000.0,
            live_trade_min_size=10.0,
        )

        assert env.live_mode_armed is False
        assert env.live_dry_run_mode is True
        assert env.max_live_notional_per_order == 1000.0
        assert env.max_live_notional_total == 5000.0
        assert env.live_trade_min_size == 10.0

    def test_live_executor_dry_run_mode(self):
        """Test: LiveOrderExecutor im Dry-Run-Modus."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)
        executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)

        assert executor.is_dry_run is True

        # Setze simulierten Preis
        executor.set_simulated_price("BTC/EUR", 50000.0)

        # Order ausführen (sollte Dry-Run sein)
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )
        result = executor.execute_order(order)

        # Sollte "filled" sein (Dry-Run)
        assert result.status == "filled"
        assert result.metadata["mode"] == "live_dry_run"
        assert result.metadata["dry_run"] is True
        assert result.metadata["phase"] == "71"
        assert "KEIN echter API-Call" in result.metadata["note"]

        # Log sollte Eintrag haben
        log = executor.get_order_log()
        assert len(log) == 1
        assert log[0].environment == TradingEnvironment.LIVE

    def test_live_executor_no_real_orders(self):
        """Test: LiveOrderExecutor sendet keine echten Orders."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)
        executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)

        executor.set_simulated_price("BTC/EUR", 50000.0)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )
        result = executor.execute_order(order)

        # Metadata sollte klarstellen, dass es Dry-Run ist
        assert result.metadata["dry_run"] is True
        assert "Phase 71" in result.metadata["note"]
        assert "KEIN echter API-Call" in result.metadata["note"]

    def test_create_order_executor_paper(self):
        """Test: create_order_executor() für Paper-Modus."""
        env = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        executor = create_order_executor(env)

        assert isinstance(executor, PaperOrderExecutor)

    def test_create_order_executor_testnet(self):
        """Test: create_order_executor() für Testnet-Modus."""
        env = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        executor = create_order_executor(env)

        assert isinstance(executor, TestnetOrderExecutor)

    def test_create_order_executor_live(self):
        """Test: create_order_executor() für Live-Modus (Phase 71: Dry-Run)."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        executor = create_order_executor(env)

        assert isinstance(executor, LiveOrderExecutor)
        assert executor.is_dry_run is True

    def test_safety_guard_two_stage_gating(self):
        """Test: Zweistufiges Gating für Live-Modus."""
        # Gate 1: enable_live_trading = False
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
            live_mode_armed=False,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)

        with pytest.raises(LiveTradingDisabledError) as exc_info:
            guard.ensure_may_place_order(is_testnet=False)
        assert "enable_live_trading=False" in str(exc_info.value)

        # Gate 2: live_mode_armed = False
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=False,  # Gate 2 blockiert
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)

        with pytest.raises(LiveTradingDisabledError) as exc_info:
            guard.ensure_may_place_order(is_testnet=False)
        assert "live_mode_armed=False" in str(exc_info.value)

    def test_safety_guard_live_dry_run_blocks_real_orders(self):
        """Test: live_dry_run_mode=True blockt echte Orders."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # Phase 71: Immer True
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard = SafetyGuard(env_config=env)

        # Auch mit allen Flags: live_dry_run_mode=True blockt echte Orders
        with pytest.raises(LiveNotImplementedError) as exc_info:
            guard.ensure_may_place_order(is_testnet=False)
        assert "live_dry_run_mode=True" in str(exc_info.value) or "Phase 71" in str(exc_info.value)

    def test_safety_guard_effective_mode_live_dry_run(self):
        """Test: get_effective_mode() für Live-Dry-Run."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)

        mode = guard.get_effective_mode()
        assert mode == "live_dry_run"

    def test_allows_real_orders_with_live_dry_run(self):
        """Test: allows_real_orders() mit live_dry_run_mode=True."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # Phase 71: Blockiert echte Orders
            confirm_token=LIVE_CONFIRM_TOKEN,
        )

        # Auch mit allen Flags: live_dry_run_mode=True blockt
        assert env.allows_real_orders is False

    def test_default_environment_has_safe_live_defaults(self):
        """Test: Default-Environment hat sichere Live-Defaults."""
        env = create_default_environment()

        assert env.live_mode_armed is False
        assert env.live_dry_run_mode is True
        assert env.max_live_notional_per_order is None
        assert env.max_live_notional_total is None
        assert env.live_trade_min_size is None

    def test_live_executor_without_price_rejects(self):
        """Test: LiveOrderExecutor ohne Preis lehnt Order ab."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)
        executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)

        # Kein Preis gesetzt
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )
        result = executor.execute_order(order)

        assert result.status == "rejected"
        assert "no_simulated_price" in result.reason

    def test_live_executor_logs_all_orders(self):
        """Test: LiveOrderExecutor loggt alle Orders."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)
        executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)

        executor.set_simulated_price("BTC/EUR", 50000.0)

        order1 = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )
        order2 = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.01,
            order_type="market",
        )

        executor.execute_order(order1)
        executor.execute_order(order2)

        log = executor.get_order_log()
        assert len(log) == 2
        assert log[0].request.side == "buy"
        assert log[1].request.side == "sell"

        assert executor.get_execution_count() == 2

    def test_is_live_execution_allowed_helper_function(self):
        """Test: is_live_execution_allowed() Helper-Funktion."""
        # Test 1: Paper-Modus -> nicht erlaubt
        env = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        allowed, reason = is_live_execution_allowed(env)
        assert allowed is False
        assert "nicht LIVE" in reason

        # Test 2: Live, aber enable_live_trading=False -> nicht erlaubt
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        allowed, reason = is_live_execution_allowed(env)
        assert allowed is False
        assert "enable_live_trading=False" in reason

        # Test 3: Live, enable_live_trading=True, aber live_mode_armed=False -> nicht erlaubt
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=False,
        )
        allowed, reason = is_live_execution_allowed(env)
        assert allowed is False
        assert "live_mode_armed=False" in reason

        # Test 4: Live, alle Gates, aber live_dry_run_mode=True -> nicht erlaubt (Phase 71)
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # Phase 71: Blockiert
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(env)
        assert allowed is False
        assert "live_dry_run_mode=True" in reason

        # Test 5: Live, alle Gates, aber falscher Token -> nicht erlaubt
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=False,  # Theoretisch möglich (Phase 71: sollte nicht vorkommen)
            require_confirm_token=True,
            confirm_token="WRONG_TOKEN",
        )
        allowed, reason = is_live_execution_allowed(env)
        assert allowed is False
        assert "confirm_token" in reason

        # Test 6: Theoretisch alle Kriterien erfüllt (Phase 71: sollte nicht vorkommen)
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=False,  # Phase 71: Sollte nicht vorkommen
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(env)
        # In Phase 71 sollte dies theoretisch True sein, aber praktisch blockiert
        # durch andere Mechanismen
        assert "theoretisch" in reason.lower() or "phase 71" in reason.lower()
