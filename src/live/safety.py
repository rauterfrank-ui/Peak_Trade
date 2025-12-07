# src/live/safety.py
"""
Peak_Trade: Safety-Layer für Live/Testnet-Operationen
=====================================================

Zentraler Safeguard für alle potenziell kritischen Trading-Operationen.
Stellt sicher, dass nur in erlaubten Umgebungen und nur mit expliziter
Bestätigung echte Orders gesendet werden können.

Phase 17: KEINE echten Orders werden implementiert!
           Dieser Layer bereitet die Architektur vor.

Exceptions:
    SafetyBlockedError: Wird geworfen wenn eine Operation geblockt wird
    LiveTradingDisabledError: Live-Trading ist deaktiviert
    ConfirmTokenInvalidError: Bestätigungs-Token ist ungültig
    LiveNotImplementedError: Live-Trading ist nicht implementiert

WICHTIG: In Phase 17 blockt der SafetyGuard ALLE echten Orders.
         Es gibt keine Implementierung für Live-Order-Calls.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

# Direkter Import um zirkuläre Abhängigkeiten zu vermeiden
from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class SafetyBlockedError(RuntimeError):
    """Basisklasse für Safety-Layer-Blockierungen."""

    pass


class LiveTradingDisabledError(SafetyBlockedError):
    """Live-Trading ist in der Konfiguration deaktiviert."""

    pass


class ConfirmTokenInvalidError(SafetyBlockedError):
    """Der Bestätigungs-Token ist ungültig oder fehlt."""

    pass


class LiveNotImplementedError(SafetyBlockedError):
    """
    Live-Trading ist in dieser Projektphase nicht implementiert.

    Diese Exception wird in Phase 17 bei jedem Versuch geworfen,
    echte Orders zu senden.
    """

    pass


class TestnetDryRunOnlyError(SafetyBlockedError):
    """Testnet ist nur im Dry-Run-Modus verfügbar."""

    pass


class PaperModeOrderError(SafetyBlockedError):
    """Im Paper-Modus können keine echten Orders gesendet werden."""

    pass


# =============================================================================
# Safety Audit Log Entry
# =============================================================================


@dataclass
class SafetyAuditEntry:
    """
    Audit-Log-Eintrag für Safety-Checks.

    Attributes:
        timestamp: Zeitpunkt des Checks
        action: Durchgeführte/versuchte Aktion
        environment: Aktive Umgebung
        allowed: Ob die Aktion erlaubt wurde
        reason: Grund für Block/Erlaubnis
        details: Zusätzliche Details
    """

    timestamp: datetime
    action: str
    environment: TradingEnvironment
    allowed: bool
    reason: str
    details: Optional[str] = None


# =============================================================================
# SafetyGuard
# =============================================================================


@dataclass
class SafetyGuard:
    """
    Zentraler Safeguard für Live/Testnet-Operationen.

    Stellt sicher, dass nur in erlaubten Umgebungen und nur
    mit expliziter Bestätigung potenziell kritische Aktionen
    durchgeführt werden.

    Phase 17 Verhalten:
        - PAPER: Nur Paper-/Backtest-Operationen erlaubt
        - TESTNET: Nur Dry-Run erlaubt (keine echten Testnet-Orders)
        - LIVE: Immer blockiert (nicht implementiert)

    Attributes:
        env_config: Die Environment-Konfiguration
        audit_log: Liste der Audit-Einträge

    Example:
        >>> guard = SafetyGuard(env_config=EnvironmentConfig())
        >>> guard.ensure_may_place_order()  # Raises PaperModeOrderError
    """

    env_config: EnvironmentConfig
    audit_log: List[SafetyAuditEntry] = None  # type: ignore

    def __post_init__(self) -> None:
        """Initialisiert die Audit-Log-Liste."""
        if self.audit_log is None:
            self.audit_log = []

    def _log_audit(
        self,
        action: str,
        allowed: bool,
        reason: str,
        details: Optional[str] = None,
    ) -> None:
        """Fügt einen Eintrag zum Audit-Log hinzu."""
        entry = SafetyAuditEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            environment=self.env_config.environment,
            allowed=allowed,
            reason=reason,
            details=details,
        )
        self.audit_log.append(entry)

        # Auch in Standard-Logger schreiben
        level = logging.INFO if allowed else logging.WARNING
        log_msg = (
            f"SafetyGuard: action={action}, env={self.env_config.environment.value}, "
            f"allowed={allowed}, reason={reason}"
        )
        if details:
            log_msg += f", details={details}"
        logger.log(level, log_msg)

    def ensure_may_place_order(self, *, is_testnet: bool = False) -> None:
        """
        Prüft ob eine Order-Platzierung erlaubt ist.

        Hebt im Fehlerfall eine Exception aus, BEVOR ein Orderversuch
        überhaupt technisch abgesetzt wird.

        Args:
            is_testnet: Ob es sich um eine Testnet-Order handelt

        Raises:
            PaperModeOrderError: Im Paper-Modus (keine echten Orders)
            TestnetDryRunOnlyError: Testnet nur im Dry-Run (Phase 17)
            LiveNotImplementedError: Live ist nicht implementiert (Phase 17)
            LiveTradingDisabledError: enable_live_trading = False
            ConfirmTokenInvalidError: Token fehlt oder ungültig

        Note:
            In Phase 17 wird diese Methode IMMER eine Exception werfen,
            da echte Orders nicht implementiert sind.
        """
        env = self.env_config.environment
        action = f"place_order(is_testnet={is_testnet})"

        # --- PAPER Mode ---
        if env == TradingEnvironment.PAPER:
            reason = "Paper-Modus: Keine echten Orders erlaubt"
            self._log_audit(action, False, reason)
            raise PaperModeOrderError(
                f"Im Paper-Modus können keine echten Orders gesendet werden. "
                f"Verwende PaperOrderExecutor für Simulationen."
            )

        # --- TESTNET Mode ---
        if env == TradingEnvironment.TESTNET:
            if self.env_config.testnet_dry_run:
                reason = "Testnet Dry-Run Modus aktiv"
                self._log_audit(action, False, reason)
                raise TestnetDryRunOnlyError(
                    f"Testnet ist nur im Dry-Run-Modus verfügbar (Phase 17). "
                    f"testnet_dry_run=True blockt echte Testnet-Orders."
                )
            # Selbst wenn dry_run=False, ist echtes Testnet in Phase 17 nicht implementiert
            reason = "Testnet-Orders nicht implementiert (Phase 17)"
            self._log_audit(
                action, False, reason, "Echte Testnet-Integration folgt später"
            )
            raise LiveNotImplementedError(
                f"Echte Testnet-Orders sind in Phase 17 nicht implementiert. "
                f"Nutze testnet_dry_run=True für Dry-Run-Logging."
            )

        # --- LIVE Mode ---
        if env == TradingEnvironment.LIVE:
            # Phase 71: Zweistufiges Gating
            # Gate 1: enable_live_trading
            if not self.env_config.enable_live_trading:
                reason = "enable_live_trading = False (Gate 1)"
                self._log_audit(action, False, reason)
                raise LiveTradingDisabledError(
                    f"Live-Trading ist deaktiviert (enable_live_trading=False). "
                    f"Setze enable_live_trading=True in der Config, um fortzufahren."
                )

            # Phase 71: Gate 2: live_mode_armed
            if not self.env_config.live_mode_armed:
                reason = "live_mode_armed = False (Gate 2 - Phase 71)"
                self._log_audit(action, False, reason)
                raise LiveTradingDisabledError(
                    f"Live-Modus ist nicht 'armed' (live_mode_armed=False). "
                    f"Phase 71: Zweistufiges Gating - zusätzliche Freigabe erforderlich. "
                    f"Setze live_mode_armed=True in der Config (nur für Design-Tests)."
                )

            # Prüfe Confirm-Token
            if self.env_config.require_confirm_token:
                if self.env_config.confirm_token != LIVE_CONFIRM_TOKEN:
                    reason = "Confirm-Token ungültig oder fehlt"
                    self._log_audit(action, False, reason)
                    raise ConfirmTokenInvalidError(
                        f"Der Bestätigungs-Token ist ungültig oder fehlt. "
                        f"Setze confirm_token='{LIVE_CONFIRM_TOKEN}' in der Config."
                    )

            # Phase 71: Live-Dry-Run-Modus prüfen
            if self.env_config.live_dry_run_mode:
                # Phase 71: Live-Path existiert als Design, aber nur Dry-Run
                # Diese Methode wird normalerweise nicht aufgerufen, wenn live_dry_run_mode=True,
                # da LiveOrderExecutor direkt simuliert. Aber für Safety-Checks:
                reason = "Live-Dry-Run-Modus aktiv (Phase 71)"
                self._log_audit(
                    action,
                    False,
                    reason,
                    "Phase 71: Live-Execution-Design - nur Dry-Run, keine echten Orders",
                )
                # In Phase 71 erlauben wir Dry-Run, aber blockieren echte Orders
                # Diese Exception wird nur geworfen, wenn jemand versucht, echte Orders zu senden
                raise LiveNotImplementedError(
                    f"Live-Trading ist in Phase 71 nur als Design/Dry-Run implementiert. "
                    f"live_dry_run_mode=True blockt echte Orders. "
                    f"Verwende LiveOrderExecutor für Dry-Run-Simulationen."
                )

            # Falls live_dry_run_mode=False (sollte in Phase 71 nicht vorkommen):
            reason = "Live-Trading nicht implementiert (Phase 71)"
            self._log_audit(
                action,
                False,
                reason,
                "Live-Order-Execution wird in einer späteren Phase implementiert",
            )
            raise LiveNotImplementedError(
                f"Live-Trading ist in Phase 71 nicht implementiert. "
                f"Diese Projektphase dient nur der Architektur-Vorbereitung. "
                f"Echte Live-Orders werden erst in einer späteren Phase unterstützt."
            )

        # Unbekannter Modus (sollte nicht vorkommen)
        reason = f"Unbekannter Environment-Modus: {env}"
        self._log_audit(action, False, reason)
        raise SafetyBlockedError(reason)

    def ensure_not_live(self) -> None:
        """
        Stellt sicher, dass wir NICHT im Live-Modus sind.

        Nützlich für Operationen, die explizit nicht im Live-Modus
        ausgeführt werden sollen (z.B. Backtest-only Features).

        Raises:
            SafetyBlockedError: Wenn im Live-Modus
        """
        if self.env_config.is_live:
            action = "ensure_not_live"
            reason = "Operation ist im Live-Modus nicht erlaubt"
            self._log_audit(action, False, reason)
            raise SafetyBlockedError(
                f"Diese Operation ist im Live-Modus nicht erlaubt. "
                f"Wechsle zu paper oder testnet Umgebung."
            )

        self._log_audit("ensure_not_live", True, "Nicht im Live-Modus")

    def ensure_confirm_token(self) -> None:
        """
        Prüft ob ein gültiger Bestätigungs-Token gesetzt ist.

        Raises:
            ConfirmTokenInvalidError: Token fehlt oder ungültig
        """
        action = "ensure_confirm_token"

        if not self.env_config.require_confirm_token:
            self._log_audit(action, True, "Token-Prüfung nicht erforderlich")
            return

        if self.env_config.confirm_token != LIVE_CONFIRM_TOKEN:
            reason = "Confirm-Token ungültig"
            self._log_audit(action, False, reason)
            raise ConfirmTokenInvalidError(
                f"Der Bestätigungs-Token ist ungültig oder fehlt. "
                f"Erwartet: '{LIVE_CONFIRM_TOKEN}'"
            )

        self._log_audit(action, True, "Token validiert")

    def may_use_dry_run(self) -> bool:
        """
        Prüft ob Dry-Run-Operationen erlaubt sind.

        Dry-Run ist in allen Umgebungen erlaubt und erzeugt
        simulierte OrderExecutionResults ohne echte API-Calls.

        Returns:
            True (immer erlaubt)
        """
        self._log_audit("may_use_dry_run", True, "Dry-Run ist immer erlaubt")
        return True

    def get_effective_mode(self) -> str:
        """
        Gibt den effektiven Ausführungsmodus zurück.

        In Phase 71 ist der effektive Modus für Live "live_dry_run",
        da Live-Execution-Path als Design existiert, aber nur Dry-Run erlaubt.

        Returns:
            "paper", "dry_run", "live_dry_run", oder "blocked"
        """
        env = self.env_config.environment

        if env == TradingEnvironment.PAPER:
            return "paper"
        if env == TradingEnvironment.TESTNET:
            return "dry_run"  # Immer Dry-Run in Phase 71
        if env == TradingEnvironment.LIVE:
            # Phase 71: Live-Path existiert als Design, aber nur Dry-Run
            if self.env_config.live_dry_run_mode:
                return "live_dry_run"  # Phase 71: Design/Dry-Run
            return "blocked"  # Falls live_dry_run_mode=False (sollte nicht vorkommen)

        return "unknown"

    def get_audit_log(self) -> List[SafetyAuditEntry]:
        """Gibt eine Kopie des Audit-Logs zurück."""
        return list(self.audit_log)

    def clear_audit_log(self) -> None:
        """Löscht das Audit-Log."""
        self.audit_log.clear()


# =============================================================================
# Factory-Funktion
# =============================================================================


def create_safety_guard(env_config: Optional[EnvironmentConfig] = None) -> SafetyGuard:
    """
    Erstellt einen SafetyGuard mit der gegebenen oder Default-Konfiguration.

    Args:
        env_config: Environment-Konfiguration (Default: Paper-Modus)

    Returns:
        Konfigurierter SafetyGuard
    """
    if env_config is None:
        from src.core.environment import create_default_environment

        env_config = create_default_environment()

    return SafetyGuard(env_config=env_config)
