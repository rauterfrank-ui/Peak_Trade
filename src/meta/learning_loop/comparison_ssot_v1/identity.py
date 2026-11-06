"""Content-addressed identity for comparison_definition_manifest_v1."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.meta.learning_loop.comparison_ssot_v1.constants import (
    COMPARABILITY_GATE_VERSION,
    COMPARISON_CONTRACT_VERSION,
    ELIGIBILITY_RULES_VERSION,
    IDENTITY_DOMAIN_SEPARATOR,
    METRIC_SET_VERSION,
    NORMALIZATION_POLICY_VERSION,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    validate_integrity_block,
)

DEFINITION_IDENTITY_FIELD_ORDER: tuple[str, ...] = (
    "comparison_contract_version",
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
)


def build_definition_identity_payload(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in DEFINITION_IDENTITY_FIELD_ORDER:
        if field not in manifest_body:
            raise ComparisonSsotError(f"definition identity payload missing field: {field}")
        payload[field] = deepcopy(manifest_body[field])
    return payload


def compute_comparison_definition_id(manifest_body: Mapping[str, Any]) -> str:
    payload = build_definition_identity_payload(manifest_body)
    return compute_content_sha256(payload)


def build_manifest_without_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = deepcopy(dict(manifest_body))
    body.pop("comparison_definition_id", None)
    body.pop("integrity", None)
    return body


def attach_definition_identity_and_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = build_manifest_without_integrity(manifest_body)
    if body.get("identity_domain") != IDENTITY_DOMAIN_SEPARATOR:
        raise ComparisonSsotError("identity_domain mismatch for comparison definition")
    comparison_definition_id = compute_comparison_definition_id(body)
    digest = compute_content_sha256(body)
    body["comparison_definition_id"] = comparison_definition_id
    body["integrity"] = {"content_sha256": digest}
    return body


def compute_definition_integrity_digest(manifest: Mapping[str, Any]) -> str:
    return compute_content_sha256(build_manifest_without_integrity(manifest))


def verify_definition_identity_and_integrity(manifest: Mapping[str, Any]) -> None:
    expected_id = compute_comparison_definition_id(manifest)
    actual_id = manifest.get("comparison_definition_id")
    if actual_id != expected_id:
        raise ComparisonSsotError("comparison_definition_id mismatch")
    expected_digest = compute_definition_integrity_digest(manifest)
    result = validate_integrity_block(manifest.get("integrity"), expected_digest=expected_digest)
    if not result.valid:
        raise ComparisonSsotError("; ".join(result.errors))


def build_result_manifest_without_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = deepcopy(dict(manifest_body))
    body.pop("integrity", None)
    return body


def attach_result_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = build_result_manifest_without_integrity(manifest_body)
    digest = compute_content_sha256(body)
    body["integrity"] = {"content_sha256": digest}
    return body


def compute_result_integrity_digest(manifest: Mapping[str, Any]) -> str:
    return compute_content_sha256(build_result_manifest_without_integrity(manifest))


def verify_result_integrity(manifest: Mapping[str, Any]) -> None:
    expected_digest = compute_result_integrity_digest(manifest)
    result = validate_integrity_block(manifest.get("integrity"), expected_digest=expected_digest)
    if not result.valid:
        raise ComparisonSsotError("; ".join(result.errors))


def build_definition_body(
    *,
    input_refs: list[dict[str, str]],
    ranking_rule_version: str,
    tie_rule_version: str,
    evaluation_slice_id: str,
    authority_invariants: Mapping[str, str | bool],
) -> dict[str, Any]:
    return {
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "identity_domain": IDENTITY_DOMAIN_SEPARATOR,
        "input_refs": input_refs,
        "metric_set_version": METRIC_SET_VERSION,
        "comparability_gate_version": COMPARABILITY_GATE_VERSION,
        "normalization_policy_version": NORMALIZATION_POLICY_VERSION,
        "ranking_rule_version": ranking_rule_version,
        "tie_rule_version": tie_rule_version,
        "evaluation_slice_id": evaluation_slice_id,
        "eligibility_rules_version": ELIGIBILITY_RULES_VERSION,
        "authority_invariants": dict(authority_invariants),
    }
