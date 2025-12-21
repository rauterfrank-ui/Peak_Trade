"""
Peak_Trade Config Models (Thread-Safe Registry Support)
=======================================================
Pydantic-based configuration models for validation and type safety.

This module provides the data models used by the thread-safe config registry.
It's based on the existing config_pydantic.py but refactored for better organization.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BacktestConfig(BaseModel):
    """Backtest-Parameter."""
    
    initial_cash: float = Field(gt=0, description="Startkapital")
    results_dir: Path = Field(default=Path("results"))


class RiskConfig(BaseModel):
    """Risk-Management-Parameter."""
    
    risk_per_trade: float = Field(
        default=0.01,
        gt=0,
        le=0.05,
        description="Max. Risiko pro Trade (1% = 0.01)"
    )
    max_daily_loss: float = Field(
        default=0.03,
        gt=0,
        le=0.10,
        description="Max. Tagesverlust (Kill-Switch)"
    )
    max_positions: int = Field(
        default=2,
        ge=1,
        description="Max. parallele Positionen"
    )
    max_position_size: float = Field(
        default=0.25,
        gt=0,
        le=1.0,
        description="Max. Positionsgröße (% des Kontos)"
    )
    min_position_value: float = Field(
        default=50.0,
        ge=0,
        description="Min. Positionswert USD"
    )
    min_stop_distance: float = Field(
        default=0.005,
        gt=0,
        description="Min. Stop-Distanz (%)"
    )


class DataConfig(BaseModel):
    """Daten-Parameter."""
    
    default_timeframe: str = Field(default="1h")
    data_dir: Path = Field(default=Path("data"))
    use_cache: bool = Field(default=True)
    cache_format: str = Field(default="parquet")


class LiveConfig(BaseModel):
    """Live-Trading-Parameter (VORSICHT!)."""

    enabled: bool = Field(default=False)
    mode: str = Field(default="paper", pattern="^(paper|dry_run|live)$")
    exchange: str = Field(default="kraken")
    default_pair: str = Field(default="BTC/USD")


class ExchangeDummyConfig(BaseModel):
    """Konfiguration für den DummyExchangeClient."""

    btc_eur_price: float = Field(default=50000.0, gt=0)
    eth_eur_price: float = Field(default=3000.0, gt=0)
    btc_usd_price: float = Field(default=55000.0, gt=0)
    fee_bps: float = Field(default=10.0, ge=0)
    slippage_bps: float = Field(default=5.0, ge=0)


class ExchangeConfig(BaseModel):
    """Exchange-Client-Konfiguration."""

    default_type: str = Field(
        default="dummy",
        pattern="^(dummy|kraken_testnet|kraken_live)$",
        description="Exchange-Client-Typ"
    )
    dummy: ExchangeDummyConfig = Field(default_factory=ExchangeDummyConfig)


class ValidationConfig(BaseModel):
    """Mindestanforderungen für Live-Trading."""
    
    min_sharpe: float = Field(default=1.5, gt=0)
    max_drawdown: float = Field(default=-0.15, lt=0)
    min_trades: int = Field(default=50, gt=0)
    min_profit_factor: float = Field(default=1.3, gt=1.0)
    min_backtest_months: int = Field(default=6, ge=3)


class ConfigSettings(BaseModel):
    """Configuration settings for the config system itself."""
    
    hot_reload_enabled: bool = Field(
        default=True,
        description="Enable automatic hot-reload on config file changes"
    )
    max_rollback_snapshots: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of config snapshots for rollback"
    )
    reload_on_validation_error: bool = Field(
        default=False,
        description="Reload config on validation error (strict mode when False)"
    )


class StrategyConfig(BaseModel):
    """Basis-Konfiguration für Trading-Strategien."""
    model_config = ConfigDict(extra="allow")
    
    stop_pct: float = Field(
        default=0.02,
        gt=0,
        le=0.10,
        description="Stop-Loss in Prozent"
    )
    
    take_profit_pct: Optional[float] = Field(
        default=None,
        gt=0,
        description="Take-Profit in Prozent (optional)"
    )


class PeakTradeConfig(BaseModel):
    """
    Main configuration model for Peak_Trade.
    
    This is the root configuration object that contains all subsystems.
    It supports both attribute access (config.backtest.initial_cash)
    and dict-like access (config["backtest"]["initial_cash"]) for
    backward compatibility.
    """

    backtest: BacktestConfig
    risk: RiskConfig
    data: DataConfig
    live: LiveConfig
    validation: ValidationConfig
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    config: ConfigSettings = Field(default_factory=ConfigSettings)
    strategy: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Enable dict-like access to config."""
        value = getattr(self, key)
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get() with default value."""
        try:
            return self[key]
        except AttributeError:
            return default
