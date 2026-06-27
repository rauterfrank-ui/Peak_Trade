"""Definition manifest and identity tests for comparison_ssot.v1."""

from __future__ import annotations

import copy

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from src.meta.learning_loop.comparison_ssot_v1.comparison_input_loader_v1 import (
    load_and_validate_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_offline_producer_v1 import (
    produce_comparison_offline_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.identity import (
    compute_comparison_definition_id,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_definition_manifest_v1
from tests.meta.comparison_ssot_v1_fixtures import (
    produce_backtest_metric_input,
    produce_two_compatible_backtest_inputs,
)


def test_definition_valid_with_two_inputs(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "cmp"
    result = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=out,
        ranking_rule_version="NONE_V1",
    )
    validate_definition_manifest_v1(result.definition_manifest)


def test_definition_rejects_single_input(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    only = produce_backtest_metric_input(tmp_path, metric_root, run_id="solo-run")
    with pytest.raises(ComparisonSsotError, match="at least 2"):
        load_and_validate_inputs([only])


def test_definition_id_stable_across_input_order(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out_a = ssot_durable_output_dir / "cmp_a"
    out_b = ssot_durable_output_dir / "cmp_b"
    res_a = produce_comparison_offline_v1(
        input_manifest_paths=[first, second], output_root=out_a, ranking_rule_version="NONE_V1"
    )
    res_b = produce_comparison_offline_v1(
        input_manifest_paths=[second, first], output_root=out_b, ranking_rule_version="NONE_V1"
    )
    assert res_a.comparison_definition_id == res_b.comparison_definition_id


def test_definition_id_changes_when_input_digest_changes(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out1 = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=ssot_durable_output_dir / "c1",
        ranking_rule_version="NONE_V1",
    )
    third = produce_backtest_metric_input(tmp_path, metric_root, run_id="cmp-ssot-run-c")
    out2 = produce_comparison_offline_v1(
        input_manifest_paths=[first, third],
        output_root=ssot_durable_output_dir / "c2",
        ranking_rule_version="NONE_V1",
    )
    assert out1.comparison_definition_id != out2.comparison_definition_id


def test_integrity_tamper_detected(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    result = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=ssot_durable_output_dir / "cmp",
        ranking_rule_version="NONE_V1",
    )
    tampered = copy.deepcopy(dict(result.definition_manifest))
    tampered["integrity"] = {"content_sha256": "0" * 64}
    with pytest.raises(ComparisonSsotError):
        validate_definition_manifest_v1(tampered)
