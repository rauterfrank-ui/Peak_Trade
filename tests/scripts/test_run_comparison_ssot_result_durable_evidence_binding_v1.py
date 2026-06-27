"""CLI tests for comparison_ssot.v1 result durable evidence binding."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.run_comparison_ssot_result_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL,
)
from tests.meta.comparison_ssot_v1_fixtures import produce_comparison_pair


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def test_cli_successful_run(tmp_path, ssot_durable_output_dir) -> None:
    _, result_path, _ = produce_comparison_pair(
        tmp_path, ssot_durable_output_dir, ranking_rule_version="NONE_V1"
    )
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    out = out_root / "bundle_out"
    rc = main(
        [
            "--manifest-path",
            str(result_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()


def test_cli_requires_all_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_manifest_usage_error(tmp_path) -> None:
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


def test_cli_binding_error(tmp_path, ssot_durable_output_dir) -> None:
    _, result_path, _ = produce_comparison_pair(
        tmp_path, ssot_durable_output_dir, ranking_rule_version="NONE_V1"
    )
    out = tmp_path / "evidence_root" / "exists"
    out.mkdir(parents=True)
    rc = main(
        [
            "--manifest-path",
            str(result_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_prints_success_message(tmp_path, ssot_durable_output_dir, capsys) -> None:
    _, result_path, comparison_definition_id = produce_comparison_pair(
        tmp_path, ssot_durable_output_dir, ranking_rule_version="NONE_V1"
    )
    out_root = tmp_path / "evidence_root2"
    out_root.mkdir()
    out = out_root / "bundle_out"
    rc = main(
        [
            "--manifest-path",
            str(result_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert comparison_definition_id in captured.out
