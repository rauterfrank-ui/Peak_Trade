"""Build comparison_definition_manifest_v1 bodies."""

from __future__ import annotations

from src.meta.learning_loop.comparison_ssot_v1.identity import build_definition_body
from src.meta.learning_loop.comparison_ssot_v1.models import LoadedMetricInput


def build_definition_manifest_body(
    inputs: list[LoadedMetricInput],
    *,
    ranking_rule_version: str,
    tie_rule_version: str,
) -> dict[str, object]:
    input_refs = [item.source_ref.to_mapping() for item in inputs]
    evaluation_slice_id = inputs[0].evaluation_slice_id
    from src.meta.learning_loop.comparison_ssot_v1.constants import CANONICAL_AUTHORITY_INVARIANTS

    return build_definition_body(
        input_refs=input_refs,
        ranking_rule_version=ranking_rule_version,
        tie_rule_version=tie_rule_version,
        evaluation_slice_id=evaluation_slice_id,
        authority_invariants=CANONICAL_AUTHORITY_INVARIANTS,
    )
