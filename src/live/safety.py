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

P0 Guardrails: This file is protected by CODEOWNERS (live trading review required).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

# Direkter Import um zirkuläre Abhängigkeiten zu vermeiden
from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)
from src.ops.gates.armed_gate import ArmedGate, ArmedState
from src.ops.gates.risk_gate import RiskLimits, RiskContext
from src.ops.wiring.execution_guards import (
    GuardConfig,
    GuardInputs,
    apply_execution_guards,
)
from src.ops.recon.models import BalanceSnapshot, PositionSnapshot
from src.ops.recon.providers import NullReconProvider
from src.ops.recon.recon_hook import (
    ReconConfig,
    config_from_env as recon_config_from_env,
    run_recon_if_enabled,
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

    def ensure_may_place_order(
        self, *, is_testnet: bool = False, context: Optional[dict] = None
    ) -> None:
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
        # --- Peak_Trade Runbook-B Guards (B5/B3) ---
        # Default OFF. Enable via PEAK_EXEC_GUARDS_ENABLED=1.
        # When enabled: PEAK_EXEC_GUARDS_SECRET required; optional PEAK_EXEC_GUARDS_TOKEN for arming.
        guards_enabled = os.getenv("PEAK_EXEC_GUARDS_ENABLED", "0") == "1"
        if guards_enabled:
            secret = os.getenv("PEAK_EXEC_GUARDS_SECRET", "").encode("utf-8")
            if not secret:
                self._log_audit(
                    "place_order(runbook_b_guards)",
                    False,
                    "Execution blocked: PEAK_EXEC_GUARDS_SECRET required when PEAK_EXEC_GUARDS_ENABLED=1",
                )
                raise RuntimeError(
                    "Execution blocked: PEAK_EXEC_GUARDS_SECRET required when PEAK_EXEC_GUARDS_ENABLED=1"
                )
            token = os.getenv("PEAK_EXEC_GUARDS_TOKEN")
            gate = ArmedGate(secret=secret, token_ttl_seconds=120)
            cfg = GuardConfig(enabled=True, armed_required=True, risk_enabled=True)
            limits = RiskLimits(
                enabled=True,
                kill_switch=(os.getenv("PEAK_KILL_SWITCH", "0") == "1"),
                max_notional_usd=float(os.getenv("PEAK_MAX_NOTIONAL_USD", "0") or 0.0),
                max_order_size=float(os.getenv("PEAK_MAX_ORDER_SIZE", "0") or 0.0),
                max_position=float(os.getenv("PEAK_MAX_POSITION", "0") or 0.0),
                max_session_loss_usd=float(os.getenv("PEAK_MAX_SESSION_LOSS_USD", "0") or 0.0),
                max_data_age_seconds=int(os.getenv("PEAK_MAX_DATA_AGE_SECONDS", "0") or 0),
            )
            now_epoch = int(os.getenv("PEAK_NOW_EPOCH", "0") or 0) or int(time.time())
            ctx = RiskContext(
                now_epoch=now_epoch,
                market_data_age_seconds=int(os.getenv("PEAK_MD_AGE_SECONDS", "0") or 0),
                session_pnl_usd=float(os.getenv("PEAK_SESSION_PNL_USD", "0") or 0.0),
                current_position=float(os.getenv("PEAK_CURRENT_POSITION", "0") or 0.0),
                order_size=float(os.getenv("PEAK_ORDER_SIZE", "0") or 0.0),
                order_notional_usd=float(os.getenv("PEAK_ORDER_NOTIONAL_USD", "0") or 0.0),
            )
            inputs = GuardInputs(
                armed_state=ArmedState(
                    enabled=True,
                    armed=False,
                    armed_since_epoch=None,
                    token_issued_epoch=None,
                ),
                armed_token=token,
                limits=limits,
                ctx=ctx,
            )
            try:
                _ = apply_execution_guards(cfg, gate=gate, inputs=inputs)
                self._log_audit(
                    "place_order(runbook_b_guards)",
                    True,
                    "Runbook-B guards: allow",
                )
            except RuntimeError as e:
                self._log_audit(
                    "place_order(runbook_b_guards)",
                    False,
                    f"Runbook-B guards: deny — {e!s}",
                )
                raise
        # --- End Guards ---
        # --- Runbook-B Reconciliation Hook (B2) ---
        # Default OFF. Enable explicitly: PEAK_RECON_ENABLED=1
        # NOTE: Pure hook; caller must supply expected/observed snapshots.
        # TODO(wire): Replace placeholder snapshots with real pre/post state.
        recon_cfg = recon_config_from_env()
        if recon_cfg.enabled:
            provider = NullReconProvider(epoch=0, balances={})
            rep = run_recon_if_enabled(
                recon_cfg,
                provider=provider,
                expected_balances=None,
                observed_balances=None,
                expected_positions=None,
                observed_positions=None,
            )
            if not rep.ok:
                self._log_audit(
                    "recon(runbook_b)",
                    False,
                    "Runbook-B recon drift: " + " | ".join(rep.drifts[:5]),
                )
                raise RuntimeError("Execution blocked: reconciliation drift")
            self._log_audit("recon(runbook_b)", True, "Runbook-B recon: ok")
        # --- End Reconciliation Hook ---
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
            self._log_audit(action, False, reason, "Echte Testnet-Integration folgt später")
            raise LiveNotImplementedError(
                f"Echte Testnet-Orders sind in Phase 17 nicht implementiert. "
                f"Nutze testnet_dry_run=True für Dry-Run-Logging."
            )

        # --- LIVE Mode ---
        if env == TradingEnvironment.LIVE:
            # Phase 71: Nutze zentrale Helper-Funktion für klare Gating-Logik
            allowed, reason_detail = is_live_execution_allowed(self.env_config)

            if not allowed:
                # Detaillierte Reason-Logik für verschiedene Blockierungen
                if "enable_live_trading=False" in reason_detail:
                    reason = "enable_live_trading = False (Gate 1)"
                    self._log_audit(action, False, reason)
                    raise LiveTradingDisabledError(
                        f"Live-Trading ist deaktiviert (enable_live_trading=False). "
                        f"Setze enable_live_trading=True in der Config, um fortzufahren."
                    )

                if "live_mode_armed=False" in reason_detail:
                    reason = "live_mode_armed = False (Gate 2 - Phase 71)"
                    self._log_audit(action, False, reason)
                    raise LiveTradingDisabledError(
                        f"Live-Modus ist nicht 'armed' (live_mode_armed=False). "
                        f"Phase 71: Zweistufiges Gating - zusätzliche Freigabe erforderlich. "
                        f"Setze live_mode_armed=True in der Config (nur für Design-Tests)."
                    )

                if "live_dry_run_mode=True" in reason_detail:
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

                if "confirm_token" in reason_detail:
                    reason = "Confirm-Token ungültig oder fehlt"
                    self._log_audit(action, False, reason)
                    raise ConfirmTokenInvalidError(
                        f"Der Bestätigungs-Token ist ungültig oder fehlt. "
                        f"Setze confirm_token='{LIVE_CONFIRM_TOKEN}' in der Config."
                    )

                # Fallback für unbekannte Blockierung
                reason = f"Live-Execution blockiert: {reason_detail}"
                self._log_audit(action, False, reason)
                raise LiveNotImplementedError(
                    f"Live-Trading ist in Phase 71 nicht implementiert. Grund: {reason_detail}"
                )

            # Falls alle Kriterien erfüllt wären (sollte in Phase 71 nicht vorkommen):
            # In Phase 71 ist dies theoretisch nicht erreichbar, da live_dry_run_mode=True
            # immer blockiert. Aber für zukünftige Phasen:
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
                f"Der Bestätigungs-Token ist ungültig oder fehlt. Erwartet: '{LIVE_CONFIRM_TOKEN}'"
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
# Helper-Funktion: is_live_execution_allowed (Phase 71)
# =============================================================================


def is_live_execution_allowed(env_config: EnvironmentConfig) -> tuple[bool, str]:
    """
    Prüft ob echte Live-Execution erlaubt wäre (Phase 71: Design-Kriterium).

    Diese Funktion definiert die **vollständigen Kriterien** für echte Live-Orders.
    In Phase 71 ist diese Funktion nur zur Dokumentation des Designs gedacht.

    Kriterien (alle müssen erfüllt sein):
        1. environment == TradingEnvironment.LIVE
        2. enable_live_trading == True (Gate 1)
        3. live_mode_armed == True (Gate 2 - Phase 71)
        4. live_dry_run_mode == False (technisches Gate - Phase 71)
        5. confirm_token == LIVE_CONFIRM_TOKEN (wenn require_confirm_token == True)

    Args:
        env_config: EnvironmentConfig-Instanz

    Returns:
        Tuple (allowed: bool, reason: str)
        - allowed: True wenn alle Kriterien erfüllt wären
        - reason: Beschreibung warum erlaubt/blockiert

    Note:
        In Phase 71 wird diese Funktion IMMER (False, reason) zurückgeben,
        da live_dry_run_mode=True in Phase 71 immer gesetzt ist.
        Diese Funktion dient der Dokumentation des zukünftigen Designs.

    Example:
        >>> env = EnvironmentConfig(
        ...     environment=TradingEnvironment.LIVE,
        ...     enable_live_trading=True,
        ...     live_mode_armed=True,
        ...     live_dry_run_mode=False,  # Phase 71: Sollte nicht vorkommen
        ...     confirm_token=LIVE_CONFIRM_TOKEN,
        ... )
        >>> allowed, reason = is_live_execution_allowed(env)
        >>> # In Phase 71: allowed wird False sein wegen live_dry_run_mode
    """
    # Kriterium 1: Mode muss LIVE sein
    if env_config.environment != TradingEnvironment.LIVE:
        return (
            False,
            f"Environment ist nicht LIVE (aktuell: {env_config.environment.value})",
        )

    # Kriterium 2: Gate 1 - enable_live_trading
    if not env_config.enable_live_trading:
        return (False, "enable_live_trading=False (Gate 1 blockiert)")

    # Kriterium 3: Gate 2 - live_mode_armed (Phase 71)
    if not env_config.live_mode_armed:
        return (False, "live_mode_armed=False (Gate 2 blockiert - Phase 71)")

    # Kriterium 4: Technisches Gate - live_dry_run_mode (Phase 71)
    if env_config.live_dry_run_mode:
        return (
            False,
            "live_dry_run_mode=True (Phase 71: Technisches Gate blockiert echte Orders)",
        )

    # Kriterium 5: Confirm-Token (wenn erforderlich)
    if env_config.require_confirm_token:
        if env_config.confirm_token != LIVE_CONFIRM_TOKEN:
            return (False, "confirm_token ungültig oder fehlt")

    # Alle Kriterien erfüllt (theoretisch - in Phase 71 nicht erreichbar)
    return (
        True,
        "Alle Kriterien erfüllt (theoretisch - Phase 71: live_dry_run_mode blockiert)",
    )


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


# P0 Drill: CODEOWNERS+MergeQueue enforcement (2025-12-23T17:37:04)
