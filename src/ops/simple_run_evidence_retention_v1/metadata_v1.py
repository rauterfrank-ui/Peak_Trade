"""Best-effort extraction from RUN_METADATA.json and sibling files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def read_run_metadata(run_root: Path) -> dict[str, Any]:
    return _load_json(run_root / "RUN_METADATA.json") or {}


def read_retention_sidecar(run_root: Path) -> dict[str, Any]:
    return _load_json(run_root / "RETENTION.json") or {}


def pick_code_sha(metadata: dict[str, Any], run_root: Path) -> str | None:
    for key in ("head", "code_sha", "git_sha", "repo_head", "CODE_SHA"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    git_state = run_root / "git_state.txt"
    if git_state.is_file():
        for line in git_state.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("HEAD="):
                return line.split("=", 1)[1].strip() or None
            if len(line) == 40 and all(c in "0123456789abcdef" for c in line.lower()):
                return line
    return None


def pick_config_ref(metadata: dict[str, Any]) -> str | None:
    for key in ("config_digest", "config_ref", "config_path", "schema", "stage"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def pick_instrument(metadata: dict[str, Any]) -> str | None:
    for key in ("instrument", "symbol", "future", "instrument_id", "scope_instrument"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def pick_venue(metadata: dict[str, Any]) -> str | None:
    for key in ("venue", "exchange", "execution_environment", "execution_venue"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def pick_times(metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    start = metadata.get("utc_start") or metadata.get("started_at")
    end = metadata.get("utc_end") or metadata.get("finished_at")
    start_s = start if isinstance(start, str) and start.strip() else None
    end_s = end if isinstance(end, str) and end.strip() else None
    return start_s, end_s


def pick_termination_reason(metadata: dict[str, Any]) -> str | None:
    for key in ("termination_reason", "stop_reason", "abort_reason", "failure_reason"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    verdict = metadata.get("verdict") or metadata.get("review_verdict")
    if isinstance(verdict, str) and verdict.strip().upper() not in ("PASS", "SUCCESS", "COMPLETE"):
        return f"verdict={verdict.strip()}"
    rc = metadata.get("adapter_rc")
    if isinstance(rc, int) and rc != 0:
        return f"adapter_rc={rc}"
    return None
