# tests/test_testnet_limits.py
"""
Tests fuer src/live/testnet_limits.py (Phase 37)

Testet:
- TestnetRunLimits, TestnetDailyLimits, TestnetSymbolPolicy
- TestnetUsageState und TestnetUsageStore
- TestnetLimitsController mit allen Check-Methoden
- Config-Loader
"""

from __future__ import annotations

import json
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.live.testnet_limits import (
    TestnetRunLimits,
    TestnetDailyLimits,
    TestnetSymbolPolicy,
    TestnetUsageState,
    TestnetUsageStore,
    TestnetLimitsController,
    TestnetCheckResult,
    load_testnet_limits_from_config,
)
from src.core.peak_config import load_config


# =============================================================================
# TestnetRunLimits Tests
# =============================================================================


class TestTestnetRunLimits:
    """Tests fuer TestnetRunLimits Dataclass."""

    def test_default_values(self):
        """Test: Default-Werte sind None."""
        limits = TestnetRunLimits()
        assert limits.max_notional_per_run is None
        assert limits.max_trades_per_run is None
        assert limits.max_duration_minutes is None

    def test_custom_values(self):
        """Test: Custom-Werte werden korrekt gesetzt."""
        limits = TestnetRunLimits(
            max_notional_per_run=1000.0,
            max_trades_per_run=50,
            max_duration_minutes=120,
        )
        assert limits.max_notional_per_run == 1000.0
        assert limits.max_trades_per_run == 50
        assert limits.max_duration_minutes == 120

    def test_to_dict(self):
        """Test: to_dict() Konvertierung."""
        limits = TestnetRunLimits(
            max_notional_per_run=500.0,
            max_trades_per_run=25,
        )
        d = limits.to_dict()
        assert d["max_notional_per_run"] == 500.0
        assert d["max_trades_per_run"] == 25
        assert d["max_duration_minutes"] is None


# =============================================================================
# TestnetDailyLimits Tests
# =============================================================================


class TestTestnetDailyLimits:
    """Tests fuer TestnetDailyLimits Dataclass."""

    def test_default_values(self):
        """Test: Default-Werte sind None."""
        limits = TestnetDailyLimits()
        assert limits.max_notional_per_day is None
        assert limits.max_trades_per_day is None

    def test_custom_values(self):
        """Test: Custom-Werte werden korrekt gesetzt."""
        limits = TestnetDailyLimits(
            max_notional_per_day=5000.0,
            max_trades_per_day=200,
        )
        assert limits.max_notional_per_day == 5000.0
        assert limits.max_trades_per_day == 200


# =============================================================================
# TestnetSymbolPolicy Tests
# =============================================================================


class TestTestnetSymbolPolicy:
    """Tests fuer TestnetSymbolPolicy Dataclass."""

    def test_default_whitelist(self):
        """Test: Default-Whitelist enthaelt BTC/EUR und ETH/EUR."""
        policy = TestnetSymbolPolicy()
        assert "BTC/EUR" in policy.allowed_symbols
        assert "ETH/EUR" in policy.allowed_symbols

    def test_custom_whitelist(self):
        """Test: Custom-Whitelist."""
        policy = TestnetSymbolPolicy(allowed_symbols={"LTC/EUR", "XRP/EUR"})
        assert "LTC/EUR" in policy.allowed_symbols
        assert "BTC/EUR" not in policy.allowed_symbols

    def test_is_allowed_positive(self):
        """Test: Symbol in Whitelist ist erlaubt."""
        policy = TestnetSymbolPolicy(allowed_symbols={"BTC/EUR", "ETH/EUR"})
        assert policy.is_allowed("BTC/EUR") is True
        assert policy.is_allowed("ETH/EUR") is True

    def test_is_allowed_negative(self):
        """Test: Symbol nicht in Whitelist ist nicht erlaubt."""
        policy = TestnetSymbolPolicy(allowed_symbols={"BTC/EUR"})
        assert policy.is_allowed("ETH/EUR") is False
        assert policy.is_allowed("LTC/EUR") is False

    def test_empty_whitelist_allows_all(self):
        """Test: Leere Whitelist erlaubt alle Symbole."""
        policy = TestnetSymbolPolicy(allowed_symbols=set())
        assert policy.is_allowed("BTC/EUR") is True
        assert policy.is_allowed("ANY/SYMBOL") is True


# =============================================================================
# TestnetUsageState Tests
# =============================================================================


class TestTestnetUsageState:
    """Tests fuer TestnetUsageState Dataclass."""

    def test_default_values(self):
        """Test: Default-Werte."""
        today = date.today()
        state = TestnetUsageState(day=today)
        assert state.day == today
        assert state.notional_used == 0.0
        assert state.trades_executed == 0
        assert state.runs_completed == 0

    def test_to_dict_from_dict_roundtrip(self):
        """Test: to_dict() und from_dict() Roundtrip."""
        today = date.today()
        state = TestnetUsageState(
            day=today,
            notional_used=1500.0,
            trades_executed=25,
            runs_completed=3,
        )

        d = state.to_dict()
        restored = TestnetUsageState.from_dict(d)

        assert restored.day == today
        assert restored.notional_used == 1500.0
        assert restored.trades_executed == 25
        assert restored.runs_completed == 3


# =============================================================================
# TestnetUsageStore Tests
# =============================================================================


class TestTestnetUsageStore:
    """Tests fuer TestnetUsageStore."""

    def test_new_day_returns_empty_state(self):
        """Test: Neuer Tag gibt leeren State zurueck."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))
            state = store.load_for_today()

            assert state.notional_used == 0.0
            assert state.trades_executed == 0
            assert state.runs_completed == 0

    def test_save_and_load(self):
        """Test: Speichern und Laden funktioniert."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))

            # State erstellen und speichern
            state = store.load_for_today()
            state.notional_used = 500.0
            state.trades_executed = 10
            state.runs_completed = 2
            store.save_for_today(state)

            # Neu laden
            loaded = store.load_for_today()
            assert loaded.notional_used == 500.0
            assert loaded.trades_executed == 10
            assert loaded.runs_completed == 2

    def test_update_usage(self):
        """Test: Usage kann aktualisiert werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))

            # Erste Nutzung
            state = store.load_for_today()
            state.notional_used += 300.0
            state.trades_executed += 5
            store.save_for_today(state)

            # Zweite Nutzung
            state = store.load_for_today()
            state.notional_used += 200.0
            state.trades_executed += 3
            store.save_for_today(state)

            # Pruefen
            final = store.load_for_today()
            assert final.notional_used == 500.0
            assert final.trades_executed == 8

    def test_different_days_separate_files(self):
        """Test: Verschiedene Tage haben separate Dateien."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))

            today = date.today()
            yesterday = today - timedelta(days=1)

            # Heute speichern
            state_today = TestnetUsageState(day=today, notional_used=100.0)
            store.save_for_day(state_today)

            # Gestern speichern
            state_yesterday = TestnetUsageState(day=yesterday, notional_used=200.0)
            store.save_for_day(state_yesterday)

            # Laden und pruefen
            loaded_today = store.load_for_day(today)
            loaded_yesterday = store.load_for_day(yesterday)

            assert loaded_today.notional_used == 100.0
            assert loaded_yesterday.notional_used == 200.0


# =============================================================================
# TestnetLimitsController Tests
# =============================================================================


class TestTestnetLimitsController:
    """Tests fuer TestnetLimitsController."""

    @pytest.fixture
    def controller(self):
        """Fixture: Controller mit Standard-Limits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))
            controller = TestnetLimitsController(
                run_limits=TestnetRunLimits(
                    max_notional_per_run=1000.0,
                    max_trades_per_run=50,
                    max_duration_minutes=120,
                ),
                daily_limits=TestnetDailyLimits(
                    max_notional_per_day=5000.0,
                    max_trades_per_day=200,
                ),
                symbol_policy=TestnetSymbolPolicy(allowed_symbols={"BTC/EUR", "ETH/EUR"}),
                usage_store=store,
            )
            yield controller

    def test_symbol_allowed(self, controller):
        """Test: Erlaubtes Symbol passiert Check."""
        result = controller.check_symbol_allowed("BTC/EUR")
        assert result.allowed is True
        assert len(result.reasons) == 0

    def test_symbol_not_allowed(self, controller):
        """Test: Nicht erlaubtes Symbol wird geblockt."""
        result = controller.check_symbol_allowed("LTC/EUR")
        assert result.allowed is False
        assert "symbol_not_allowed" in result.reasons[0]

    def test_run_limits_ok(self, controller):
        """Test: Run unter Limits passiert."""
        result = controller.check_run_limits(
            planned_notional=500.0,
            planned_trades=20,
            planned_duration_minutes=60,
        )
        assert result.allowed is True

    def test_run_limits_notional_exceeded(self, controller):
        """Test: Run ueber Notional-Limit wird geblockt."""
        result = controller.check_run_limits(planned_notional=1500.0)
        assert result.allowed is False
        assert "run_notional_exceeded" in result.reasons[0]

    def test_run_limits_trades_exceeded(self, controller):
        """Test: Run ueber Trade-Limit wird geblockt."""
        result = controller.check_run_limits(planned_trades=100)
        assert result.allowed is False
        assert "run_trades_exceeded" in result.reasons[0]

    def test_run_limits_duration_exceeded(self, controller):
        """Test: Run ueber Duration-Limit wird geblockt."""
        result = controller.check_run_limits(planned_duration_minutes=180)
        assert result.allowed is False
        assert "run_duration_exceeded" in result.reasons[0]

    def test_daily_limits_ok(self, controller):
        """Test: Daily-Limits nicht ueberschritten."""
        result = controller.check_daily_limits(
            additional_notional=1000.0,
            additional_trades=30,
        )
        assert result.allowed is True

    def test_daily_limits_notional_exceeded(self, controller):
        """Test: Daily Notional-Limit wird geblockt."""
        result = controller.check_daily_limits(additional_notional=6000.0)
        assert result.allowed is False
        assert "daily_notional_exceeded" in result.reasons[0]

    def test_daily_limits_trades_exceeded(self, controller):
        """Test: Daily Trade-Limit wird geblockt."""
        result = controller.check_daily_limits(additional_trades=250)
        assert result.allowed is False
        assert "daily_trades_exceeded" in result.reasons[0]

    def test_daily_limits_with_prior_usage(self):
        """Test: Daily-Limits beruecksichtigen vorherige Nutzung."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TestnetUsageStore(base_dir=Path(tmpdir))

            # Vorherige Nutzung eintragen
            state = store.load_for_today()
            state.notional_used = 4000.0
            store.save_for_today(state)

            controller = TestnetLimitsController(
                run_limits=TestnetRunLimits(),
                daily_limits=TestnetDailyLimits(max_notional_per_day=5000.0),
                symbol_policy=TestnetSymbolPolicy(),
                usage_store=store,
            )

            # 1500 wuerde Limit ueberschreiten (4000 + 1500 = 5500 > 5000)
            result = controller.check_daily_limits(additional_notional=1500.0)
            assert result.allowed is False
            assert "daily_notional_exceeded" in result.reasons[0]

    def test_combined_check_all_ok(self, controller):
        """Test: Kombinierter Check mit allen Limits OK."""
        result = controller.check_run_allowed(
            symbol="BTC/EUR",
            planned_notional=500.0,
            planned_trades=20,
            planned_duration_minutes=60,
        )
        assert result.allowed is True
        assert len(result.reasons) == 0

    def test_combined_check_multiple_violations(self, controller):
        """Test: Kombinierter Check mit mehreren Verletzungen."""
        result = controller.check_run_allowed(
            symbol="LTC/EUR",  # Nicht erlaubt
            planned_notional=2000.0,  # Ueber Run-Limit
            planned_trades=100,  # Ueber Run-Limit
        )
        assert result.allowed is False
        assert len(result.reasons) >= 2  # Mindestens Symbol und Notional

    def test_register_run_consumption(self, controller):
        """Test: Run-Verbrauch wird korrekt registriert."""
        # Initial leer
        usage = controller.get_daily_usage()
        assert usage.notional_used == 0.0
        assert usage.trades_executed == 0

        # Run registrieren
        controller.register_run_consumption(notional=500.0, trades=15)

        # Pruefen
        usage = controller.get_daily_usage()
        assert usage.notional_used == 500.0
        assert usage.trades_executed == 15
        assert usage.runs_completed == 1

        # Zweiter Run
        controller.register_run_consumption(notional=300.0, trades=10)

        usage = controller.get_daily_usage()
        assert usage.notional_used == 800.0
        assert usage.trades_executed == 25
        assert usage.runs_completed == 2

    def test_get_remaining_budget(self, controller):
        """Test: Remaining Budget wird korrekt berechnet."""
        # Initial
        budget = controller.get_remaining_budget()
        assert budget["remaining_notional"] == 5000.0
        assert budget["remaining_trades"] == 200

        # Nach Verbrauch
        controller.register_run_consumption(notional=1000.0, trades=50)

        budget = controller.get_remaining_budget()
        assert budget["remaining_notional"] == 4000.0
        assert budget["remaining_trades"] == 150


# =============================================================================
# Config Loader Tests
# =============================================================================


class TestLoadTestnetLimitsFromConfig:
    """Tests fuer load_testnet_limits_from_config()."""

    def test_load_from_test_config(self, test_config_path):
        """Test: Laden aus Test-Config."""
        cfg = load_config(test_config_path)
        controller = load_testnet_limits_from_config(cfg)

        # Run-Limits aus Test-Config
        assert controller.run_limits.max_notional_per_run == 500.0
        assert controller.run_limits.max_trades_per_run == 25
        assert controller.run_limits.max_duration_minutes == 60

        # Daily-Limits aus Test-Config
        assert controller.daily_limits.max_notional_per_day == 2000.0
        assert controller.daily_limits.max_trades_per_day == 100

        # Symbol-Policy aus Test-Config
        assert "BTC/EUR" in controller.symbol_policy.allowed_symbols
        assert "ETH/EUR" in controller.symbol_policy.allowed_symbols

    def test_load_with_custom_base_dir(self, test_config_path):
        """Test: Laden mit custom Base-Dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = load_config(test_config_path)
            controller = load_testnet_limits_from_config(cfg, base_dir=Path(tmpdir))

            # Controller sollte funktionieren
            result = controller.check_run_allowed(symbol="BTC/EUR", planned_notional=100.0)
            assert result.allowed is True


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_config_path():
    """Gibt den Pfad zur Test-Config zurueck."""
    return Path(__file__).parent.parent / "config" / "config.test.toml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
