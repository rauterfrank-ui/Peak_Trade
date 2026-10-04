"""BWP-3 Productive Trading Path domain evaluator (replay/read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import (
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    InvariantResultV1,
    MetricResultV1,
    ProtectedSemanticDigestsV1,
    ReplayTraceV1,
    contract_digest_hex,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.evaluators._fanout_v1 import bwp3_failure_fan_out
from src.evaluation.golden_vectors.evaluators._result_v1 import fail_result, pass_result
from src.evaluation.golden_vectors.evaluators.ptp_owners_v1 import (
    PTP_STAGE_ORDER,
    PTP_STAGE_OWNERS,
)

PRODUCTIVE_TRADING_PATH_EVALUATOR_ID = "productive_trading_path_evaluator_v1"
EVALUATOR_SCHEMA_VERSION = "1.5.0"
BWP_ID = "BWP-3"
PRIMARY_FAILURE_CLASS = FailureClassification.INVARIANT_FAILURE
REPROOF_CLASS = FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION


@dataclass(frozen=True)
class ProductiveTradingPathEvaluatorV1:
    """Observes replay stage traces only. TRADING_AUTHORITY=NONE."""

    evaluator_id: str = PRODUCTIVE_TRADING_PATH_EVALUATOR_ID
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
        return bwp3_failure_fan_out(failure)

    def _evaluate(
        self,
        *,
        context: DomainEvaluationContextV1,
        replay: ReplayTraceV1,
        label: str,
    ) -> DomainEvaluationResultV1:
        run_id = context.run_manifest.run_id
        stages, err = self._parse_stages(replay, expected_run_id=run_id)
        if err:
            return fail_result(
                domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=err,
            )
        order_err = self._check_order(stages)
        if order_err:
            return fail_result(
                domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=order_err,
            )
        owner_err = self._check_owners(stages)
        if owner_err:
            return fail_result(
                domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=owner_err,
            )
        terminal_err = self._check_pre_external_terminal(stages)
        if terminal_err:
            return fail_result(
                domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail=terminal_err,
            )
        if self._crosses_pre_external(stages):
            return fail_result(
                domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
                failure=FailureClassification.INVARIANT_FAILURE,
                detail="PRE_EXTERNAL crossed",
            )
        trace_payload = {
            "run_id": run_id,
            "label": label,
            "stages": stages,
            "TEST_ONLY_SYNTHETIC": self._is_synthetic(replay),
        }
        metrics = [
            MetricResultV1(metric_id="ptp.stage_count", value=len(stages)),
            MetricResultV1(
                metric_id="ptp.trace_digest",
                value=sha256_hex(trace_payload),
            ),
        ]
        boundaries = [
            BoundaryResultV1(
                edge_id=f"{PTP_STAGE_ORDER[i]}->{PTP_STAGE_ORDER[i + 1]}",
                pass_=True,
                producer=PTP_STAGE_OWNERS[PTP_STAGE_ORDER[i]],
                consumer=PTP_STAGE_OWNERS[PTP_STAGE_ORDER[i + 1]],
                current_verdict="PROVEN_CURRENT",
            )
            for i in range(len(PTP_STAGE_ORDER) - 1)
        ]
        return pass_result(
            domain=EvaluationDomain.PRODUCTIVE_TRADING_PATH,
            metrics=metrics,
            invariants=[
                InvariantResultV1(
                    invariant_id="ptp.pre_external_terminal",
                    pass_=True,
                )
            ],
            boundary_results=boundaries,
            evidence_refs=[f"evidence/ptp/{label}/{run_id}"],
            semantic_digest_deltas={
                "ptp_stage_trace": trace_payload,
                "evidence_source_class": self._evidence_class(replay),
            },
        )

    def _parse_stages(
        self, replay: ReplayTraceV1, *, expected_run_id: str
    ) -> tuple[list[dict[str, Any]], str | None]:
        stages: list[dict[str, Any]] = []
        for entry in replay.entries:
            if entry.get("kind") != "ptp_stage":
                continue
            if entry.get("run_id") not in (None, expected_run_id):
                return [], "run/vector identity mismatch"
            stage = entry.get("stage")
            if not isinstance(stage, str):
                return [], "malformed stage evidence"
            stages.append(
                {
                    "stage": stage,
                    "owner": entry.get("owner"),
                    "gvef_authority": False,
                }
            )
        if not stages:
            return [], "missing required stage evidence"
        return stages, None

    def _check_order(self, stages: list[dict[str, Any]]) -> str | None:
        observed = [s["stage"] for s in stages]
        if observed != list(PTP_STAGE_ORDER):
            return "stage reordered or missing"
        return None

    def _check_owners(self, stages: list[dict[str, Any]]) -> str | None:
        for s in stages:
            stage = s["stage"]
            expected = PTP_STAGE_OWNERS.get(stage)
            if expected and s.get("owner") not in (None, expected):
                return f"owner mismatch at {stage}"
        return None

    def _check_pre_external_terminal(self, stages: list[dict[str, Any]]) -> str | None:
        if not stages or stages[-1]["stage"] != "PRE_EXTERNAL":
            return "Venue Plan must terminate at PRE_EXTERNAL"
        return None

    def _crosses_pre_external(self, stages: list[dict[str, Any]]) -> bool:
        seen_terminal = False
        for s in stages:
            if seen_terminal:
                return True
            if s["stage"] == "PRE_EXTERNAL":
                seen_terminal = True
            if s["stage"] in ("LIVE_POST", "EXCHANGE_POST"):
                return True
        return False

    def _is_synthetic(self, replay: ReplayTraceV1) -> bool:
        return any(e.get("TEST_ONLY_SYNTHETIC") is True for e in replay.entries)

    def _evidence_class(self, replay: ReplayTraceV1) -> str:
        if self._is_synthetic(replay):
            return "MECHANISM_TEST_EVIDENCE"
        return "SEALED_GHV_REPLAY_EVIDENCE"


def ptp_protected_output_digest(result: DomainEvaluationResultV1) -> str:
    return contract_digest_hex(result)
