#!/usr/bin/env python3
"""OKX economic research dataset staging from verified raw cache v1 (RUNBOOK STEP 29M).

Offline-only: reads digest-verified OKX raw staging, normalizes to economic_research_v1,
binds execution cost model, validates admissibility, atomically finalizes dataset.
No network, no evaluation, no runtime effect.
Operator GO: GO_OKX_ECONOMIC_RESEARCH_DATASET_STAGING_V1
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (
    ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as okx_ingest,
)
from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest import cost_config_v0 as cost

CONFIRM_TOKEN = "GO_OKX_ECONOMIC_RESEARCH_DATASET_STAGING_V1"
DATASET_PROFILE = ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value
L1_OBSERVATION_STATUS = ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value
MANIFEST_VERSION = "admissible_versioned_futures_dataset_manifest_v1"
DEFAULT_CONSERVATIVE_HALF_SPREAD_BPS = 5.0

CANONICAL_FEE_BPS = 10.0
CANONICAL_SLIPPAGE_BPS = 5.0


class StagingError(Exception):
    """Fail-closed economic research dataset staging error."""


@dataclass(frozen=True)
class RawDigestVerification:
    verified: bool
    file_count: int
    mismatch_count: int
    mismatches: Tuple[str, ...]


@dataclass(frozen=True)
class IntegrityReport:
    passed: bool
    raw_row_counts: Dict[str, int]
    join_row_count: int
    discarded_rows: List[Dict[str, Any]]
    gap_statistics: Dict[str, Any]
    missingness: Dict[str, int]
    staleness: Dict[str, Any]
    data_period: Dict[str, str]
    bar_granularity: str
    reason_codes: Tuple[str, ...]


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _parse_utc_z(value: str) -> pd.Timestamp:
    return (
        pd.Timestamp(value).tz_convert("UTC")
        if pd.Timestamp(value).tzinfo
        else pd.Timestamp(value, tz="UTC")
    )


def _iso_z(ts: pd.Timestamp) -> str:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_raw_staging_digests(
    raw_staging_root: Path,
    *,
    request_log_path: Optional[Path] = None,
) -> RawDigestVerification:
    log_path = request_log_path or (raw_staging_root / "reports" / "REQUEST_LOG.json")
    if not log_path.is_file():
        raise StagingError(f"request_log_missing:{log_path}")
    request_log = json.loads(log_path.read_text(encoding="utf-8"))
    mismatches: List[str] = []
    seen = 0
    for entry in request_log:
        rel_path = entry.get("raw_response_path")
        expected = str(entry.get("raw_response_sha256", ""))
        if not rel_path or not expected:
            continue
        raw_path = Path(str(rel_path))
        if not raw_path.is_file():
            mismatches.append(f"missing_file:{raw_path}")
            continue
        actual = okx_ingest._sha256_bytes(raw_path.read_bytes())
        seen += 1
        if actual != expected:
            mismatches.append(f"digest_mismatch:{raw_path}:expected={expected}:actual={actual}")
    return RawDigestVerification(
        verified=len(mismatches) == 0 and seen > 0,
        file_count=seen,
        mismatch_count=len(mismatches),
        mismatches=tuple(mismatches),
    )


def _load_finalized_candles(raw_dir: Path, prefix: str) -> Dict[int, List[Any]]:
    dedup: Dict[int, List[Any]] = {}
    for path in sorted(raw_dir.glob(f"{prefix}_p*.json")):
        payload = json.loads(path.read_bytes())
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, list) and okx_ingest._candle_is_final(row):
                dedup[int(str(row[0]))] = row
    return dedup


def _load_funding_rows(raw_dir: Path) -> Dict[int, Dict[str, Any]]:
    dedup: Dict[int, Dict[str, Any]] = {}
    for path in sorted(raw_dir.glob("funding_p*.json")):
        payload = json.loads(path.read_bytes())
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, Mapping):
                dedup[int(str(row["fundingTime"]))] = dict(row)
    return dedup


def _candle_frame(candles: Mapping[int, Sequence[Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for ts in sorted(candles):
        row = candles[ts]
        rows.append(
            {
                "timestamp_ms": ts,
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
        )
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    return frame.set_index("timestamp").sort_index()


def _price_candle_frame(candles: Mapping[int, Sequence[Any]], column: str) -> pd.DataFrame:
    rows = [{"timestamp_ms": ts, column: float(candles[ts][4])} for ts in sorted(candles)]
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    return frame.set_index("timestamp").sort_index()[[column]]


def _funding_frame(funding: Mapping[int, Mapping[str, Any]]) -> pd.DataFrame:
    rows = [
        {
            "funding_time_ms": ts,
            "funding_rate": float(funding[ts]["fundingRate"]),
        }
        for ts in sorted(funding)
    ]
    frame = pd.DataFrame(rows)
    frame["funding_time"] = pd.to_datetime(frame["funding_time_ms"], unit="ms", utc=True)
    return frame.set_index("funding_time").sort_index()


def _backward_asof_join(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    *,
    value_column: str,
    tolerance_ms: int,
    staleness_key: str,
    staleness_accumulator: Dict[str, List[float]],
) -> pd.Series:
    if secondary.empty:
        raise StagingError(f"secondary_series_empty:{value_column}")
    left = primary.reset_index().rename(columns={"timestamp": "primary_ts"})
    left["primary_ts"] = pd.to_datetime(left["primary_ts"], utc=True)
    right = secondary.reset_index()
    time_col = right.columns[0]
    right = right.rename(columns={time_col: "secondary_ts", value_column: value_column})
    right["secondary_ts"] = pd.to_datetime(right["secondary_ts"], utc=True)
    merged = pd.merge_asof(
        left.sort_values("primary_ts"),
        right.sort_values("secondary_ts"),
        left_on="primary_ts",
        right_on="secondary_ts",
        direction="backward",
        tolerance=pd.Timedelta(milliseconds=tolerance_ms),
    )
    staleness_ms = (merged["primary_ts"] - merged["secondary_ts"]).dt.total_seconds() * 1000.0
    staleness_accumulator[staleness_key] = [float(v) for v in staleness_ms.dropna().tolist()]
    return pd.Series(merged[value_column].values, index=primary.index, name=value_column)


def normalize_economic_research_bars(
    *,
    raw_dir: Path,
    start_utc: str,
    end_utc: str,
) -> Tuple[pd.DataFrame, IntegrityReport]:
    start_ts = _parse_utc_z(start_utc)
    end_ts = _parse_utc_z(end_utc)
    start_ms = int(start_ts.timestamp() * 1000)
    end_ms = int(end_ts.timestamp() * 1000)

    ohlcv_raw = _load_finalized_candles(raw_dir, "ohlcv")
    mark_raw = _load_finalized_candles(raw_dir, "mark")
    index_raw = _load_finalized_candles(raw_dir, "index")
    funding_raw = _load_funding_rows(raw_dir)

    raw_counts = {
        "ohlcv": len(ohlcv_raw),
        "mark": len(mark_raw),
        "index": len(index_raw),
        "funding": len(funding_raw),
    }

    ohlcv_in_window = {ts: row for ts, row in ohlcv_raw.items() if start_ms <= ts <= end_ms}
    ohlcv = _candle_frame(ohlcv_in_window)
    mark = _price_candle_frame(
        {ts: row for ts, row in mark_raw.items() if start_ms <= ts <= end_ms},
        "mark_price",
    )
    index = _price_candle_frame(
        {ts: row for ts, row in index_raw.items() if start_ms <= ts <= end_ms},
        "index_price",
    )
    funding = _funding_frame(
        {ts: row for ts, row in funding_raw.items() if start_ms <= ts <= end_ms}
    )

    discarded: List[Dict[str, Any]] = []
    staleness: Dict[str, List[float]] = {}
    bars = ohlcv.copy()
    bars["mark_price"] = _backward_asof_join(
        bars,
        mark,
        value_column="mark_price",
        tolerance_ms=okx_ingest.MAX_MARK_INDEX_STALENESS_MS,
        staleness_key="mark_price_ms",
        staleness_accumulator=staleness,
    )
    bars["index_price"] = _backward_asof_join(
        bars,
        index,
        value_column="index_price",
        tolerance_ms=okx_ingest.MAX_MARK_INDEX_STALENESS_MS,
        staleness_key="index_price_ms",
        staleness_accumulator=staleness,
    )
    bars["funding_rate"] = _backward_asof_join(
        bars,
        funding.rename(columns={"funding_rate": "funding_rate"}),
        value_column="funding_rate",
        tolerance_ms=okx_ingest.MAX_FUNDING_STALENESS_MS,
        staleness_key="funding_rate_ms",
        staleness_accumulator=staleness,
    )
    bars["is_final"] = True

    missing_mask = bars[["mark_price", "index_price", "funding_rate"]].isna().any(axis=1)
    if missing_mask.any():
        for ts in bars.index[missing_mask]:
            discarded.append({"timestamp": _iso_z(ts), "reason": "join_missing_required_field"})
        bars = bars.loc[~missing_mask]

    reason_codes: List[str] = []
    if bars.empty:
        reason_codes.append("bars_empty_after_join")

    if not bars.index.is_monotonic_increasing:
        reason_codes.append("index_not_sorted")
    if bars.index.has_duplicates:
        reason_codes.append("duplicate_timestamps")

    gap_seconds: List[float] = []
    if len(bars) > 1:
        deltas = bars.index.to_series().diff().dropna().dt.total_seconds()
        gap_seconds = [float(v) for v in deltas.tolist()]
        unexpected = [g for g in gap_seconds if g > 60.0]
        if unexpected:
            reason_codes.append("unexplained_time_gaps")

    for column in ("open", "high", "low", "close", "mark_price", "index_price"):
        if (bars[column] <= 0).any():
            reason_codes.append(f"non_positive:{column}")
    if (bars["volume"] < 0).any():
        reason_codes.append("negative_volume")
    if not bars["is_final"].all():
        reason_codes.append("non_final_rows")
    if not bars["funding_rate"].map(math.isfinite).all():
        reason_codes.append("non_finite_funding_rate")

    for ts, row in bars.iterrows():
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        if h < max(o, c, l) or l > min(o, c, h):
            reason_codes.append("ohlc_inconsistent")
            break

    missingness = {col: int(bars[col].isna().sum()) for col in bars.columns}
    gap_stats = {
        "bar_granularity_seconds": 60,
        "gap_count_gt_60s": sum(1 for g in gap_seconds if g > 60.0),
        "max_gap_seconds": max(gap_seconds) if gap_seconds else 0.0,
        "median_gap_seconds": float(pd.Series(gap_seconds).median()) if gap_seconds else 0.0,
    }
    staleness_summary = {
        key: {
            "max_ms": max(values) if values else None,
            "p95_ms": float(pd.Series(values).quantile(0.95)) if values else None,
        }
        for key, values in staleness.items()
    }

    report = IntegrityReport(
        passed=len(reason_codes) == 0,
        raw_row_counts=raw_counts,
        join_row_count=len(bars),
        discarded_rows=discarded,
        gap_statistics=gap_stats,
        missingness=missingness,
        staleness=staleness_summary,
        data_period={"start_utc": start_utc, "end_utc": end_utc},
        bar_granularity=okx_ingest.BAR_GRANULARITY,
        reason_codes=tuple(sorted(set(reason_codes))),
    )
    return bars, report


def build_cost_model_binding(
    *,
    half_spread_bps: float = DEFAULT_CONSERVATIVE_HALF_SPREAD_BPS,
    fee_bps: float = CANONICAL_FEE_BPS,
    slippage_bps: float = CANONICAL_SLIPPAGE_BPS,
) -> Dict[str, Any]:
    if fee_bps <= 0 or slippage_bps <= 0 or half_spread_bps <= 0:
        raise StagingError("execution_cost_binding_non_positive")
    entry = cost.compute_effective_entry_cost_bps(
        fee_bps=fee_bps, slippage_bps=slippage_bps, half_spread_bps=half_spread_bps
    )
    exit_cost = cost.compute_effective_exit_cost_bps(
        fee_bps=fee_bps, slippage_bps=slippage_bps, half_spread_bps=half_spread_bps
    )
    roundtrip = cost.compute_effective_roundtrip_cost_bps(
        fee_bps=fee_bps, slippage_bps=slippage_bps, half_spread_bps=half_spread_bps
    )
    spread_binding = {
        "spread_model_version": cost.RESEARCH_SPREAD_MODEL_VERSION,
        "execution_price_observation_source": cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED,
        "conservative_half_spread_bps": half_spread_bps,
    }
    payload = {
        "fee_model_version": cost.FEE_MODEL_VERSION,
        "slippage_model_version": cost.SLIPPAGE_MODEL_VERSION,
        "spread_model_version": cost.RESEARCH_SPREAD_MODEL_VERSION,
        "execution_model_version": cost.EXECUTION_MODEL_VERSION,
        "execution_price_observation_source": cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "conservative_half_spread_bps": half_spread_bps,
        "effective_entry_cost_bps": entry,
        "effective_exit_cost_bps": exit_cost,
        "roundtrip_cost_bps": roundtrip,
        "execution_cost_binding": spread_binding,
        "double_counting_policy": "fee_slippage_and_half_spread_separate_no_double_count",
    }
    payload["config_digest"] = cost.compute_cost_config_digest(payload)
    return payload


def build_profile_binding(cost_binding: Mapping[str, Any]) -> ds.DatasetProfileBindingV1:
    return ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version=str(cost_binding["spread_model_version"]),
            execution_price_observation_source=str(
                cost_binding["execution_price_observation_source"]
            ),
            conservative_half_spread_bps=float(cost_binding["conservative_half_spread_bps"]),
        ),
    )


def _resolve_target_version(target_dataset_root: Path, normalized_digest: str) -> Tuple[Path, str]:
    parent = target_dataset_root.parent
    version = target_dataset_root.name
    if not target_dataset_root.exists():
        return target_dataset_root, version
    manifest_path = target_dataset_root / "dataset_manifest.json"
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if str(existing.get("normalized_dataset_digest")) == normalized_digest:
            return target_dataset_root, version
    if version == "v1":
        return parent / "v2", "v2"
    raise StagingError(f"DATASET_VERSION_CONFLICT:{target_dataset_root}")


def run_economic_research_staging_from_raw(
    *,
    confirm: str,
    raw_staging_root: Path,
    target_dataset_root: Path,
    durable_evidence_root: Path,
    ingestion_evidence_root: Optional[Path] = None,
    request_log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required")

    if not raw_staging_root.is_dir():
        raise StagingError(f"raw_staging_root_missing:{raw_staging_root}")

    digest_report = verify_raw_staging_digests(raw_staging_root, request_log_path=request_log_path)
    if not digest_report.verified:
        return {
            "verdict": "RAW_STAGING_DIGEST_MISMATCH",
            "digest_verification": digest_report.__dict__,
            "manifest_verify_rc": 1,
        }

    ingestion_config_path = raw_staging_root / "INGESTION_CONFIG.json"
    instrument_binding_path = raw_staging_root / "INSTRUMENT_BINDING.json"
    if not ingestion_config_path.is_file() or not instrument_binding_path.is_file():
        raise StagingError("raw_staging_metadata_missing")

    ingestion_config = json.loads(ingestion_config_path.read_text(encoding="utf-8"))
    instrument_binding = json.loads(instrument_binding_path.read_text(encoding="utf-8"))
    data_period = ingestion_config["data_period"]
    start_utc = str(data_period["start_utc"])
    end_utc = str(data_period["end_utc"])

    bars, integrity = normalize_economic_research_bars(
        raw_dir=raw_staging_root / "raw",
        start_utc=start_utc,
        end_utc=end_utc,
    )
    if not integrity.passed:
        return {
            "verdict": "DATASET_INTEGRITY_FAILED",
            "integrity_report": integrity.__dict__,
            "manifest_verify_rc": 1,
        }

    cost_binding = build_cost_model_binding()
    profile_binding = build_profile_binding(cost_binding)
    field_bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    dataset_digest = ds.compute_versioned_dataset_digest(bars, field_bindings=field_bindings)
    training, validation, oos = ds.compute_split_periods_from_bars(bars)
    idx = bars.sort_index().index

    provenance_payload = {
        "source_type": "operator_staged_futures_v1",
        "source_venue": "OKX",
        "native_instrument_id": okx_ingest.NATIVE_INSTRUMENT_ID,
        "canonical_instrument_id": okx_ingest.CANONICAL_INSTRUMENT_ID,
        "contract_type": okx_ingest.CANONICAL_CONTRACT_TYPE,
        "acquisition_method": "okx_public_rest_api_v5",
        "authenticated": False,
        "credentials_used": False,
        "dataset_profile": DATASET_PROFILE,
        "l1_observation_status": L1_OBSERVATION_STATUS,
        "observed_l1_used": False,
        "generation_method": "okx_economic_research_dataset_staging_v1",
        "staging_timestamp_utc": _utc_now_z(),
        "raw_staging_root": str(raw_staging_root),
        "ingestion_evidence_root": str(ingestion_evidence_root or ""),
    }
    provenance = ds.DatasetProvenanceV1(
        source_type="operator_staged_futures_v1",
        venue_id="OKX",
        ingestion_timestamp=str(
            json.loads((raw_staging_root / "reports" / "PROVENANCE.json").read_text())[
                "ingestion_timestamp_utc"
            ]
        ),
        generation_method="okx_economic_research_dataset_staging_v1",
        provenance_ref=str(raw_staging_root / "reports" / "PROVENANCE.json"),
    )
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id=f"{okx_ingest.CANONICAL_INSTRUMENT_ID}_{ds.DEFAULT_DATASET_VERSION}",
        dataset_version=ds.DEFAULT_DATASET_VERSION,
        dataset_schema_version=ds.DATASET_SCHEMA_VERSION,
        dataset_digest=dataset_digest,
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        contract_type=okx_ingest.CANONICAL_CONTRACT_TYPE,
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id="OKX",
        start_time=str(idx[0]),
        end_time=str(idx[-1]),
        row_count=len(bars),
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

    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        profile_binding=profile_binding,
    )
    runtime_rejection = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        profile_binding=ds.default_runtime_profile_binding_v1(),
    )

    if not admissibility.is_admissible():
        return {
            "verdict": "DATASET_PROFILE_ADMISSIBILITY_FAILED",
            "admissibility_status": admissibility.admissibility_status.value,
            "reason_codes": list(admissibility.reason_codes),
            "manifest_verify_rc": 1,
        }
    if runtime_rejection.is_admissible():
        return {
            "verdict": "DATASET_PROFILE_ADMISSIBILITY_FAILED",
            "reason_codes": ["runtime_profile_must_reject_research_dataset"],
            "manifest_verify_rc": 1,
        }

    resolved_target, dataset_version = _resolve_target_version(target_dataset_root, dataset_digest)
    if resolved_target.exists() and dataset_version != target_dataset_root.name:
        conflict_note = (
            f"target_version_exists_with_different_digest; using {dataset_version} instead of "
            f"{target_dataset_root.name}"
        )
    else:
        conflict_note = ""

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp_root = resolved_target.parent / f".tmp_{ts_slug}"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)

    split_binding = {
        "split_policy_version": ds.SPLIT_POLICY_VERSION,
        "training_period": training,
        "validation_period": validation,
        "out_of_sample_period": oos,
        "disjoint": True,
        "temporally_ordered": True,
        "leakage_free": admissibility.leakage_check_status == "PASS",
    }
    staging_config = {
        "go_token": CONFIRM_TOKEN,
        "dataset_profile": DATASET_PROFILE,
        "l1_observation_status": L1_OBSERVATION_STATUS,
        "observed_l1_used": False,
        "raw_staging_root": str(raw_staging_root),
        "target_dataset_root": str(resolved_target),
        "dataset_version": dataset_version,
        "join_policies": ingestion_config.get("join_policies", {}),
        "economic_research_execution_cost": {
            "spread_model_version": cost.RESEARCH_SPREAD_MODEL_VERSION,
            "execution_price_observation_source": cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED,
            "conservative_half_spread_bps": DEFAULT_CONSERVATIVE_HALF_SPREAD_BPS,
            "fee_bps": CANONICAL_FEE_BPS,
            "slippage_bps": CANONICAL_SLIPPAGE_BPS,
        },
    }
    data_quality = {
        "dataset_admissible": True,
        "integrity_pass": integrity.passed,
        "raw_row_counts": integrity.raw_row_counts,
        "join_row_count": integrity.join_row_count,
        "discarded_rows": integrity.discarded_rows,
        "gap_statistics": integrity.gap_statistics,
        "missingness": integrity.missingness,
        "staleness": integrity.staleness,
        "data_period": integrity.data_period,
        "bar_granularity": integrity.bar_granularity,
        "reason_codes": list(integrity.reason_codes),
    }

    request_log = json.loads((raw_staging_root / "reports" / "REQUEST_LOG.json").read_text())
    raw_response_digests = {
        str(entry.get("raw_response_path", "")): str(entry.get("raw_response_sha256", ""))
        for entry in request_log
        if entry.get("raw_response_sha256")
    }

    manifest_without_digest: Dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "dataset_profile": DATASET_PROFILE,
        "dataset_version": dataset_version,
        "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
        "instrument_id": okx_ingest.CANONICAL_INSTRUMENT_ID,
        "native_instrument_id": okx_ingest.NATIVE_INSTRUMENT_ID,
        "contract_type": okx_ingest.CANONICAL_CONTRACT_TYPE,
        "futures_only": True,
        "data_period": integrity.data_period,
        "bar_granularity": integrity.bar_granularity,
        "row_count": len(bars),
        "required_columns": sorted(
            ds.required_bar_columns_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
        ),
        "optional_columns": [],
        "l1_observation_status": L1_OBSERVATION_STATUS,
        "observed_l1_used": False,
        "execution_cost_binding": cost_binding["execution_cost_binding"],
        "fee_model_version": cost_binding["fee_model_version"],
        "slippage_model_version": cost_binding["slippage_model_version"],
        "spread_model_version": cost_binding["spread_model_version"],
        "execution_model_version": cost_binding["execution_model_version"],
        "source_endpoints": ingestion_config.get("acquisition_endpoint_order", []),
        "acquisition_timestamps": {
            "ingestion_timestamp_utc": provenance.ingestion_timestamp,
            "staging_timestamp_utc": _utc_now_z(),
        },
        "provenance": provenance_payload,
        "instrument_metadata": instrument_binding.get("instrument_metadata", {}),
        "join_policies": ingestion_config.get("join_policies", {}),
        "staleness_limits": {
            "max_mark_index_staleness_ms": okx_ingest.MAX_MARK_INDEX_STALENESS_MS,
            "max_funding_staleness_ms": okx_ingest.MAX_FUNDING_STALENESS_MS,
        },
        "integrity_results": data_quality,
        "training_period": training,
        "validation_period": validation,
        "out_of_sample_period": oos,
        "raw_response_digests": raw_response_digests,
        "normalized_dataset_digest": dataset_digest,
        "implementation_digest": admissibility.implementation_digest,
        "config_digest": admissibility.config_digest,
        "profile_binding": profile_binding.to_dict(),
        "profile_binding_digest": admissibility.profile_binding_digest,
    }
    manifest_digest = okx_ingest._stable_digest(manifest_without_digest)
    manifest = {**manifest_without_digest, "manifest_digest": manifest_digest}

    bars_out = bars.reset_index().rename(columns={"timestamp": "timestamp"})
    bars_out["timestamp"] = bars_out["timestamp"].map(_iso_z)
    bars_out.to_parquet(tmp_root / "bars.parquet", index=False)

    for name, payload in (
        ("dataset_manifest.json", manifest),
        ("STAGING_CONFIG.json", staging_config),
        ("DATA_QUALITY_REPORT.json", data_quality),
        ("INSTRUMENT_BINDING.json", instrument_binding),
        ("COST_MODEL_BINDING.json", cost_binding),
        ("SPLIT_BINDING.json", split_binding),
        ("PROVENANCE.json", provenance_payload),
    ):
        (tmp_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    post_manifest = json.loads((tmp_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    post_digest = okx_ingest._stable_digest(
        {k: v for k, v in post_manifest.items() if k != "manifest_digest"}
    )
    if post_digest != post_manifest["manifest_digest"]:
        raise StagingError("manifest_digest_mismatch_after_write")

    if resolved_target.exists():
        raise StagingError(f"DATASET_VERSION_CONFLICT:{resolved_target}")
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    tmp_root.rename(resolved_target)

    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"step29m_okx_economic_research_dataset_staging_v1_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "verdict": "OKX_ECONOMIC_RESEARCH_DATASET_STAGING_COMPLETE",
        "dataset_path": str(resolved_target),
        "manifest_path": str(resolved_target / "dataset_manifest.json"),
        "dataset_digest": dataset_digest,
        "manifest_digest": manifest_digest,
        "dataset_version": dataset_version,
        "version_conflict_note": conflict_note,
        "admissibility_status": admissibility.admissibility_status.value,
        "runtime_rejection_status": runtime_rejection.admissibility_status.value,
        "integrity_report": integrity.__dict__,
        "cost_binding": cost_binding,
        "split_binding": split_binding,
        "provenance": provenance_payload,
        "raw_digest_verification": digest_report.__dict__,
        "real_admissible_futures_dataset_found": True,
        "real_admissible_futures_evidence_present": True,
        "real_admissible_futures_evidence_bound": False,
        "real_evaluation_performed": False,
        "economic_validity_result": "NOT_PROVEN",
        "economic_validity_offline_gate_pass": False,
        "current_promotion_evaluation": "INELIGIBLE",
        "operator_input_required_for_real_evaluation": True,
        "real_evaluation_input_status": "ADMISSIBLE_DATASET_STAGED_AWAITING_EVALUATION_CONFIG_AND_RUN",
        "runtime_rewire_implementation_allowed": False,
        "runbook_step_29m_complete": True,
        "economic_research_dataset_profile_v1_bound": True,
    }
    (evidence_dir / "STAGING_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for rel in (
        "dataset_manifest.json",
        "STAGING_CONFIG.json",
        "DATA_QUALITY_REPORT.json",
        "INSTRUMENT_BINDING.json",
        "COST_MODEL_BINDING.json",
        "SPLIT_BINDING.json",
        "PROVENANCE.json",
    ):
        shutil.copy2(resolved_target / rel, evidence_dir / rel)

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    result["durable_evidence_path"] = str(evidence_dir)
    result["manifest_verify_rc"] = rc
    result["manifest_verify_msg"] = verify_msg
    _emit_machine_lines(result)
    return result


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    lines = [
        f"VERDICT={result.get('verdict')}",
        f"GO_TOKEN={CONFIRM_TOKEN}",
        f"REAL_ADMISSIBLE_FUTURES_DATASET_FOUND={str(result.get('real_admissible_futures_dataset_found', False)).lower()}",
        f"REAL_ADMISSIBLE_FUTURES_EVIDENCE_PRESENT={str(result.get('real_admissible_futures_evidence_present', False)).lower()}",
        f"REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND={str(result.get('real_admissible_futures_evidence_bound', False)).lower()}",
        f"REAL_EVALUATION_PERFORMED=false",
        f"ECONOMIC_VALIDITY_RESULT=NOT_PROVEN",
        f"MANIFEST_VERIFY_RC={result.get('manifest_verify_rc', 1)}",
        "ORDER_EFFECT=false",
        "RUNTIME_EFFECT=false",
        "LIVE_AUTHORIZED=false",
    ]
    for line in lines:
        print(line)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage OKX economic research dataset from verified raw cache v1."
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_TOKEN])
    parser.add_argument("--raw-staging-root", type=Path, required=True)
    parser.add_argument("--target-dataset-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--ingestion-evidence-root", type=Path, default=None)
    parser.add_argument("--request-log-path", type=Path, default=None)
    ns = parser.parse_args(argv)
    try:
        run_economic_research_staging_from_raw(
            confirm=ns.confirm_go_token,
            raw_staging_root=ns.raw_staging_root,
            target_dataset_root=ns.target_dataset_root,
            durable_evidence_root=ns.durable_evidence_root,
            ingestion_evidence_root=ns.ingestion_evidence_root,
            request_log_path=ns.request_log_path,
        )
    except (StagingError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            raise
        _die(f"ERR: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
