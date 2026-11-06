"""Drain durable O6 fault/recovery notices through the existing email channel.

Run outside the trading loop. SMTP acceptance is not an operator read receipt;
an uncertain send can be retried and can duplicate an email after a crash.
"""

import asyncio
from datetime import datetime
from hashlib import sha256
import json
import logging
import os
import time
import math
from pathlib import Path
from uuid import UUID

from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)
from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity
from src.risk_layer.alerting.channels.email_channel import EmailChannel

from .constants_v1 import DEFAULT_BOUNDED_RETRY_LIMIT
from .evidence_v1 import write_json
from .runtime_notice_v1 import EVENTS_FILENAME

LOGGER = logging.getLogger(__name__)


def default_recovery_email_config_path_v1() -> Path:
    return Path.home() / ".config" / "peak_trade" / "runtime_recovery_email_v1.json"


def build_recovery_email_channel_v1(config_path: Path) -> EmailChannel:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    source = cfg.get("password_source", "environment")
    if source == "macos_keychain":
        from .email_keychain_v1 import MAIL_KEYCHAIN_SERVICE, read_mail_keychain_password_v1

        if cfg.get("keychain_service") != MAIL_KEYCHAIN_SERVICE:
            raise ValueError("MAIL_KEYCHAIN_SERVICE_UNPROVEN")
        password = read_mail_keychain_password_v1(cfg["smtp_user"])
    elif source == "environment":
        password = os.environ.get(cfg["password_env_var"], "")
    else:
        raise ValueError("UNKNOWN_MAIL_PASSWORD_SOURCE")
    # Password stays in mail-worker memory, outside source and evidence.
    return EmailChannel(
        {
            "enabled": cfg.get("enabled") is True,
            "smtp_host": cfg["smtp_host"],
            "smtp_port": cfg["smtp_port"],
            "smtp_user": cfg["smtp_user"],
            "smtp_password": password,
            "from_address": cfg["from_address"],
            "to_addresses": cfg["to_addresses"],
            "use_tls": True,
        },
        min_severity=AlertSeverity.INFO,
    )


def _digest(value: dict) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _read_notices(root: Path) -> dict[str, dict]:
    result = {}
    path = Path(root) / EVENTS_FILENAME
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("notification_kind") not in {"FAULT", "RECOVERED"}:
            continue
        identity = str(payload["event_id"])
        UUID(identity)  # IDs must never be usable as paths.
        if identity in result and result[identity] != payload:
            raise ValueError("RUNTIME_NOTICE_ID_CONTENT_CONFLICT")
        result[identity] = payload
    return result


def _as_email(payload: dict, notices: dict[str, dict]) -> AlertEvent:
    recovered = payload["notification_kind"] == "RECOVERED"
    context = payload.get("extra", {})
    if recovered:
        incident = notices.get(context.get("incident_id"))
        if not (
            incident
            and incident["notification_kind"] == "FAULT"
            and incident["component"] == payload["component"]
            and incident["run_id"] == payload["run_id"]
            and incident["observed_at_utc"] <= payload["observed_at_utc"]
        ):
            raise ValueError("RECOVERY_EMAIL_CAUSAL_INCIDENT_UNPROVEN")
    scope_key = context.get("recovery_scope", payload["component"])
    scope = {
        "FRESH_C1_DATA_PROCESSING": "laufende Marktdatenverarbeitung",
        "DASHBOARD_PROCESS_HEARTBEAT": "Dashboard-Prozess",
    }.get(scope_key, scope_key)
    message = (
        f"Wiederherstellung bestätigt: {scope} wurde erneut geprüft und ist wieder verfügbar."
        if recovered
        else f"Störung erkannt bei {scope}. {payload['recovery_action']}"
    )
    return AlertEvent(
        severity=AlertSeverity.INFO if recovered else AlertSeverity.CRITICAL,
        category=AlertCategory.SYSTEM_HEALTH,
        source=payload["component"],
        message=message,
        event_id=payload["event_id"],
        timestamp=datetime.fromisoformat(payload["observed_at_utc"]),
        context={
            "status": "Wiederherstellung bestätigt" if recovered else "Störung erkannt",
            "scope": scope,
            "run_id": payload["run_id"],
            "reason": payload["reason_code"],
            "incident_id": context.get("incident_id", payload["event_id"]),
        },
    )


async def process_runtime_recovery_emails_v1(
    *,
    evidence_root: Path,
    channel: EmailChannel,
    deliver: bool = False,
    retry_cooldown_seconds: float | None = None,
    now_fn=time.time,
) -> dict:
    """Each event gets at most one attempt per batch, three durable attempts total.

    Disabled/missing credentials and dry runs never mark anything as delivered.
    Notification failures cannot terminate the producer's processing loop.
    """
    if retry_cooldown_seconds is not None and (
        not math.isfinite(retry_cooldown_seconds) or retry_cooldown_seconds < 60
    ):
        raise ValueError("MAIL_RETRY_COOLDOWN_INVALID")
    notices = _read_notices(evidence_root)
    delivery_root = Path(evidence_root) / "runtime_recovery_email_delivery_v1"
    target = _digest({"from": channel.from_address, "to": channel.to_addresses})
    accepted, pending, exhausted, preview = [], [], [], []
    with LauncherSingleWriterV1(
        delivery_root, writer_identity="peak_trade.o6_runtime_recovery_mail_v1"
    ):
        for identity, payload in notices.items():
            event = _as_email(payload, notices)
            preview.append(event.to_dict())
            path = delivery_root / target / f"{identity}.json"
            content_digest = _digest(payload)
            state = {
                "event_id": identity,
                "content_digest": content_digest,
                "attempts": 0,
                "status": "PENDING",
            }
            if path.exists():
                state = json.loads(path.read_text(encoding="utf-8"))
                material = {k: v for k, v in state.items() if k != "integrity_digest"}
                if (
                    state.get("integrity_digest") != _digest(material)
                    or state.get("event_id") != identity
                    or state.get("status") not in {"PENDING", "IN_PROGRESS", "TRANSPORT_ACCEPTED"}
                    or state.get("content_digest") != content_digest
                    or type(state.get("attempts")) is not int
                    or not 0 <= state["attempts"] <= DEFAULT_BOUNDED_RETRY_LIMIT
                ):
                    raise ValueError("RUNTIME_EMAIL_DELIVERY_STATE_UNPROVEN")
            if state["status"] == "TRANSPORT_ACCEPTED":
                accepted.append(identity)
                continue
            if state["attempts"] >= DEFAULT_BOUNDED_RETRY_LIMIT:
                last_attempt = state.get("last_attempt_at")
                if (
                    deliver
                    and retry_cooldown_seconds is not None
                    and state.get("retryable") is True
                    and type(last_attempt) in (int, float)
                    and math.isfinite(last_attempt)
                    and now_fn() - last_attempt >= retry_cooldown_seconds
                ):
                    state["attempts"] = 0
                    state["retry_windows"] = state.get("retry_windows", 0) + 1
                else:
                    exhausted.append(identity)
                    continue
            if not deliver or not channel.should_send(event):
                pending.append(identity)
                continue
            state["attempts"] += 1
            state["total_attempts"] = state.get("total_attempts", state["attempts"] - 1) + 1
            state["last_attempt_at"] = now_fn()
            state["retryable"] = False  # An uncertain crash never renews a window.
            state["status"] = "IN_PROGRESS"
            state["integrity_digest"] = _digest(
                {k: v for k, v in state.items() if k != "integrity_digest"}
            )
            write_json(path, state)
            # Reuse the existing explicit bool-returning email transport. A null
            # channel or a log entry is never treated as successful delivery.
            succeeded = await channel.dispatch(event)
            state["retryable"] = channel.last_failure_retryable is True
            state["status"] = "TRANSPORT_ACCEPTED" if succeeded is True else "PENDING"
            state["integrity_digest"] = _digest(
                {k: v for k, v in state.items() if k != "integrity_digest"}
            )
            write_json(path, state)
            (accepted if succeeded is True else pending).append(identity)
    return {
        "transport_accepted": accepted,
        "pending": pending,
        "exhausted": exhausted,
        "preview": preview,
        "operator_read_receipt_proven": False,
        "channel_configured": channel.is_enabled(),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="O6 recovery mail queue; preview unless --deliver is explicit."
    )
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--config-path", type=Path, default=default_recovery_email_config_path_v1())
    parser.add_argument("--deliver", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(
        process_runtime_recovery_emails_v1(
            evidence_root=args.evidence_root,
            channel=build_recovery_email_channel_v1(args.config_path),
            deliver=args.deliver,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return (
        1
        if args.deliver
        and (not result["channel_configured"] or result["pending"] or result["exhausted"])
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
