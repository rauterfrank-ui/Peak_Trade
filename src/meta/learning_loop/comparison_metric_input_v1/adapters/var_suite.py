"""VAR_SUITE domain adapter for comparison_metric_input.v1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import VAR_SUITE_OWNER_DOMAIN
from src.meta.learning_loop.comparison_metric_input_v1.adapters.backtest import (
    adapt_backtest_domain,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import (
    AdapterResult,
    ComparisonMetricInputError,
    SourceRef,
)
from src.meta.learning_loop.comparison_metric_input_v1.source_binding import (
    load_json_object,
    verify_digest_matches_file,
    verify_source_ref,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_var_suite_lineage_ref(
    *,
    suite_report_dir: Path,
    source_ref: Mapping[str, Any],
) -> SourceRef:
    ref = verify_source_ref(source_ref, expected_domain="VAR_SUITE")
    if ref.owner_domain != VAR_SUITE_OWNER_DOMAIN:
        raise ComparisonMetricInputError("VAR_SUITE source_ref owner_domain mismatch")
    report_path = suite_report_dir / SUITE_REPORT_JSON
    if not report_path.is_file():
        raise ComparisonMetricInputError(f"{SUITE_REPORT_JSON} not found in suite_report_dir")
    if ref.ref_id != suite_report_dir.name:
        raise ComparisonMetricInputError(
            "VAR_SUITE source_ref ref_id must equal suite_report_dir.name"
        )
    expected_digest = _sha256_file(report_path)
    if ref.digest != expected_digest:
        raise ComparisonMetricInputError(
            "VAR_SUITE source_ref digest mismatch with suite_report.json bytes"
        )
    verify_digest_matches_file(report_path, expected_digest, label=SUITE_REPORT_JSON)
    return ref


def adapt_var_suite_domain(
    *,
    suite_report_dir: Path,
    companion_run_dir: Path,
    var_suite_source_ref: Mapping[str, Any],
    backtest_source_ref: Mapping[str, Any],
    evaluation_slice_id: str | None = None,
) -> AdapterResult:
    suite_report_dir = suite_report_dir.resolve()
    if not suite_report_dir.is_dir() or suite_report_dir.is_symlink():
        raise ComparisonMetricInputError(f"suite_report_dir invalid: {suite_report_dir}")
    suite_ref = _validate_var_suite_lineage_ref(
        suite_report_dir=suite_report_dir,
        source_ref=var_suite_source_ref,
    )
    backtest_result = adapt_backtest_domain(
        run_dir=companion_run_dir, source_ref=backtest_source_ref
    )
    if (
        evaluation_slice_id is not None
        and backtest_result.evaluation_slice_id != evaluation_slice_id
    ):
        raise ComparisonMetricInputError(
            "VAR_SUITE evaluation_slice_id mismatch with companion backtest"
        )
    suite_report = load_json_object(
        suite_report_dir / SUITE_REPORT_JSON,
        label=SUITE_REPORT_JSON,
    )
    forbidden_metric_keys = {
        "sharpe",
        "max_drawdown",
        "profit_factor",
        "total_return",
        "volatility",
        "trade_count",
    }
    if forbidden_metric_keys & set(suite_report):
        raise ComparisonMetricInputError(
            "suite_report.json must not supply trading performance metrics"
        )
    var_suite_companion = {
        "companion_required": True,
        "wired_backtest_lineage_ref": backtest_result.source_ref.to_mapping(),
        "suite_report_lineage_ref": suite_ref.to_mapping(),
    }
    return AdapterResult(
        source_domain="VAR_SUITE",
        source_ref=suite_ref,
        source_digest=backtest_result.source_digest,
        evaluation_slice_id=backtest_result.evaluation_slice_id,
        comparability_metadata={
            **backtest_result.comparability_metadata,
            "source_domain": "VAR_SUITE",
        },
        metrics=backtest_result.metrics,
        source_bindings=backtest_result.source_bindings,
        var_suite_companion=var_suite_companion,
    )
