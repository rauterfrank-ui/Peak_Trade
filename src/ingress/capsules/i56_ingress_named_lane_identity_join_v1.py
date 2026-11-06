"""EG-I82-JOIN U-I82-R21 — I56 named-lane IDENTITY join on EvidenceCapsule.

Attaches Package-N SHA256 IDENTITY onto the named I56 live contract
surfaces without rewriting EvidenceCapsule / ArtifactRef, without Cap 7.2 /
src.execution, and without persistence, migration, or backfill.
run_id remains RUN (including orchestrator default "default").
capsule_id remains EVIDENCE. Artifact sha256 remains CONTENT_HASH.
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
from src.ingress.capsules.i56_ingress_join_attachment_v1 import (
    I56IngressJoinAttachmentError,
    attach_i56_ingress_join_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

CONTRACT_ID = "i56_ingress_named_lane_identity_join_v1"
I56_NAMED_LANE_IDENTITY_JOIN_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "capsule",
    "artifact",
)

_CAPSULE_KEYS = frozenset({"capsule_id", "run_id", "ts_ms", "artifacts", "labels", "facts"})
_ARTIFACT_KEYS = frozenset({"path", "sha256"})

_FORBIDDEN_LIVE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
        "registry_run_id",
        "mlflow_run_id",
        "orders",
        "credentials",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "I16",
        "I17",
        "I52",
        "I56",
        "I61",
        "I65",
        "plane_presence",
        "join_key",
    }
)
_FORBIDDEN_LIVE_CONTENT_KEYS = frozenset(
    {
        "payload",
        "raw",
        "raw_payload",
        "transcript",
        "secrets",
        "orders",
        "credentials",
    }
)
_CROSS_LANE_KEYS = frozenset({"I16", "I17", "I52", "I61", "I65"})
_CROSS_PLANE_KEYS = frozenset({"plane_presence", "join_key"})


class I56IngressNamedLaneIdentityJoinError(ValueError):
    """Fail-closed I56 named-lane IDENTITY join error."""


def _reject(message: str) -> None:
    raise I56IngressNamedLaneIdentityJoinError(message)


def is_i56_named_lane_identity_join_registered() -> bool:
    """True iff the I56 named-lane IDENTITY join is registered on live I56 surfaces."""
    return I56_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def _require_identity(identity: object) -> str:
    if identity is None:
        _reject("implicit absence rejected: I56 named-lane IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _reject_forbidden_keys(payload: Mapping[str, Any], *, surface: str) -> None:
    keys = {str(key) for key in payload.keys()}
    forbidden = sorted(keys & _FORBIDDEN_LIVE_KEYS)
    if forbidden:
        if forbidden[0] in _CROSS_LANE_KEYS:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in _CROSS_PLANE_KEYS:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    content = sorted(keys & _FORBIDDEN_LIVE_CONTENT_KEYS)
    if content:
        _reject(f"malformed plane data rejected: I56 live surface {surface} carries {content[0]}")
    allowed = _CAPSULE_KEYS if surface == "capsule" else _ARTIFACT_KEYS
    extra = sorted(keys - allowed - _FORBIDDEN_LIVE_KEYS - _FORBIDDEN_LIVE_CONTENT_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I56 {surface} field: {extra[0]}")


def _unique_artifact_hash(artifacts: list[Mapping[str, Any]]) -> str | None:
    hashes: list[str] = []
    for item in artifacts:
        if not isinstance(item, Mapping):
            _reject("malformed plane data rejected: I56 artifact is not an object")
        _reject_forbidden_keys(item, surface="artifact")
        if "path" not in item or "sha256" not in item:
            _reject("malformed plane data rejected: I56 artifact missing path or sha256")
        digest = item["sha256"]
        if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
            _reject("malformed plane data rejected: I56 artifact sha256 is invalid")
        hashes.append(digest)
    if not hashes:
        return None
    unique = set(hashes)
    if len(unique) > 1:
        _reject("conflicting identity rejected: CONTENT_HASH values disagree")
    return hashes[0]


def _extract_live_fields(live: Mapping[str, Any], *, surface: str) -> dict[str, Any]:
    if surface == "artifact":
        digest = _unique_artifact_hash([live])
        if digest is None:
            _reject("implicit absence rejected: I56 CONTENT_HASH is missing")
        return {"artifact_sha256": digest}

    for required in ("capsule_id", "run_id", "ts_ms"):
        if required not in live:
            _reject(f"malformed plane data rejected: I56 capsule missing {required}")
    artifacts_raw = live.get("artifacts", [])
    if artifacts_raw is None:
        artifacts_raw = []
    if not isinstance(artifacts_raw, list):
        _reject("malformed plane data rejected: I56 capsule artifacts is not a list")
    out: dict[str, Any] = {
        "capsule_id": live["capsule_id"],
        "run_id": live["run_id"],
    }
    digest = _unique_artifact_hash(list(artifacts_raw))
    if digest is not None:
        out["artifact_sha256"] = digest
    return out


def join_i56_named_lane_identity_v1(
    live: object,
    *,
    surface: str,
    experiment_identity_id: str | None = None,
    run_id: str | None = None,
    campaign_id: str | None = None,
    session_id: str | None = None,
    legacy_alias_md5_12: str | None = None,
    content_sha256: str | None = None,
    evidence_ref: str | None = None,
    historical_provenance: Mapping[str, Any] | None = None,
) -> CrossLaneIdentityJoinV1:
    """Join Package-N SHA256 IDENTITY onto a named I56 live contract payload.

    Does not mutate inputs and does not rewrite persisted I56 schemas.
    """
    if surface not in LIVE_CONTRACT_SURFACES:
        _reject(f"malformed plane data rejected: unknown I56 live surface {surface}")
    if isinstance(live, (list, tuple)):
        _reject("ambiguous join rejected: I56 live surface has multiple Package-N assignments")
    if not isinstance(live, Mapping):
        _reject("malformed plane data rejected: I56 live payload is not an object")
    snapshot = copy.deepcopy(dict(live))
    _reject_forbidden_keys(live, surface=surface)

    identity = _require_identity(experiment_identity_id)
    if run_id is not None:
        _reject("noncanonical ID substitution rejected: run_id")
    extracted = _extract_live_fields(live, surface=surface)
    sidecar_campaign = _optional_sidecar(campaign_id, field="campaign_id")
    sidecar_session = _optional_sidecar(session_id, field="session_id")
    sidecar_alias = _optional_sidecar(legacy_alias_md5_12, field="legacy_alias_md5_12")
    sidecar_hash = _optional_sidecar(content_sha256, field="content_sha256")
    sidecar_evidence = _optional_sidecar(evidence_ref, field="evidence_ref")

    payload: dict[str, Any] = {"experiment_identity_id": identity}
    if extracted.get("capsule_id"):
        payload["capsule_id"] = extracted["capsule_id"]
    if extracted.get("run_id") is not None:
        payload["run_id"] = extracted["run_id"]
    live_hash = extracted.get("artifact_sha256")
    if sidecar_hash is not None and live_hash and sidecar_hash != live_hash:
        _reject("conflicting identity rejected: CONTENT_HASH values disagree")
    if live_hash:
        payload["artifact_sha256"] = live_hash
    if sidecar_hash is not None:
        payload["content_sha256"] = sidecar_hash
    live_evidence = extracted.get("capsule_id")
    if sidecar_evidence is not None and live_evidence and sidecar_evidence != live_evidence:
        _reject("conflicting identity rejected: EVIDENCE values disagree")
    if sidecar_evidence is not None:
        payload["evidence_ref"] = sidecar_evidence
    if sidecar_campaign is not None:
        payload["campaign_id"] = sidecar_campaign
    if sidecar_session is not None:
        payload["session_id"] = sidecar_session
    if sidecar_alias is not None:
        payload["legacy_alias_md5_12"] = sidecar_alias
    if historical_provenance is not None:
        if not isinstance(historical_provenance, Mapping):
            _reject("malformed plane data rejected: historical_provenance must be an object")
        provenance_copy = copy.deepcopy(dict(historical_provenance))
        nested = provenance_copy.get("experiment_identity_id")
        if nested is not None and nested != identity:
            _reject("conflicting identity rejected: historical_provenance.experiment_identity_id")
        payload["historical_provenance"] = provenance_copy

    try:
        record = attach_i56_ingress_join_v1(payload)
    except I56IngressJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message or "cannot fill IDENTITY" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I56IngressNamedLaneIdentityJoinError(
            f"I56 named-lane IDENTITY join rejected by R7 attachment: {exc}"
        ) from exc

    if dict(live) != snapshot:
        _reject("I56 live payload input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I56IngressNamedLaneIdentityJoinError",
    "I56_NAMED_LANE_IDENTITY_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i56_named_lane_identity_join_registered",
    "join_i56_named_lane_identity_v1",
]
