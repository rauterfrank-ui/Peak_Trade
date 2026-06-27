"""Adapter tests for BACKTEST, EXPERIMENT, and VAR_SUITE comparison_metric_input.v1."""

from __future__ import annotations

import json

import pytest

from src.meta.learning_loop.comparison_metric_input_v1.adapters.backtest import (
    adapt_backtest_domain,
)
from src.meta.learning_loop.comparison_metric_input_v1.adapters.experiment import (
    adapt_experiment_domain,
)
from src.meta.learning_loop.comparison_metric_input_v1.adapters.var_suite import (
    adapt_var_suite_domain,
)
from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.source_binding import (
    verify_digest_matches_file,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON
from tests.meta.comparison_metric_input_v1_fixtures import (
    GOLDEN_METRICS,
    GOLDEN_SOURCE_DIGEST,
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)


def test_adapt_backtest_domain_happy_path(tmp_path) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = adapt_backtest_domain(run_dir=run_dir, source_ref=ref)
    assert result.source_domain == "BACKTEST"
    assert result.metrics == GOLDEN_METRICS
    assert result.source_digest == GOLDEN_SOURCE_DIGEST
    assert set(result.metrics) == set(METRIC_KEYS)


def test_adapt_backtest_domain_rejects_bad_digest(tmp_path) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    bad = dict(ref)
    bad["digest"] = "0" * 64
    with pytest.raises(ComparisonMetricInputError, match="digest mismatch"):
        adapt_backtest_domain(run_dir=run_dir, source_ref=bad)


def test_adapt_backtest_domain_rejects_non_finished_run(tmp_path) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    summary_path = run_dir / "run_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["status"] = "RUNNING"
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonMetricInputError, match="must be FINISHED"):
        adapt_backtest_domain(run_dir=run_dir, source_ref=ref)


def test_adapt_backtest_domain_rejects_missing_equity(tmp_path) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    (run_dir / "equity.csv").unlink()
    with pytest.raises((ComparisonMetricInputError, FileNotFoundError), match="equity"):
        adapt_backtest_domain(run_dir=run_dir, source_ref=ref)


def test_adapt_experiment_domain_happy_path(tmp_path) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    result = adapt_experiment_domain(
        manifest_dir=manifest_dir,
        completed_run_dir=completed,
        source_ref=exp_ref,
    )
    assert result.source_domain == "EXPERIMENT"
    assert result.metrics["trade_count"] == GOLDEN_METRICS["trade_count"]


def test_adapt_experiment_domain_rejects_missing_completed_run_summary(tmp_path) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    (completed / "run_summary.json").unlink()
    with pytest.raises(ComparisonMetricInputError, match="missing run_summary.json"):
        adapt_experiment_domain(
            manifest_dir=manifest_dir,
            completed_run_dir=completed,
            source_ref=exp_ref,
        )


def test_adapt_experiment_domain_rejects_ref_id_mismatch(tmp_path) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    bad = dict(exp_ref)
    bad["ref_id"] = "wrong-id"
    with pytest.raises(ComparisonMetricInputError, match="ref_id mismatch"):
        adapt_experiment_domain(
            manifest_dir=manifest_dir,
            completed_run_dir=completed,
            source_ref=bad,
        )


def test_adapt_var_suite_domain_happy_path(tmp_path) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    result = adapt_var_suite_domain(
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        var_suite_source_ref=var_ref,
        backtest_source_ref=backtest_ref,
    )
    assert result.source_domain == "VAR_SUITE"
    assert result.var_suite_companion is not None
    assert result.metrics == GOLDEN_METRICS


def test_adapt_var_suite_domain_rejects_suite_report_metrics(tmp_path) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir = tmp_path / "suite_run_candidate"
    suite_dir.mkdir()
    report = {"overall_result": "PASS", "checks": [], "sharpe": 1.0}
    (suite_dir / SUITE_REPORT_JSON).write_text(json.dumps(report), encoding="utf-8")
    from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
        produce_var_suite_lineage_ref_v1,
    )
    from src.governance.promotion_loop.candidate_lineage_manifest_v1 import lineage_ref_to_mapping
    from tests.meta.comparison_metric_input_v1_fixtures import comparison_source_ref

    var_ref = comparison_source_ref(
        lineage_ref_to_mapping(produce_var_suite_lineage_ref_v1(report_dir=suite_dir).ref)
    )
    with pytest.raises(
        ComparisonMetricInputError, match="must not supply trading performance metrics"
    ):
        adapt_var_suite_domain(
            suite_report_dir=suite_dir,
            companion_run_dir=run_dir,
            var_suite_source_ref=var_ref,
            backtest_source_ref=backtest_ref,
        )


def test_adapt_var_suite_domain_rejects_ref_id_not_equal_dir_name(tmp_path) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    bad = dict(var_ref)
    bad["ref_id"] = "not-the-dir-name"
    with pytest.raises(ComparisonMetricInputError, match="ref_id must equal suite_report_dir.name"):
        adapt_var_suite_domain(
            suite_report_dir=suite_dir,
            companion_run_dir=run_dir,
            var_suite_source_ref=bad,
            backtest_source_ref=backtest_ref,
        )


def test_adapt_var_suite_domain_rejects_evaluation_slice_override_mismatch(tmp_path) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    with pytest.raises(ComparisonMetricInputError, match="evaluation_slice_id mismatch"):
        adapt_var_suite_domain(
            suite_report_dir=suite_dir,
            companion_run_dir=run_dir,
            var_suite_source_ref=var_ref,
            backtest_source_ref=backtest_ref,
            evaluation_slice_id="deadbeef" * 8,
        )


def test_adapt_backtest_verify_digest_matches_file_detects_file_tampering(tmp_path) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    adapt_backtest_domain(run_dir=run_dir, source_ref=ref)
    summary_path = run_dir / "run_summary.json"
    with pytest.raises(ComparisonMetricInputError, match="digest mismatch"):
        verify_digest_matches_file(summary_path, "0" * 64, label="run_summary.json")
