"""EG-I82-JOIN U-I82-R19 — I17 named-lane IDENTITY join on prereg/GO/artifact.

Attaches Package-N SHA256 IDENTITY onto the named I17 live contract
surfaces without rewriting persisted prereg/GO/artifact schemas, without
Cap 7.2 / src.execution, and without persistence, migration, or backfill.
session_id remains SESSION and is required independently of IDENTITY.
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
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1 import (
    I17PaperShadowJoinAttachmentError,
    attach_i17_paper_shadow_join_v1,
)

CONTRACT_ID = "i17_paper_shadow_named_lane_identity_join_v1"
I17_NAMED_LANE_IDENTITY_JOIN_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "preregistration",
    "operator_go",
    "authorization_artifact",
)

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
        "run_id",
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


class I17PaperShadowNamedLaneIdentityJoinError(ValueError):
    """Fail-closed I17 named-lane IDENTITY join error."""


def _reject(message: str) -> None:
    raise I17PaperShadowNamedLaneIdentityJoinError(message)


def is_i17_named_lane_identity_join_registered() -> bool:
    """True iff the I17 named-lane IDENTITY join is registered on live I17 surfaces."""
    return I17_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def _require_identity(identity: object) -> str:
    if identity is None:
        _reject("implicit absence rejected: I17 named-lane IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def join_i17_named_lane_identity_v1(
    live: Mapping[str, Any],
    *,
    experiment_identity_id: str,
    surface: str,
    run_id: str | None = None,
    legacy_alias_md5_12: str | None = None,
    content_sha256: str | None = None,
    historical_provenance: Mapping[str, Any] | None = None,
) -> CrossLaneIdentityJoinV1:
    """Join Package-N SHA256 IDENTITY onto a named I17 live contract payload.

    Does not mutate inputs and does not rewrite persisted I17 schemas.
    """
    if surface not in LIVE_CONTRACT_SURFACES:
        _reject(f"malformed plane data rejected: unknown I17 live surface {surface}")
    if not isinstance(live, Mapping):
        _reject("malformed plane data rejected: I17 live payload is not an object")
    snapshot = copy.deepcopy(dict(live))
    forbidden = sorted(str(key) for key in live.keys() if str(key) in _FORBIDDEN_LIVE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I52", "I56", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")

    identity = _require_identity(experiment_identity_id)
    session_id = live.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        _reject("implicit absence rejected: I17 SESSION is missing")

    sidecar_run = _optional_sidecar(run_id, field="run_id")
    sidecar_alias = _optional_sidecar(legacy_alias_md5_12, field="legacy_alias_md5_12")
    sidecar_hash = _optional_sidecar(content_sha256, field="content_sha256")

    payload: dict[str, Any] = {
        "experiment_identity_id": identity,
        "session_id": session_id,
    }
    evidence_root = live.get("evidence_root")
    if isinstance(evidence_root, str) and evidence_root.strip():
        payload["evidence_root"] = evidence_root
    for field in ("config_identity", "code_identity", "expected_repository_sha"):
        value = live.get(field)
        if isinstance(value, str) and value.strip():
            payload[field] = value
    go_id = live.get("go_id")
    if isinstance(go_id, str) and go_id.strip():
        payload["go_id"] = go_id
    authorization_id = live.get("authorization_id")
    if isinstance(authorization_id, str) and authorization_id.strip():
        payload["authorization_id"] = authorization_id
    live_hash = live.get("scope_digest")
    if sidecar_hash is not None:
        payload["content_sha256"] = sidecar_hash
    elif isinstance(live_hash, str) and live_hash.strip():
        payload["content_sha256"] = live_hash
    if sidecar_run is not None:
        payload["run_id"] = sidecar_run
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
        record = attach_i17_paper_shadow_join_v1(payload)
    except I17PaperShadowJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I17PaperShadowNamedLaneIdentityJoinError(
            f"I17 named-lane IDENTITY join rejected by R5 attachment: {exc}"
        ) from exc

    if dict(live) != snapshot:
        _reject("I17 live payload input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I17PaperShadowNamedLaneIdentityJoinError",
    "I17_NAMED_LANE_IDENTITY_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i17_named_lane_identity_join_registered",
    "join_i17_named_lane_identity_v1",
]
