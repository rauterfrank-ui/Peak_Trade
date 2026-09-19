"""Self-learning optimization return input v1 — offline evidence ACK boundary only.

Validates optimization experiment evidence for self-learning universe intake.
Does not mutate learning_state_record_v0, run meta-learning, or apply promotion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT,
    SCHEMA_VERSION as OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    UNIVERSE_CLASS_OPTIMIZATION,
    validate_optimization_experiment_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "self_learning_optimization_return_input_v1"
RETURN_INPUT_DOMAIN: Final[str] = (
    "peak_trade.learning.ddo.self_learning_optimization_return_input.v1"
)
DIGEST_ALGORITHM: Final[str] = "sha256"
UNIVERSE_CLASS_SELF_LEARNING: Final[str] = "SELF_LEARNING_UNIVERSE"

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
META_LEARNING_INGEST_PERFORMED: Final[bool] = False

STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT: Final[str] = "ACCEPTED_OFFLINE_EVIDENCE_INPUT"
STATUS_REJECTED_INVALID_EVIDENCE: Final[str] = "REJECTED_INVALID_EVIDENCE"
STATUS_REJECTED_STALE_CONTRACT: Final[str] = "REJECTED_STALE_CONTRACT"
STATUS_REJECTED_OUT_OF_ORDER: Final[str] = "REJECTED_OUT_OF_ORDER"
STATUS_REJECTED_AUTHORITY_BOUNDARY: Final[str] = "REJECTED_AUTHORITY_BOUNDARY"
STATUS_REJECTED_MALFORMED: Final[str] = "REJECTED_MALFORMED"

_LOGGER = logging.getLogger(__name__)


class SelfLearningOptimizationReturnInputError(ValueError):
    """Fail-closed self-learning return input request error."""


@dataclass(frozen=True)
class SelfLearningOptimizationReturnInputRequestV1:
    optimization_experiment_evidence: Mapping[str, Any] | None
    expected_plane_identity: str | None = None
    expected_evidence_schema_version: str | None = OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION
    requested_learning_state_mutation: bool = False
    requested_meta_learning_ingest: bool = False
    requested_promotion: bool = False
    requested_search_feedback: bool = False


def validate_self_learning_optimization_return_input_v1(
    request: SelfLearningOptimizationReturnInputRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_learning_state_mutation:
        raise SelfLearningOptimizationReturnInputError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_meta_learning_ingest:
        raise SelfLearningOptimizationReturnInputError("META_LEARNING_INGEST_FORBIDDEN")
    if request.requested_promotion:
        raise SelfLearningOptimizationReturnInputError("PROMOTION_FORBIDDEN")
    if request.requested_search_feedback:
        raise SelfLearningOptimizationReturnInputError("SEARCH_FEEDBACK_FORBIDDEN")

    if request.expected_evidence_schema_version not in (
        None,
        OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    ):
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_STALE_CONTRACT,
                reason="OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION_MISMATCH",
                evidence_digest=None,
            )
        )

    if request.optimization_experiment_evidence is None:
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_INVALID_EVIDENCE,
                reason="MISSING_OPTIMIZATION_EXPERIMENT_EVIDENCE",
                evidence_digest=None,
            )
        )

    try:
        evidence = validate_optimization_experiment_evidence_v1(
            request.optimization_experiment_evidence
        )
    except Exception as exc:
        _LOGGER.debug("optimization experiment evidence validation failed: %s", exc)
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_MALFORMED,
                reason="OPTIMIZATION_EXPERIMENT_EVIDENCE_VALIDATION_FAILED",
                evidence_digest=None,
            )
        )

    if request.expected_plane_identity is not None:
        if str(evidence.get("plane_identity")) != request.expected_plane_identity:
            return MappingProxyType(
                _ack_payload(
                    status=STATUS_REJECTED_OUT_OF_ORDER,
                    reason="PLANE_IDENTITY_MISMATCH",
                    evidence_digest=str(evidence.get("content_hash")),
                )
            )

    content_hash = str(evidence.get("content_hash"))
    if not is_valid_sha256_hex(content_hash):
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_MALFORMED,
                reason="EVIDENCE_CONTENT_HASH_INVALID",
                evidence_digest=None,
            )
        )

    if evidence.get("universe_class") != UNIVERSE_CLASS_OPTIMIZATION:
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_AUTHORITY_BOUNDARY,
                reason="EVIDENCE_UNIVERSE_CLASS_NOT_OPTIMIZATION",
                evidence_digest=content_hash,
            )
        )
    if evidence.get("evidence_class") != EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT:
        return MappingProxyType(
            _ack_payload(
                status=STATUS_REJECTED_AUTHORITY_BOUNDARY,
                reason="EVIDENCE_CLASS_NOT_OPTIMIZATION_EXPERIMENT",
                evidence_digest=content_hash,
            )
        )

    return MappingProxyType(
        _ack_payload(
            status=STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
            reason="OFFLINE_EVIDENCE_INPUT_ONLY_NOT_LEARNED_NOT_APPLIED",
            evidence_digest=content_hash,
            plane_identity=str(evidence.get("plane_identity")),
            reproducibility_digest=str(evidence.get("reproducibility_digest")),
            record_id=str(evidence.get("record_id")),
            target_universe_class=UNIVERSE_CLASS_SELF_LEARNING,
        )
    )


def _ack_payload(
    *,
    status: str,
    reason: str,
    evidence_digest: str | None,
    plane_identity: str | None = None,
    reproducibility_digest: str | None = None,
    record_id: str | None = None,
    target_universe_class: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": RETURN_INPUT_DOMAIN,
        "status": status,
        "reason": reason,
        "target_universe_class": target_universe_class,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "meta_learning_ingest_performed": META_LEARNING_INGEST_PERFORMED,
        "optimization_experiment_evidence_digest": evidence_digest,
        "plane_identity": plane_identity,
        "reproducibility_digest": reproducibility_digest,
        "optimization_experiment_evidence_record_id": record_id,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return body
