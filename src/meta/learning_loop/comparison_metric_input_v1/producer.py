"""Generic offline producer for comparison_metric_input.v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.comparison_metric_input_v1.adapters import (
    adapt_backtest_domain,
    adapt_experiment_domain,
    adapt_var_suite_domain,
)
from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    ARTIFACT_FILENAME,
    CANONICAL_AUTHORITY_INVARIANTS,
    COMPARABILITY_METADATA_VERSION,
    COMPARISON_METRIC_INPUT_CONTRACT_VERSION,
    METRIC_SEMANTICS_VERSION,
    METRIC_SET_VERSION,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import (
    publish_manifest_atomic,
    read_manifest,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import (
    AdapterResult,
    ComparisonMetricInputError,
    ComparisonMetricInputResult,
)


def _adapter_result_to_manifest_body(result: AdapterResult) -> dict[str, Any]:
    body: dict[str, Any] = {
        "comparison_metric_input_contract_version": COMPARISON_METRIC_INPUT_CONTRACT_VERSION,
        "metric_set_version": METRIC_SET_VERSION,
        "metric_semantics_version": METRIC_SEMANTICS_VERSION,
        "comparability_metadata_version": COMPARABILITY_METADATA_VERSION,
        "source_domain": result.source_domain,
        "source_ref": result.source_ref.to_mapping(),
        "source_digest": result.source_digest,
        "evaluation_slice_id": result.evaluation_slice_id,
        "comparability_metadata": result.comparability_metadata,
        "metrics": dict(result.metrics),
        "authority_invariants": dict(CANONICAL_AUTHORITY_INVARIANTS),
    }
    if result.var_suite_companion is not None:
        body["var_suite_companion"] = result.var_suite_companion
    return body


def produce_comparison_metric_input_v1(
    *,
    source_domain: str,
    output_root: Path,
    source_ref: Mapping[str, Any],
    run_dir: Path | None = None,
    manifest_dir: Path | None = None,
    completed_run_dir: Path | None = None,
    suite_report_dir: Path | None = None,
    companion_run_dir: Path | None = None,
    backtest_source_ref: Mapping[str, Any] | None = None,
    evaluation_slice_id: str | None = None,
) -> ComparisonMetricInputResult:
    domain = source_domain.upper()
    if domain == "BACKTEST":
        if run_dir is None:
            raise ComparisonMetricInputError("run_dir required for BACKTEST domain")
        adapter_result = adapt_backtest_domain(run_dir=run_dir, source_ref=source_ref)
    elif domain == "EXPERIMENT":
        if manifest_dir is None or completed_run_dir is None:
            raise ComparisonMetricInputError(
                "manifest_dir and completed_run_dir required for EXPERIMENT domain"
            )
        adapter_result = adapt_experiment_domain(
            manifest_dir=manifest_dir,
            completed_run_dir=completed_run_dir,
            source_ref=source_ref,
        )
    elif domain == "VAR_SUITE":
        if suite_report_dir is None or companion_run_dir is None or backtest_source_ref is None:
            raise ComparisonMetricInputError(
                "suite_report_dir, companion_run_dir, and backtest_source_ref required for VAR_SUITE"
            )
        adapter_result = adapt_var_suite_domain(
            suite_report_dir=suite_report_dir,
            companion_run_dir=companion_run_dir,
            var_suite_source_ref=source_ref,
            backtest_source_ref=backtest_source_ref,
            evaluation_slice_id=evaluation_slice_id,
        )
    else:
        raise ComparisonMetricInputError(f"unsupported source_domain: {source_domain}")

    manifest_body = _adapter_result_to_manifest_body(adapter_result)
    manifest_path = publish_manifest_atomic(output_root=output_root, manifest_body=manifest_body)
    manifest = read_manifest(manifest_path)
    return ComparisonMetricInputResult(
        output_dir=manifest_path.parent,
        manifest_path=manifest_path,
        comparison_metric_input_id=str(manifest["comparison_metric_input_id"]),
        manifest=manifest,
    )
