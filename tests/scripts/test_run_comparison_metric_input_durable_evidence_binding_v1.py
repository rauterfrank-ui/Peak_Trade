"""CLI tests for comparison_metric_input.v1 durable evidence binding."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_comparison_metric_input_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL,
)
from tests.meta.comparison_metric_input_v1_fixtures import build_backtest_run_dir


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _produce_manifest(tmp_path, durable_output_dir):
    run_dir, ref = build_backtest_run_dir(tmp_path)
    return produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_output_dir,
        source_ref=ref,
        run_dir=run_dir,
    )


def test_cli_successful_run(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    out = out_root / "bundle_out"
    rc = main(
        [
            "--manifest-path",
            str(produced.manifest_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()


def test_cli_requires_all_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_manifest_usage_error(tmp_path, durable_output_dir) -> None:
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    rc = main(
        [
            "--manifest-path",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_binding_error(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = tmp_path / "evidence_root" / "exists"
    out.mkdir(parents=True)
    rc = main(
        [
            "--manifest-path",
            str(produced.manifest_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_prints_success_message(tmp_path, durable_output_dir, capsys) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out_root = tmp_path / "evidence_root2"
    out_root.mkdir()
    out = out_root / "bundle_out"
    rc = main(
        [
            "--manifest-path",
            str(produced.manifest_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert produced.comparison_metric_input_id in captured.out
