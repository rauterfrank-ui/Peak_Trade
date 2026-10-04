"""GVEF V1.5 deterministic generic runner orchestration (BWP-2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from src.evaluation.golden_vectors.contracts.enums import (
    DomainVerdict,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    DecisionDeltaManifestV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    EvidenceBundleV1,
    PromotionEvidenceEnvelopeV1,
    ProtectedSemanticDigestsV1,
    ReplayTraceV1,
    RunManifestV1,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.promotion.errors import GvefPromotionAuthorityError
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PassThroughPromotionEvidenceAdapterV1,
    PromotionAdaptRequestV1,
)
from src.evaluation.golden_vectors.contracts.validation import parse_run_manifest_v1
from src.evaluation.golden_vectors.runner.digest_projection import (
    protected_semantic_digests_digest,
    run_manifest_protected_digest_hex,
)
from src.evaluation.golden_vectors.runner.errors import GvefNonDeterminismError, GvefRunnerError
from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError
from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError
from src.evaluation.golden_vectors.corpus.gate_v1 import PassThroughCorpusIntegrityGateV1
from src.evaluation.golden_vectors.runner.protocols import (
    ComparatorV1,
    CorpusIntegrityGateV1,
    DeltaManifestBuilderV1,
    DomainEvaluatorV1,
    EvidenceBundleBuilderV1,
    EvidenceRegistryV1,
    PostConstraintGateV1,
    PreConstraintGateV1,
    PromotionEvidenceAdapterProtocolV1,
    ReplayAdapterV1,
)
from src.evaluation.golden_vectors.runner.states import RunnerState, transition


@dataclass(frozen=True)
class GvefRunRequestV1:
    evaluation_context: DomainEvaluationContextV1


@dataclass
class GvefRunnerDependenciesV1:
    pre_gate: PreConstraintGateV1
    post_gate: PostConstraintGateV1
    replay_adapter: ReplayAdapterV1
    evaluator: DomainEvaluatorV1
    comparator: ComparatorV1
    delta_builder: DeltaManifestBuilderV1
    evidence_builder: EvidenceBundleBuilderV1
    registry: EvidenceRegistryV1
    corpus_gate: CorpusIntegrityGateV1 = field(default_factory=PassThroughCorpusIntegrityGateV1)
    promotion_adapter: PromotionEvidenceAdapterProtocolV1 = field(
        default_factory=PassThroughPromotionEvidenceAdapterV1
    )


@dataclass
class GvefRunRecordV1:
    state: RunnerState
    state_history: list[RunnerState] = field(default_factory=list)
    run_manifest: RunManifestV1 | None = None
    replay_trace: ReplayTraceV1 | None = None
    baseline_result: DomainEvaluationResultV1 | None = None
    candidate_result: DomainEvaluationResultV1 | None = None
    baseline_result_digest: str | None = None
    delta_manifest: DecisionDeltaManifestV1 | None = None
    protected_digests: ProtectedSemanticDigestsV1 | None = None
    evidence_bundle: EvidenceBundleV1 | None = None
    registry_ref: str | None = None
    failure_classification: FailureClassification | None = None
    fan_out_evaluation_class: FanOutEvaluationClass | None = None
    protected_output_digest: str | None = None
    promotion_envelope: PromotionEvidenceEnvelopeV1 | None = None

    def __post_init__(self) -> None:
        if not self.state_history:
            self.state_history = [self.state]


def evidence_complete(record: GvefRunRecordV1) -> bool:
    return (
        record.state is RunnerState.REGISTERED
        and record.evidence_bundle is not None
        and record.evidence_bundle.post_constraint_gate_pass is True
    )


@dataclass
class GenericRunnerV1:
    BWP_ID: ClassVar[str] = "BWP-2"
    PRIMARY_FAILURE_CLASS: ClassVar[str] = "NON_DETERMINISM"
    REPROOF_CLASS: ClassVar[str] = "WHOLE_SYSTEM_REPROOF"
    integrated_fail_closed_reproof: FanOutEvaluationClass | None = None

    def execute(
        self,
        request: GvefRunRequestV1,
        deps: GvefRunnerDependenciesV1,
        *,
        verify_deterministic_replay: bool = True,
    ) -> GvefRunRecordV1:
        record = GvefRunRecordV1(state=RunnerState.CREATED)
        try:
            self._advance(record, RunnerState.BOUND)
            run = parse_run_manifest_v1(
                request.evaluation_context.run_manifest.model_dump(mode="json", by_alias=True)
            )
            record.run_manifest = run

            try:
                deps.corpus_gate.evaluate_bound_corpus(run=run, context=request.evaluation_context)
            except GvefCorpusDriftError:
                return self._fail(
                    record,
                    FailureClassification.CORPUS_DRIFT,
                    FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF,
                )

            pre_ok, pre_boundaries = deps.pre_gate.evaluate_pre(run)
            if not pre_ok:
                return self._fail(
                    record,
                    FailureClassification.CONSTRAINT_FAILURE,
                    run.fan_out_evaluation_class,
                )
            self._advance(record, RunnerState.PRE_CONSTRAINT_CHECKED)

            self._advance(record, RunnerState.REPLAY_READY)
            replay = deps.replay_adapter.replay(run=run, context=request.evaluation_context)
            record.replay_trace = replay
            self._advance(record, RunnerState.REPLAYED)

            baseline = deps.evaluator.evaluate_baseline(
                context=request.evaluation_context, replay=replay
            )
            if baseline.verdict is DomainVerdict.FAIL:
                fc = baseline.failure_classification or FailureClassification.INVARIANT_FAILURE
                return self._fail(record, fc, deps.evaluator.failure_fan_out(fc))
            record.baseline_result = baseline
            record.baseline_result_digest = contract_digest_hex(baseline)

            candidate = deps.evaluator.evaluate_candidate(
                context=request.evaluation_context, replay=replay
            )
            if candidate.verdict is DomainVerdict.FAIL:
                fc = candidate.failure_classification or FailureClassification.INVARIANT_FAILURE
                return self._fail(record, fc, deps.evaluator.failure_fan_out(fc))
            if contract_digest_hex(baseline) != record.baseline_result_digest:
                return self._fail(
                    record,
                    FailureClassification.INVARIANT_FAILURE,
                    run.fan_out_evaluation_class,
                )
            record.candidate_result = candidate
            self._advance(record, RunnerState.EVALUATED)

            if verify_deterministic_replay:
                self._verify_deterministic_replay(
                    request=request,
                    deps=deps,
                    run=run,
                    replay=replay,
                    baseline_digest=record.baseline_result_digest,
                )

            baseline_d = deps.evaluator.protected_digests_baseline(
                context=request.evaluation_context
            )
            candidate_d = deps.evaluator.protected_digests_candidate(
                context=request.evaluation_context
            )
            delta, merged_d = deps.comparator.compare(
                baseline=baseline,
                candidate=candidate,
                baseline_digests=baseline_d,
                candidate_digests=candidate_d,
            )
            record.protected_digests = merged_d
            self._advance(record, RunnerState.COMPARED)

            built_delta = deps.delta_builder.build(comparator_delta=delta)
            record.delta_manifest = built_delta
            self._advance(record, RunnerState.DELTA_MANIFEST_BUILT)

            post_ok, post_boundaries = deps.post_gate.evaluate_post(
                run=run,
                post_gate_pass_required=True,
                protected_digests=merged_d,
            )
            if not post_ok:
                return self._fail(
                    record,
                    FailureClassification.CONSTRAINT_FAILURE,
                    run.fan_out_evaluation_class,
                )
            self._advance(record, RunnerState.POST_CONSTRAINT_CHECKED)

            bundle = deps.evidence_builder.build(
                run=run,
                delta=built_delta,
                protected_digests=merged_d,
                boundary_results=pre_boundaries + post_boundaries,
                post_gate_pass=True,
                domain_evaluation_result=record.candidate_result,
            )
            record.evidence_bundle = bundle
            self._advance(record, RunnerState.EVIDENCE_BUILT)

            record.registry_ref = deps.registry.register(bundle)
            self._advance(record, RunnerState.REGISTERED)
            try:
                envelope = deps.promotion_adapter.adapt(
                    bundle=bundle,
                    request=PromotionAdaptRequestV1(
                        evidence_bundle_ref=record.registry_ref or f"registry/{run.run_id}",
                        governance_handoff_timestamp=run.created_at_utc,
                    ),
                )
                if envelope is not None:
                    record.promotion_envelope = envelope
            except GvefPromotionAuthorityError:
                return self._fail(
                    record,
                    FailureClassification.AUTHORITY_FAILURE,
                    FanOutEvaluationClass.LOCAL_EVALUATION,
                )
            record.fan_out_evaluation_class = run.fan_out_evaluation_class
            record.protected_output_digest = self._protected_output_digest(record)
            return record
        except GvefNonDeterminismError:
            return self._fail(
                record,
                FailureClassification.NON_DETERMINISM,
                FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF,
            )
        except GvefProtectedDigestDriftError as exc:
            return self._fail(
                record,
                FailureClassification.PROTECTED_DIGEST_DRIFT,
                exc.reproof_class,
            )
        except (GvefRunnerError, ValueError):
            fan = (
                record.run_manifest.fan_out_evaluation_class
                if record.run_manifest
                else FanOutEvaluationClass.LOCAL_EVALUATION
            )
            return self._fail(record, FailureClassification.SCHEMA_FAILURE, fan)

    def _verify_deterministic_replay(
        self,
        *,
        request: GvefRunRequestV1,
        deps: GvefRunnerDependenciesV1,
        run: RunManifestV1,
        replay: ReplayTraceV1,
        baseline_digest: str,
    ) -> None:
        first_manifest_digest = run_manifest_protected_digest_hex(run)
        baseline2 = deps.evaluator.evaluate_baseline(
            context=request.evaluation_context, replay=replay
        )
        if contract_digest_hex(baseline2) != baseline_digest:
            raise GvefNonDeterminismError("baseline replay digest mismatch")
        _ = deps.evaluator.evaluate_candidate(context=request.evaluation_context, replay=replay)
        second_manifest_digest = run_manifest_protected_digest_hex(run)
        if first_manifest_digest != second_manifest_digest:
            raise GvefNonDeterminismError("run manifest protected digest drift")

    def _protected_output_digest(self, record: GvefRunRecordV1) -> str:
        payload: dict[str, Any] = {
            "states": [s.value for s in record.state_history],
            "run_manifest_digest": (
                run_manifest_protected_digest_hex(record.run_manifest)
                if record.run_manifest
                else ""
            ),
            "baseline_result_digest": record.baseline_result_digest or "",
            "delta_digest": (
                record.delta_manifest.digest if record.delta_manifest is not None else ""
            ),
            "protected_digests": (
                protected_semantic_digests_digest(record.protected_digests)
                if record.protected_digests
                else ""
            ),
            "evidence_digest": (
                record.evidence_bundle.evidence_digest if record.evidence_bundle else ""
            ),
        }
        from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

        return sha256_hex(payload)

    def _advance(self, record: GvefRunRecordV1, target: RunnerState) -> None:
        record.state = transition(record.state, target)
        record.state_history.append(record.state)

    def _fail(
        self,
        record: GvefRunRecordV1,
        failure: FailureClassification,
        fan_out: FanOutEvaluationClass,
    ) -> GvefRunRecordV1:
        if record.state is not RunnerState.FAILED:
            record.state = RunnerState.FAILED
            record.state_history.append(RunnerState.FAILED)
        record.failure_classification = failure
        effective_fan = fan_out
        if self.integrated_fail_closed_reproof is not None:
            effective_fan = self.integrated_fail_closed_reproof
        if failure is FailureClassification.NON_DETERMINISM:
            record.fan_out_evaluation_class = FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
        else:
            record.fan_out_evaluation_class = effective_fan
        record.protected_output_digest = self._protected_output_digest(record)
        return record
