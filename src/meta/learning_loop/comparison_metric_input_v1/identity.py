"""Content-addressed identity for comparison_metric_input.v1."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    COMPARABILITY_METADATA_VERSION,
    COMPARISON_METRIC_INPUT_CONTRACT_VERSION,
    IDENTITY_DOMAIN_SEPARATOR,
    METRIC_SEMANTICS_VERSION,
    METRIC_SET_VERSION,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    validate_integrity_block,
)


IDENTITY_PAYLOAD_FIELD_ORDER: tuple[str, ...] = (
    "comparison_metric_input_contract_version",
    "metric_set_version",
    "metric_semantics_version",
    "comparability_metadata_version",
    "source_domain",
    "source_ref",
    "source_digest",
    "evaluation_slice_id",
    "comparability_metadata",
    "metrics",
    "var_suite_companion",
    "authority_invariants",
)


def build_identity_payload(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in IDENTITY_PAYLOAD_FIELD_ORDER:
        if field not in manifest_body:
            if field == "var_suite_companion":
                payload[field] = None
                continue
            raise ComparisonMetricInputError(f"identity payload missing field: {field}")
        value = manifest_body[field]
        payload[field] = deepcopy(value)
    return payload


def compute_comparison_metric_input_id(manifest_body: Mapping[str, Any]) -> str:
    identity_payload = build_identity_payload(manifest_body)
    identity_payload["identity_domain"] = IDENTITY_DOMAIN_SEPARATOR
    return compute_content_sha256(identity_payload)


def build_manifest_without_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = deepcopy(dict(manifest_body))
    body.pop("comparison_metric_input_id", None)
    body.pop("integrity", None)
    return body


def attach_identity_and_integrity(manifest_body: Mapping[str, Any]) -> dict[str, Any]:
    body = build_manifest_without_integrity(manifest_body)
    comparison_metric_input_id = compute_comparison_metric_input_id(body)
    digest = compute_content_sha256(body)
    body["comparison_metric_input_id"] = comparison_metric_input_id
    body["integrity"] = {"content_sha256": digest}
    return body


def compute_integrity_digest(manifest: Mapping[str, Any]) -> str:
    return compute_content_sha256(build_manifest_without_integrity(manifest))


def verify_manifest_identity_and_integrity(manifest: Mapping[str, Any]) -> None:
    expected_id = compute_comparison_metric_input_id(manifest)
    actual_id = manifest.get("comparison_metric_input_id")
    if actual_id != expected_id:
        raise ComparisonMetricInputError("comparison_metric_input_id mismatch")
    expected_digest = compute_integrity_digest(manifest)
    result = validate_integrity_block(manifest.get("integrity"), expected_digest=expected_digest)
    if not result.valid:
        raise ComparisonMetricInputError("; ".join(result.errors))
