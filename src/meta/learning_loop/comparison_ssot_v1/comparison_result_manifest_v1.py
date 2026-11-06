"""Build comparison_result_manifest_v1 bodies."""

from __future__ import annotations

from typing import Any

from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    CANONICAL_AUTHORITY_INVARIANTS,
    COMPARISON_CONTRACT_VERSION,
)
from src.meta.learning_loop.comparison_ssot_v1.models import GateOutcome, LoadedMetricInput


def _gate_to_mapping(outcome: GateOutcome) -> dict[str, object]:
    return {
        "gate_id": outcome.gate_id,
        "version": outcome.version,
        "status": outcome.status,
        "reason_code": outcome.reason_code,
        "evidence_refs": list(outcome.evidence_refs),
    }


def build_input_snapshots(inputs: list[LoadedMetricInput]) -> list[dict[str, object]]:
    snapshots: list[dict[str, object]] = []
    for item in inputs:
        source_digest = str(item.manifest["source_digest"])
        snapshots.append(
            {
                "comparison_metric_input_id": item.comparison_metric_input_id,
                "source_ref": item.source_ref.to_mapping(),
                "source_digest": source_digest,
                "metrics": {key: item.metrics[key] for key in METRIC_KEYS},
            }
        )
    return snapshots


def build_metric_matrix(inputs: list[LoadedMetricInput]) -> dict[str, list[float | int]]:
    matrix: dict[str, list[float | int]] = {key: [] for key in METRIC_KEYS}
    for item in inputs:
        for key in METRIC_KEYS:
            matrix[key].append(item.metrics[key])
    return matrix


def build_result_manifest_body(
    *,
    comparison_definition_id: str,
    inputs: list[LoadedMetricInput],
    gate_outcomes: list[GateOutcome],
    overall_comparable: bool,
    pareto_result: dict[str, object] | None,
    ranking_result: dict[str, object],
    warnings: list[str],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": comparison_definition_id,
        "input_snapshots": build_input_snapshots(inputs),
        "metric_matrix": build_metric_matrix(inputs),
        "comparability_gate_outcomes": [_gate_to_mapping(g) for g in gate_outcomes],
        "overall_comparable": overall_comparable,
        "warnings": warnings,
        "authority_invariants": dict(CANONICAL_AUTHORITY_INVARIANTS),
    }
    if overall_comparable and pareto_result is not None:
        body["pareto_result"] = pareto_result
    body["ranking_result"] = ranking_result
    return body
