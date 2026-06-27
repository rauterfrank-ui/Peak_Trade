"""Manifest validation for comparison_ssot.v1."""

from __future__ import annotations

from typing import Any, Mapping

from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    CANONICAL_AUTHORITY_INVARIANTS,
    COMPARABILITY_GATE_VERSION,
    COMPARISON_CONTRACT_VERSION,
    ELIGIBILITY_RULES_VERSION,
    IDENTITY_DOMAIN_SEPARATOR,
    METRIC_SET_VERSION,
    NORMALIZATION_POLICY_VERSION,
    RANKING_RULE_NONE,
)
from src.meta.learning_loop.comparison_ssot_v1.identity import (
    verify_definition_identity_and_integrity,
    verify_result_integrity,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex


def _require_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ComparisonSsotError(f"{label} must be object")
    return value


def validate_input_ref(ref: Any, *, label: str) -> None:
    mapping = _require_mapping(ref, label=label)
    for key in ("owner_domain", "ref_type", "ref_id", "digest"):
        if key not in mapping or not isinstance(mapping[key], str) or not mapping[key].strip():
            raise ComparisonSsotError(f"{label}.{key} must be non-empty string")
    if not is_valid_sha256_hex(str(mapping["digest"])):
        raise ComparisonSsotError(f"{label}.digest must be sha256 hex")


def validate_definition_manifest_v1(manifest: Mapping[str, Any]) -> None:
    for key in (
        "comparison_contract_version",
        "comparison_definition_id",
        "identity_domain",
        "input_refs",
        "metric_set_version",
        "comparability_gate_version",
        "normalization_policy_version",
        "ranking_rule_version",
        "tie_rule_version",
        "evaluation_slice_id",
        "eligibility_rules_version",
        "authority_invariants",
        "integrity",
    ):
        if key not in manifest:
            raise ComparisonSsotError(f"definition manifest missing {key}")

    if manifest["comparison_contract_version"] != COMPARISON_CONTRACT_VERSION:
        raise ComparisonSsotError("comparison_contract_version mismatch")
    if manifest["identity_domain"] != IDENTITY_DOMAIN_SEPARATOR:
        raise ComparisonSsotError("identity_domain mismatch")
    if manifest["metric_set_version"] != METRIC_SET_VERSION:
        raise ComparisonSsotError("metric_set_version mismatch")
    if manifest["comparability_gate_version"] != COMPARABILITY_GATE_VERSION:
        raise ComparisonSsotError("comparability_gate_version mismatch")
    if manifest["normalization_policy_version"] != NORMALIZATION_POLICY_VERSION:
        raise ComparisonSsotError("normalization_policy_version mismatch")
    if manifest["eligibility_rules_version"] != ELIGIBILITY_RULES_VERSION:
        raise ComparisonSsotError("eligibility_rules_version mismatch")

    input_refs = manifest["input_refs"]
    if not isinstance(input_refs, list) or len(input_refs) < 2:
        raise ComparisonSsotError("input_refs must contain at least 2 entries")
    for idx, ref in enumerate(input_refs):
        validate_input_ref(ref, label=f"input_refs[{idx}]")

    authority = _require_mapping(manifest["authority_invariants"], label="authority_invariants")
    for key, expected in CANONICAL_AUTHORITY_INVARIANTS.items():
        if authority.get(key) != expected:
            raise ComparisonSsotError(f"authority_invariants.{key} mismatch")

    verify_definition_identity_and_integrity(manifest)


def validate_result_manifest_v1(manifest: Mapping[str, Any]) -> None:
    forbidden = {"winner", "selection", "acceptance", "promotion_status", "runtime_status"}
    for key in forbidden:
        if key in manifest:
            raise ComparisonSsotError(f"forbidden result field: {key}")

    for key in (
        "comparison_contract_version",
        "comparison_definition_id",
        "input_snapshots",
        "metric_matrix",
        "comparability_gate_outcomes",
        "overall_comparable",
        "authority_invariants",
        "integrity",
    ):
        if key not in manifest:
            raise ComparisonSsotError(f"result manifest missing {key}")

    if manifest["comparison_contract_version"] != COMPARISON_CONTRACT_VERSION:
        raise ComparisonSsotError("comparison_contract_version mismatch")

    snapshots = manifest["input_snapshots"]
    if not isinstance(snapshots, list) or not snapshots:
        raise ComparisonSsotError("input_snapshots must be non-empty list")

    for idx, snap in enumerate(snapshots):
        mapping = _require_mapping(snap, label=f"input_snapshots[{idx}]")
        for field in (
            "comparison_metric_input_id",
            "source_ref",
            "source_digest",
            "metrics",
        ):
            if field not in mapping:
                raise ComparisonSsotError(f"input_snapshots[{idx}] missing {field}")
        validate_input_ref(mapping["source_ref"], label=f"input_snapshots[{idx}].source_ref")
        if not is_valid_sha256_hex(str(mapping["source_digest"])):
            raise ComparisonSsotError(f"input_snapshots[{idx}].source_digest invalid")
        metrics = _require_mapping(mapping["metrics"], label=f"input_snapshots[{idx}].metrics")
        if set(metrics.keys()) != set(METRIC_KEYS):
            raise ComparisonSsotError(f"input_snapshots[{idx}] metric keys invalid")

    matrix = _require_mapping(manifest["metric_matrix"], label="metric_matrix")
    if set(matrix.keys()) != set(METRIC_KEYS):
        raise ComparisonSsotError("metric_matrix keys invalid")

    ranking = manifest.get("ranking_result")
    if ranking is not None:
        ranking_map = _require_mapping(ranking, label="ranking_result")
        if ranking_map.get("ranking_rule_version", RANKING_RULE_NONE) == RANKING_RULE_NONE:
            if ranking_map.get("ranking_status") not in (None, "NONE"):
                raise ComparisonSsotError("ranking_status inconsistent with NONE rule")

    authority = _require_mapping(manifest["authority_invariants"], label="authority_invariants")
    for key, expected in CANONICAL_AUTHORITY_INVARIANTS.items():
        if authority.get(key) != expected:
            raise ComparisonSsotError(f"authority_invariants.{key} mismatch")

    verify_result_integrity(manifest)
