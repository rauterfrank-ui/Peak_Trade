"""Fixtures for comparison_completion_research_validity_binding_v1 contract tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_completion_evidence_v1 import (
    produce_comparison_completion_evidence_v1,
)
from src.meta.learning_loop.research_validity_evidence_v1 import (
    produce_research_validity_evidence_v1,
)
from tests.meta.research_validity_evidence_v1_fixtures import produce_full_research_validity_inputs


@dataclass(frozen=True)
class MatchedEvidenceBundles:
    completion_bundle_dir: Path
    research_validity_bundle_dir: Path
    checkpoint_bundle_dir: Path
    comparison_definition_id: str


def produce_matched_completion_and_validity_bundles(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    completion_name: str = "completion_evidence",
    validity_name: str = "research_validity_evidence",
) -> MatchedEvidenceBundles:
    """Produce completion and research validity bundles sharing one checkpoint lineage."""
    inputs = produce_full_research_validity_inputs(
        tmp_path, durable_root, all_domains_pass=all_domains_pass
    )
    validity_out = durable_root / validity_name
    validity_result = produce_research_validity_evidence_v1(
        inputs=inputs,
        output_dir=validity_out,
    )
    completion_out = durable_root / completion_name
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=inputs.checkpoint_bundle_dir,
        output_dir=completion_out,
    )
    return MatchedEvidenceBundles(
        completion_bundle_dir=completion_out,
        research_validity_bundle_dir=validity_out,
        checkpoint_bundle_dir=inputs.checkpoint_bundle_dir,
        comparison_definition_id=validity_result.comparison_definition_id,
    )
