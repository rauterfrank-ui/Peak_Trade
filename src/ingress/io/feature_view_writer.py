"""
Write FeatureView to out/ops/views/ with SHA256 sidecar (Runbook A3).
Output is pointer-only; no raw payload in written JSON.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ingress.views.feature_view import FeatureView


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_feature_view(view: FeatureView, base_path: Path) -> tuple[Path, str]:
    """
    Write FeatureView as JSON; add .sha256 file with hex digest.
    Returns (path_to_json, sha256_hex).
    """
    base_path = Path(base_path)
    base_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = base_path.with_suffix(".json") if base_path.suffix != ".json" else base_path
    payload = json.dumps(view.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    json_path.write_text(payload, encoding="utf-8")
    digest = _sha256_hex(payload.encode("utf-8"))
    sha_path = json_path.with_suffix(json_path.suffix + ".sha256")
    sha_path.write_text(digest + "\n", encoding="utf-8")
    return (json_path, digest)
