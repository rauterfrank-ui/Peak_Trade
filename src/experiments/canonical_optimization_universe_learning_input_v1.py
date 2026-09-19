"""Optimization-universe learning input contract v1 (research validation only).

Validates exported productive learning evidence for offline optimization
pipelines. Does not search, rank, promote, mutate config, or join productive
runtime. Does not define optimizable envelopes or parameter spaces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    EVIDENCE_CLASS_LEARNING,
    UNIVERSE_CLASS_SELF_LEARNING,
    validate_learning_evidence_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_optimization_universe_learning_input_v1"
OPTIMIZATION_LEARNING_INPUT_DOMAIN: Final[str] = (
    "peak_trade.canonical_optimization_universe_learning_input.v1"
)
DIGEST_ALGORITHM: Final[str] = "sha256"

OPTIMIZATION_UNIVERSE_PRESENT: Final[bool] = True
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_HAS_RUNTIME_AUTHORITY: Final[bool] = False
OPTIMIZATION_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
OPTIMIZATION_CAN_PROMOTE: Final[bool] = False
OPTIMIZATION_CAN_SUBMIT_ORDER: Final[bool] = False
OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE: Final[bool] = False
OPTIMIZATION_CAN_TRIGGER_SEARCH: Final[bool] = False
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT: Final[str] = "ACCEPTED_OFFLINE_RESEARCH_INPUT"
STATUS_REJECTED_INVALID_EVIDENCE: Final[str] = "REJECTED_INVALID_EVIDENCE"
STATUS_REJECTED_AUTHORITY_BOUNDARY: Final[str] = "REJECTED_AUTHORITY_BOUNDARY"
STATUS_REJECTED_UNSUPPORTED_EVIDENCE_CLASS: Final[str] = "REJECTED_UNSUPPORTED_EVIDENCE_CLASS"

_LOGGER = logging.getLogger(__name__)


class CanonicalOptimizationUniverseLearningInputError(ValueError):
    """Fail-closed malformed optimization learning-input request."""


@dataclass(frozen=True)
class CanonicalOptimizationUniverseLearningInputRequestV1:
    learning_evidence: Mapping[str, Any] | None
    requested_productive_join: bool = False
    requested_auto_search: bool = False
    requested_envelope_mutation: bool = False


def _reject_if_forbidden_flags(
    request: CanonicalOptimizationUniverseLearningInputRequestV1,
) -> None:
    if request.requested_productive_join:
        raise CanonicalOptimizationUniverseLearningInputError("PRODUCTIVE_JOIN_FORBIDDEN")
    if request.requested_auto_search:
        raise CanonicalOptimizationUniverseLearningInputError("AUTO_SEARCH_FORBIDDEN")
    if request.requested_envelope_mutation:
        raise CanonicalOptimizationUniverseLearningInputError("ENVELOPE_MUTATION_FORBIDDEN")


def validate_canonical_optimization_universe_learning_input_v1(
    request: CanonicalOptimizationUniverseLearningInputRequestV1,
) -> MappingProxyType[str, Any]:
    _reject_if_forbidden_flags(request)
    if request.learning_evidence is None:
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_INVALID_EVIDENCE,
                reason="MISSING_LEARNING_EVIDENCE",
                learning_evidence_digest=None,
            )
        )
    raw = request.learning_evidence
    try:
        evidence = validate_learning_evidence_record_v1(raw)
    except Exception as exc:
        _LOGGER.debug("learning evidence validation failed: %s", exc)
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_INVALID_EVIDENCE,
                reason="LEARNING_EVIDENCE_VALIDATION_FAILED",
                learning_evidence_digest=None,
            )
        )
    if evidence.get("universe_class") != UNIVERSE_CLASS_SELF_LEARNING:
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_UNSUPPORTED_EVIDENCE_CLASS,
                reason="UNIVERSE_CLASS_NOT_SELF_LEARNING",
                learning_evidence_digest=str(evidence.get("content_hash")),
            )
        )
    if evidence.get("evidence_class") != EVIDENCE_CLASS_LEARNING:
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_UNSUPPORTED_EVIDENCE_CLASS,
                reason="EVIDENCE_CLASS_NOT_LEARNING",
                learning_evidence_digest=str(evidence.get("content_hash")),
            )
        )
    if evidence.get("productive_authority") != "NONE":
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_AUTHORITY_BOUNDARY,
                reason="LEARNING_EVIDENCE_PRODUCTIVE_AUTHORITY_NOT_NONE",
                learning_evidence_digest=str(evidence.get("content_hash")),
            )
        )
    digest = str(evidence.get("content_hash"))
    if not is_valid_sha256_hex(digest):
        return MappingProxyType(
            _result_payload(
                status=STATUS_REJECTED_INVALID_EVIDENCE,
                reason="LEARNING_EVIDENCE_DIGEST_INVALID",
                learning_evidence_digest=None,
            )
        )
    return MappingProxyType(
        _result_payload(
            status=STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
            reason="OFFLINE_RESEARCH_INPUT_ONLY",
            learning_evidence_digest=digest,
            source_learning_state_record_ref=str(evidence["source_learning_state_record_ref"]),
            state_scope_id=str(evidence["state_scope_id"]),
            state_version=int(evidence["state_version"]),
        )
    )


def _result_payload(
    *,
    status: str,
    reason: str,
    learning_evidence_digest: str | None,
    source_learning_state_record_ref: str | None = None,
    state_scope_id: str | None = None,
    state_version: int | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZATION_LEARNING_INPUT_DOMAIN,
        "status": status,
        "reason": reason,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "optimizable_envelope_defined": False,
        "learning_evidence_digest": learning_evidence_digest,
        "source_learning_state_record_ref": source_learning_state_record_ref,
        "state_scope_id": state_scope_id,
        "state_version": state_version,
    }
    body["result_digest"] = compute_content_sha256(body)
    return body
