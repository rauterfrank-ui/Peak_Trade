"""EG-I82-JOIN U-I82-R5 — dormant I17 paper-shadow join attachment.

Adds Package-N SHA256 IDENTITY onto I17 prereg/GO/artifact join payloads.
session_id remains SESSION and is required independently of IDENTITY.
Does not rewrite live preregistration/GO/artifact contracts, does not
register into runtime/execution, and does not import Cap 7.2.
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

CONTRACT_ID = "i17_paper_shadow_join_attachment_v1"

_KNOWN_KEYS = frozenset(
    {
        "experiment_identity_id",
        "session_id",
        "run_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "evidence_root",
        "content_sha256",
        "scope_digest",
        "config_identity",
        "code_identity",
        "expected_repository_sha",
        "go_id",
        "authorization_id",
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
        "campaign_id",
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
_NON_IDENTITY_I17_FIELDS = (
    "session_id",
    "run_id",
    "config_identity",
    "code_identity",
    "expected_repository_sha",
    "go_id",
    "authorization_id",
)


class I17PaperShadowJoinAttachmentError(ValueError):
    """Fail-closed I17 paper-shadow join attachment error."""


def _reject(message: str) -> None:
    raise I17PaperShadowJoinAttachmentError(message)


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
        _reject("I17 IDENTITY missing: experiment_identity_id required")
    if not is_package_n_sha256_canonical_id(identity):
        _reject("experiment_identity_id must be Package-N SHA256")
    return identity


def _require_session_id(payload: Mapping[str, Any]) -> str:
    session_id = _optional_str(payload, "session_id")
    if session_id is None:
        _reject("I17 SESSION missing: session_id required independently of IDENTITY")
    return session_id


def _evidence_ref(payload: Mapping[str, Any]) -> str | None:
    evidence = _optional_str(payload, "evidence_ref")
    evidence_root = _optional_str(payload, "evidence_root")
    if evidence is not None and evidence_root is not None and evidence != evidence_root:
        _reject("conflicting EVIDENCE values")
    return evidence if evidence is not None else evidence_root


def _content_sha256(payload: Mapping[str, Any]) -> str | None:
    direct = _optional_str(payload, "content_sha256")
    scope_digest = _optional_str(payload, "scope_digest")
    candidates: list[str] = []
    for label, value in (("content_sha256", direct), ("scope_digest", scope_digest)):
        if value is None:
            continue
        if not is_valid_sha256_hex(value):
            _reject(f"{label} must be 64-char lowercase sha256 hex when used as CONTENT_HASH")
        candidates.append(value)
    if len(set(candidates)) > 1:
        _reject("conflicting CONTENT_HASH values")
    return candidates[0] if candidates else None


def attach_i17_paper_shadow_join_v1(
    i17_identity: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Attach Package-N SHA256 IDENTITY onto an I17 prereg/GO/artifact join payload."""
    if not isinstance(i17_identity, Mapping):
        _reject("I17 identity payload must be an object")
    forbidden = sorted(str(key) for key in i17_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I17 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i17_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I17 join field: {extra[0]}")

    identity_id = _resolve_identity(i17_identity)
    session_id = _require_session_id(i17_identity)
    run_id = _optional_str(i17_identity, "run_id")
    alias = _optional_str(i17_identity, "legacy_alias_md5_12")
    evidence = _evidence_ref(i17_identity)
    content_hash = _content_sha256(i17_identity)
    provenance = i17_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}

    if session_id == identity_id:
        _reject("session_id must not substitute for Package-N SHA256 IDENTITY")
    for label in _NON_IDENTITY_I17_FIELDS:
        value = _optional_str(i17_identity, label)
        if value is not None and value == identity_id:
            _reject(f"{label} must not substitute for Package-N SHA256 IDENTITY")

    contributions = {
        "IDENTITY": _present("IDENTITY", identity_id, identity_id),
        "ALIAS": _present("ALIAS", alias, identity_id) if alias is not None else _absent("ALIAS"),
        "RUN": _present("RUN", run_id, identity_id) if run_id is not None else _absent("RUN"),
        "CAMPAIGN": _absent("CAMPAIGN"),
        "SESSION": _present("SESSION", session_id, identity_id),
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
        raise I17PaperShadowJoinAttachmentError(
            f"I17 paper-shadow join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I17PaperShadowJoinAttachmentError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i17_paper_shadow_join_v1",
]
