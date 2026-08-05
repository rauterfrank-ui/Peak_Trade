"""PRE→POST new-process continuity marker (no same-process resume)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    PRE_PROCESS_MARKER_FILENAME,
    RESTART_CAMPAIGN_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.digest_v1 import (
    read_json_v1,
    write_json_atomic_v1,
)


def marker_path_v1(persistence_root: Path) -> Path:
    return Path(persistence_root) / PRE_PROCESS_MARKER_FILENAME


def write_pre_process_marker_v1(
    *,
    persistence_root: Path,
    restart_campaign_id: str = RESTART_CAMPAIGN_ID,
    session_id: str = TARGET_SESSION_ID,
    pre_authorization_id: str,
    pre_terminal_manifest_digest: str | None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "phase_9_2_pre_restart_process_marker.v1",
        "session_id": session_id,
        "restart_campaign_id": restart_campaign_id,
        "pre_authorization_id": pre_authorization_id,
        "pre_terminal_manifest_digest": pre_terminal_manifest_digest,
        "pre_process_pid": int(os.getpid()),
        "same_session_resume_allowed": False,
        "post_restart_new_process_required": True,
    }
    write_json_atomic_v1(marker_path_v1(persistence_root), payload)
    return payload


def assert_post_is_new_process_v1(
    *,
    persistence_root: Path,
    restart_campaign_id: str = RESTART_CAMPAIGN_ID,
    session_id: str = TARGET_SESSION_ID,
) -> list[str]:
    path = marker_path_v1(persistence_root)
    if not path.is_file():
        return ["PRE_PROCESS_MARKER_MISSING"]
    raw = read_json_v1(path)
    blockers: list[str] = []
    if str(raw.get("session_id") or "") != session_id:
        blockers.append("PRE_PROCESS_MARKER_SESSION_MISMATCH")
    if str(raw.get("restart_campaign_id") or "") != restart_campaign_id:
        blockers.append("PRE_PROCESS_MARKER_CAMPAIGN_MISMATCH")
    pre_pid = int(raw.get("pre_process_pid") or -1)
    if pre_pid == int(os.getpid()):
        blockers.append("POST_RESTART_SAME_PROCESS_FORBIDDEN")
    if bool(raw.get("same_session_resume_allowed")):
        blockers.append("SAME_SESSION_RESUME_MUST_REMAIN_FALSE")
    return sorted(set(blockers))


def load_pre_authorization_id_v1(persistence_root: Path) -> str | None:
    path = marker_path_v1(persistence_root)
    if not path.is_file():
        return None
    raw = read_json_v1(path)
    value = raw.get("pre_authorization_id")
    return None if value is None else str(value)
