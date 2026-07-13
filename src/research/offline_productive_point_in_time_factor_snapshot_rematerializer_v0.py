"""Offline productive point-in-time factor snapshot rematerializer v0.

Deterministic as-of rematerialization of productive factor snapshots from
manifest-verified trade ledger rows and admissible futures bar history. Selects
the latest finalized bar strictly before each trade entry_time for
funding_rate and volatility_estimate while preserving trade join keys.
No factor exposure diagnostic execution, runtime, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.research.linear_evidence.factor_exposure_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    PRODUCTIVE_FACTOR_SPECS,
    RUNTIME_EFFECT,
    stable_digest_v0,
)

PACKAGE_MARKER = "OFFLINE_PRODUCTIVE_POINT_IN_TIME_FACTOR_SNAPSHOT_REMATERIALIZER_V0=true"
SCHEMA_VERSION = "offline_productive_point_in_time_factor_snapshot_rematerializer.v0"
CANONICAL_BARS_LOADER_OWNER = (
    "scripts/ops/run_economic_viability_evidence_evaluation_v1.py::_load_bars_from_dataset_path"
)
CANONICAL_SPREAD_BINDING_OWNER = (
    "src/research/trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0.py"
)
ASOF_POLICY = "latest_finalized_bar_strictly_before_entry_time"


class DropReason(str, Enum):
    MISSING_TRADE_ID = "MISSING_TRADE_ID"
    DUPLICATE_TRADE_ID = "DUPLICATE_TRADE_ID"
    MISSING_INSTRUMENT_ID = "MISSING_INSTRUMENT_ID"
    MISSING_ENTRY_TIME = "MISSING_ENTRY_TIME"
    MISSING_PRIOR_BAR = "MISSING_PRIOR_BAR"
    DUPLICATE_PRIOR_BAR_CANDIDATE = "DUPLICATE_PRIOR_BAR_CANDIDATE"
    UNFINALIZED_PRIOR_BAR = "UNFINALIZED_PRIOR_BAR"
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    MISSING_VOLATILITY_ESTIMATE = "MISSING_VOLATILITY_ESTIMATE"
    MISSING_SPREAD_BPS_BINDING = "MISSING_SPREAD_BPS_BINDING"
    FEATURE_TIME_NOT_STRICTLY_BEFORE_ENTRY = "FEATURE_TIME_NOT_STRICTLY_BEFORE_ENTRY"
    INSTRUMENT_ID_MISMATCH = "INSTRUMENT_ID_MISMATCH"


class RematerializationStatus(str, Enum):
    PASS = "PASS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"


@dataclass(frozen=True)
class RejectedSnapshotRowV0:
    trade_id: str
    reason: DropReason


@dataclass(frozen=True)
class RematerializationResultV0:
    status: RematerializationStatus
    snapshots: tuple[dict[str, Any], ...]
    admissible_count: int
    rejected: tuple[RejectedSnapshotRowV0, ...]
    dropped_rows_by_reason: dict[str, int]
    materialization_digest: str
    source_trade_ledger_digest: str
    source_bars_digest: str
    source_dataset_ref: str
    spread_bps_binding: float
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def load_jsonl_rows(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError("JSONL_ROW_NOT_OBJECT")
        rows.append(payload)
    return tuple(rows)


def compute_source_rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(
        rows,
        key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":"), default=str),
    )
    return stable_digest_v0({"rows": list(ordered), "schema": "offline_evidence_jsonl_v0"})


def compute_bars_source_digest(*, bars: pd.DataFrame, source_dataset_ref: str) -> str:
    index_values = [ts.isoformat() for ts in bars.index]
    return stable_digest_v0(
        {
            "schema": "admissible_futures_bars_v0",
            "source_dataset_ref": source_dataset_ref,
            "row_count": len(bars),
            "index_min": index_values[0] if index_values else "",
            "index_max": index_values[-1] if index_values else "",
            "columns": sorted(str(col) for col in bars.columns),
        }
    )


def _is_finalized_bar(row: Mapping[str, Any]) -> bool:
    if "is_finalized" in row:
        return row.get("is_finalized") is True
    if "is_final" in row:
        return row.get("is_final") is True
    return False


def _row_mapping(row: Any) -> Mapping[str, Any]:
    if hasattr(row, "to_dict"):
        return row.to_dict()
    if isinstance(row, Mapping):
        return row
    raise TypeError("bar_row_not_mapping")


def lookup_prior_bar_asof_v0(
    *,
    bars: pd.DataFrame,
    entry_time: Any,
) -> tuple[pd.Timestamp, Mapping[str, Any]] | tuple[None, DropReason]:
    if bars.empty or entry_time is None:
        return None, DropReason.MISSING_PRIOR_BAR
    try:
        stamp = pd.Timestamp(entry_time)
        if stamp.tzinfo is None:
            stamp = stamp.tz_localize("UTC")
    except (TypeError, ValueError):
        return None, DropReason.MISSING_ENTRY_TIME

    prior_index = bars.index[bars.index < stamp]
    if len(prior_index) == 0:
        return None, DropReason.MISSING_PRIOR_BAR
    if len(prior_index) != len(set(prior_index)):
        return None, DropReason.DUPLICATE_PRIOR_BAR_CANDIDATE

    feature_ts = prior_index[-1]
    matched = bars.loc[feature_ts]
    if isinstance(matched, pd.DataFrame):
        return None, DropReason.DUPLICATE_PRIOR_BAR_CANDIDATE

    row = _row_mapping(matched)
    if not _is_finalized_bar(row):
        return None, DropReason.UNFINALIZED_PRIOR_BAR
    if feature_ts >= stamp:
        return None, DropReason.FEATURE_TIME_NOT_STRICTLY_BEFORE_ENTRY
    return feature_ts, row


def resolve_spread_bps_from_half_binding_v0(
    spread_half_bps: float | None,
) -> tuple[float | None, DropReason | None]:
    if spread_half_bps is None:
        return None, DropReason.MISSING_SPREAD_BPS_BINDING
    return 2.0 * float(spread_half_bps), None


def materialize_single_productive_point_in_time_factor_snapshot_v0(
    *,
    trade: Mapping[str, Any],
    bars: pd.DataFrame,
    spread_bps: float,
    source_dataset_ref: str,
    expected_instrument_id: str | None = None,
) -> tuple[dict[str, Any] | None, DropReason | None]:
    trade_id = str(trade.get("trade_id", ""))
    if not trade_id:
        return None, DropReason.MISSING_TRADE_ID

    instrument_id = str(trade.get("instrument_id", ""))
    if not instrument_id:
        return None, DropReason.MISSING_INSTRUMENT_ID
    if expected_instrument_id and instrument_id != expected_instrument_id:
        return None, DropReason.INSTRUMENT_ID_MISMATCH

    entry_time = str(trade.get("entry_time", ""))
    if not entry_time:
        return None, DropReason.MISSING_ENTRY_TIME

    feature_ts, prior_or_reason = lookup_prior_bar_asof_v0(bars=bars, entry_time=entry_time)
    if isinstance(prior_or_reason, DropReason):
        return None, prior_or_reason
    assert feature_ts is not None
    prior = prior_or_reason

    funding_raw = prior.get("funding_rate")
    if funding_raw is None or (isinstance(funding_raw, float) and pd.isna(funding_raw)):
        return None, DropReason.MISSING_FUNDING_RATE
    try:
        funding_rate = float(funding_raw)
    except (TypeError, ValueError):
        return None, DropReason.MISSING_FUNDING_RATE

    vol_raw = prior.get("volatility_estimate")
    if vol_raw is None or (isinstance(vol_raw, float) and pd.isna(vol_raw)):
        return None, DropReason.MISSING_VOLATILITY_ESTIMATE
    try:
        volatility_estimate = float(vol_raw)
    except (TypeError, ValueError):
        return None, DropReason.MISSING_VOLATILITY_ESTIMATE

    feature_timestamp = feature_ts.isoformat()
    if feature_timestamp >= entry_time:
        return None, DropReason.FEATURE_TIME_NOT_STRICTLY_BEFORE_ENTRY

    snapshot: dict[str, Any] = {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "bar_timestamp": entry_time,
        "feature_timestamp": feature_timestamp,
        "funding_rate": funding_rate,
        "spread_bps": spread_bps,
        "volatility_estimate": volatility_estimate,
        "is_finalized": True,
        "source_dataset_ref": source_dataset_ref,
        "source_row_identity": f"{instrument_id}@{feature_timestamp}",
        "asof_policy": ASOF_POLICY,
        "schema_version": SCHEMA_VERSION,
    }
    if prior.get("mark_price") is not None and not pd.isna(prior.get("mark_price")):
        snapshot["mark_price"] = float(prior["mark_price"])
    if prior.get("volume") is not None and not pd.isna(prior.get("volume")):
        snapshot["volume"] = float(prior["volume"])
    return snapshot, None


def materialize_productive_point_in_time_factor_snapshots_v0(
    *,
    trade_ledger_rows: Sequence[Mapping[str, Any]],
    bars: pd.DataFrame,
    spread_half_bps: float | None,
    source_dataset_ref: str,
    expected_instrument_id: str | None = None,
    source_trade_ledger_digest: str | None = None,
    source_bars_digest: str | None = None,
) -> RematerializationResultV0:
    spread_bps, spread_reason = resolve_spread_bps_from_half_binding_v0(spread_half_bps)
    if spread_reason is not None or spread_bps is None:
        spread_bps = float("nan")

    ledger_digest = source_trade_ledger_digest or compute_source_rows_digest(trade_ledger_rows)
    bars_digest = source_bars_digest or compute_bars_source_digest(
        bars=bars,
        source_dataset_ref=source_dataset_ref,
    )

    rejected: list[RejectedSnapshotRowV0] = []
    dropped: dict[str, int] = {}
    admissible: list[dict[str, Any]] = []
    seen_trade_ids: set[str] = set()

    ordered_trades = sorted(
        trade_ledger_rows,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("entry_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )

    for trade in ordered_trades:
        trade_id = str(trade.get("trade_id", ""))
        if not trade_id:
            reason = DropReason.MISSING_TRADE_ID
            rejected.append(RejectedSnapshotRowV0(trade_id="", reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        if trade_id in seen_trade_ids:
            reason = DropReason.DUPLICATE_TRADE_ID
            rejected.append(RejectedSnapshotRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        seen_trade_ids.add(trade_id)

        if spread_reason is not None:
            rejected.append(RejectedSnapshotRowV0(trade_id=trade_id, reason=spread_reason))
            dropped[spread_reason.value] = dropped.get(spread_reason.value, 0) + 1
            continue

        snapshot, row_reason = materialize_single_productive_point_in_time_factor_snapshot_v0(
            trade=trade,
            bars=bars,
            spread_bps=spread_bps,
            source_dataset_ref=source_dataset_ref,
            expected_instrument_id=expected_instrument_id,
        )
        if row_reason is not None or snapshot is None:
            reason = row_reason or DropReason.MISSING_PRIOR_BAR
            rejected.append(RejectedSnapshotRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        admissible.append(snapshot)

    admissible_sorted = sorted(
        admissible,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("entry_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )

    if not admissible_sorted:
        status = (
            RematerializationStatus.TARGET_BINDING_MISSING
            if trade_ledger_rows
            else RematerializationStatus.INSUFFICIENT_DATA
        )
    else:
        status = RematerializationStatus.PASS

    materialization_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "snapshots": admissible_sorted,
            "source_trade_ledger_digest": ledger_digest,
            "source_bars_digest": bars_digest,
            "spread_half_bps": spread_half_bps,
            "dropped_rows_by_reason": dropped,
        }
    )

    return RematerializationResultV0(
        status=status,
        snapshots=tuple(admissible_sorted),
        admissible_count=len(admissible_sorted),
        rejected=tuple(rejected),
        dropped_rows_by_reason=dropped,
        materialization_digest=materialization_digest,
        source_trade_ledger_digest=ledger_digest,
        source_bars_digest=bars_digest,
        source_dataset_ref=source_dataset_ref,
        spread_bps_binding=spread_bps if spread_reason is None else float("nan"),
    )


def serialize_productive_point_in_time_factor_snapshots_v0(
    snapshots: Sequence[Mapping[str, Any]],
) -> str:
    ordered = sorted(
        snapshots,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("entry_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) for row in ordered]
    return "\n".join(lines) + ("\n" if lines else "")


def productive_factor_field_provenance_v0() -> dict[str, Any]:
    return {
        "features": [
            {
                "canonical_name": spec.canonical_name,
                "source_field": spec.source_field,
                "source_artifact": "admissible_futures_bars.parquet",
                "observed_event_timestamp_field": "feature_timestamp",
                "availability_timestamp_field": "feature_timestamp",
                "finalized_bar_field": "is_final",
                "instrument_identity_field": "instrument_id",
                "asof_policy": ASOF_POLICY,
            }
            for spec in PRODUCTIVE_FACTOR_SPECS
        ],
        "spread_bps": {
            "source_artifact": "spread_half_bps_binding",
            "observed_event_timestamp_field": "N/A_STATIC_BINDING",
            "availability_timestamp_field": "evaluation_binding_time",
            "transformation": "2.0 * spread_half_bps",
        },
    }


__all__ = [
    "ASOF_POLICY",
    "AUTHORITY_EFFECT",
    "CANONICAL_BARS_LOADER_OWNER",
    "CANONICAL_SPREAD_BINDING_OWNER",
    "DropReason",
    "PACKAGE_MARKER",
    "RematerializationResultV0",
    "RematerializationStatus",
    "RejectedSnapshotRowV0",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "compute_bars_source_digest",
    "compute_source_rows_digest",
    "load_jsonl_rows",
    "lookup_prior_bar_asof_v0",
    "materialize_productive_point_in_time_factor_snapshots_v0",
    "materialize_single_productive_point_in_time_factor_snapshot_v0",
    "productive_factor_field_provenance_v0",
    "resolve_spread_bps_from_half_binding_v0",
    "serialize_productive_point_in_time_factor_snapshots_v0",
]
