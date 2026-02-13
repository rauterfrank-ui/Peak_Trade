"""P33 — Backtest report artifacts v1 (serialization + schema)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, List, Mapping, Union

Json = Union[None, bool, int, float, str, List["Json"], Dict[str, "Json"]]


class ArtifactSchemaError(ValueError):
    pass


SCHEMA_VERSION_V1 = 1


def _is_json_scalar(x: Any) -> bool:
    return x is None or isinstance(x, (bool, int, float, str))


def _ensure_jsonable(x: Any, path: str) -> Json:
    if _is_json_scalar(x):
        return x  # type: ignore[return-value]
    if isinstance(x, list):
        return [_ensure_jsonable(v, f"{path}[]") for v in x]
    if isinstance(x, dict):
        out: Dict[str, Json] = {}
        for k, v in x.items():
            if not isinstance(k, str):
                raise ArtifactSchemaError(f"Non-string key at {path}: {k!r}")
            out[k] = _ensure_jsonable(v, f"{path}.{k}")
        return out
    raise ArtifactSchemaError(f"Non-JSONable type at {path}: {type(x).__name__}")


def _require_keys(d: Mapping[str, Any], keys: List[str], where: str) -> None:
    missing = [k for k in keys if k not in d]
    if missing:
        raise ArtifactSchemaError(f"Missing keys at {where}: {missing}")


def _floatify(x: Any, where: str) -> float:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    raise ArtifactSchemaError(f"Expected number at {where}, got {x!r}")


def _intify(x: Any, where: str) -> int:
    if isinstance(x, int) and not isinstance(x, bool):
        return x
    raise ArtifactSchemaError(f"Expected int at {where}, got {x!r}")


def _strify(x: Any, where: str) -> str:
    if isinstance(x, str):
        return x
    raise ArtifactSchemaError(f"Expected str at {where}, got {x!r}")


def _map_float(x: Any, where: str) -> Dict[str, float]:
    if not isinstance(x, dict):
        raise ArtifactSchemaError(f"Expected dict at {where}, got {type(x).__name__}")
    out: Dict[str, float] = {}
    for k, v in x.items():
        if not isinstance(k, str):
            raise ArtifactSchemaError(f"Non-string key at {where}: {k!r}")
        out[k] = _floatify(v, f"{where}.{k}")
    return out


@dataclass(frozen=True)
class FillRecordDTO:
    order_id: str
    side: str
    qty: float
    price: float
    fee: float
    symbol: str

    @classmethod
    def from_any(cls, x: Any) -> "FillRecordDTO":
        if isinstance(x, dict):
            _require_keys(x, ["order_id", "side", "qty", "price", "fee", "symbol"], "fills[]")
            return cls(
                order_id=_strify(x["order_id"], "fills[].order_id"),
                side=_strify(x["side"], "fills[].side"),
                qty=_floatify(x["qty"], "fills[].qty"),
                price=_floatify(x["price"], "fills[].price"),
                fee=_floatify(x["fee"], "fills[].fee"),
                symbol=_strify(x["symbol"], "fills[].symbol"),
            )
        try:
            return cls(
                order_id=_strify(getattr(x, "order_id"), "fills[].order_id"),
                side=_strify(getattr(x, "side"), "fills[].side"),
                qty=_floatify(getattr(x, "qty"), "fills[].qty"),
                price=_floatify(getattr(x, "price"), "fills[].price"),
                fee=_floatify(getattr(x, "fee"), "fills[].fee"),
                symbol=_strify(getattr(x, "symbol"), "fills[].symbol"),
            )
        except Exception as e:  # noqa: BLE001
            raise ArtifactSchemaError(f"Cannot convert fill record: {x!r}") from e


@dataclass(frozen=True)
class PositionCashStateV2DTO:
    cash: float
    positions_qty: Dict[str, float]
    avg_cost: Dict[str, float]
    realized_pnl: float

    @classmethod
    def from_any(cls, x: Any) -> "PositionCashStateV2DTO":
        if isinstance(x, dict):
            _require_keys(x, ["cash", "positions_qty", "avg_cost", "realized_pnl"], "state")
            return cls(
                cash=_floatify(x["cash"], "state.cash"),
                positions_qty=_map_float(x["positions_qty"], "state.positions_qty"),
                avg_cost=_map_float(x["avg_cost"], "state.avg_cost"),
                realized_pnl=_floatify(x["realized_pnl"], "state.realized_pnl"),
            )
        if is_dataclass(x):
            return cls.from_any(asdict(x))
        try:
            return cls(
                cash=_floatify(getattr(x, "cash"), "state.cash"),
                positions_qty=_map_float(getattr(x, "positions_qty"), "state.positions_qty"),
                avg_cost=_map_float(getattr(x, "avg_cost"), "state.avg_cost"),
                realized_pnl=_floatify(getattr(x, "realized_pnl"), "state.realized_pnl"),
            )
        except Exception as e:  # noqa: BLE001
            raise ArtifactSchemaError(f"Cannot convert state: {x!r}") from e


@dataclass(frozen=True)
class BacktestReportV1DTO:
    schema_version: int
    fills: List[FillRecordDTO]
    state: PositionCashStateV2DTO
    equity: List[float]
    metrics: Dict[str, float]

    @classmethod
    def from_any_report(cls, report: Any) -> "BacktestReportV1DTO":
        fills = [FillRecordDTO.from_any(f) for f in getattr(report, "fills")]
        state = PositionCashStateV2DTO.from_any(getattr(report, "state"))
        equity_raw = list(getattr(report, "equity"))
        equity = [_floatify(v, f"equity[{i}]") for i, v in enumerate(equity_raw)]
        metrics = _map_float(dict(getattr(report, "metrics")), "metrics")
        return cls(
            schema_version=SCHEMA_VERSION_V1,
            fills=fills,
            state=state,
            equity=equity,
            metrics=metrics,
        )

    def to_dict(self) -> Dict[str, Json]:
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "fills": [asdict(f) for f in self.fills],
            "state": asdict(self.state),
            "equity": list(self.equity),
            "metrics": dict(self.metrics),
        }
        return _ensure_jsonable(d, "report")  # type: ignore[return-value]

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "BacktestReportV1DTO":
        _require_keys(d, ["schema_version", "fills", "state", "equity", "metrics"], "report")
        sv = _intify(d["schema_version"], "report.schema_version")
        if sv != SCHEMA_VERSION_V1:
            raise ArtifactSchemaError(
                f"Unsupported schema_version: {sv} (expected {SCHEMA_VERSION_V1})"
            )
        fills_raw = d["fills"]
        if not isinstance(fills_raw, list):
            raise ArtifactSchemaError("report.fills must be a list")
        fills = [FillRecordDTO.from_any(x) for x in fills_raw]
        state = PositionCashStateV2DTO.from_any(d["state"])
        equity_raw = d["equity"]
        if not isinstance(equity_raw, list):
            raise ArtifactSchemaError("report.equity must be a list")
        equity = [_floatify(v, f"report.equity[{i}]") for i, v in enumerate(equity_raw)]
        metrics = _map_float(d["metrics"], "report.metrics")
        return cls(schema_version=sv, fills=fills, state=state, equity=equity, metrics=metrics)


def report_to_dict(report: Any) -> Dict[str, Json]:
    dto = BacktestReportV1DTO.from_any_report(report)
    return dto.to_dict()


def report_from_dict(d: Mapping[str, Any]) -> BacktestReportV1DTO:
    return BacktestReportV1DTO.from_dict(d)
