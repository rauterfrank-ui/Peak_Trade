"""Domain reference contracts for integrated offline economic evidence v1."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    DOMAIN_SCHEMA_VERSION,
    ECONOMIC_METRICS_DOMAIN_SCHEMA_ID,
    ECONOMIC_METRICS_VERIFIER_ID,
    MONTE_CARLO_DOMAIN_SCHEMA_ID,
    MONTE_CARLO_VERIFIER_ID,
    STRESS_DOMAIN_SCHEMA_ID,
    STRESS_VERIFIER_ID,
    WALK_FORWARD_DOMAIN_SCHEMA_ID,
    WALK_FORWARD_VERIFIER_ID,
)

_RELPATH_FORBIDDEN = re.compile(r"(^|[\\/])\.\.([\\/]|$)")

REQUIRED_REFERENCE_FIELDS: tuple[str, ...] = (
    "schema_id",
    "schema_version",
    "authority_effect",
    "artifact_relpath",
    "artifact_digest_sha256",
    "producer_id",
    "verifier_id",
    "proven_source_sha",
    "implementation_surface_digest_sha256",
    "config_digest_sha256",
    "dataset_input_binding_digest_sha256",
)


@dataclass
class DomainVerificationResultV1:
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
        }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_resolve_under_repo(*, repo_root: Path, relpath: str) -> Path | None:
    rel = relpath.strip().replace("\\", "/")
    if not rel or rel.startswith("/") or _RELPATH_FORBIDDEN.search(rel):
        return None
    root = repo_root.resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def load_json_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if not path.is_file():
        return {}, ["ARTIFACT_MISSING"]
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, ["ARTIFACT_JSON_MALFORMED"]
    if not isinstance(loaded, dict):
        return {}, ["ARTIFACT_JSON_NOT_OBJECT"]
    return loaded, blockers


def validate_reference_binding_fields(
    ref: Mapping[str, Any],
    *,
    expected_schema_id: str,
    expected_verifier_id: str,
    prefix: str,
) -> list[str]:
    blockers: list[str] = []
    for key in REQUIRED_REFERENCE_FIELDS:
        if not str(ref.get(key) or "").strip():
            blockers.append(f"{prefix}{key.upper()}_MISSING")
    if ref.get("schema_id") != expected_schema_id:
        blockers.append(f"{prefix}SCHEMA_ID_MISMATCH")
    if ref.get("schema_version") != DOMAIN_SCHEMA_VERSION:
        blockers.append(f"{prefix}SCHEMA_VERSION_MISMATCH")
    if ref.get("authority_effect") != AUTHORITY_EFFECT_NONE:
        blockers.append(f"{prefix}AUTHORITY_EFFECT_NOT_NONE")
    if ref.get("verifier_id") != expected_verifier_id:
        blockers.append(f"{prefix}VERIFIER_ID_MISMATCH")
    proven = str(ref.get("proven_source_sha") or "")
    if len(proven) != 40:
        blockers.append(f"{prefix}PROVEN_SOURCE_SHA_INVALID")
    return blockers


def verify_reference_integrity(
    *,
    repo_root: Path,
    ref: Mapping[str, Any],
    prefix: str,
    expected_implementation_digest: str | None = None,
    expected_config_digest: str | None = None,
) -> tuple[list[str], Path | None, dict[str, Any]]:
    blockers: list[str] = []
    rel = str(ref.get("artifact_relpath") or "")
    artifact_path = safe_resolve_under_repo(repo_root=repo_root, relpath=rel)
    if artifact_path is None:
        blockers.append(f"{prefix}ARTIFACT_RELPATH_UNSAFE")
        return blockers, None, {}
    if not artifact_path.is_file():
        blockers.append(f"{prefix}ARTIFACT_MISSING")
        return blockers, artifact_path, {}

    declared_digest = str(ref.get("artifact_digest_sha256") or "")
    actual_digest = sha256_file(artifact_path)
    if not declared_digest:
        blockers.append(f"{prefix}ARTIFACT_DIGEST_MISSING")
    elif declared_digest != actual_digest:
        blockers.append(f"{prefix}ARTIFACT_DIGEST_MISMATCH")

    if not str(expected_implementation_digest or "").strip():
        blockers.append(f"{prefix}EXPECTED_IMPLEMENTATION_SURFACE_DIGEST_MISSING")
    else:
        impl = str(ref.get("implementation_surface_digest_sha256") or "")
        if impl != expected_implementation_digest:
            blockers.append(f"{prefix}IMPLEMENTATION_SURFACE_DIGEST_MISMATCH")
    if not str(expected_config_digest or "").strip():
        blockers.append(f"{prefix}EXPECTED_CONFIG_DIGEST_MISSING")
    else:
        cfg = str(ref.get("config_digest_sha256") or "")
        if cfg != expected_config_digest:
            blockers.append(f"{prefix}CONFIG_DIGEST_MISMATCH")

    doc, load_blockers = load_json_object(artifact_path)
    blockers.extend(f"{prefix}{b}" for b in load_blockers)
    return blockers, artifact_path, doc


def expected_domain_schema_verifier(domain: str) -> tuple[str, str]:
    if domain == "economic_metrics":
        return ECONOMIC_METRICS_DOMAIN_SCHEMA_ID, ECONOMIC_METRICS_VERIFIER_ID
    if domain == "walk_forward":
        return WALK_FORWARD_DOMAIN_SCHEMA_ID, WALK_FORWARD_VERIFIER_ID
    if domain == "monte_carlo":
        return MONTE_CARLO_DOMAIN_SCHEMA_ID, MONTE_CARLO_VERIFIER_ID
    if domain == "stress":
        return STRESS_DOMAIN_SCHEMA_ID, STRESS_VERIFIER_ID
    raise ValueError(f"unknown_domain:{domain}")
