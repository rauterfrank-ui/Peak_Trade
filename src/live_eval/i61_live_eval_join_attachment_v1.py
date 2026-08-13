"""EG-I82-JOIN U-I82-R8 — dormant I61 live-eval identity envelope.

Attaches Package-N SHA256 IDENTITY onto an I61 eval metadata envelope.
Fill trade fields stay off the join surface. --session-dir remains a
filesystem SESSION hint and is never IDENTITY or session_id.
Does not rewrite Fill, fill CSV IO, or the eval CLI,
does not register into runtime/execution, and does not import Cap 7.2.
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

CONTRACT_ID = "live_session_eval_identity_envelope_v1"

_KNOWN_KEYS = frozenset(
    {
        "experiment_identity_id",
        "session_id",
        "session_dir",
        "run_id",
        "campaign_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
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
        "fills",
        "ts",
        "symbol",
        "side",
        "qty",
        "fill_price",
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
_NON_IDENTITY_I61_FIELDS = (
    "session_id",
    "session_dir",
    "run_id",
    "campaign_id",
    "evidence_ref",
)


class I61LiveEvalJoinAttachmentError(ValueError):
    """Fail-closed I61 live-eval identity envelope error."""


def _reject(message: str) -> None:
    raise I61LiveEvalJoinAttachmentError(message)


def _looks_like_filesystem_path(value: str) -> bool:
    return "/" in value or "\\" in value


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
        _reject("I61 IDENTITY missing: experiment_identity_id required")
    if _looks_like_filesystem_path(identity):
        _reject("session-dir path is not identity")
    if not is_package_n_sha256_canonical_id(identity):
        _reject("experiment_identity_id must be Package-N SHA256")
    return identity


def _content_sha256(payload: Mapping[str, Any]) -> str | None:
    value = _optional_str(payload, "content_sha256")
    if value is None:
        return None
    if not is_valid_sha256_hex(value):
        _reject("content_sha256 must be 64-char lowercase sha256 hex when CONTENT_HASH is PRESENT")
    return value


def attach_i61_live_eval_join_v1(i61_identity: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    """Attach Package-N SHA256 IDENTITY onto an I61 eval metadata envelope."""
    if not isinstance(i61_identity, Mapping):
        _reject("I61 identity payload must be an object")
    forbidden = sorted(str(key) for key in i61_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I61 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i61_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I61 join field: {extra[0]}")

    identity_id = _resolve_identity(i61_identity)
    session_id = _optional_str(i61_identity, "session_id")
    session_dir = _optional_str(i61_identity, "session_dir")
    run_id = _optional_str(i61_identity, "run_id")
    campaign_id = _optional_str(i61_identity, "campaign_id")
    alias = _optional_str(i61_identity, "legacy_alias_md5_12")
    evidence = _optional_str(i61_identity, "evidence_ref")
    content_hash = _content_sha256(i61_identity)
    provenance = i61_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}

    if session_dir is not None and session_dir == identity_id:
        _reject("session-dir path is not identity")
    if session_id is not None and _looks_like_filesystem_path(session_id):
        _reject("session-dir path is not session_id")
    if session_id is not None and session_dir is not None and session_id == session_dir:
        _reject("session-dir path is not session_id")
    for label in _NON_IDENTITY_I61_FIELDS:
        value = _optional_str(i61_identity, label)
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
        raise I61LiveEvalJoinAttachmentError(
            f"I61 live-eval join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I61LiveEvalJoinAttachmentError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i61_live_eval_join_v1",
]
