from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from src.infra.escalation.network_gate import ensure_may_use_network_escalation


class EscalationProvider(Protocol):
    def send(self, event: Dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class PagerDutyConfig:
    """allow_network=true is explicit risk acceptance. Retries/backoff small and deterministic; no infinite loops."""

    allow_network: bool = False
    endpoint: str = "https://events.pagerduty.com/v2/enqueue"
    timeout_seconds: float = 5.0
    max_retries: int = 2
    backoff_seconds: float = 1.0


def _load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import tomllib  # py311+

        return tomllib.loads(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        import tomli  # type: ignore

        return tomli.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class EscalationConfig:
    provider: str = "stub"  # stub|pagerduty
    outbox_path: str = "data/escalation/outbox.jsonl"  # for stub + debugging

    @staticmethod
    def from_toml(path: Path) -> "EscalationConfig":
        d = _load_toml(path)
        esc = d.get("escalation", d)
        return EscalationConfig(
            provider=str(esc.get("provider", "stub")),
            outbox_path=str(esc.get("outbox_path", "data/escalation/outbox.jsonl")),
        )


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


class StubProvider:
    """
    Default-safe provider: writes event to outbox JSONL (append-only).
    No network calls.
    """

    def __init__(self, *, outbox_path: Path) -> None:
        self.outbox_path = outbox_path

    def send(self, event: Dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", time.time())
        payload["provider"] = "stub"
        _append_jsonl(self.outbox_path, payload)


def _pagerduty_config_from_toml(path: Path) -> PagerDutyConfig:
    d = _load_toml(path)
    pd = d.get("pagerduty", {})
    return PagerDutyConfig(
        allow_network=bool(pd.get("allow_network", False)),
        endpoint=str(pd.get("endpoint", "https://events.pagerduty.com/v2/enqueue")),
        timeout_seconds=float(pd.get("timeout_seconds", 5.0)),
        max_retries=int(pd.get("max_retries", 2)),
        backoff_seconds=float(pd.get("backoff_seconds", 1.0)),
    )


class PagerDutyProvider:
    """
    Optional provider. Offline-first: by default writes envelope only (no network).
    When [pagerduty] allow_network=true, can POST to PagerDuty Events API v2.
    Contract: requires routing key; if missing -> fail fast.
    """

    def __init__(
        self,
        *,
        routing_key_env: str = "PAGERDUTY_ROUTING_KEY",
        pagerduty_config: Optional[PagerDutyConfig] = None,
        env_config: Optional[object] = None,
    ) -> None:
        self.routing_key_env = routing_key_env
        self.routing_key = os.getenv(routing_key_env)
        if not self.routing_key:
            raise RuntimeError(f"PagerDuty routing key missing: env {routing_key_env} not set")
        self._pd = pagerduty_config or PagerDutyConfig()
        self._env_config = env_config

    def send(self, event: Dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", time.time())
        payload["provider"] = "pagerduty"
        payload["routing_key_env"] = self.routing_key_env
        # NOTE: we do not include routing_key value in persisted envelopes.
        outbox = Path("data/escalation/pagerduty_envelopes.jsonl")
        envelope = {k: v for k, v in payload.items() if k != "routing_key"}
        _append_jsonl(outbox, envelope)

        ensure_may_use_network_escalation(
            allow_network=self._pd.allow_network,
            context="pagerduty",
            env_config=getattr(self, "_env_config", None),
        )
        if self._pd.allow_network:
            self._send_http(event)

    def _send_http(self, event: Dict[str, Any]) -> None:
        import urllib.request

        raw = (event.get("severity") or "critical").upper()
        severity = {
            "CRITICAL": "critical",
            "WARN": "warning",
            "WARNING": "warning",
            "INFO": "info",
        }.get(raw, raw.lower())
        body = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "dedup_key": f"peak_trade_{event.get('dedup_key', event.get('ts', time.time()))}",
            "payload": {
                "summary": event.get("summary", ""),
                "severity": severity,
                "source": event.get("source", "peak_trade"),
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(event.get("ts", time.time()))
                ),
                "custom_details": {
                    k: v
                    for k, v in event.items()
                    if k
                    not in ("summary", "severity", "source", "ts", "provider", "routing_key_env")
                },
            },
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self._pd.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=self._pd.timeout_seconds)


def build_provider(config_path: Path) -> EscalationProvider:
    cfg = EscalationConfig.from_toml(config_path)
    name = (cfg.provider or "stub").strip().lower()
    if name == "stub":
        return StubProvider(outbox_path=Path(cfg.outbox_path))
    if name == "pagerduty":
        pd_cfg = _pagerduty_config_from_toml(config_path)
        return PagerDutyProvider(pagerduty_config=pd_cfg)
    raise ValueError(f"Unknown escalation provider: {cfg.provider!r}")


# -----------------------------------------------------------------------------
# Legacy API (for EscalationManager / Phase 85): send(event, target)
# -----------------------------------------------------------------------------


def _event_target_to_dict(event: Any, target: Any) -> Dict[str, Any]:
    """Convert legacy EscalationEvent + EscalationTarget to dict for outbox."""
    d: Dict[str, Any] = {}
    if hasattr(event, "to_dict") and callable(event.to_dict):
        d = dict(event.to_dict())
    elif isinstance(event, dict):
        d = dict(event)
    else:
        d = dict(getattr(event, "__dict__", {}))
    if hasattr(target, "to_dict") and callable(target.to_dict):
        d["target"] = target.to_dict()
    elif isinstance(target, dict):
        d["target"] = dict(target)
    else:
        d["target"] = dict(getattr(target, "__dict__", {}))
    return d


# Severity mapping for legacy PagerDuty-like payload
_LEGACY_SEVERITY_MAPPING = {
    "CRITICAL": "critical",
    "WARN": "warning",
    "WARNING": "warning",
    "INFO": "info",
}


class NullEscalationProvider:
    """Legacy: no-op provider for EscalationManager (send(event, target))."""

    def __init__(self, log_would_escalate: bool = True) -> None:
        self._log_would_escalate = log_would_escalate
        self._logger = logging.getLogger(f"{__name__}.NullEscalationProvider")

    @property
    def name(self) -> str:
        return "null"

    def send(self, event: Any, target: Any) -> None:
        if self._log_would_escalate:
            summary = getattr(event, "summary", "")
            severity = getattr(event, "severity", "")
            target_name = getattr(target, "name", "")
            self._logger.info(
                f"[NULL-ESCALATION] Would escalate to '{target_name}': [{severity}] {summary}"
            )


def _legacy_build_pagerduty_payload(event: Any, target: Any) -> Dict[str, Any]:
    """Build PagerDuty Events API v2–style payload for legacy stub."""
    severity = _LEGACY_SEVERITY_MAPPING.get(getattr(event, "severity", "").upper(), "warning")
    details = getattr(event, "details", None) or {}
    custom_details = {
        "alert_id": getattr(event, "alert_id", ""),
        "alert_type": getattr(event, "alert_type", ""),
        "severity": getattr(event, "severity", ""),
        **details,
    }
    if getattr(event, "symbol", None):
        custom_details["symbol"] = event.symbol
    if getattr(event, "session_id", None):
        custom_details["session_id"] = event.session_id
    created_at = getattr(event, "created_at", None)
    timestamp = (
        created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or "")
    )
    return {
        "routing_key": getattr(target, "routing_key", None) or "default-routing-key",
        "event_action": "trigger",
        "dedup_key": f"peak_trade_{getattr(event, 'alert_id', '')}",
        "payload": {
            "summary": getattr(event, "summary", ""),
            "severity": severity,
            "source": f"peak_trade:{getattr(event, 'alert_type', '').lower()}",
            "timestamp": timestamp,
            "custom_details": custom_details,
        },
    }


class PagerDutyLikeProviderStub:
    """Legacy: stub provider for EscalationManager; stores payloads in sent_payloads (no network)."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        enable_real_calls: bool = False,
        outbox_path: Optional[Path] = None,
    ) -> None:
        self._api_url = api_url
        self._enable_real_calls = enable_real_calls
        self._outbox = outbox_path or Path("data/escalation/outbox.jsonl")
        self._logger = logging.getLogger(f"{__name__}.PagerDutyLikeProviderStub")
        self.sent_payloads: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "pagerduty_stub"

    def send(self, event: Any, target: Any) -> None:
        payload = _legacy_build_pagerduty_payload(event, target)
        self.sent_payloads.append(payload)
        if self._enable_real_calls and self._api_url:
            self._logger.warning(
                "[PAGERDUTY-STUB] Real calls enabled but not implemented in Phase 85"
            )

    def clear_sent_payloads(self) -> None:
        self.sent_payloads.clear()


def get_provider(provider_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """Legacy factory for EscalationManager. Prefer build_provider(config_path) for new code."""
    config = config or {}
    name = (provider_name or "null").strip().lower()
    if name == "null":
        return NullEscalationProvider(log_would_escalate=config.get("log_would_escalate", True))
    if name in ("pagerduty_stub", "pagerduty"):
        outbox = config.get("outbox_path")
        return PagerDutyLikeProviderStub(outbox_path=Path(outbox) if outbox else None)
    return NullEscalationProvider()
