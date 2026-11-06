"""Local liveness evidence for existing runtime owners; no recovery authority."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .evidence_v1 import write_json

LOGGER = logging.getLogger(__name__)
EVENTS_FILENAME = "runtime_liveness_events_v1.jsonl"
LATEST_FILENAME = "runtime_liveness_latest_v1.json"


def record_runtime_notice_v1(
    *,
    evidence_root: Path,
    component: str,
    run_id: str,
    reason_code: str,
    action: str,
    owner_action_required: bool,
    extra: Mapping[str, Any] | None = None,
    notification_kind: str | None = None,
) -> dict[str, Any]:
    """Persist before continuing/stopping, and make required action visible in logs.

    This is a local evidence/log delivery, not an external notification receipt.
    Callers must not put credentials or arbitrary transport exception text here.
    """
    if notification_kind not in {None, "FAULT", "RECOVERED"}:
        raise ValueError("UNKNOWN_RUNTIME_NOTIFICATION_KIND")
    if notification_kind == "RECOVERED" and not (extra or {}).get("incident_id"):
        raise ValueError("RECOVERY_NOTIFICATION_REQUIRES_INCIDENT")
    payload = {
        "event_id": uuid4().hex,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "run_id": run_id,
        "reason_code": reason_code,
        "recovery_action": action,
        "owner_action_required": owner_action_required,
        "notification_kind": notification_kind,
        "post_allowed": False,
        "external_effect_authorized": False,
        "extra": dict(extra or {}),
    }
    root = Path(evidence_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
        with (root / EVENTS_FILENAME).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        write_json(root / LATEST_FILENAME, payload)
    except OSError:
        LOGGER.error(
            "Runtime notice persistence failed: component=%s reason=%s action=%s",
            component,
            reason_code,
            action,
        )
        raise
    log = LOGGER.error if owner_action_required else LOGGER.info
    log(
        "PeakTrade runtime: component=%s reason=%s action=%s evidence=%s",
        component,
        reason_code,
        action,
        root / LATEST_FILENAME,
    )
    return payload
