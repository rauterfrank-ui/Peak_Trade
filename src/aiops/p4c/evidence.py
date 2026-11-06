from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(
    files: Iterable[Path], meta: Dict[str, Any], base_dir: Optional[Path] = None
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for p in sorted([Path(x) for x in files], key=lambda x: x.name):
        if base_dir and p.exists():
            try:
                relpath = p.relative_to(base_dir).as_posix()
            except ValueError:
                relpath = p.as_posix()
        else:
            relpath = p.as_posix()
        entries.append(
            {
                "name": p.name,
                "relpath": relpath,
                "bytes": p.stat().st_size if p.exists() else None,
                "sha256": sha256_file(p) if p.exists() else None,
            }
        )
    return {"meta": meta, "files": entries}
