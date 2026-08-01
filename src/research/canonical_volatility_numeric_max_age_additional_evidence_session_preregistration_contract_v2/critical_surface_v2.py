"""Versioned critical-surface manifest and content digest for contract v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
    CRITICAL_SURFACE_PATHS,
    REPOSITORY_BINDING_MODE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.git_binding_v2 import (
    read_blob_at_sha_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
    sha256_hex,
    sha256_hex_bytes,
)

CRITICAL_SURFACE_MANIFEST_SCHEMA_NAME = (
    "canonical_volatility_numeric_max_age_additional_evidence_critical_surface_manifest"
)
CRITICAL_SURFACE_MANIFEST_SCHEMA_VERSION = "v2"


def build_critical_surface_manifest_v2(
    *,
    paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    ordered = tuple(paths) if paths is not None else CRITICAL_SURFACE_PATHS
    if tuple(ordered) != tuple(sorted(ordered)):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_paths_must_be_sorted"
        )
    if len(ordered) != len(set(ordered)):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_paths_not_unique"
        )
    return {
        "schema_name": CRITICAL_SURFACE_MANIFEST_SCHEMA_NAME,
        "schema_version": CRITICAL_SURFACE_MANIFEST_SCHEMA_VERSION,
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "paths": list(ordered),
    }


def render_critical_surface_manifest_bytes_v2(
    *,
    paths: Sequence[str] | None = None,
) -> bytes:
    payload = build_critical_surface_manifest_v2(paths=paths)
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _resolve_path_hashes(
    *,
    repo_root: Path,
    paths: Sequence[str],
    at_sha: str | None,
    path_content_overrides: Mapping[str, bytes] | None,
) -> dict[str, str]:
    root = Path(repo_root)
    out: dict[str, str] = {}
    for rel in paths:
        if path_content_overrides is not None and rel in path_content_overrides:
            out[rel] = sha256_hex_bytes(path_content_overrides[rel])
            continue
        if at_sha is not None:
            out[rel] = sha256_hex_bytes(
                read_blob_at_sha_v2(sha=at_sha, relative_path=rel, repo_root=root)
            )
            continue
        path = root / rel
        if not path.is_file():
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                f"critical_surface_path_missing:{rel}"
            )
        out[rel] = sha256_hex_bytes(path.read_bytes())
    return out


def compute_critical_surface_manifest_digest_v2(
    *,
    repo_root: Path,
    paths: Sequence[str] | None = None,
    at_sha: str | None = None,
    path_content_overrides: Mapping[str, bytes] | None = None,
) -> str:
    """Canonical digest over sorted path→content-sha256 map."""
    ordered = tuple(paths) if paths is not None else CRITICAL_SURFACE_PATHS
    hashes = _resolve_path_hashes(
        repo_root=repo_root,
        paths=ordered,
        at_sha=at_sha,
        path_content_overrides=path_content_overrides,
    )
    material = {
        "content_sha256_by_path": {k: hashes[k] for k in ordered},
        "paths": list(ordered),
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "schema_name": CRITICAL_SURFACE_MANIFEST_SCHEMA_NAME,
        "schema_version": CRITICAL_SURFACE_MANIFEST_SCHEMA_VERSION,
    }
    return sha256_hex(material)


def assert_critical_surface_digest_match_v2(
    *,
    expected_digest: str,
    repo_root: Path,
    at_sha: str | None = None,
    paths: Sequence[str] | None = None,
    path_content_overrides: Mapping[str, bytes] | None = None,
) -> str:
    actual = compute_critical_surface_manifest_digest_v2(
        repo_root=repo_root,
        paths=paths,
        at_sha=at_sha,
        path_content_overrides=path_content_overrides,
    )
    if not isinstance(expected_digest, str) or not expected_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_manifest_digest_required"
        )
    if actual != expected_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_manifest_digest_mismatch"
        )
    return actual


def verify_critical_surface_manifest_artifact_v2(
    *,
    repo_root: Path,
    artifact_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    path = artifact_path or (root / CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH)
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_critical_surface_manifest_v2()
    if payload != expected:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_manifest_artifact_drift"
        )
    return payload
