"""Fixtures for comparison_completion_promotion_input_binding_v1 contract tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
    ComparisonCompletionResearchValidityBindingInputs,
    produce_comparison_completion_research_validity_binding_v1,
)
from tests.meta.comparison_completion_research_validity_binding_v1_fixtures import (
    MatchedEvidenceBundles,
    produce_matched_completion_and_validity_bundles,
)


@dataclass(frozen=True)
class UpstreamBindingBundle:
    completion_validity_binding_bundle_dir: Path
    matched: MatchedEvidenceBundles


def produce_upstream_binding_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    binding_name: str = "completion_validity_binding",
) -> UpstreamBindingBundle:
    """Produce a completion+validity binding bundle for promotion input binding tests."""
    matched = produce_matched_completion_and_validity_bundles(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
    )
    binding_out = durable_root / binding_name
    produce_comparison_completion_research_validity_binding_v1(
        inputs=ComparisonCompletionResearchValidityBindingInputs(
            completion_evidence_bundle_dir=matched.completion_bundle_dir,
            research_validity_evidence_bundle_dir=matched.research_validity_bundle_dir,
        ),
        output_dir=binding_out,
    )
    return UpstreamBindingBundle(
        completion_validity_binding_bundle_dir=binding_out,
        matched=matched,
    )
