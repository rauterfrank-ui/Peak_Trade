# src/infra/escalation/providers.py
"""
Peak_Trade: Escalation Providers (Phase 85)
============================================

Provider-Implementierungen für Eskalations-Dienste.

Phase 85: Nur Stubs, keine echten API-Calls by default.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from .models import EscalationEvent, EscalationTarget

logger = logging.getLogger(__name__)


# =============================================================================
# PROVIDER PROTOCOL
# =============================================================================


class EscalationProvider(Protocol):
    """
    Protocol für Escalation-Provider.

    Jeder Provider muss send() implementieren.
    """

    @property
    def name(self) -> str:
        """Name des Providers."""
        ...

    def send(self, event: EscalationEvent, target: EscalationTarget) -> None:
        """
        Sendet eine Eskalation.

        Args:
            event: EscalationEvent zum Senden
            target: EscalationTarget mit Routing-Informationen

        Raises:
            Exception: Bei Fehlern (wird vom Manager gefangen)
        """
        ...


# =============================================================================
# NULL PROVIDER (No-Op)
# =============================================================================


class NullEscalationProvider:
    """
    Null-Provider der keine Eskalationen sendet.

    Verwendet wenn Eskalation deaktiviert ist oder in nicht-live Umgebungen.
    Loggt optional, dass eine Eskalation "gesendet" worden wäre.
    """

    def __init__(self, log_would_escalate: bool = True) -> None:
        """
        Initialisiert NullEscalationProvider.

        Args:
            log_would_escalate: Ob geloggt werden soll, dass eskaliert worden wäre
        """
        self._log_would_escalate = log_would_escalate
        self._logger = logging.getLogger(f"{__name__}.NullEscalationProvider")

    @property
    def name(self) -> str:
        return "null"

    def send(self, event: EscalationEvent, target: EscalationTarget) -> None:
        """
        Tut nichts, loggt aber optional.

        Args:
            event: EscalationEvent (wird ignoriert)
            target: EscalationTarget (wird ignoriert)
        """
        if self._log_would_escalate:
            self._logger.info(
                f"[NULL-ESCALATION] Would escalate to '{target.name}': "
                f"[{event.severity}] {event.summary}"
            )


# =============================================================================
# PAGERDUTY-LIKE STUB PROVIDER
# =============================================================================


class PagerDutyLikeProviderStub:
    """
    Stub-Provider für PagerDuty-ähnliche APIs.

    Phase 85: Sendet KEINE echten API-Calls.
    Baut den Payload auf und speichert ihn für Tests / Logging.

    Für echte API-Calls in späteren Phasen:
    - enable_real_calls muss True sein
    - Environment muss "live" sein
    - api_url muss gesetzt sein

    Attributes:
        sent_payloads: Liste aller "gesendeten" Payloads (für Tests)
    """

    # Severity-Mapping für PagerDuty-API
    SEVERITY_MAPPING = {
        "CRITICAL": "critical",
        "WARN": "warning",
        "WARNING": "warning",
        "INFO": "info",
    }

    def __init__(
        self,
        api_url: Optional[str] = None,
        enable_real_calls: bool = False,
    ) -> None:
        """
        Initialisiert PagerDutyLikeProviderStub.

        Args:
            api_url: PagerDuty Events API URL (für echte Calls)
            enable_real_calls: Ob echte HTTP-Calls gemacht werden sollen
        """
        self._api_url = api_url
        self._enable_real_calls = enable_real_calls
        self._logger = logging.getLogger(f"{__name__}.PagerDutyLikeProviderStub")

        # Für Tests: Speichert alle "gesendeten" Payloads
        self.sent_payloads: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "pagerduty_stub"

    def send(self, event: EscalationEvent, target: EscalationTarget) -> None:
        """
        Baut PagerDuty-Payload und "sendet" ihn.

        In Phase 85: Kein echter API-Call, nur Payload speichern + loggen.

        Args:
            event: EscalationEvent zum Senden
            target: EscalationTarget mit Routing-Key
        """
        payload = self._build_payload(event, target)
        self.sent_payloads.append(payload)

        self._logger.info(
            f"[PAGERDUTY-STUB] Would send to '{target.name}': "
            f"[{event.severity}] {event.summary}"
        )
        self._logger.debug(f"[PAGERDUTY-STUB] Payload: {json.dumps(payload, indent=2)}")

        # Phase 85: Keine echten Calls
        if self._enable_real_calls and self._api_url:
            self._logger.warning(
                "[PAGERDUTY-STUB] Real calls enabled but not implemented in Phase 85"
            )
            # Hier würde in späteren Phasen der echte HTTP-Call erfolgen
            # self._send_http(payload)

    def _build_payload(
        self, event: EscalationEvent, target: EscalationTarget
    ) -> Dict[str, Any]:
        """
        Baut PagerDuty Events API v2 kompatiblen Payload.

        Args:
            event: EscalationEvent
            target: EscalationTarget

        Returns:
            Dict für PagerDuty Events API
        """
        severity = self.SEVERITY_MAPPING.get(event.severity.upper(), "warning")

        payload = {
            "routing_key": target.routing_key or "default-routing-key",
            "event_action": "trigger",
            "dedup_key": f"peak_trade_{event.alert_id}",
            "payload": {
                "summary": event.summary,
                "severity": severity,
                "source": f"peak_trade:{event.alert_type.lower()}",
                "timestamp": event.created_at.isoformat(),
                "custom_details": {
                    "alert_id": event.alert_id,
                    "alert_type": event.alert_type,
                    "severity": event.severity,
                    **(event.details or {}),
                },
            },
        }

        # Optionale Felder
        if event.symbol:
            payload["payload"]["custom_details"]["symbol"] = event.symbol
        if event.session_id:
            payload["payload"]["custom_details"]["session_id"] = event.session_id

        return payload

    def clear_sent_payloads(self) -> None:
        """Leert die Liste gesendeter Payloads (für Tests)."""
        self.sent_payloads.clear()


# =============================================================================
# PROVIDER FACTORY
# =============================================================================


def get_provider(provider_name: str, config: Optional[Dict[str, Any]] = None) -> EscalationProvider:
    """
    Factory-Funktion für Escalation-Provider.

    Args:
        provider_name: Name des Providers ("null", "pagerduty_stub")
        config: Optionale Provider-spezifische Konfiguration

    Returns:
        EscalationProvider-Instanz
    """
    config = config or {}

    if provider_name == "null":
        return NullEscalationProvider(
            log_would_escalate=config.get("log_would_escalate", True)
        )
    elif provider_name in ("pagerduty_stub", "pagerduty"):
        return PagerDutyLikeProviderStub(
            api_url=config.get("api_url"),
            enable_real_calls=config.get("enable_real_calls", False),
        )
    else:
        logger.warning(f"Unknown escalation provider '{provider_name}', using null")
        return NullEscalationProvider()



