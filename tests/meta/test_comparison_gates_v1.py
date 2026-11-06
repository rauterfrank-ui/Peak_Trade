"""Comparability gate tests for comparison_ssot.v1."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from src.meta.learning_loop.comparison_ssot_v1.comparison_gates_v1 import (
    evaluate_comparability_gates,
    overall_comparable,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_input_loader_v1 import (
    load_and_validate_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_offline_producer_v1 import (
    produce_comparison_offline_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from tests.meta.comparison_ssot_v1_fixtures import (
    produce_backtest_metric_input,
    produce_two_compatible_backtest_inputs,
)


def _load_pair(tmp_path, ssot_durable_output_dir):
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    return load_and_validate_inputs(
        list(produce_two_compatible_backtest_inputs(tmp_path, metric_root))
    )


def test_gates_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    inputs = _load_pair(tmp_path, ssot_durable_output_dir)
    outcomes = evaluate_comparability_gates(inputs)
    assert overall_comparable(outcomes)
    assert all(item.status == "PASS" for item in outcomes)


def test_timeframe_mismatch_not_comparable(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first_path = produce_backtest_metric_input(tmp_path, metric_root, run_id="tf-a", timeframe="1d")
    second_path = produce_backtest_metric_input(
        tmp_path, metric_root, run_id="tf-b", timeframe="1h"
    )
    inputs = load_and_validate_inputs([first_path, second_path])
    outcomes = evaluate_comparability_gates(inputs)
    assert not overall_comparable(outcomes)


def test_cross_domain_mix_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    from tests.meta.comparison_metric_input_v1_fixtures import (
        build_backtest_run_dir,
        build_experiment_bundle,
    )
    from src.meta.learning_loop.comparison_metric_input_v1.producer import (
        produce_comparison_metric_input_v1,
    )

    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    backtest_path = produce_backtest_metric_input(tmp_path, metric_root, run_id="bt-only")
    completed_dir, _ = build_backtest_run_dir(tmp_path / "exp_completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    experiment_path = produce_comparison_metric_input_v1(
        source_domain="EXPERIMENT",
        output_root=metric_root,
        source_ref=exp_ref,
        manifest_dir=manifest_dir,
        completed_run_dir=completed,
    ).manifest_path
    with pytest.raises(ComparisonSsotError, match="cross-domain"):
        load_and_validate_inputs([backtest_path, experiment_path])


def test_non_comparable_suppresses_pareto(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first_path = produce_backtest_metric_input(
        tmp_path, metric_root, run_id="range-a", end_date="2025-01-20"
    )
    second_path = produce_backtest_metric_input(
        tmp_path, metric_root, run_id="range-b", end_date="2025-02-20"
    )
    produced = produce_comparison_offline_v1(
        input_manifest_paths=[first_path, second_path],
        output_root=ssot_durable_output_dir / "bad",
        ranking_rule_version="NONE_V1",
    )
    assert produced.result_manifest["overall_comparable"] is False
    assert "pareto_result" not in produced.result_manifest


def test_duplicate_input_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, _ = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    with pytest.raises(ComparisonSsotError, match="duplicate"):
        load_and_validate_inputs([first, first])
