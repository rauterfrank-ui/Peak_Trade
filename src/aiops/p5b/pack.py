from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _iter_files(paths: List[Path]) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend([x for x in p.rglob("*") if x.is_file()])
    out2 = sorted({x.resolve() for x in out}, key=lambda x: x.as_posix())
    return out2


def build_pack_entries(files: List[Path], base_dir: Path) -> List[Dict[str, Any]]:
    base = base_dir.resolve()
    entries: List[Dict[str, Any]] = []
    for f in files:
        try:
            rel = f.relative_to(base).as_posix()
        except ValueError:
            rel = f.name
        entries.append(
            {
                "relpath": rel,
                "bytes": f.stat().st_size,
                "sha256": sha256_file(f),
            }
        )
    return sorted(entries, key=lambda e: e["relpath"])


@dataclass(frozen=True)
class EvidencePackMeta:
    kind: str = "evidence_pack"
    schema_version: str = "p5b.evidence_pack.v0"
    pack_id: str = ""
    created_at_utc: str = ""
    base_dir: str = ""


def build_manifest(meta: EvidencePackMeta, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"meta": asdict(meta), "files": entries}
