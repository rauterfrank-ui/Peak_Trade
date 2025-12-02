"""
Tests für Environment-Variable-basiertes Config-System
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os
import tempfile
from src.core import (
    resolve_config_path,
    load_settings_from_file,
    DEFAULT_CONFIG_ENV_VAR,
    DEFAULT_CONFIG_PATH,
    reset_config,
)


def test_resolve_config_path_default():
    """Test: Default-Pfad wird verwendet."""
    # Sicherstellen dass env var nicht gesetzt ist
    if DEFAULT_CONFIG_ENV_VAR in os.environ:
        del os.environ[DEFAULT_CONFIG_ENV_VAR]
    
    path = resolve_config_path()
    assert path == DEFAULT_CONFIG_PATH


def test_resolve_config_path_env_var(tmp_path):
    """Test: Environment Variable hat Priorität."""
    custom_config = tmp_path / "custom_config.toml"
    
    # Env var setzen
    os.environ[DEFAULT_CONFIG_ENV_VAR] = str(custom_config)
    
    try:
        path = resolve_config_path()
        assert path == custom_config
    finally:
        # Cleanup
        if DEFAULT_CONFIG_ENV_VAR in os.environ:
            del os.environ[DEFAULT_CONFIG_ENV_VAR]


def test_resolve_config_path_explicit():
    """Test: Expliziter Pfad hat höchste Priorität."""
    explicit_path = Path("/tmp/explicit_config.toml")
    
    # Selbst wenn env var gesetzt ist
    os.environ[DEFAULT_CONFIG_ENV_VAR] = "/tmp/env_config.toml"
    
    try:
        path = resolve_config_path(explicit_path)
        assert path == explicit_path
    finally:
        if DEFAULT_CONFIG_ENV_VAR in os.environ:
            del os.environ[DEFAULT_CONFIG_ENV_VAR]


def test_load_with_env_var(tmp_path):
    """Test: Config wird aus env var-Pfad geladen."""
    # Minimale Test-Config erstellen
    test_config = tmp_path / "test_config.toml"
    test_config.write_text("""
[backtest]
initial_cash = 5000.0
results_dir = "test_results"

[risk]
risk_per_trade = 0.02

[data]
default_timeframe = "1h"

[live]
enabled = false

[validation]
min_sharpe = 1.5
max_drawdown = -0.15
min_trades = 50
min_profit_factor = 1.3
min_backtest_months = 6
""")
    
    # Env var setzen
    os.environ[DEFAULT_CONFIG_ENV_VAR] = str(test_config)
    
    try:
        reset_config()  # Cache leeren
        settings = load_settings_from_file()
        
        # Prüfen dass die Test-Werte geladen wurden
        assert settings.backtest.initial_cash == 5000.0
        assert settings.risk.risk_per_trade == 0.02
        
    finally:
        if DEFAULT_CONFIG_ENV_VAR in os.environ:
            del os.environ[DEFAULT_CONFIG_ENV_VAR]
        reset_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
