"""Schema validation adversarial tests for comparison_metric_input.v1."""

from __future__ import annotations

import copy

import pytest

from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.comparison_metric_input_v1.validation import (
    validate_authority_invariants,
    validate_comparison_metric_input_manifest_v1,
    validate_comparability_metadata,
    validate_metrics_block,
    validate_var_suite_companion,
)
from tests.meta.comparison_metric_input_v1_fixtures import (
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)


def _valid_manifest(tmp_path, durable_output_dir) -> dict:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    return copy.deepcopy(dict(result.manifest))


def test_validate_comparison_metric_input_manifest_v1_accepts_produced_manifest(
    tmp_path, durable_output_dir
) -> None:
    validate_comparison_metric_input_manifest_v1(_valid_manifest(tmp_path, durable_output_dir))


def test_validate_metrics_block_rejects_unknown_key() -> None:
    metrics = {key: 1 for key in METRIC_KEYS}
    metrics["unexpected"] = 1
    with pytest.raises(ComparisonMetricInputError, match="unknown keys"):
        validate_metrics_block(metrics)


def test_validate_metrics_block_rejects_missing_key() -> None:
    metrics = {key: 1 for key in METRIC_KEYS}
    metrics.pop("sharpe")
    with pytest.raises(ComparisonMetricInputError, match="missing required key"):
        validate_metrics_block(metrics)


def test_validate_metrics_block_rejects_non_finite_sharpe() -> None:
    metrics = {key: 1 for key in METRIC_KEYS}
    metrics["sharpe"] = float("inf")
    with pytest.raises(ComparisonMetricInputError, match="must be finite"):
        validate_metrics_block(metrics)


def test_validate_metrics_block_rejects_negative_profit_factor() -> None:
    metrics = {key: 1 for key in METRIC_KEYS}
    metrics["profit_factor"] = -1.0
    with pytest.raises(ComparisonMetricInputError, match="profit_factor must be non-negative"):
        validate_metrics_block(metrics)


def test_validate_metrics_block_rejects_bool_trade_count() -> None:
    metrics = {key: 1 for key in METRIC_KEYS}
    metrics["trade_count"] = True
    with pytest.raises(ComparisonMetricInputError, match="trade_count must be integer"):
        validate_metrics_block(metrics)


def test_validate_comparability_metadata_rejects_unknown_timeframe(
    tmp_path, durable_output_dir
) -> None:
    manifest = _valid_manifest(tmp_path, durable_output_dir)
    metadata = copy.deepcopy(manifest["comparability_metadata"])
    metadata["timeframe"] = "999x"
    with pytest.raises(ComparisonMetricInputError, match="unknown timeframe"):
        validate_comparability_metadata(metadata, source_domain="BACKTEST")


def test_validate_comparability_metadata_rejects_non_zero_risk_free_rate(
    tmp_path, durable_output_dir
) -> None:
    manifest = _valid_manifest(tmp_path, durable_output_dir)
    metadata = copy.deepcopy(manifest["comparability_metadata"])
    metadata["risk_free_rate_annualized"] = 0.01
    with pytest.raises(ComparisonMetricInputError, match="must be exactly 0.0"):
        validate_comparability_metadata(metadata, source_domain="BACKTEST")


def test_validate_authority_invariants_rejects_unknown_key() -> None:
    block = {"evidence_does_not_authorize_runtime": True, "unexpected": True}
    with pytest.raises(ComparisonMetricInputError, match="unknown keys"):
        validate_authority_invariants(block)


def test_validate_manifest_rejects_source_domain_mismatch_in_metadata(
    tmp_path, durable_output_dir
) -> None:
    manifest = _valid_manifest(tmp_path, durable_output_dir)
    manifest["comparability_metadata"]["source_domain"] = "EXPERIMENT"
    with pytest.raises(ComparisonMetricInputError, match="source_domain mismatch"):
        validate_comparison_metric_input_manifest_v1(manifest)


def test_validate_manifest_rejects_evaluation_slice_id_mismatch(
    tmp_path, durable_output_dir
) -> None:
    manifest = _valid_manifest(tmp_path, durable_output_dir)
    manifest["evaluation_slice_id"] = "changed"
    with pytest.raises(ComparisonMetricInputError, match="evaluation_slice_id mismatch"):
        validate_comparison_metric_input_manifest_v1(manifest)


def test_validate_var_suite_companion_required_for_var_suite(tmp_path, durable_output_dir) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    result = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=durable_output_dir,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    manifest = copy.deepcopy(dict(result.manifest))
    manifest.pop("var_suite_companion", None)
    with pytest.raises(ComparisonMetricInputError, match="var_suite_companion required"):
        validate_comparison_metric_input_manifest_v1(manifest)


def test_validate_var_suite_companion_rejects_forbidden_on_backtest(
    tmp_path, durable_output_dir
) -> None:
    manifest = _valid_manifest(tmp_path, durable_output_dir)
    manifest["var_suite_companion"] = {"companion_required": True}
    with pytest.raises(ComparisonMetricInputError, match="only allowed for VAR_SUITE"):
        validate_comparison_metric_input_manifest_v1(manifest)


def test_validate_var_suite_companion_accepts_produced_var_suite_manifest(
    tmp_path, durable_output_dir
) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    result = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=durable_output_dir,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    validate_var_suite_companion(result.manifest["var_suite_companion"], source_domain="VAR_SUITE")
