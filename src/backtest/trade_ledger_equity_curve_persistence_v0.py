"""Canonical trade ledger, equity curve, and drawdown persistence v0 (offline contract).

Reuses engine trade records and stats/equity owners. No new formula owners, runtime rewire,
or economic evaluation semantics.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.backtest.economic_observability_snapshot_v1 import (
    MetricMaterializationStatus,
    serialize_canonical_json,
)

SCHEMA_VERSION = "canonical_trade_ledger.v0"
TRADE_LEDGER_OWNER = "backtest.trade_ledger_equity_curve_persistence_v0"
EQUITY_CURVE_OWNER = "backtest.trade_ledger_equity_curve_persistence_v0"
DRAWDOWN_CURVE_OWNER = "backtest.trade_ledger_equity_curve_persistence_v0"
TRADE_RECORD_SOURCE = "backtest.engine:Trade"

RECONCILIATION_TOLERANCE = 1e-9

CANONICAL_TRADE_LEDGER_FIELDS: tuple[str, ...] = (
    "trade_id",
    "instrument_id",
    "side",
    "entry_time",
    "exit_time",
    "holding_time",
    "entry_price",
    "exit_price",
    "entry_notional",
    "exit_notional",
    "gross_pnl",
    "net_pnl",
    "fees",
    "slippage",
    "funding",
    "exit_reason",
    "entry_reason",
    "regime",
    "strategy_ref",
    "decision_ref",
    "risk_ref",
    "sizing_ref",
    "cost_ref",
)


class PersistenceContractError(ValueError):
    """Raised when persistence contract validation fails."""


class DrawdownCurveStatus(str, Enum):
    COMPUTED = "COMPUTED"
    RECONSTRUCTED = "RECONSTRUCTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_MISSING = "SOURCE_MISSING"


@dataclass(frozen=True)
class FieldValueV0:
    value: Any
    status: MetricMaterializationStatus
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class TradeLedgerRowV0:
    fields: dict[str, FieldValueV0]

    def to_dict(self) -> dict[str, Any]:
        return {name: field_value.to_dict() for name, field_value in sorted(self.fields.items())}

    def resolved_values(self) -> dict[str, Any]:
        return {
            name: field_value.value
            for name, field_value in self.fields.items()
            if field_value.status
            in {
                MetricMaterializationStatus.COMPUTED,
                MetricMaterializationStatus.RECONSTRUCTED,
            }
        }


@dataclass(frozen=True)
class TradeLedgerReconciliationV0:
    row_count: int
    canonical_trade_count: int
    trade_count_reconciliation_pass: bool
    gross_pnl_reconciliation_pass: bool
    net_pnl_reconciliation_pass: bool
    total_cost_reconciliation_pass: bool
    gross_pnl_ledger_sum: float
    net_pnl_ledger_sum: float
    costs_ledger_sum: float
    snapshot_gross_pnl: float
    snapshot_net_pnl: float
    snapshot_total_cost: float
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EquityCurvePersistenceV0:
    owner: str
    point_count: int
    final_value: float
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DrawdownCurvePersistenceV0:
    owner: str
    status: DrawdownCurveStatus
    reason_codes: tuple[str, ...]
    point_count: int
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ObservabilityPersistenceArtifactsV0:
    trade_ledger_rows: tuple[TradeLedgerRowV0, ...]
    equity_curve: EquityCurvePersistenceV0
    drawdown_curve: DrawdownCurvePersistenceV0
    reconciliation: TradeLedgerReconciliationV0


def _computed(value: Any) -> FieldValueV0:
    return FieldValueV0(value=value, status=MetricMaterializationStatus.COMPUTED)


def _source_missing(reason: str) -> FieldValueV0:
    return FieldValueV0(
        value=None,
        status=MetricMaterializationStatus.SOURCE_MISSING,
        reason_codes=(reason,),
    )


def _side_from_size(size: float) -> FieldValueV0:
    if size > 0:
        return _computed("long")
    if size < 0:
        return _computed("short")
    return _source_missing("TRADE_SIZE_ZERO_OR_MISSING")


def _iso_timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _finite_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _field_from_numeric(value: Any, *, reason: str) -> FieldValueV0:
    resolved = _finite_float(value)
    if resolved is None:
        return _source_missing(reason)
    return _computed(resolved)


def _holding_time_seconds(entry_time: Any, exit_time: Any) -> FieldValueV0:
    if entry_time is None or exit_time is None:
        return _source_missing("ENTRY_OR_EXIT_TIME_MISSING")
    try:
        delta = pd.Timestamp(exit_time) - pd.Timestamp(entry_time)
        return _computed(float(delta.total_seconds()))
    except (TypeError, ValueError):
        return _source_missing("HOLDING_TIME_NOT_DETERMINISTIC")


def _fees_from_trade(trade: Mapping[str, Any]) -> FieldValueV0:
    entry_cost = _finite_float(trade.get("entry_cost"))
    exit_cost = _finite_float(trade.get("exit_cost"))
    if entry_cost is None and exit_cost is None:
        if "fee" in trade and trade.get("fee") is not None:
            fee = _finite_float(trade.get("fee"))
            if fee is not None:
                return _computed(fee)
        return _source_missing("FEE_FIELDS_NOT_PRESENT")
    total = float(entry_cost or 0.0) + float(exit_cost or 0.0)
    return _computed(total)


def _optional_string_field(trade: Mapping[str, Any], key: str, *, reason: str) -> FieldValueV0:
    raw = trade.get(key)
    if raw is None or raw == "":
        return _source_missing(reason)
    return _computed(str(raw))


def materialize_trade_ledger_row_v0(
    trade: Mapping[str, Any],
    *,
    trade_index: int,
    instrument_id: str,
    run_id: str,
    strategy_ref: Optional[str] = None,
) -> TradeLedgerRowV0:
    """Materialize one canonical trade ledger row from an existing engine trade record."""
    size = _finite_float(trade.get("size"))
    entry_price = trade.get("entry_price")
    exit_price = trade.get("exit_price")
    entry_time = trade.get("entry_time")
    exit_time = trade.get("exit_time")

    entry_notional: FieldValueV0
    if size is not None and _finite_float(entry_price) is not None:
        entry_notional = _computed(abs(size) * float(entry_price))
    else:
        entry_notional = _source_missing("ENTRY_NOTIONAL_INPUTS_MISSING")

    exit_notional: FieldValueV0
    if size is not None and _finite_float(exit_price) is not None:
        exit_notional = _computed(abs(size) * float(exit_price))
    else:
        exit_notional = _source_missing("EXIT_NOTIONAL_INPUTS_MISSING")

    trade_id_raw = trade.get("trade_id")
    if trade_id_raw is not None and str(trade_id_raw).strip():
        trade_id = _computed(str(trade_id_raw))
    else:
        trade_id = _computed(f"{run_id}-trade-{trade_index}")

    fields: dict[str, FieldValueV0] = {
        "trade_id": trade_id,
        "instrument_id": _computed(instrument_id),
        "side": _side_from_size(size)
        if size is not None
        else _source_missing("TRADE_SIZE_MISSING"),
        "entry_time": (
            _computed(_iso_timestamp(entry_time))
            if entry_time is not None
            else _source_missing("ENTRY_TIME_MISSING")
        ),
        "exit_time": (
            _computed(_iso_timestamp(exit_time))
            if exit_time is not None
            else _source_missing("EXIT_TIME_MISSING")
        ),
        "holding_time": _holding_time_seconds(entry_time, exit_time),
        "entry_price": _field_from_numeric(entry_price, reason="ENTRY_PRICE_MISSING"),
        "exit_price": _field_from_numeric(exit_price, reason="EXIT_PRICE_MISSING"),
        "entry_notional": entry_notional,
        "exit_notional": exit_notional,
        "gross_pnl": _field_from_numeric(trade.get("gross_pnl"), reason="GROSS_PNL_MISSING"),
        "net_pnl": _field_from_numeric(
            trade.get("pnl", trade.get("net_pnl")),
            reason="NET_PNL_MISSING",
        ),
        "fees": _fees_from_trade(trade),
        "slippage": _source_missing("SLIPPAGE_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "funding": _source_missing("FUNDING_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "exit_reason": _optional_string_field(trade, "exit_reason", reason="EXIT_REASON_MISSING"),
        "entry_reason": _source_missing("ENTRY_REASON_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "regime": _source_missing("REGIME_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "strategy_ref": (
            _computed(strategy_ref)
            if strategy_ref
            else _source_missing("STRATEGY_REF_NOT_PROVIDED")
        ),
        "decision_ref": _source_missing("DECISION_REF_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "risk_ref": _source_missing("RISK_REF_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "sizing_ref": _source_missing("SIZING_REF_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
        "cost_ref": _source_missing("COST_REF_NOT_BOUND_IN_ENGINE_TRADE_RECORD"),
    }
    return TradeLedgerRowV0(fields=fields)


def materialize_trade_ledger_rows_v0(
    trades: Sequence[Mapping[str, Any]],
    *,
    instrument_id: str,
    run_id: str,
    strategy_ref: Optional[str] = None,
) -> tuple[TradeLedgerRowV0, ...]:
    return tuple(
        materialize_trade_ledger_row_v0(
            trade,
            trade_index=index,
            instrument_id=instrument_id,
            run_id=run_id,
            strategy_ref=strategy_ref,
        )
        for index, trade in enumerate(trades)
    )


def materialize_equity_curve_rows_v0(
    equity_curve: pd.Series,
) -> tuple[dict[str, Any], ...]:
    if equity_curve is None or equity_curve.empty:
        return ()
    rows: list[dict[str, Any]] = []
    for timestamp, equity in equity_curve.items():
        rows.append(
            {
                "timestamp": _iso_timestamp(timestamp),
                "equity": float(equity),
            }
        )
    return tuple(rows)


def _reconstruct_drawdown_from_equity(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve - running_max


def materialize_drawdown_curve_v0(
    *,
    equity_curve: pd.Series,
    drawdown_curve: Optional[pd.Series] = None,
) -> DrawdownCurvePersistenceV0:
    if equity_curve is None or equity_curve.empty:
        return DrawdownCurvePersistenceV0(
            owner=DRAWDOWN_CURVE_OWNER,
            status=DrawdownCurveStatus.SOURCE_MISSING,
            reason_codes=("EQUITY_CURVE_EMPTY",),
            point_count=0,
            rows=(),
        )

    if drawdown_curve is not None and not drawdown_curve.empty:
        if len(drawdown_curve) != len(equity_curve):
            return DrawdownCurvePersistenceV0(
                owner=DRAWDOWN_CURVE_OWNER,
                status=DrawdownCurveStatus.SOURCE_MISSING,
                reason_codes=("DRAWDOWN_EQUITY_LENGTH_MISMATCH",),
                point_count=0,
                rows=(),
            )
        status = DrawdownCurveStatus.COMPUTED
        reason_codes: tuple[str, ...] = ()
        series = drawdown_curve
    else:
        status = DrawdownCurveStatus.RECONSTRUCTED
        reason_codes = ("DRAWDOWN_RECONSTRUCTED_FROM_EQUITY_CURVE",)
        series = _reconstruct_drawdown_from_equity(equity_curve)

    rows: list[dict[str, Any]] = []
    for timestamp, drawdown in series.items():
        rows.append(
            {
                "timestamp": _iso_timestamp(timestamp),
                "drawdown": float(drawdown),
            }
        )
    return DrawdownCurvePersistenceV0(
        owner=DRAWDOWN_CURVE_OWNER,
        status=DrawdownCurveStatus(status.value),
        reason_codes=reason_codes,
        point_count=len(rows),
        rows=tuple(rows),
    )


def _sum_ledger_numeric(rows: Sequence[TradeLedgerRowV0], field: str) -> float:
    total = 0.0
    for row in rows:
        field_value = row.fields[field]
        if field_value.status not in {
            MetricMaterializationStatus.COMPUTED,
            MetricMaterializationStatus.RECONSTRUCTED,
        }:
            continue
        numeric = _finite_float(field_value.value)
        if numeric is not None:
            total += numeric
    return total


def validate_trade_ledger_reconciliation_v0(
    *,
    rows: Sequence[TradeLedgerRowV0],
    canonical_trade_count: int,
    snapshot_gross_pnl: float,
    snapshot_net_pnl: float,
    snapshot_total_cost: float,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> TradeLedgerReconciliationV0:
    row_count = len(rows)
    gross_sum = _sum_ledger_numeric(rows, "gross_pnl")
    net_sum = _sum_ledger_numeric(rows, "net_pnl")
    cost_sum = _sum_ledger_numeric(rows, "fees")

    trade_count_pass = row_count == int(canonical_trade_count)
    gross_pass = abs(gross_sum - snapshot_gross_pnl) <= tolerance * max(
        1.0, abs(snapshot_gross_pnl)
    )
    net_pass = abs(net_sum - snapshot_net_pnl) <= tolerance * max(1.0, abs(snapshot_net_pnl))
    cost_pass = abs(cost_sum - snapshot_total_cost) <= tolerance * max(
        1.0, abs(snapshot_total_cost)
    )

    reason_codes: list[str] = []
    if not trade_count_pass:
        reason_codes.append("TRADE_COUNT_MISMATCH")
    if not gross_pass:
        reason_codes.append("GROSS_PNL_MISMATCH")
    if not net_pass:
        reason_codes.append("NET_PNL_MISMATCH")
    if not cost_pass:
        reason_codes.append("TOTAL_COST_MISMATCH")

    reconciliation = TradeLedgerReconciliationV0(
        row_count=row_count,
        canonical_trade_count=int(canonical_trade_count),
        trade_count_reconciliation_pass=trade_count_pass,
        gross_pnl_reconciliation_pass=gross_pass,
        net_pnl_reconciliation_pass=net_pass,
        total_cost_reconciliation_pass=cost_pass,
        gross_pnl_ledger_sum=gross_sum,
        net_pnl_ledger_sum=net_sum,
        costs_ledger_sum=cost_sum,
        snapshot_gross_pnl=snapshot_gross_pnl,
        snapshot_net_pnl=snapshot_net_pnl,
        snapshot_total_cost=snapshot_total_cost,
        reason_codes=tuple(reason_codes),
    )
    if reason_codes:
        raise PersistenceContractError(
            "trade_ledger_reconciliation_failed:" + ":".join(reason_codes)
        )
    return reconciliation


def validate_equity_final_value_reconciliation_v0(
    *,
    equity_curve: EquityCurvePersistenceV0,
    final_equity: float,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> bool:
    if equity_curve.point_count == 0:
        raise PersistenceContractError("equity_curve_empty")
    if abs(equity_curve.final_value - final_equity) > tolerance * max(1.0, abs(final_equity)):
        raise PersistenceContractError(
            f"equity_final_value_mismatch:curve={equity_curve.final_value}:final={final_equity}"
        )
    return True


def validate_drawdown_reconciliation_v0(
    *,
    equity_curve: pd.Series,
    drawdown: DrawdownCurvePersistenceV0,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> bool:
    if drawdown.status in {DrawdownCurveStatus.NOT_APPLICABLE, DrawdownCurveStatus.SOURCE_MISSING}:
        return True
    if drawdown.point_count != len(equity_curve):
        raise PersistenceContractError("drawdown_point_count_mismatch")
    if drawdown.status is DrawdownCurveStatus.RECONSTRUCTED:
        expected = _reconstruct_drawdown_from_equity(equity_curve)
        for idx, timestamp in enumerate(equity_curve.index):
            expected_value = float(expected.iloc[idx])
            actual_value = float(drawdown.rows[idx]["drawdown"])
            if abs(expected_value - actual_value) > tolerance:
                raise PersistenceContractError("drawdown_reconstruction_mismatch")
            if _iso_timestamp(timestamp) != drawdown.rows[idx]["timestamp"]:
                raise PersistenceContractError("drawdown_timestamp_mismatch")
    return True


def serialize_trade_ledger_jsonl(rows: Sequence[TradeLedgerRowV0]) -> str:
    lines = [serialize_canonical_json(row.to_dict()) for row in rows]
    return "\n".join(lines) + ("\n" if lines else "")


def serialize_equity_curve_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["timestamp", "equity"])
    writer.writeheader()
    for row in rows:
        writer.writerow({"timestamp": row["timestamp"], "equity": row["equity"]})
    return buffer.getvalue()


def serialize_drawdown_curve_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["timestamp", "drawdown"])
    writer.writeheader()
    for row in rows:
        writer.writerow({"timestamp": row["timestamp"], "drawdown": row["drawdown"]})
    return buffer.getvalue()


def compute_bundle_file_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class CanonicalObservabilityBundleV0:
    snapshot_payload: dict[str, Any]
    registry_payload: dict[str, Any]
    trade_ledger_jsonl: str
    equity_curve_csv: str
    drawdown_curve_csv: str
    drawdown_not_applicable_payload: Optional[dict[str, Any]]
    decision_funnel_payload: dict[str, Any]
    data_quality_payload: dict[str, Any]
    provenance_payload: dict[str, Any]
    reconciliation_payload: dict[str, Any]
    final_report: str
    advanced_capability_payloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    bundle_digest: str = field(default="", init=False)

    def artifact_payloads(self) -> dict[str, str | dict[str, Any]]:
        artifacts: dict[str, str | dict[str, Any]] = {
            "OBSERVABILITY_SNAPSHOT.json": self.snapshot_payload,
            "METRIC_REGISTRY_SNAPSHOT.json": self.registry_payload,
            "TRADE_LEDGER.jsonl": self.trade_ledger_jsonl,
            "EQUITY_CURVE.csv": self.equity_curve_csv,
            "DECISION_FUNNEL.json": self.decision_funnel_payload,
            "DATA_QUALITY.json": self.data_quality_payload,
            "PROVENANCE.json": self.provenance_payload,
            "reconciliation_matrix.json": self.reconciliation_payload,
            "final_report.txt": self.final_report,
        }
        if self.drawdown_not_applicable_payload is not None:
            artifacts["DRAWDOWN_CURVE.not_applicable.json"] = self.drawdown_not_applicable_payload
        else:
            artifacts["DRAWDOWN_CURVE.csv"] = self.drawdown_curve_csv
        artifacts.update(self.advanced_capability_payloads)
        return artifacts

    def compute_digest(self) -> str:
        canonical_parts = []
        for name in sorted(self.artifact_payloads()):
            payload = self.artifact_payloads()[name]
            if isinstance(payload, dict):
                canonical_parts.append(serialize_canonical_json(payload))
            else:
                canonical_parts.append(str(payload))
        digest = hashlib.sha256("\n".join(canonical_parts).encode("utf-8")).hexdigest()
        self.bundle_digest = digest
        return digest


def write_observability_bundle_v0(bundle: CanonicalObservabilityBundleV0, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in bundle.artifact_payloads().items():
        path = output_dir / name
        if isinstance(payload, dict):
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            path.write_text(str(payload), encoding="utf-8")
