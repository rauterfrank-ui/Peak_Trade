"""Deterministic in-memory BWP-2 test doubles (AUTHORITY=NONE)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.evaluation.golden_vectors.contracts.enums import (
    DigestVerdict,
    DomainVerdict,
    EvaluationDomain,
    ExternalPromotionStatus,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.evaluators._fanout_v1 import bwp456_failure_fan_out
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    DecisionDeltaManifestV1,
    DecisionDeltaV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    EvidenceBundleV1,
    InvariantResultV1,
    MetricResultV1,
    ProtectedDigestEntryV1,
    ProtectedSemanticDigestsV1,
    ReplayTraceV1,
    RunManifestV1,
    contract_to_canonical_mapping,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    evidence_bundle_semantic_digest,
)
from src.evaluation.golden_vectors.runner.errors import GvefNonDeterminismError


@dataclass
class DeterministicPreGateV1:
    should_pass: bool = True

    def evaluate_pre(self, run: RunManifestV1) -> tuple[bool, list[BoundaryResultV1]]:
        _ = run
        br = BoundaryResultV1(
            edge_id="PRE_GATE",
            pass_=self.should_pass,
            producer="gvef.pre_constraint_gate_v1",
            consumer="generic_runner",
            current_verdict="PROVEN_CURRENT",
        )
        return self.should_pass, [br]


@dataclass
class DeterministicPostGateV1:
    should_pass: bool = True

    def evaluate_post(
        self,
        *,
        run: RunManifestV1,
        post_gate_pass_required: bool,
        protected_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[bool, list[BoundaryResultV1]]:
        _ = (run, post_gate_pass_required, protected_digests)
        ok = self.should_pass
        br = BoundaryResultV1(
            edge_id="POST_GATE",
            pass_=ok,
            producer="gvef.post_constraint_gate_v1",
            consumer="generic_runner",
            current_verdict="PROVEN_CURRENT",
        )
        return ok, [br]


@dataclass
class DeterministicReplayAdapterV1:
    def replay(self, *, run: RunManifestV1, context: DomainEvaluationContextV1) -> ReplayTraceV1:
        _ = run
        return context.replay_trace


@dataclass
class DeterministicDomainEvaluatorV1:
    nondeterministic_on_replay: bool = False
    _baseline_pass: int = field(default=0, init=False, repr=False)
    baseline_calls: int = field(default=0, init=False, repr=False)
    candidate_calls: int = field(default=0, init=False, repr=False)

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        self.baseline_calls += 1
        self._baseline_pass += 1
        if self.nondeterministic_on_replay and self._baseline_pass > 1:
            raise GvefNonDeterminismError("evaluator baseline replay mismatch")
        _ = replay
        return self._result(context, suffix="baseline")

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        self.candidate_calls += 1
        _ = replay
        return self._result(context, suffix="candidate", metric_value=2)

    def protected_digests_baseline(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        return context.protected_digest_baseline

    def protected_digests_candidate(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        return context.protected_digest_baseline

    def failure_fan_out(self, failure: FailureClassification) -> FanOutEvaluationClass:
        return bwp456_failure_fan_out(failure)

    def _result(
        self,
        context: DomainEvaluationContextV1,
        *,
        suffix: str,
        metric_value: int = 1,
    ) -> DomainEvaluationResultV1:
        return DomainEvaluationResultV1(
            domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
            verdict=DomainVerdict.PASS,
            metrics=[MetricResultV1(metric_id=f"m.{suffix}", value=metric_value)],
            invariants=[InvariantResultV1(invariant_id="inv.ok", pass_=True)],
            boundary_results=[],
            evidence_refs=[f"evidence/{suffix}"],
        )


@dataclass
class DeterministicComparatorV1:
    def compare(
        self,
        *,
        baseline: DomainEvaluationResultV1,
        candidate: DomainEvaluationResultV1,
        baseline_digests: ProtectedSemanticDigestsV1,
        candidate_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[DecisionDeltaManifestV1, ProtectedSemanticDigestsV1]:
        _ = (baseline, candidate, baseline_digests)
        delta = DecisionDeltaManifestV1(
            deltas=[DecisionDeltaV1(delta_id="d1", before="baseline", after="candidate")],
            digest=sha256_hex({"delta_id": "d1"}),
        )
        return delta, candidate_digests


@dataclass
class DeterministicDeltaBuilderV1:
    def build(self, *, comparator_delta: DecisionDeltaManifestV1) -> DecisionDeltaManifestV1:
        return comparator_delta


@dataclass
class DeterministicEvidenceBuilderV1:
    def build(
        self,
        *,
        run: RunManifestV1,
        delta: DecisionDeltaManifestV1,
        protected_digests: ProtectedSemanticDigestsV1,
        boundary_results: list[BoundaryResultV1],
        post_gate_pass: bool,
    ) -> EvidenceBundleV1:
        _ = (delta, boundary_results)
        bundle_payload = {
            "run_id": run.run_id,
            "experiment_id": run.experiment_id,
            "baseline_sha": run.baseline_sha,
            "candidate_sha": run.candidate_sha,
            "constraint_matrix_version": run.constraint_matrix_version,
            "constraint_matrix_digest": run.constraint_matrix_digest,
            "vector_corpus_version": "1.0.0",
            "vector_corpus_digest": run.seed_set_digest,
            "protected_semantic_digests": contract_to_canonical_mapping(protected_digests),
            "config_digest": run.constraint_matrix_digest,
            "config_provenance": {"source": "stub", "ref": "deterministic"},
            "data_manifest": {
                "data_manifest_id": "data-stub",
                "data_digest": run.seed_set_digest,
            },
            "data_provenance": {"source": "stub", "ref": "deterministic"},
            "seed_set": [42],
            "metric_schema_version": "1.0.0",
            "invariant_results": [{"invariant_id": "i1", "pass": True}],
            "authority_boundary_results": [
                {
                    "edge_id": "POST_GATE",
                    "pass": post_gate_pass,
                    "producer": "gvef",
                    "consumer": "PRE_EXTERNAL",
                    "current_verdict": "PROVEN_CURRENT",
                }
            ],
            "decision_delta_manifest": contract_to_canonical_mapping(delta),
            "fan_out_evaluation_class": run.fan_out_evaluation_class.value,
            "evidence_digest": "0" * 64,
            "promotion_status": ExternalPromotionStatus.EXTERNAL_UNSET.value,
            "post_constraint_gate_pass": post_gate_pass,
        }
        bundle_payload["evidence_digest"] = "0" * 64
        bundle = EvidenceBundleV1.model_validate(bundle_payload)
        bundle_payload["evidence_digest"] = evidence_bundle_semantic_digest(bundle)
        return EvidenceBundleV1.model_validate(bundle_payload)


@dataclass
class InMemoryEvidenceRegistryV1:
    fail_on_duplicate: bool = True
    fail_next_register: bool = False
    _entries: dict[str, EvidenceBundleV1] = field(default_factory=dict)

    def register(self, bundle: EvidenceBundleV1) -> str:
        if self.fail_next_register:
            raise ValueError("registry boundary failure")
        if self.fail_on_duplicate and bundle.run_id in self._entries:
            raise ValueError("duplicate run_id")
        self._entries[bundle.run_id] = bundle
        return f"registry/{bundle.run_id}"


def baseline_result_digest(result: DomainEvaluationResultV1) -> str:
    return contract_digest_hex(result)
