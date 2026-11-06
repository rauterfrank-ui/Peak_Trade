"""CLI tests for run_comparison_offline_v1.py."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts import run_comparison_offline_v1
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


def test_cli_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "cli_out"
    rc = run_comparison_offline_v1.main(
        [
            "--input-manifest",
            str(first),
            "--input-manifest",
            str(second),
            "--output-root",
            str(out),
            "--ranking-rule-version",
            "NONE_V1",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "comparison_definition_manifest_v1.json" in captured.out
    assert "comparison_result_manifest_v1.json" in captured.out


def test_cli_requires_two_inputs(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, _ = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    rc = run_comparison_offline_v1.main(
        [
            "--input-manifest",
            str(first),
            "--output-root",
            str(ssot_durable_output_dir / "cli_out"),
        ]
    )
    assert rc == 1
