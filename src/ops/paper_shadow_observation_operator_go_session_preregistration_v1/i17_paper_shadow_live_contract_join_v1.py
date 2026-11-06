"""EG-I82-JOIN U-I82-R12 — dormant I17 live-contract join registration.

Binds Package-N SHA256 IDENTITY onto validated I17 prereg/GO/artifact
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
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactError,
    parse_authorization_artifact_v1,
    validate_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1 import (
    I17PaperShadowJoinAttachmentError,
    attach_i17_paper_shadow_join_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractError,
    parse_operator_go_contract_v1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    PreregistrationContractError,
    parse_preregistration_contract_v1,
    validate_preregistration_contract_v1,
)

CONTRACT_ID = "i17_paper_shadow_live_contract_join_v1"
I17_LIVE_CONTRACT_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "preregistration",
    "operator_go",
    "authorization_artifact",
)

_KNOWN_ENVELOPE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "preregistration",
        "operator_go",
        "authorization_artifact",
        "run_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
        "historical_provenance",
    }
)
_FORBIDDEN_ENVELOPE_KEYS = frozenset(
    {
        "session_id",
        "campaign_id",
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
        "I52",
        "I56",
        "I61",
        "I65",
    }
)


class I17PaperShadowLiveContractJoinError(ValueError):
    """Fail-closed I17 live-contract join registration error."""


def _reject(message: str) -> None:
    raise I17PaperShadowLiveContractJoinError(message)


def is_i17_live_contract_registered() -> bool:
    """True iff the dormant I17 live-contract join surface is registered."""
    return I17_LIVE_CONTRACT_REGISTERED is True


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
        _reject("implicit absence rejected: I17 live-contract IDENTITY is missing")
    identity = envelope.get("experiment_identity_id")
    if identity is None:
        _reject("implicit absence rejected: I17 live-contract IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _snapshot_live_payload(raw: object, *, surface: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: I17 live surface {surface} is missing")
    if isinstance(raw, (list, tuple)):
        if not raw:
            _reject(f"implicit absence rejected: I17 live surface {surface} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: I17 live surface {surface} has multiple Package-N assignments"
            )
        return _snapshot_live_payload(raw[0], surface=surface)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: I17 live surface {surface} is not an object")
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
        _reject("implicit absence rejected: I17 live contract surface is missing")
    if len(present) != 1:
        _reject("ambiguous join rejected: I17 live contract has multiple Package-N assignments")
    surface = present[0]
    return surface, _snapshot_live_payload(envelope[surface], surface=surface)


def _validate_preregistration(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        contract = parse_preregistration_contract_v1(payload)
        result = validate_preregistration_contract_v1(contract)
    except PreregistrationContractError as exc:
        _reject(f"malformed plane data rejected: I17 preregistration is invalid: {exc}")
    if not result.ok:
        _reject(
            "malformed plane data rejected: I17 preregistration is invalid: "
            + ",".join(result.blockers)
        )
    return contract.to_dict()


def _validate_operator_go(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        contract = parse_operator_go_contract_v1(payload)
        result = validate_operator_go_contract_v1(contract)
    except OperatorGoContractError as exc:
        _reject(f"malformed plane data rejected: I17 operator_go is invalid: {exc}")
    if not result.ok:
        _reject(
            "malformed plane data rejected: I17 operator_go is invalid: "
            + ",".join(result.blockers)
        )
    return contract.to_dict()


def _validate_authorization_artifact(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        artifact = parse_authorization_artifact_v1(payload)
        result = validate_authorization_artifact_v1(artifact)
    except AuthorizationArtifactError as exc:
        _reject(f"malformed plane data rejected: I17 authorization_artifact is invalid: {exc}")
    if not result.ok:
        _reject(
            "malformed plane data rejected: I17 authorization_artifact is invalid: "
            + ",".join(result.blockers)
        )
    return artifact.to_dict()


_SURFACE_VALIDATORS = {
    "preregistration": _validate_preregistration,
    "operator_go": _validate_operator_go,
    "authorization_artifact": _validate_authorization_artifact,
}


def _join_payload(
    *,
    identity_id: str,
    live: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "experiment_identity_id": identity_id,
        "session_id": live["session_id"],
        "config_identity": live.get("config_identity"),
        "code_identity": live.get("code_identity"),
        "expected_repository_sha": live.get("expected_repository_sha"),
    }
    if live.get("evidence_root"):
        payload["evidence_root"] = live["evidence_root"]
    if live.get("go_id"):
        payload["go_id"] = live["go_id"]
    if live.get("authorization_id"):
        payload["authorization_id"] = live["authorization_id"]

    envelope_evidence = _optional_str(envelope, "evidence_ref")
    live_evidence = live.get("evidence_root")
    if envelope_evidence is not None and live_evidence and envelope_evidence != live_evidence:
        _reject("conflicting identity rejected: EVIDENCE values disagree")
    if envelope_evidence is not None:
        payload["evidence_ref"] = envelope_evidence

    envelope_hash = _optional_str(envelope, "content_sha256")
    live_hash = live.get("scope_digest")
    if (
        envelope_hash is not None
        and isinstance(live_hash, str)
        and live_hash
        and envelope_hash != live_hash
    ):
        _reject("conflicting identity rejected: CONTENT_HASH values disagree")
    if envelope_hash is not None:
        payload["content_sha256"] = envelope_hash
    elif isinstance(live_hash, str) and live_hash:
        payload["content_sha256"] = live_hash

    run_id = _optional_str(envelope, "run_id")
    if run_id is not None:
        payload["run_id"] = run_id
    alias = _optional_str(envelope, "legacy_alias_md5_12")
    if alias is not None:
        payload["legacy_alias_md5_12"] = alias
    provenance = envelope.get("historical_provenance")
    if provenance is not None:
        payload["historical_provenance"] = copy.deepcopy(provenance)
    return {key: value for key, value in payload.items() if value is not None}


def register_i17_live_contract_join_v1(
    live_join: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Register an I17 live-contract payload onto the Package-N SHA256 join path."""
    if not isinstance(live_join, Mapping):
        _reject("malformed plane data rejected: I17 live-contract envelope is not an object")
    snapshot = copy.deepcopy(dict(live_join))
    forbidden = sorted(str(key) for key in live_join.keys() if str(key) in _FORBIDDEN_ENVELOPE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I52", "I56", "I61", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"}:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    extra = sorted(str(key) for key in live_join.keys() if str(key) not in _KNOWN_ENVELOPE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I17 live-contract field: {extra[0]}")

    identity_id = _require_identity(live_join)
    surface, live_payload = _select_live_surface(live_join)
    _reject_live_identity_substitution(live_payload, surface=surface)
    validated = _SURFACE_VALIDATORS[surface](live_payload)
    attachment = _join_payload(identity_id=identity_id, live=validated, envelope=live_join)
    try:
        record = attach_i17_paper_shadow_join_v1(attachment)
    except I17PaperShadowJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        raise I17PaperShadowLiveContractJoinError(
            f"I17 live-contract join rejected by R5 attachment: {exc}"
        ) from exc

    if dict(live_join) != snapshot:
        _reject("I17 live-contract envelope input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I17PaperShadowLiveContractJoinError",
    "I17_LIVE_CONTRACT_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i17_live_contract_registered",
    "register_i17_live_contract_join_v1",
]
