"""META_EVIDENCE_V1 — typed routing envelope over meta_learning_evidence_v1 (AUTHORITY=NONE).

Dual-routing classification only; does not authorize promotion, search execution,
learning-state mutation, or external effect.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    validate_meta_learning_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "meta_evidence_v1"
META_EVIDENCE_DOMAIN: Final[str] = "peak_trade.learning.ddo.meta_evidence.v1"
PERMITTED_USE_RESEARCH_ONLY: Final[str] = "RESEARCH_ONLY"
PROVENANCE_LINEAGE_REF_KEY: Final[str] = "learning_representation_lineage_ref"


class SemanticRoutingClass(str, Enum):
    RESEARCH_CHOICE = "RESEARCH_CHOICE"
    LEARNING_REPRESENTATION = "LEARNING_REPRESENTATION"
    UNKNOWN = "UNKNOWN"
    MIXED = "MIXED"


class IntendedSemanticConsumer(str, Enum):
    OPTIMIZATION_RESEARCH = "OPTIMIZATION_RESEARCH"
    LEARNING_RESEARCH = "LEARNING_RESEARCH"
    NONE_FAIL_CLOSED = "NONE_FAIL_CLOSED"


_ROUTING_TO_CONSUMER: Final[Mapping[str, str]] = MappingProxyType(
    {
        SemanticRoutingClass.RESEARCH_CHOICE.value: IntendedSemanticConsumer.OPTIMIZATION_RESEARCH.value,
        SemanticRoutingClass.LEARNING_REPRESENTATION.value: (
            IntendedSemanticConsumer.LEARNING_RESEARCH.value
        ),
        SemanticRoutingClass.UNKNOWN.value: IntendedSemanticConsumer.NONE_FAIL_CLOSED.value,
        SemanticRoutingClass.MIXED.value: IntendedSemanticConsumer.NONE_FAIL_CLOSED.value,
    }
)

_FAIL_CLOSED_CLASSES: Final[frozenset[str]] = frozenset(
    {SemanticRoutingClass.UNKNOWN.value, SemanticRoutingClass.MIXED.value}
)


class MetaEvidenceValidationError(ValueError):
    """Fail-closed META_EVIDENCE_V1 validation."""


def derive_meta_evidence_record_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"ddo.meta_evidence.{digest[:48]}"


def derive_route_identity_v1(*, meta_evidence_record_id: str, semantic_routing_class: str) -> str:
    return compute_content_sha256(
        {
            "meta_evidence_record_id": meta_evidence_record_id,
            "semantic_routing_class": semantic_routing_class,
            "schema_version": SCHEMA_VERSION,
        }
    )


def _validate_routing_class(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise MetaEvidenceValidationError("SEMANTIC_ROUTING_CLASS_REQUIRED")
    value = raw.strip()
    if value not in {item.value for item in SemanticRoutingClass}:
        raise MetaEvidenceValidationError("SEMANTIC_ROUTING_CLASS_UNSUPPORTED")
    return value


def assert_routing_class_lineage_binding_v1(
    *,
    meta_learning_evidence: Mapping[str, Any],
    semantic_routing_class: str,
) -> None:
    """Explicit lineage binding; no inference from feature availability."""
    if semantic_routing_class == SemanticRoutingClass.RESEARCH_CHOICE.value:
        digest = meta_learning_evidence.get("source_optimization_experiment_evidence_digest")
        if not isinstance(digest, str) or not digest.strip():
            raise MetaEvidenceValidationError("RESEARCH_CHOICE_REQUIRES_OPTIMIZATION_LINEAGE")
        return
    if semantic_routing_class == SemanticRoutingClass.LEARNING_REPRESENTATION.value:
        provenance = meta_learning_evidence.get("provenance")
        if not isinstance(provenance, Mapping):
            raise MetaEvidenceValidationError("LEARNING_REPRESENTATION_REQUIRES_PROVENANCE")
        ref = provenance.get(PROVENANCE_LINEAGE_REF_KEY)
        if not isinstance(ref, str) or not ref.strip():
            raise MetaEvidenceValidationError("LEARNING_REPRESENTATION_LINEAGE_REF_REQUIRED")
        return
    if semantic_routing_class in _FAIL_CLOSED_CLASSES:
        return
    raise MetaEvidenceValidationError("ROUTING_CLASS_UNRESOLVED")


def build_meta_evidence_v1(
    *,
    meta_learning_evidence: Mapping[str, Any],
    semantic_routing_class: str,
    classification_provenance: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    """Materialize META_EVIDENCE_V1 with explicit routing class (fail-closed)."""
    routing_class = _validate_routing_class(semantic_routing_class)
    nested = validate_meta_learning_evidence_v1(meta_learning_evidence)
    assert_routing_class_lineage_binding_v1(
        meta_learning_evidence=nested,
        semantic_routing_class=routing_class,
    )
    intended_consumer = _ROUTING_TO_CONSUMER[routing_class]
    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "meta_learning_evidence_schema_version": META_LEARNING_EVIDENCE_SCHEMA_VERSION,
        "source_meta_evidence_id": str(nested["meta_evidence_id"]),
        "source_meta_reproducibility_digest": str(nested["reproducibility_digest"]),
        "semantic_routing_class": routing_class,
        "intended_semantic_consumer": intended_consumer,
        "permitted_use_classification": PERMITTED_USE_RESEARCH_ONLY,
        "classification_provenance": dict(classification_provenance or {}),
    }
    record_id = derive_meta_evidence_record_id_v1(identity_body=identity_body)
    route_identity = derive_route_identity_v1(
        meta_evidence_record_id=record_id,
        semantic_routing_class=routing_class,
    )
    body = {
        **identity_body,
        "domain": META_EVIDENCE_DOMAIN,
        "meta_evidence_record_id": record_id,
        "route_identity": route_identity,
        "meta_learning_evidence": dict(nested),
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "automatic_consumer_feedback_authorized": routing_class not in _FAIL_CLOSED_CLASSES,
        "meta_broadcast_forbidden": True,
    }
    digest = compute_content_sha256(
        {key: body[key] for key in sorted(body) if key != "content_digest"}
    )
    if not is_valid_sha256_hex_v0(digest):
        raise MetaEvidenceValidationError("CONTENT_DIGEST_INVALID")
    body["content_digest"] = digest
    return validate_meta_evidence_v1(body)


def validate_meta_evidence_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise MetaEvidenceValidationError("META_EVIDENCE_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MetaEvidenceValidationError("META_EVIDENCE_SCHEMA_MISMATCH")
    if payload.get("meta_evidence_authority") != META_EVIDENCE_AUTHORITY:
        raise MetaEvidenceValidationError("META_EVIDENCE_AUTHORITY_MUST_BE_NONE")
    routing_class = _validate_routing_class(payload.get("semantic_routing_class"))
    expected_consumer = _ROUTING_TO_CONSUMER[routing_class]
    if payload.get("intended_semantic_consumer") != expected_consumer:
        raise MetaEvidenceValidationError("INTENDED_SEMANTIC_CONSUMER_MISMATCH")
    if payload.get("permitted_use_classification") != PERMITTED_USE_RESEARCH_ONLY:
        raise MetaEvidenceValidationError("PERMITTED_USE_MUST_BE_RESEARCH_ONLY")
    if payload.get("meta_broadcast_forbidden") is not True:
        raise MetaEvidenceValidationError("META_BROADCAST_MUST_BE_FORBIDDEN")
    nested_raw = payload.get("meta_learning_evidence")
    if not isinstance(nested_raw, Mapping):
        raise MetaEvidenceValidationError("NESTED_META_LEARNING_EVIDENCE_REQUIRED")
    nested = validate_meta_learning_evidence_v1(nested_raw)
    if str(payload.get("source_meta_evidence_id")) != str(nested["meta_evidence_id"]):
        raise MetaEvidenceValidationError("SOURCE_META_EVIDENCE_ID_MISMATCH")
    record_id = str(payload.get("meta_evidence_record_id") or "")
    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "meta_learning_evidence_schema_version": payload.get(
            "meta_learning_evidence_schema_version"
        ),
        "source_meta_evidence_id": str(nested["meta_evidence_id"]),
        "source_meta_reproducibility_digest": str(nested["reproducibility_digest"]),
        "semantic_routing_class": routing_class,
        "intended_semantic_consumer": expected_consumer,
        "permitted_use_classification": PERMITTED_USE_RESEARCH_ONLY,
        "classification_provenance": dict(payload.get("classification_provenance") or {}),
    }
    if record_id != derive_meta_evidence_record_id_v1(identity_body=identity_body):
        raise MetaEvidenceValidationError("META_EVIDENCE_RECORD_ID_MISMATCH")
    route_identity = str(payload.get("route_identity") or "")
    if route_identity != derive_route_identity_v1(
        meta_evidence_record_id=record_id,
        semantic_routing_class=routing_class,
    ):
        raise MetaEvidenceValidationError("ROUTE_IDENTITY_MISMATCH")
    digest = payload.get("content_digest")
    if not is_valid_sha256_hex_v0(str(digest or "")):
        raise MetaEvidenceValidationError("CONTENT_DIGEST_INVALID")
    auto = payload.get("automatic_consumer_feedback_authorized")
    if routing_class in _FAIL_CLOSED_CLASSES:
        if auto is not False:
            raise MetaEvidenceValidationError("FAIL_CLOSED_CLASS_MUST_NOT_AUTHORIZE_FEEDBACK")
    elif auto is not True:
        raise MetaEvidenceValidationError("ROUTED_CLASS_MUST_AUTHORIZE_TYPED_FEEDBACK")
    return MappingProxyType(dict(payload))


__all__ = [
    "META_EVIDENCE_DOMAIN",
    "PROVENANCE_LINEAGE_REF_KEY",
    "SCHEMA_VERSION",
    "IntendedSemanticConsumer",
    "MetaEvidenceValidationError",
    "PERMITTED_USE_RESEARCH_ONLY",
    "SemanticRoutingClass",
    "assert_routing_class_lineage_binding_v1",
    "build_meta_evidence_v1",
    "derive_meta_evidence_record_id_v1",
    "derive_route_identity_v1",
    "validate_meta_evidence_v1",
]
