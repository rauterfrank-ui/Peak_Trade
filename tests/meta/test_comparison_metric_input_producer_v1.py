"""Producer, atomic publish, and self-verify tests for comparison_metric_input.v1."""

from __future__ import annotations

import json
import shutil

import pytest

from src.meta.learning_loop.comparison_metric_input_v1.constants import ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_metric_input_v1.io import (
    publish_manifest_atomic,
    read_manifest,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.comparison_metric_input_v1.validation import (
    validate_comparison_metric_input_manifest_v1,
)
from src.meta.learning_loop.comparison_metric_input_v1.identity import (
    verify_manifest_identity_and_integrity,
)
from tests.meta.comparison_metric_input_v1_fixtures import (
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)


def test_produce_backtest_writes_manifest_and_self_verifies(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    assert result.manifest_path.is_file()
    assert result.output_dir.name == result.comparison_metric_input_id
    validate_comparison_metric_input_manifest_v1(result.manifest)
    verify_manifest_identity_and_integrity(result.manifest)


def test_produce_backtest_is_idempotent(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    first = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    second = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    assert first.manifest_path == second.manifest_path
    assert first.comparison_metric_input_id == second.comparison_metric_input_id


def test_produce_experiment_domain_happy_path(tmp_path, durable_output_dir) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    result = produce_comparison_metric_input_v1(
        source_domain="EXPERIMENT",
        output_root=durable_output_dir,
        source_ref=exp_ref,
        manifest_dir=manifest_dir,
        completed_run_dir=completed,
    )
    assert result.manifest["source_domain"] == "EXPERIMENT"


def test_produce_var_suite_domain_includes_companion_block(tmp_path, durable_output_dir) -> None:
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
    assert result.manifest["var_suite_companion"]["companion_required"] is True


def test_produce_backtest_requires_run_dir(durable_output_dir) -> None:
    with pytest.raises(ComparisonMetricInputError, match="run_dir required"):
        produce_comparison_metric_input_v1(
            source_domain="BACKTEST",
            output_root=durable_output_dir,
            source_ref={
                "owner_domain": "x",
                "ref_type": "BACKTEST",
                "ref_id": "y",
                "digest": "d" * 64,
            },
        )


def test_produce_experiment_requires_manifest_and_completed_run(durable_output_dir) -> None:
    with pytest.raises(ComparisonMetricInputError, match="manifest_dir and completed_run_dir"):
        produce_comparison_metric_input_v1(
            source_domain="EXPERIMENT",
            output_root=durable_output_dir,
            source_ref={
                "owner_domain": "x",
                "ref_type": "EXPERIMENT",
                "ref_id": "y",
                "digest": "d" * 64,
            },
        )


def test_publish_manifest_atomic_rejects_existing_dir_without_manifest(
    tmp_path, durable_output_dir, monkeypatch
) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_v1.io.is_under_tmp",
        lambda _path: False,
    )
    run_dir, ref = build_backtest_run_dir(tmp_path)
    produced = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    orphan = produced.output_dir
    manifest_path = orphan / ARTIFACT_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    shutil.rmtree(orphan)
    orphan.mkdir()
    with pytest.raises(ComparisonMetricInputError, match="exists without manifest"):
        publish_manifest_atomic(output_root=durable_output_dir, manifest_body=payload)


def test_publish_manifest_atomic_rejects_tmp_output(
    tmp_path, durable_output_dir, monkeypatch
) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    produced = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    body = read_manifest(produced.manifest_path)
    body.pop("comparison_metric_input_id", None)
    body.pop("integrity", None)
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_v1.io.is_under_tmp",
        lambda _path: True,
    )
    with pytest.raises(ComparisonMetricInputError, match="must be outside /tmp"):
        publish_manifest_atomic(output_root=tmp_path / "tmp_root", manifest_body=body)


def test_publish_manifest_atomic_self_verifies_written_manifest(
    tmp_path, durable_output_dir
) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    produced = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )
    on_disk = json.loads(produced.manifest_path.read_text(encoding="utf-8"))
    validate_comparison_metric_input_manifest_v1(on_disk)
    verify_manifest_identity_and_integrity(on_disk)


def test_produce_unsupported_domain_fail_closed(durable_output_dir) -> None:
    with pytest.raises(ComparisonMetricInputError, match="unsupported source_domain"):
        produce_comparison_metric_input_v1(
            source_domain="UNKNOWN",
            output_root=durable_output_dir,
            source_ref={
                "owner_domain": "x",
                "ref_type": "BACKTEST",
                "ref_id": "y",
                "digest": "d" * 64,
            },
            run_dir=durable_output_dir,
        )
