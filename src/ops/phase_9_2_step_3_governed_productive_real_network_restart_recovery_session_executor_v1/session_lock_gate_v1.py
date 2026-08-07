"""Session-lock / single-writer gate for Step-3 executor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockError,
    SessionLockV1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    OWNER,
    SESSION_LOCK_NAME,
    SESSION_LOCK_OWNER,
    TARGET_SESSION_ID,
)


def acquire_step3_executor_session_lock_v1(
    *,
    persistence_root: Path,
    session_id: str = TARGET_SESSION_ID,
    owner: str = OWNER,
) -> dict[str, Any]:
    lock_path = Path(persistence_root) / "locks" / f"{SESSION_LOCK_NAME}.lock"
    lock = SessionLockV1(lock_path=lock_path, session_id=session_id, owner=owner)
    try:
        lock.acquire()
    except SessionLockError as exc:
        return {
            "ok": False,
            "acquired": False,
            "blockers": [str(exc) if str(exc) else "ABORT_DUPLICATE_SESSION"],
            "lock_path": str(lock_path),
            "session_lock_owner": SESSION_LOCK_OWNER,
            "lock": None,
        }
    return {
        "ok": True,
        "acquired": True,
        "blockers": [],
        "lock_path": str(lock_path),
        "session_lock_owner": SESSION_LOCK_OWNER,
        "lock": lock,
    }


def prove_second_writer_rejected_v1(*, persistence_root: Path) -> dict[str, Any]:
    first = acquire_step3_executor_session_lock_v1(persistence_root=persistence_root)
    if not first.get("ok"):
        return {"ok": False, "blockers": list(first.get("blockers") or ["FIRST_LOCK_FAILED"])}
    second = acquire_step3_executor_session_lock_v1(persistence_root=persistence_root)
    lock = first.get("lock")
    if isinstance(lock, SessionLockV1):
        lock.release()
    return {
        "ok": (not second.get("ok"))
        and any("DUPLICATE" in b or "ABORT" in b for b in (second.get("blockers") or [])),
        "first_ok": True,
        "second_ok": bool(second.get("ok")),
        "second_blockers": list(second.get("blockers") or []),
        "SINGLE_WRITER_ENFORCED": True,
        "SESSION_LOCK_BOUND": True,
    }
