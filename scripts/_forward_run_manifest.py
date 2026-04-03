# scripts/_forward_run_manifest.py
"""Kleine Hilfen für Forward-CLI Run-Manifeste (NO-LIVE, nur Metadaten).

Kurz: ``run_id`` = SHA-256 über script_name, argv, config_path, git_sha — siehe
``docs/ops/CLI_RUN_MANIFEST_RUN_ID.md``. ``generated_at_utc`` ist bewusst *nicht* Teil von ``run_id``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parent.parent


def compute_deterministic_run_id(
    *,
    script_name: str,
    argv: list[str],
    config_path: str,
    git_sha: str | None,
) -> str:
    """
    Stabile Run-ID (SHA-256-Hex) aus Script, CLI-Args, Config-Pfad und Git-HEAD.

    Gleiche Eingaben ergeben dieselbe ID; Änderungen an argv/config/git_sha ändern die ID.

    ``generated_at_utc`` (im Manifest gesetzt) fließt hier nicht ein — sonst wäre die ID
    pro Lauf neu und nicht als Eingabe-Fingerprint brauchbar.
    """
    blob = json.dumps(
        {
            "script_name": script_name,
            "argv": argv,
            "config_path": config_path,
            "git_sha": git_sha,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


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
