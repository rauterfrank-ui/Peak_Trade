"""Offline final research fleet signal matrix productive input join materializer v0.

Deterministic, offline-only join of ratified final-research-fleet strategy signals
via canonical strategy_signal_binding_v1 owners. Reuses
``signal_matrix_productive_contract_v0`` as the sole join contract owner.
No orthogonality diagnostics, economic evaluation, runtime, order, or authority effect.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    execute_configured_strategy_signal_series_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    load_step31f_evaluation_config_v0,
)
from src.research.linear_evidence.signal_matrix_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    DECISION_TIME_KEY,
    EXPECTED_FLEET_SIGNAL_ORDER,
    FEATURE_TIME_KEY,
    INSTRUMENT_ID_KEY,
    RATIFIED_BINDING_SOURCE,
    RUNTIME_EFFECT,
    ProductiveSignalJoinRejectionReason,
    SignalMatrixBindingV0,
    SignalMatrixProductiveProvenanceV0,
    compute_instrument_universe_digest_v0,
    compute_signal_matrix_digest_v0,
    compute_warmup_rows_v0,
    stable_digest_v0,
    validate_requested_signal_set_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    REASON_MISSING_PANEL_BARS,
    REASON_MISSING_PANEL_MANIFEST,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
)
from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    quarantine_research_fleet_join_volatility_v1,
    require_admitted_legacy_volatility_float_v1,
)

PACKAGE_MARKER = (
    "OFFLINE_FINAL_RESEARCH_FLEET_SIGNAL_MATRIX_PRODUCTIVE_INPUT_JOIN_MATERIALIZER_V0=true"
)
SCHEMA_VERSION = "offline_final_research_fleet_signal_matrix_productive_input_join_materializer.v0"
CANONICAL_CONTRACT_OWNER = "src/research/linear_evidence/signal_matrix_productive_contract_v0.py"
CANONICAL_SIGNAL_BINDING_OWNER = "src/backtest/strategy_signal_binding_v1.py"
DEFAULT_STAGING_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
IMPLEMENTATION_DIGEST = stable_digest_v0(
    {
        "contract": SCHEMA_VERSION,
        "join_owner": CANONICAL_CONTRACT_OWNER,
        "signal_binding_owner": CANONICAL_SIGNAL_BINDING_OWNER,
        "signal_column_order": list(EXPECTED_FLEET_SIGNAL_ORDER),
    }
)


class MaterializationStatus(str, Enum):
    PASS = "PASS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"


@dataclass(frozen=True)
class SignalSeriesRowV0:
    instrument_id: str
    decision_time: str
    feature_time: str
    signal_name: str
    signal_value: float


@dataclass(frozen=True)
class ProductiveSignalJoinValidationResultV0:
    admissible_rows: tuple[dict[str, Any], ...]
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: dict[str, int]
    per_signal_null_count: dict[str, int]
    per_signal_warmup_exclusion_count: dict[str, int]
    instrument_universe: tuple[str, ...]
    instrument_universe_digest: str
    time_range: dict[str, str]
    binding: SignalMatrixBindingV0
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class MaterializationResultV0:
    status: MaterializationStatus
    rows: tuple[dict[str, Any], ...]
    join_result: ProductiveSignalJoinValidationResultV0
    provenance: SignalMatrixProductiveProvenanceV0
    binding: SignalMatrixBindingV0
    materialization_digest: str
    output_digest: str
    signal_matrix_digest: str
    source_binding_digest: str
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_panel_series_for_signal_matrix_v0(
    staging_root: Path,
) -> tuple[tuple[InstrumentPanelSeriesV1, ...], str]:
    """Narrow adapter around panel staging load (Python 3.9-safe zip semantics)."""
    panel_dir = staging_root / "panel"
    manifest_path = panel_dir / "panel_dataset_manifest.json"
    bars_path = panel_dir / "normalized_panel_bars.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(REASON_MISSING_PANEL_MANIFEST)
    if not bars_path.is_file():
        raise FileNotFoundError(REASON_MISSING_PANEL_BARS)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = json.loads(bars_path.read_text(encoding="utf-8"))
    grouped: dict[str, list[PanelBarV1]] = {}
    for row in rows:
        bar = PanelBarV1(
            instrument_id=str(row["instrument_id"]),
            timestamp_utc=str(row["timestamp_utc"]),
            open=str(row["open"]),
            high=str(row["high"]),
            low=str(row["low"]),
            close=str(row["close"]),
            volume=str(row["volume"]),
            is_final=bool(row["is_final"]),
        )
        grouped.setdefault(bar.instrument_id, []).append(bar)
    instrument_ids = list(manifest["instrument_ids"])
    native_ids = list(manifest["native_instrument_ids"])
    if len(instrument_ids) != len(native_ids):
        raise ValueError("PANEL_MANIFEST_INSTRUMENT_NATIVE_MISMATCH")
    native_by_id = dict(zip(instrument_ids, native_ids))
    series_list: list[InstrumentPanelSeriesV1] = []
    for instrument_id in sorted(grouped):
        bars = tuple(sorted(grouped[instrument_id], key=lambda item: item.timestamp_utc))
        interim = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=native_by_id.get(instrument_id, instrument_id),
            bars=bars,
            series_digest="0" * 64,
        )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=interim.instrument_id,
                native_instrument_id=interim.native_instrument_id,
                bars=interim.bars,
                series_digest=compute_series_digest(interim),
            )
        )
    panel_ref = (
        f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{manifest['panel_id']}:"
        f"sha256:{manifest['manifest_digest']}"
    )
    return tuple(series_list), panel_ref


def load_ratified_binding_completion_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / RATIFIED_BINDING_SOURCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("BINDING_COMPLETION_NOT_OBJECT")
    return payload


def _candidate_by_strategy_id(
    binding_completion: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    candidates = binding_completion.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value)
    mapping: dict[str, Mapping[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        strategy_id = str(candidate.get("strategy_id", ""))
        if not strategy_id:
            continue
        if strategy_id in mapping:
            raise ValueError(ProductiveSignalJoinRejectionReason.DUPLICATE_TIMESTAMP.value)
        mapping[strategy_id] = candidate
    return mapping


def panel_bars_to_strategy_dataframe_v0(
    bars: Sequence[PanelBarV1],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for bar in bars:
        if not bar.is_final:
            continue
        close = float(bar.close)
        records.append(
            {
                "timestamp": pd.Timestamp(bar.timestamp_utc, tz="UTC"),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": close,
                "mark_price": close,
                "index_price": close,
                "best_bid": close - 0.05,
                "best_ask": close + 0.05,
                "spread": 0.1,
                "volume": float(bar.volume),
                "open_interest": 10000.0,
                "funding_rate": 0.0001,
                "volatility_estimate": require_admitted_legacy_volatility_float_v1(
                    quarantine_research_fleet_join_volatility_v1()
                ),
                "is_final": True,
                "bar_interval": "1h",
            }
        )
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records).set_index("timestamp").sort_index()
    if frame.index.has_duplicates:
        raise ValueError(ProductiveSignalJoinRejectionReason.DUPLICATE_TIMESTAMP.value)
    return frame


def materialize_strategy_signal_rows_v0(
    *,
    instrument_id: str,
    panel_series: InstrumentPanelSeriesV1,
    strategy_id: str,
    candidate_binding: Mapping[str, Any],
    repo_root: Path,
    coverage_start_utc: str,
    coverage_end_utc: str,
) -> tuple[tuple[SignalSeriesRowV0, ...], dict[str, int]]:
    dropped: dict[str, int] = {}
    warmup_excluded = 0
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    parameter_binding = dict(candidate_binding.get("parameter_binding", {}))
    warmup_rows = compute_warmup_rows_v0(strategy_id, parameter_binding)
    bars_frame = panel_bars_to_strategy_dataframe_v0(panel_series.bars)
    if bars_frame.empty:
        dropped[ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value] = (
            dropped.get(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value, 0) + 1
        )
        return (), dropped

    try:
        binding_result = execute_configured_strategy_signal_series_v1(
            bars_frame,
            strategy_id=strategy_id,
            cfg=cfg,
        )
    except StrategySignalBindingError as exc:
        dropped[ProductiveSignalJoinRejectionReason.STRATEGY_EXECUTION_FAILED.value] = (
            dropped.get(ProductiveSignalJoinRejectionReason.STRATEGY_EXECUTION_FAILED.value, 0) + 1
        )
        raise ValueError(
            f"{ProductiveSignalJoinRejectionReason.STRATEGY_EXECUTION_FAILED.value}:{exc}"
        ) from exc

    signals = binding_result.signals.astype(int)
    coverage_start = _parse_utc(coverage_start_utc)
    coverage_end = _parse_utc(coverage_end_utc)
    rows: list[SignalSeriesRowV0] = []
    timestamps = [_format_utc(ts.to_pydatetime()) for ts in bars_frame.index]
    for index in range(1, len(timestamps)):
        if index < warmup_rows:
            warmup_excluded += 1
            continue
        decision_time = timestamps[index]
        feature_time = timestamps[index - 1]
        decision_dt = _parse_utc(decision_time)
        if decision_dt < coverage_start or decision_dt > coverage_end:
            dropped[ProductiveSignalJoinRejectionReason.OUTSIDE_COVERAGE_PERIOD.value] = (
                dropped.get(ProductiveSignalJoinRejectionReason.OUTSIDE_COVERAGE_PERIOD.value, 0)
                + 1
            )
            continue
        if feature_time >= decision_time:
            dropped[ProductiveSignalJoinRejectionReason.LOOKAHEAD_DETECTED.value] = (
                dropped.get(ProductiveSignalJoinRejectionReason.LOOKAHEAD_DETECTED.value, 0) + 1
            )
            continue
        signal_value = float(int(signals.iloc[index - 1]))
        rows.append(
            SignalSeriesRowV0(
                instrument_id=instrument_id,
                decision_time=decision_time,
                feature_time=feature_time,
                signal_name=strategy_id,
                signal_value=signal_value,
            )
        )
    dropped[ProductiveSignalJoinRejectionReason.WARMUP_EXCLUDED.value] = warmup_excluded
    return tuple(rows), dropped


def join_productive_signal_matrix_v0(
    signal_rows_by_name: Mapping[str, Sequence[SignalSeriesRowV0]],
) -> tuple[tuple[dict[str, Any], ...], dict[str, int], dict[str, int]]:
    dropped: dict[str, int] = {}
    null_counts = {name: 0 for name in EXPECTED_FLEET_SIGNAL_ORDER}
    warmup_counts = {name: 0 for name in EXPECTED_FLEET_SIGNAL_ORDER}

    keyed: dict[tuple[str, str], dict[str, Any]] = {}
    for signal_name in EXPECTED_FLEET_SIGNAL_ORDER:
        rows = signal_rows_by_name.get(signal_name, ())
        for row in rows:
            key = (row.instrument_id, row.decision_time)
            payload = keyed.setdefault(
                key,
                {
                    INSTRUMENT_ID_KEY: row.instrument_id,
                    DECISION_TIME_KEY: row.decision_time,
                    FEATURE_TIME_KEY: row.feature_time,
                },
            )
            if payload.get(FEATURE_TIME_KEY) != row.feature_time:
                dropped[ProductiveSignalJoinRejectionReason.LOOKAHEAD_DETECTED.value] = (
                    dropped.get(ProductiveSignalJoinRejectionReason.LOOKAHEAD_DETECTED.value, 0) + 1
                )
                continue
            payload[signal_name] = row.signal_value

    joined: list[dict[str, Any]] = []
    for key in sorted(keyed.keys()):
        payload = keyed[key]
        missing = [name for name in EXPECTED_FLEET_SIGNAL_ORDER if name not in payload]
        if missing:
            dropped[ProductiveSignalJoinRejectionReason.INNER_JOIN_MISS.value] = (
                dropped.get(ProductiveSignalJoinRejectionReason.INNER_JOIN_MISS.value, 0) + 1
            )
            for name in missing:
                null_counts[name] += 1
            continue
        invalid = False
        for name in EXPECTED_FLEET_SIGNAL_ORDER:
            value = payload.get(name)
            if value is None:
                null_counts[name] += 1
                dropped[ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_VALUE.value] = (
                    dropped.get(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_VALUE.value, 0)
                    + 1
                )
                invalid = True
                break
            if int(value) not in {-1, 0, 1}:
                dropped[ProductiveSignalJoinRejectionReason.INVALID_SIGNAL_ENCODING.value] = (
                    dropped.get(
                        ProductiveSignalJoinRejectionReason.INVALID_SIGNAL_ENCODING.value, 0
                    )
                    + 1
                )
                invalid = True
                break
        if not invalid:
            joined.append(payload)

    return tuple(joined), dropped, warmup_counts


def build_signal_matrix_binding_v0(
    *,
    binding_completion: Mapping[str, Any],
    binding_digest: str,
) -> SignalMatrixBindingV0:
    shared = binding_completion.get("shared_bindings", {})
    dataset_binding = shared.get("dataset_binding", {}) if isinstance(shared, Mapping) else {}
    period_binding = shared.get("period_binding", {}) if isinstance(shared, Mapping) else {}
    instrument_binding = shared.get("instrument_binding", {}) if isinstance(shared, Mapping) else {}
    candidates = _candidate_by_strategy_id(binding_completion)
    strategy_bindings = tuple(
        {
            "strategy_id": strategy_id,
            "strategy_version": str(candidates[strategy_id].get("strategy_version", "v1")),
            "parameter_binding": dict(candidates[strategy_id].get("parameter_binding", {})),
            "config_digest": str(candidates[strategy_id].get("config_digest", "")),
            "strategy_params_digest": str(
                candidates[strategy_id].get("strategy_params_digest", "")
            ),
            "implementation_digest": str(candidates[strategy_id].get("implementation_digest", "")),
            "source_config_ref": str(candidates[strategy_id].get("source_config_ref", "")),
        }
        for strategy_id in EXPECTED_FLEET_SIGNAL_ORDER
        if strategy_id in candidates
    )
    instrument_ids = tuple(
        sorted(str(item) for item in instrument_binding.get("eligible_instrument_ids", ()))
    )
    return SignalMatrixBindingV0(
        binding_digest=binding_digest,
        strategy_bindings=strategy_bindings,
        instrument_ids=instrument_ids,
        coverage_period_start_utc=str(period_binding.get("coverage_period_start_utc", "")),
        coverage_period_end_utc=str(period_binding.get("coverage_period_end_utc", "")),
        dataset_id=str(dataset_binding.get("dataset_id", "")),
        dataset_digest=str(dataset_binding.get("data_digest", "")),
        panel_dataset_digest=str(dataset_binding.get("panel_dataset_digest", "")),
    )


def materialize_offline_final_research_fleet_signal_matrix_v0(
    *,
    repo_root: Path,
    staging_root: Path,
    binding_completion: Mapping[str, Any] | None = None,
    requested_signals: Sequence[str] | None = None,
) -> MaterializationResultV0:
    validate_requested_signal_set_v0(
        requested_signals if requested_signals is not None else EXPECTED_FLEET_SIGNAL_ORDER
    )
    binding_payload = binding_completion or load_ratified_binding_completion_v0(repo_root)
    binding_digest = str(binding_payload.get("completion_digest", ""))
    binding = build_signal_matrix_binding_v0(
        binding_completion=binding_payload,
        binding_digest=binding_digest,
    )
    candidates = _candidate_by_strategy_id(binding_payload)
    for strategy_id in EXPECTED_FLEET_SIGNAL_ORDER:
        if strategy_id not in candidates:
            raise ValueError(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value)
        if candidates[strategy_id].get("ratified") is not True:
            raise ValueError(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value)

    panel_series, _panel_ref = load_panel_series_for_signal_matrix_v0(staging_root)
    eligible = set(binding.instrument_ids)
    filtered_series = tuple(series for series in panel_series if series.instrument_id in eligible)
    if not filtered_series:
        raise ValueError(ProductiveSignalJoinRejectionReason.INSTRUMENT_NOT_IN_BINDING.value)

    dropped_total: dict[str, int] = {}
    warmup_total = {name: 0 for name in EXPECTED_FLEET_SIGNAL_ORDER}
    signal_rows_by_name: dict[str, list[SignalSeriesRowV0]] = {
        name: [] for name in EXPECTED_FLEET_SIGNAL_ORDER
    }

    for strategy_id in EXPECTED_FLEET_SIGNAL_ORDER:
        for series in filtered_series:
            rows, dropped = materialize_strategy_signal_rows_v0(
                instrument_id=series.instrument_id,
                panel_series=series,
                strategy_id=strategy_id,
                candidate_binding=candidates[strategy_id],
                repo_root=repo_root,
                coverage_start_utc=binding.coverage_period_start_utc,
                coverage_end_utc=binding.coverage_period_end_utc,
            )
            signal_rows_by_name[strategy_id].extend(rows)
            for reason, count in dropped.items():
                if reason == ProductiveSignalJoinRejectionReason.WARMUP_EXCLUDED.value:
                    warmup_total[strategy_id] += count
                else:
                    dropped_total[reason] = dropped_total.get(reason, 0) + count

    joined_rows, join_dropped, _ = join_productive_signal_matrix_v0(
        {name: tuple(rows) for name, rows in signal_rows_by_name.items()}
    )
    for reason, count in join_dropped.items():
        dropped_total[reason] = dropped_total.get(reason, 0) + count

    row_count_before = sum(len(rows) for rows in signal_rows_by_name.values())
    row_count_after = len(joined_rows)
    time_range: dict[str, str] = {}
    if joined_rows:
        time_range = {
            "start": str(joined_rows[0][DECISION_TIME_KEY]),
            "end": str(joined_rows[-1][DECISION_TIME_KEY]),
        }

    instrument_universe = binding.instrument_ids
    instrument_universe_digest = compute_instrument_universe_digest_v0(instrument_universe)
    signal_matrix_digest = compute_signal_matrix_digest_v0(joined_rows)
    output_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "signal_matrix_digest": signal_matrix_digest,
            "row_count_after_join": row_count_after,
        }
    )
    materialization_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "output_digest": output_digest,
            "source_binding_digest": binding_digest,
            "signal_matrix_digest": signal_matrix_digest,
        }
    )
    parameter_config_digests = {
        str(item["strategy_id"]): str(item.get("strategy_params_digest", ""))
        for item in binding.strategy_bindings
    }
    provenance = SignalMatrixProductiveProvenanceV0(
        binding_digest=binding_digest,
        parameter_config_digests=parameter_config_digests,
        dataset_id=binding.dataset_id,
        dataset_digest=binding.dataset_digest,
        panel_dataset_digest=binding.panel_dataset_digest,
        instrument_ids=instrument_universe,
        instrument_universe_digest=instrument_universe_digest,
        coverage_period_start_utc=binding.coverage_period_start_utc,
        coverage_period_end_utc=binding.coverage_period_end_utc,
        row_count_before_join=row_count_before,
        row_count_after_join=row_count_after,
        dropped_rows_by_reason=dropped_total,
        per_signal_null_count={name: 0 for name in EXPECTED_FLEET_SIGNAL_ORDER},
        per_signal_warmup_exclusion_count=warmup_total,
        signal_matrix_digest=signal_matrix_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
    )
    join_result = ProductiveSignalJoinValidationResultV0(
        admissible_rows=joined_rows,
        row_count_before_filter=row_count_before,
        row_count_after_filter=row_count_after,
        dropped_rows_by_reason=dropped_total,
        per_signal_null_count={name: 0 for name in EXPECTED_FLEET_SIGNAL_ORDER},
        per_signal_warmup_exclusion_count=warmup_total,
        instrument_universe=instrument_universe,
        instrument_universe_digest=instrument_universe_digest,
        time_range=time_range,
        binding=binding,
    )
    status = MaterializationStatus.PASS if joined_rows else MaterializationStatus.INSUFFICIENT_DATA
    return MaterializationResultV0(
        status=status,
        rows=joined_rows,
        join_result=join_result,
        provenance=provenance,
        binding=binding,
        materialization_digest=materialization_digest,
        output_digest=output_digest,
        signal_matrix_digest=signal_matrix_digest,
        source_binding_digest=binding_digest,
    )


def serialize_signal_matrix_rows_v0(rows: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get(INSTRUMENT_ID_KEY, "")),
            str(row.get(DECISION_TIME_KEY, "")),
        ),
    )
    lines = [
        json.dumps(
            {
                INSTRUMENT_ID_KEY: row[INSTRUMENT_ID_KEY],
                DECISION_TIME_KEY: row[DECISION_TIME_KEY],
                FEATURE_TIME_KEY: row[FEATURE_TIME_KEY],
                **{name: row[name] for name in EXPECTED_FLEET_SIGNAL_ORDER},
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        for row in ordered
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def write_signal_matrix_csv_v0(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = [
        INSTRUMENT_ID_KEY,
        DECISION_TIME_KEY,
        FEATURE_TIME_KEY,
        *EXPECTED_FLEET_SIGNAL_ORDER,
    ]
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get(INSTRUMENT_ID_KEY, "")),
            str(row.get(DECISION_TIME_KEY, "")),
        ),
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in ordered:
            writer.writerow({name: row[name] for name in fieldnames})


def materializer_to_contract_roundtrip_pass_v0(rows: Sequence[Mapping[str, Any]]) -> bool:
    from src.research.linear_evidence.signal_orthogonality import analyze_signal_orthogonality

    if not rows:
        return False
    evidence = analyze_signal_orthogonality(
        list(rows),
        EXPECTED_FLEET_SIGNAL_ORDER,
        productive_binding_gap=False,
    )
    return (
        evidence.n_samples == len(rows)
        and evidence.feature_names == EXPECTED_FLEET_SIGNAL_ORDER
        and "PRODUCTIVE_BINDING_GAP" not in evidence.reason_codes
    )


__all__ = [
    "AUTHORITY_EFFECT",
    "CANONICAL_CONTRACT_OWNER",
    "CANONICAL_SIGNAL_BINDING_OWNER",
    "DEFAULT_STAGING_REL",
    "IMPLEMENTATION_DIGEST",
    "MaterializationResultV0",
    "MaterializationStatus",
    "PACKAGE_MARKER",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SignalSeriesRowV0",
    "build_signal_matrix_binding_v0",
    "join_productive_signal_matrix_v0",
    "load_panel_series_for_signal_matrix_v0",
    "load_ratified_binding_completion_v0",
    "materialize_offline_final_research_fleet_signal_matrix_v0",
    "materialize_strategy_signal_rows_v0",
    "materializer_to_contract_roundtrip_pass_v0",
    "panel_bars_to_strategy_dataframe_v0",
    "serialize_signal_matrix_rows_v0",
    "write_signal_matrix_csv_v0",
]
