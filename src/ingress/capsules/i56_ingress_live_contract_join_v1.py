"""EG-I82-JOIN U-I82-R14 — dormant I56 live-contract join registration.

Binds Package-N SHA256 IDENTITY onto validated I56 EvidenceCapsule/ArtifactRef
payloads without rewriting those live schemas, without hooking Cap 7.2 /
src.execution, and without persistence, migration, or backfill.
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
from src.ingress.capsules.evidence_capsule import ArtifactRef, EvidenceCapsule
from src.ingress.capsules.i56_ingress_join_attachment_v1 import (
    I56IngressJoinAttachmentError,
    attach_i56_ingress_join_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

CONTRACT_ID = "i56_ingress_live_contract_join_v1"
I56_LIVE_CONTRACT_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "capsule",
    "artifact",
)

_CAPSULE_KEYS = frozenset({"capsule_id", "run_id", "ts_ms", "artifacts", "labels", "facts"})
_ARTIFACT_KEYS = frozenset({"path", "sha256"})
_KNOWN_ENVELOPE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "capsule",
        "artifact",
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
        "capsule_id",
        "run_id",
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
        "secrets",
        "payload",
        "raw",
        "raw_payload",
        "transcript",
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
        "I52",
        "I61",
        "I65",
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


class I56IngressLiveContractJoinError(ValueError):
    """Fail-closed I56 live-contract join registration error."""


def _reject(message: str) -> None:
    raise I56IngressLiveContractJoinError(message)


def is_i56_live_contract_registered() -> bool:
    """True iff the dormant I56 live-contract join surface is registered."""
    return I56_LIVE_CONTRACT_REGISTERED is True


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
        _reject("implicit absence rejected: I56 live-contract IDENTITY is missing")
    identity = envelope.get("experiment_identity_id")
    if identity is None:
        _reject("implicit absence rejected: I56 live-contract IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _snapshot_live_payload(raw: object, *, surface: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: I56 live surface {surface} is missing")
    if isinstance(raw, (list, tuple)):
        if not raw:
            _reject(f"implicit absence rejected: I56 live surface {surface} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: I56 live surface {surface} has multiple Package-N assignments"
            )
        return _snapshot_live_payload(raw[0], surface=surface)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: I56 live surface {surface} is not an object")
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
    forbidden = sorted(
        str(key) for key in payload.keys() if str(key) in _FORBIDDEN_LIVE_CONTENT_KEYS
    )
    if forbidden:
        _reject(f"malformed plane data rejected: I56 live surface {surface} carries {forbidden[0]}")


def _select_live_surface(envelope: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    present = [name for name in LIVE_CONTRACT_SURFACES if name in envelope]
    if not present:
        _reject("implicit absence rejected: I56 live contract surface is missing")
    if len(present) != 1:
        _reject("ambiguous join rejected: I56 live contract has multiple Package-N assignments")
    surface = present[0]
    return surface, _snapshot_live_payload(envelope[surface], surface=surface)


def _unique_artifact_hash(artifacts: list[ArtifactRef]) -> str | None:
    hashes = [item.sha256 for item in artifacts]
    if not hashes:
        return None
    unique = set(hashes)
    if len(unique) > 1:
        _reject("conflicting identity rejected: CONTENT_HASH values disagree")
    digest = hashes[0]
    if not is_valid_sha256_hex(digest):
        _reject("malformed plane data rejected: I56 artifact sha256 is invalid")
    return digest


def _validate_capsule(payload: Mapping[str, Any]) -> dict[str, Any]:
    extra = sorted(str(key) for key in payload.keys() if str(key) not in _CAPSULE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I56 capsule field: {extra[0]}")
    for required in ("capsule_id", "run_id", "ts_ms"):
        if required not in payload:
            _reject(f"malformed plane data rejected: I56 capsule missing {required}")
    artifacts_raw = payload.get("artifacts", [])
    if artifacts_raw is None:
        artifacts_raw = []
    if not isinstance(artifacts_raw, list):
        _reject("malformed plane data rejected: I56 capsule artifacts is not a list")
    refs: list[ArtifactRef] = []
    for item in artifacts_raw:
        if not isinstance(item, Mapping):
            _reject("malformed plane data rejected: I56 artifact is not an object")
        extra_art = sorted(str(key) for key in item.keys() if str(key) not in _ARTIFACT_KEYS)
        if extra_art:
            _reject(f"malformed plane data rejected: unknown I56 artifact field: {extra_art[0]}")
        if "path" not in item or "sha256" not in item:
            _reject("malformed plane data rejected: I56 artifact missing path or sha256")
        refs.append(ArtifactRef(path=str(item["path"]), sha256=str(item["sha256"])))
    labels = payload.get("labels") or {}
    facts = payload.get("facts") or {}
    if not isinstance(labels, Mapping) or not isinstance(facts, Mapping):
        _reject("malformed plane data rejected: I56 capsule labels/facts must be objects")
    try:
        capsule = EvidenceCapsule(
            capsule_id=str(payload["capsule_id"]),
            run_id=str(payload["run_id"]),
            ts_ms=int(payload["ts_ms"]),
            artifacts=refs,
            labels=dict(labels),
            facts=dict(facts),
        )
    except (TypeError, ValueError) as exc:
        _reject(f"malformed plane data rejected: I56 capsule is invalid: {exc}")
    out: dict[str, Any] = {
        "capsule_id": capsule.capsule_id,
        "run_id": capsule.run_id,
    }
    digest = _unique_artifact_hash(capsule.artifacts)
    if digest is not None:
        out["artifact_sha256"] = digest
    return out


def _validate_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    extra = sorted(str(key) for key in payload.keys() if str(key) not in _ARTIFACT_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I56 artifact field: {extra[0]}")
    if "path" not in payload or "sha256" not in payload:
        _reject("malformed plane data rejected: I56 artifact missing path or sha256")
    try:
        artifact = ArtifactRef(path=str(payload["path"]), sha256=str(payload["sha256"]))
    except (TypeError, ValueError) as exc:
        _reject(f"malformed plane data rejected: I56 artifact is invalid: {exc}")
    if not is_valid_sha256_hex(artifact.sha256):
        _reject("malformed plane data rejected: I56 artifact sha256 is invalid")
    return {"artifact_sha256": artifact.sha256}


_SURFACE_VALIDATORS = {
    "capsule": _validate_capsule,
    "artifact": _validate_artifact,
}


def _join_payload(
    *,
    identity_id: str,
    live: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"experiment_identity_id": identity_id}
    if live.get("capsule_id"):
        payload["capsule_id"] = live["capsule_id"]
    if live.get("run_id"):
        payload["run_id"] = live["run_id"]
    live_hash = live.get("artifact_sha256")
    envelope_hash = _optional_str(envelope, "content_sha256")
    if envelope_hash is not None and live_hash and envelope_hash != live_hash:
        _reject("conflicting identity rejected: CONTENT_HASH values disagree")
    if live_hash:
        payload["artifact_sha256"] = live_hash
    if envelope_hash is not None:
        payload["content_sha256"] = envelope_hash
    envelope_evidence = _optional_str(envelope, "evidence_ref")
    live_evidence = live.get("capsule_id")
    if envelope_evidence is not None and live_evidence and envelope_evidence != live_evidence:
        _reject("conflicting identity rejected: EVIDENCE values disagree")
    if envelope_evidence is not None:
        payload["evidence_ref"] = envelope_evidence
    for key in ("campaign_id", "session_id", "legacy_alias_md5_12"):
        value = _optional_str(envelope, key)
        if value is not None:
            payload[key] = value
    provenance = envelope.get("historical_provenance")
    if provenance is not None:
        payload["historical_provenance"] = copy.deepcopy(provenance)
    return payload


def register_i56_live_contract_join_v1(
    live_join: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Register an I56 live-contract payload onto the Package-N SHA256 join path."""
    if not isinstance(live_join, Mapping):
        _reject("malformed plane data rejected: I56 live-contract envelope is not an object")
    snapshot = copy.deepcopy(dict(live_join))
    forbidden = sorted(str(key) for key in live_join.keys() if str(key) in _FORBIDDEN_ENVELOPE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I17", "I52", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    extra = sorted(str(key) for key in live_join.keys() if str(key) not in _KNOWN_ENVELOPE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I56 live-contract field: {extra[0]}")

    identity_id = _require_identity(live_join)
    surface, live_payload = _select_live_surface(live_join)
    _reject_live_identity_substitution(live_payload, surface=surface)
    validated = _SURFACE_VALIDATORS[surface](live_payload)
    attachment = _join_payload(identity_id=identity_id, live=validated, envelope=live_join)
    try:
        record = attach_i56_ingress_join_v1(attachment)
    except I56IngressJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message or "cannot fill IDENTITY" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        raise I56IngressLiveContractJoinError(
            f"I56 live-contract join rejected by R7 attachment: {exc}"
        ) from exc

    if dict(live_join) != snapshot:
        _reject("I56 live-contract envelope input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I56IngressLiveContractJoinError",
    "I56_LIVE_CONTRACT_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i56_live_contract_registered",
    "register_i56_live_contract_join_v1",
]
