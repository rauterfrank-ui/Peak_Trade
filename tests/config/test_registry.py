"""
Tests for ConfigRegistry with Pydantic Validation
=================================================
Tests config loading, validation, and error handling.

Test Coverage:
- Valid config loading
- Invalid config files
- File not found
- Validation error formatting
- Type-safe accessors
- Singleton pattern
"""

import os
import pytest
import tempfile
from pathlib import Path

from src.config.registry import ConfigRegistry, get_registry, reset_registry
from src.config.models import BacktestConfig, DataConfig, RiskConfig
from src.core.errors import ConfigError


class TestConfigRegistry:
    """Tests for ConfigRegistry."""
    
    def test_load_valid_config(self, tmp_path):
        """Test: Load valid config file."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0
start_date = "2024-01-01"
end_date = "2024-12-31"
results_dir = "results"

[data]
provider = "kraken"
cache_enabled = true
cache_ttl = 3600
default_timeframe = "1h"
data_dir = "data"

[risk]
max_position_size = 0.1
max_portfolio_leverage = 1.0
risk_per_trade = 0.01
""")
        
        registry = ConfigRegistry()
        config = registry.load(config_file)
        
        assert config.backtest.initial_capital == 10000.0
        assert config.data.provider == "kraken"
        assert config.risk.max_position_size == 0.1
    
    def test_load_config_with_alias(self, tmp_path):
        """Test: Load config with backward compatible aliases."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_cash = 5000.0

[data]
use_cache = false

[risk]
max_position_size = 0.2
""")
        
        registry = ConfigRegistry()
        config = registry.load(config_file)
        
        # Check alias works
        assert config.backtest.initial_capital == 5000.0
        assert config.data.cache_enabled is False
    
    def test_load_config_file_not_found(self):
        """Test: File not found raises ConfigError."""
        registry = ConfigRegistry(Path("/nonexistent/config.toml"))
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load()
        
        error = exc_info.value
        assert "not found" in error.message.lower()
        assert "nonexistent" in error.message
        assert error.hint is not None
    
    def test_load_invalid_config_negative_capital(self, tmp_path):
        """Test: Invalid config raises ConfigError with helpful message."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = -1000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        registry = ConfigRegistry()
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load(config_file)
        
        error = exc_info.value
        assert "validation failed" in error.message.lower()
        assert "initial_capital" in error.message
        assert error.hint is not None
        assert "errors" in error.context
    
    def test_load_invalid_config_missing_section(self, tmp_path):
        """Test: Missing required section raises ConfigError."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

# Missing [risk] section
""")
        
        registry = ConfigRegistry()
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load(config_file)
        
        error = exc_info.value
        assert "validation failed" in error.message.lower()
        assert error.hint is not None
    
    def test_load_invalid_toml_syntax(self, tmp_path):
        """Test: Invalid TOML syntax raises ConfigError."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0
invalid syntax here
""")
        
        registry = ConfigRegistry()
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load(config_file)
        
        error = exc_info.value
        assert "failed to load" in error.message.lower()
        assert error.hint is not None
    
    def test_config_property_lazy_loading(self, tmp_path):
        """Test: config property loads lazily."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        registry = ConfigRegistry(config_file)
        
        # Access config property (should load automatically)
        config = registry.config
        assert config.backtest.initial_capital == 10000.0
    
    def test_reload_config(self, tmp_path):
        """Test: Reload config forces re-read from file."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        registry = ConfigRegistry(config_file)
        config1 = registry.load()
        assert config1.backtest.initial_capital == 10000.0
        
        # Modify file
        config_file.write_text("""
[backtest]
initial_capital = 20000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        # Reload
        registry.reload()
        config2 = registry.config
        assert config2.backtest.initial_capital == 20000.0


class TestTypeSafeAccessors:
    """Tests for type-safe accessor methods."""
    
    def test_get_backtest_config(self, tmp_path):
        """Test: Get backtest config with type safety."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 15000.0
commission = 0.002

[data]
provider = "kraken"

[risk]
max_position_size = 0.15
""")
        
        registry = ConfigRegistry(config_file)
        registry.load()
        
        backtest = registry.get_backtest_config()
        
        assert isinstance(backtest, BacktestConfig)
        assert backtest.initial_capital == 15000.0
        assert backtest.commission == 0.002
    
    def test_get_data_config(self, tmp_path):
        """Test: Get data config with type safety."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "csv"
cache_ttl = 7200

[risk]
max_position_size = 0.1
""")
        
        registry = ConfigRegistry(config_file)
        registry.load()
        
        data = registry.get_data_config()
        
        assert isinstance(data, DataConfig)
        assert data.provider == "csv"
        assert data.cache_ttl == 7200
    
    def test_get_risk_config(self, tmp_path):
        """Test: Get risk config with type safety."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.25
max_portfolio_leverage = 2.0
stop_loss_pct = 0.03
""")
        
        registry = ConfigRegistry(config_file)
        registry.load()
        
        risk = registry.get_risk_config()
        
        assert isinstance(risk, RiskConfig)
        assert risk.max_position_size == 0.25
        assert risk.max_portfolio_leverage == 2.0
        assert risk.stop_loss_pct == 0.03


class TestSingletonPattern:
    """Tests for singleton registry pattern."""
    
    def test_get_registry_singleton(self, tmp_path):
        """Test: get_registry returns singleton."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        # Reset global state
        reset_registry()
        
        # Override default path via env
        os.environ["PEAK_TRADE_CONFIG"] = str(config_file)
        
        try:
            registry1 = get_registry()
            registry2 = get_registry()
            
            # Should be same instance
            assert registry1 is registry2
        finally:
            # Clean up
            if "PEAK_TRADE_CONFIG" in os.environ:
                del os.environ["PEAK_TRADE_CONFIG"]
            reset_registry()
    
    def test_reset_registry(self, tmp_path):
        """Test: reset_registry clears singleton."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        import os
        os.environ["PEAK_TRADE_CONFIG"] = str(config_file)
        
        try:
            registry1 = get_registry()
            reset_registry()
            registry2 = get_registry()
            
            # Should be different instances
            assert registry1 is not registry2
        finally:
            if "PEAK_TRADE_CONFIG" in os.environ:
                del os.environ["PEAK_TRADE_CONFIG"]
            reset_registry()
    
    def test_get_registry_force_reload(self, tmp_path):
        """Test: force_reload reloads config."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 10000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        os.environ["PEAK_TRADE_CONFIG"] = str(config_file)
        
        try:
            # Reset and get initial registry
            reset_registry()
            registry1 = get_registry()
            config1 = registry1.config
            assert config1.backtest.initial_capital == 10000.0
            
            # Modify file
            config_file.write_text("""
[backtest]
initial_capital = 25000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
            
            # Force reload
            registry2 = get_registry(force_reload=True)
            config2 = registry2.config
            
            # Should have new value
            assert config2.backtest.initial_capital == 25000.0
        finally:
            if "PEAK_TRADE_CONFIG" in os.environ:
                del os.environ["PEAK_TRADE_CONFIG"]
            reset_registry()


class TestEnvironmentVariables:
    """Tests for environment variable config path resolution."""
    
    def test_resolve_from_env_var(self, tmp_path):
        """Test: Resolve config path from environment variable."""
        config_file = tmp_path / "custom_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 12345.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        os.environ["PEAK_TRADE_CONFIG"] = str(config_file)
        
        try:
            registry = ConfigRegistry()
            config = registry.load()
            
            # Should load from env var path
            assert config.backtest.initial_capital == 12345.0
        finally:
            if "PEAK_TRADE_CONFIG" in os.environ:
                del os.environ["PEAK_TRADE_CONFIG"]


class TestErrorMessages:
    """Tests for error message quality."""
    
    def test_error_includes_file_path(self, tmp_path):
        """Test: Error messages include file path."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = -1000.0

[data]
provider = "kraken"

[risk]
max_position_size = 0.1
""")
        
        registry = ConfigRegistry(config_file)
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load()
        
        error = exc_info.value
        assert str(config_file) in error.context["file"]
    
    def test_error_includes_hint(self, tmp_path):
        """Test: Error messages include actionable hints."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = 0.0

[data]
provider = "kraken"

[risk]
max_position_size = 2.0
""")
        
        registry = ConfigRegistry(config_file)
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load()
        
        error = exc_info.value
        assert error.hint is not None
        assert len(error.hint) > 0
    
    def test_error_includes_multiple_validation_errors(self, tmp_path):
        """Test: Error context includes all validation errors."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[backtest]
initial_capital = -1000.0
commission = 0.5

[data]
provider = "invalid"
cache_ttl = -100

[risk]
max_position_size = 2.0
""")
        
        registry = ConfigRegistry(config_file)
        
        with pytest.raises(ConfigError) as exc_info:
            registry.load()
        
        error = exc_info.value
        assert "errors" in error.context
        assert len(error.context["errors"]) > 0
