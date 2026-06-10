"""Pure fixture-backed Market Trades / Tape readmodel v0.

Safety boundary:
- read-only JSON-native readmodel builder
- explicit bundle_root only; no /tmp default
- no provider/network calls
- no fill/order/position truth semantics
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

READMODEL_ID = "market_tape_readmodel.v0"
DEFAULT_STALE_REASON = "offline_bundle_scan"

AUTHORITY_BOUNDARY: dict[str, bool] = {
    "non_authorizing": True,
    "provider_truth_blocked": True,
    "dashboard_truth_blocked": True,
    "trading_readiness_blocked": True,
    "selected_future_truth_blocked": True,
    "order_fill_position_truth_blocked": True,
    "slippage_liquidity_depth_truth_blocked": True,
    "signal_strategy_readiness_blocked": True,
}

FORBIDDEN_TRADE_FIELDS = frozenset(
    {
        "order_id",
        "client_order_id",
        "fill_id",
        "position",
        "pnl",
        "leverage",
        "approval",
        "approved",
        "live_authorized",
        "strategy_activation",
        "execute",
        "execution",
        "slippage",
        "liquidity",
        "depth",
        "fills",
        "fills_count",
    }
)


class MarketTapeReadmodelError(ValueError):
    """Raised when a tape fixture cannot be converted into the v0 readmodel."""


@dataclass(frozen=True)
class TapeTrade:
    trade_id: str | None
    sequence: int
    price: Decimal
    size: Decimal
    side: str
    timestamp_iso: str

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "sequence": self.sequence,
            "price": _decimal_to_str(self.price),
            "size": _decimal_to_str(self.size),
            "side": self.side,
            "timestamp_iso": self.timestamp_iso,
        }
        if self.trade_id is not None:
            payload["trade_id"] = self.trade_id
        return payload


@dataclass(frozen=True)
class MarketTapeReadmodel:
    readmodel_id: str
    symbol: str
    source: str
    limit: int
    generated_at_iso: str
    runtime_source_status: str
    stale: bool
    stale_reason: str
    trades: tuple[TapeTrade, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "readmodel_id": self.readmodel_id,
            "symbol": self.symbol,
            "source": self.source,
            "limit": self.limit,
            "generated_at_iso": self.generated_at_iso,
            "runtime_source_status": self.runtime_source_status,
            "stale": self.stale,
            "stale_reason": self.stale_reason,
            **AUTHORITY_BOUNDARY,
            "tape": {
                "trades": [trade.to_json_dict() for trade in self.trades],
                "trades_returned": len(self.trades),
                "trade_limit": self.limit,
            },
        }


def build_market_tape_readmodel_v0(
    *,
    bundle_root: str | Path,
    limit: int | None = None,
    generated_at_iso: str | None = None,
) -> MarketTapeReadmodel:
    """Build a JSON-native tape readmodel from an explicit local fixture bundle."""

    root = Path(bundle_root)
    if not root.exists() or not root.is_dir():
        raise MarketTapeReadmodelError(f"bundle_root does not exist or is not a directory: {root}")

    payload_path = root / "tape.json"
    if not payload_path.exists():
        raise MarketTapeReadmodelError(f"missing tape fixture: {payload_path}")

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarketTapeReadmodelError(f"malformed tape fixture JSON: {payload_path}") from exc

    if not isinstance(payload, dict):
        raise MarketTapeReadmodelError("tape fixture root must be an object")

    symbol = _required_str(payload, "symbol")
    source = _required_str(payload, "source")
    requested_limit = _resolve_limit(payload=payload, explicit_limit=limit)

    trades = _parse_trades(payload.get("trades"))
    trades = tuple(sorted(trades, key=lambda trade: trade.sequence, reverse=True)[:requested_limit])

    return MarketTapeReadmodel(
        readmodel_id=READMODEL_ID,
        symbol=symbol,
        source=source,
        limit=requested_limit,
        generated_at_iso=generated_at_iso or _utc_now_iso(),
        runtime_source_status="offline_bundle",
        stale=True,
        stale_reason=DEFAULT_STALE_REASON,
        trades=trades,
    )


def to_json_dict(readmodel: MarketTapeReadmodel) -> dict[str, Any]:
    return readmodel.to_json_dict()


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MarketTapeReadmodelError(f"missing or invalid string field: {key}")
    return value


def _resolve_limit(*, payload: dict[str, Any], explicit_limit: int | None) -> int:
    raw = explicit_limit if explicit_limit is not None else payload.get("limit", 50)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
        raise MarketTapeReadmodelError("limit must be a positive integer")
    return raw


def _parse_trades(raw: Any) -> list[TapeTrade]:
    if not isinstance(raw, list):
        raise MarketTapeReadmodelError("trades must be a list")

    trades: list[TapeTrade] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise MarketTapeReadmodelError(f"trades[{idx}] must be an object")

        forbidden = sorted(FORBIDDEN_TRADE_FIELDS.intersection(item))
        if forbidden:
            raise MarketTapeReadmodelError(
                f"trades[{idx}] contains forbidden fields: {', '.join(forbidden)}"
            )

        sequence = _int_field(item, "sequence", idx=idx)
        price = _decimal_field(item, "price", idx=idx)
        size = _decimal_field(item, "size", idx=idx)
        side = _required_trade_str(item, "side", idx=idx)
        timestamp_iso = _required_trade_str(item, "timestamp_iso", idx=idx)

        if price <= 0:
            raise MarketTapeReadmodelError(f"trades[{idx}].price must be positive")
        if size <= 0:
            raise MarketTapeReadmodelError(f"trades[{idx}].size must be positive")

        trade_id_raw = item.get("trade_id")
        trade_id: str | None = None
        if trade_id_raw is not None:
            if not isinstance(trade_id_raw, str) or not trade_id_raw.strip():
                raise MarketTapeReadmodelError(f"trades[{idx}].trade_id must be a non-empty string")
            trade_id = trade_id_raw

        trades.append(
            TapeTrade(
                trade_id=trade_id,
                sequence=sequence,
                price=price,
                size=size,
                side=side,
                timestamp_iso=timestamp_iso,
            )
        )

    return trades


def _required_trade_str(item: dict[str, Any], key: str, *, idx: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MarketTapeReadmodelError(f"trades[{idx}].{key} must be a non-empty string")
    return value


def _int_field(item: dict[str, Any], key: str, *, idx: int) -> int:
    value = item.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise MarketTapeReadmodelError(f"trades[{idx}].{key} must be an integer")
    return value


def _decimal_field(item: dict[str, Any], key: str, *, idx: int) -> Decimal:
    raw_val = item.get(key)
    if isinstance(raw_val, bool) or raw_val is None:
        raise MarketTapeReadmodelError(f"trades[{idx}].{key} must be decimal-like")
    try:
        return Decimal(str(raw_val))
    except (InvalidOperation, ValueError) as exc:
        raise MarketTapeReadmodelError(f"trades[{idx}].{key} must be decimal-like") from exc


def _decimal_to_str(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
