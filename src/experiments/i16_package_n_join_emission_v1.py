"""EG-I82-JOIN U-I82-R10 — dormant I16 Package-N producer join emission.

Registers the R4 I16 join attachment at the Package-N producer boundary.
Canonical join key is experiment_identity_id from build_manifest only.
Does not rewrite experiment_identity_manifest_v1.json, does not hook
produce()/CLI/ExperimentRunner, and does not import Cap 7.2 or src.execution.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)
from src.experiments.experiment_identity_manifest_v1 import (
    ExperimentIdentityManifestError,
    build_manifest,
    validate_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1 import (
    I16RemainingPlanesJoinAttachmentError,
    attach_i16_remaining_planes_join_v1,
)

CONTRACT_ID = "i16_package_n_join_emission_v1"

_FORBIDDEN_MANIFEST_JOIN_KEYS = frozenset(
    {
        "run_id",
        "campaign_id",
        "session_id",
        "experiment_id",
        "registry_run_id",
        "mlflow_run_id",
        "orders",
        "credentials",
    }
)


class I16PackageNJoinEmissionError(ValueError):
    """Fail-closed I16 Package-N producer join emission error."""


def _reject(message: str) -> None:
    raise I16PackageNJoinEmissionError(message)


def emit_i16_package_n_join_v1(
    package_n_manifest: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Emit an I16 join record from a canonical Package-N producer manifest."""
    if not isinstance(package_n_manifest, Mapping):
        _reject("Package-N manifest must be an object")
    snapshot = copy.deepcopy(dict(package_n_manifest))
    forbidden = sorted(
        str(key) for key in package_n_manifest.keys() if str(key) in _FORBIDDEN_MANIFEST_JOIN_KEYS
    )
    if forbidden:
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    try:
        validate_experiment_identity_manifest_v1(package_n_manifest)
    except ExperimentIdentityManifestError as exc:
        raise I16PackageNJoinEmissionError(f"malformed Package-N producer manifest: {exc}") from exc

    identity_id = package_n_manifest.get("experiment_identity_id")
    if not is_package_n_sha256_canonical_id(identity_id):
        _reject("experiment_identity_id must be Package-N SHA256")

    provenance = package_n_manifest.get("provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}
    source_id = provenance_copy.get("source_experiment_id")
    if source_id is not None and source_id == identity_id:
        _reject("source_experiment_id must not substitute for Package-N SHA256 IDENTITY")

    payload = {
        "experiment_identity_id": identity_id,
        "legacy_aliases": copy.deepcopy(dict(package_n_manifest["legacy_aliases"])),
        "integrity": copy.deepcopy(dict(package_n_manifest["integrity"])),
        "historical_provenance": provenance_copy or None,
    }
    if payload["historical_provenance"] is None:
        payload.pop("historical_provenance")

    try:
        record = attach_i16_remaining_planes_join_v1(payload)
    except I16RemainingPlanesJoinAttachmentError as exc:
        raise I16PackageNJoinEmissionError(
            f"I16 producer join rejected by R4 attachment: {exc}"
        ) from exc

    if dict(package_n_manifest) != snapshot:
        _reject("Package-N manifest input was mutated")
    return record


def emit_i16_package_n_join_from_producer_v1(
    config: Any,
    *,
    source_experiment_id: str | None = None,
) -> CrossLaneIdentityJoinV1:
    """Build a Package-N manifest via the producer, then emit the I16 join."""
    manifest = build_manifest(config, source_experiment_id=source_experiment_id)
    return emit_i16_package_n_join_v1(manifest)


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I16PackageNJoinEmissionError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "emit_i16_package_n_join_from_producer_v1",
    "emit_i16_package_n_join_v1",
]
