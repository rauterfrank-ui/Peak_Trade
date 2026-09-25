from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.aiops.p5b.pack import sha256_file


class EvidencePackValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise EvidencePackValidationError("manifest must be a JSON object")
    return obj


def validate_manifest_structure(m: Dict[str, Any]) -> None:
    meta = m.get("meta")
    files = m.get("files")
    if not isinstance(meta, dict):
        raise EvidencePackValidationError("meta must be dict")
    if meta.get("kind") != "evidence_pack":
        raise EvidencePackValidationError(
            f"meta.kind must be 'evidence_pack', got {meta.get('kind')!r}"
        )
    if not isinstance(meta.get("schema_version", ""), str) or not meta.get("schema_version"):
        raise EvidencePackValidationError("meta.schema_version missing")
    if not isinstance(meta.get("pack_id", ""), str) or not meta.get("pack_id"):
        raise EvidencePackValidationError("meta.pack_id missing")
    if not isinstance(files, list) or not files:
        raise EvidencePackValidationError("files must be a non-empty list")
    for e in files:
        if not isinstance(e, dict):
            raise EvidencePackValidationError("file entry must be dict")
        for k in ("relpath", "bytes", "sha256"):
            if k not in e:
                raise EvidencePackValidationError(f"file entry missing {k}")
        if not isinstance(e["relpath"], str) or not e["relpath"]:
            raise EvidencePackValidationError("relpath must be str")
        if not isinstance(e["bytes"], int) or e["bytes"] < 0:
            raise EvidencePackValidationError("bytes must be non-negative int")
        if not isinstance(e["sha256"], str) or len(e["sha256"]) != 64:
            raise EvidencePackValidationError("sha256 must be 64-hex string")


def verify_files(m: Dict[str, Any], base_dir: Path) -> None:
    for e in m["files"]:
        fp = base_dir / e["relpath"]
        if not fp.is_file():
            raise EvidencePackValidationError(f"missing file: {fp}")
        if fp.stat().st_size != e["bytes"]:
            raise EvidencePackValidationError(f"size mismatch: {fp}")
        got = sha256_file(fp)
        if got != e["sha256"]:
            raise EvidencePackValidationError(f"sha256 mismatch: {fp}")


def validate_pack(manifest_path: Path) -> None:
    m = load_json(manifest_path)
    validate_manifest_structure(m)
    meta = m["meta"]
    base_dir_s = str(meta.get("base_dir", "") or "").strip()
    if not base_dir_s:
        base_dir = manifest_path.parent.parent.resolve()
    elif base_dir_s.startswith("/") or (len(base_dir_s) > 1 and base_dir_s[1] == ":"):
        base_dir = Path(base_dir_s).expanduser().resolve()
    else:
        base_dir = (manifest_path.parent / base_dir_s).resolve()
    verify_files(m, base_dir=base_dir)
