"""CLI tests for comparison completion research validity binding v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
]

from scripts.run_comparison_completion_research_validity_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import ARTIFACT_REL
from tests.meta.comparison_completion_research_validity_binding_v1_fixtures import (
    produce_matched_completion_and_validity_bundles,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.research_validity_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "binding_cli_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--completion-evidence-bundle-dir",
            str(matched.completion_bundle_dir),
            "--research-validity-evidence-bundle-dir",
            str(matched.research_validity_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_completion_bundle(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--completion-evidence-bundle-dir",
            str(tmp_path / "missing"),
            "--research-validity-evidence-bundle-dir",
            str(matched.research_validity_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_missing_validity_bundle(tmp_path, ssot_durable_output_dir) -> None:
    matched = produce_matched_completion_and_validity_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--completion-evidence-bundle-dir",
            str(matched.completion_bundle_dir),
            "--research-validity-evidence-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_binding_error_on_lineage_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    root_a = ssot_durable_output_dir / "cli_a"
    root_b = ssot_durable_output_dir / "cli_b"
    root_a.mkdir(parents=True, exist_ok=True)
    root_b.mkdir(parents=True, exist_ok=True)
    matched_a = produce_matched_completion_and_validity_bundles(tmp_path / "cli_case_a", root_a)
    matched_b = produce_matched_completion_and_validity_bundles(tmp_path / "cli_case_b", root_b)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--completion-evidence-bundle-dir",
            str(matched_a.completion_bundle_dir),
            "--research-validity-evidence-bundle-dir",
            str(matched_b.research_validity_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR
