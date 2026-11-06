"""Fixtures for comparison_promotion_candidate_eligibility_evidence_v1 contract tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ComparisonPromotionCandidateIdentityBindingInputs,
    produce_comparison_promotion_candidate_identity_binding_v1,
)
from tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures import (
    produce_candidate_lineage_candidate_bundle,
    produce_metric_input_candidate_bundle,
    produce_promotion_input_binding_bundle,
)


@dataclass(frozen=True)
class CandidateIdentityBindingFixtureBundle:
    candidate_identity_binding_bundle_dir: Path
    source_type: str


def produce_candidate_identity_binding_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = False,
    binding_name: str = "identity_binding",
) -> CandidateIdentityBindingFixtureBundle:
    promotion_input = produce_promotion_input_binding_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
    )
    if use_candidate_lineage:
        candidate = produce_candidate_lineage_candidate_bundle(
            durable_root, promotion_input=promotion_input
        )
    else:
        candidate = produce_metric_input_candidate_bundle(
            tmp_path, durable_root, promotion_input=promotion_input
        )
    out = durable_root / binding_name
    produce_comparison_promotion_candidate_identity_binding_v1(
        inputs=ComparisonPromotionCandidateIdentityBindingInputs(
            promotion_input_binding_bundle_dir=promotion_input.promotion_input_binding_bundle_dir,
            candidate_identity_bundle_dir=candidate.candidate_identity_bundle_dir,
        ),
        output_dir=out,
    )
    return CandidateIdentityBindingFixtureBundle(
        candidate_identity_binding_bundle_dir=out,
        source_type=candidate.source_type,
    )
