"""Atomic single-file write: temp + fsync + os.replace (+ best-effort dir fsync)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class AtomicWriteErrorV1(OSError):
    """Atomic write failed after validation."""


def atomic_write_text_v1(*, destination: Path, body: str) -> None:
    """Write ``body`` atomically into ``destination``.

    - Creates parent directories when missing (authorized write path only).
    - Temp file is created in the destination directory.
    - On failure, best-effort temp cleanup is performed.
    - No transactional multi-file rollback is claimed.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd: int | None = None
    tmp_name: str | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=destination.name + ".",
            dir=str(destination.parent),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = None  # ownership transferred to fdopen
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, destination)
        tmp_name = None
        try:
            dir_fd = os.open(str(destination.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            # Directory fsync is best-effort / platform-dependent.
            pass
    except OSError as exc:
        raise AtomicWriteErrorV1(str(exc)) from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp_name is not None and os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
