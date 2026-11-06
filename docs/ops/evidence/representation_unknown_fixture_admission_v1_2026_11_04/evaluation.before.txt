"""Offline bounded evaluation for representation research plans (Phase 24; AUTHORITY=NONE).

Evaluates research/adaptation plans only — never applies productive changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_COVERAGE_WEAKNESS,
    FIXTURE_LABEL_DRIFT,
    FIXTURE_LABEL_FAILED_HYPOTHESIS,
    FIXTURE_LABEL_REDUNDANCY,
    SCHEMA_VERSION as PLAN_SCHEMA,
    RepresentationResearchPurpose,
    validate_learning_representation_research_adaptation_plan_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_learning_representation_offline_evaluation_v1"
EVALUATION_DOMAIN: Final[str] = "peak_trade.canonical_learning_representation_offline_evaluation.v1"

PRODUCTIVE_APPLY_PERFORMED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False


class OfflineEvaluationOutcome(str, Enum):
    RESEARCH_EVIDENCE_SUPPORTED = "RESEARCH_EVIDENCE_SUPPORTED"
    REJECTED_REDUNDANCY = "REJECTED_REDUNDANCY"
    REJECTED_INSUFFICIENT_EVIDENCE = "REJECTED_INSUFFICIENT_EVIDENCE"
    REJECTED_UNSTABLE_OOS = "REJECTED_UNSTABLE_OOS"
    REJECTED_COVERAGE_FAILURE = "REJECTED_COVERAGE_FAILURE"
    REJECTED_DRIFT_INCOMPATIBILITY = "REJECTED_DRIFT_INCOMPATIBILITY"
    REJECTED_UNSUPPORTED_FAMILY = "REJECTED_UNSUPPORTED_FAMILY"
    FAIL_CLOSED_NO_EVALUATION = "FAIL_CLOSED_NO_EVALUATION"


class LearningRepresentationOfflineEvaluationError(ValueError):
    """Fail-closed offline evaluation error."""


@dataclass(frozen=True)
class LearningRepresentationOfflineEvaluationRequestV1:
    research_plan: Mapping[str, Any]
    requested_productive_apply: bool = False


def _outcome_for_fixture(*, fixture_label: str, research_purpose: str) -> str:
    if fixture_label == "FIXTURE_FAIL_CLOSED":
        return OfflineEvaluationOutcome.FAIL_CLOSED_NO_EVALUATION.value
    if fixture_label == FIXTURE_LABEL_REDUNDANCY:
        return OfflineEvaluationOutcome.REJECTED_REDUNDANCY.value
    if fixture_label == FIXTURE_LABEL_COVERAGE_WEAKNESS:
        return OfflineEvaluationOutcome.REJECTED_COVERAGE_FAILURE.value
    if fixture_label == FIXTURE_LABEL_DRIFT:
        return OfflineEvaluationOutcome.REJECTED_DRIFT_INCOMPATIBILITY.value
    if fixture_label == FIXTURE_LABEL_FAILED_HYPOTHESIS:
        return OfflineEvaluationOutcome.REJECTED_INSUFFICIENT_EVIDENCE.value
    if research_purpose == RepresentationResearchPurpose.NO_ACTION_FAIL_CLOSED.value:
        return OfflineEvaluationOutcome.FAIL_CLOSED_NO_EVALUATION.value
    if fixture_label.endswith("_UNSTABLE_OOS"):
        return OfflineEvaluationOutcome.REJECTED_UNSTABLE_OOS.value
    if fixture_label.endswith("_UNSUPPORTED_FAMILY"):
        return OfflineEvaluationOutcome.REJECTED_UNSUPPORTED_FAMILY.value
    return OfflineEvaluationOutcome.RESEARCH_EVIDENCE_SUPPORTED.value


def run_learning_representation_offline_evaluation_v1(
    request: LearningRepresentationOfflineEvaluationRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_productive_apply:
        raise LearningRepresentationOfflineEvaluationError("PRODUCTIVE_APPLY_FORBIDDEN")

    plan = validate_learning_representation_research_adaptation_plan_v1(request.research_plan)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise LearningRepresentationOfflineEvaluationError("PLAN_SCHEMA_MISMATCH")

    fixture_label = str(plan.get("evaluation_fixture_label") or "")
    purpose = str(plan.get("research_purpose") or "")
    plan_identity = str(plan.get("plan_identity") or "")

    if not plan.get("offline_evaluation_required"):
        outcome = OfflineEvaluationOutcome.FAIL_CLOSED_NO_EVALUATION.value
        eval_status = "EVALUATION_SKIPPED_PLAN_FAIL_CLOSED"
    else:
        outcome = _outcome_for_fixture(fixture_label=fixture_label, research_purpose=purpose)
        eval_status = "EVALUATION_COMPLETE"

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "domain": EVALUATION_DOMAIN,
        "plan_identity": plan_identity,
        "evaluation_fixture_label": fixture_label,
        "research_purpose": purpose,
        "evaluation_outcome": outcome,
        "evaluation_status": eval_status,
    }
    evaluation_identity = compute_content_sha256(identity_body)
    body = {
        **identity_body,
        "evaluation_identity": evaluation_identity,
        "source_plan_result_digest": plan.get("result_digest"),
        "productive_apply_performed": PRODUCTIVE_APPLY_PERFORMED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "evaluation_is_evidence_not_authority": True,
        "rejection_is_typed_evidence": outcome.startswith("REJECTED_")
        or outcome == OfflineEvaluationOutcome.FAIL_CLOSED_NO_EVALUATION.value,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)


__all__ = [
    "LearningRepresentationOfflineEvaluationError",
    "LearningRepresentationOfflineEvaluationRequestV1",
    "OfflineEvaluationOutcome",
    "SCHEMA_VERSION",
    "run_learning_representation_offline_evaluation_v1",
]
