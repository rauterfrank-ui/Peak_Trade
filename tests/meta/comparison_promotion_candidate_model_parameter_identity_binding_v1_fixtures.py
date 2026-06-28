"""Fixtures for comparison_promotion_candidate_model_parameter_identity_binding_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ComparisonPromotionCandidateEligibilityEvidenceInputs,
    produce_comparison_promotion_candidate_eligibility_evidence_v1,
)
from tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures import (
    produce_candidate_identity_binding_bundle,
)


@dataclass(frozen=True)
class EligibilityEvidenceFixtureBundle:
    eligibility_evidence_bundle_dir: Path
    source_type: str


def produce_eligibility_evidence_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = False,
    identity_binding_name: str = "identity_binding",
    eligibility_name: str = "eligibility_evidence",
) -> EligibilityEvidenceFixtureBundle:
    identity = produce_candidate_identity_binding_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        binding_name=identity_binding_name,
    )
    out = durable_root / eligibility_name
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=ComparisonPromotionCandidateEligibilityEvidenceInputs(
            candidate_identity_binding_bundle_dir=identity.candidate_identity_binding_bundle_dir,
        ),
        output_dir=out,
    )
    return EligibilityEvidenceFixtureBundle(
        eligibility_evidence_bundle_dir=out,
        source_type=identity.source_type,
    )
