"""
Data Safety Gate (IDEA-RISK-008)
================================

Safety-First Konzept: Strikte Trennung zwischen synthetischen und realen Daten.

Dieses Modul verhindert, dass synthetische Daten versehentlich im Live-Trading
verwendet werden. Jede Datenquelle muss einen DataSafetyContext deklarieren,
der vom DataSafetyGate geprüft wird.

Regeln:
    - SYNTHETIC_OFFLINE_RT ist NIEMALS erlaubt für LIVE_TRADE
    - SYNTHETIC_OFFLINE_RT ist erlaubt für: BACKTEST, RESEARCH, PAPER_TRADE
    - REAL und HISTORICAL Daten sind grundsätzlich erlaubt

Verwendung:
    from src.data.safety import DataSafetyGate, DataSafetyContext, DataSourceKind, DataUsageContextKind

    context = DataSafetyContext(
        source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
        usage=DataUsageContextKind.BACKTEST,
    )
    DataSafetyGate.ensure_allowed(context)  # OK

    context = DataSafetyContext(
        source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
        usage=DataUsageContextKind.LIVE_TRADE,
    )
    DataSafetyGate.ensure_allowed(context)  # Raises DataSafetyViolationError
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DataSourceKind(Enum):
    """
    Art der Datenquelle.

    Definiert, woher die Daten stammen und ob sie synthetisch sind.
    """

    REAL = "real"
    """Echte Live-Daten von einer Exchange."""

    HISTORICAL = "historical"
    """Historische Daten (z.B. aus CSV, Parquet, API-Abruf)."""

    SYNTHETIC_OFFLINE_RT = "synthetic_offline_rt"
    """Synthetisch generierte Realtime-Daten für Offline-Tests (OfflineRealtimeFeed)."""


class DataUsageContextKind(Enum):
    """
    Kontext, in dem die Daten verwendet werden.

    Bestimmt die Sicherheitsanforderungen.
    """

    BACKTEST = "backtest"
    """Backtesting mit historischen oder synthetischen Daten."""

    RESEARCH = "research"
    """Forschung und Analyse (kein Trading)."""

    PAPER_TRADE = "paper_trade"
    """Paper-Trading (simuliertes Trading, keine echten Orders)."""

    LIVE_TRADE = "live_trade"
    """Live-Trading mit echtem Geld - HÖCHSTE SICHERHEITSANFORDERUNGEN."""


@dataclass(frozen=True)
class DataSafetyContext:
    """
    Kontext für die Safety-Prüfung.

    Beschreibt Datenquelle und Verwendungszweck für die Safety-Gate-Prüfung.

    Attributes:
        source_kind: Art der Datenquelle (real, historical, synthetic).
        usage: Verwendungskontext (backtest, research, paper_trade, live_trade).
        run_id: Optionale Run-ID für Tracing/Logging.
        notes: Optionale Notizen/Kommentare.
    """

    source_kind: DataSourceKind
    usage: DataUsageContextKind
    run_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class DataSafetyResult:
    """
    Ergebnis der Safety-Prüfung.

    Attributes:
        allowed: True, wenn die Kombination erlaubt ist.
        reason: Begründung für die Entscheidung.
        details: Optionale zusätzliche Details (z.B. für Logging).
    """

    allowed: bool
    reason: str
    details: Optional[dict] = field(default=None)


class DataSafetyViolationError(RuntimeError):
    """
    Exception für Safety-Verletzungen.

    Wird geworfen, wenn synthetische Daten in einem nicht erlaubten
    Kontext verwendet werden sollen.

    Attributes:
        result: Das DataSafetyResult mit Details zur Verletzung.
        context: Der DataSafetyContext, der geprüft wurde.
    """

    def __init__(
        self,
        result: DataSafetyResult,
        context: Optional[DataSafetyContext] = None,
    ):
        self.result = result
        self.context = context
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = f"DataSafetyViolation: {self.result.reason}"
        if self.context:
            msg += f" [source={self.context.source_kind.value}, usage={self.context.usage.value}]"
        if self.result.details:
            msg += f" Details: {self.result.details}"
        return msg


class DataSafetyGate:
    """
    Safety-Gate für Datenquellen.

    Prüft, ob eine Datenquelle für einen bestimmten Verwendungszweck
    erlaubt ist. Verhindert insbesondere die Verwendung synthetischer
    Daten im Live-Trading.

    Standard-Regeln (konservativ):
        - SYNTHETIC_OFFLINE_RT ist NIEMALS erlaubt für LIVE_TRADE
        - SYNTHETIC_OFFLINE_RT ist erlaubt für: BACKTEST, RESEARCH, PAPER_TRADE
        - REAL und HISTORICAL sind grundsätzlich erlaubt

    Beispiel:
        context = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.BACKTEST,
        )
        result = DataSafetyGate.check(context)
        assert result.allowed is True

        DataSafetyGate.ensure_allowed(context)  # OK, keine Exception
    """

    # Erlaubte Kombinationen für synthetische Daten
    _SYNTHETIC_ALLOWED_USAGES = frozenset(
        {
            DataUsageContextKind.BACKTEST,
            DataUsageContextKind.RESEARCH,
            DataUsageContextKind.PAPER_TRADE,
        }
    )

    @staticmethod
    def check(context: DataSafetyContext) -> DataSafetyResult:
        """
        Prüft, ob der DataSafetyContext erlaubt ist.

        Args:
            context: Der zu prüfende Kontext.

        Returns:
            DataSafetyResult mit allowed=True/False und Begründung.
        """
        source = context.source_kind
        usage = context.usage

        # Regel 1: Synthetische Daten dürfen NIEMALS für Live-Trading verwendet werden
        if source == DataSourceKind.SYNTHETIC_OFFLINE_RT:
            if usage == DataUsageContextKind.LIVE_TRADE:
                return DataSafetyResult(
                    allowed=False,
                    reason=(
                        "Synthetische Daten (SYNTHETIC_OFFLINE_RT) sind für "
                        "LIVE_TRADE strikt verboten. Synthetische Daten dürfen "
                        "nur für Backtest, Research oder Paper-Trading verwendet werden."
                    ),
                    details={
                        "source_kind": source.value,
                        "usage": usage.value,
                        "rule": "SYNTHETIC_LIVE_BLOCKED",
                    },
                )

            # Synthetische Daten in erlaubten Kontexten
            if usage in DataSafetyGate._SYNTHETIC_ALLOWED_USAGES:
                return DataSafetyResult(
                    allowed=True,
                    reason=(f"Synthetische Daten sind für {usage.value} erlaubt."),
                    details={
                        "source_kind": source.value,
                        "usage": usage.value,
                        "rule": "SYNTHETIC_ALLOWED_CONTEXT",
                    },
                )

            # Fallback: Unbekannter Kontext für synthetische Daten -> sicherheitshalber blockieren
            return DataSafetyResult(
                allowed=False,
                reason=(
                    f"Synthetische Daten sind für unbekannten Kontext "
                    f"'{usage.value}' nicht erlaubt (Safety-First)."
                ),
                details={
                    "source_kind": source.value,
                    "usage": usage.value,
                    "rule": "SYNTHETIC_UNKNOWN_BLOCKED",
                },
            )

        # Regel 2: REAL und HISTORICAL sind grundsätzlich erlaubt
        if source in (DataSourceKind.REAL, DataSourceKind.HISTORICAL):
            return DataSafetyResult(
                allowed=True,
                reason=f"{source.value} Daten sind für {usage.value} erlaubt.",
                details={
                    "source_kind": source.value,
                    "usage": usage.value,
                    "rule": "REAL_HISTORICAL_ALLOWED",
                },
            )

        # Fallback: Unbekannte Quelle -> blockieren
        return DataSafetyResult(
            allowed=False,
            reason=f"Unbekannte Datenquelle '{source.value}' ist nicht erlaubt.",
            details={
                "source_kind": source.value,
                "usage": usage.value,
                "rule": "UNKNOWN_SOURCE_BLOCKED",
            },
        )

    @staticmethod
    def ensure_allowed(context: DataSafetyContext) -> None:
        """
        Prüft den Kontext und wirft eine Exception, wenn nicht erlaubt.

        Args:
            context: Der zu prüfende Kontext.

        Raises:
            DataSafetyViolationError: Wenn die Kombination nicht erlaubt ist.
        """
        result = DataSafetyGate.check(context)
        if not result.allowed:
            raise DataSafetyViolationError(result=result, context=context)
