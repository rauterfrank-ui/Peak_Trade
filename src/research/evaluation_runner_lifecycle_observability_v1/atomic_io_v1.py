"""Atomic JSON persistence helpers for runner lifecycle diagnostics."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping


def atomic_write_json_v1(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON via temp file + fsync + os.replace (crash-safe replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.stem}_",
        suffix=path.suffix or ".json",
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    finally:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass


def read_json_if_present_v1(path: Path) -> dict[str, Any] | None:
    path = Path(path)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
