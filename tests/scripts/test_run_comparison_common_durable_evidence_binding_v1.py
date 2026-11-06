"""CLI tests for comparison common durable evidence binding v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.run_comparison_common_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import INDEX_ARTIFACT_REL
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    for target in (
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
    ):
        monkeypatch.setattr(target, lambda _path: False)


def _produce_bound_chain(tmp_path: Path, durable_root: Path):
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
    return metric_bindings, definition_binding, result_binding, offline.comparison_definition_id


def test_cli_successful_run(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, comparison_definition_id = (
        _produce_bound_chain(tmp_path, ssot_durable_output_dir)
    )
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    out = out_root / "common_out"
    args = [
        "--definition-bound-bundle-dir",
        str(definition_binding),
        "--result-bound-bundle-dir",
        str(result_binding),
        "--output-dir",
        str(out),
    ]
    for path in metric_bindings:
        args.extend(["--metric-input-bound-bundle-dir", str(path)])
    rc = main(args)
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()


def test_cli_requires_all_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_definition_usage_error(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, _, result_binding, _ = _produce_bound_chain(tmp_path, ssot_durable_output_dir)
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    args = [
        "--definition-bound-bundle-dir",
        str(tmp_path / "missing"),
        "--result-bound-bundle-dir",
        str(result_binding),
        "--output-dir",
        str(out_root / "out"),
    ]
    for path in metric_bindings:
        args.extend(["--metric-input-bound-bundle-dir", str(path)])
    rc = main(args)
    assert rc == EXIT_USAGE_ERROR


def test_cli_binding_error(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = tmp_path / "evidence_root" / "exists"
    out.mkdir(parents=True)
    args = [
        "--definition-bound-bundle-dir",
        str(definition_binding),
        "--result-bound-bundle-dir",
        str(result_binding),
        "--output-dir",
        str(out),
    ]
    for path in metric_bindings:
        args.extend(["--metric-input-bound-bundle-dir", str(path)])
    rc = main(args)
    assert rc == EXIT_BINDING_ERROR


def test_cli_prints_success_message(tmp_path, ssot_durable_output_dir, capsys) -> None:
    metric_bindings, definition_binding, result_binding, comparison_definition_id = (
        _produce_bound_chain(tmp_path, ssot_durable_output_dir)
    )
    out_root = tmp_path / "evidence_root2"
    out_root.mkdir()
    out = out_root / "common_out"
    args = [
        "--definition-bound-bundle-dir",
        str(definition_binding),
        "--result-bound-bundle-dir",
        str(result_binding),
        "--output-dir",
        str(out),
    ]
    for path in metric_bindings:
        args.extend(["--metric-input-bound-bundle-dir", str(path)])
    rc = main(args)
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert comparison_definition_id in captured.out
