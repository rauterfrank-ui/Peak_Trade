"""
ConfigRegistry with Pydantic Validation
=======================================
Integrates Pydantic models with config loading and validation.

Design:
- Wraps config loading with Pydantic validation
- Provides type-safe accessor methods
- Integrates with existing error taxonomy (ConfigError)
- Backward compatible with existing config.toml files

Usage:
    from src.config import ConfigRegistry
    from pathlib import Path
    
    registry = ConfigRegistry()
    config = registry.load(Path("config.toml"))
    
    # Type-safe access
    backtest_cfg = registry.get_backtest_config()
    print(backtest_cfg.initial_capital)  # Type: float, validated > 0
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "Requires Python 3.11+ (tomllib) or 'pip install tomli'"
        )

from pydantic import ValidationError

from src.config.models import (
    BacktestConfig,
    DataConfig,
    RiskConfig,
    PeakTradeConfig,
)
from src.core.errors import ConfigError


# Default config path (relative to project root)
DEFAULT_CONFIG_PATH = Path("config.toml")


class ConfigRegistry:
    """
    Configuration registry with Pydantic validation.
    
    This class provides validated config loading and type-safe access
    to configuration sections.
    
    Attributes:
        config_path: Path to config.toml file
        _config: Cached validated config (PeakTradeConfig)
    
    Examples:
        >>> registry = ConfigRegistry()
        >>> config = registry.load(Path("config.toml"))
        >>> backtest_cfg = registry.get_backtest_config()
        >>> print(backtest_cfg.initial_capital)
        10000.0
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigRegistry.
        
        Args:
            config_path: Path to config.toml (default: config.toml in current dir)
        """
        self.config_path = config_path or self._resolve_config_path()
        self._config: Optional[PeakTradeConfig] = None
    
    def _resolve_config_path(self) -> Path:
        """
        Resolve config path from environment or default.
        
        Returns:
            Path to config file
        """
        env_path = os.getenv("PEAK_TRADE_CONFIG")
        if env_path:
            return Path(env_path)
        return DEFAULT_CONFIG_PATH
    
    def load(self, path: Optional[Path] = None) -> PeakTradeConfig:
        """
        Load and validate config from TOML file.
        
        Args:
            path: Path to config.toml file (optional, uses self.config_path if None)
        
        Returns:
            Validated PeakTradeConfig instance
        
        Raises:
            ConfigError: If config validation fails or file not found
        
        Examples:
            >>> registry = ConfigRegistry()
            >>> config = registry.load(Path("config.toml"))
            >>> print(config.backtest.initial_capital)
            10000.0
        """
        if path is not None:
            self.config_path = path
        
        try:
            if not self.config_path.exists():
                raise ConfigError(
                    f"Config file not found: {self.config_path}",
                    hint=f"Create {self.config_path} or set PEAK_TRADE_CONFIG environment variable",
                    context={"file": str(self.config_path)}
                )
            
            with open(self.config_path, "rb") as f:
                raw_config = tomllib.load(f)
            
            # Validate with Pydantic
            try:
                config = PeakTradeConfig(**raw_config)
                self._config = config
                return config
            except ValidationError as e:
                # Format Pydantic errors into human-readable messages
                errors = []
                for err in e.errors():
                    loc = " -> ".join(str(x) for x in err['loc'])
                    errors.append(f"{loc}: {err['msg']}")
                
                raise ConfigError(
                    f"Config validation failed: {errors[0]}",
                    hint=f"Check {self.config_path} for: {', '.join(errors[:3])}",
                    context={
                        "file": str(self.config_path),
                        "errors": errors
                    }
                ) from e
                
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(
                f"Failed to load config: {e}",
                hint=f"Check {self.config_path} for syntax errors",
                context={"file": str(self.config_path), "error": str(e)}
            ) from e
    
    @property
    def config(self) -> PeakTradeConfig:
        """
        Get cached validated config (loads if not loaded).
        
        Returns:
            Validated PeakTradeConfig instance
        
        Raises:
            ConfigError: If config not loaded yet
        """
        if self._config is None:
            self.load()
        return self._config
    
    def reload(self):
        """Force reload of config from file."""
        self._config = None
        self.load()
    
    def get_backtest_config(self) -> BacktestConfig:
        """
        Get validated backtest configuration.
        
        Returns:
            Validated BacktestConfig instance
        
        Examples:
            >>> registry = ConfigRegistry()
            >>> registry.load()
            >>> backtest = registry.get_backtest_config()
            >>> print(backtest.initial_capital)
            10000.0
        """
        return self.config.backtest
    
    def get_data_config(self) -> DataConfig:
        """
        Get validated data configuration.
        
        Returns:
            Validated DataConfig instance
        
        Examples:
            >>> registry = ConfigRegistry()
            >>> registry.load()
            >>> data = registry.get_data_config()
            >>> print(data.provider)
            kraken
        """
        return self.config.data
    
    def get_risk_config(self) -> RiskConfig:
        """
        Get validated risk configuration.
        
        Returns:
            Validated RiskConfig instance
        
        Examples:
            >>> registry = ConfigRegistry()
            >>> registry.load()
            >>> risk = registry.get_risk_config()
            >>> print(risk.max_position_size)
            0.1
        """
        return self.config.risk


# Global registry instance (singleton pattern)
_GLOBAL_REGISTRY: Optional[ConfigRegistry] = None


def get_registry(force_reload: bool = False) -> ConfigRegistry:
    """
    Get global ConfigRegistry instance (singleton).
    
    Args:
        force_reload: Force reload of config from file
    
    Returns:
        ConfigRegistry instance
    
    Examples:
        >>> registry = get_registry()
        >>> backtest = registry.get_backtest_config()
    """
    global _GLOBAL_REGISTRY
    
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ConfigRegistry()
        _GLOBAL_REGISTRY.load()
    elif force_reload:
        _GLOBAL_REGISTRY.reload()
    
    return _GLOBAL_REGISTRY


def reset_registry():
    """
    Reset global registry (useful for tests).
    
    Examples:
        >>> reset_registry()
        >>> registry = get_registry()  # Creates fresh instance
    """
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = None
