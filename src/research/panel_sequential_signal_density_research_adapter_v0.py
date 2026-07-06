"""Panel sequential signal-density research adapter v0.

Materializes per-panel-member evaluation datasets from extended_chronological_v1
staging and computes sparse-signal density metrics via deterministic instrument_id
ascending rotation. Reuses canonical STEP31F / MV2 research wiring owners.

Research-only. No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    PanelMemberBindingV0,
    load_panel_member_binding_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    load_funding_panel_from_staging,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
    NATIVE_INSTRUMENT_ID,
    SOURCE_VENUE,
    STEP31F_CONFIG_PATHS,
    load_step31f_evaluation_config_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    PANEL_STAGING_ROOT,
)
from src.research.step31f_promotion_metric_materialization_path_execution_owner_v0 import (
    bind_step31f_promotion_metric_materialization_dataset_manifest_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    CONSERVATIVE_HALF_SPREAD_BPS,
    NarrowDatasetMaterializationV0,
    build_runtime_step31f_config_v0,
)

PACKAGE_MARKER = "PANEL_SEQUENTIAL_SIGNAL_DENSITY_RESEARCH_ADAPTER_V0=true"
ADAPTER_KIND = "PANEL_SEQUENTIAL_SIGNAL_DENSITY_RESEARCH_ADAPTER_v0"
ROTATION_POLICY = "deterministic_instrument_id_asc"

REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_PANEL_MEMBER_MISSING = "PANEL_MEMBER_MISSING"


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SparseSignalDensityMetricsV0:
    panel_member_count: int
    instruments_scanned: int
    instruments_with_nonzero_trades: int
    instruments_with_zero_trades: int
    max_trade_count: int
    rotation_policy: str
    evaluation_instrument_id: str
    evaluation_native_instrument_id: str
    member_trade_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_kind": ADAPTER_KIND,
            "evaluation_instrument_id": self.evaluation_instrument_id,
            "evaluation_native_instrument_id": self.evaluation_native_instrument_id,
            "instruments_scanned": self.instruments_scanned,
            "instruments_with_nonzero_trades": self.instruments_with_nonzero_trades,
            "instruments_with_zero_trades": self.instruments_with_zero_trades,
            "max_trade_count": self.max_trade_count,
            "member_trade_counts": self.member_trade_counts,
            "panel_member_count": self.panel_member_count,
            "rotation_policy": self.rotation_policy,
            "sparse_signal_research": True,
        }


def resolve_panel_staging_root(staging_root: Path | None = None) -> Path:
    return staging_root or Path(PANEL_STAGING_ROOT)


def load_sorted_panel_binding(staging_root: Path | None = None) -> PanelMemberBindingV0:
    root = resolve_panel_staging_root(staging_root)
    if not root.is_dir():
        raise FileNotFoundError(REASON_STAGING_MISSING)
    binding = load_panel_member_binding_v0(root)
    sorted_ids = tuple(sorted(binding.instrument_ids))
    native_by_id = dict(zip(binding.instrument_ids, binding.native_instrument_ids))
    return PanelMemberBindingV0(
        staging_root=binding.staging_root,
        panel_member_count=binding.panel_member_count,
        instrument_ids=sorted_ids,
        native_instrument_ids=tuple(native_by_id[item] for item in sorted_ids),
        panel_calendar_start_utc=binding.panel_calendar_start_utc,
        panel_calendar_end_utc=binding.panel_calendar_end_utc,
        panel_dataset_manifest_path=binding.panel_dataset_manifest_path,
    )


def materialize_panel_member_evaluation_dataset_v0(
    *,
    staging_root: Path,
    instrument_id: str,
    output_root: Path,
) -> NarrowDatasetMaterializationV0:
    funding_series, _panel_ref, _manifest_path = load_funding_panel_from_staging(staging_root)
    selected = None
    for series in funding_series:
        if series.instrument_id == instrument_id:
            selected = series
            break
    if selected is None:
        raise ValueError(f"{REASON_PANEL_MEMBER_MISSING}:{instrument_id}")

    rows: list[dict[str, Any]] = []
    for bar in selected.bars:
        close = float(bar.close)
        rows.append(
            {
                "timestamp": pd.Timestamp(bar.timestamp_utc, tz="UTC"),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": close,
                "volume": float(bar.volume),
                "mark_price": close,
                "index_price": close,
                "funding_rate": float(bar.funding_rate),
                "is_final": True,
            }
        )
    frame = pd.DataFrame(rows).set_index("timestamp").sort_index()
    if frame.empty:
        raise ValueError(f"empty_panel_member_dataset:{instrument_id}")

    field_bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    dataset_digest = ds.compute_versioned_dataset_digest(frame, field_bindings=field_bindings)
    training, validation, oos = ds.compute_split_periods_from_bars(frame)

    output_root.mkdir(parents=True, exist_ok=True)
    bars_path = output_root / "bars.parquet"
    frame.to_parquet(bars_path)

    provenance = ds.DatasetProvenanceV1(
        source_type="panel_sequential_signal_density_adapter_v0",
        venue_id=SOURCE_VENUE,
        ingestion_timestamp=_utc_now_z(),
        generation_method="panel_sequential_signal_density_research_adapter_v0",
        provenance_ref=str(staging_root / "panel" / "panel_funding_dataset_manifest.json"),
    )
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id=f"{CANONICAL_INSTRUMENT_ID}_{ds.DEFAULT_DATASET_VERSION}",
        dataset_version=ds.DEFAULT_DATASET_VERSION,
        dataset_schema_version=ds.DATASET_SCHEMA_VERSION,
        dataset_digest=dataset_digest,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        contract_type="perpetual",
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id=SOURCE_VENUE,
        start_time=str(frame.index[0]),
        end_time=str(frame.index[-1]),
        row_count=len(frame),
        field_bindings=field_bindings,
        training_period=training,
        validation_period=validation,
        out_of_sample_period=oos,
        split_policy_version=ds.SPLIT_POLICY_VERSION,
        timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
        timezone=ds.TIMEZONE,
        ordering_status=ds.ORDERING_STATUS_SORTED,
        duplicate_policy=ds.DUPLICATE_POLICY,
        missing_data_policy=ds.MISSING_DATA_POLICY,
    )
    profile_binding = ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=CONSERVATIVE_HALF_SPREAD_BPS,
        ),
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )
    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=frame,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=profile_binding,
    )
    manifest_body = bind_step31f_promotion_metric_materialization_dataset_manifest_v0(
        {
            "acquisition_timestamps": {
                "ingestion_timestamp_utc": _utc_now_z(),
                "staging_timestamp_utc": _utc_now_z(),
            },
            "adapter_kind": ADAPTER_KIND,
            "bar_granularity": "1h",
            "bitcoin_direction_allowed": False,
            "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
            "contract_type": "perpetual",
            "data_period": {"end_utc": str(frame.index[-1]), "start_utc": str(frame.index[0])},
            "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
            "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
            "dataset_version": ds.DEFAULT_DATASET_VERSION,
            "execution_cost_binding": {
                "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                "spread_model_version": "research_conservative_bps_v1",
            },
            "fee_model_version": "backtest_fee_taker_symmetric_v0",
            "funding_model_version": "backtest_funding_perpetual_interval_v1",
            "futures_only": True,
            "instrument_id": CANONICAL_INSTRUMENT_ID,
            "integrity_results": {
                "dataset_admissible": admissibility.is_admissible(),
                "integrity_pass": admissibility.is_admissible(),
                "leakage_check_status": admissibility.leakage_check_status,
            },
            "native_instrument_id": NATIVE_INSTRUMENT_ID,
            "normalized_dataset_digest": dataset_digest,
            "out_of_sample_period": oos,
            "panel_source_binding": {
                "adapter_kind": ADAPTER_KIND,
                "panel_member_instrument_id": instrument_id,
                "rotation_policy": ROTATION_POLICY,
                "sequential_rotation": True,
                "staging_root": str(staging_root),
            },
            "profile_binding": profile_binding.to_dict(),
            "provenance": provenance.to_dict(),
            "row_count": len(frame),
            "slippage_model_version": "backtest_slippage_symmetric_v0",
            "source_venue": SOURCE_VENUE,
            "training_period": training,
            "validation_period": validation,
        }
    )
    manifest_body["manifest_digest"] = _stable_digest(
        {key: value for key, value in manifest_body.items() if key != "manifest_digest"}
    )
    manifest_path = output_root / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_body, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return NarrowDatasetMaterializationV0(
        dataset_root=output_root,
        bars_path=bars_path,
        manifest_path=manifest_path,
        dataset_digest=dataset_digest,
        manifest_digest=str(manifest_body["manifest_digest"]),
        row_count=len(frame),
        bar_granularity="1h",
        training_period=training,
        validation_period=validation,
        out_of_sample_period=oos,
    )


def _count_trades_for_member_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    staging_root: Path,
    instrument_id: str,
    scratch_root: Path,
) -> int:
    member_root = scratch_root / instrument_id.replace(":", "_")
    narrow = materialize_panel_member_evaluation_dataset_v0(
        staging_root=staging_root,
        instrument_id=instrument_id,
        output_root=member_root,
    )
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    bars = pd.read_parquet(narrow.bars_path)
    wiring = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=strategy_id,
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
    )
    return int(wiring.backtest_result.stats.get("total_trades", 0))


def compute_sparse_signal_density_metrics_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    staging_root: Path | None = None,
    scratch_root: Path,
) -> SparseSignalDensityMetricsV0:
    root = resolve_panel_staging_root(staging_root)
    binding = load_sorted_panel_binding(root)
    member_trade_counts: dict[str, int] = {}
    for instrument_id in binding.instrument_ids:
        member_trade_counts[instrument_id] = _count_trades_for_member_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            staging_root=root,
            instrument_id=instrument_id,
            scratch_root=scratch_root,
        )
    nonzero = [item for item in member_trade_counts.values() if item > 0]
    max_trade_count = max(member_trade_counts.values()) if member_trade_counts else 0
    evaluation_instrument_id = binding.instrument_ids[0]
    if max_trade_count > 0:
        evaluation_instrument_id = max(member_trade_counts, key=member_trade_counts.get)
    native_index = binding.instrument_ids.index(evaluation_instrument_id)
    return SparseSignalDensityMetricsV0(
        panel_member_count=binding.panel_member_count,
        instruments_scanned=len(member_trade_counts),
        instruments_with_nonzero_trades=len(nonzero),
        instruments_with_zero_trades=len(member_trade_counts) - len(nonzero),
        max_trade_count=max_trade_count,
        rotation_policy=ROTATION_POLICY,
        evaluation_instrument_id=evaluation_instrument_id,
        evaluation_native_instrument_id=binding.native_instrument_ids[native_index],
        member_trade_counts=member_trade_counts,
    )


def build_sparse_signal_runtime_step31f_config_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    staging_root: Path,
    instrument_id: str,
    output_path: Path,
) -> Path:
    member_root = output_path.parent / "datasets" / instrument_id.replace(":", "_")
    narrow = materialize_panel_member_evaluation_dataset_v0(
        staging_root=staging_root,
        instrument_id=instrument_id,
        output_root=member_root,
    )
    return build_runtime_step31f_config_v0(
        repo_root=repo_root,
        strategy_id=strategy_id,
        narrow_dataset=narrow,
        output_path=output_path,
    )


__all__ = [
    "ADAPTER_KIND",
    "ROTATION_POLICY",
    "SparseSignalDensityMetricsV0",
    "build_sparse_signal_runtime_step31f_config_v0",
    "compute_sparse_signal_density_metrics_v0",
    "load_sorted_panel_binding",
    "materialize_panel_member_evaluation_dataset_v0",
    "resolve_panel_staging_root",
]
