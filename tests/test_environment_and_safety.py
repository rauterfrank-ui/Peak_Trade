# tests/test_environment_and_safety.py
"""
Peak_Trade: Tests für Environment-Abstraktion und Safety-Layer (Phase 17)
=========================================================================

Testet:
- EnvironmentConfig und TradingEnvironment
- SafetyGuard und Safety-Exceptions
- TestnetOrderExecutor (Dry-Run)
- LiveOrderExecutor (Stub)
- ExchangeOrderExecutor

WICHTIG: Diese Tests verifizieren, dass KEINE echten Orders gesendet werden.
"""

import pytest
from datetime import datetime, timezone

from src.core.environment import (
    TradingEnvironment,
    EnvironmentConfig,
    LIVE_CONFIRM_TOKEN,
    get_environment_from_config,
    create_default_environment,
    is_paper,
    is_testnet,
    is_live,
)
from src.core.peak_config import PeakConfig
from src.live.safety import (
    SafetyGuard,
    SafetyAuditEntry,
    SafetyBlockedError,
    LiveTradingDisabledError,
    ConfirmTokenInvalidError,
    LiveNotImplementedError,
    TestnetDryRunOnlyError,
    PaperModeOrderError,
    create_safety_guard,
)
from src.orders.base import OrderRequest
from src.orders.exchange import (
    TestnetOrderExecutor,
    LiveOrderExecutor,
    ExchangeOrderExecutor,
    EXECUTION_MODE_TESTNET_DRY_RUN,
)


# =============================================================================
# TradingEnvironment Tests
# =============================================================================


class TestTradingEnvironment:
    """Tests für TradingEnvironment Enum."""

    def test_environment_values(self):
        """Environment-Werte sind korrekt."""
        assert TradingEnvironment.PAPER.value == "paper"
        assert TradingEnvironment.TESTNET.value == "testnet"
        assert TradingEnvironment.LIVE.value == "live"

    def test_environment_from_string(self):
        """Environment kann aus String erstellt werden."""
        assert TradingEnvironment("paper") == TradingEnvironment.PAPER
        assert TradingEnvironment("testnet") == TradingEnvironment.TESTNET
        assert TradingEnvironment("live") == TradingEnvironment.LIVE

    def test_environment_is_string(self):
        """Environment ist ein str-Subtyp."""
        assert isinstance(TradingEnvironment.PAPER, str)
        assert TradingEnvironment.PAPER == "paper"


# =============================================================================
# EnvironmentConfig Tests
# =============================================================================


class TestEnvironmentConfig:
    """Tests für EnvironmentConfig Dataclass."""

    def test_default_is_paper(self):
        """Default-Environment ist Paper."""
        config = EnvironmentConfig()
        assert config.environment == TradingEnvironment.PAPER
        assert config.is_paper is True
        assert config.is_testnet is False
        assert config.is_live is False

    def test_string_to_enum_conversion(self):
        """String wird automatisch zu Enum konvertiert."""
        config = EnvironmentConfig(environment="testnet")  # type: ignore
        assert config.environment == TradingEnvironment.TESTNET

    def test_safety_defaults(self):
        """Safety-Defaults sind korrekt."""
        config = EnvironmentConfig()
        assert config.enable_live_trading is False
        assert config.require_confirm_token is True
        assert config.confirm_token is None
        assert config.testnet_dry_run is True

    def test_paper_never_allows_real_orders(self):
        """Paper-Modus erlaubt niemals echte Orders."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
            enable_live_trading=True,  # Sollte ignoriert werden
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        assert config.allows_real_orders is False

    def test_testnet_dry_run_blocks_orders(self):
        """Testnet mit dry_run=True blockt echte Orders."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,
        )
        assert config.allows_real_orders is False

    def test_testnet_without_dry_run_would_allow(self):
        """Testnet ohne dry_run würde theoretisch erlauben."""
        # In Phase 17 ist dies aber durch SafetyGuard blockiert
        config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=False,
        )
        assert config.allows_real_orders is True

    def test_live_requires_enable_flag(self):
        """Live erfordert enable_live_trading=True."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        assert config.allows_real_orders is False

    def test_live_requires_token(self):
        """Live erfordert korrekten Confirm-Token."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token="wrong_token",
        )
        assert config.allows_real_orders is False

    def test_live_with_correct_token(self):
        """Live mit korrektem Token und allen Gates würde erlauben."""
        # Phase 71: Alle Gates müssen explizit gesetzt werden
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=True,  # Gate 2 muss explizit aktiviert sein
            live_dry_run_mode=False,  # Dry-Run muss deaktiviert sein
        )
        assert config.allows_real_orders is True

    def test_live_blocked_by_dry_run_mode(self):
        """Live mit live_dry_run_mode=True blockiert echte Orders."""
        # Phase 71: Default-Verhalten - Live ist im Dry-Run-Modus
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=True,
            live_dry_run_mode=True,  # Phase 71 Default - blockiert echte Orders
        )
        assert config.allows_real_orders is False

    def test_live_blocked_by_armed_flag(self):
        """Live mit live_mode_armed=False blockiert echte Orders."""
        # Phase 71: Gate 2 muss explizit aktiviert sein
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=False,  # Gate 2 blockiert
            live_dry_run_mode=False,
        )
        assert config.allows_real_orders is False

    def test_validate_confirm_token(self):
        """Confirm-Token-Validierung funktioniert."""
        config_valid = EnvironmentConfig(
            confirm_token=LIVE_CONFIRM_TOKEN,
            require_confirm_token=True,
        )
        assert config_valid.validate_confirm_token() is True

        config_invalid = EnvironmentConfig(
            confirm_token="wrong",
            require_confirm_token=True,
        )
        assert config_invalid.validate_confirm_token() is False

        config_not_required = EnvironmentConfig(
            confirm_token=None,
            require_confirm_token=False,
        )
        assert config_not_required.validate_confirm_token() is True


# =============================================================================
# Environment Helper Functions Tests
# =============================================================================


class TestEnvironmentHelpers:
    """Tests für Environment Helper-Funktionen."""

    def test_create_default_environment(self):
        """Default-Environment ist Paper mit Safety-Defaults."""
        config = create_default_environment()
        assert config.is_paper is True
        assert config.enable_live_trading is False
        assert config.testnet_dry_run is True

    def test_is_paper_helper(self):
        """is_paper() Helper funktioniert."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        assert is_paper(config) is True
        assert is_testnet(config) is False
        assert is_live(config) is False

    def test_is_testnet_helper(self):
        """is_testnet() Helper funktioniert."""
        config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        assert is_paper(config) is False
        assert is_testnet(config) is True
        assert is_live(config) is False

    def test_is_live_helper(self):
        """is_live() Helper funktioniert."""
        config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        assert is_paper(config) is False
        assert is_testnet(config) is False
        assert is_live(config) is True

    def test_get_environment_from_config(self):
        """Environment wird korrekt aus PeakConfig gelesen."""
        # Mock-Config mit environment-Block
        raw = {
            "environment": {
                "mode": "testnet",
                "enable_live_trading": True,
                "testnet_dry_run": False,
            }
        }
        peak_config = PeakConfig(raw=raw)
        env_config = get_environment_from_config(peak_config)

        assert env_config.environment == TradingEnvironment.TESTNET
        assert env_config.enable_live_trading is True
        assert env_config.testnet_dry_run is False

    def test_get_environment_from_config_defaults(self):
        """Fehlende Config-Werte verwenden Defaults."""
        peak_config = PeakConfig(raw={})
        env_config = get_environment_from_config(peak_config)

        assert env_config.environment == TradingEnvironment.PAPER
        assert env_config.enable_live_trading is False


# =============================================================================
# SafetyGuard Tests
# =============================================================================


class TestSafetyGuard:
    """Tests für SafetyGuard Klasse."""

    def test_paper_mode_blocks_orders(self):
        """Paper-Modus blockt Order-Platzierung."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=config)

        with pytest.raises(PaperModeOrderError):
            guard.ensure_may_place_order()

    def test_testnet_dry_run_blocks_orders(self):
        """Testnet Dry-Run blockt Order-Platzierung."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,
        )
        guard = SafetyGuard(env_config=config)

        with pytest.raises(TestnetDryRunOnlyError):
            guard.ensure_may_place_order(is_testnet=True)

    def test_testnet_without_dry_run_still_blocked_in_phase17(self):
        """Testnet ohne Dry-Run ist in Phase 17 trotzdem blockiert."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=False,
        )
        guard = SafetyGuard(env_config=config)

        # LiveNotImplementedError weil echte Testnet-Orders nicht implementiert
        with pytest.raises(LiveNotImplementedError):
            guard.ensure_may_place_order(is_testnet=True)

    def test_live_mode_disabled_blocks(self):
        """Live-Modus ohne enable_live_trading blockt."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        guard = SafetyGuard(env_config=config)

        with pytest.raises(LiveTradingDisabledError):
            guard.ensure_may_place_order()

    def test_live_mode_wrong_token_blocks(self):
        """Live-Modus mit falschem Token blockt."""
        # Phase 71: Alle Gates müssen aktiv sein, damit Token-Check erreicht wird
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token="wrong_token",
            live_mode_armed=True,  # Gate 2 aktiv, damit Token-Check erreicht wird
            live_dry_run_mode=False,  # Dry-Run deaktiviert
        )
        guard = SafetyGuard(env_config=config)

        with pytest.raises(ConfirmTokenInvalidError):
            guard.ensure_may_place_order()

    def test_live_mode_correct_token_still_blocked_in_phase71(self):
        """Live mit korrektem Token ist in Phase 71 blockiert (not implemented)."""
        # Phase 71: Alle Gates aktiv, aber LiveNotImplementedError am Ende
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=True,  # Gate 2 aktiv
            live_dry_run_mode=False,  # Dry-Run deaktiviert
        )
        guard = SafetyGuard(env_config=config)

        # LiveNotImplementedError weil Live-Trading nicht implementiert
        with pytest.raises(LiveNotImplementedError):
            guard.ensure_may_place_order()

    def test_live_mode_blocked_by_armed_flag(self):
        """Live-Modus mit live_mode_armed=False blockt."""
        # Phase 71: Gate 2 blockiert bevor Token-Check
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=False,  # Gate 2 blockiert
            live_dry_run_mode=False,
        )
        guard = SafetyGuard(env_config=config)

        with pytest.raises(LiveTradingDisabledError):
            guard.ensure_may_place_order()

    def test_ensure_not_live_in_paper(self):
        """ensure_not_live() passiert im Paper-Modus."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=config)

        # Sollte keine Exception werfen
        guard.ensure_not_live()

    def test_ensure_not_live_in_live_mode(self):
        """ensure_not_live() blockiert im Live-Modus."""
        config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=config)

        with pytest.raises(SafetyBlockedError):
            guard.ensure_not_live()

    def test_ensure_confirm_token_valid(self):
        """ensure_confirm_token() passiert bei validem Token."""
        config = EnvironmentConfig(
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard = SafetyGuard(env_config=config)

        guard.ensure_confirm_token()  # Keine Exception

    def test_ensure_confirm_token_invalid(self):
        """ensure_confirm_token() blockiert bei invalidem Token."""
        config = EnvironmentConfig(
            require_confirm_token=True,
            confirm_token="wrong",
        )
        guard = SafetyGuard(env_config=config)

        with pytest.raises(ConfirmTokenInvalidError):
            guard.ensure_confirm_token()

    def test_may_use_dry_run_always_true(self):
        """may_use_dry_run() ist immer True."""
        for env in TradingEnvironment:
            config = EnvironmentConfig(environment=env)
            guard = SafetyGuard(env_config=config)
            assert guard.may_use_dry_run() is True

    def test_get_effective_mode(self):
        """get_effective_mode() gibt korrekten Modus zurück."""
        paper_guard = SafetyGuard(
            env_config=EnvironmentConfig(environment=TradingEnvironment.PAPER)
        )
        assert paper_guard.get_effective_mode() == "paper"

        testnet_guard = SafetyGuard(
            env_config=EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        )
        assert testnet_guard.get_effective_mode() == "dry_run"

        # Phase 71: Live mit Default live_dry_run_mode=True gibt "live_dry_run"
        live_guard = SafetyGuard(env_config=EnvironmentConfig(environment=TradingEnvironment.LIVE))
        assert live_guard.get_effective_mode() == "live_dry_run"

        # Live mit live_dry_run_mode=False gibt "blocked"
        live_guard_blocked = SafetyGuard(
            env_config=EnvironmentConfig(
                environment=TradingEnvironment.LIVE,
                live_dry_run_mode=False,
            )
        )
        assert live_guard_blocked.get_effective_mode() == "blocked"

    def test_audit_log_is_populated(self):
        """Audit-Log wird bei Checks befüllt."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=config)

        try:
            guard.ensure_may_place_order()
        except PaperModeOrderError:
            pass

        log = guard.get_audit_log()
        assert len(log) == 1
        assert log[0].action.startswith("place_order")
        assert log[0].allowed is False

    def test_audit_log_clear(self):
        """Audit-Log kann geleert werden."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=config)

        guard.may_use_dry_run()  # Erzeugt Eintrag
        assert len(guard.get_audit_log()) > 0

        guard.clear_audit_log()
        assert len(guard.get_audit_log()) == 0


class TestCreateSafetyGuard:
    """Tests für create_safety_guard Factory."""

    def test_create_with_default(self):
        """Factory mit Default erstellt Paper-Guard."""
        guard = create_safety_guard()
        assert guard.env_config.is_paper is True

    def test_create_with_config(self):
        """Factory mit Config erstellt entsprechenden Guard."""
        config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        guard = create_safety_guard(env_config=config)
        assert guard.env_config.is_testnet is True


# =============================================================================
# TestnetOrderExecutor Tests
# =============================================================================


class TestTestnetOrderExecutor:
    """Tests für TestnetOrderExecutor (Dry-Run)."""

    @pytest.fixture
    def testnet_executor(self):
        """Erstellt einen Testnet-Executor für Tests."""
        config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        guard = SafetyGuard(env_config=config)
        return TestnetOrderExecutor(
            safety_guard=guard,
            simulated_prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
        )

    @pytest.fixture
    def sample_order(self):
        """Erstellt eine Test-OrderRequest."""
        return OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="market",
        )

    def test_dry_run_creates_result(self, testnet_executor, sample_order):
        """Dry-Run erzeugt OrderExecutionResult."""
        result = testnet_executor.execute_order(sample_order)

        assert result.status == "filled"
        assert result.metadata["mode"] == EXECUTION_MODE_TESTNET_DRY_RUN
        assert result.metadata["dry_run"] is True
        assert result.metadata["environment"] == "testnet"

    def test_dry_run_no_api_calls(self, testnet_executor, sample_order):
        """Dry-Run macht keine echten API-Calls."""
        # Wenn echte API-Calls passieren würden, würde es crashen
        # (keine Credentials, keine Verbindung)
        result = testnet_executor.execute_order(sample_order)
        assert result is not None
        assert "note" in result.metadata

    def test_dry_run_uses_simulated_price(self, testnet_executor, sample_order):
        """Dry-Run verwendet simulierten Preis."""
        result = testnet_executor.execute_order(sample_order)

        assert result.fill is not None
        # Preis sollte nahe 50000 sein (mit Slippage)
        assert 49000 < result.fill.price < 51000

    def test_missing_price_rejects(self, testnet_executor):
        """Order für Symbol ohne Preis wird rejected."""
        order = OrderRequest(
            symbol="XRP/EUR",  # Kein simulierter Preis
            side="buy",
            quantity=100,
        )
        result = testnet_executor.execute_order(order)

        assert result.status == "rejected"
        assert "no_simulated_price" in result.reason

    def test_execution_count_increments(self, testnet_executor, sample_order):
        """Execution-Counter wird inkrementiert."""
        assert testnet_executor.get_execution_count() == 0

        testnet_executor.execute_order(sample_order)
        assert testnet_executor.get_execution_count() == 1

        testnet_executor.execute_order(sample_order)
        assert testnet_executor.get_execution_count() == 2

    def test_order_log_populated(self, testnet_executor, sample_order):
        """Order-Log wird befüllt."""
        testnet_executor.execute_order(sample_order)
        testnet_executor.execute_order(sample_order)

        log = testnet_executor.get_order_log()
        assert len(log) == 2
        assert log[0].environment == TradingEnvironment.TESTNET

    def test_multiple_orders(self, testnet_executor):
        """execute_orders() verarbeitet mehrere Orders."""
        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1),
            OrderRequest(symbol="ETH/EUR", side="sell", quantity=1.0),
        ]

        results = testnet_executor.execute_orders(orders)
        assert len(results) == 2
        assert all(r.metadata["dry_run"] is True for r in results)

    def test_set_simulated_price(self, testnet_executor):
        """Simulierter Preis kann gesetzt werden."""
        testnet_executor.set_simulated_price("XRP/EUR", 0.5)
        assert testnet_executor.get_simulated_price("XRP/EUR") == 0.5

    def test_reset_clears_state(self, testnet_executor, sample_order):
        """reset() setzt den Executor zurück."""
        testnet_executor.execute_order(sample_order)
        assert testnet_executor.get_execution_count() > 0
        assert len(testnet_executor.get_order_log()) > 0

        testnet_executor.reset()
        assert testnet_executor.get_execution_count() == 0
        assert len(testnet_executor.get_order_log()) == 0


# =============================================================================
# LiveOrderExecutor Tests
# =============================================================================


class TestLiveOrderExecutor:
    """Tests für LiveOrderExecutor (Phase 71: Dry-Run)."""

    @pytest.fixture
    def live_executor(self):
        """Erstellt einen Live-Executor für Tests (Dry-Run Mode)."""
        # Phase 71: LiveOrderExecutor macht Dry-Run statt zu werfen
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_dry_run_mode=True,  # Phase 71 Default
        )
        guard = SafetyGuard(env_config=config)
        return LiveOrderExecutor(
            safety_guard=guard,
            simulated_prices={"BTC/EUR": 50000.0},
            dry_run_mode=True,  # Phase 71: Immer Dry-Run
        )

    @pytest.fixture
    def sample_order(self):
        """Erstellt eine Test-OrderRequest."""
        return OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )

    def test_live_executor_dry_run_mode(self, live_executor, sample_order):
        """LiveOrderExecutor im Dry-Run-Modus führt simuliert aus."""
        # Phase 71: Dry-Run statt Exception
        result = live_executor.execute_order(sample_order)

        assert result.status == "filled"
        assert result.metadata["dry_run"] is True
        assert result.metadata["mode"] == "live_dry_run"

    def test_live_executor_multiple_orders_dry_run(self, live_executor):
        """execute_orders() führt mehrere Orders im Dry-Run aus."""
        orders = [OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)]
        results = live_executor.execute_orders(orders)

        assert len(results) == 1
        assert results[0].metadata["dry_run"] is True

    def test_execution_count_tracked(self, live_executor, sample_order):
        """Execution-Count wird korrekt gezählt."""
        live_executor.execute_order(sample_order)
        assert live_executor.get_execution_count() == 1


# =============================================================================
# ExchangeOrderExecutor Tests
# =============================================================================


class TestExchangeOrderExecutor:
    """Tests für ExchangeOrderExecutor (Unified)."""

    @pytest.fixture
    def sample_order(self):
        """Erstellt eine Test-OrderRequest."""
        return OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )

    def test_paper_mode_redirects(self, sample_order):
        """Paper-Modus gibt Redirect-Hinweis."""
        config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=config)
        executor = ExchangeOrderExecutor(safety_guard=guard)

        result = executor.execute_order(sample_order)
        assert result.status == "rejected"
        assert "use_paper_executor" in result.reason

    def test_testnet_mode_dry_run(self, sample_order):
        """Testnet-Modus führt Dry-Run aus."""
        config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        guard = SafetyGuard(env_config=config)
        executor = ExchangeOrderExecutor(
            safety_guard=guard,
            simulated_prices={"BTC/EUR": 50000.0},
        )

        result = executor.execute_order(sample_order)
        assert result.status == "filled"
        assert result.metadata["mode"] == EXECUTION_MODE_TESTNET_DRY_RUN

    def test_live_mode_blocked(self, sample_order):
        """Live-Modus mit allen Gates ist blockiert (not implemented)."""
        # Phase 71: Alle Gates aktiv, aber LiveNotImplementedError am Ende
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=True,  # Gate 2 aktiv
            live_dry_run_mode=False,  # Dry-Run deaktiviert
        )
        guard = SafetyGuard(env_config=config)
        executor = ExchangeOrderExecutor(safety_guard=guard)

        with pytest.raises(LiveNotImplementedError):
            executor.execute_order(sample_order)

    def test_live_mode_blocked_by_armed_flag(self, sample_order):
        """Live-Modus mit live_mode_armed=False blockiert."""
        # Phase 71: Gate 2 blockiert
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            live_mode_armed=False,  # Gate 2 blockiert
        )
        guard = SafetyGuard(env_config=config)
        executor = ExchangeOrderExecutor(safety_guard=guard)

        with pytest.raises(LiveTradingDisabledError):
            executor.execute_order(sample_order)


# =============================================================================
# Integration Tests
# =============================================================================


class TestSafetyIntegration:
    """Integration-Tests für das Safety-System."""

    def test_full_paper_workflow(self):
        """Kompletter Paper-Workflow funktioniert."""
        from src.orders import PaperOrderExecutor, PaperMarketContext

        # Paper-Setup
        ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0})
        executor = PaperOrderExecutor(market_context=ctx)

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        result = executor.execute_order(order)

        assert result.status == "filled"
        assert result.metadata["mode"] == "paper"

    def test_safety_guard_with_config_loader(self):
        """SafetyGuard mit Config-Loader funktioniert."""
        # Simuliere Config mit environment-Block
        raw = {"environment": {"mode": "paper", "testnet_dry_run": True}}
        peak_config = PeakConfig(raw=raw)

        env_config = get_environment_from_config(peak_config)
        guard = SafetyGuard(env_config=env_config)

        # Paper sollte blocken
        with pytest.raises(PaperModeOrderError):
            guard.ensure_may_place_order()

    def test_no_real_orders_possible(self):
        """Verifiziert dass keine echten Orders möglich sind."""
        # Teste alle Umgebungen
        for env in TradingEnvironment:
            config = EnvironmentConfig(
                environment=env,
                enable_live_trading=True,
                confirm_token=LIVE_CONFIRM_TOKEN,
                testnet_dry_run=False,  # Auch ohne Dry-Run
            )
            guard = SafetyGuard(env_config=config)

            # Alle sollten Exceptions werfen (Phase 17)
            with pytest.raises(SafetyBlockedError):
                guard.ensure_may_place_order()
