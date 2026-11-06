"""End-to-end producer tests for comparison_ssot.v1."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from src.meta.learning_loop.comparison_ssot_v1.comparison_offline_producer_v1 import (
    produce_comparison_offline_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    DEFINITION_ARTIFACT_FILENAME,
    RESULT_ARTIFACT_FILENAME,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.validation import (
    validate_definition_manifest_v1,
    validate_result_manifest_v1,
)
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


def test_producer_writes_definition_and_result(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    result = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=ssot_durable_output_dir / "out",
        ranking_rule_version="NONE_V1",
    )
    assert result.definition_path.name == DEFINITION_ARTIFACT_FILENAME
    assert result.result_path.name == RESULT_ARTIFACT_FILENAME
    validate_definition_manifest_v1(result.definition_manifest)
    validate_result_manifest_v1(result.result_manifest)


def test_producer_idempotent(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "out"
    one = produce_comparison_offline_v1(
        input_manifest_paths=[first, second], output_root=out, ranking_rule_version="NONE_V1"
    )
    two = produce_comparison_offline_v1(
        input_manifest_paths=[first, second], output_root=out, ranking_rule_version="NONE_V1"
    )
    assert one.definition_path == two.definition_path
    assert one.result_path == two.result_path


def test_producer_atomic_no_partial_artifacts(
    tmp_path, ssot_durable_output_dir, monkeypatch
) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "out"

    def boom(self, target):
        raise OSError("simulated publish failure")

    monkeypatch.setattr(
        "pathlib.Path.replace",
        boom,
    )
    with pytest.raises(OSError):
        produce_comparison_offline_v1(
            input_manifest_paths=[first, second], output_root=out, ranking_rule_version="NONE_V1"
        )
    assert not any(out.iterdir()) if out.exists() else True


def test_snapshot_digest_consistency(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    produced = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=ssot_durable_output_dir / "out",
        ranking_rule_version="NONE_V1",
    )
    for snap in produced.result_manifest["input_snapshots"]:
        assert (
            snap["source_digest"]
            == read_manifest(
                next(
                    p
                    for p in [first, second]
                    if str(read_manifest(p)["comparison_metric_input_id"])
                    == snap["comparison_metric_input_id"]
                )
            )["source_digest"]
        )


def test_unknown_ranking_version_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    with pytest.raises(ComparisonSsotError, match="unknown ranking_rule_version"):
        produce_comparison_offline_v1(
            input_manifest_paths=[first, second],
            output_root=ssot_durable_output_dir / "out",
            ranking_rule_version="bad_rule_v9",
        )
