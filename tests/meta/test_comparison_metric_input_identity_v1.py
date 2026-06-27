"""Identity and digest tests for comparison_metric_input.v1."""

from __future__ import annotations

import copy

import pytest

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    COMPARISON_METRIC_INPUT_CONTRACT_VERSION,
    IDENTITY_DOMAIN_SEPARATOR,
)
from src.meta.learning_loop.comparison_metric_input_v1.identity import (
    IDENTITY_PAYLOAD_FIELD_ORDER,
    attach_identity_and_integrity,
    build_identity_payload,
    build_manifest_without_integrity,
    compute_comparison_metric_input_id,
    compute_integrity_digest,
    verify_manifest_identity_and_integrity,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.meta.comparison_metric_input_v1_fixtures import build_backtest_run_dir


def _produce_backtest_manifest(tmp_path, durable_output_dir):
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    return result.manifest


def test_identity_payload_field_order_is_stable() -> None:
    assert IDENTITY_PAYLOAD_FIELD_ORDER[0] == "comparison_metric_input_contract_version"
    assert IDENTITY_PAYLOAD_FIELD_ORDER[-1] == "authority_invariants"


def test_build_identity_payload_includes_var_suite_companion_none(
    tmp_path, durable_output_dir
) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    payload = build_identity_payload(manifest)
    assert payload["var_suite_companion"] is None


def test_compute_comparison_metric_input_id_uses_identity_domain_separator(
    tmp_path, durable_output_dir
) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    body = build_manifest_without_integrity(manifest)
    payload = build_identity_payload(body)
    payload["identity_domain"] = IDENTITY_DOMAIN_SEPARATOR
    expected = compute_content_sha256(payload)
    assert manifest["comparison_metric_input_id"] == expected


def test_attach_identity_and_integrity_is_deterministic(tmp_path, durable_output_dir) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    body = build_manifest_without_integrity(manifest)
    first = attach_identity_and_integrity(body)
    second = attach_identity_and_integrity(body)
    assert first["comparison_metric_input_id"] == second["comparison_metric_input_id"]
    assert first["integrity"] == second["integrity"]


def test_compute_integrity_digest_matches_integrity_block(tmp_path, durable_output_dir) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    assert compute_integrity_digest(manifest) == manifest["integrity"]["content_sha256"]


def test_verify_manifest_identity_and_integrity_accepts_valid_manifest(
    tmp_path, durable_output_dir
) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    verify_manifest_identity_and_integrity(manifest)


def test_verify_manifest_identity_and_integrity_rejects_id_mismatch(
    tmp_path, durable_output_dir
) -> None:
    manifest = copy.deepcopy(_produce_backtest_manifest(tmp_path, durable_output_dir))
    manifest["comparison_metric_input_id"] = "0" * 64
    with pytest.raises(ComparisonMetricInputError, match="comparison_metric_input_id mismatch"):
        verify_manifest_identity_and_integrity(manifest)


def test_verify_manifest_identity_and_integrity_rejects_integrity_mismatch(
    tmp_path, durable_output_dir
) -> None:
    manifest = copy.deepcopy(_produce_backtest_manifest(tmp_path, durable_output_dir))
    manifest["integrity"] = {"content_sha256": "0" * 64}
    with pytest.raises(ComparisonMetricInputError):
        verify_manifest_identity_and_integrity(manifest)


def test_build_manifest_without_integrity_strips_identity_fields(
    tmp_path, durable_output_dir
) -> None:
    manifest = _produce_backtest_manifest(tmp_path, durable_output_dir)
    stripped = build_manifest_without_integrity(manifest)
    assert "comparison_metric_input_id" not in stripped
    assert "integrity" not in stripped
    assert (
        stripped["comparison_metric_input_contract_version"]
        == COMPARISON_METRIC_INPUT_CONTRACT_VERSION
    )


def test_identity_payload_missing_required_field_fail_closed() -> None:
    with pytest.raises(ComparisonMetricInputError, match="identity payload missing field"):
        build_identity_payload(
            {"comparison_metric_input_contract_version": COMPARISON_METRIC_INPUT_CONTRACT_VERSION}
        )
