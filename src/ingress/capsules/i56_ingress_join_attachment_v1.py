"""EG-I82-JOIN U-I82-R7 — dormant I56 Ingress join attachment.

Attaches Package-N SHA256 IDENTITY onto I56 EvidenceCapsule join payloads.
run_id remains RUN (including orchestrator default "default") and is never IDENTITY.
capsule_id remains EVIDENCE and is never IDENTITY.
Artifact sha256 remains CONTENT_HASH and is never IDENTITY.
Does not rewrite EvidenceCapsule / orchestrator / CLI, does not register
into runtime/execution, and does not import Cap 7.2.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_record_v1 import (
    CrossLaneIdentityJoinRecordError,
    build_cross_lane_identity_join_record_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    JOIN_PLANES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PlanePresence,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

CONTRACT_ID = "i56_ingress_join_attachment_v1"

_INGRESS_DEFAULT_RUN_ID = "default"

_KNOWN_KEYS = frozenset(
    {
        "experiment_identity_id",
        "capsule_id",
        "run_id",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
        "artifact_sha256",
        "historical_provenance",
    }
)
_FORBIDDEN_KEYS = frozenset(
    {
        "orders",
        "credentials",
        "secrets",
        "payload",
        "raw",
        "raw_payload",
        "transcript",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
    }
)
_NON_IDENTITY_I56_FIELDS = (
    "capsule_id",
    "run_id",
    "campaign_id",
    "session_id",
    "evidence_ref",
)


class I56IngressJoinAttachmentError(ValueError):
    """Fail-closed I56 Ingress join attachment error."""


def _reject(message: str) -> None:
    raise I56IngressJoinAttachmentError(message)


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str):
        _reject(f"{key} must be a string when present")
    if not value.strip() or value != value.strip():
        _reject(f"{key} is present but empty or whitespace-padded")
    return value


def _present(plane: str, value: str, join_key: str) -> dict[str, str]:
    return {
        "plane": plane,
        "presence": PlanePresence.PRESENT.value,
        "join_key": join_key,
        "value": value,
    }


def _absent(plane: str) -> dict[str, str]:
    return {"plane": plane, "presence": PlanePresence.ABSENT_DECLARED.value}


def _resolve_identity(payload: Mapping[str, Any]) -> str:
    identity = _optional_str(payload, "experiment_identity_id")
    if identity is None:
        _reject("I56 IDENTITY missing: experiment_identity_id required")
    if identity == _INGRESS_DEFAULT_RUN_ID:
        _reject("run_id default cannot fill IDENTITY")
    if identity.endswith(".capsule"):
        _reject("capsule_id cannot fill IDENTITY")
    if not is_package_n_sha256_canonical_id(identity):
        _reject("experiment_identity_id must be Package-N SHA256")
    return identity


def _evidence_ref(payload: Mapping[str, Any]) -> str | None:
    evidence = _optional_str(payload, "evidence_ref")
    capsule_id = _optional_str(payload, "capsule_id")
    if evidence is not None and capsule_id is not None and evidence != capsule_id:
        _reject("conflicting EVIDENCE values")
    return capsule_id if capsule_id is not None else evidence


def _content_sha256(payload: Mapping[str, Any]) -> str | None:
    direct = _optional_str(payload, "content_sha256")
    artifact = _optional_str(payload, "artifact_sha256")
    candidates: list[str] = []
    for label, value in (("content_sha256", direct), ("artifact_sha256", artifact)):
        if value is None:
            continue
        if not is_valid_sha256_hex(value):
            _reject(f"{label} must be 64-char lowercase sha256 hex when CONTENT_HASH is PRESENT")
        candidates.append(value)
    if len(set(candidates)) > 1:
        _reject("conflicting CONTENT_HASH values")
    return candidates[0] if candidates else None


def attach_i56_ingress_join_v1(i56_identity: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    """Attach Package-N SHA256 IDENTITY onto an I56 Ingress join payload."""
    if not isinstance(i56_identity, Mapping):
        _reject("I56 identity payload must be an object")
    forbidden = sorted(str(key) for key in i56_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I56 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i56_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I56 join field: {extra[0]}")

    identity_id = _resolve_identity(i56_identity)
    capsule_id = _optional_str(i56_identity, "capsule_id")
    run_id = _optional_str(i56_identity, "run_id")
    campaign_id = _optional_str(i56_identity, "campaign_id")
    session_id = _optional_str(i56_identity, "session_id")
    alias = _optional_str(i56_identity, "legacy_alias_md5_12")
    evidence = _evidence_ref(i56_identity)
    content_hash = _content_sha256(i56_identity)
    provenance = i56_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}

    if capsule_id is not None and capsule_id == identity_id:
        _reject("capsule_id must not substitute for Package-N SHA256 IDENTITY")
    if run_id is not None and run_id == identity_id:
        _reject("run_id must not substitute for Package-N SHA256 IDENTITY")
    for label in _NON_IDENTITY_I56_FIELDS:
        value = _optional_str(i56_identity, label)
        if value is not None and value == identity_id:
            _reject(f"{label} must not substitute for Package-N SHA256 IDENTITY")

    contributions = {
        "IDENTITY": _present("IDENTITY", identity_id, identity_id),
        "ALIAS": _present("ALIAS", alias, identity_id) if alias is not None else _absent("ALIAS"),
        "RUN": _present("RUN", run_id, identity_id) if run_id is not None else _absent("RUN"),
        "CAMPAIGN": (
            _present("CAMPAIGN", campaign_id, identity_id)
            if campaign_id is not None
            else _absent("CAMPAIGN")
        ),
        "SESSION": (
            _present("SESSION", session_id, identity_id)
            if session_id is not None
            else _absent("SESSION")
        ),
        "EVIDENCE": (
            _present("EVIDENCE", evidence, identity_id)
            if evidence is not None
            else _absent("EVIDENCE")
        ),
        "CONTENT_HASH": (
            _present("CONTENT_HASH", content_hash, identity_id)
            if content_hash is not None
            else _absent("CONTENT_HASH")
        ),
    }
    ordered = [contributions[plane] for plane in JOIN_PLANES]
    try:
        return build_cross_lane_identity_join_record_v1(
            ordered,
            package_n_identity_id=identity_id,
            historical_provenance=provenance_copy or None,
        )
    except CrossLaneIdentityJoinRecordError as exc:
        raise I56IngressJoinAttachmentError(
            f"I56 Ingress join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I56IngressJoinAttachmentError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i56_ingress_join_v1",
]
