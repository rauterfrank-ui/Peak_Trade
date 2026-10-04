"""Narrow BWP-2 orchestration protocols (no domain trading logic)."""

from __future__ import annotations

from typing import Protocol

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    DecisionDeltaManifestV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    EvidenceBundleV1,
    PromotionEvidenceEnvelopeV1,
    ProtectedSemanticDigestsV1,
    ReplayTraceV1,
    RunManifestV1,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PromotionAdaptRequestV1,
)


class PreConstraintGateV1(Protocol):
    def evaluate_pre(self, run: RunManifestV1) -> tuple[bool, list[BoundaryResultV1]]: ...


class PostConstraintGateV1(Protocol):
    def evaluate_post(
        self,
        *,
        run: RunManifestV1,
        post_gate_pass_required: bool,
        protected_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[bool, list[BoundaryResultV1]]: ...


class ReplayAdapterV1(Protocol):
    def replay(
        self, *, run: RunManifestV1, context: DomainEvaluationContextV1
    ) -> ReplayTraceV1: ...


class CorpusIntegrityGateV1(Protocol):
    def evaluate_bound_corpus(
        self,
        *,
        run: RunManifestV1,
        context: DomainEvaluationContextV1,
    ) -> None: ...


class PromotionEvidenceAdapterProtocolV1(Protocol):
    def adapt(
        self,
        *,
        bundle: EvidenceBundleV1,
        request: PromotionAdaptRequestV1,
    ) -> PromotionEvidenceEnvelopeV1 | None: ...


class DomainEvaluatorV1(Protocol):
    """Test doubles only in BWP-2; TRADING_AUTHORITY=NONE."""

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1: ...

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1: ...

    def protected_digests_baseline(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1: ...

    def protected_digests_candidate(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1: ...

    def failure_fan_out(self, failure: FailureClassification) -> FanOutEvaluationClass: ...


class ComparatorV1(Protocol):
    def compare(
        self,
        *,
        baseline: DomainEvaluationResultV1,
        candidate: DomainEvaluationResultV1,
        baseline_digests: ProtectedSemanticDigestsV1,
        candidate_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[DecisionDeltaManifestV1, ProtectedSemanticDigestsV1]: ...


class DeltaManifestBuilderV1(Protocol):
    def build(self, *, comparator_delta: DecisionDeltaManifestV1) -> DecisionDeltaManifestV1: ...


class EvidenceBundleBuilderV1(Protocol):
    def build(
        self,
        *,
        run: RunManifestV1,
        delta: DecisionDeltaManifestV1,
        protected_digests: ProtectedSemanticDigestsV1,
        boundary_results: list[BoundaryResultV1],
        post_gate_pass: bool,
    ) -> EvidenceBundleV1: ...


class EvidenceRegistryV1(Protocol):
    def register(self, bundle: EvidenceBundleV1) -> str: ...
