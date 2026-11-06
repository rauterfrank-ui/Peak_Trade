"""BACKTEST domain adapter for comparison_metric_input.v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.experiments.equity_loader import load_equity_curves_from_run_dir
from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    BACKTEST_OWNER_DOMAIN,
    RUN_SUMMARY_REL_PATH,
    compute_backtest_lineage_ref_digest,
)
from src.meta.learning_loop.comparison_metric_input_v1.comparability import (
    comparability_from_backtest_config_snapshot,
)
from src.meta.learning_loop.comparison_metric_input_v1.constants import ANNUALIZATION_PROFILE_V1
from src.meta.learning_loop.comparison_metric_input_v1.metrics import compute_all_metrics
from src.meta.learning_loop.comparison_metric_input_v1.models import (
    AdapterResult,
    ComparisonMetricInputError,
    SourceBindingRecord,
    SourceRef,
)
from src.meta.learning_loop.comparison_metric_input_v1.source_binding import (
    build_binding_records,
    compute_equity_series_digest,
    compute_source_digest,
    compute_trade_ledger_digest,
    load_json_object,
    load_trades_from_parquet,
    sha256_file,
    verify_source_ref,
)

CONFIG_SNAPSHOT_REL = "config_snapshot.json"
TRADES_REL = "trades.parquet"


def _resolve_run_dir(run_dir: Path) -> Path:
    if not run_dir.exists() or not run_dir.is_dir() or run_dir.is_symlink():
        raise ComparisonMetricInputError(f"run_dir invalid: {run_dir}")
    return run_dir.resolve()


def _equity_relative_path(run_dir: Path) -> str:
    equity_csv = run_dir / "equity.csv"
    if equity_csv.is_file():
        return "equity.csv"
    matches = sorted(run_dir.glob("*equity.csv"))
    if not matches:
        raise ComparisonMetricInputError("equity artifact not found in run_dir")
    if len(matches) > 1:
        raise ComparisonMetricInputError("ambiguous equity artifacts in run_dir")
    return matches[0].name


def _validate_backtest_lineage_ref(
    *,
    run_dir: Path,
    source_ref: Mapping[str, Any],
) -> SourceRef:
    ref = verify_source_ref(source_ref, expected_domain="BACKTEST")
    if ref.owner_domain != BACKTEST_OWNER_DOMAIN:
        raise ComparisonMetricInputError("BACKTEST source_ref owner_domain mismatch")
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    if not summary_path.is_file():
        raise ComparisonMetricInputError(f"{RUN_SUMMARY_REL_PATH} not found in run_dir")
    summary = RunSummary.read_json(summary_path)
    errors = summary.validate_contract(strict=True)
    if errors:
        raise ComparisonMetricInputError(f"RunSummary validation failed: {'; '.join(errors)}")
    if summary.status != "FINISHED":
        raise ComparisonMetricInputError("backtest run must be FINISHED")
    expected_digest = compute_backtest_lineage_ref_digest(summary)
    if ref.digest != expected_digest:
        raise ComparisonMetricInputError("BACKTEST source_ref digest mismatch with run_summary")
    if ref.ref_id != str(summary.run_id):
        raise ComparisonMetricInputError(
            "BACKTEST source_ref ref_id mismatch with run_summary.run_id"
        )
    return ref


def adapt_backtest_domain(
    *,
    run_dir: Path,
    source_ref: Mapping[str, Any],
) -> AdapterResult:
    resolved_run_dir = _resolve_run_dir(run_dir)
    ref = _validate_backtest_lineage_ref(run_dir=resolved_run_dir, source_ref=source_ref)
    config_path = resolved_run_dir / CONFIG_SNAPSHOT_REL
    config_snapshot = load_json_object(config_path, label=CONFIG_SNAPSHOT_REL)
    summary = RunSummary.read_json(resolved_run_dir / RUN_SUMMARY_REL_PATH)
    comparability_metadata, evaluation_slice_id = comparability_from_backtest_config_snapshot(
        config_snapshot=config_snapshot,
        run_summary_params=summary.params,
        source_domain="BACKTEST",
        source_ref_id=ref.ref_id,
        evaluation_start=summary.started_at_utc,
        evaluation_end=summary.finished_at_utc,
    )
    periods_per_year = ANNUALIZATION_PROFILE_V1.get(str(comparability_metadata["timeframe"]))
    if periods_per_year is None:
        raise ComparisonMetricInputError(
            f"unknown timeframe: {comparability_metadata['timeframe']}"
        )
    equity = load_equity_curves_from_run_dir(resolved_run_dir, max_curves=1)[0]
    trades_path = resolved_run_dir / TRADES_REL
    trades = load_trades_from_parquet(trades_path)
    source_digest = compute_source_digest(
        equity_series_digest=compute_equity_series_digest(equity),
        trade_ledger_digest=compute_trade_ledger_digest(trades),
    )
    metrics = compute_all_metrics(
        equity=equity,
        trades=trades,
        periods_per_year=periods_per_year,
    )
    equity_rel = _equity_relative_path(resolved_run_dir)
    bindings = build_binding_records(
        SourceBindingRecord(CONFIG_SNAPSHOT_REL, sha256_file(config_path)),
        SourceBindingRecord(
            RUN_SUMMARY_REL_PATH, sha256_file(resolved_run_dir / RUN_SUMMARY_REL_PATH)
        ),
        SourceBindingRecord(TRADES_REL, sha256_file(trades_path)),
        SourceBindingRecord(equity_rel, sha256_file(resolved_run_dir / equity_rel)),
    )
    return AdapterResult(
        source_domain="BACKTEST",
        source_ref=ref,
        source_digest=source_digest,
        evaluation_slice_id=evaluation_slice_id,
        comparability_metadata=comparability_metadata,
        metrics=metrics,
        source_bindings=bindings,
        var_suite_companion=None,
    )
