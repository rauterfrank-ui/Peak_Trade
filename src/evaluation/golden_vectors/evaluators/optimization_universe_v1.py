"""BWP-4 Optimization Universe domain evaluator (evidence only)."""

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

OPTIMIZATION_UNIVERSE_EVALUATOR_ID = "optimization_universe_evaluator_v1"
EVALUATOR_SCHEMA_VERSION = "1.5.0"
BWP_ID = "BWP-4"
PRIMARY_FAILURE_CLASS = FailureClassification.INVARIANT_FAILURE
REPROOF_CLASS = FanOutEvaluationClass.LOCAL_EVALUATION


@dataclass
class OptimizationUniverseEvaluatorV1:
    """Optimization candidate comparison only. OPTIMIZATION_PRODUCTIVE_APPLY=false."""

    evaluator_id: str = OPTIMIZATION_UNIVERSE_EVALUATOR_ID
    schema_version: str = EVALUATOR_SCHEMA_VERSION
    _baseline_params: dict[str, Any] | None = field(default=None, init=False)
    _candidate_opt_digest: str | None = field(default=None, init=False)

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        inv_err = self._invariant_violation(replay)
        if inv_err:
            return fail_result(
                domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=inv_err,
            )
        params, err = self._params(replay, label="baseline", context=context)
        if err:
            return fail_result(
                domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        self._baseline_params = dict(params)
        return self._pass(params, label="baseline", delta=None)

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        inv_err = self._invariant_violation(replay)
        if inv_err:
            return fail_result(
                domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=inv_err,
            )
        params, err = self._params(replay, label="candidate", context=context)
        if err:
            return fail_result(
                domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        if self._baseline_params is None:
            return fail_result(
                domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail="baseline not evaluated",
            )
        delta = self._delta(self._baseline_params, params)
        return self._pass(params, label="candidate", delta=delta)

    def protected_digests_baseline(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        return context.protected_digest_baseline

    def protected_digests_candidate(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        base = context.protected_digest_baseline
        if self._candidate_opt_digest is None:
            return base
        if self._candidate_opt_digest == base.selection.digest_hex:
            raise ValueError("optimization/selection digest collapse")
        return base

    def failure_fan_out(self, failure: FailureClassification) -> FanOutEvaluationClass:
        return bwp456_failure_fan_out(failure)

    def _invariant_violation(self, replay: ReplayTraceV1) -> str | None:
        for entry in replay.entries:
            if entry.get("productive_apply") is True:
                return "optimization productive apply forbidden"
            if entry.get("claims_mv2_authority") is True:
                return "MV2 authority claim forbidden"
            if entry.get("claims_risk_authority") is True:
                return "risk authority claim forbidden"
            if entry.get("selection_mutation") is True:
                return "selection mutation forbidden"
            if entry.get("auto_promotion") is True:
                return "automatic promotion forbidden"
        return None

    def _params(
        self,
        replay: ReplayTraceV1,
        *,
        label: str,
        context: DomainEvaluationContextV1,
    ) -> tuple[dict[str, Any], str | None]:
        for entry in replay.entries:
            if entry.get("kind") != "optimization_universe":
                continue
            if entry.get("label") not in (None, label):
                continue
            if entry.get("run_id") not in (None, context.run_manifest.run_id):
                return {}, "run identity mismatch"
            raw = entry.get("parameters")
            if not isinstance(raw, dict):
                return {}, "malformed optimization parameters"
            return dict(sorted(raw.items())), None
        return {}, "missing optimization universe evidence"

    def _delta(self, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        changes: list[dict[str, str]] = []
        keys = sorted(set(baseline) | set(candidate))
        for key in keys:
            b = baseline.get(key)
            c = candidate.get(key)
            if b != c:
                changes.append({"key": key, "before": str(b), "after": str(c)})
        return {"parameter_changes": changes}

    def _pass(
        self,
        params: dict[str, Any],
        *,
        label: str,
        delta: dict[str, Any] | None,
    ) -> DomainEvaluationResultV1:
        payload = {"parameters": params, "label": label}
        opt_digest = sha256_hex(payload)
        if label == "candidate":
            self._candidate_opt_digest = opt_digest
        semantic: dict[str, Any] = {
            "optimization_universe": payload,
            "optimization_digest": opt_digest,
            "evidence_source_class": self._evidence_class(params),
        }
        if delta is not None:
            semantic["optimization_delta"] = delta
        return pass_result(
            domain=EvaluationDomain.OPTIMIZATION_UNIVERSE,
            metrics=[
                MetricResultV1(metric_id="opt.param_count", value=len(params)),
                MetricResultV1(metric_id="opt.digest", value=opt_digest),
            ],
            invariants=[
                InvariantResultV1(
                    invariant_id="opt.no_productive_apply",
                    pass_=True,
                    detail="OPTIMIZATION_PRODUCTIVE_APPLY=false",
                )
            ],
            boundary_results=[],
            evidence_refs=[f"evidence/opt/{label}"],
            semantic_digest_deltas=semantic,
        )

    def _evidence_class(self, params: dict[str, Any]) -> str:
        if params.get("TEST_ONLY_SYNTHETIC") is True:
            return "MECHANISM_TEST_EVIDENCE"
        return "SEALED_EXISTING_EVIDENCE"
