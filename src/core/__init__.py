"""
Peak_Trade Core Module
======================
Zentrale Konfiguration und gemeinsame Utilities.

Es gibt zwei Config-Systeme:
1. config_pydantic.py - Pydantic-basiert (für alte Scripts)
2. peak_config.py - TOML-basiert (neue OOP-API)
3. config_registry.py - Registry-basiert (für Portfolio-Backtests)
"""

# Wave A (Stability): Error Taxonomy
from .errors import (
    PeakTradeError,
    DataContractError,
    ConfigError,
    ProviderError,
    CacheCorruptionError,
    BacktestInvariantError,
)

# Alte Pydantic-Config (Legacy)
from .config_pydantic import (
    Settings,
    StrategyConfig,
    load_config,  # Behalte Original-Namen für Rückwärtskompatibilität
    load_config as load_pydantic_config,  # Alias
    load_settings_from_file,
    get_config,
    get_strategy_cfg,
    list_strategies,
    reset_config,
    resolve_config_path,
    DEFAULT_CONFIG_ENV_VAR,
    DEFAULT_CONFIG_PATH,
)

# Neue TOML-Config (OOP)
from .peak_config import (
    PeakConfig,
    load_config as load_peak_config,
)

# Registry-Config (Portfolio)
from .config_registry import (
    get_config as get_registry_config,
    get_active_strategies,
    get_strategy_config,
    list_strategies as list_registry_strategies,
)

# Environment & Safety (Phase 17)
from .environment import (
    TradingEnvironment,
    EnvironmentConfig,
    LIVE_CONFIRM_TOKEN,
    get_environment_from_config,
    create_default_environment,
    is_paper,
    is_testnet,
    is_live,
)

# Wave A (Stability): Repro Context & Seed Policy
from .repro import (
    ReproContext,
    set_global_seed,
    verify_determinism,
)

__all__ = [
    # Wave A (Stability): Error Taxonomy
    "PeakTradeError",
    "DataContractError",
    "ConfigError",
    "ProviderError",
    "CacheCorruptionError",
    "BacktestInvariantError",
    # Wave A (Stability): Repro
    "ReproContext",
    "set_global_seed",
    "verify_determinism",
    # Legacy Pydantic
    "Settings",
    "StrategyConfig",
    "load_config",  # Rückwärtskompatibilität
    "load_pydantic_config",
    "load_settings_from_file",
    "get_config",
    "get_strategy_cfg",
    "list_strategies",
    "reset_config",
    "resolve_config_path",
    "DEFAULT_CONFIG_ENV_VAR",
    "DEFAULT_CONFIG_PATH",
    # New TOML
    "PeakConfig",
    "load_peak_config",
    # Registry
    "get_registry_config",
    "get_active_strategies",
    "get_strategy_config",
    "list_registry_strategies",
    # Environment & Safety (Phase 17)
    "TradingEnvironment",
    "EnvironmentConfig",
    "LIVE_CONFIRM_TOKEN",
    "get_environment_from_config",
    "create_default_environment",
    "is_paper",
    "is_testnet",
    "is_live",
]
