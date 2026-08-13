"""EG-I82-JOIN U-I82-R13 — dormant I52 live-contract join registration.

Binds Package-N SHA256 IDENTITY onto validated I52 manifest/slice/evidence
payloads without rewriting those live schemas, without hooking Cap 7.2 /
src.execution, and without persistence, migration, or backfill.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from pydantic import ValidationError

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
from src.levelup.v0_models import EvidenceBundleRefV0, LevelUpManifestV0, SliceContractV0

CONTRACT_ID = "i52_levelup_live_contract_join_v1"
I52_LIVE_CONTRACT_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "manifest",
    "slice",
    "evidence_bundle",
)

_KNOWN_ENVELOPE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "manifest",
        "slice",
        "evidence_bundle",
        "run_id",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
        "historical_provenance",
    }
)
_FORBIDDEN_ENVELOPE_KEYS = frozenset(
    {
        "slice_id",
        "relative_dir",
        "experiment_id",
        "identity_id",
        "ref_id",
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
_LIVE_IDENTITY_SUBSTITUTE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "plane_presence",
        "join_key",
        "I16",
        "I17",
        "I56",
        "I61",
        "I65",
    }
)


class I52LevelUpLiveContractJoinError(ValueError):
    """Fail-closed I52 live-contract join registration error."""


def _reject(message: str) -> None:
    raise I52LevelUpLiveContractJoinError(message)


def is_i52_live_contract_registered() -> bool:
    """True iff the dormant I52 live-contract join surface is registered."""
    return I52_LIVE_CONTRACT_REGISTERED is True


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


def _require_identity(envelope: Mapping[str, Any]) -> str:
    if "experiment_identity_id" not in envelope:
        _reject("implicit absence rejected: I52 live-contract IDENTITY is missing")
    identity = envelope.get("experiment_identity_id")
    if identity is None:
        _reject("implicit absence rejected: I52 live-contract IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _snapshot_live_payload(raw: object, *, surface: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: I52 live surface {surface} is missing")
    if isinstance(raw, (list, tuple)):
        if not raw:
            _reject(f"implicit absence rejected: I52 live surface {surface} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: I52 live surface {surface} has multiple Package-N assignments"
            )
        return _snapshot_live_payload(raw[0], surface=surface)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: I52 live surface {surface} is not an object")
    return copy.deepcopy(dict(raw))


def _reject_live_identity_substitution(payload: Mapping[str, Any], *, surface: str) -> None:
    substitutes = sorted(
        str(key) for key in payload.keys() if str(key) in _LIVE_IDENTITY_SUBSTITUTE_KEYS
    )
    if substitutes:
        _reject(
            f"noncanonical ID substitution rejected: live surface {surface} uses {substitutes[0]} "
            "as Package-N identity"
        )


def _select_live_surface(envelope: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    present = [name for name in LIVE_CONTRACT_SURFACES if name in envelope]
    if not present:
        _reject("implicit absence rejected: I52 live contract surface is missing")
    if len(present) != 1:
        _reject("ambiguous join rejected: I52 live contract has multiple Package-N assignments")
    surface = present[0]
    return surface, _snapshot_live_payload(envelope[surface], surface=surface)


def _validate_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        contract = LevelUpManifestV0.model_validate(payload)
    except ValidationError as exc:
        _reject(f"malformed plane data rejected: I52 manifest is invalid: {exc}")
    if len(contract.slices) > 1:
        _reject("ambiguous join rejected: I52 manifest has multiple Package-N assignments")
    dumped = contract.model_dump(mode="python")
    if contract.slices:
        slice_dump = dumped["slices"][0]
        out: dict[str, Any] = {"slice_id": slice_dump["slice_id"]}
        evidence = slice_dump.get("evidence")
        if isinstance(evidence, Mapping) and evidence.get("relative_dir"):
            out["relative_dir"] = evidence["relative_dir"]
        return out
    return {}


def _validate_slice(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        contract = SliceContractV0.model_validate(payload)
    except ValidationError as exc:
        _reject(f"malformed plane data rejected: I52 slice is invalid: {exc}")
    dumped = contract.model_dump(mode="python")
    out: dict[str, Any] = {"slice_id": dumped["slice_id"]}
    evidence = dumped.get("evidence")
    if isinstance(evidence, Mapping) and evidence.get("relative_dir"):
        out["relative_dir"] = evidence["relative_dir"]
    return out


def _validate_evidence_bundle(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        contract = EvidenceBundleRefV0.model_validate(payload)
    except ValidationError as exc:
        _reject(f"malformed plane data rejected: I52 evidence_bundle is invalid: {exc}")
    return {"relative_dir": contract.relative_dir}


_SURFACE_VALIDATORS = {
    "manifest": _validate_manifest,
    "slice": _validate_slice,
    "evidence_bundle": _validate_evidence_bundle,
}


def _join_payload(
    *,
    identity_id: str,
    live: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"experiment_identity_id": identity_id}
    if live.get("slice_id"):
        payload["slice_id"] = live["slice_id"]
    live_evidence = live.get("relative_dir")
    envelope_evidence = _optional_str(envelope, "evidence_ref")
    if envelope_evidence is not None and live_evidence and envelope_evidence != live_evidence:
        _reject("conflicting identity rejected: EVIDENCE values disagree")
    if live_evidence:
        payload["relative_dir"] = live_evidence
    if envelope_evidence is not None:
        payload["evidence_ref"] = envelope_evidence

    content_hash = _optional_str(envelope, "content_sha256")
    if content_hash is not None:
        payload["content_sha256"] = content_hash
    for key in ("run_id", "campaign_id", "session_id", "legacy_alias_md5_12"):
        value = _optional_str(envelope, key)
        if value is not None:
            payload[key] = value
    provenance = envelope.get("historical_provenance")
    if provenance is not None:
        payload["historical_provenance"] = copy.deepcopy(provenance)
    return payload


def register_i52_live_contract_join_v1(
    live_join: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Register an I52 live-contract payload onto the Package-N SHA256 join path."""
    if not isinstance(live_join, Mapping):
        _reject("malformed plane data rejected: I52 live-contract envelope is not an object")
    snapshot = copy.deepcopy(dict(live_join))
    forbidden = sorted(str(key) for key in live_join.keys() if str(key) in _FORBIDDEN_ENVELOPE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I17", "I56", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    extra = sorted(str(key) for key in live_join.keys() if str(key) not in _KNOWN_ENVELOPE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I52 live-contract field: {extra[0]}")

    identity_id = _require_identity(live_join)
    surface, live_payload = _select_live_surface(live_join)
    _reject_live_identity_substitution(live_payload, surface=surface)
    validated = _SURFACE_VALIDATORS[surface](live_payload)
    attachment = _join_payload(identity_id=identity_id, live=validated, envelope=live_join)
    try:
        record = attach_i52_levelup_join_v1(attachment)
    except I52LevelUpJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        raise I52LevelUpLiveContractJoinError(
            f"I52 live-contract join rejected by R6 attachment: {exc}"
        ) from exc

    if dict(live_join) != snapshot:
        _reject("I52 live-contract envelope input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I52LevelUpLiveContractJoinError",
    "I52_LIVE_CONTRACT_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i52_live_contract_registered",
    "register_i52_live_contract_join_v1",
]
