"""EG-I82-JOIN U-I82-R20 — I52 named-lane IDENTITY join on v0 models.

Attaches Package-N SHA256 IDENTITY onto the named I52 live contract
surfaces without rewriting LevelUpManifestV0 / SliceContractV0 /
EvidenceBundleRefV0, without Cap 7.2 / src.execution, and without
persistence, migration, or backfill. relative_dir remains EVIDENCE.
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
from src.levelup.i52_levelup_join_attachment_v1 import (
    I52LevelUpJoinAttachmentError,
    attach_i52_levelup_join_v1,
)

CONTRACT_ID = "i52_levelup_named_lane_identity_join_v1"
I52_NAMED_LANE_IDENTITY_JOIN_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "manifest",
    "slice",
    "evidence_bundle",
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


class I52LevelUpNamedLaneIdentityJoinError(ValueError):
    """Fail-closed I52 named-lane IDENTITY join error."""


def _reject(message: str) -> None:
    raise I52LevelUpNamedLaneIdentityJoinError(message)


def is_i52_named_lane_identity_join_registered() -> bool:
    """True iff the I52 named-lane IDENTITY join is registered on live I52 surfaces."""
    return I52_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def _require_identity(identity: object) -> str:
    if identity is None:
        _reject("implicit absence rejected: I52 named-lane IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _extract_live_fields(live: Mapping[str, Any], *, surface: str) -> dict[str, Any]:
    if surface == "evidence_bundle":
        relative_dir = live.get("relative_dir")
        if not isinstance(relative_dir, str) or not relative_dir.strip():
            _reject("implicit absence rejected: I52 EVIDENCE is missing")
        return {"relative_dir": relative_dir}

    slices = live.get("slices")
    if surface == "manifest":
        if slices is None:
            slices = ()
        if not isinstance(slices, (list, tuple)):
            _reject("malformed plane data rejected: I52 manifest slices are invalid")
        if len(slices) > 1:
            _reject("ambiguous join rejected: I52 manifest has multiple Package-N assignments")
        if not slices:
            return {}
        item = slices[0]
        if not isinstance(item, Mapping):
            _reject("malformed plane data rejected: I52 manifest slice is not an object")
        return _extract_slice_fields(item)

    return _extract_slice_fields(live)


def _extract_slice_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    slice_id = payload.get("slice_id")
    if isinstance(slice_id, str) and slice_id.strip():
        out["slice_id"] = slice_id
    evidence = payload.get("evidence")
    if isinstance(evidence, Mapping) and evidence.get("relative_dir"):
        out["relative_dir"] = evidence["relative_dir"]
    elif isinstance(payload.get("relative_dir"), str) and payload["relative_dir"].strip():
        out["relative_dir"] = payload["relative_dir"]
    return out


def join_i52_named_lane_identity_v1(
    live: Mapping[str, Any],
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
    """Join Package-N SHA256 IDENTITY onto a named I52 live contract payload.

    Does not mutate inputs and does not rewrite persisted I52 schemas.
    """
    if surface not in LIVE_CONTRACT_SURFACES:
        _reject(f"malformed plane data rejected: unknown I52 live surface {surface}")
    if not isinstance(live, Mapping):
        _reject("malformed plane data rejected: I52 live payload is not an object")
    snapshot = copy.deepcopy(dict(live))
    forbidden = sorted(str(key) for key in live.keys() if str(key) in _FORBIDDEN_LIVE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I17", "I56", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")

    nested_candidates: list[Mapping[str, Any]] = []
    slices = live.get("slices")
    if isinstance(slices, (list, tuple)):
        nested_candidates.extend(item for item in slices if isinstance(item, Mapping))
    evidence = live.get("evidence")
    if isinstance(evidence, Mapping):
        nested_candidates.append(evidence)
    for nested in nested_candidates:
        nested_forbidden = sorted(
            str(key) for key in nested.keys() if str(key) in _FORBIDDEN_LIVE_KEYS
        )
        if nested_forbidden:
            if nested_forbidden[0] in {"I16", "I17", "I56", "I61", "I65"}:
                _reject(f"cross-lane substitution rejected: {nested_forbidden[0]}")
            if nested_forbidden[0] in {"plane_presence", "join_key"}:
                _reject(f"cross-plane substitution rejected: {nested_forbidden[0]}")
            _reject(f"noncanonical ID substitution rejected: {nested_forbidden[0]}")

    identity = _require_identity(experiment_identity_id)
    extracted = _extract_live_fields(live, surface=surface)
    sidecar_run = _optional_sidecar(run_id, field="run_id")
    sidecar_campaign = _optional_sidecar(campaign_id, field="campaign_id")
    sidecar_session = _optional_sidecar(session_id, field="session_id")
    sidecar_alias = _optional_sidecar(legacy_alias_md5_12, field="legacy_alias_md5_12")
    sidecar_hash = _optional_sidecar(content_sha256, field="content_sha256")
    sidecar_evidence = _optional_sidecar(evidence_ref, field="evidence_ref")

    payload: dict[str, Any] = {"experiment_identity_id": identity}
    if extracted.get("slice_id"):
        payload["slice_id"] = extracted["slice_id"]
    live_evidence = extracted.get("relative_dir")
    if sidecar_evidence is not None and live_evidence and sidecar_evidence != live_evidence:
        _reject("conflicting identity rejected: EVIDENCE values disagree")
    if live_evidence:
        payload["relative_dir"] = live_evidence
    if sidecar_evidence is not None:
        payload["evidence_ref"] = sidecar_evidence
    if sidecar_run is not None:
        payload["run_id"] = sidecar_run
    if sidecar_campaign is not None:
        payload["campaign_id"] = sidecar_campaign
    if sidecar_session is not None:
        payload["session_id"] = sidecar_session
    if sidecar_alias is not None:
        payload["legacy_alias_md5_12"] = sidecar_alias
    if sidecar_hash is not None:
        payload["content_sha256"] = sidecar_hash
    if historical_provenance is not None:
        if not isinstance(historical_provenance, Mapping):
            _reject("malformed plane data rejected: historical_provenance must be an object")
        provenance_copy = copy.deepcopy(dict(historical_provenance))
        nested = provenance_copy.get("experiment_identity_id")
        if nested is not None and nested != identity:
            _reject("conflicting identity rejected: historical_provenance.experiment_identity_id")
        payload["historical_provenance"] = provenance_copy

    try:
        record = attach_i52_levelup_join_v1(payload)
    except I52LevelUpJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I52LevelUpNamedLaneIdentityJoinError(
            f"I52 named-lane IDENTITY join rejected by R6 attachment: {exc}"
        ) from exc

    if dict(live) != snapshot:
        _reject("I52 live payload input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I52LevelUpNamedLaneIdentityJoinError",
    "I52_NAMED_LANE_IDENTITY_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i52_named_lane_identity_join_registered",
    "join_i52_named_lane_identity_v1",
]
