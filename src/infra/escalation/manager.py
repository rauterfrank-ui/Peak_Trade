# src/infra/escalation/manager.py
"""
Peak_Trade: Escalation Manager (Phase 85)
==========================================

Zentrale Verwaltung von Eskalationen mit Config-Gating.

Features:
- Severity-basierte Eskalations-Entscheidung
- Environment-Gating (nur in konfigurierten Umgebungen)
- Robuste Fehlerbehandlung (Eskalations-Fehler blockieren nie Alerts)
- Unterstützung für mehrere Targets
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Set

from .models import EscalationEvent, EscalationTarget
from .providers import EscalationProvider, NullEscalationProvider, get_provider

logger = logging.getLogger(__name__)


class EscalationManager:
    """
    Zentrale Verwaltung von Eskalationen.

    Entscheidet basierend auf:
    - Severity des Events
    - Aktuellem Environment
    - Konfiguration (enabled, critical_severities, enabled_environments)

    Fehler in Eskalationen werden geloggt, aber NIEMALS propagiert.
    Dies garantiert, dass die Alert-Pipeline nicht blockiert wird.

    Usage:
        >>> manager = EscalationManager(
        ...     provider=PagerDutyLikeProviderStub(),
        ...     targets=[EscalationTarget(name="Primary On-Call")],
        ...     enabled=True,
        ...     enabled_environments={"live"},
        ...     critical_severities={"CRITICAL"},
        ...     current_environment="live",
        ... )
        >>> manager.maybe_escalate(event)
    """

    def __init__(
        self,
        provider: EscalationProvider,
        targets: List[EscalationTarget],
        enabled: bool = True,
        enabled_environments: Optional[Set[str]] = None,
        critical_severities: Optional[Set[str]] = None,
        current_environment: str = "paper",
    ) -> None:
        """
        Initialisiert EscalationManager.

        Args:
            provider: EscalationProvider-Instanz
            targets: Liste von EscalationTarget-Definitionen
            enabled: Ob Eskalation global aktiviert ist
            enabled_environments: Set von Environments in denen eskaliert wird
            critical_severities: Set von Severities die eskaliert werden
            current_environment: Aktuelles Environment ("paper", "testnet", "live")
        """
        self._provider = provider
        self._targets = targets
        self._enabled = enabled
        self._enabled_environments = enabled_environments or {"live"}
        self._critical_severities = critical_severities or {"CRITICAL"}
        self._current_environment = current_environment
        self._logger = logging.getLogger(f"{__name__}.EscalationManager")

    @property
    def enabled(self) -> bool:
        """Ob Eskalation global aktiviert ist."""
        return self._enabled

    @property
    def current_environment(self) -> str:
        """Aktuelles Environment."""
        return self._current_environment

    @property
    def enabled_environments(self) -> Set[str]:
        """Environments in denen eskaliert wird."""
        return self._enabled_environments

    @property
    def critical_severities(self) -> Set[str]:
        """Severities die eskaliert werden."""
        return self._critical_severities

    def maybe_escalate(self, event: EscalationEvent) -> bool:
        """
        Prüft ob eskaliert werden soll und führt ggf. Eskalation durch.

        Eskalation erfolgt nur wenn:
        1. enabled = True
        2. current_environment in enabled_environments
        3. event.severity in critical_severities

        Fehler werden geloggt, aber NIEMALS propagiert.

        Args:
            event: EscalationEvent zum Prüfen/Eskalieren

        Returns:
            True wenn eskaliert wurde, False sonst
        """
        try:
            # Gate 1: Global deaktiviert?
            if not self._enabled:
                self._logger.debug("Escalation disabled globally")
                return False

            # Gate 2: Environment nicht in enabled_environments?
            if self._current_environment not in self._enabled_environments:
                self._logger.debug(
                    f"Escalation disabled for environment '{self._current_environment}' "
                    f"(enabled: {self._enabled_environments})"
                )
                return False

            # Gate 3: Severity nicht kritisch genug?
            severity_upper = event.severity.upper()
            if severity_upper not in self._critical_severities:
                self._logger.debug(
                    f"Severity '{event.severity}' not in critical_severities "
                    f"({self._critical_severities})"
                )
                return False

            # Eskalation durchführen
            return self._do_escalate(event)

        except Exception as e:
            # KRITISCH: Fehler NIEMALS nach außen propagieren
            self._logger.error(
                f"Error in escalation decision/execution: {e}",
                exc_info=True,
            )
            return False

    def _do_escalate(self, event: EscalationEvent) -> bool:
        """
        Führt die eigentliche Eskalation durch.

        Args:
            event: EscalationEvent zum Eskalieren

        Returns:
            True wenn mindestens ein Target erfolgreich eskaliert wurde
        """
        escalated_any = False

        for target in self._targets:
            if not target.enabled:
                continue

            # Target-spezifische Severity-Prüfung
            if not self._severity_meets_target(event.severity, target.min_severity):
                continue

            try:
                self._provider.send(event, target)
                self._logger.info(
                    f"Escalated to '{target.name}': [{event.severity}] {event.summary}"
                )
                escalated_any = True
            except Exception as e:
                # Provider-Fehler loggen, aber weiter zu anderen Targets
                self._logger.error(
                    f"Failed to escalate to '{target.name}': {e}",
                    exc_info=True,
                )

        return escalated_any

    def _severity_meets_target(
        self, event_severity: str, target_min_severity: str
    ) -> bool:
        """
        Prüft ob Event-Severity >= Target-Min-Severity.

        Args:
            event_severity: Severity des Events
            target_min_severity: Minimale Severity des Targets

        Returns:
            True wenn Event-Severity >= Target-Min-Severity
        """
        # Severity-Ordering
        severity_order = {"INFO": 10, "WARN": 20, "WARNING": 20, "CRITICAL": 30}

        event_level = severity_order.get(event_severity.upper(), 0)
        target_level = severity_order.get(target_min_severity.upper(), 30)

        return event_level >= target_level


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def build_escalation_manager_from_config(
    config: Mapping[str, Any],
    environment: Optional[str] = None,
) -> EscalationManager:
    """
    Baut EscalationManager aus Config-Dict.

    Config-Struktur (TOML):
        [escalation]
        enabled = true
        enabled_environments = ["live"]
        provider = "null"  # oder "pagerduty_stub"
        critical_severities = ["CRITICAL"]

        [escalation.targets.primary]
        name = "Primary Risk On-Call"
        provider = "pagerduty_stub"
        routing_key = "..."
        min_severity = "CRITICAL"
        enabled = true

        [escalation.providers.pagerduty]
        api_url = "..."
        enable_real_calls = false

    Args:
        config: Config-Dict (z.B. aus TOML)
        environment: Aktuelles Environment (überschreibt config["environment"]["mode"])

    Returns:
        Konfigurierter EscalationManager
    """
    escalation_config = config.get("escalation", {})

    # Global deaktiviert?
    enabled = escalation_config.get("enabled", False)

    # Environment ermitteln
    if environment is None:
        env_config = config.get("environment", {})
        environment = env_config.get("mode", "paper")

    # Enabled Environments
    enabled_envs_raw = escalation_config.get("enabled_environments", ["live"])
    if isinstance(enabled_envs_raw, str):
        enabled_environments = {enabled_envs_raw}
    else:
        enabled_environments = set(enabled_envs_raw)

    # Critical Severities
    critical_sevs_raw = escalation_config.get("critical_severities", ["CRITICAL"])
    if isinstance(critical_sevs_raw, str):
        critical_severities = {critical_sevs_raw.upper()}
    else:
        critical_severities = {s.upper() for s in critical_sevs_raw}

    # Provider erstellen
    provider_name = escalation_config.get("provider", "null")
    provider_config = escalation_config.get("providers", {}).get(provider_name, {})
    provider = get_provider(provider_name, provider_config)

    # Targets erstellen
    targets: List[EscalationTarget] = []
    targets_config = escalation_config.get("targets", {})

    if targets_config:
        for target_id, target_data in targets_config.items():
            if isinstance(target_data, dict):
                target = EscalationTarget(
                    name=target_data.get("name", target_id),
                    provider=target_data.get("provider", provider_name),
                    routing_key=target_data.get("routing_key"),
                    min_severity=target_data.get("min_severity", "CRITICAL"),
                    enabled=target_data.get("enabled", True),
                )
                targets.append(target)
    else:
        # Default-Target wenn keine konfiguriert
        targets.append(
            EscalationTarget(
                name="default",
                provider=provider_name,
                min_severity="CRITICAL",
            )
        )

    logger.info(
        f"Escalation manager configured: enabled={enabled}, "
        f"environment={environment}, provider={provider_name}, "
        f"targets={len(targets)}"
    )

    return EscalationManager(
        provider=provider,
        targets=targets,
        enabled=enabled,
        enabled_environments=enabled_environments,
        critical_severities=critical_severities,
        current_environment=environment,
    )


