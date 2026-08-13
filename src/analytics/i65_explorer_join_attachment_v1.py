"""EG-I82-JOIN U-I82-R9 — dormant I65 explorer join attachment.

Attaches Package-N SHA256 IDENTITY onto an I65 explorer join payload.
Splits IDENTITY from RUN: experiment_identity_id is SHA256 only; run_id
stays UUID RUN; legacy experiment_id is RUN_PROVENANCE_ALIAS only.
Does not rewrite explorer.py / ExperimentSummary / UUID run_id generator,
does not register into runtime/execution, and does not import Cap 7.2.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from src.analytics.legacy_identity_row_interpretation_v1 import (
    LEGACY_EXPERIMENT_ID_CLASSIFICATION,
    IdentityRequestMode,
    LegacyIdentityRowInterpretationError,
    interpret_legacy_identity_row_v1,
)
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

CONTRACT_ID = "i65_explorer_join_attachment_v1"

_R2_KEYS = (
    "experiment_identity_id",
    "run_id",
    "experiment_id",
    "legacy_alias_md5_12",
    "legacy_experiment_id_md5_12",
)
_KNOWN_KEYS = frozenset(
    {
        *_R2_KEYS,
        "campaign_id",
        "session_id",
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
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
        "evidence_id",
        "config_hash",
        "git_sha",
    }
)
_NON_IDENTITY_I65_FIELDS = (
    "run_id",
    "experiment_id",
    "campaign_id",
    "session_id",
    "evidence_ref",
)


class I65ExplorerJoinAttachmentError(ValueError):
    """Fail-closed I65 explorer join attachment error."""


def _reject(message: str) -> None:
    raise I65ExplorerJoinAttachmentError(message)


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
        _reject("I65 IDENTITY missing: experiment_identity_id required")
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


def _classify_legacy_fields(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    row_subset = {key: payload[key] for key in _R2_KEYS if key in payload}
    try:
        return interpret_legacy_identity_row_v1(
            row_subset,
            identity_request=IdentityRequestMode.IDENTITY_CANONICAL,
        )
    except LegacyIdentityRowInterpretationError as exc:
        raise I65ExplorerJoinAttachmentError(f"I65 field separation rejected: {exc}") from exc


def attach_i65_explorer_join_v1(i65_identity: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    """Attach Package-N SHA256 IDENTITY onto an I65 explorer join payload."""
    if not isinstance(i65_identity, Mapping):
        _reject("I65 identity payload must be an object")
    forbidden = sorted(str(key) for key in i65_identity.keys() if str(key) in _FORBIDDEN_KEYS)
    if forbidden:
        _reject(f"forbidden I65 join field: {forbidden[0]}")
    extra = sorted(str(key) for key in i65_identity.keys() if str(key) not in _KNOWN_KEYS)
    if extra:
        _reject(f"unknown I65 join field: {extra[0]}")

    identity_id = _resolve_identity(i65_identity)
    interpreted = _classify_legacy_fields(i65_identity)
    if interpreted.experiment_identity_id != identity_id:
        _reject("conflicting identities: R2 classification disagrees with Package-N SHA256")

    run_id = interpreted.run_id
    alias = interpreted.legacy_alias_md5_12
    campaign_id = _optional_str(i65_identity, "campaign_id")
    session_id = _optional_str(i65_identity, "session_id")
    evidence = _optional_str(i65_identity, "evidence_ref")
    content_hash = _content_sha256(i65_identity)
    provenance = i65_identity.get("historical_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        _reject("historical_provenance must be an object")
    provenance_copy = copy.deepcopy(dict(provenance)) if isinstance(provenance, Mapping) else {}
    if interpreted.legacy_experiment_id is not None:
        provenance_copy.setdefault("legacy_experiment_id", interpreted.legacy_experiment_id)
        provenance_copy.setdefault(
            "legacy_experiment_id_classification",
            interpreted.legacy_experiment_id_classification or LEGACY_EXPERIMENT_ID_CLASSIFICATION,
        )
    if run_id is not None:
        provenance_copy.setdefault("run_id", run_id)

    if run_id is not None and run_id == identity_id:
        _reject("run_id must not substitute for Package-N SHA256 IDENTITY")
    if (
        interpreted.legacy_experiment_id is not None
        and interpreted.legacy_experiment_id == identity_id
    ):
        _reject("legacy experiment_id must not substitute for Package-N SHA256 IDENTITY")
    for label in _NON_IDENTITY_I65_FIELDS:
        value = _optional_str(i65_identity, label)
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
        raise I65ExplorerJoinAttachmentError(
            f"I65 explorer join rejected by R3 primitive: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I65ExplorerJoinAttachmentError",
    "LEGACY_EXPERIMENT_ID_CLASSIFICATION",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "attach_i65_explorer_join_v1",
]
