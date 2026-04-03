# scripts/_forward_run_manifest.py
"""Kleine Hilfen für Forward-CLI Run-Manifeste (NO-LIVE, nur Metadaten)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parent.parent


def try_git_sha() -> str | None:
    """Liefert HEAD-SHA wenn ``git`` erreichbar, sonst ``None``."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except OSError:
        pass
    return None


def write_forward_run_manifest(path: Path, data: Mapping[str, Any]) -> None:
    """Schreibt JSON-Manifest; setzt ``generated_at_utc`` falls nicht gesetzt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload.setdefault(
        "generated_at_utc",
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def python_version_short() -> str:
    return sys.version.split()[0]
