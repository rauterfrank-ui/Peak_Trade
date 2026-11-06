"""
Write EvidenceCapsule to out/ops/capsules/ (Runbook A4).
JSONL line or single JSON + .sha256 sidecar; no raw in output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ingress.capsules.evidence_capsule import EvidenceCapsule


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_evidence_capsule(capsule: EvidenceCapsule, json_path: Path) -> tuple[Path, str]:
    """
    Write capsule as JSON; add .sha256 file.
    Returns (path_to_json, sha256_hex).
    """
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        capsule.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    json_path.write_text(payload, encoding="utf-8")
    digest = _sha256_hex(payload.encode("utf-8"))
    sha_path = json_path.with_suffix(json_path.suffix + ".sha256")
    # shasum -c compatible: "<hex>  <relative_filename>"
    sha_path.write_text(f"{digest}  {json_path.name}\n", encoding="utf-8")
    return (json_path, digest)
