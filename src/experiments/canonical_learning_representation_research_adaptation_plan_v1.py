"""Bounded Learning representation research/adaptation PLAN (Phase 24; AUTHORITY=NONE).

Consumes Phase-23 LEARNING_RESEARCH_ADAPTATION_INPUT decisions only. Produces a typed
research plan — never productive apply or learning-state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    DISPOSITION_NO_ACTION_FAIL_CLOSED,
    DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
    SCHEMA_VERSION as ADAPTATION_INPUT_SCHEMA,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_learning_representation_research_adaptation_plan_v1"
PLAN_DOMAIN: Final[str] = "peak_trade.canonical_learning_representation_research_adaptation_plan.v1"

PRODUCTIVE_APPLY_AUTHORIZED: Final[bool] = False
LEARNING_STATE_MUTATION_AUTHORIZED: Final[bool] = False
PLAN_NOT_AUTHORITY: Final[bool] = True

FIXTURE_LABEL_REDUNDANCY: Final[str] = "FIXTURE_REPRESENTATION_REDUNDANCY"
FIXTURE_LABEL_COVERAGE_WEAKNESS: Final[str] = "FIXTURE_COVERAGE_WEAKNESS"
FIXTURE_LABEL_DRIFT: Final[str] = "FIXTURE_REPRESENTATION_DRIFT"
FIXTURE_LABEL_FAILED_HYPOTHESIS: Final[str] = "FIXTURE_FAILED_REPRESENTATION_HYPOTHESIS"
FIXTURE_LABEL_REGIME: Final[str] = "FIXTURE_REGIME_CONDITIONALITY"
FIXTURE_LABEL_CONTEXT_FAMILY: Final[str] = "FIXTURE_CONTEXT_FAMILY_USEFULNESS"
FIXTURE_LABEL_DEFAULT: Final[str] = "FIXTURE_FEATURE_USEFULNESS"


class RepresentationResearchPurpose(str, Enum):
    INVESTIGATE_FEATURE_USEFULNESS = "INVESTIGATE_FEATURE_USEFULNESS"
    ASSESS_REDUNDANCY = "ASSESS_REDUNDANCY"
    ASSESS_CONTEXT_FAMILY = "ASSESS_CONTEXT_FAMILY"
    ASSESS_REGIME_CONDITIONALITY = "ASSESS_REGIME_CONDITIONALITY"
    ADDRESS_COVERAGE_WEAKNESS = "ADDRESS_COVERAGE_WEAKNESS"
    ASSESS_REPRESENTATION_DRIFT = "ASSESS_REPRESENTATION_DRIFT"
    REVIEW_FAILED_HYPOTHESIS = "REVIEW_FAILED_REPRESENTATION_HYPOTHESIS"
    NO_ACTION_FAIL_CLOSED = "NO_ACTION_FAIL_CLOSED"


class LearningRepresentationResearchAdaptationPlanError(ValueError):
    """Fail-closed representation research plan error."""


@dataclass(frozen=True)
class LearningRepresentationResearchAdaptationPlanRequestV1:
    adaptation_input_decision: Mapping[str, Any]
    requested_productive_apply: bool = False
    requested_learning_state_mutation: bool = False
    requested_feature_drop: bool = False
    requested_parameter_mutation: bool = False


def classify_representation_research_purpose_v1(*, pattern_ref: str) -> str:
    pattern_label = pattern_ref.strip()
    if pattern_label == FIXTURE_LABEL_REDUNDANCY:
        return RepresentationResearchPurpose.ASSESS_REDUNDANCY.value
    if pattern_label == FIXTURE_LABEL_COVERAGE_WEAKNESS:
        return RepresentationResearchPurpose.ADDRESS_COVERAGE_WEAKNESS.value
    if pattern_label == FIXTURE_LABEL_DRIFT:
        return RepresentationResearchPurpose.ASSESS_REPRESENTATION_DRIFT.value
    if pattern_label == FIXTURE_LABEL_FAILED_HYPOTHESIS:
        return RepresentationResearchPurpose.REVIEW_FAILED_HYPOTHESIS.value
    if pattern_label == FIXTURE_LABEL_REGIME:
        return RepresentationResearchPurpose.ASSESS_REGIME_CONDITIONALITY.value
    if pattern_label == FIXTURE_LABEL_CONTEXT_FAMILY:
        return RepresentationResearchPurpose.ASSESS_CONTEXT_FAMILY.value
    if pattern_label.startswith("FIXTURE_"):
        return RepresentationResearchPurpose.INVESTIGATE_FEATURE_USEFULNESS.value
    return RepresentationResearchPurpose.INVESTIGATE_FEATURE_USEFULNESS.value


def derive_representation_research_plan_identity_v1(*, identity_body: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(identity_body))


def build_learning_representation_research_adaptation_plan_v1(
    request: LearningRepresentationResearchAdaptationPlanRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_productive_apply:
        raise LearningRepresentationResearchAdaptationPlanError("PRODUCTIVE_APPLY_FORBIDDEN")
    if request.requested_learning_state_mutation:
        raise LearningRepresentationResearchAdaptationPlanError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_feature_drop:
        raise LearningRepresentationResearchAdaptationPlanError("FEATURE_DROP_FORBIDDEN")
    if request.requested_parameter_mutation:
        raise LearningRepresentationResearchAdaptationPlanError("PARAMETER_MUTATION_FORBIDDEN")

    decision = request.adaptation_input_decision
    if decision.get("schema_version") != ADAPTATION_INPUT_SCHEMA:
        raise LearningRepresentationResearchAdaptationPlanError("ADAPTATION_INPUT_SCHEMA_MISMATCH")

    overall = str(decision.get("overall_disposition") or "")
    source_meta_id = decision.get("source_meta_evidence_id")
    adaptation_decision_identity = decision.get("adaptation_decision_identity")

    if overall == DISPOSITION_NO_ACTION_FAIL_CLOSED:
        purpose = RepresentationResearchPurpose.NO_ACTION_FAIL_CLOSED.value
        evaluation_fixture_label = "FIXTURE_FAIL_CLOSED"
        plan_status = "PLAN_FAIL_CLOSED"
    elif overall == DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT:
        items = decision.get("adaptation_items") or []
        pattern_ref = FIXTURE_LABEL_DEFAULT
        lineage_ref = None
        if items and isinstance(items[0], Mapping):
            payload = items[0].get("payload") or {}
            if isinstance(payload, Mapping):
                pattern_ref = str(payload.get("pattern_ref") or FIXTURE_LABEL_DEFAULT)
                lineage_ref = payload.get("learning_representation_lineage_ref")
        purpose = classify_representation_research_purpose_v1(pattern_ref=pattern_ref)
        evaluation_fixture_label = pattern_ref
        plan_status = "PLAN_READY_OFFLINE_EVALUATION"
    else:
        raise LearningRepresentationResearchAdaptationPlanError(
            "ADAPTATION_DISPOSITION_UNSUPPORTED"
        )

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "domain": PLAN_DOMAIN,
        "source_meta_evidence_id": source_meta_id,
        "adaptation_decision_identity": adaptation_decision_identity,
        "research_purpose": purpose,
        "evaluation_fixture_label": evaluation_fixture_label,
        "plan_status": plan_status,
        "productive_apply_authorized": PRODUCTIVE_APPLY_AUTHORIZED,
        "learning_state_mutation_authorized": LEARNING_STATE_MUTATION_AUTHORIZED,
    }
    plan_identity = derive_representation_research_plan_identity_v1(identity_body=identity_body)
    body = {
        **identity_body,
        "plan_identity": plan_identity,
        "plan_not_authority": PLAN_NOT_AUTHORITY,
        "adaptation_input_result_digest": decision.get("result_digest"),
        "learning_representation_lineage_ref": (
            str(lineage_ref)
            if overall == DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT
            else None
        ),
        "offline_evaluation_required": plan_status == "PLAN_READY_OFFLINE_EVALUATION",
        "productive_feature_mutation_authorized": False,
        "trading_configuration_mutation_authorized": False,
        "promotion_authorized": False,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)


def validate_learning_representation_research_adaptation_plan_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise LearningRepresentationResearchAdaptationPlanError("PLAN_SCHEMA_MISMATCH")
    if payload.get("productive_apply_authorized") is not False:
        raise LearningRepresentationResearchAdaptationPlanError("PRODUCTIVE_APPLY_MUST_BE_FALSE")
    plan_id = str(payload.get("plan_identity") or "")
    if not is_valid_sha256_hex(plan_id):
        raise LearningRepresentationResearchAdaptationPlanError("PLAN_IDENTITY_INVALID")
    return MappingProxyType(dict(payload))


__all__ = [
    "FIXTURE_LABEL_COVERAGE_WEAKNESS",
    "FIXTURE_LABEL_DEFAULT",
    "FIXTURE_LABEL_DRIFT",
    "FIXTURE_LABEL_FAILED_HYPOTHESIS",
    "FIXTURE_LABEL_REDUNDANCY",
    "LearningRepresentationResearchAdaptationPlanError",
    "LearningRepresentationResearchAdaptationPlanRequestV1",
    "RepresentationResearchPurpose",
    "SCHEMA_VERSION",
    "build_learning_representation_research_adaptation_plan_v1",
    "classify_representation_research_purpose_v1",
    "validate_learning_representation_research_adaptation_plan_v1",
]
