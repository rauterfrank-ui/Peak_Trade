"""CLI tests for learning loop comparison completion evidence v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.run_comparison_completion_evidence_v1 import (
    EXIT_COMPLETION_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_checkpoint_v1 import produce_comparison_checkpoint_v1
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    produce_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_completion_evidence_v1 import ARTIFACT_REL
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    produce_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    produce_comparison_ssot_definition_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    produce_comparison_ssot_result_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    for target in (
        "src.meta.learning_loop.comparison_completion_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
    ):
        monkeypatch.setattr(target, lambda _path: False)


def _produce_checkpoint(tmp_path: Path, durable_root: Path) -> Path:
    metric_root = durable_root / "metric_inputs"
    metric_root.mkdir(exist_ok=True)
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    comparison_root = durable_root / "comparisons"
    comparison_root.mkdir(exist_ok=True)
    offline = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=comparison_root,
        ranking_rule_version="NONE_V1",
    )
    metric_bindings = []
    for idx, manifest_path in enumerate([first, second]):
        out = durable_root / f"metric_input_binding_{idx}"
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=manifest_path,
            output_dir=out,
        )
        metric_bindings.append(out)
    definition_binding = durable_root / "definition_binding"
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=offline.definition_path,
        output_dir=definition_binding,
    )
    result_binding = durable_root / "result_binding"
    produce_comparison_ssot_result_durable_evidence_bundle_v1(
        manifest_path=offline.result_path,
        output_dir=result_binding,
    )
    common_out = durable_root / "common_bundle"
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=common_out,
    )
    checkpoint_out = durable_root / "checkpoint"
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=checkpoint_out)
    return checkpoint_out


def test_cli_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = ssot_durable_output_dir / "completion_cli"
    rc = main(
        [
            "--checkpoint-bundle-dir",
            str(checkpoint_out),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_checkpoint(tmp_path) -> None:
    out = tmp_path / "evidence_root" / "out"
    rc = main(
        [
            "--checkpoint-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_invalid_checkpoint(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    (checkpoint_out / "MANIFEST.sha256").write_text("broken", encoding="utf-8")
    out = ssot_durable_output_dir / "bad_cli"
    rc = main(
        [
            "--checkpoint-bundle-dir",
            str(checkpoint_out),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_COMPLETION_ERROR
