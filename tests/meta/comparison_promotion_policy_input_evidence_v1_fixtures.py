"""Fixtures for comparison_promotion_policy_input_evidence_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1 import (
    ComparisonPromotionPolicyInputEvidenceInputs,
    produce_comparison_promotion_policy_input_evidence_v1,
)
from tests.meta.comparison_eligibility_promotion_policy_input_binding_v1_fixtures import (
    produce_policy_input_binding_fixture,
)


@dataclass(frozen=True)
class PolicyInputEvidenceFixtureBundle:
    policy_input_binding_bundle_dir: Path
    promotion_policy_input_evidence_bundle_dir: Path | None = None


def produce_policy_input_evidence_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    policy_input_binding_name: str = "policy_input_binding",
    policy_input_evidence_name: str = "policy_input_evidence",
    produce_output: bool = True,
) -> PolicyInputEvidenceFixtureBundle:
    binding = produce_policy_input_binding_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        policy_input_binding_name=policy_input_binding_name,
        produce_output=True,
    )
    assert binding.policy_input_binding_bundle_dir is not None
    evidence_dir: Path | None = None
    if produce_output:
        evidence_dir = durable_root / policy_input_evidence_name
        produce_comparison_promotion_policy_input_evidence_v1(
            inputs=ComparisonPromotionPolicyInputEvidenceInputs(
                policy_input_binding_bundle_dir=binding.policy_input_binding_bundle_dir,
            ),
            output_dir=evidence_dir,
        )
    return PolicyInputEvidenceFixtureBundle(
        policy_input_binding_bundle_dir=binding.policy_input_binding_bundle_dir,
        promotion_policy_input_evidence_bundle_dir=evidence_dir,
    )
