"""EG-I82-JOIN U-I82-R18 — I16 named-lane remaining-plane join on lineage producer.

Attaches RUN/CAMPAIGN/SESSION onto Package-N SHA256 IDENTITY at the I16
LineageRef producer without rewriting lineage JSON, without changing
ref_id, and without Cap 7.2 / src.execution / persistence / migration.
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
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import LineageRef, LineageRefType
from src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1 import (
    I16RemainingPlanesJoinAttachmentError,
    attach_i16_remaining_planes_join_v1,
)

CONTRACT_ID = "i16_lineage_remaining_planes_live_join_v1"
I16_LINEAGE_REMAINING_PLANES_JOIN_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = ("lineage_ref",)

_FORBIDDEN_SIDECAR_KEYS = frozenset(
    {
        "experiment_id",
        "identity_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
        "orders",
        "credentials",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "I17",
        "I52",
        "I56",
        "I61",
        "I65",
        "plane_presence",
        "join_key",
    }
)


class I16LineageRemainingPlanesLiveJoinError(ValueError):
    """Fail-closed I16 lineage remaining-plane live join error."""


def _reject(message: str) -> None:
    raise I16LineageRemainingPlanesLiveJoinError(message)


def is_i16_lineage_remaining_planes_join_registered() -> bool:
    """True iff the I16 lineage remaining-plane join is registered on the named producer."""
    return I16_LINEAGE_REMAINING_PLANES_JOIN_REGISTERED is True


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def join_i16_lineage_remaining_planes_v1(
    manifest: Mapping[str, Any],
    *,
    ref: LineageRef,
    artifact_path: str,
    run_id: str | None = None,
    campaign_id: str | None = None,
    session_id: str | None = None,
) -> CrossLaneIdentityJoinV1:
    """Join I16 remaining planes onto a named-lane LineageRef. Does not mutate inputs."""
    if not isinstance(manifest, Mapping):
        _reject("malformed plane data rejected: lineage manifest is not an object")
    if not isinstance(ref, LineageRef):
        _reject("malformed plane data rejected: lineage ref is not a LineageRef")
    snapshot = copy.deepcopy(dict(manifest))
    forbidden = sorted(str(key) for key in manifest.keys() if str(key) in _FORBIDDEN_SIDECAR_KEYS)
    if forbidden:
        if forbidden[0] in {"I17", "I52", "I56", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")

    if ref.ref_type != LineageRefType.EXPERIMENT:
        _reject(f"malformed plane data rejected: ref_type must be EXPERIMENT, got {ref.ref_type}")
    identity = manifest.get("experiment_identity_id")
    if not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    if ref.ref_id != identity:
        _reject("conflicting identity rejected: LineageRef.ref_id != experiment_identity_id")
    if not is_package_n_sha256_canonical_id(ref.digest):
        _reject("malformed plane data rejected: LineageRef.digest must be sha256 hex")

    sidecar_run = _optional_sidecar(run_id, field="run_id")
    sidecar_campaign = _optional_sidecar(campaign_id, field="campaign_id")
    sidecar_session = _optional_sidecar(session_id, field="session_id")

    payload: dict[str, Any] = {
        "experiment_identity_id": identity,
        "ref_id": ref.ref_id,
        "digest": ref.digest,
        "artifact_path": artifact_path,
        "integrity": {"content_sha256": ref.digest},
    }
    aliases = manifest.get("legacy_aliases")
    if isinstance(aliases, Mapping):
        payload["legacy_aliases"] = copy.deepcopy(dict(aliases))
    provenance = manifest.get("provenance")
    if provenance is not None:
        if not isinstance(provenance, Mapping):
            _reject("malformed plane data rejected: provenance must be an object")
        provenance_copy = copy.deepcopy(dict(provenance))
        source_id = provenance_copy.get("source_experiment_id")
        if source_id is not None and source_id == identity:
            _reject(
                "noncanonical ID substitution rejected: source_experiment_id must not be IDENTITY"
            )
        payload["historical_provenance"] = provenance_copy
    if sidecar_run is not None:
        payload["run_id"] = sidecar_run
    if sidecar_campaign is not None:
        payload["campaign_id"] = sidecar_campaign
    if sidecar_session is not None:
        payload["session_id"] = sidecar_session

    try:
        record = attach_i16_remaining_planes_join_v1(payload)
    except I16RemainingPlanesJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I16LineageRemainingPlanesLiveJoinError(
            f"I16 lineage remaining-plane join rejected by R4 attachment: {exc}"
        ) from exc

    if dict(manifest) != snapshot:
        _reject("lineage manifest input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I16LineageRemainingPlanesLiveJoinError",
    "I16_LINEAGE_REMAINING_PLANES_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i16_lineage_remaining_planes_join_registered",
    "join_i16_lineage_remaining_planes_v1",
]
