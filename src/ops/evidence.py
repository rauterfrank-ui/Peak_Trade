"""
Evidence Pack Layout für Research/Backtest-Runs (Phase B).

Standardisiertes Verzeichnislayout pro run_id:
- meta.json (Run-Metadaten: git sha, python, platform, sandbox, run params)
- env/, logs/, reports/, plots/, results/ (Unterverzeichnisse für Artifacts)

Usage:
    from src.ops.evidence import ensure_evidence_dirs, write_meta, EVIDENCE_LAYOUT

    base_dir = Path("artifacts/research") / run_id
    dirs = ensure_evidence_dirs(base_dir)
    write_meta(dirs["meta.json"], extra={"command": "sweep", "run_id": run_id})
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

EVIDENCE_LAYOUT = [
    "meta.json",
    "env",
    "logs",
    "reports",
    "plots",
    "results",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cmd_out(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    except Exception as e:
        return f"<error: {e}>"


def ensure_evidence_dirs(base_dir: Path) -> Dict[str, Path]:
    """Erstellt base_dir und alle EVIDENCE_LAYOUT-Einträge (Dateien/Verzeichnisse)."""
    base_dir.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Path] = {}
    for name in EVIDENCE_LAYOUT:
        p = base_dir / name
        if name.endswith(".json"):
            out[name] = p
        else:
            p.mkdir(parents=True, exist_ok=True)
            out[name] = p
    return out


def write_meta(meta_path: Path, extra: Optional[Dict[str, Any]] = None) -> None:
    """Schreibt meta.json mit Umgebungs- und optionalen Zusatzfeldern."""
    extra = extra or {}
    meta = {
        "created_utc": _utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "git_sha": _cmd_out(["git", "rev-parse", "--short", "HEAD"]),
        "git_status_porcelain": _cmd_out(["git", "status", "--porcelain"]),
        "env": {
            "PEAKTRADE_SANDBOX": os.getenv("PEAKTRADE_SANDBOX"),
        },
        **extra,
    }
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
