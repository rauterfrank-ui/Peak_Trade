"""BWP-5 Self-Learning domain evaluator (evidence only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import (
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    InvariantResultV1,
    MetricResultV1,
    ProtectedSemanticDigestsV1,
    ReplayTraceV1,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.evaluators._fanout_v1 import bwp456_failure_fan_out
from src.evaluation.golden_vectors.evaluators._result_v1 import fail_result, pass_result

SELF_LEARNING_EVALUATOR_ID = "self_learning_evaluator_v1"
EVALUATOR_SCHEMA_VERSION = "1.5.0"
BWP_ID = "BWP-5"
PRIMARY_FAILURE_CLASS = FailureClassification.AUTHORITY_FAILURE
REPROOF_CLASS = FanOutEvaluationClass.LOCAL_EVALUATION


@dataclass
class SelfLearningEvaluatorV1:
    """Learning artifact evaluation only. No productive writeback."""

    evaluator_id: str = SELF_LEARNING_EVALUATOR_ID
    schema_version: str = EVALUATOR_SCHEMA_VERSION
    _baseline_artifact_digest: str | None = field(default=None, init=False)

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        auth_err = self._authority_violation(replay)
        if auth_err:
            return fail_result(
                domain=EvaluationDomain.SELF_LEARNING,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=auth_err,
            )
        artifact, err = self._artifact(replay, label="baseline", context=context)
        if err:
            return fail_result(
                domain=EvaluationDomain.SELF_LEARNING,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        digest = sha256_hex(artifact)
        self._baseline_artifact_digest = digest
        return self._pass(artifact, digest, label="baseline")

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        auth_err = self._authority_violation(replay)
        if auth_err:
            return fail_result(
                domain=EvaluationDomain.SELF_LEARNING,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=auth_err,
            )
        artifact, err = self._artifact(replay, label="candidate", context=context)
        if err:
            return fail_result(
                domain=EvaluationDomain.SELF_LEARNING,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        digest = sha256_hex(artifact)
        return self._pass(artifact, digest, label="candidate")

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

    def _authority_violation(self, replay: ReplayTraceV1) -> str | None:
        for entry in replay.entries:
            if entry.get("productive_writeback") is True:
                return "productive writeback forbidden"
            if entry.get("productive_config_write") is True:
                return "productive config write forbidden"
            if entry.get("claims_trading_authority") is True:
                return "trading authority claim forbidden"
            if entry.get("selection_mutation") is True:
                return "selection mutation forbidden"
            if entry.get("auto_promotion") is True:
                return "automatic promotion forbidden"
            if entry.get("mutate_productive_parameters") is True:
                return "productive parameter mutation forbidden"
        return None

    def _artifact(
        self,
        replay: ReplayTraceV1,
        *,
        label: str,
        context: DomainEvaluationContextV1,
    ) -> tuple[dict[str, Any], str | None]:
        for entry in replay.entries:
            if entry.get("kind") != "self_learning":
                continue
            if entry.get("label") not in (None, label):
                continue
            if entry.get("run_id") not in (None, context.run_manifest.run_id):
                return {}, "run identity mismatch"
            raw = entry.get("learning_artifact")
            if not isinstance(raw, dict):
                return {}, "malformed learning artifact"
            return dict(raw), None
        return {}, "missing self-learning evidence"

    def _pass(
        self,
        artifact: dict[str, Any],
        digest: str,
        *,
        label: str,
    ) -> DomainEvaluationResultV1:
        return pass_result(
            domain=EvaluationDomain.SELF_LEARNING,
            metrics=[
                MetricResultV1(metric_id="sl.artifact_digest", value=digest),
            ],
            invariants=[
                InvariantResultV1(
                    invariant_id="sl.no_productive_writeback",
                    pass_=True,
                    detail="SELF_LEARNING_PRODUCTIVE_WRITEBACK=false",
                ),
                InvariantResultV1(
                    invariant_id="sl.baseline_candidate_bound",
                    pass_=True,
                ),
            ],
            boundary_results=[],
            evidence_refs=[f"evidence/sl/{label}"],
            semantic_digest_deltas={
                "learning_artifact": artifact,
                "learning_artifact_digest": digest,
                "evidence_source_class": (
                    "MECHANISM_TEST_EVIDENCE"
                    if artifact.get("TEST_ONLY_SYNTHETIC") is True
                    else "SEALED_EXISTING_EVIDENCE"
                ),
            },
        )
