"""
Peak_Trade Config Module with Pydantic Validation
=================================================
Provides validated configuration models and registry access.

Usage:
    from src.config import PeakTradeConfig, ConfigRegistry
    
    registry = ConfigRegistry()
    config = registry.load(Path("config.toml"))
    
    # Type-safe access
    backtest_cfg = registry.get_backtest_config()
    initial_capital = backtest_cfg.initial_capital  # Type: float, validated > 0
"""

from src.config.models import (
    BacktestConfig,
    DataConfig,
    RiskConfig,
    PeakTradeConfig,
)
from src.config.registry import ConfigRegistry

__all__ = [
    "BacktestConfig",
    "DataConfig",
    "RiskConfig",
    "PeakTradeConfig",
    "ConfigRegistry",
]
