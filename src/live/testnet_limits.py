# src/live/testnet_limits.py
"""
Peak_Trade: Testnet-Limits & Budget-Kontrolle (Phase 37)
=========================================================

Implementiert ein kontrolliertes Testnet-Budget-System mit:
- Run-Limits (max Notional, max Trades, max Duration pro Run)
- Daily-Limits (max Notional, max Trades pro Tag)
- Symbol-Whitelist (erlaubte Symbole fuer Testnet)
- Usage-Tracking (Persistenz der Tages-Nutzung)

Das Modul ergaenzt die bestehenden LiveRiskLimits (src/live/risk_limits.py)
um eine zusaetzliche Schicht fuer kontrolliertes Testnet-Trading.

Config-Beispiel (config.toml):
------------------------------
    [testnet_limits.run]
    max_notional_per_run = 1000.0
    max_trades_per_run = 50
    max_duration_minutes = 240

    [testnet_limits.daily]
    max_notional_per_day = 5000.0
    max_trades_per_day = 200

    [testnet_limits.symbols]
    allowed = ["BTC/EUR", "ETH/EUR"]

Usage:
------
    from src.live.testnet_limits import (
        TestnetLimitsController,
        TestnetUsageStore,
        load_testnet_limits_from_config,
    )

    controller = load_testnet_limits_from_config(cfg)
    result = controller.check_run_allowed(planned_notional=500.0, planned_trades=20)
    if result.allowed:
        # Run starten...
        controller.register_run_consumption(notional=480.0, trades=18)
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.core.peak_config import PeakConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Dataclasses fuer Limits & State
# =============================================================================


@dataclass
class TestnetRunLimits:
    """
    Limits pro einzelnem Testnet-Run.

    Attributes:
        max_notional_per_run: Maximales Notional (Handelsvolumen) pro Run
        max_trades_per_run: Maximale Anzahl Trades pro Run
        max_duration_minutes: Maximale Laufzeit pro Run in Minuten
    """
    max_notional_per_run: float | None = None
    max_trades_per_run: int | None = None
    max_duration_minutes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dict (fuer Logging/Serialisierung)."""
        return asdict(self)


@dataclass
class TestnetDailyLimits:
    """
    Tages-Limits fuer Testnet-Trading.

    Attributes:
        max_notional_per_day: Maximales Gesamt-Notional pro Tag
        max_trades_per_day: Maximale Anzahl Trades pro Tag
    """
    max_notional_per_day: float | None = None
    max_trades_per_day: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dict (fuer Logging/Serialisierung)."""
        return asdict(self)


@dataclass
class TestnetSymbolPolicy:
    """
    Symbol-Whitelist fuer Testnet-Trading.

    Attributes:
        allowed_symbols: Menge der erlaubten Symbole (z.B. {"BTC/EUR", "ETH/EUR"})
    """
    allowed_symbols: set[str] = field(default_factory=lambda: {"BTC/EUR", "ETH/EUR"})

    def is_allowed(self, symbol: str) -> bool:
        """Prueft, ob ein Symbol erlaubt ist."""
        # Leere Whitelist = alle erlaubt
        if not self.allowed_symbols:
            return True
        return symbol in self.allowed_symbols

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dict (fuer Logging/Serialisierung)."""
        return {"allowed_symbols": list(self.allowed_symbols)}


@dataclass
class TestnetUsageState:
    """
    Aktueller Nutzungsstand fuer einen Tag.

    Attributes:
        day: Datum (UTC)
        notional_used: Bisher verwendetes Notional
        trades_executed: Bisher ausgefuehrte Trades
        runs_completed: Anzahl abgeschlossener Runs
    """
    day: date
    notional_used: float = 0.0
    trades_executed: int = 0
    runs_completed: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dict (fuer Serialisierung)."""
        return {
            "day": self.day.isoformat(),
            "notional_used": self.notional_used,
            "trades_executed": self.trades_executed,
            "runs_completed": self.runs_completed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestnetUsageState:
        """Erstellt TestnetUsageState aus Dict."""
        day_str = data.get("day", "")
        if isinstance(day_str, str):
            day = date.fromisoformat(day_str)
        elif isinstance(day_str, date):
            day = day_str
        else:
            day = date.today()

        return cls(
            day=day,
            notional_used=float(data.get("notional_used", 0.0)),
            trades_executed=int(data.get("trades_executed", 0)),
            runs_completed=int(data.get("runs_completed", 0)),
        )


# =============================================================================
# Check Result
# =============================================================================


@dataclass
class TestnetCheckResult:
    """
    Ergebnis einer Testnet-Limit-Pruefung.

    Attributes:
        allowed: True wenn alle Checks bestanden
        reasons: Liste von Verletzungsgruenden (leer wenn allowed=True)
        current_usage: Aktueller Nutzungsstand
        limits_info: Informationen zu den Limits
    """
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    current_usage: dict[str, Any] | None = None
    limits_info: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        """Ermoeglicht `if result:` Syntax."""
        return self.allowed


# =============================================================================
# Usage Store (Persistenz)
# =============================================================================


class TestnetUsageStore:
    """
    Persistiert die taegliche Testnet-Nutzung.

    Speichert Usage-Daten in JSON-Dateien:
    - Pfad: {base_dir}/usage/usage_YYYY-MM-DD.json
    - Pro Tag eine Datei
    - Automatisches Cleanup alter Dateien (optional)

    Example:
        >>> store = TestnetUsageStore(base_dir=Path("test_results"))
        >>> state = store.load_for_today()
        >>> state.notional_used += 500.0
        >>> state.trades_executed += 10
        >>> store.save_for_today(state)
    """

    def __init__(
        self,
        base_dir: Path,
        retention_days: int = 30,
    ) -> None:
        """
        Initialisiert den UsageStore.

        Args:
            base_dir: Basisverzeichnis fuer Usage-Dateien
            retention_days: Anzahl Tage, die Usage-Dateien aufbewahrt werden
        """
        self._base_dir = Path(base_dir)
        self._usage_dir = self._base_dir / "usage"
        self._retention_days = retention_days

        # Verzeichnis erstellen
        self._usage_dir.mkdir(parents=True, exist_ok=True)

    def _get_usage_file(self, day: date) -> Path:
        """Gibt den Pfad zur Usage-Datei fuer einen Tag zurueck."""
        return self._usage_dir / f"usage_{day.isoformat()}.json"

    def load_for_day(self, day: date) -> TestnetUsageState:
        """
        Laedt den Usage-Stand fuer einen bestimmten Tag.

        Args:
            day: Das Datum

        Returns:
            TestnetUsageState (neu initialisiert wenn Datei nicht existiert)
        """
        usage_file = self._get_usage_file(day)

        if not usage_file.exists():
            return TestnetUsageState(day=day)

        try:
            with open(usage_file) as f:
                data = json.load(f)
            return TestnetUsageState.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[USAGE STORE] Konnte {usage_file} nicht laden: {e}")
            return TestnetUsageState(day=day)

    def load_for_today(self) -> TestnetUsageState:
        """Laedt den Usage-Stand fuer heute (UTC)."""
        today = datetime.now(UTC).date()
        return self.load_for_day(today)

    def save_for_day(self, state: TestnetUsageState) -> None:
        """
        Speichert den Usage-Stand fuer einen Tag.

        Args:
            state: Der zu speichernde State
        """
        usage_file = self._get_usage_file(state.day)

        try:
            with open(usage_file, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.debug(f"[USAGE STORE] Gespeichert: {usage_file}")
        except OSError as e:
            logger.error(f"[USAGE STORE] Konnte {usage_file} nicht speichern: {e}")
            raise

    def save_for_today(self, state: TestnetUsageState) -> None:
        """Speichert den Usage-Stand fuer heute."""
        # Sicherstellen, dass das Datum heute ist
        today = datetime.now(UTC).date()
        state.day = today
        self.save_for_day(state)

    def cleanup_old_files(self) -> int:
        """
        Entfernt alte Usage-Dateien.

        Returns:
            Anzahl geloeschter Dateien
        """
        cutoff = datetime.now(UTC).date()
        deleted = 0

        try:
            for usage_file in self._usage_dir.glob("usage_*.json"):
                try:
                    # Datum aus Dateiname extrahieren
                    date_str = usage_file.stem.replace("usage_", "")
                    file_date = date.fromisoformat(date_str)

                    days_old = (cutoff - file_date).days
                    if days_old > self._retention_days:
                        usage_file.unlink()
                        deleted += 1
                        logger.debug(f"[USAGE STORE] Geloescht: {usage_file}")
                except (ValueError, OSError):
                    pass  # Ungueltige Datei ignorieren

        except OSError as e:
            logger.warning(f"[USAGE STORE] Cleanup fehlgeschlagen: {e}")

        return deleted


# =============================================================================
# Testnet Limits Controller
# =============================================================================


class TestnetLimitsController:
    """
    Kontrolliert Testnet-Limits und -Budgets.

    Dieser Controller:
    1. Prueft Run-Limits (Notional, Trades, Duration)
    2. Prueft Daily-Limits (Notional, Trades)
    3. Prueft Symbol-Whitelist
    4. Trackt und persistiert die taegliche Nutzung

    Example:
        >>> controller = TestnetLimitsController(
        ...     run_limits=TestnetRunLimits(max_notional_per_run=1000.0),
        ...     daily_limits=TestnetDailyLimits(max_notional_per_day=5000.0),
        ...     symbol_policy=TestnetSymbolPolicy({"BTC/EUR", "ETH/EUR"}),
        ...     usage_store=TestnetUsageStore(Path("test_results")),
        ... )
        >>>
        >>> # Vor Run pruefen
        >>> result = controller.check_run_allowed(planned_notional=500.0)
        >>> if result.allowed:
        ...     # Run starten...
        ...     controller.register_run_consumption(notional=480.0, trades=15)
    """

    def __init__(
        self,
        run_limits: TestnetRunLimits,
        daily_limits: TestnetDailyLimits,
        symbol_policy: TestnetSymbolPolicy,
        usage_store: TestnetUsageStore,
    ) -> None:
        """
        Initialisiert den TestnetLimitsController.

        Args:
            run_limits: Limits pro Run
            daily_limits: Limits pro Tag
            symbol_policy: Symbol-Whitelist
            usage_store: Store fuer Usage-Persistenz
        """
        self._run_limits = run_limits
        self._daily_limits = daily_limits
        self._symbol_policy = symbol_policy
        self._usage_store = usage_store

        logger.info(
            f"[TESTNET LIMITS] Initialisiert: "
            f"run_limits={run_limits.to_dict()}, "
            f"daily_limits={daily_limits.to_dict()}"
        )

    @property
    def run_limits(self) -> TestnetRunLimits:
        """Zugriff auf Run-Limits."""
        return self._run_limits

    @property
    def daily_limits(self) -> TestnetDailyLimits:
        """Zugriff auf Daily-Limits."""
        return self._daily_limits

    @property
    def symbol_policy(self) -> TestnetSymbolPolicy:
        """Zugriff auf Symbol-Policy."""
        return self._symbol_policy

    def check_symbol_allowed(self, symbol: str) -> TestnetCheckResult:
        """
        Prueft, ob ein Symbol in der Whitelist ist.

        Args:
            symbol: Das zu pruefende Symbol (z.B. "BTC/EUR")

        Returns:
            TestnetCheckResult
        """
        is_allowed = self._symbol_policy.is_allowed(symbol)

        if is_allowed:
            return TestnetCheckResult(
                allowed=True,
                reasons=[],
                limits_info={"allowed_symbols": list(self._symbol_policy.allowed_symbols)},
            )
        else:
            return TestnetCheckResult(
                allowed=False,
                reasons=[
                    f"symbol_not_allowed(symbol={symbol}, "
                    f"allowed={list(self._symbol_policy.allowed_symbols)})"
                ],
                limits_info={"allowed_symbols": list(self._symbol_policy.allowed_symbols)},
            )

    def check_run_limits(
        self,
        planned_notional: float | None = None,
        planned_trades: int | None = None,
        planned_duration_minutes: int | None = None,
    ) -> TestnetCheckResult:
        """
        Prueft, ob ein geplanter Run die Run-Limits einhält.

        Args:
            planned_notional: Geplantes Notional fuer den Run
            planned_trades: Geplante Anzahl Trades
            planned_duration_minutes: Geplante Laufzeit in Minuten

        Returns:
            TestnetCheckResult
        """
        reasons: list[str] = []
        limits = self._run_limits

        # Notional pruefen
        if (
            planned_notional is not None
            and limits.max_notional_per_run is not None
            and planned_notional > limits.max_notional_per_run
        ):
            reasons.append(
                f"run_notional_exceeded(planned={planned_notional:.2f}, "
                f"max={limits.max_notional_per_run:.2f})"
            )

        # Trades pruefen
        if (
            planned_trades is not None
            and limits.max_trades_per_run is not None
            and planned_trades > limits.max_trades_per_run
        ):
            reasons.append(
                f"run_trades_exceeded(planned={planned_trades}, "
                f"max={limits.max_trades_per_run})"
            )

        # Duration pruefen
        if (
            planned_duration_minutes is not None
            and limits.max_duration_minutes is not None
            and planned_duration_minutes > limits.max_duration_minutes
        ):
            reasons.append(
                f"run_duration_exceeded(planned={planned_duration_minutes}min, "
                f"max={limits.max_duration_minutes}min)"
            )

        return TestnetCheckResult(
            allowed=len(reasons) == 0,
            reasons=reasons,
            limits_info=limits.to_dict(),
        )

    def check_daily_limits(
        self,
        additional_notional: float | None = None,
        additional_trades: int | None = None,
    ) -> TestnetCheckResult:
        """
        Prueft, ob ein zusaetzlicher Run die Daily-Limits einhalten wuerde.

        Args:
            additional_notional: Zusaetzliches Notional durch den Run
            additional_trades: Zusaetzliche Trades durch den Run

        Returns:
            TestnetCheckResult mit aktuellem Usage-Stand
        """
        reasons: list[str] = []
        limits = self._daily_limits
        current_usage = self._usage_store.load_for_today()

        # Notional pruefen
        if additional_notional is not None and limits.max_notional_per_day is not None:
            projected = current_usage.notional_used + additional_notional
            if projected > limits.max_notional_per_day:
                reasons.append(
                    f"daily_notional_exceeded(current={current_usage.notional_used:.2f}, "
                    f"additional={additional_notional:.2f}, "
                    f"projected={projected:.2f}, "
                    f"max={limits.max_notional_per_day:.2f})"
                )

        # Trades pruefen
        if additional_trades is not None and limits.max_trades_per_day is not None:
            projected = current_usage.trades_executed + additional_trades
            if projected > limits.max_trades_per_day:
                reasons.append(
                    f"daily_trades_exceeded(current={current_usage.trades_executed}, "
                    f"additional={additional_trades}, "
                    f"projected={projected}, "
                    f"max={limits.max_trades_per_day})"
                )

        return TestnetCheckResult(
            allowed=len(reasons) == 0,
            reasons=reasons,
            current_usage=current_usage.to_dict(),
            limits_info=limits.to_dict(),
        )

    def check_run_allowed(
        self,
        symbol: str | None = None,
        planned_notional: float | None = None,
        planned_trades: int | None = None,
        planned_duration_minutes: int | None = None,
    ) -> TestnetCheckResult:
        """
        Kombinierte Pruefung aller Limits fuer einen geplanten Run.

        Prueft:
        1. Symbol-Whitelist (wenn symbol angegeben)
        2. Run-Limits (Notional, Trades, Duration)
        3. Daily-Limits (aktueller Stand + geplanter Run)

        Args:
            symbol: Symbol des geplanten Runs (optional)
            planned_notional: Geplantes Notional
            planned_trades: Geplante Anzahl Trades
            planned_duration_minutes: Geplante Laufzeit

        Returns:
            TestnetCheckResult mit allen Pruefungsergebnissen
        """
        all_reasons: list[str] = []
        current_usage = self._usage_store.load_for_today()

        # 1. Symbol-Check
        if symbol is not None:
            symbol_result = self.check_symbol_allowed(symbol)
            if not symbol_result.allowed:
                all_reasons.extend(symbol_result.reasons)

        # 2. Run-Limits
        run_result = self.check_run_limits(
            planned_notional=planned_notional,
            planned_trades=planned_trades,
            planned_duration_minutes=planned_duration_minutes,
        )
        if not run_result.allowed:
            all_reasons.extend(run_result.reasons)

        # 3. Daily-Limits
        daily_result = self.check_daily_limits(
            additional_notional=planned_notional,
            additional_trades=planned_trades,
        )
        if not daily_result.allowed:
            all_reasons.extend(daily_result.reasons)

        return TestnetCheckResult(
            allowed=len(all_reasons) == 0,
            reasons=all_reasons,
            current_usage=current_usage.to_dict(),
            limits_info={
                "run_limits": self._run_limits.to_dict(),
                "daily_limits": self._daily_limits.to_dict(),
                "symbol_policy": self._symbol_policy.to_dict(),
            },
        )

    def register_run_consumption(
        self,
        notional: float,
        trades: int,
    ) -> TestnetUsageState:
        """
        Registriert den Verbrauch eines abgeschlossenen Runs.

        Args:
            notional: Tatsaechlich verwendetes Notional
            trades: Tatsaechlich ausgefuehrte Trades

        Returns:
            Aktualisierter UsageState
        """
        current_usage = self._usage_store.load_for_today()

        current_usage.notional_used += notional
        current_usage.trades_executed += trades
        current_usage.runs_completed += 1

        self._usage_store.save_for_today(current_usage)

        logger.info(
            f"[TESTNET LIMITS] Run registriert: "
            f"notional={notional:.2f}, trades={trades}, "
            f"daily_total_notional={current_usage.notional_used:.2f}, "
            f"daily_total_trades={current_usage.trades_executed}"
        )

        return current_usage

    def get_daily_usage(self) -> TestnetUsageState:
        """Gibt den aktuellen taeglichen Nutzungsstand zurueck."""
        return self._usage_store.load_for_today()

    def get_remaining_budget(self) -> dict[str, Any]:
        """
        Berechnet das verbleibende Budget fuer heute.

        Returns:
            Dict mit remaining_notional, remaining_trades, etc.
        """
        usage = self._usage_store.load_for_today()
        daily = self._daily_limits

        remaining_notional = None
        if daily.max_notional_per_day is not None:
            remaining_notional = max(0.0, daily.max_notional_per_day - usage.notional_used)

        remaining_trades = None
        if daily.max_trades_per_day is not None:
            remaining_trades = max(0, daily.max_trades_per_day - usage.trades_executed)

        return {
            "day": usage.day.isoformat(),
            "notional_used": usage.notional_used,
            "trades_executed": usage.trades_executed,
            "runs_completed": usage.runs_completed,
            "remaining_notional": remaining_notional,
            "remaining_trades": remaining_trades,
            "limits": daily.to_dict(),
        }


# =============================================================================
# Config Loader
# =============================================================================


def load_testnet_limits_from_config(
    cfg: PeakConfig,
    base_dir: Path | None = None,
) -> TestnetLimitsController:
    """
    Erstellt einen TestnetLimitsController aus PeakConfig.

    Liest die Konfiguration aus:
    - [testnet_limits.run]
    - [testnet_limits.daily]
    - [testnet_limits.symbols]

    Args:
        cfg: PeakConfig-Instanz
        base_dir: Optionales Basisverzeichnis fuer Usage-Store
                  (Default: test_results/)

    Returns:
        Konfigurierter TestnetLimitsController

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config("config/config.toml")
        >>> controller = load_testnet_limits_from_config(cfg)
    """
    # Run-Limits
    run_limits = TestnetRunLimits(
        max_notional_per_run=cfg.get("testnet_limits.run.max_notional_per_run"),
        max_trades_per_run=cfg.get("testnet_limits.run.max_trades_per_run"),
        max_duration_minutes=cfg.get("testnet_limits.run.max_duration_minutes"),
    )

    # Daily-Limits
    daily_limits = TestnetDailyLimits(
        max_notional_per_day=cfg.get("testnet_limits.daily.max_notional_per_day"),
        max_trades_per_day=cfg.get("testnet_limits.daily.max_trades_per_day"),
    )

    # Symbol-Policy
    allowed_symbols_list = cfg.get("testnet_limits.symbols.allowed", ["BTC/EUR", "ETH/EUR"])
    if isinstance(allowed_symbols_list, str):
        allowed_symbols_list = [allowed_symbols_list]
    symbol_policy = TestnetSymbolPolicy(allowed_symbols=set(allowed_symbols_list))

    # Usage-Store
    if base_dir is None:
        base_dir_str = cfg.get("testnet_orchestration.runs_base_dir", "test_results")
        base_dir = Path(base_dir_str)

    usage_store = TestnetUsageStore(base_dir=base_dir)

    return TestnetLimitsController(
        run_limits=run_limits,
        daily_limits=daily_limits,
        symbol_policy=symbol_policy,
        usage_store=usage_store,
    )
