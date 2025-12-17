"""
Peak_Trade Core Module
======================
Zentrale Konfiguration und gemeinsame Utilities.

Es gibt zwei Config-Systeme:
1. config_pydantic.py - Pydantic-basiert (für alte Scripts)
2. peak_config.py - TOML-basiert (neue OOP-API)
3. config_registry.py - Registry-basiert (für Portfolio-Backtests)
"""

# Alte Pydantic-Config (Legacy)
from .config_pydantic import (
    DEFAULT_CONFIG_ENV_VAR,
    DEFAULT_CONFIG_PATH,
    Settings,
    StrategyConfig,
    get_config,
    get_strategy_cfg,
    list_strategies,
    load_config,  # Behalte Original-Namen für Rückwärtskompatibilität
    load_settings_from_file,
    reset_config,
    resolve_config_path,
)
from .config_pydantic import (
    load_config as load_pydantic_config,  # Alias
)
from .config_registry import (
    get_active_strategies,
    get_strategy_config,
)

# Registry-Config (Portfolio)
from .config_registry import (
    get_config as get_registry_config,
)
from .config_registry import (
    list_strategies as list_registry_strategies,
)

# Environment & Safety (Phase 17)
from .environment import (
    LIVE_CONFIRM_TOKEN,
    EnvironmentConfig,
    TradingEnvironment,
    create_default_environment,
    get_environment_from_config,
    is_live,
    is_paper,
    is_testnet,
)

# Neue TOML-Config (OOP)
from .peak_config import (
    PeakConfig,
)
from .peak_config import (
    load_config as load_peak_config,
)

__all__ = [
    "DEFAULT_CONFIG_ENV_VAR",
    "DEFAULT_CONFIG_PATH",
    "LIVE_CONFIRM_TOKEN",
    "EnvironmentConfig",
    # New TOML
    "PeakConfig",
    # Legacy Pydantic
    "Settings",
    "StrategyConfig",
    # Environment & Safety (Phase 17)
    "TradingEnvironment",
    "create_default_environment",
    "get_active_strategies",
    "get_config",
    "get_environment_from_config",
    # Registry
    "get_registry_config",
    "get_strategy_cfg",
    "get_strategy_config",
    "is_live",
    "is_paper",
    "is_testnet",
    "list_registry_strategies",
    "list_strategies",
    "load_config",  # Rückwärtskompatibilität
    "load_peak_config",
    "load_pydantic_config",
    "load_settings_from_file",
    "reset_config",
    "resolve_config_path",
]
