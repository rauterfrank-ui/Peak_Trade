# src/core/environment.py
"""
Peak_Trade: Environment-Abstraktion & Konfiguration
====================================================

Definiert die Trading-Umgebungen (paper, testnet, live) und die
zugehörige Konfiguration für das Safety-System.

Environments:
- PAPER: Simulation ohne echte Orders (Backtests, Paper-Trading)
- TESTNET: Testnet-Orders (z.B. Kraken/Binance Testnet) - aktuell Dry-Run
- LIVE: Echte Orders an Börsen (NICHT implementiert in Phase 17)

WICHTIG: In Phase 17 werden KEINE echten Orders gesendet.
         Testnet/Live sind nur als Architektur vorbereitet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .peak_config import PeakConfig


class TradingEnvironment(str, Enum):
    """
    Trading-Umgebung.

    Values:
        PAPER: Paper-Trading / Backtest (Simulation)
        TESTNET: Testnet-Orders (Dry-Run in Phase 17)
        LIVE: Echte Orders (NICHT implementiert)
    """

    PAPER = "paper"
    TESTNET = "testnet"
    LIVE = "live"


# Sicherer Bestätigungs-Token für Live-Trading
# Muss explizit in der Config gesetzt werden
LIVE_CONFIRM_TOKEN = "I_KNOW_WHAT_I_AM_DOING"


@dataclass
class EnvironmentConfig:
    """
    Konfiguration für die Trading-Umgebung.

    Attributes:
        environment: Aktive Trading-Umgebung (paper/testnet/live)
        enable_live_trading: Zusätzlicher Safety-Schalter für Live-Trading
        require_confirm_token: Ob ein Bestätigungs-Token erforderlich ist
        confirm_token: Der Bestätigungs-Token (wenn gesetzt)
        testnet_dry_run: Ob Testnet im Dry-Run-Modus läuft (Default: True)
        log_all_orders: Ob alle Orders geloggt werden sollen

    Safety-Hinweise:
        - enable_live_trading = False blockt alle echten Orders
        - require_confirm_token = True erfordert den korrekten Token
        - In Phase 17 ist Live-Trading generell nicht implementiert
    """

    environment: TradingEnvironment = TradingEnvironment.PAPER
    enable_live_trading: bool = False
    require_confirm_token: bool = True
    confirm_token: Optional[str] = None
    testnet_dry_run: bool = True
    log_all_orders: bool = True

    def __post_init__(self) -> None:
        """Validierung und Typ-Konvertierung nach Initialisierung."""
        # Konvertiere String zu Enum wenn nötig
        if isinstance(self.environment, str):
            self.environment = TradingEnvironment(self.environment.lower())

    @property
    def is_paper(self) -> bool:
        """True wenn Paper-Trading-Modus aktiv."""
        return self.environment == TradingEnvironment.PAPER

    @property
    def is_testnet(self) -> bool:
        """True wenn Testnet-Modus aktiv."""
        return self.environment == TradingEnvironment.TESTNET

    @property
    def is_live(self) -> bool:
        """True wenn Live-Modus aktiv."""
        return self.environment == TradingEnvironment.LIVE

    @property
    def allows_real_orders(self) -> bool:
        """
        True wenn echte Orders theoretisch erlaubt wären.

        ACHTUNG: In Phase 17 gibt es KEINE Implementation für echte Orders.
                 Diese Property dient nur zur Safety-Architektur.
        """
        if self.environment == TradingEnvironment.PAPER:
            return False
        if self.environment == TradingEnvironment.TESTNET:
            # Testnet könnte echte Testnet-Orders senden, aber in Phase 17
            # ist dies nur als Dry-Run implementiert
            return not self.testnet_dry_run
        if self.environment == TradingEnvironment.LIVE:
            # Live nur wenn explizit aktiviert UND Token korrekt
            if not self.enable_live_trading:
                return False
            if self.require_confirm_token:
                return self.confirm_token == LIVE_CONFIRM_TOKEN
            return True
        return False

    def validate_confirm_token(self) -> bool:
        """
        Prüft ob der Confirm-Token korrekt ist.

        Returns:
            True wenn Token korrekt oder nicht erforderlich
        """
        if not self.require_confirm_token:
            return True
        return self.confirm_token == LIVE_CONFIRM_TOKEN


def get_environment_from_config(peak_config: PeakConfig) -> EnvironmentConfig:
    """
    Erstellt eine EnvironmentConfig aus einer PeakConfig.

    Liest den [environment]-Block aus der TOML-Config.
    Wenn nicht vorhanden, werden sichere Defaults verwendet.

    Args:
        peak_config: Die PeakConfig-Instanz

    Returns:
        EnvironmentConfig mit den Werten aus der Config
    """
    # Environment-Mode aus Config lesen
    mode_str = peak_config.get("environment.mode", "paper")
    try:
        environment = TradingEnvironment(mode_str.lower())
    except ValueError:
        # Fallback auf Paper bei ungültigem Wert
        environment = TradingEnvironment.PAPER

    return EnvironmentConfig(
        environment=environment,
        enable_live_trading=peak_config.get("environment.enable_live_trading", False),
        require_confirm_token=peak_config.get(
            "environment.require_confirm_token", True
        ),
        confirm_token=peak_config.get("environment.confirm_token", None),
        testnet_dry_run=peak_config.get("environment.testnet_dry_run", True),
        log_all_orders=peak_config.get("environment.log_all_orders", True),
    )


def create_default_environment() -> EnvironmentConfig:
    """
    Erstellt eine sichere Default-EnvironmentConfig.

    Defaults auf Paper-Modus mit allen Safety-Features aktiviert.

    Returns:
        EnvironmentConfig mit sicheren Defaults
    """
    return EnvironmentConfig(
        environment=TradingEnvironment.PAPER,
        enable_live_trading=False,
        require_confirm_token=True,
        confirm_token=None,
        testnet_dry_run=True,
        log_all_orders=True,
    )


# Convenience-Funktionen für schnelle Checks


def is_paper(env_config: EnvironmentConfig) -> bool:
    """Prüft ob Paper-Modus aktiv."""
    return env_config.is_paper


def is_testnet(env_config: EnvironmentConfig) -> bool:
    """Prüft ob Testnet-Modus aktiv."""
    return env_config.is_testnet


def is_live(env_config: EnvironmentConfig) -> bool:
    """Prüft ob Live-Modus aktiv."""
    return env_config.is_live
