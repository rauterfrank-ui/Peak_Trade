"""
Test für Strategy Config-Funktionen

Phase 36: Diese Tests nutzen die test-config (config/config.test.toml)
und pruefen, dass die Config korrekt geladen wird.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.core import get_strategy_cfg, list_strategies
from src.core.config_pydantic import reset_config


def test_get_strategy_cfg_success():
    """Test: Strategie-Config erfolgreich laden."""
    # Config-Cache zuruecksetzen, um sicherzustellen, dass Test-Config verwendet wird
    reset_config()

    params = get_strategy_cfg("ma_crossover")

    # Basis-Test: stop_pct muss in allen Configs enthalten sein
    assert "stop_pct" in params
    assert params["stop_pct"] == 0.02

    # ma_crossover kann entweder fast_window/slow_window (OOP-API, Test-Config)
    # oder fast_period/slow_period (Legacy, Haupt-Config) haben
    has_window_api = "fast_window" in params and "slow_window" in params
    has_period_api = "fast_period" in params and "slow_period" in params

    # Mindestens eine API muss vorhanden sein
    assert has_window_api or has_period_api, (
        f"ma_crossover config muss entweder fast_window/slow_window oder "
        f"fast_period/slow_period haben. Gefunden: {params.keys()}"
    )

    # Wenn window-API vorhanden, prüfe Werte aus Test-Config
    if has_window_api:
        assert params["fast_window"] == 20
        assert params["slow_window"] == 50


def test_get_strategy_cfg_not_found():
    """Test: Fehler bei nicht existierender Strategie."""

    with pytest.raises(KeyError) as exc_info:
        get_strategy_cfg("non_existent_strategy")

    error_msg = str(exc_info.value)
    assert "non_existent_strategy" in error_msg
    assert "nicht in config.toml definiert" in error_msg
    assert "Verfügbare Strategien" in error_msg


def test_list_strategies():
    """Test: Liste aller Strategien."""
    strategies = list_strategies()

    assert isinstance(strategies, list)
    assert "ma_crossover" in strategies
    assert strategies == sorted(strategies)  # Sollte sortiert sein


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
