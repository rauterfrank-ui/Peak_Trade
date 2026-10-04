"""Fail-closed parsing entrypoints for GVEF contracts."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from src.evaluation.golden_vectors.contracts.enums import EvidenceBundleLifecycleState
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError, SCHEMA_FAILURE
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    CapitalRiskCrsSizingEvidenceBundleV1,
    ConstraintMatrixV1,
    CorpusManifestV1,
    DecisionDeltaManifestV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    EvidenceBundleV1,
    InvariantResultV1,
    MetricResultV1,
    PromotionEvidenceEnvelopeV1,
    ProtectedDigestManifestV1,
    ProtectedSemanticDigestsV1,
    RankingDeltaManifestV1,
    RankingUniverseManifestV1,
    RunManifestV1,
    VectorManifestV1,
)

T = TypeVar("T", bound=BaseModel)


def _parse(model_cls: type[T], payload: dict[str, Any]) -> T:
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        raise GvefSchemaError(str(exc), field=SCHEMA_FAILURE) from exc


def parse_run_manifest_v1(payload: dict[str, Any]) -> RunManifestV1:
    return _parse(RunManifestV1, payload)


def parse_vector_manifest_v1(payload: dict[str, Any]) -> VectorManifestV1:
    return _parse(VectorManifestV1, payload)


def parse_corpus_manifest_v1(payload: dict[str, Any]) -> CorpusManifestV1:
    return _parse(CorpusManifestV1, payload)


def parse_constraint_matrix_v1(payload: dict[str, Any]) -> ConstraintMatrixV1:
    return _parse(ConstraintMatrixV1, payload)


def parse_domain_evaluation_context_v1(payload: dict[str, Any]) -> DomainEvaluationContextV1:
    return _parse(DomainEvaluationContextV1, payload)


def parse_domain_evaluation_result_v1(payload: dict[str, Any]) -> DomainEvaluationResultV1:
    return _parse(DomainEvaluationResultV1, payload)


def parse_metric_result_v1(payload: dict[str, Any]) -> MetricResultV1:
    return _parse(MetricResultV1, payload)


def parse_invariant_result_v1(payload: dict[str, Any]) -> InvariantResultV1:
    return _parse(InvariantResultV1, payload)


def parse_boundary_result_v1(payload: dict[str, Any]) -> BoundaryResultV1:
    return _parse(BoundaryResultV1, payload)


def parse_protected_digest_manifest_v1(payload: dict[str, Any]) -> ProtectedDigestManifestV1:
    return _parse(ProtectedDigestManifestV1, payload)


def parse_protected_semantic_digests_v1(payload: dict[str, Any]) -> ProtectedSemanticDigestsV1:
    return _parse(ProtectedSemanticDigestsV1, payload)


def parse_decision_delta_manifest_v1(payload: dict[str, Any]) -> DecisionDeltaManifestV1:
    return _parse(DecisionDeltaManifestV1, payload)


def parse_ranking_universe_manifest_v1(payload: dict[str, Any]) -> RankingUniverseManifestV1:
    return _parse(RankingUniverseManifestV1, payload)


def parse_ranking_delta_manifest_v1(payload: dict[str, Any]) -> RankingDeltaManifestV1:
    return _parse(RankingDeltaManifestV1, payload)


def parse_capital_risk_crs_sizing_evidence_bundle_v1(
    payload: dict[str, Any],
) -> CapitalRiskCrsSizingEvidenceBundleV1:
    return _parse(CapitalRiskCrsSizingEvidenceBundleV1, payload)


def parse_evidence_bundle_v1(payload: dict[str, Any]) -> EvidenceBundleV1:
    return _parse(EvidenceBundleV1, payload)


def parse_promotion_evidence_envelope_v1(payload: dict[str, Any]) -> PromotionEvidenceEnvelopeV1:
    return _parse(PromotionEvidenceEnvelopeV1, payload)


def validate_evidence_bundle_lifecycle_state(value: str) -> EvidenceBundleLifecycleState:
    try:
        return EvidenceBundleLifecycleState(value)
    except ValueError as exc:
        raise GvefSchemaError("unknown evidence bundle lifecycle state") from exc


def evidence_complete_not_implied_by_schema() -> bool:
    """BWP-1: schema construction does not imply EVIDENCE_COMPLETE."""
    return True
