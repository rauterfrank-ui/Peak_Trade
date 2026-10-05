"""Evidence artifact writer with SHA256 manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json_v1(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def hash_file_v1(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_evidence_manifest_v1(root: Path, files: list[str]) -> dict[str, Any]:
    entries = []
    for name in sorted(files):
        p = root / name
        if p.is_file():
            entries.append({"path": name, "sha256": hash_file_v1(p)})
    return {"AUTHORITY": "NONE", "ARTIFACTS": entries, "COUNT": len(entries)}
