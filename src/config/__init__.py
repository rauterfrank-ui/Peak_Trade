"""
Peak_Trade Config Module
=========================
Thread-safe configuration system with hot-reload support.

This module provides a complete configuration management system with:
- Thread-safe access via RLock
- Atomic config updates (no partial state)
- Rollback mechanism with snapshot history
- Hot-reload with file watching (optional)
- Deep copy on reads to prevent mutations
- Pydantic-based validation

Usage:
    from src.config import get_registry, start_config_watcher
    from pathlib import Path
    
    # Get registry and load config
    registry = get_registry()
    config = registry.load(Path("config.toml"))
    
    # Get config (thread-safe, returns deep copy)
    config = registry.get_config()
    
    # Optional: Enable hot-reload
    observer = start_config_watcher(registry, Path("config.toml"))
    
    # Reload manually
    success = registry.reload(Path("config.toml"))
    
    # Rollback if needed
    registry.rollback(steps=1)
"""

from src.config.models import (
    PeakTradeConfig,
    BacktestConfig,
    RiskConfig,
    DataConfig,
    LiveConfig,
    ExchangeConfig,
    ValidationConfig,
    ConfigSettings,
    StrategyConfig,
)

from src.config.registry import (
    ConfigRegistry,
    get_registry,
    reset_registry,
)

from src.config.watcher import (
    start_config_watcher,
    is_watchdog_available,
)

__all__ = [
    # Models
    "PeakTradeConfig",
    "BacktestConfig",
    "RiskConfig",
    "DataConfig",
    "LiveConfig",
    "ExchangeConfig",
    "ValidationConfig",
    "ConfigSettings",
    "StrategyConfig",
    # Registry
    "ConfigRegistry",
    "get_registry",
    "reset_registry",
    # Watcher
    "start_config_watcher",
    "is_watchdog_available",
]
