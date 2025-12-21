"""
Peak_Trade Config System (Phase 36 refactored)
===============================================
Pydantic-basierte Konfigurationsverwaltung mit Validierung.

Verwendung:
    from src.core import get_config

    cfg = get_config()
    print(cfg.risk.risk_per_trade)

Environment Variables:
    PEAK_TRADE_CONFIG_PATH: Pfad zu alternativer config.toml

    Beispiel:
        export PEAK_TRADE_CONFIG_PATH=/path/to/custom_config.toml
        python scripts/run_backtest.py

Config-Pfad-Prioritaet:
    1. Explizit uebergebener path-Parameter
    2. Environment Variable PEAK_TRADE_CONFIG_PATH
    3. Default: config/config.toml relativ zum Projekt-Root
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import toml


# Environment Variable fuer Config-Pfad (Phase 36: vereinheitlicht)
DEFAULT_CONFIG_ENV_VAR = "PEAK_TRADE_CONFIG_PATH"

# Projekt-Root ermitteln (relativ zu dieser Datei)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default Config-Pfad: config/config.toml im Projekt-Root
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.toml"


class BacktestConfig(BaseModel):
    """Backtest-Parameter."""

    initial_cash: float = Field(gt=0, description="Startkapital")
    results_dir: Path = Field(default=Path("results"))


class RiskConfig(BaseModel):
    """Risk-Management-Parameter."""

    risk_per_trade: float = Field(
        default=0.01, gt=0, le=0.05, description="Max. Risiko pro Trade (1% = 0.01)"
    )
    max_daily_loss: float = Field(
        default=0.03, gt=0, le=0.10, description="Max. Tagesverlust (Kill-Switch)"
    )
    max_positions: int = Field(default=2, ge=1, description="Max. parallele Positionen")
    max_position_size: float = Field(
        default=0.25, gt=0, le=1.0, description="Max. Positionsgröße (% des Kontos)"
    )
    min_position_value: float = Field(default=50.0, ge=0, description="Min. Positionswert USD")
    min_stop_distance: float = Field(default=0.005, gt=0, description="Min. Stop-Distanz (%)")


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
    """Konfiguration für den DummyExchangeClient (Phase 38)."""

    btc_eur_price: float = Field(default=50000.0, gt=0)
    eth_eur_price: float = Field(default=3000.0, gt=0)
    btc_usd_price: float = Field(default=55000.0, gt=0)
    fee_bps: float = Field(default=10.0, ge=0)
    slippage_bps: float = Field(default=5.0, ge=0)


class ExchangeConfig(BaseModel):
    """
    Exchange-Client-Konfiguration (Phase 38).

    Bestimmt, welcher Exchange-Client für Trading verwendet wird.

    Attributes:
        default_type: Client-Typ ("dummy", "kraken_testnet", später "kraken_live")
        dummy: Einstellungen für DummyExchangeClient
    """

    default_type: str = Field(
        default="dummy",
        pattern="^(dummy|kraken_testnet|kraken_live)$",
        description="Exchange-Client-Typ",
    )
    dummy: ExchangeDummyConfig = Field(default_factory=ExchangeDummyConfig)


class ValidationConfig(BaseModel):
    """Mindestanforderungen für Live-Trading."""

    min_sharpe: float = Field(default=1.5, gt=0)
    max_drawdown: float = Field(default=-0.15, lt=0)
    min_trades: int = Field(default=50, gt=0)
    min_profit_factor: float = Field(default=1.3, gt=1.0)
    min_backtest_months: int = Field(default=6, ge=3)


class StrategyConfig(BaseModel):
    """
    Basis-Konfiguration für Trading-Strategien.

    Alle Strategien sollten mindestens diese Felder haben.
    Zusätzliche Parameter können als beliebige Felder hinzugefügt werden.
    """

    model_config = ConfigDict(extra="allow")

    # Pflichtfelder für alle Strategien
    stop_pct: float = Field(default=0.02, gt=0, le=0.10, description="Stop-Loss in Prozent")

    # Optional: Take-Profit
    take_profit_pct: Optional[float] = Field(
        default=None, gt=0, description="Take-Profit in Prozent (optional)"
    )


class Settings(BaseModel):
    """
    Hauptkonfiguration.

    Unterstützt sowohl Attribut-Zugriff (settings.backtest.initial_cash)
    als auch Dict-Zugriff (settings["backtest"]["initial_cash"]) für
    Rückwärtskompatibilität.
    """

    backtest: BacktestConfig
    risk: RiskConfig
    data: DataConfig
    live: LiveConfig
    validation: ValidationConfig
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    strategy: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """
        Ermöglicht Dict-ähnlichen Zugriff auf Settings.

        Args:
            key: Attributname (z.B. "backtest", "risk")

        Returns:
            Attributwert oder nested dict für Sub-Configs

        Example:
            >>> settings["backtest"]["initial_cash"]
            10000.0
        """
        value = getattr(self, key)
        # Wenn value ein Pydantic-Model ist, wandle es in dict um für nested access
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Dict-ähnlicher get()-Zugriff mit Default-Wert.

        Args:
            key: Attributname
            default: Rückgabewert wenn key nicht existiert

        Returns:
            Attributwert oder default
        """
        try:
            return self[key]
        except AttributeError:
            return default


# Singleton-Pattern für globale Config
_CONFIG_CACHE: Optional[Settings] = None


def resolve_config_path(path: Optional[Path] = None) -> Path:
    """
    Bestimmt den Config-Pfad mit folgender Priorität:
    1. Explizit übergebener Path-Parameter
    2. Environment Variable PEAK_TRADE_CONFIG
    3. Default: config.toml im aktuellen Verzeichnis

    Args:
        path: Optional expliziter Pfad

    Returns:
        Aufgelöster Config-Pfad

    Example:
        >>> # Mit Environment Variable
        >>> os.environ['PEAK_TRADE_CONFIG'] = '/custom/config.toml'
        >>> path = resolve_config_path()
        >>> print(path)
        /custom/config.toml
    """
    # 1. Explizit übergeben
    if path is not None:
        return Path(path)

    # 2. Environment Variable
    env_path = os.getenv(DEFAULT_CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)

    # 3. Default
    return DEFAULT_CONFIG_PATH


def load_settings_from_file(path: Optional[Path] = None) -> Settings:
    """
    Liest config.toml ein und baut ein Settings-Objekt.

    Args:
        path: Optional - Pfad zur config.toml
              Wenn None: Nutzt resolve_config_path() (env var oder default)

    Returns:
        Settings-Instanz

    Raises:
        FileNotFoundError: Wenn config.toml nicht existiert
        toml.TomlDecodeError: Bei fehlerhaftem TOML

    Example:
        >>> # Mit Default-Pfad
        >>> settings = load_settings_from_file()

        >>> # Mit custom Pfad
        >>> settings = load_settings_from_file(Path("custom_config.toml"))

        >>> # Mit Environment Variable
        >>> os.environ['PEAK_TRADE_CONFIG'] = 'test_config.toml'
        >>> settings = load_settings_from_file()
    """
    config_path = resolve_config_path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config nicht gefunden: {config_path}\n"
            f"Gesucht in: {config_path.absolute()}\n"
            f"Tipp: Setze Environment Variable {DEFAULT_CONFIG_ENV_VAR} "
            f"oder übergebe path-Parameter"
        )

    raw = toml.load(config_path)

    # Pydantic macht bereits Basis-Validierung
    settings = Settings(**raw)
    return settings


def validate_settings(settings: Settings) -> Settings:
    """
    Führt zusätzliche, logische Validierungen aus,
    die über reine Typprüfungen hinausgehen.

    Args:
        settings: Settings-Instanz

    Returns:
        Validierte Settings-Instanz

    Raises:
        ValueError: Bei logischen Inkonsistenzen

    Note:
        Diese Funktion ist ZUSÄTZLICH zu Pydantics Validierung.
        Hier prüfen wir Dinge wie Pfad-Existenz, Plausibilität, etc.
    """
    # --- Risk-Checks ---
    risk = settings.risk

    # Pydantic prüft bereits gt=0, le=0.05, aber wir können noch mehr:
    if risk.risk_per_trade > 0.02:
        # WARNUNG (keine Exception, aber Log)
        import logging

        logging.warning(f"⚠️  risk_per_trade={risk.risk_per_trade:.1%} ist hoch! Empfohlen: <= 2%")

    if risk.max_position_size > 0.5:
        import logging

        logging.warning(
            f"⚠️  max_position_size={risk.max_position_size:.0%} ist hoch! Empfohlen: <= 50%"
        )

    # --- Backtest-Checks ---
    bt = settings.backtest

    # Verzeichnisse anlegen, falls nicht vorhanden
    bt.results_dir.mkdir(parents=True, exist_ok=True)

    # --- Data-Checks ---
    data = settings.data
    data.data_dir.mkdir(parents=True, exist_ok=True)

    # --- Live-Trading-Checks ---
    if settings.live.enabled and settings.live.mode == "live":
        raise ValueError(
            "⛔ Live-Trading ist aktiviert! "
            "NIEMALS ohne min. 6 Monate erfolgreiche Backtests aktivieren! "
            "Setze live.enabled=false oder live.mode='paper'"
        )

    return settings


def get_config(force_reload: bool = False) -> Settings:
    """
    Gibt das globale Settings-Objekt zurück (Singleton-Pattern).
    Liest config.toml nur einmal ein (Caching).

    Args:
        force_reload: Cache ignorieren und neu laden?

    Returns:
        Validierte Settings-Instanz

    Usage:
        >>> from src.core import get_config
        >>> cfg = get_config()
        >>> print(cfg.risk.risk_per_trade)
        0.01

    Note:
        - Beim ersten Aufruf wird config.toml geladen
        - Weitere Aufrufe nutzen den Cache
        - force_reload=True erzwingt Neuladen (z.B. für Tests)
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None and not force_reload:
        return _CONFIG_CACHE

    # Config laden und validieren
    settings = load_settings_from_file()
    settings = validate_settings(settings)

    # Cache speichern
    _CONFIG_CACHE = settings
    return settings


def reset_config() -> None:
    """
    Reset Config-Cache (für Tests).

    Usage:
        >>> from src.core.config import reset_config, get_config
        >>> reset_config()
        >>> cfg = get_config()  # Lädt config.toml neu
    """
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


# Backwards-Compatibility (falls alte Funktionsnamen verwendet werden)
load_config = load_settings_from_file


def get_strategy_cfg(name: str) -> Dict[str, Any]:
    """
    Holt Strategie-Konfiguration aus config.toml mit klarer Fehlerbehandlung.

    Args:
        name: Name der Strategie (z.B. "ma_crossover")

    Returns:
        Dict mit Strategie-Parametern

    Raises:
        KeyError: Wenn Strategie nicht in config.toml definiert ist

    Example:
        >>> from src.core import get_strategy_cfg
        >>> params = get_strategy_cfg("ma_crossover")
        >>> print(params['fast_period'])
        10

    Note:
        Wirft einen hilfreichen Fehler mit Liste aller verfügbaren Strategien.
    """
    cfg = get_config()

    if name not in cfg.strategy:
        available = ", ".join(sorted(cfg.strategy.keys())) if cfg.strategy else "keine"
        raise KeyError(
            f"Strategy '{name}' nicht in config.toml definiert. Verfügbare Strategien: {available}"
        )

    return cfg.strategy[name]


def list_strategies() -> list[str]:
    """
    Liste aller in config.toml definierten Strategien.

    Returns:
        Sortierte Liste von Strategie-Namen

    Example:
        >>> from src.core import list_strategies
        >>> strategies = list_strategies()
        >>> print(strategies)
        ['ma_crossover', 'rsi_strategy']
    """
    cfg = get_config()
    return sorted(cfg.strategy.keys())
