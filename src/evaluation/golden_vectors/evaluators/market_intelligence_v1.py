"""BWP-6 Market Intelligence domain evaluator (evidence only)."""

from __future__ import annotations

from dataclasses import dataclass

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

MARKET_INTELLIGENCE_EVALUATOR_ID = "market_intelligence_evaluator_v1"
EVALUATOR_SCHEMA_VERSION = "1.5.0"
BWP_ID = "BWP-6"
PRIMARY_FAILURE_CLASS = FailureClassification.INVARIANT_FAILURE
REPROOF_CLASS = FanOutEvaluationClass.LOCAL_EVALUATION


@dataclass(frozen=True)
class MarketIntelligenceEvaluatorV1:
    """MI context evaluation only. No productive materialization."""

    evaluator_id: str = MARKET_INTELLIGENCE_EVALUATOR_ID
    schema_version: str = EVALUATOR_SCHEMA_VERSION

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        return self._evaluate(context=context, replay=replay, label="baseline")

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        return self._evaluate(context=context, replay=replay, label="candidate")

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

    def _evaluate(
        self,
        *,
        context: DomainEvaluationContextV1,
        replay: ReplayTraceV1,
        label: str,
    ) -> DomainEvaluationResultV1:
        inv_err = self._invariant_violation(replay)
        if inv_err:
            return fail_result(
                domain=EvaluationDomain.MARKET_INTELLIGENCE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=inv_err,
            )
        bundle, err = self._bundle(replay, label=label, context=context)
        if err:
            return fail_result(
                domain=EvaluationDomain.MARKET_INTELLIGENCE,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        digest = sha256_hex({"mi_bundle": bundle, "label": label})
        return pass_result(
            domain=EvaluationDomain.MARKET_INTELLIGENCE,
            metrics=[
                MetricResultV1(metric_id="mi.bundle_digest", value=digest),
                MetricResultV1(
                    metric_id="mi.freshness_token", value=str(bundle.get("freshness_token", ""))
                ),
            ],
            invariants=[
                InvariantResultV1(
                    invariant_id="mi.no_productive_materialization",
                    pass_=True,
                    detail="MARKET_INTELLIGENCE_PRODUCTIVE_MATERIALIZATION=false",
                ),
                InvariantResultV1(
                    invariant_id="mi.leakage_check",
                    pass_=bundle.get("leakage_detected") is not True,
                ),
            ],
            boundary_results=[],
            evidence_refs=[f"evidence/mi/{label}"],
            semantic_digest_deltas={
                "mi_context_bundle": bundle,
                "mi_digest": digest,
                "evidence_source_class": (
                    "MECHANISM_TEST_EVIDENCE"
                    if bundle.get("TEST_ONLY_SYNTHETIC") is True
                    else "SEALED_EXISTING_EVIDENCE"
                ),
            },
        )

    def _invariant_violation(self, replay: ReplayTraceV1) -> str | None:
        for entry in replay.entries:
            if entry.get("selection_mutation") is True:
                return "selection mutation forbidden"
            if entry.get("binding_mutation") is True:
                return "binding mutation forbidden"
            if entry.get("productive_trading_intent_authority") is True:
                return "trading intent authority forbidden"
            if entry.get("venue_post") is True:
                return "venue POST forbidden"
            if entry.get("materialize_productive_state") is True:
                return "productive materialization forbidden"
            if entry.get("mutate_mv2") is True:
                return "MV2 mutation forbidden"
            if entry.get("mutate_risk") is True:
                return "risk mutation forbidden"
        return None

    def _bundle(
        self,
        replay: ReplayTraceV1,
        *,
        label: str,
        context: DomainEvaluationContextV1,
    ) -> tuple[dict, str | None]:
        for entry in replay.entries:
            if entry.get("kind") != "market_intelligence":
                continue
            if entry.get("label") not in (None, label):
                continue
            if entry.get("run_id") not in (None, context.run_manifest.run_id):
                return {}, "run identity mismatch"
            raw = entry.get("mi_context_bundle")
            if not isinstance(raw, dict):
                return {}, "malformed MI context bundle"
            if raw.get("leakage_detected") is True:
                return {}, "leakage invariant violated"
            if raw.get("causality_proof_present") is False:
                return {}, "missing causality evidence"
            return dict(raw), None
        return {}, "missing market intelligence evidence"
