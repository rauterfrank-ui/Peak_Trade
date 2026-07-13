"""Offline linear cost diagnostic row materializer v0.

Deterministic, offline-only join of manifest-verified TRADE_LEDGER_V1 rows to
entry-time bar reference snapshots. Computes SIMULATED_BACKTEST_SLIPPAGE target
via the canonical execution_reports side-adjusted formula. No OLS, calibration,
economic evaluation, runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

SCHEMA_VERSION = "offline_linear_cost_diagnostic_row_materializer.v0"
TARGET_NAME = "simulated_backtest_slippage_bps"
TARGET_PROVENANCE_CLASS = "SIMULATED_BACKTEST_SLIPPAGE"
CANONICAL_REFERENCE_PRICE_OWNER = "close_for_execution_reference_only"
CANONICAL_JOIN_KEY = "trade_id + instrument_id + entry_time"

INCONCLUSIVE_SENTINEL = "INCONCLUSIVE"

REQUIRED_DIAGNOSTIC_FIELDS = (
    "instrument_id",
    "side",
    "decision_time",
    "spread_bps",
    "volatility_estimate",
    "order_notional",
    "simulated_or_realized_fill_price",
    "execution_reference_price",
    TARGET_NAME,
)

OPTIONAL_DIAGNOSTIC_FIELDS = (
    "funding_rate_abs",
    "liquidity_score",
    "regime",
    "best_bid",
    "best_ask",
    "depth_near_touch",
)


class RejectionReason(str, Enum):
    MISSING_TRADE_ID = "MISSING_TRADE_ID"
    DUPLICATE_TRADE_ID = "DUPLICATE_TRADE_ID"
    MISSING_INSTRUMENT_ID = "MISSING_INSTRUMENT_ID"
    MISSING_ENTRY_TIME = "MISSING_ENTRY_TIME"
    MISSING_REFERENCE_SNAPSHOT = "MISSING_REFERENCE_SNAPSHOT"
    DUPLICATE_JOIN_CANDIDATE = "DUPLICATE_JOIN_CANDIDATE"
    NONPOSITIVE_REFERENCE_PRICE = "NONPOSITIVE_REFERENCE_PRICE"
    FEATURE_AFTER_TARGET_TIME = "FEATURE_AFTER_TARGET_TIME"
    UNFINALIZED_BAR = "UNFINALIZED_BAR"
    INCONCLUSIVE_FIELD = "INCONCLUSIVE_FIELD"
    INVALID_SIDE = "INVALID_SIDE"
    MISSING_FILL_PRICE = "MISSING_FILL_PRICE"
    MISSING_ORDER_NOTIONAL = "MISSING_ORDER_NOTIONAL"
    MISSING_SPREAD_BPS = "MISSING_SPREAD_BPS"
    MISSING_VOLATILITY_ESTIMATE = "MISSING_VOLATILITY_ESTIMATE"


class MaterializationStatus(str, Enum):
    PASS = "PASS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"


@dataclass(frozen=True)
class RejectedRowV0:
    trade_id: str
    reason: RejectionReason


@dataclass(frozen=True)
class MaterializationResultV0:
    status: MaterializationStatus
    rows: tuple[dict[str, Any], ...]
    admissible_count: int
    rejected: tuple[RejectedRowV0, ...]
    materialization_digest: str
    target_provenance_class: str = TARGET_PROVENANCE_CLASS
    target_name: str = TARGET_NAME
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def _stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_inconclusive(value: Any) -> bool:
    return value is None or value == INCONCLUSIVE_SENTINEL


def _side_to_execution_side(side: str) -> str:
    normalized = str(side).strip().lower()
    if normalized == "long":
        return "buy"
    if normalized == "short":
        return "sell"
    raise ValueError(RejectionReason.INVALID_SIDE.value)


def compute_simulated_backtest_slippage_bps(
    *,
    side: str,
    fill_price: float,
    execution_reference_price: float,
) -> float:
    """Canonical side-adjusted slippage formula from execution_reports."""
    if execution_reference_price <= 0:
        raise ValueError(RejectionReason.NONPOSITIVE_REFERENCE_PRICE.value)
    execution_side = _side_to_execution_side(side)
    if execution_side == "buy":
        return (fill_price - execution_reference_price) / execution_reference_price * 10000.0
    return (execution_reference_price - fill_price) / execution_reference_price * 10000.0


def _snapshot_join_key(snapshot: Mapping[str, Any]) -> tuple[str, str]:
    return (str(snapshot.get("instrument_id", "")), str(snapshot.get("bar_timestamp", "")))


def _build_snapshot_index(
    snapshots: Sequence[Mapping[str, Any]],
) -> tuple[dict[tuple[str, str], Mapping[str, Any]], dict[tuple[str, str], int]]:
    index: dict[tuple[str, str], Mapping[str, Any]] = {}
    counts: dict[tuple[str, str], int] = {}
    for snapshot in snapshots:
        key = _snapshot_join_key(snapshot)
        counts[key] = counts.get(key, 0) + 1
        if counts[key] == 1:
            index[key] = snapshot
    return index, counts


def _resolve_snapshot_for_trade(
    *,
    trade: Mapping[str, Any],
    snapshot_index: Mapping[tuple[str, str], Mapping[str, Any]],
    snapshot_counts: Mapping[tuple[str, str], int],
) -> tuple[Mapping[str, Any] | None, RejectionReason | None]:
    inline = trade.get("entry_bar_reference_snapshot")
    if isinstance(inline, Mapping):
        return inline, None

    instrument_id = str(trade.get("instrument_id", ""))
    entry_time = str(trade.get("entry_time", ""))
    if not instrument_id or not entry_time:
        return None, RejectionReason.MISSING_REFERENCE_SNAPSHOT

    key = (instrument_id, entry_time)
    if snapshot_counts.get(key, 0) > 1:
        return None, RejectionReason.DUPLICATE_JOIN_CANDIDATE
    snapshot = snapshot_index.get(key)
    if snapshot is None:
        return None, RejectionReason.MISSING_REFERENCE_SNAPSHOT
    return snapshot, None


def _validate_snapshot_point_in_time(
    *,
    snapshot: Mapping[str, Any],
    entry_time: str,
) -> RejectionReason | None:
    if snapshot.get("is_finalized") is False:
        return RejectionReason.UNFINALIZED_BAR

    feature_time = str(
        snapshot.get("feature_timestamp") or snapshot.get("bar_timestamp") or entry_time
    )
    if feature_time > entry_time:
        return RejectionReason.FEATURE_AFTER_TARGET_TIME
    return None


def _as_positive_float(
    value: Any, *, reason: RejectionReason
) -> tuple[float | None, RejectionReason | None]:
    if _is_inconclusive(value):
        return None, reason
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, reason
    if parsed <= 0:
        return None, RejectionReason.NONPOSITIVE_REFERENCE_PRICE
    return parsed, None


def _as_required_float(
    value: Any, *, reason: RejectionReason
) -> tuple[float | None, RejectionReason | None]:
    if _is_inconclusive(value):
        return None, reason
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, reason


def _materialize_single_row(
    *,
    trade: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, RejectionReason | None]:
    trade_id = str(trade.get("trade_id", ""))
    if not trade_id:
        return None, RejectionReason.MISSING_TRADE_ID

    instrument_id = str(trade.get("instrument_id", ""))
    if not instrument_id:
        return None, RejectionReason.MISSING_INSTRUMENT_ID

    entry_time = str(trade.get("entry_time", ""))
    if not entry_time:
        return None, RejectionReason.MISSING_ENTRY_TIME

    pit_reason = _validate_snapshot_point_in_time(snapshot=snapshot, entry_time=entry_time)
    if pit_reason is not None:
        return None, pit_reason

    execution_reference_price, ref_reason = _as_positive_float(
        snapshot.get("close"),
        reason=RejectionReason.NONPOSITIVE_REFERENCE_PRICE,
    )
    if ref_reason is not None or execution_reference_price is None:
        return None, ref_reason or RejectionReason.NONPOSITIVE_REFERENCE_PRICE

    fill_price, fill_reason = _as_positive_float(
        trade.get("entry_price"),
        reason=RejectionReason.MISSING_FILL_PRICE,
    )
    if fill_reason is not None or fill_price is None:
        return None, fill_reason or RejectionReason.MISSING_FILL_PRICE

    order_notional, notional_reason = _as_positive_float(
        trade.get("notional"),
        reason=RejectionReason.MISSING_ORDER_NOTIONAL,
    )
    if notional_reason is not None or order_notional is None:
        return None, notional_reason or RejectionReason.MISSING_ORDER_NOTIONAL

    side = str(trade.get("side", ""))
    if side in ("", INCONCLUSIVE_SENTINEL):
        return None, RejectionReason.INVALID_SIDE

    spread_bps, spread_reason = _as_required_float(
        snapshot.get("spread_bps"),
        reason=RejectionReason.MISSING_SPREAD_BPS,
    )
    if spread_reason is not None or spread_bps is None:
        return None, spread_reason or RejectionReason.MISSING_SPREAD_BPS

    volatility_estimate, vol_reason = _as_required_float(
        snapshot.get("volatility_estimate"),
        reason=RejectionReason.MISSING_VOLATILITY_ESTIMATE,
    )
    if vol_reason is not None or volatility_estimate is None:
        return None, vol_reason or RejectionReason.MISSING_VOLATILITY_ESTIMATE

    try:
        slippage_bps = compute_simulated_backtest_slippage_bps(
            side=side,
            fill_price=fill_price,
            execution_reference_price=execution_reference_price,
        )
    except ValueError as exc:
        reason_name = str(exc)
        if reason_name in RejectionReason.__members__:
            return None, RejectionReason(reason_name)
        return None, RejectionReason.INVALID_SIDE

    row: dict[str, Any] = {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "side": side,
        "decision_time": entry_time,
        "spread_bps": spread_bps,
        "volatility_estimate": volatility_estimate,
        "order_notional": order_notional,
        "simulated_or_realized_fill_price": fill_price,
        "execution_reference_price": execution_reference_price,
        TARGET_NAME: slippage_bps,
        "target_provenance_class": TARGET_PROVENANCE_CLASS,
        "target_name": TARGET_NAME,
        "reference_price_owner": CANONICAL_REFERENCE_PRICE_OWNER,
    }

    for optional in OPTIONAL_DIAGNOSTIC_FIELDS:
        value = snapshot.get(optional)
        if value is not None and not _is_inconclusive(value):
            row[optional] = value

    return row, None


def materialize_offline_linear_cost_diagnostic_rows_v0(
    *,
    trade_ledger_rows: Sequence[Mapping[str, Any]],
    entry_bar_reference_snapshots: Sequence[Mapping[str, Any]] | None = None,
) -> MaterializationResultV0:
    """Materialize admissible diagnostic rows from ledger rows and bar snapshots."""
    snapshots = list(entry_bar_reference_snapshots or ())
    snapshot_index, snapshot_counts = _build_snapshot_index(snapshots)

    seen_trade_ids: set[str] = set()
    admissible: list[dict[str, Any]] = []
    rejected: list[RejectedRowV0] = []

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
            rejected.append(RejectedRowV0(trade_id="", reason=RejectionReason.MISSING_TRADE_ID))
            continue
        if trade_id in seen_trade_ids:
            rejected.append(
                RejectedRowV0(trade_id=trade_id, reason=RejectionReason.DUPLICATE_TRADE_ID)
            )
            continue
        seen_trade_ids.add(trade_id)

        snapshot, snap_reason = _resolve_snapshot_for_trade(
            trade=trade,
            snapshot_index=snapshot_index,
            snapshot_counts=snapshot_counts,
        )
        if snap_reason is not None or snapshot is None:
            rejected.append(
                RejectedRowV0(
                    trade_id=trade_id,
                    reason=snap_reason or RejectionReason.MISSING_REFERENCE_SNAPSHOT,
                )
            )
            continue

        row, row_reason = _materialize_single_row(trade=trade, snapshot=snapshot)
        if row_reason is not None or row is None:
            rejected.append(
                RejectedRowV0(
                    trade_id=trade_id,
                    reason=row_reason or RejectionReason.TARGET_BINDING_MISSING,
                )
            )
            continue
        admissible.append(row)

    admissible_sorted = sorted(
        admissible,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("decision_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )

    if not admissible_sorted:
        status = (
            MaterializationStatus.TARGET_BINDING_MISSING
            if trade_ledger_rows
            else MaterializationStatus.INSUFFICIENT_DATA
        )
    else:
        status = MaterializationStatus.PASS

    digest = _stable_digest({"rows": admissible_sorted, "schema_version": SCHEMA_VERSION})
    return MaterializationResultV0(
        status=status,
        rows=tuple(admissible_sorted),
        admissible_count=len(admissible_sorted),
        rejected=tuple(rejected),
        materialization_digest=digest,
    )


def serialize_materialized_rows_v0(rows: Sequence[Mapping[str, Any]]) -> str:
    """Deterministic JSONL serialization for repeated materialization checks."""
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("decision_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )
    lines = [json.dumps(row, sort_keys=True, default=str) for row in ordered]
    return "\n".join(lines) + ("\n" if lines else "")


__all__ = [
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "TARGET_NAME",
    "TARGET_PROVENANCE_CLASS",
    "CANONICAL_REFERENCE_PRICE_OWNER",
    "CANONICAL_JOIN_KEY",
    "MaterializationResultV0",
    "MaterializationStatus",
    "RejectionReason",
    "RejectedRowV0",
    "compute_simulated_backtest_slippage_bps",
    "materialize_offline_linear_cost_diagnostic_rows_v0",
    "serialize_materialized_rows_v0",
]
