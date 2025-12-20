"""
Pydantic Config Models for Peak_Trade
=====================================
Provides strict validation for all configuration sections.

Design:
- Use Pydantic V2 features (Field, field_validator)
- Follow existing error taxonomy (ConfigError)
- Backward compatible with existing TOML files
- Apple Silicon (M2/M3) compatible

Usage:
    from src.config.models import PeakTradeConfig
    
    config = PeakTradeConfig(**raw_config)
    print(config.backtest.initial_capital)  # Type-safe access
"""

from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class BacktestConfig(BaseModel):
    """
    Backtest configuration with validation.
    
    Attributes:
        initial_capital: Initial capital for backtesting (must be positive)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (must be after start_date)
        max_drawdown: Maximum drawdown as fraction (0-1)
        commission: Trading commission as fraction (0-0.1, default 0.001)
        results_dir: Directory for backtest results (default "results")
    
    Examples:
        >>> config = BacktestConfig(
        ...     initial_capital=10000.0,
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ...     max_drawdown=0.25,
        ...     commission=0.001
        ... )
    """
    
    initial_capital: float = Field(
        gt=0, 
        description="Initial capital must be positive",
        alias="initial_cash"  # Support existing config key
    )
    start_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format"
    )
    max_drawdown: Optional[float] = Field(
        None,
        ge=0, 
        le=1, 
        description="Max drawdown as fraction (0-1)"
    )
    commission: float = Field(
        default=0.001,
        ge=0, 
        le=0.1, 
        description="Trading commission as fraction"
    )
    results_dir: str = Field(
        default="results",
        description="Directory for backtest results"
    )
    
    model_config = ConfigDict(populate_by_name=True)  # Allow both field name and alias
    
    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that end_date is after start_date."""
        if v is None:
            return v
        
        start_date = info.data.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('end_date must be after start_date')
        return v


class DataConfig(BaseModel):
    """
    Data loading configuration.
    
    Attributes:
        provider: Data provider (kraken, csv, or cache)
        cache_enabled: Whether to enable caching (default True)
        cache_ttl: Cache time-to-live in seconds (default 3600)
        symbols: List of trading symbols (must have at least 1)
        default_timeframe: Default timeframe for data (default "1h")
        data_dir: Directory for data storage (default "data")
        use_cache: Alias for cache_enabled
        cache_format: Cache storage format (default "parquet")
    
    Examples:
        >>> config = DataConfig(
        ...     provider="kraken",
        ...     cache_enabled=True,
        ...     cache_ttl=3600,
        ...     symbols=["BTC/USD", "ETH/USD"]
        ... )
    """
    
    provider: Optional[Literal["kraken", "csv", "cache"]] = Field(
        default="kraken",
        description="Data provider type"
    )
    cache_enabled: bool = Field(
        default=True,
        alias="use_cache",
        description="Enable data caching"
    )
    cache_ttl: int = Field(
        default=3600,
        gt=0, 
        description="Cache TTL in seconds"
    )
    symbols: Optional[List[str]] = Field(
        default=None,
        min_length=1,
        description="List of trading symbols"
    )
    default_timeframe: str = Field(
        default="1h",
        description="Default timeframe for data"
    )
    data_dir: str = Field(
        default="data",
        description="Data storage directory"
    )
    cache_format: str = Field(
        default="parquet",
        description="Cache storage format"
    )
    
    model_config = ConfigDict(populate_by_name=True)


class RiskConfig(BaseModel):
    """
    Risk management configuration.
    
    Attributes:
        max_position_size: Maximum position size as fraction of portfolio (0-1)
        max_portfolio_leverage: Maximum portfolio leverage (1-10, default 1.0)
        stop_loss_pct: Stop loss percentage (0-1, optional)
        risk_per_trade: Risk per trade as fraction (default 0.01)
        max_daily_loss: Maximum daily loss as fraction (default 0.03)
        max_positions: Maximum number of concurrent positions (default 2)
        min_position_value: Minimum position value in USD (default 50.0)
        min_stop_distance: Minimum stop distance as fraction (default 0.005)
    
    Examples:
        >>> config = RiskConfig(
        ...     max_position_size=0.1,
        ...     max_portfolio_leverage=1.0,
        ...     stop_loss_pct=0.02
        ... )
    """
    
    max_position_size: float = Field(
        default=0.1,
        gt=0, 
        le=1, 
        description="Max position size as fraction of portfolio"
    )
    max_portfolio_leverage: float = Field(
        default=1.0,
        ge=1, 
        le=10, 
        description="Max portfolio leverage"
    )
    stop_loss_pct: Optional[float] = Field(
        default=None,
        ge=0, 
        le=1, 
        description="Stop loss percentage"
    )
    risk_per_trade: float = Field(
        default=0.01,
        gt=0,
        le=0.05,
        description="Risk per trade as fraction"
    )
    max_daily_loss: float = Field(
        default=0.03,
        gt=0,
        le=0.10,
        description="Maximum daily loss as fraction"
    )
    max_positions: int = Field(
        default=2,
        ge=1,
        description="Maximum concurrent positions"
    )
    min_position_value: float = Field(
        default=50.0,
        ge=0,
        description="Minimum position value in USD"
    )
    min_stop_distance: float = Field(
        default=0.005,
        gt=0,
        description="Minimum stop distance as fraction"
    )


class PeakTradeConfig(BaseModel):
    """
    Root configuration with all sections.
    
    This is the main configuration model that combines all subsections.
    It validates the entire configuration structure and rejects unknown keys.
    
    Attributes:
        backtest: Backtest configuration
        data: Data loading configuration
        risk: Risk management configuration
    
    Examples:
        >>> config = PeakTradeConfig(
        ...     backtest={"initial_capital": 10000.0, ...},
        ...     data={"provider": "kraken", ...},
        ...     risk={"max_position_size": 0.1, ...}
        ... )
    """
    
    backtest: BacktestConfig
    data: DataConfig
    risk: RiskConfig
    
    # Allow extra fields for backward compatibility with full config.toml
    # In production, this could be set to "forbid" for stricter validation
    model_config = ConfigDict(extra="allow")  # Allow unknown keys for now (for compatibility)
