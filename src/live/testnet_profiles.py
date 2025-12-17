# src/live/testnet_profiles.py
"""
Peak_Trade: Testnet-Session-Profile (Phase 37)
===============================================

Implementiert vordefinierte Testnet-Session-Profile, die eine
standardisierte und wiederholbare Testnet-Konfiguration ermoeglichen.

Ein Profil beschreibt:
- Strategie (z.B. "ma_crossover")
- Symbol (z.B. "BTC/EUR")
- Timeframe (z.B. "1m", "5m", "1h")
- Laufzeit (Duration in Minuten)
- Limits (max Notional, max Trades)
- Optionale Beschreibung

Config-Beispiel (config.toml):
------------------------------
    [testnet_profiles.ma_crossover_small]
    strategy = "ma_crossover"
    symbol = "BTC/EUR"
    timeframe = "1m"
    duration_minutes = 60
    max_notional = 500.0
    max_trades = 20
    description = "Kleiner BTC/EUR Intraday-Test"

    [testnet_profiles.eth_swing]
    strategy = "ma_crossover"
    symbol = "ETH/EUR"
    timeframe = "15m"
    duration_minutes = 180
    max_notional = 2000.0
    max_trades = 40
    description = "ETH Swing Test"

Usage:
------
    from src.live.testnet_profiles import (
        load_testnet_profiles,
        get_testnet_profile,
        TestnetSessionProfile,
    )

    profiles = load_testnet_profiles(cfg)
    profile = profiles.get("ma_crossover_small")
    if profile:
        print(f"Profile: {profile.id} - {profile.description}")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.core.peak_config import PeakConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Testnet Session Profile
# =============================================================================


@dataclass
class TestnetSessionProfile:
    """
    Vordefiniertes Profil fuer eine Testnet-Session.

    Attributes:
        id: Eindeutige Profil-ID (z.B. "ma_crossover_small")
        description: Beschreibung des Profils
        strategy: Name der Strategie (z.B. "ma_crossover")
        symbol: Trading-Symbol (z.B. "BTC/EUR")
        timeframe: Candle-Timeframe (z.B. "1m", "5m", "1h")
        duration_minutes: Max. Laufzeit in Minuten (None = unbegrenzt)
        max_notional: Max. Notional pro Run (None = unbegrenzt)
        max_trades: Max. Trades pro Run (None = unbegrenzt)
        position_fraction: Anteil des Kapitals pro Trade (optional)
        fee_rate: Fee-Rate fuer PnL-Berechnung (optional)
        slippage_bps: Slippage in Basispunkten (optional)
        extra_params: Zusaetzliche strategie-spezifische Parameter
    """

    id: str
    description: str = ""
    strategy: str = "ma_crossover"
    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    duration_minutes: int | None = None
    max_notional: float | None = None
    max_trades: int | None = None
    position_fraction: float | None = None
    fee_rate: float | None = None
    slippage_bps: float | None = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert das Profil zu einem Dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "strategy": self.strategy,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "duration_minutes": self.duration_minutes,
            "max_notional": self.max_notional,
            "max_trades": self.max_trades,
            "position_fraction": self.position_fraction,
            "fee_rate": self.fee_rate,
            "slippage_bps": self.slippage_bps,
            "extra_params": self.extra_params,
        }

    def with_overrides(self, **kwargs: Any) -> TestnetSessionProfile:
        """
        Erstellt eine Kopie des Profils mit ueberschriebenen Werten.

        Args:
            **kwargs: Zu ueberschreibende Felder

        Returns:
            Neues TestnetSessionProfile mit aktualisierten Werten

        Example:
            >>> profile = TestnetSessionProfile(id="test", strategy="ma_crossover")
            >>> modified = profile.with_overrides(duration_minutes=30, max_notional=300.0)
        """
        current = self.to_dict()
        current.update(kwargs)
        return TestnetSessionProfile(**current)

    @classmethod
    def from_dict(cls, profile_id: str, data: dict[str, Any]) -> TestnetSessionProfile:
        """
        Erstellt ein Profil aus einem Dictionary.

        Args:
            profile_id: Die Profil-ID
            data: Dictionary mit Profil-Daten

        Returns:
            TestnetSessionProfile-Instanz
        """
        # Bekannte Felder extrahieren
        known_fields = {
            "description",
            "strategy",
            "symbol",
            "timeframe",
            "duration_minutes",
            "max_notional",
            "max_trades",
            "position_fraction",
            "fee_rate",
            "slippage_bps",
        }

        # Extra-Parameter sammeln (alles was nicht bekannt ist)
        extra_params = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            id=profile_id,
            description=data.get("description", ""),
            strategy=data.get("strategy", "ma_crossover"),
            symbol=data.get("symbol", "BTC/EUR"),
            timeframe=data.get("timeframe", "1m"),
            duration_minutes=data.get("duration_minutes"),
            max_notional=data.get("max_notional"),
            max_trades=data.get("max_trades"),
            position_fraction=data.get("position_fraction"),
            fee_rate=data.get("fee_rate"),
            slippage_bps=data.get("slippage_bps"),
            extra_params=extra_params,
        )


# =============================================================================
# Profile Validation
# =============================================================================


@dataclass
class ProfileValidationResult:
    """
    Ergebnis der Profil-Validierung.

    Attributes:
        valid: True wenn Profil gueltig
        errors: Liste von Fehlern
        warnings: Liste von Warnungen
    """
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_profile(profile: TestnetSessionProfile) -> ProfileValidationResult:
    """
    Validiert ein Testnet-Session-Profil.

    Prueft:
    - Pflichtfelder (id, strategy, symbol)
    - Wertebereiche (duration, notional, trades)
    - Timeframe-Format

    Args:
        profile: Das zu validierende Profil

    Returns:
        ProfileValidationResult
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Pflichtfelder
    if not profile.id:
        errors.append("Profil-ID fehlt")
    if not profile.strategy:
        errors.append("Strategie fehlt")
    if not profile.symbol:
        errors.append("Symbol fehlt")

    # Wertebereiche
    if profile.duration_minutes is not None and profile.duration_minutes <= 0:
        errors.append(f"duration_minutes muss positiv sein (ist: {profile.duration_minutes})")

    if profile.max_notional is not None and profile.max_notional <= 0:
        errors.append(f"max_notional muss positiv sein (ist: {profile.max_notional})")

    if profile.max_trades is not None and profile.max_trades <= 0:
        errors.append(f"max_trades muss positiv sein (ist: {profile.max_trades})")

    if profile.position_fraction is not None and not (0 < profile.position_fraction <= 1.0):
        errors.append(
            f"position_fraction muss zwischen 0 und 1 liegen (ist: {profile.position_fraction})"
        )

    # Timeframe-Format
    valid_timeframes = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}
    if profile.timeframe and profile.timeframe not in valid_timeframes:
        warnings.append(
            f"Unbekannter Timeframe: {profile.timeframe}. "
            f"Bekannte: {sorted(valid_timeframes)}"
        )

    # Warnungen fuer fehlende Limits
    if profile.duration_minutes is None:
        warnings.append("Keine Laufzeit-Begrenzung (duration_minutes) definiert")
    if profile.max_notional is None:
        warnings.append("Kein Notional-Limit (max_notional) definiert")

    return ProfileValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# =============================================================================
# Profile Loader
# =============================================================================


def load_testnet_profiles(cfg: PeakConfig) -> dict[str, TestnetSessionProfile]:
    """
    Laedt alle Testnet-Profile aus der Config.

    Liest Profile aus [testnet_profiles.*] Bloecken.

    Args:
        cfg: PeakConfig-Instanz

    Returns:
        Dictionary von profile_id -> TestnetSessionProfile

    Example:
        >>> cfg = load_config("config/config.toml")
        >>> profiles = load_testnet_profiles(cfg)
        >>> for name, profile in profiles.items():
        ...     print(f"{name}: {profile.description}")
    """
    profiles: dict[str, TestnetSessionProfile] = {}

    # Hole den gesamten testnet_profiles Block
    profiles_block = cfg.get("testnet_profiles", {})

    if not isinstance(profiles_block, dict):
        logger.warning("[TESTNET PROFILES] Kein [testnet_profiles] Block in Config")
        return profiles

    for profile_id, profile_data in profiles_block.items():
        if not isinstance(profile_data, dict):
            logger.warning(
                f"[TESTNET PROFILES] Profil '{profile_id}' uebersprungen: "
                f"Erwartet dict, bekommen {type(profile_data).__name__}"
            )
            continue

        try:
            profile = TestnetSessionProfile.from_dict(profile_id, profile_data)

            # Validierung
            validation = validate_profile(profile)
            if not validation.valid:
                logger.warning(
                    f"[TESTNET PROFILES] Profil '{profile_id}' ungueltig: "
                    f"{validation.errors}"
                )
                continue

            if validation.warnings:
                logger.debug(
                    f"[TESTNET PROFILES] Profil '{profile_id}' Warnungen: "
                    f"{validation.warnings}"
                )

            profiles[profile_id] = profile
            logger.debug(f"[TESTNET PROFILES] Profil '{profile_id}' geladen")

        except Exception as e:
            logger.warning(
                f"[TESTNET PROFILES] Fehler beim Laden von '{profile_id}': {e}"
            )

    logger.info(f"[TESTNET PROFILES] {len(profiles)} Profile geladen: {list(profiles.keys())}")
    return profiles


def get_testnet_profile(
    cfg: PeakConfig,
    profile_id: str,
) -> TestnetSessionProfile | None:
    """
    Laedt ein einzelnes Testnet-Profil aus der Config.

    Args:
        cfg: PeakConfig-Instanz
        profile_id: Die Profil-ID

    Returns:
        TestnetSessionProfile oder None wenn nicht gefunden

    Example:
        >>> profile = get_testnet_profile(cfg, "ma_crossover_small")
        >>> if profile:
        ...     print(profile.strategy)
    """
    profiles = load_testnet_profiles(cfg)
    return profiles.get(profile_id)


def list_testnet_profiles(cfg: PeakConfig) -> list[str]:
    """
    Listet alle verfuegbaren Profil-IDs.

    Args:
        cfg: PeakConfig-Instanz

    Returns:
        Sortierte Liste von Profil-IDs
    """
    profiles = load_testnet_profiles(cfg)
    return sorted(profiles.keys())


# =============================================================================
# Profile Summary
# =============================================================================


def get_profiles_summary(cfg: PeakConfig) -> str:
    """
    Erstellt eine formatierte Zusammenfassung aller Profile.

    Args:
        cfg: PeakConfig-Instanz

    Returns:
        Formatierter String mit Profil-Uebersicht
    """
    profiles = load_testnet_profiles(cfg)

    if not profiles:
        return "Keine Testnet-Profile definiert."

    lines = ["Verfuegbare Testnet-Profile:", "=" * 50]

    for profile_id, profile in sorted(profiles.items()):
        lines.append(f"\n[{profile_id}]")
        lines.append(f"  Strategie:    {profile.strategy}")
        lines.append(f"  Symbol:       {profile.symbol}")
        lines.append(f"  Timeframe:    {profile.timeframe}")

        if profile.duration_minutes:
            lines.append(f"  Laufzeit:     {profile.duration_minutes} Minuten")
        else:
            lines.append("  Laufzeit:     unbegrenzt")

        if profile.max_notional:
            lines.append(f"  Max Notional: {profile.max_notional:.2f}")

        if profile.max_trades:
            lines.append(f"  Max Trades:   {profile.max_trades}")

        if profile.description:
            lines.append(f"  Beschreibung: {profile.description}")

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


# =============================================================================
# Built-in Default Profiles
# =============================================================================


def get_default_profiles() -> dict[str, TestnetSessionProfile]:
    """
    Gibt die eingebauten Default-Profile zurueck.

    Diese Profile koennen verwendet werden, wenn keine Config-Profile
    definiert sind.

    Returns:
        Dictionary von profile_id -> TestnetSessionProfile
    """
    return {
        "quick_test": TestnetSessionProfile(
            id="quick_test",
            description="Schneller Smoke-Test (5 Minuten)",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            duration_minutes=5,
            max_notional=100.0,
            max_trades=5,
        ),
        "btc_intraday": TestnetSessionProfile(
            id="btc_intraday",
            description="BTC Intraday Test (1 Stunde)",
            strategy="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            duration_minutes=60,
            max_notional=500.0,
            max_trades=20,
        ),
        "eth_swing": TestnetSessionProfile(
            id="eth_swing",
            description="ETH Swing Test (3 Stunden)",
            strategy="ma_crossover",
            symbol="ETH/EUR",
            timeframe="15m",
            duration_minutes=180,
            max_notional=2000.0,
            max_trades=40,
        ),
    }
