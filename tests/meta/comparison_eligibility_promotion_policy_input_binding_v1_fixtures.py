"""Fixtures for comparison_eligibility_promotion_policy_input_binding_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1 import (
    ComparisonEligibilityPromotionPolicyInputBindingInputs,
    produce_comparison_eligibility_promotion_policy_input_binding_v1,
)
from tests.meta.comparison_promotion_candidate_input_v1_fixtures import (
    produce_candidate_input_fixture,
)


@dataclass(frozen=True)
class PolicyInputBindingFixtureBundle:
    candidate_input_bundle_dir: Path
    policy_input_binding_bundle_dir: Path | None = None


def produce_policy_input_binding_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    candidate_input_name: str = "candidate_input",
    policy_input_binding_name: str = "policy_input_binding",
    produce_output: bool = True,
) -> PolicyInputBindingFixtureBundle:
    candidate_input = produce_candidate_input_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        candidate_input_name=candidate_input_name,
        produce_output=True,
    )
    assert candidate_input.candidate_input_bundle_dir is not None
    binding_dir: Path | None = None
    if produce_output:
        binding_dir = durable_root / policy_input_binding_name
        produce_comparison_eligibility_promotion_policy_input_binding_v1(
            inputs=ComparisonEligibilityPromotionPolicyInputBindingInputs(
                candidate_input_bundle_dir=candidate_input.candidate_input_bundle_dir,
            ),
            output_dir=binding_dir,
        )
    return PolicyInputBindingFixtureBundle(
        candidate_input_bundle_dir=candidate_input.candidate_input_bundle_dir,
        policy_input_binding_bundle_dir=binding_dir,
    )
