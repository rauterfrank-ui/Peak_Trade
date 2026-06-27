"""EXPERIMENT domain adapter for comparison_metric_input.v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.experiments.equity_loader import load_equity_curves_from_run_dir
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT,
    validate_experiment_identity_manifest_v1,
)
from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import EXPERIMENT_OWNER_DOMAIN
from src.meta.learning_loop.comparison_metric_input_v1.adapters.backtest import (
    CONFIG_SNAPSHOT_REL,
    TRADES_REL,
    _equity_relative_path,
)
from src.meta.learning_loop.comparison_metric_input_v1.comparability import (
    comparability_from_experiment_identity,
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

RUN_SUMMARY_REL_PATH = "run_summary.json"


def _validate_experiment_lineage_ref(
    *,
    manifest_dir: Path,
    source_ref: Mapping[str, Any],
) -> tuple[SourceRef, dict[str, Any]]:
    ref = verify_source_ref(source_ref, expected_domain="EXPERIMENT")
    if ref.owner_domain != EXPERIMENT_OWNER_DOMAIN:
        raise ComparisonMetricInputError("EXPERIMENT source_ref owner_domain mismatch")
    manifest_path = manifest_dir / EXPERIMENT_IDENTITY_ARTIFACT
    manifest = load_json_object(manifest_path, label=EXPERIMENT_IDENTITY_ARTIFACT)
    validate_experiment_identity_manifest_v1(manifest)
    integrity = manifest.get("integrity")
    if not isinstance(integrity, dict):
        raise ComparisonMetricInputError("experiment identity manifest missing integrity")
    expected_digest = integrity.get("content_sha256")
    if ref.digest != expected_digest:
        raise ComparisonMetricInputError(
            "EXPERIMENT source_ref digest mismatch with identity manifest"
        )
    experiment_identity_id = manifest.get("experiment_identity_id")
    if ref.ref_id != experiment_identity_id:
        raise ComparisonMetricInputError(
            "EXPERIMENT source_ref ref_id mismatch with experiment_identity_id"
        )
    return ref, manifest


def _validate_completed_run_dir(run_dir: Path) -> RunSummary:
    if not run_dir.exists() or not run_dir.is_dir() or run_dir.is_symlink():
        raise ComparisonMetricInputError(f"completed_run_dir invalid: {run_dir}")
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    if not summary_path.is_file():
        raise ComparisonMetricInputError("completed run_dir missing run_summary.json")
    summary = RunSummary.read_json(summary_path)
    errors = summary.validate_contract(strict=True)
    if errors:
        raise ComparisonMetricInputError(f"completed run summary invalid: {'; '.join(errors)}")
    if summary.status != "FINISHED":
        raise ComparisonMetricInputError("experiment run must be FINISHED")
    return summary


def adapt_experiment_domain(
    *,
    manifest_dir: Path,
    completed_run_dir: Path,
    source_ref: Mapping[str, Any],
) -> AdapterResult:
    manifest_dir = manifest_dir.resolve()
    completed_run_dir = completed_run_dir.resolve()
    ref, manifest = _validate_experiment_lineage_ref(
        manifest_dir=manifest_dir, source_ref=source_ref
    )
    identity_config = manifest.get("identity_config")
    if not isinstance(identity_config, dict):
        raise ComparisonMetricInputError("experiment identity manifest missing identity_config")
    _validate_completed_run_dir(completed_run_dir)
    comparability_metadata, evaluation_slice_id = comparability_from_experiment_identity(
        identity_config=identity_config,
        source_ref_id=ref.ref_id,
    )
    periods_per_year = ANNUALIZATION_PROFILE_V1.get(str(comparability_metadata["timeframe"]))
    if periods_per_year is None:
        raise ComparisonMetricInputError(
            f"unknown timeframe: {comparability_metadata['timeframe']}"
        )
    equity = load_equity_curves_from_run_dir(completed_run_dir, max_curves=1)[0]
    trades_path = completed_run_dir / TRADES_REL
    trades = load_trades_from_parquet(trades_path)
    config_path = completed_run_dir / CONFIG_SNAPSHOT_REL
    if not config_path.is_file():
        raise ComparisonMetricInputError("completed run_dir missing config_snapshot.json")
    source_digest = compute_source_digest(
        equity_series_digest=compute_equity_series_digest(equity),
        trade_ledger_digest=compute_trade_ledger_digest(trades),
    )
    metrics = compute_all_metrics(
        equity=equity,
        trades=trades,
        periods_per_year=periods_per_year,
    )
    equity_rel = _equity_relative_path(completed_run_dir)
    bindings = build_binding_records(
        SourceBindingRecord(
            f"manifest/{EXPERIMENT_IDENTITY_ARTIFACT}",
            sha256_file(manifest_dir / EXPERIMENT_IDENTITY_ARTIFACT),
        ),
        SourceBindingRecord(CONFIG_SNAPSHOT_REL, sha256_file(config_path)),
        SourceBindingRecord(TRADES_REL, sha256_file(trades_path)),
        SourceBindingRecord(equity_rel, sha256_file(completed_run_dir / equity_rel)),
    )
    return AdapterResult(
        source_domain="EXPERIMENT",
        source_ref=ref,
        source_digest=source_digest,
        evaluation_slice_id=evaluation_slice_id,
        comparability_metadata=comparability_metadata,
        metrics=metrics,
        source_bindings=bindings,
        var_suite_companion=None,
    )
