"""EG-I82-JOIN U-I82-R6 — dormant I52 Level-Up join attachment.

Attaches Package-N SHA256 IDENTITY onto I52 Level-Up join payloads.
relative_dir remains an EVIDENCE pointer under out/ops/ and is never IDENTITY.
Does not rewrite LevelUpManifestV0 / EvidenceBundleRefV0, does not register
into runtime/execution, and does not import Cap 7.2.
"""

from __future__ import annotations

import copy
import re
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

CONTRACT_ID = "i52_levelup_join_attachment_v1"

_EVIDENCE_PREFIX = "out/ops/"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]*$")

_KNOWN_KEYS = frozenset(
    {
        "experiment_identity_id",
        "slice_id",
        "relative_dir",
        "evidence_ref",
        "content_sha256",
        "run_id",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
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
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
    }
)
_NON_IDENTITY_I52_FIELDS = (
    "slice_id",
    "relative_dir",
    "run_id",
    "campaign_id",
    "session_id",
)


class I52LevelUpJoinAttachmentError(ValueError):
    """Fail-closed I52 Level-Up join attachment error."""


def _reject(message: str) -> None:
    raise I52LevelUpJoinAttachmentError(message)


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
        _reject("I52 IDENTITY missing: experiment_identity_id required")
    if not is_package_n_sha256_canonical_id(identity):
        _reject("experiment_identity_id must be Package-N SHA256")
    return identity


def _validate_relative_dir(relative_dir: str) -> str:
    path = relative_dir.replace("\\", "/")
    if not path.startswith(_EVIDENCE_PREFIX):
        _reject(f"relative_dir must start with {_EVIDENCE_PREFIX!r}")
    if ".." in path or path.startswith("/"):
        _reject("relative_dir path traversal is not allowed")
    rest = path[len(_EVIDENCE_PREFIX) :]
    if not rest or _SAFE_SEGMENT.match(rest) is None:
        _reject("relative_dir has invalid evidence path segments")
    return path


def _evidence_ref(payload: Mapping[str, Any]) -> str | None:
    evidence = _optional_str(payload, "evidence_ref")
    relative_dir = _optional_str(payload, "relative_dir")
    if relative_dir is not None:
        relative_dir = _validate_relative_dir(relative_dir)
    if evidence is not None:
        evidence = _validate_relative_dir(evidence)
    if evidence is not None and relative_dir is not None and evidence != relative_dir:
        _reject("conflicting EVIDENCE values")
    return relative_dir if relative_dir is not None else evidence


def _content_sha256(payload: Mapping[str, Any]) -> str | None:
    value = _optional_str(payload, "content_sha256")
    if value is None:
        return None
    if not is_valid_sha256_hex(value):
        _reject("content_sha256 must be 64-char lowercase sha256 hex when CONTENT_HASH is PRESENT")
    return value


def attach_i52_levelup_join_v1(i52_identity: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    """Attach Package-N SHA256 IDENTITY onto an I52 Level-Up join payload."""
    if not isinstance(i52_identity, Mapping):
        _reject("I52 identity payload must be an object")
    forbidden = sorted(str(key) for key in i52_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I52 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i52_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I52 join field: {extra[0]}")

    identity_id = _resolve_identity(i52_identity)
    slice_id = _optional_str(i52_identity, "slice_id")
    run_id = _optional_str(i52_identity, "run_id")
    campaign_id = _optional_str(i52_identity, "campaign_id")
    session_id = _optional_str(i52_identity, "session_id")
    alias = _optional_str(i52_identity, "legacy_alias_md5_12")
    evidence = _evidence_ref(i52_identity)
    content_hash = _content_sha256(i52_identity)
    provenance = i52_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}

    if slice_id is not None and slice_id == identity_id:
        _reject("slice_id must not substitute for Package-N SHA256 IDENTITY")
    for label in _NON_IDENTITY_I52_FIELDS:
        value = _optional_str(i52_identity, label)
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
        raise I52LevelUpJoinAttachmentError(
            f"I52 Level-Up join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I52LevelUpJoinAttachmentError",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i52_levelup_join_v1",
]
