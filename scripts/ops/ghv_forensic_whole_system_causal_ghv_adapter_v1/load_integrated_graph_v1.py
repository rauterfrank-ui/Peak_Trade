"""Load WP2-A output directory artifacts (read-only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.contracts_v1 import (
    INVALID_INPUT,
    WP2A_REQUIRED_ARTIFACTS,
)


@dataclass
class Wp2aArtifactBundleV1:
    wp2a_output_dir: Path
    integrated: dict[str, Any]
    manifest: dict[str, Any]
    gaps: dict[str, Any]
    overlay: dict[str, Any]
    artifact_sha256: dict[str, str] = field(default_factory=dict)


@dataclass
class Wp2aLoadResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    bundle: Wp2aArtifactBundleV1 | None = None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected_object:{path.name}")
    return raw


def load_wp2a_artifacts_v1(*, wp2a_output_dir: Path) -> Wp2aLoadResultV1:
    result = Wp2aLoadResultV1(ok=False)
    root = wp2a_output_dir.resolve()
    if not root.is_dir():
        result.failure_semantic = INVALID_INPUT
        result.errors.append(f"missing_wp2a_output_dir:{root}")
        return result

    missing = [name for name in WP2A_REQUIRED_ARTIFACTS if not (root / name).is_file()]
    if missing:
        result.failure_semantic = INVALID_INPUT
        result.errors.append(f"missing_required_artifacts:{','.join(missing)}")
        return result

    hashes: dict[str, str] = {}
    docs: dict[str, dict[str, Any]] = {}
    try:
        for name in WP2A_REQUIRED_ARTIFACTS:
            path = root / name
            hashes[name] = _sha256_file(path)
            docs[name] = _read_json_object(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result.failure_semantic = INVALID_INPUT
        result.errors.append(f"artifact_parse_error:{exc}")
        return result

    bundle = Wp2aArtifactBundleV1(
        wp2a_output_dir=root,
        integrated=docs["integrated_causal_graph.v1.json"],
        manifest=docs["causal_integration_manifest.v1.json"],
        gaps=docs["causal_coverage_gaps.v1.json"],
        overlay=docs["causal_overlay.v1.json"],
        artifact_sha256=hashes,
    )
    result.ok = True
    result.bundle = bundle
    return result
