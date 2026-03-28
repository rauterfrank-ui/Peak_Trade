"""
Zentrale Config-Facade (re-exports).

Historisch war dieses Modul ein Platzhalter. Es bündelt die öffentliche
Config-API für stabile Imports::

    from src.core.config import load_config, PeakConfig
    from src.core.config import reset_config, get_config  # Pydantic-Cache

``load_config`` ohne Qualifier bezeichnet hier den **TOML-/PeakConfig**-Loader
(:func:`src.core.peak_config.load_config`). Der Legacy-Pydantic-Loader ist
:func:`load_pydantic_config`.
"""

from __future__ import annotations

from .config_pydantic import (
    DEFAULT_CONFIG_ENV_VAR,
    DEFAULT_CONFIG_PATH,
    Settings,
    StrategyConfig,
    get_config,
    get_strategy_cfg,
    list_strategies,
    load_config as load_pydantic_config,
    load_settings_from_file,
    reset_config,
    resolve_config_path,
)
from .peak_config import (
    AUTO_LIVE_OVERRIDES_PATH,
    PeakConfig,
    load_config,
    load_config_default,
    load_config_with_live_overrides,
)

__all__ = [
    "AUTO_LIVE_OVERRIDES_PATH",
    "DEFAULT_CONFIG_ENV_VAR",
    "DEFAULT_CONFIG_PATH",
    "PeakConfig",
    "Settings",
    "StrategyConfig",
    "get_config",
    "get_strategy_cfg",
    "list_strategies",
    "load_config",
    "load_config_default",
    "load_config_with_live_overrides",
    "load_pydantic_config",
    "load_settings_from_file",
    "reset_config",
    "resolve_config_path",
]
