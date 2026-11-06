"""Fixtures for comparison_promotion_candidate_input_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_input_v1 import (
    ComparisonPromotionCandidateInputInputs,
    produce_comparison_promotion_candidate_input_v1,
)
from tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures import (
    produce_cross_domain_lineage_binding_fixture,
)


@dataclass(frozen=True)
class CandidateInputFixtureBundle:
    cross_domain_lineage_binding_bundle_dir: Path
    candidate_input_bundle_dir: Path | None = None


def produce_candidate_input_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    cross_domain_binding_name: str = "cross_domain_lineage_binding",
    candidate_input_name: str = "candidate_input",
    produce_output: bool = True,
) -> CandidateInputFixtureBundle:
    cross_domain = produce_cross_domain_lineage_binding_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        cross_domain_binding_name=cross_domain_binding_name,
        produce_output=True,
    )
    assert cross_domain.cross_domain_binding_bundle_dir is not None
    candidate_input_dir: Path | None = None
    if produce_output:
        candidate_input_dir = durable_root / candidate_input_name
        produce_comparison_promotion_candidate_input_v1(
            inputs=ComparisonPromotionCandidateInputInputs(
                cross_domain_lineage_binding_bundle_dir=(
                    cross_domain.cross_domain_binding_bundle_dir
                ),
            ),
            output_dir=candidate_input_dir,
        )
    return CandidateInputFixtureBundle(
        cross_domain_lineage_binding_bundle_dir=cross_domain.cross_domain_binding_bundle_dir,
        candidate_input_bundle_dir=candidate_input_dir,
    )
