"""G1 — Typed M5→M6 federated return join (surface_execution_identity; no M4 plane).

Deterministic, provenance-preserving join boundary for federated projected M5 records.
Does not invoke M4, mutate learning state, or coalesce plane_identity with surface identity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
    validate_federated_projected_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT,
    SCHEMA_VERSION as OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    UNIVERSE_CLASS_OPTIMIZATION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "federated_m5_m6_return_join_v1"
RETURN_JOIN_DOMAIN: Final[str] = "peak_trade.federated_m5_m6_return_join.v1"
DECISION_CONFIG: Final[str] = (
    "config/governance/m5_m8_bounded_meta_return_and_replay_completion_v1_decision_v1.json"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_NORMATIVE_V1.md"
)

JOIN_KEY_KIND: Final[str] = "SURFACE_EXECUTION_IDENTITY"
JOIN_CARDINALITY: Final[str] = "ONE_TO_ONE"
M4_RE_EXECUTION: Final[bool] = False

JOIN_STATUS_COMPLETE: Final[str] = "FEDERATED_M5_M6_RETURN_JOIN_COMPLETE"
JOIN_STATUS_REJECTED_FOREIGN: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_FOREIGN_EVIDENCE"
JOIN_STATUS_REJECTED_IDENTITY: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_IDENTITY"
JOIN_STATUS_REJECTED_PLANE: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_PLANE_IDENTITY_PRESENT"
JOIN_STATUS_REJECTED_DUPLICATE: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_DUPLICATE_JOIN_KEY"
JOIN_STATUS_REJECTED_CARDINALITY: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_CARDINALITY"
JOIN_STATUS_REJECTED_MALFORMED: Final[str] = "FEDERATED_RETURN_JOIN_REJECTED_MALFORMED"

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
META_LEARNING_INGEST_PERFORMED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False

_LOGGER = logging.getLogger(__name__)


class FederatedM5M6ReturnJoinError(ValueError):
    """Fail-closed federated M5→M6 return join request error."""


@dataclass(frozen=True)
class FederatedM5M6ReturnJoinRequestV1:
    optimization_experiment_evidence: Mapping[str, Any] | None
    expected_evidence_schema_version: str | None = OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION
    expected_surface_execution_identity: str | None = None
    seen_surface_execution_identities: frozenset[str] = field(default_factory=frozenset)
    requested_m4_re_execution: bool = False
    requested_learning_state_mutation: bool = False
    requested_meta_learning_ingest: bool = False


def derive_federated_return_join_identity_v1(
    *,
    surface_execution_identity: str,
    optimization_experiment_evidence_digest: str,
) -> str:
    return compute_content_sha256(
        {
            "digest_domain": f"{RETURN_JOIN_DOMAIN}.return_join_identity",
            "schema_version": SCHEMA_VERSION,
            "join_key_kind": JOIN_KEY_KIND,
            "join_cardinality": JOIN_CARDINALITY,
            "surface_execution_identity": surface_execution_identity,
            "optimization_experiment_evidence_digest": optimization_experiment_evidence_digest,
        }
    )


def perform_federated_m5_m6_return_join_v1(
    request: FederatedM5M6ReturnJoinRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_m4_re_execution:
        raise FederatedM5M6ReturnJoinError("M4_RE_EXECUTION_FORBIDDEN")
    if request.requested_learning_state_mutation:
        raise FederatedM5M6ReturnJoinError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_meta_learning_ingest:
        raise FederatedM5M6ReturnJoinError("META_LEARNING_INGEST_FORBIDDEN_AT_JOIN_BOUNDARY")

    if request.expected_evidence_schema_version not in (
        None,
        OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    ):
        return _join_payload(
            status=JOIN_STATUS_REJECTED_MALFORMED,
            reason="OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION_MISMATCH",
            surface_execution_identity=None,
            evidence_digest=None,
            record_id=None,
            return_join_identity=None,
        )

    if request.optimization_experiment_evidence is None:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_MALFORMED,
            reason="MISSING_OPTIMIZATION_EXPERIMENT_EVIDENCE",
            surface_execution_identity=None,
            evidence_digest=None,
            record_id=None,
            return_join_identity=None,
        )

    raw = request.optimization_experiment_evidence
    if raw.get("plane_identity") is not None:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_PLANE,
            reason="PLANE_IDENTITY_FORBIDDEN_ON_FEDERATED_JOIN",
            surface_execution_identity=str(raw.get("surface_execution_identity") or "") or None,
            evidence_digest=str(raw.get("content_hash") or "") or None,
            record_id=str(raw.get("record_id") or "") or None,
            return_join_identity=None,
        )

    try:
        evidence = validate_federated_projected_optimization_experiment_evidence_v1(raw)
    except Exception as exc:
        _LOGGER.debug("federated evidence validation failed: %s", exc)
        return _join_payload(
            status=JOIN_STATUS_REJECTED_FOREIGN,
            reason="NOT_FEDERATED_PROJECTED_OPTIMIZATION_EXPERIMENT_EVIDENCE",
            surface_execution_identity=None,
            evidence_digest=None,
            record_id=None,
            return_join_identity=None,
        )

    if evidence.get("universe_class") != UNIVERSE_CLASS_OPTIMIZATION:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_FOREIGN,
            reason="EVIDENCE_UNIVERSE_CLASS_NOT_OPTIMIZATION",
            surface_execution_identity=str(evidence.get("surface_execution_identity")),
            evidence_digest=str(evidence.get("content_hash")),
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )
    if evidence.get("evidence_class") != EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_FOREIGN,
            reason="EVIDENCE_CLASS_NOT_OPTIMIZATION_EXPERIMENT",
            surface_execution_identity=str(evidence.get("surface_execution_identity")),
            evidence_digest=str(evidence.get("content_hash")),
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    surface_execution_identity = str(evidence.get("surface_execution_identity") or "")
    if not is_valid_sha256_hex(surface_execution_identity):
        return _join_payload(
            status=JOIN_STATUS_REJECTED_IDENTITY,
            reason="SURFACE_EXECUTION_IDENTITY_INVALID",
            surface_execution_identity=None,
            evidence_digest=str(evidence.get("content_hash")),
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    if (
        request.expected_surface_execution_identity is not None
        and request.expected_surface_execution_identity != surface_execution_identity
    ):
        return _join_payload(
            status=JOIN_STATUS_REJECTED_IDENTITY,
            reason="SURFACE_EXECUTION_IDENTITY_MISMATCH",
            surface_execution_identity=surface_execution_identity,
            evidence_digest=str(evidence.get("content_hash")),
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    if surface_execution_identity in request.seen_surface_execution_identities:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_DUPLICATE,
            reason="DUPLICATE_SURFACE_EXECUTION_IDENTITY_JOIN_KEY",
            surface_execution_identity=surface_execution_identity,
            evidence_digest=str(evidence.get("content_hash")),
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    content_hash = str(evidence.get("content_hash"))
    if not is_valid_sha256_hex(content_hash):
        return _join_payload(
            status=JOIN_STATUS_REJECTED_MALFORMED,
            reason="EVIDENCE_CONTENT_HASH_INVALID",
            surface_execution_identity=surface_execution_identity,
            evidence_digest=None,
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    provenance = evidence.get("provenance")
    if not isinstance(provenance, Mapping):
        return _join_payload(
            status=JOIN_STATUS_REJECTED_MALFORMED,
            reason="PROVENANCE_MISSING",
            surface_execution_identity=surface_execution_identity,
            evidence_digest=content_hash,
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )
    if str(provenance.get("surface_execution_identity") or "") != surface_execution_identity:
        return _join_payload(
            status=JOIN_STATUS_REJECTED_CARDINALITY,
            reason="PROVENANCE_SURFACE_EXECUTION_IDENTITY_MISMATCH",
            surface_execution_identity=surface_execution_identity,
            evidence_digest=content_hash,
            record_id=str(evidence.get("record_id")),
            return_join_identity=None,
        )

    return_join_identity = derive_federated_return_join_identity_v1(
        surface_execution_identity=surface_execution_identity,
        optimization_experiment_evidence_digest=content_hash,
    )

    return _join_payload(
        status=JOIN_STATUS_COMPLETE,
        reason="FEDERATED_OFFLINE_EVIDENCE_RETURN_JOIN_ONLY_NOT_M4_NOT_LEARNED",
        surface_execution_identity=surface_execution_identity,
        evidence_digest=content_hash,
        record_id=str(evidence.get("record_id")),
        return_join_identity=return_join_identity,
        reproducibility_digest=str(evidence.get("reproducibility_digest")),
    )


def _join_payload(
    *,
    status: str,
    reason: str,
    surface_execution_identity: str | None,
    evidence_digest: str | None,
    record_id: str | None,
    return_join_identity: str | None,
    reproducibility_digest: str | None = None,
) -> MappingProxyType[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": RETURN_JOIN_DOMAIN,
        "status": status,
        "reason": reason,
        "join_key_kind": JOIN_KEY_KIND,
        "join_cardinality": JOIN_CARDINALITY,
        "surface_execution_identity": surface_execution_identity,
        "optimization_experiment_evidence_digest": evidence_digest,
        "optimization_experiment_evidence_record_id": record_id,
        "return_join_identity": return_join_identity,
        "reproducibility_digest": reproducibility_digest,
        "federated_projection": True,
        "m4_re_execution": M4_RE_EXECUTION,
        "plane_identity": None,
        "decision_config_ref": DECISION_CONFIG,
        "normative_spec_ref": NORMATIVE_SPEC,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "meta_learning_ingest_performed": META_LEARNING_INGEST_PERFORMED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)


__all__ = [
    "FederatedM5M6ReturnJoinError",
    "FederatedM5M6ReturnJoinRequestV1",
    "JOIN_CARDINALITY",
    "JOIN_KEY_KIND",
    "JOIN_STATUS_COMPLETE",
    "JOIN_STATUS_REJECTED_DUPLICATE",
    "JOIN_STATUS_REJECTED_FOREIGN",
    "JOIN_STATUS_REJECTED_IDENTITY",
    "JOIN_STATUS_REJECTED_PLANE",
    "M4_RE_EXECUTION",
    "SCHEMA_VERSION",
    "derive_federated_return_join_identity_v1",
    "perform_federated_m5_m6_return_join_v1",
]
