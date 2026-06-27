"""Offline comparison producer for comparison_ssot.v1."""

from __future__ import annotations

from pathlib import Path

from src.meta.learning_loop.comparison_metric_input_v1.constants import TIE_TOLERANCE_VERSION
from src.meta.learning_loop.comparison_ssot_v1.constants import RANKING_RULE_NONE
from src.meta.learning_loop.comparison_ssot_v1.comparison_definition_manifest_v1 import (
    build_definition_manifest_body,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_gates_v1 import (
    evaluate_comparability_gates,
    overall_comparable,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_input_loader_v1 import (
    load_and_validate_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_pareto_v1 import compute_pareto_front
from src.meta.learning_loop.comparison_ssot_v1.comparison_ranking_v1 import compute_ranking
from src.meta.learning_loop.comparison_ssot_v1.comparison_result_manifest_v1 import (
    build_result_manifest_body,
)
from src.meta.learning_loop.comparison_ssot_v1.identity import (
    attach_definition_identity_and_integrity,
    compute_comparison_definition_id,
)
from src.meta.learning_loop.comparison_ssot_v1.io import publish_comparison_manifests_atomic
from src.meta.learning_loop.comparison_ssot_v1.models import (
    ComparisonOfflineResult,
    ComparisonSsotError,
)


def produce_comparison_offline_v1(
    *,
    input_manifest_paths: list[Path],
    output_root: Path,
    ranking_rule_version: str,
) -> ComparisonOfflineResult:
    inputs = load_and_validate_inputs(input_manifest_paths)
    definition_body = build_definition_manifest_body(
        inputs,
        ranking_rule_version=ranking_rule_version,
        tie_rule_version=TIE_TOLERANCE_VERSION,
    )
    definition_with_id = attach_definition_identity_and_integrity(definition_body)
    comparison_definition_id = str(definition_with_id["comparison_definition_id"])

    gate_outcomes = evaluate_comparability_gates(inputs)
    comparable = overall_comparable(gate_outcomes)
    warnings: list[str] = []
    if not comparable:
        warnings.append("overall_comparable=false; pareto and ranking suppressed")

    pareto_result = compute_pareto_front(inputs) if comparable else None
    if not comparable and ranking_rule_version != RANKING_RULE_NONE:
        ranking_result = compute_ranking(inputs, ranking_rule_version=RANKING_RULE_NONE)
    else:
        ranking_result = compute_ranking(inputs, ranking_rule_version=ranking_rule_version)
    if not comparable and ranking_result.get("ranking_status") != "NONE":
        raise ComparisonSsotError("ranking emitted while inputs not comparable")

    result_body = build_result_manifest_body(
        comparison_definition_id=comparison_definition_id,
        inputs=inputs,
        gate_outcomes=gate_outcomes,
        overall_comparable=comparable,
        pareto_result=pareto_result,
        ranking_result=ranking_result
        if comparable
        else {
            "ranking_status": "NONE",
            "ranking_rule_version": ranking_rule_version,
            "ranked_input_ids": [],
        },
        warnings=warnings,
    )

    replay_id = compute_comparison_definition_id(definition_body)
    if replay_id != comparison_definition_id:
        raise ComparisonSsotError("definition id replay mismatch")

    output_root.mkdir(parents=True, exist_ok=True)
    definition_path, result_path = publish_comparison_manifests_atomic(
        output_root=output_root,
        definition_body=definition_body,
        result_body=result_body,
    )

    from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest

    definition_manifest = read_manifest(definition_path)
    result_manifest = read_manifest(result_path)
    return ComparisonOfflineResult(
        output_dir=definition_path.parent,
        definition_path=definition_path,
        result_path=result_path,
        comparison_definition_id=comparison_definition_id,
        definition_manifest=definition_manifest,
        result_manifest=result_manifest,
    )
