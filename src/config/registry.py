"""
Peak_Trade Thread-Safe Config Registry
======================================
Thread-safe configuration registry with hot-reload support and rollback mechanism.

Features:
- Thread-safe access with RLock (reentrant lock for nested calls)
- Atomic config swaps (no partial updates visible)
- Rollback mechanism with configurable snapshot history
- Deep copy on reads to prevent external mutations
- Automatic validation and error handling

Usage:
    from src.config.registry import ConfigRegistry, get_registry
    
    # Get global registry
    registry = get_registry()
    
    # Load config
    config = registry.load(Path("config.toml"))
    
    # Get config (thread-safe, returns deep copy)
    config = registry.get_config()
    
    # Hot-reload config
    success = registry.reload(Path("config.toml"))
    
    # Rollback to previous config
    registry.rollback(steps=1)
"""

import logging
from pathlib import Path
from threading import RLock
from typing import Optional, List
from copy import deepcopy

import toml
from pydantic import ValidationError

from src.config.models import PeakTradeConfig
from src.core.errors import ConfigError

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """
    Thread-safe configuration registry with hot-reload support.
    
    This registry provides thread-safe access to configuration with the following guarantees:
    - All config reads/writes are protected by a reentrant lock (RLock)
    - Config updates are atomic (all-or-nothing)
    - Failed reloads automatically rollback to previous config
    - Deep copy on reads prevents external mutations
    - Maintains history of config snapshots for manual rollback
    
    Attributes:
        _config: Current active configuration
        _lock: Reentrant lock for thread synchronization
        _snapshots: List of previous config snapshots for rollback
        _max_snapshots: Maximum number of snapshots to keep
    """
    
    def __init__(self, max_snapshots: int = 5):
        """
        Initialize the config registry.
        
        Args:
            max_snapshots: Maximum number of config snapshots to keep for rollback
        """
        self._config: Optional[PeakTradeConfig] = None
        self._lock = RLock()  # Reentrant lock for nested calls
        self._snapshots: List[PeakTradeConfig] = []
        self._max_snapshots = max_snapshots
    
    def _load_and_validate(self, path: Path) -> PeakTradeConfig:
        """
        Load and validate config from file.
        
        This method is called OUTSIDE the lock to avoid holding the lock
        during potentially slow I/O operations.
        
        Args:
            path: Path to config TOML file
            
        Returns:
            Validated PeakTradeConfig instance
            
        Raises:
            ConfigError: If file not found, invalid TOML, or validation fails
        """
        if not path.exists():
            raise ConfigError(
                f"Config file not found: {path}",
                hint=f"Expected path: {path.absolute()}",
                context={"path": str(path)}
            )
        
        try:
            raw_config = toml.load(path)
        except Exception as e:
            raise ConfigError(
                f"Failed to parse TOML: {e}",
                hint="Check for syntax errors in config file",
                context={"path": str(path), "error": str(e)}
            )
        
        try:
            config = PeakTradeConfig(**raw_config)
        except ValidationError as e:
            raise ConfigError(
                f"Config validation failed: {e}",
                hint="Check config values against schema requirements",
                context={"path": str(path), "validation_errors": e.errors()}
            )
        
        # Additional logical validations
        self._validate_config_logic(config)
        
        return config
    
    def _validate_config_logic(self, config: PeakTradeConfig) -> None:
        """
        Perform additional logical validation beyond Pydantic checks.
        
        Args:
            config: Config to validate
            
        Raises:
            ConfigError: If logical validation fails
        """
        # Check for dangerous live trading config
        if config.live.enabled and config.live.mode == "live":
            raise ConfigError(
                "Live trading is enabled!",
                hint="NEVER enable live trading without extensive backtesting. "
                     "Set live.enabled=false or live.mode='paper'",
                context={"live_enabled": True, "live_mode": "live"}
            )
        
        # Warn about high risk settings
        if config.risk.risk_per_trade > 0.02:
            logger.warning(
                f"⚠️  risk_per_trade={config.risk.risk_per_trade:.1%} is high! "
                f"Recommended: <= 2%"
            )
        
        if config.risk.max_position_size > 0.5:
            logger.warning(
                f"⚠️  max_position_size={config.risk.max_position_size:.0%} is high! "
                f"Recommended: <= 50%"
            )
        
        # Ensure directories exist
        config.backtest.results_dir.mkdir(parents=True, exist_ok=True)
        config.data.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, path: Path) -> PeakTradeConfig:
        """
        Load config with atomic swap.
        
        This method:
        1. Loads and validates the new config (outside lock)
        2. Atomically swaps the old config with new config (inside lock)
        3. Saves old config as snapshot for rollback
        
        Args:
            path: Path to config TOML file
            
        Returns:
            The newly loaded config
            
        Raises:
            ConfigError: If loading or validation fails
        """
        # Load and validate OUTSIDE lock (avoid holding lock during I/O)
        new_config = self._load_and_validate(path)
        
        # Atomic swap INSIDE lock
        with self._lock:
            old_config = self._config
            self._config = new_config
            
            # Save snapshot for rollback
            if old_config:
                self._add_snapshot(old_config)
            
            logger.info(f"Config loaded successfully from {path}")
            return self._config
    
    def get_config(self) -> PeakTradeConfig:
        """
        Get config with thread-safe read.
        
        Returns a deep copy of the config to prevent external mutations.
        This adds ~1ms overhead but ensures thread safety and immutability.
        
        Returns:
            Deep copy of current config
            
        Raises:
            ConfigError: If config not loaded yet
        """
        with self._lock:
            if self._config is None:
                raise ConfigError(
                    "Config not loaded",
                    hint="Call registry.load(path) first",
                    context={}
                )
            # Return deep copy to prevent mutations
            return deepcopy(self._config)
    
    def get_backtest_config(self):
        """
        Get backtest config (deep copy to prevent mutation).
        
        Returns:
            Deep copy of backtest config section
        """
        with self._lock:
            if self._config is None:
                raise ConfigError("Config not loaded")
            return deepcopy(self._config.backtest)
    
    def reload(self, path: Path) -> bool:
        """
        Hot-reload config with automatic rollback on failure.
        
        This method attempts to reload the config from file. If loading or
        validation fails, it automatically rolls back to the previous config
        and returns False.
        
        Args:
            path: Path to config TOML file
            
        Returns:
            True if reload succeeded, False if it failed and rolled back
        """
        with self._lock:
            old_config = self._config
            
            try:
                # Load and validate outside lock context (but still inside method)
                # We're already holding the lock, so this is safe
                new_config = self._load_and_validate(path)
                self._config = new_config
                
                # Save old config as snapshot
                if old_config:
                    self._add_snapshot(old_config)
                
                logger.info(f"Config reloaded successfully from {path}")
                return True
                
            except Exception as e:
                # Rollback to previous config
                logger.error(f"Config reload failed: {e}, rolling back")
                self._config = old_config
                return False
    
    def rollback(self, steps: int = 1) -> bool:
        """
        Manual rollback to previous config snapshot.
        
        Args:
            steps: Number of snapshots to roll back (default: 1)
            
        Returns:
            True if rollback succeeded, False if not enough snapshots
        """
        with self._lock:
            if len(self._snapshots) < steps:
                logger.warning(
                    f"Cannot rollback {steps} step(s), "
                    f"only {len(self._snapshots)} snapshot(s) available"
                )
                return False
            
            # Restore snapshot
            self._config = self._snapshots[-(steps)]
            logger.info(f"Rolled back config {steps} step(s)")
            return True
    
    def _add_snapshot(self, config: PeakTradeConfig) -> None:
        """
        Add config snapshot for rollback.
        
        Maintains a fixed-size history by removing oldest snapshots when
        the maximum is reached.
        
        Args:
            config: Config to snapshot
        """
        self._snapshots.append(config)
        
        # Keep only last N snapshots
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)
    
    def get_snapshot_count(self) -> int:
        """
        Get the number of available snapshots for rollback.
        
        Returns:
            Number of snapshots
        """
        with self._lock:
            return len(self._snapshots)
    
    def clear_snapshots(self) -> None:
        """
        Clear all config snapshots.
        
        This is useful for testing or when you want to free memory.
        """
        with self._lock:
            self._snapshots.clear()
            logger.info("Cleared all config snapshots")


# Global registry instance (singleton pattern)
_GLOBAL_REGISTRY: Optional[ConfigRegistry] = None
_REGISTRY_LOCK = RLock()


def get_registry(force_new: bool = False) -> ConfigRegistry:
    """
    Get the global ConfigRegistry instance (singleton).
    
    This function is thread-safe and ensures only one global registry exists.
    
    Args:
        force_new: If True, create a new registry instance (useful for tests)
        
    Returns:
        Global ConfigRegistry instance
    """
    global _GLOBAL_REGISTRY
    
    with _REGISTRY_LOCK:
        if _GLOBAL_REGISTRY is None or force_new:
            _GLOBAL_REGISTRY = ConfigRegistry()
        
        return _GLOBAL_REGISTRY


def reset_registry() -> None:
    """
    Reset the global registry (for tests).
    
    This clears the global registry instance, forcing a new one to be
    created on the next call to get_registry().
    """
    global _GLOBAL_REGISTRY
    
    with _REGISTRY_LOCK:
        _GLOBAL_REGISTRY = None
