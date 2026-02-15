from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


def _now_iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_audit_event_v1(
    *,
    event: str,
    details: Dict[str, Any],
    audit_path: Optional[Path] = None,
) -> None:
    audit_path = audit_path or Path("out/ops/ai_policy/ai_model_policy_v1_audit.ndjson")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts_utc": _now_iso_utc(),
        "event": event,
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "details": details,
    }
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
