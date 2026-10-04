"""Protected digest projection per V1.5 digest model."""

from __future__ import annotations

from typing import Any, Mapping

from src.evaluation.golden_vectors.contracts.models import (
    ProtectedSemanticDigestsV1,
    RunManifestV1,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

# contract_schema_manifest.json digest_model.excluded_volatile_fields
EXCLUDED_VOLATILE_FIELDS = frozenset({"created_at_utc", "runner_host", "process_id"})
RUN_MANIFEST_VOLATILE_FIELDS = frozenset({"created_at_utc"})


def project_mapping_for_protected_digest(
    payload: Mapping[str, Any],
    *,
    exclude: frozenset[str],
) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in exclude}


def project_run_manifest_for_protected_digest(run: RunManifestV1) -> dict[str, Any]:
    """RunManifest digest input: volatile created_at_utc excluded (V1.5 digest model)."""
    raw = contract_to_canonical_mapping(run)
    return project_mapping_for_protected_digest(raw, exclude=RUN_MANIFEST_VOLATILE_FIELDS)


def run_manifest_protected_digest_hex(run: RunManifestV1) -> str:
    return sha256_hex(project_run_manifest_for_protected_digest(run))


def protected_semantic_digests_digest(digests: ProtectedSemanticDigestsV1) -> str:
    payload = contract_to_canonical_mapping(digests)
    return sha256_hex(payload)
