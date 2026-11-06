"""Fixtures for ai_promotion_assessment_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.ai_promotion_assessment_v1 import (
    AiPromotionAssessmentInputs,
    produce_ai_promotion_assessment_v1,
)
from tests.meta.comparison_promotion_policy_decision_v1_fixtures import (
    produce_policy_decision_fixture,
)


@dataclass(frozen=True)
class AiPromotionAssessmentFixtureBundle:
    policy_decision_bundle_dir: Path
    ai_promotion_assessment_bundle_dir: Path | None = None


def produce_ai_promotion_assessment_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    policy_decision_name: str = "policy_decision",
    ai_assessment_name: str = "ai_assessment",
    produce_output: bool = True,
) -> AiPromotionAssessmentFixtureBundle:
    decision = produce_policy_decision_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        policy_decision_name=policy_decision_name,
        produce_output=True,
    )
    assert decision.promotion_policy_decision_bundle_dir is not None
    assessment_dir: Path | None = None
    if produce_output:
        assessment_dir = durable_root / ai_assessment_name
        produce_ai_promotion_assessment_v1(
            inputs=AiPromotionAssessmentInputs(
                policy_decision_bundle_dir=decision.promotion_policy_decision_bundle_dir,
            ),
            output_dir=assessment_dir,
        )
    return AiPromotionAssessmentFixtureBundle(
        policy_decision_bundle_dir=decision.promotion_policy_decision_bundle_dir,
        ai_promotion_assessment_bundle_dir=assessment_dir,
    )
