"""
Tests for Config File Watcher
==============================
Tests for hot-reload functionality with file system monitoring.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import time

from src.config import (
    ConfigRegistry,
    start_config_watcher,
    is_watchdog_available,
    reset_registry,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[risk]
risk_per_trade = 0.01
max_daily_loss = 0.03
max_positions = 2
max_position_size = 0.25
min_position_value = 50.0
min_stop_distance = 0.005

[data]
default_timeframe = "1h"
data_dir = "data"
use_cache = true
cache_format = "parquet"

[live]
enabled = false
mode = "paper"
exchange = "kraken"
default_pair = "BTC/USD"

[validation]
min_sharpe = 1.5
max_drawdown = -0.15
min_trades = 50
min_profit_factor = 1.3
min_backtest_months = 6

[config]
hot_reload_enabled = true
max_rollback_snapshots = 5
reload_on_validation_error = false
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(config_content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    reset_registry()
    reg = ConfigRegistry(max_snapshots=5)
    yield reg
    reset_registry()


class TestFileWatcher:
    """Test file watcher functionality."""
    
    @pytest.mark.skipif(not is_watchdog_available(), reason="watchdog not installed")
    def test_watchdog_available(self):
        """Test that watchdog is available."""
        assert is_watchdog_available() is True
    
    @pytest.mark.skipif(not is_watchdog_available(), reason="watchdog not installed")
    def test_start_watcher(self, registry, temp_config_file):
        """Test starting the config watcher."""
        registry.load(temp_config_file)
        
        observer = start_config_watcher(registry, temp_config_file)
        assert observer is not None
        assert observer.is_alive()
        
        # Cleanup
        observer.stop()
        observer.join(timeout=5)
    
    @pytest.mark.skipif(not is_watchdog_available(), reason="watchdog not installed")
    def test_auto_reload_on_file_change(self, registry, temp_config_file):
        """Test that config auto-reloads when file changes."""
        registry.load(temp_config_file)
        
        # Start watcher
        observer = start_config_watcher(registry, temp_config_file)
        
        try:
            # Get initial value
            initial_cash = registry.get_config().backtest.initial_cash
            assert initial_cash == 10000.0
            
            # Modify file
            content = temp_config_file.read_text()
            modified_content = content.replace("initial_cash = 10000.0", "initial_cash = 20000.0")
            temp_config_file.write_text(modified_content)
            
            # Wait for watcher to detect and reload
            time.sleep(2)  # Give watchdog time to detect and process
            
            # Check that config was reloaded
            new_cash = registry.get_config().backtest.initial_cash
            assert new_cash == 20000.0
            
        finally:
            observer.stop()
            observer.join(timeout=5)
    
    @pytest.mark.skipif(not is_watchdog_available(), reason="watchdog not installed")
    def test_failed_reload_keeps_previous_config(self, registry, temp_config_file):
        """Test that failed auto-reload keeps previous config."""
        registry.load(temp_config_file)
        
        # Start watcher
        observer = start_config_watcher(registry, temp_config_file)
        
        try:
            # Get initial value
            initial_cash = registry.get_config().backtest.initial_cash
            assert initial_cash == 10000.0
            
            # Corrupt file
            temp_config_file.write_text("INVALID TOML {{{{")
            
            # Wait for watcher to detect
            time.sleep(2)
            
            # Config should still be the original (rollback)
            cash = registry.get_config().backtest.initial_cash
            assert cash == 10000.0
            
        finally:
            observer.stop()
            observer.join(timeout=5)
    
    @pytest.mark.skipif(not is_watchdog_available(), reason="watchdog not installed")
    def test_multiple_file_changes(self, registry, temp_config_file):
        """Test multiple consecutive file changes."""
        registry.load(temp_config_file)
        
        observer = start_config_watcher(registry, temp_config_file)
        
        try:
            values = [20000.0, 30000.0, 40000.0]
            
            for value in values:
                content = temp_config_file.read_text()
                current_value = registry.get_config().backtest.initial_cash
                modified = content.replace(
                    f"initial_cash = {current_value}",
                    f"initial_cash = {value}"
                )
                temp_config_file.write_text(modified)
                time.sleep(2)  # Wait for reload
                
                # Check value updated
                new_value = registry.get_config().backtest.initial_cash
                assert new_value == value
                
        finally:
            observer.stop()
            observer.join(timeout=5)


class TestWatchdogNotInstalled:
    """Test behavior when watchdog is not installed."""
    
    def test_is_watchdog_available_returns_bool(self):
        """Test that is_watchdog_available returns a bool."""
        result = is_watchdog_available()
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
