"""Durable O5 derived read-model store (atomic load/commit).

Authority effect remains NONE / DERIVED. Does not recompute bars.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    READ_MODEL_RELATIVE_PATH,
    READ_MODEL_SCHEMA_NAME,
)


def durable_read_model_path_v1(state_root: Path) -> Path:
    return Path(state_root) / READ_MODEL_RELATIVE_PATH


def load_durable_read_model_v1(state_root: Path) -> Optional[dict[str, Any]]:
    path = durable_read_model_path_v1(state_root)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("DURABLE_READ_MODEL_NOT_OBJECT")
    if str(raw.get("schema_name") or "") != READ_MODEL_SCHEMA_NAME:
        raise ValueError("DURABLE_READ_MODEL_SCHEMA_MISMATCH")
    return raw


def commit_durable_read_model_v1(
    state_root: Path,
    read_model: Mapping[str, Any],
    *,
    commit_time_unix: Optional[float] = None,
) -> dict[str, Any]:
    """Atomically persist the derived read model and stamp commit provenance."""
    if str(read_model.get("schema_name") or "") != READ_MODEL_SCHEMA_NAME:
        raise ValueError("DURABLE_READ_MODEL_SCHEMA_MISMATCH")
    if read_model.get("trading_authority") or read_model.get("orders"):
        raise ValueError("DASHBOARD_TRADING_AUTHORITY_FORBIDDEN")
    now = float(time.time() if commit_time_unix is None else commit_time_unix)
    payload = dict(read_model)
    payload["read_model_commit_time_unix"] = now
    payload["durable"] = True
    payload["relative_path"] = READ_MODEL_RELATIVE_PATH

    path = durable_read_model_path_v1(state_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return payload
