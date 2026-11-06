"""Reclaim a dead local process's lock, retaining its original bytes.

Only for state roots on this host. All acquiring writers must use the guard;
an unreadable lock, unknown identity or possibly live PID remains blocked.
"""

import fcntl
import json
import os
from pathlib import Path
import uuid
from typing import Mapping, Any, Callable


def acquire_exclusive_local_writer_lock_v1(
    path: Path,
    *,
    writer_identity: str,
    payload: Mapping[str, Any],
    dead_owner_validator: Callable[[Mapping[str, Any]], bool] | None = None,
) -> None:
    guard = os.open(str(path) + ".recovery_guard", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise FileExistsError("writer acquisition in progress") from exc
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                existing = {}
            pid = existing.get("pid") if isinstance(existing, dict) else None
            if (
                not isinstance(existing, dict)
                or existing.get("writer_identity") != writer_identity
                or type(pid) is not int
                or pid <= 0
            ):
                raise FileExistsError("unproven lock owner")
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                if dead_owner_validator is not None and dead_owner_validator(existing) is not True:
                    raise FileExistsError("dead owner checkpoint is unproven")
                # The guard serializes competing reclaimers. Preserve the old
                # receipt before claiming a new exclusive lock; never use age/TTL.
                path.rename(path.with_name(path.name + ".dead_process." + uuid.uuid4().hex))
            except PermissionError as exc:
                raise FileExistsError("lock owner may be alive") from exc
            else:
                raise FileExistsError("lock owner is alive")
        # Publish a complete receipt atomically without replacing any existing
        # lock. A process death cannot leave an empty canonical lock behind.
        staged = path.with_name(path.name + ".acquiring." + uuid.uuid4().hex)
        try:
            fd = os.open(str(staged), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(dict(payload), sort_keys=True, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.link(staged, path)
        finally:
            staged.unlink(missing_ok=True)
    finally:
        os.close(guard)
