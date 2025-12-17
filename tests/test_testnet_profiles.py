# tests/test_testnet_profiles.py
"""
Tests fuer src/live/testnet_profiles.py (Phase 37)

Testet:
- TestnetSessionProfile Dataclass
- Profile-Validierung
- Profile-Loader aus Config
- Profile-Hilfsfunktionen
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.peak_config import load_config
from src.live.testnet_profiles import (
    TestnetSessionProfile,
    get_default_profiles,
    get_profiles_summary,
    get_testnet_profile,
    list_testnet_profiles,
    load_testnet_profiles,
    validate_profile,
)

# =============================================================================
# TestnetSessionProfile Tests
# =============================================================================


class TestTestnetSessionProfile:
    """Tests fuer TestnetSessionProfile Dataclass."""

    def test_default_values(self):
        """Test: Default-Werte."""
        profile = TestnetSessionProfile(id="test")
        assert profile.id == "test"
        assert profile.description == ""
        assert profile.strategy == "ma_crossover"
        assert profile.symbol == "BTC/EUR"
        assert profile.timeframe == "1m"
        assert profile.duration_minutes is None
        assert profile.max_notional is None
        assert profile.max_trades is None

    def test_custom_values(self):
        """Test: Custom-Werte."""
        profile = TestnetSessionProfile(
            id="custom",
            description="Custom Test",
            strategy="rsi_strategy",
            symbol="ETH/EUR",
            timeframe="5m",
            duration_minutes=60,
            max_notional=500.0,
            max_trades=20,
        )
        assert profile.id == "custom"
        assert profile.description == "Custom Test"
        assert profile.strategy == "rsi_strategy"
        assert profile.symbol == "ETH/EUR"
        assert profile.timeframe == "5m"
        assert profile.duration_minutes == 60
        assert profile.max_notional == 500.0
        assert profile.max_trades == 20

    def test_to_dict(self):
        """Test: to_dict() Konvertierung."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            duration_minutes=30,
        )
        d = profile.to_dict()
        assert d["id"] == "test"
        assert d["strategy"] == "ma_crossover"
        assert d["symbol"] == "BTC/EUR"
        assert d["duration_minutes"] == 30

    def test_from_dict(self):
        """Test: from_dict() Erstellung."""
        data = {
            "description": "Test Profile",
            "strategy": "momentum_1h",
            "symbol": "ETH/EUR",
            "timeframe": "15m",
            "duration_minutes": 120,
            "max_notional": 1000.0,
            "max_trades": 50,
        }
        profile = TestnetSessionProfile.from_dict("my_profile", data)

        assert profile.id == "my_profile"
        assert profile.description == "Test Profile"
        assert profile.strategy == "momentum_1h"
        assert profile.symbol == "ETH/EUR"
        assert profile.timeframe == "15m"
        assert profile.duration_minutes == 120
        assert profile.max_notional == 1000.0
        assert profile.max_trades == 50

    def test_from_dict_extra_params(self):
        """Test: from_dict() sammelt unbekannte Felder in extra_params."""
        data = {
            "strategy": "ma_crossover",
            "symbol": "BTC/EUR",
            "custom_param1": "value1",
            "custom_param2": 42,
        }
        profile = TestnetSessionProfile.from_dict("test", data)

        assert profile.extra_params == {"custom_param1": "value1", "custom_param2": 42}

    def test_with_overrides(self):
        """Test: with_overrides() erstellt modifizierte Kopie."""
        original = TestnetSessionProfile(
            id="original",
            strategy="ma_crossover",
            duration_minutes=60,
            max_notional=500.0,
        )

        modified = original.with_overrides(
            duration_minutes=30,
            max_notional=300.0,
        )

        # Original unveraendert
        assert original.duration_minutes == 60
        assert original.max_notional == 500.0

        # Modifiziert hat neue Werte
        assert modified.duration_minutes == 30
        assert modified.max_notional == 300.0

        # Andere Felder unveraendert
        assert modified.id == "original"
        assert modified.strategy == "ma_crossover"


# =============================================================================
# Profile Validation Tests
# =============================================================================


class TestProfileValidation:
    """Tests fuer validate_profile()."""

    def test_valid_profile(self):
        """Test: Gueltiges Profil passiert Validierung."""
        profile = TestnetSessionProfile(
            id="valid",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            duration_minutes=60,
            max_notional=500.0,
        )
        result = validate_profile(profile)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_id(self):
        """Test: Fehlende ID ist Fehler."""
        profile = TestnetSessionProfile(
            id="",
            strategy="ma_crossover",
            symbol="BTC/EUR",
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("ID" in e for e in result.errors)

    def test_missing_strategy(self):
        """Test: Fehlende Strategie ist Fehler."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="",
            symbol="BTC/EUR",
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("Strategie" in e for e in result.errors)

    def test_missing_symbol(self):
        """Test: Fehlendes Symbol ist Fehler."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="",
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("Symbol" in e for e in result.errors)

    def test_negative_duration(self):
        """Test: Negative Duration ist Fehler."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            duration_minutes=-10,
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("duration_minutes" in e for e in result.errors)

    def test_negative_max_notional(self):
        """Test: Negatives max_notional ist Fehler."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            max_notional=-100.0,
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("max_notional" in e for e in result.errors)

    def test_invalid_position_fraction(self):
        """Test: position_fraction ausserhalb 0-1 ist Fehler."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            position_fraction=1.5,
        )
        result = validate_profile(profile)
        assert result.valid is False
        assert any("position_fraction" in e for e in result.errors)

    def test_unknown_timeframe_is_warning(self):
        """Test: Unbekannter Timeframe ist Warnung (kein Fehler)."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            timeframe="2h",  # Unbekannt
        )
        result = validate_profile(profile)
        assert result.valid is True  # Immer noch gueltig
        assert any("Timeframe" in w for w in result.warnings)

    def test_missing_limits_is_warning(self):
        """Test: Fehlende Limits sind Warnungen."""
        profile = TestnetSessionProfile(
            id="test",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            # Keine duration_minutes oder max_notional
        )
        result = validate_profile(profile)
        assert result.valid is True
        assert any("duration_minutes" in w for w in result.warnings)
        assert any("max_notional" in w for w in result.warnings)


# =============================================================================
# Profile Loader Tests
# =============================================================================


class TestProfileLoader:
    """Tests fuer Profile-Loader-Funktionen."""

    def test_load_testnet_profiles_from_test_config(self, test_config_path):
        """Test: Profile werden aus Test-Config geladen."""
        cfg = load_config(test_config_path)
        profiles = load_testnet_profiles(cfg)

        assert "test_profile" in profiles
        assert "test_profile_eth" in profiles

    def test_profile_values_from_config(self, test_config_path):
        """Test: Profil-Werte aus Config sind korrekt."""
        cfg = load_config(test_config_path)
        profiles = load_testnet_profiles(cfg)

        profile = profiles["test_profile"]
        assert profile.strategy == "ma_crossover"
        assert profile.symbol == "BTC/EUR"
        assert profile.timeframe == "1m"
        assert profile.duration_minutes == 5
        assert profile.max_notional == 100.0
        assert profile.max_trades == 5
        assert "Test-Profil" in profile.description

    def test_get_testnet_profile(self, test_config_path):
        """Test: get_testnet_profile() findet einzelnes Profil."""
        cfg = load_config(test_config_path)

        profile = get_testnet_profile(cfg, "test_profile")
        assert profile is not None
        assert profile.id == "test_profile"

        # Nicht existierendes Profil
        missing = get_testnet_profile(cfg, "non_existent")
        assert missing is None

    def test_list_testnet_profiles(self, test_config_path):
        """Test: list_testnet_profiles() gibt sortierte Liste."""
        cfg = load_config(test_config_path)
        profile_ids = list_testnet_profiles(cfg)

        assert "test_profile" in profile_ids
        assert "test_profile_eth" in profile_ids
        assert profile_ids == sorted(profile_ids)

    def test_get_profiles_summary(self, test_config_path):
        """Test: get_profiles_summary() gibt formatierten String."""
        cfg = load_config(test_config_path)
        summary = get_profiles_summary(cfg)

        assert "test_profile" in summary
        assert "ma_crossover" in summary
        assert "BTC/EUR" in summary


# =============================================================================
# Default Profiles Tests
# =============================================================================


class TestDefaultProfiles:
    """Tests fuer eingebaute Default-Profile."""

    def test_get_default_profiles(self):
        """Test: Default-Profile existieren."""
        defaults = get_default_profiles()

        assert "quick_test" in defaults
        assert "btc_intraday" in defaults
        assert "eth_swing" in defaults

    def test_default_profile_validation(self):
        """Test: Default-Profile sind alle gueltig."""
        defaults = get_default_profiles()

        for profile_id, profile in defaults.items():
            result = validate_profile(profile)
            assert result.valid, f"Default-Profil '{profile_id}' ist ungueltig: {result.errors}"

    def test_quick_test_profile(self):
        """Test: quick_test Profil hat erwartete Werte."""
        defaults = get_default_profiles()
        profile = defaults["quick_test"]

        assert profile.duration_minutes == 5
        assert profile.max_notional == 100.0
        assert profile.max_trades == 5
        assert profile.symbol == "BTC/EUR"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_config_path():
    """Gibt den Pfad zur Test-Config zurueck."""
    return Path(__file__).parent.parent / "config" / "config.test.toml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
