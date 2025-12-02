"""
Peak_Trade Simple Config Loader
=================================
Einfacher TOML-basierter Config-Loader ohne Pydantic.

Verwendung:
    from src.core.config_simple import load_config

    cfg = load_config()
    print(cfg['risk']['risk_per_trade'])

Environment Variables:
    PEAK_TRADE_CONFIG: Pfad zu alternativer config.toml
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import os

try:
    import toml
except ImportError:
    import tomli as toml  # Python 3.11+ fallback


# Default Config Pfad
DEFAULT_CONFIG_PATH = Path("config/default.toml")
DEFAULT_CONFIG_ENV_VAR = "PEAK_TRADE_CONFIG"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """
    Lädt die TOML-Config und gibt sie als dict zurück.

    Wenn config_path None ist, wird config/default.toml verwendet,
    es sei denn PEAK_TRADE_CONFIG Environment Variable ist gesetzt.

    Args:
        config_path: Pfad zur TOML-Datei (optional)

    Returns:
        dict mit Config-Daten

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert

    Examples:
        >>> # Default config/default.toml
        >>> cfg = load_config()
        >>> print(cfg['backtest']['initial_cash'])
        10000.0

        >>> # Custom path
        >>> cfg = load_config('my_config.toml')

        >>> # Via Environment Variable
        >>> import os
        >>> os.environ['PEAK_TRADE_CONFIG'] = 'custom.toml'
        >>> cfg = load_config()
    """
    # Pfad bestimmen
    if config_path is not None:
        path = Path(config_path)
    else:
        # 1. Environment Variable prüfen
        env_path = os.getenv(DEFAULT_CONFIG_ENV_VAR)
        if env_path:
            path = Path(env_path)
        else:
            # 2. Default verwenden
            path = DEFAULT_CONFIG_PATH

    # Datei prüfen
    if not path.is_file():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            f"Gesucht in: {path.absolute()}\n"
            f"Tipp: Setze Environment Variable {DEFAULT_CONFIG_ENV_VAR} oder "
            f"übergebe config_path Parameter"
        )

    # TOML laden
    with open(path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    return config


def get_strategy_config(config: dict[str, Any], strategy_name: str) -> dict[str, Any]:
    """
    Holt Strategie-Config aus dem Config-Dict.

    Args:
        config: Config-Dict von load_config()
        strategy_name: Name der Strategie (z.B. 'ma_crossover')

    Returns:
        dict mit Strategie-Parametern

    Raises:
        KeyError: Wenn Strategie nicht definiert ist

    Example:
        >>> cfg = load_config()
        >>> strat_cfg = get_strategy_config(cfg, 'ma_crossover')
        >>> print(strat_cfg['fast_period'])
        10
    """
    if 'strategy' not in config:
        raise KeyError("Keine Strategien in Config definiert (fehlt [strategy] Sektion)")

    if strategy_name not in config['strategy']:
        available = ", ".join(sorted(config['strategy'].keys()))
        raise KeyError(
            f"Strategie '{strategy_name}' nicht in Config gefunden. "
            f"Verfügbare Strategien: {available}"
        )

    return config['strategy'][strategy_name]


def list_strategies(config: dict[str, Any]) -> list[str]:
    """
    Liste aller definierten Strategien.

    Args:
        config: Config-Dict von load_config()

    Returns:
        Sortierte Liste von Strategie-Namen

    Example:
        >>> cfg = load_config()
        >>> strategies = list_strategies(cfg)
        >>> print(strategies)
        ['ma_crossover', 'momentum_1h', 'rsi_strategy']
    """
    if 'strategy' not in config:
        return []

    return sorted(config['strategy'].keys())
