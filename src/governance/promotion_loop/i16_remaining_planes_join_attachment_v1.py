"""EG-I82-JOIN U-I82-R4 — dormant I16 remaining-plane join attachment.

Joins I16 RUN/CAMPAIGN/SESSION onto already-proven Package-N SHA256 IDENTITY.
Does not rewrite lineage artifacts, does not change ref_id, and does not
register into runtime/execution pipelines.
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

CONTRACT_ID = "i16_remaining_planes_join_attachment_v1"

_KNOWN_KEYS = frozenset(
    {
        "experiment_identity_id",
        "ref_id",
        "run_id",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
        "legacy_aliases",
        "evidence_ref",
        "artifact_path",
        "content_sha256",
        "digest",
        "integrity",
        "historical_provenance",
    }
)
_FORBIDDEN_KEYS = frozenset(
    {
        "orders",
        "credentials",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "experiment_id",
        "identity_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
    }
)


class I16RemainingPlanesJoinAttachmentError(ValueError):
    """Fail-closed I16 remaining-plane join attachment error."""


def _reject(message: str) -> None:
    raise I16RemainingPlanesJoinAttachmentError(message)


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
    ref_id = _optional_str(payload, "ref_id")
    if identity is None and ref_id is None:
        _reject("I16 IDENTITY missing: experiment_identity_id or ref_id required")
    if identity is not None and not is_package_n_sha256_canonical_id(identity):
        _reject("experiment_identity_id must be Package-N SHA256")
    if ref_id is not None and not is_package_n_sha256_canonical_id(ref_id):
        _reject("ref_id must be Package-N SHA256 and must not be UUID/run_id/MD5")
    if identity is not None and ref_id is not None and identity != ref_id:
        _reject("conflicting Package-N SHA256 identities: ref_id != experiment_identity_id")
    resolved = identity or ref_id
    if resolved is None or not is_package_n_sha256_canonical_id(resolved):
        _reject("I16 IDENTITY must be Package-N SHA256")
    return resolved


def _alias_md5_12(payload: Mapping[str, Any]) -> str | None:
    direct = _optional_str(payload, "legacy_alias_md5_12")
    nested = payload.get("legacy_aliases")
    nested_id: str | None = None
    if nested is not None:
        if not isinstance(nested, Mapping):
            _reject("legacy_aliases must be an object")
        raw = nested.get("legacy_experiment_id_md5_12")
        if raw is not None:
            if not isinstance(raw, str) or not raw.strip() or raw != raw.strip():
                _reject("legacy_aliases.legacy_experiment_id_md5_12 is invalid")
            nested_id = raw
    if direct is not None and nested_id is not None and direct != nested_id:
        _reject("conflicting identities: MD5 alias fields disagree")
    return direct if direct is not None else nested_id


def _content_sha256(payload: Mapping[str, Any]) -> str | None:
    direct = _optional_str(payload, "content_sha256")
    digest = _optional_str(payload, "digest")
    nested = payload.get("integrity")
    nested_id: str | None = None
    if nested is not None:
        if not isinstance(nested, Mapping):
            _reject("integrity must be an object")
        raw = nested.get("content_sha256")
        if raw is not None:
            if not isinstance(raw, str) or not raw.strip() or raw != raw.strip():
                _reject("integrity.content_sha256 is invalid")
            nested_id = raw
    found = [item for item in (direct, digest, nested_id) if item is not None]
    if len(set(found)) > 1:
        _reject("conflicting CONTENT_HASH values")
    return found[0] if found else None


def _evidence_ref(payload: Mapping[str, Any]) -> str | None:
    evidence = _optional_str(payload, "evidence_ref")
    artifact = _optional_str(payload, "artifact_path")
    if evidence is not None and artifact is not None and evidence != artifact:
        _reject("conflicting EVIDENCE values")
    return evidence if evidence is not None else artifact


def attach_i16_remaining_planes_join_v1(
    i16_identity: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Attach explicit RUN/CAMPAIGN/SESSION planes onto proven I16 Package-N IDENTITY."""
    if not isinstance(i16_identity, Mapping):
        _reject("I16 identity payload must be an object")
    forbidden = sorted(str(key) for key in i16_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I16 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i16_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I16 join field: {extra[0]}")

    identity_id = _resolve_identity(i16_identity)
    run_id = _optional_str(i16_identity, "run_id")
    campaign_id = _optional_str(i16_identity, "campaign_id")
    session_id = _optional_str(i16_identity, "session_id")
    alias = _alias_md5_12(i16_identity)
    evidence = _evidence_ref(i16_identity)
    content_hash = _content_sha256(i16_identity)
    provenance = i16_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}

    for label, value in (
        ("run_id", run_id),
        ("campaign_id", campaign_id),
        ("session_id", session_id),
    ):
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
        raise I16RemainingPlanesJoinAttachmentError(
            f"I16 remaining-plane join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I16RemainingPlanesJoinAttachmentError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i16_remaining_planes_join_v1",
]
