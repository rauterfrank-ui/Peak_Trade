"""GHV reference manifest v1 — digests and semantic checkpoints only (AUTHORITY=NONE).

Binds GHV-referenced integration work to forensic evidence under
``evidence/research/ghv_referenced_full_system_natural_enter_pre_external_proof_v3/``.
Does not load GHV values into productive runtime configuration.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1"
GHV_AUTHORITY: Final[str] = "NONE"
DEFAULT_GHV_REFERENCE_ROOT: Final[str] = (
    "evidence/research/ghv_referenced_full_system_natural_enter_pre_external_proof_v3/"
    "20261006T182600Z"
)
DEFAULT_BOUNDED_RUN_SUBDIR: Final[str] = "bounded_run_post_merge_t2_causal_reproof_001"
MANIFEST_CONFIG_REL: Final[str] = (
    "config/governance/"
    "ghv_referenced_complete_intelligence_superstructure_integration_v1_ghv_reference_manifest_v1.json"
)

_ARTIFACT_REL_PATHS: Final[tuple[str, ...]] = (
    f"{DEFAULT_BOUNDED_RUN_SUBDIR}/PRE_EXTERNAL_CONVERGENCE_REPORT.json",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[2]


def ghv_reference_root_path_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or repo_root_v1()
    return root / DEFAULT_GHV_REFERENCE_ROOT


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_ghv_reference_manifest_config_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or repo_root_v1()
    path = root / MANIFEST_CONFIG_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GHV_MANIFEST_CONFIG_NOT_OBJECT")
    return payload


def prove_ghv_reference_artifacts_v1(
    *, repo_root: Path | None = None
) -> MappingProxyType[str, Any]:
    """Verify referenced GHV evidence files exist and return content digests."""
    root = repo_root or repo_root_v1()
    ref_root = ghv_reference_root_path_v1(repo_root=root)
    artifacts: dict[str, Any] = {}
    missing: list[str] = []
    for rel in _ARTIFACT_REL_PATHS:
        path = ref_root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        artifacts[rel] = {
            "sha256": _sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
    ok = not missing
    body = {
        "schema_version": SCHEMA_VERSION,
        "ghv_authority": GHV_AUTHORITY,
        "ghv_reference_root": DEFAULT_GHV_REFERENCE_ROOT,
        "bounded_run_subdir": DEFAULT_BOUNDED_RUN_SUBDIR,
        "artifacts_ok": ok,
        "missing_artifacts": tuple(missing),
        "artifact_digests": artifacts,
    }
    body["manifest_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def ghv_semantic_checkpoints_v1(*, repo_root: Path | None = None) -> MappingProxyType[str, Any]:
    """Read-only semantic checkpoints from GHV PRE_EXTERNAL report (reference only)."""
    root = repo_root or repo_root_v1()
    report_path = (
        ghv_reference_root_path_v1(repo_root=root)
        / DEFAULT_BOUNDED_RUN_SUBDIR
        / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    )
    if not report_path.is_file():
        return MappingProxyType(
            {
                "ok": False,
                "reason": "GHV_REPORT_MISSING",
                "ghv_authority": GHV_AUTHORITY,
            }
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    checkpoints = {
        "GENUINE_NATURAL_ENTER": str(report.get("NATURAL_ENTER_OBSERVED", "")).lower() == "true",
        "PRE_EXTERNAL_REACHED": str(report.get("PRE_EXTERNAL_REACHED", "")).lower() == "true",
        "POST_COUNT_ZERO": int(report.get("POST_COUNT", -1)) == 0,
        "EXTERNAL_EFFECT_COUNT_ZERO": int(report.get("EXTERNAL_EFFECT_COUNT", -1)) == 0,
        "REFERENCE_INSTRUMENT": str(report.get("NATIVE_ID") or ""),
        "BASELINE_SHA_IN_REPORT": str(report.get("BASELINE_SHA") or ""),
    }
    digest = compute_content_sha256(checkpoints)
    if not is_valid_sha256_hex(digest):
        raise ValueError("GHV_CHECKPOINT_DIGEST_INVALID")
    return MappingProxyType(
        {
            "ok": True,
            "ghv_authority": GHV_AUTHORITY,
            "checkpoints": checkpoints,
            "checkpoint_digest": digest,
            "report_path": str(report_path.relative_to(root)),
        }
    )


__all__ = [
    "DEFAULT_BOUNDED_RUN_SUBDIR",
    "DEFAULT_GHV_REFERENCE_ROOT",
    "GHV_AUTHORITY",
    "MANIFEST_CONFIG_REL",
    "SCHEMA_VERSION",
    "ghv_reference_root_path_v1",
    "ghv_semantic_checkpoints_v1",
    "load_ghv_reference_manifest_config_v1",
    "prove_ghv_reference_artifacts_v1",
    "repo_root_v1",
]
