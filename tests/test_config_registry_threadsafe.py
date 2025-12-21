"""
Tests for Thread-Safe Config Registry
======================================
Comprehensive tests for the thread-safe config registry including:
- Thread-safety (concurrent reads/writes)
- Atomic reload (no partial updates)
- Rollback mechanism
- File watcher functionality
- Stress testing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

from src.config import (
    ConfigRegistry,
    get_registry,
    reset_registry,
    PeakTradeConfig,
)
from src.core.errors import ConfigError


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


class TestBasicFunctionality:
    """Test basic registry functionality."""
    
    def test_load_config(self, registry, temp_config_file):
        """Test loading config from file."""
        config = registry.load(temp_config_file)
        
        assert isinstance(config, PeakTradeConfig)
        assert config.backtest.initial_cash == 10000.0
        assert config.risk.risk_per_trade == 0.01
    
    def test_get_config(self, registry, temp_config_file):
        """Test getting config returns deep copy."""
        registry.load(temp_config_file)
        
        config1 = registry.get_config()
        config2 = registry.get_config()
        
        # Should be equal but not the same object
        assert config1.backtest.initial_cash == config2.backtest.initial_cash
        assert config1 is not config2
    
    def test_get_config_before_load_raises_error(self, registry):
        """Test that getting config before loading raises error."""
        with pytest.raises(ConfigError, match="Config not loaded"):
            registry.get_config()
    
    def test_load_nonexistent_file_raises_error(self, registry):
        """Test loading nonexistent file raises error."""
        with pytest.raises(ConfigError, match="Config file not found"):
            registry.load(Path("/nonexistent/config.toml"))
    
    def test_deep_copy_prevents_mutation(self, registry, temp_config_file):
        """Test that deep copy prevents external mutations."""
        registry.load(temp_config_file)
        
        config = registry.get_config()
        original_cash = config.backtest.initial_cash
        
        # Mutate the returned config
        config.backtest.initial_cash = 99999.0
        
        # Get config again - should still have original value
        config2 = registry.get_config()
        assert config2.backtest.initial_cash == original_cash


class TestThreadSafety:
    """Test thread-safety of the registry."""
    
    def test_concurrent_reads(self, registry, temp_config_file):
        """Test multiple concurrent reads are safe."""
        registry.load(temp_config_file)
        
        results = []
        errors = []
        
        def read_config():
            try:
                config = registry.get_config()
                results.append(config.backtest.initial_cash)
            except Exception as e:
                errors.append(e)
        
        # Start 50 concurrent readers
        threads = []
        for _ in range(50):
            t = threading.Thread(target=read_config)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50
        assert all(r == 10000.0 for r in results)
    
    def test_concurrent_reads_and_reload(self, registry, temp_config_file):
        """Test concurrent reads during reload are safe."""
        registry.load(temp_config_file)
        
        results = []
        errors = []
        reload_count = [0]
        
        def read_config():
            try:
                for _ in range(10):
                    config = registry.get_config()
                    results.append(config.backtest.initial_cash)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def reload_config():
            try:
                for _ in range(5):
                    registry.reload(temp_config_file)
                    reload_count[0] += 1
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)
        
        # Start readers and reloaders
        threads = []
        
        # 10 readers
        for _ in range(10):
            t = threading.Thread(target=read_config)
            threads.append(t)
            t.start()
        
        # 2 reloaders
        for _ in range(2):
            t = threading.Thread(target=reload_config)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 100  # 10 readers * 10 reads each
        # All reads should return valid configs (no partial updates)
        assert all(isinstance(r, (int, float)) for r in results)


class TestAtomicReload:
    """Test atomic reload behavior."""
    
    def test_reload_success(self, registry, temp_config_file):
        """Test successful reload."""
        registry.load(temp_config_file)
        
        # Modify the file
        config_content = temp_config_file.read_text()
        modified_content = config_content.replace("initial_cash = 10000.0", "initial_cash = 20000.0")
        temp_config_file.write_text(modified_content)
        
        # Reload
        success = registry.reload(temp_config_file)
        assert success is True
        
        # Check new value
        config = registry.get_config()
        assert config.backtest.initial_cash == 20000.0
    
    def test_reload_failure_rollback(self, registry, temp_config_file):
        """Test that failed reload rolls back to previous config."""
        registry.load(temp_config_file)
        original_cash = registry.get_config().backtest.initial_cash
        
        # Corrupt the file
        temp_config_file.write_text("INVALID TOML {{{{")
        
        # Reload should fail
        success = registry.reload(temp_config_file)
        assert success is False
        
        # Should still have original config
        config = registry.get_config()
        assert config.backtest.initial_cash == original_cash
    
    def test_no_partial_updates(self, registry, temp_config_file):
        """Test that readers never see partial updates."""
        registry.load(temp_config_file)
        
        seen_values = set()
        errors = []
        stop_flag = [False]
        
        def continuous_reader():
            try:
                while not stop_flag[0]:
                    config = registry.get_config()
                    seen_values.add(config.backtest.initial_cash)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)
        
        # Start continuous reader
        reader_thread = threading.Thread(target=continuous_reader)
        reader_thread.start()
        
        # Perform multiple reloads with different values
        test_values = [15000.0, 25000.0, 35000.0, 45000.0]
        for value in test_values:
            config_content = temp_config_file.read_text()
            modified_content = config_content.replace(
                f"initial_cash = {list(seen_values)[0] if seen_values else 10000.0}",
                f"initial_cash = {value}"
            )
            temp_config_file.write_text(modified_content)
            registry.reload(temp_config_file)
            time.sleep(0.01)
        
        # Stop reader
        stop_flag[0] = True
        reader_thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        # Should only see valid config values (10000.0 and test_values)
        expected_values = {10000.0} | set(test_values)
        assert seen_values.issubset(expected_values)


class TestRollback:
    """Test rollback mechanism."""
    
    def test_single_rollback(self, registry, temp_config_file):
        """Test rolling back one step."""
        # Load initial config
        registry.load(temp_config_file)
        assert registry.get_config().backtest.initial_cash == 10000.0
        
        # Modify and reload
        content = temp_config_file.read_text()
        temp_config_file.write_text(content.replace("initial_cash = 10000.0", "initial_cash = 20000.0"))
        registry.reload(temp_config_file)
        assert registry.get_config().backtest.initial_cash == 20000.0
        
        # Rollback
        success = registry.rollback(steps=1)
        assert success is True
        assert registry.get_config().backtest.initial_cash == 10000.0
    
    def test_multi_step_rollback(self, registry, temp_config_file):
        """Test rolling back multiple steps."""
        values = [10000.0, 20000.0, 30000.0, 40000.0, 50000.0]
        
        # Load initial
        registry.load(temp_config_file)
        
        # Perform multiple reloads
        for value in values[1:]:
            content = temp_config_file.read_text()
            current_value = registry.get_config().backtest.initial_cash
            temp_config_file.write_text(
                content.replace(f"initial_cash = {current_value}", f"initial_cash = {value}")
            )
            registry.reload(temp_config_file)
        
        # Should be at last value
        assert registry.get_config().backtest.initial_cash == values[-1]
        
        # Rollback 2 steps
        success = registry.rollback(steps=2)
        assert success is True
        assert registry.get_config().backtest.initial_cash == values[-3]
    
    def test_rollback_beyond_history_fails(self, registry, temp_config_file):
        """Test that rollback fails if not enough history."""
        registry.load(temp_config_file)
        
        # Try to rollback when no history exists
        success = registry.rollback(steps=1)
        assert success is False
    
    def test_snapshot_limit(self, registry, temp_config_file):
        """Test that only max_snapshots are kept."""
        registry.load(temp_config_file)
        
        # Perform more reloads than max_snapshots
        for i in range(10):
            content = temp_config_file.read_text()
            current_value = registry.get_config().backtest.initial_cash
            new_value = current_value + 1000.0
            temp_config_file.write_text(
                content.replace(f"initial_cash = {current_value}", f"initial_cash = {new_value}")
            )
            registry.reload(temp_config_file)
        
        # Should only have max_snapshots
        assert registry.get_snapshot_count() <= registry._max_snapshots


class TestStress:
    """Stress tests for the registry."""
    
    def test_stress_concurrent_readers_and_writer(self, registry, temp_config_file):
        """Stress test: 100 concurrent readers + 1 writer."""
        registry.load(temp_config_file)
        
        results = []
        errors = []
        
        def reader():
            try:
                for _ in range(100):
                    config = registry.get_config()
                    results.append(config.backtest.initial_cash)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)
        
        def writer():
            try:
                for i in range(10):
                    content = temp_config_file.read_text()
                    current_value = registry.get_config().backtest.initial_cash
                    new_value = current_value + 1000.0
                    temp_config_file.write_text(
                        content.replace(f"initial_cash = {current_value}", f"initial_cash = {new_value}")
                    )
                    registry.reload(temp_config_file)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        # Start threads
        threads = []
        
        # 100 readers
        for _ in range(100):
            t = threading.Thread(target=reader)
            threads.append(t)
            t.start()
        
        # 1 writer
        t = threading.Thread(target=writer)
        threads.append(t)
        t.start()
        
        # Wait for all
        for t in threads:
            t.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10000  # 100 readers * 100 reads
        # All reads should return valid values
        assert all(isinstance(r, (int, float)) and r >= 10000.0 for r in results)


class TestGlobalRegistry:
    """Test global registry singleton."""
    
    def test_get_registry_returns_singleton(self):
        """Test that get_registry returns the same instance."""
        reset_registry()
        
        reg1 = get_registry()
        reg2 = get_registry()
        
        assert reg1 is reg2
    
    def test_reset_registry(self):
        """Test that reset_registry clears the singleton."""
        reset_registry()
        
        reg1 = get_registry()
        reset_registry()
        reg2 = get_registry()
        
        assert reg1 is not reg2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
