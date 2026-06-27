"""Deterministic replay tests for comparison_metric_input.v1."""

from __future__ import annotations

import json

from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest, serialize_manifest
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from tests.meta.comparison_metric_input_v1_fixtures import (
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)


def test_backtest_replay_is_deterministic(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    out_a = durable_output_dir / "a"
    out_b = durable_output_dir / "b"
    out_a.mkdir()
    out_b.mkdir()
    first = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=out_a,
        source_ref=ref,
        run_dir=run_dir,
    )
    second = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=out_b,
        source_ref=ref,
        run_dir=run_dir,
    )
    assert first.comparison_metric_input_id == second.comparison_metric_input_id
    assert serialize_manifest(first.manifest) == serialize_manifest(second.manifest)


def test_experiment_replay_is_deterministic(tmp_path, durable_output_dir) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    out_a = durable_output_dir / "a"
    out_b = durable_output_dir / "b"
    out_a.mkdir()
    out_b.mkdir()
    first = produce_comparison_metric_input_v1(
        source_domain="EXPERIMENT",
        output_root=out_a,
        source_ref=exp_ref,
        manifest_dir=manifest_dir,
        completed_run_dir=completed,
    )
    second = produce_comparison_metric_input_v1(
        source_domain="EXPERIMENT",
        output_root=out_b,
        source_ref=exp_ref,
        manifest_dir=manifest_dir,
        completed_run_dir=completed,
    )
    assert first.comparison_metric_input_id == second.comparison_metric_input_id


def test_var_suite_replay_is_deterministic(tmp_path, durable_output_dir) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    out_a = durable_output_dir / "a"
    out_b = durable_output_dir / "b"
    out_a.mkdir()
    out_b.mkdir()
    first = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=out_a,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    second = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=out_b,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    assert first.comparison_metric_input_id == second.comparison_metric_input_id


def test_replay_manifest_bytes_are_stable(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    first_bytes = result.manifest_path.read_bytes()
    replay = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    assert replay.manifest_path.read_bytes() == first_bytes


def test_read_manifest_roundtrip_matches_serialized_form(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    loaded = read_manifest(result.manifest_path)
    assert json.loads(serialize_manifest(loaded)) == loaded


def test_replay_metrics_block_is_identical_across_domains(tmp_path, durable_output_dir) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    out_backtest = durable_output_dir / "backtest"
    out_var = durable_output_dir / "var"
    out_backtest.mkdir()
    out_var.mkdir()
    backtest = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=out_backtest,
        source_ref=backtest_ref,
        run_dir=run_dir,
    )
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    var_suite = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=out_var,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    assert backtest.manifest["metrics"] == var_suite.manifest["metrics"]


def test_replay_source_digest_matches_for_var_suite_companion_backtest(
    tmp_path, durable_output_dir
) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    out_backtest = durable_output_dir / "backtest"
    out_var = durable_output_dir / "var"
    out_backtest.mkdir()
    out_var.mkdir()
    backtest = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=out_backtest,
        source_ref=backtest_ref,
        run_dir=run_dir,
    )
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    var_suite = produce_comparison_metric_input_v1(
        source_domain="VAR_SUITE",
        output_root=out_var,
        source_ref=var_ref,
        suite_report_dir=suite_dir,
        companion_run_dir=run_dir,
        backtest_source_ref=backtest_ref,
    )
    assert var_suite.manifest["source_digest"] == backtest.manifest["source_digest"]


def test_replay_evaluation_slice_id_stable_for_backtest(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    ids = []
    for suffix in ("one", "two", "three"):
        out = durable_output_dir / suffix
        out.mkdir()
        result = produce_comparison_metric_input_v1(
            source_domain="BACKTEST",
            output_root=out,
            source_ref=ref,
            run_dir=run_dir,
        )
        ids.append(result.manifest["evaluation_slice_id"])
    assert len(set(ids)) == 1
