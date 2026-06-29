"""Fixtures for comparison_promotion_policy_decision_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    ComparisonPromotionPolicyDecisionInputs,
    produce_comparison_promotion_policy_decision_v1,
)
from tests.meta.comparison_promotion_policy_input_evidence_v1_fixtures import (
    produce_policy_input_evidence_fixture,
)


@dataclass(frozen=True)
class PolicyDecisionFixtureBundle:
    policy_input_evidence_bundle_dir: Path
    promotion_policy_decision_bundle_dir: Path | None = None


def produce_policy_decision_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    policy_input_evidence_name: str = "policy_input_evidence",
    policy_decision_name: str = "policy_decision",
    produce_output: bool = True,
) -> PolicyDecisionFixtureBundle:
    evidence = produce_policy_input_evidence_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        policy_input_evidence_name=policy_input_evidence_name,
        produce_output=True,
    )
    assert evidence.promotion_policy_input_evidence_bundle_dir is not None
    decision_dir: Path | None = None
    if produce_output:
        decision_dir = durable_root / policy_decision_name
        produce_comparison_promotion_policy_decision_v1(
            inputs=ComparisonPromotionPolicyDecisionInputs(
                policy_input_evidence_bundle_dir=evidence.promotion_policy_input_evidence_bundle_dir,
            ),
            output_dir=decision_dir,
        )
    return PolicyDecisionFixtureBundle(
        policy_input_evidence_bundle_dir=evidence.promotion_policy_input_evidence_bundle_dir,
        promotion_policy_decision_bundle_dir=decision_dir,
    )
