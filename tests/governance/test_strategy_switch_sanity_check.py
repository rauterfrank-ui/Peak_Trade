"""
Tests für Strategy-Switch Sanity Check (Governance).

Testet die Governance-Prüfung für [live_profile.strategy_switch]:
  1. active_strategy_id ist in allowed
  2. Keine R&D-Strategien in allowed
  3. Keine unbekannten Strategy-IDs in allowed
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.governance.strategy_switch_sanity_check import (
    StrategySwitchSanityResult,
    StrategyMeta,
    run_strategy_switch_sanity_check,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Erstellt ein temporäres Config-Verzeichnis."""
    return tmp_path


def write_temp_config(temp_dir: Path, content: str) -> Path:
    """Schreibt eine temporäre Config-Datei."""
    config_path = temp_dir / "config.toml"
    config_path.write_text(content)
    return config_path


# ============================================================================
# Tests: Healthy Config
# ============================================================================


class TestHealthyConfig:
    """Tests für eine gesunde Konfiguration."""

    def test_healthy_config_returns_ok(self, temp_config_dir: Path):
        """Test: Gesunde Config → Status OK."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "rsi_reversion"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "OK"
        assert result.ok is True
        assert result.active_strategy_id == "ma_crossover"
        assert result.allowed == ["ma_crossover", "rsi_reversion"]
        assert result.invalid_strategies == []
        assert result.r_and_d_strategies == []
        assert len(result.messages) >= 1

    def test_healthy_config_with_one_strategy(self, temp_config_dir: Path):
        """Test: Gesunde Config mit nur einer Strategie → OK."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "breakout"
allowed = ["breakout"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "OK"
        assert result.active_strategy_id == "breakout"
        assert result.allowed == ["breakout"]


# ============================================================================
# Tests: Active Strategy Not in Allowed
# ============================================================================


class TestActiveNotInAllowed:
    """Tests für active_strategy_id nicht in allowed."""

    def test_active_not_in_allowed_returns_fail(self, temp_config_dir: Path):
        """Test: active_strategy_id nicht in allowed → FAIL."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "unknown_strategy"
allowed = ["ma_crossover", "rsi_reversion"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"
        assert result.has_failures is True
        assert "unknown_strategy" in result.active_strategy_id
        assert any("NICHT in der allowed-Liste" in m for m in result.messages)

    def test_empty_active_with_allowed_is_ok(self, temp_config_dir: Path):
        """Test: Leerer active_strategy_id mit allowed → OK (kein Zwang)."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = ""
allowed = ["ma_crossover"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        # Leerer active ist kein Fehler, solange allowed nicht leer ist
        assert result.status == "OK"


# ============================================================================
# Tests: R&D Strategies in Allowed
# ============================================================================


class TestRAndDStrategiesInAllowed:
    """Tests für R&D-Strategien in der allowed-Liste."""

    def test_r_and_d_in_allowed_returns_fail(self, temp_config_dir: Path):
        """Test: R&D-Strategie in allowed → FAIL."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "armstrong_cycle"]

[strategy.armstrong_cycle]
tier = "r_and_d"
is_live_ready = false
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"
        assert "armstrong_cycle" in result.r_and_d_strategies
        assert any("R&D" in m for m in result.messages)

    def test_known_r_and_d_keys_detected(self, temp_config_dir: Path):
        """Test: Bekannte R&D-Keys werden ohne Config-Block erkannt."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "el_karoui_vol_model"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
            r_and_d_strategy_keys=["el_karoui_vol_model"],  # Explizit übergeben
        )

        assert result.status == "FAIL"
        assert "el_karoui_vol_model" in result.r_and_d_strategies


# ============================================================================
# Tests: Empty Allowed List
# ============================================================================


class TestEmptyAllowedList:
    """Tests für leere allowed-Liste."""

    def test_empty_allowed_returns_fail(self, temp_config_dir: Path):
        """Test: Leere allowed-Liste → FAIL."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = []
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"
        assert any("leer" in m for m in result.messages)

    def test_missing_allowed_key_returns_fail(self, temp_config_dir: Path):
        """Test: Fehlende allowed-Key → FAIL (leere Liste)."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"


# ============================================================================
# Tests: Config Errors
# ============================================================================


class TestConfigErrors:
    """Tests für Config-Fehler."""

    def test_missing_config_file_returns_fail(self, temp_config_dir: Path):
        """Test: Nicht existierende Config → FAIL."""
        result = run_strategy_switch_sanity_check(
            config_path=str(temp_config_dir / "nonexistent.toml"),
        )

        assert result.status == "FAIL"
        assert any("nicht gefunden" in m for m in result.messages)

    def test_missing_section_returns_fail(self, temp_config_dir: Path):
        """Test: Fehlende Section → FAIL."""
        config = """
[some_other_section]
foo = "bar"
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"
        assert any("nicht in Config gefunden" in m for m in result.messages)

    def test_invalid_toml_returns_fail(self, temp_config_dir: Path):
        """Test: Ungültiges TOML → FAIL."""
        config = """
[live_profile.strategy_switch
active_strategy_id = "broken
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
        )

        assert result.status == "FAIL"
        assert any("Parse" in m or "Fehler" in m for m in result.messages)


# ============================================================================
# Tests: Too Many Strategies Warning
# ============================================================================


class TestTooManyStrategiesWarning:
    """Tests für Warnung bei zu vielen Strategien."""

    def test_many_strategies_returns_warn(self, temp_config_dir: Path):
        """Test: Viele Strategien in allowed → WARN."""
        config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "rsi_reversion", "breakout", "macd", "bollinger_bands", "momentum_1h"]
"""
        config_path = write_temp_config(temp_config_dir, config)

        result = run_strategy_switch_sanity_check(
            config_path=str(config_path),
            max_allowed_strategies_warn=3,  # Niedrigerer Threshold für Test
        )

        assert result.status == "WARN"
        assert result.has_warnings is True
        assert any("bewusst überprüfen" in m for m in result.messages)


# ============================================================================
# Tests: DataClass Properties
# ============================================================================


class TestResultProperties:
    """Tests für StrategySwitchSanityResult Properties."""

    def test_ok_property(self):
        """Test: ok Property funktioniert korrekt."""
        result = StrategySwitchSanityResult(
            status="OK",
            active_strategy_id="test",
            allowed=["test"],
            invalid_strategies=[],
            r_and_d_strategies=[],
            messages=["Alles gut"],
        )

        assert result.ok is True
        assert result.has_failures is False
        assert result.has_warnings is False

    def test_has_failures_property(self):
        """Test: has_failures Property funktioniert korrekt."""
        result = StrategySwitchSanityResult(
            status="FAIL",
            active_strategy_id="test",
            allowed=["test"],
            invalid_strategies=["unknown"],
            r_and_d_strategies=[],
            messages=["Fehler"],
        )

        assert result.ok is False
        assert result.has_failures is True
        assert result.has_warnings is False

    def test_has_warnings_property(self):
        """Test: has_warnings Property funktioniert korrekt."""
        result = StrategySwitchSanityResult(
            status="WARN",
            active_strategy_id="test",
            allowed=["test", "a", "b", "c", "d", "e"],
            invalid_strategies=[],
            r_and_d_strategies=[],
            messages=["Warnung"],
        )

        assert result.ok is False
        assert result.has_failures is False
        assert result.has_warnings is True


# ============================================================================
# Tests: Integration with Real Config (optional)
# ============================================================================


class TestIntegrationWithRealConfig:
    """Integration-Tests mit echter Config (wenn vorhanden)."""

    @pytest.mark.skipif(
        not Path("config/config.toml").exists(), reason="Echte Config nicht vorhanden"
    )
    def test_real_config_can_be_loaded(self):
        """Test: Echte Config kann geladen werden."""
        result = run_strategy_switch_sanity_check(
            config_path="config/config.toml",
        )

        # Mindestens sollte der Check durchlaufen (egal welcher Status)
        assert result.status in ("OK", "WARN", "FAIL")
        assert isinstance(result.allowed, list)
        assert isinstance(result.messages, list)

