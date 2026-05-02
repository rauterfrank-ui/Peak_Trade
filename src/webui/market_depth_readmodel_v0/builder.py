"""Pure fixture-backed Market Depth / Orderbook readmodel v0.

Safety boundary:
- read-only JSON-native readmodel builder
- explicit bundle_root only; no /tmp default
- no provider/network/GitHub calls
- no live placement or brokerage session handles
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

READMODEL_ID = "market_depth_readmodel.v0"
DEFAULT_STALE_REASON = "offline_bundle_scan"


class MarketDepthReadmodelError(ValueError):
    """Raised when a depth fixture cannot be converted into the v0 readmodel."""


@dataclass(frozen=True)
class DepthLevel:
    price: Decimal
    size: Decimal

    @property
    def notional(self) -> Decimal:
        return self.price * self.size

    def to_json_dict(self) -> dict[str, str]:
        return {
            "price": _decimal_to_str(self.price),
            "size": _decimal_to_str(self.size),
            "notional": _decimal_to_str(self.notional),
        }


@dataclass(frozen=True)
class MarketDepthReadmodel:
    readmodel_id: str
    symbol: str
    source: str
    limit: int
    generated_at_iso: str
    runtime_source_status: str
    stale: bool
    stale_reason: str
    bids: tuple[DepthLevel, ...]
    asks: tuple[DepthLevel, ...]

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
            "depth": {
                "bids": [level.to_json_dict() for level in self.bids],
                "asks": [level.to_json_dict() for level in self.asks],
                "levels_returned": {
                    "bids": len(self.bids),
                    "asks": len(self.asks),
                },
                "level_limit": self.limit,
            },
        }


def build_market_depth_readmodel_v0(
    *,
    bundle_root: str | Path,
    limit: int | None = None,
    generated_at_iso: str | None = None,
) -> MarketDepthReadmodel:
    """Build a JSON-native readmodel from an explicit local fixture bundle."""

    root = Path(bundle_root)
    if not root.exists() or not root.is_dir():
        raise MarketDepthReadmodelError(f"bundle_root does not exist or is not a directory: {root}")

    payload_path = root / "depth.json"
    if not payload_path.exists():
        raise MarketDepthReadmodelError(f"missing depth fixture: {payload_path}")

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarketDepthReadmodelError(f"malformed depth fixture JSON: {payload_path}") from exc

    if not isinstance(payload, dict):
        raise MarketDepthReadmodelError("depth fixture root must be an object")

    symbol = _required_str(payload, "symbol")
    source = _required_str(payload, "source")
    requested_limit = _resolve_limit(payload=payload, explicit_limit=limit)

    bids = _parse_levels(payload.get("bids"), side="bids")
    asks = _parse_levels(payload.get("asks"), side="asks")

    bids = tuple(sorted(bids, key=lambda level: level.price, reverse=True)[:requested_limit])
    asks = tuple(sorted(asks, key=lambda level: level.price)[:requested_limit])

    return MarketDepthReadmodel(
        readmodel_id=READMODEL_ID,
        symbol=symbol,
        source=source,
        limit=requested_limit,
        generated_at_iso=generated_at_iso or _utc_now_iso(),
        runtime_source_status="offline_bundle",
        stale=True,
        stale_reason=DEFAULT_STALE_REASON,
        bids=bids,
        asks=asks,
    )


def to_json_dict(readmodel: MarketDepthReadmodel) -> dict[str, Any]:
    return readmodel.to_json_dict()


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MarketDepthReadmodelError(f"missing or invalid string field: {key}")
    return value


def _resolve_limit(*, payload: dict[str, Any], explicit_limit: int | None) -> int:
    raw = explicit_limit if explicit_limit is not None else payload.get("limit", 10)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
        raise MarketDepthReadmodelError("limit must be a positive integer")
    return raw


def _parse_levels(raw: Any, *, side: str) -> list[DepthLevel]:
    if not isinstance(raw, list):
        raise MarketDepthReadmodelError(f"{side} must be a list")

    levels: list[DepthLevel] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise MarketDepthReadmodelError(f"{side}[{idx}] must be an object")

        price = _decimal_field(item, "price", side=side, idx=idx)
        size = _decimal_field(item, "size", side=side, idx=idx)

        if price <= 0:
            raise MarketDepthReadmodelError(f"{side}[{idx}].price must be positive")
        if size <= 0:
            raise MarketDepthReadmodelError(f"{side}[{idx}].size must be positive")

        levels.append(DepthLevel(price=price, size=size))

    return levels


def _decimal_field(item: dict[str, Any], key: str, *, side: str, idx: int) -> Decimal:
    raw_val = item.get(key)
    if isinstance(raw_val, bool) or raw_val is None:
        raise MarketDepthReadmodelError(f"{side}[{idx}].{key} must be decimal-like")
    try:
        return Decimal(str(raw_val))
    except (InvalidOperation, ValueError) as exc:
        raise MarketDepthReadmodelError(f"{side}[{idx}].{key} must be decimal-like") from exc


def _decimal_to_str(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
