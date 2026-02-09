from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from .db import upsert_asset


@dataclass(frozen=True)
class NormalizedAsset:
    asset_id: str
    symbol: str | None
    name: str | None
    chain: str | None
    contract_address: str | None
    decimals: int | None
    first_seen_at: str
    sources: list[str]
    tags: dict[str, Any]


@dataclass(frozen=True)
class SnapshotOverrides:
    """Optional price/volume from ticker for market_snapshots (best-effort)."""

    price: float | None
    volume_24h_usd: float | None


def derive_asset_id(payload: Mapping[str, Any]) -> str:
    # P3: offline seed derivation; later phases use venue-specific canonicalization
    sym = str(payload.get("symbol") or payload.get("note") or "UNKNOWN").upper()
    chain = str(payload.get("chain") or "seedchain")
    return f"{chain}:{sym}"


def normalize_seed_payload(
    payload: Mapping[str, Any], *, source: str, observed_at: str
) -> NormalizedAsset:
    asset_id = derive_asset_id(payload)
    symbol = str(payload.get("symbol") or "SEED").upper()
    chain = str(payload.get("chain") or "seedchain")
    name = payload.get("name")
    contract_address = payload.get("contract_address")
    decimals = payload.get("decimals")
    if isinstance(decimals, bool):
        decimals = None
    if decimals is not None:
        decimals = int(decimals)
    tags: dict[str, Any] = {"p3": True, "seed": True}
    # preserve minimal provenance
    tags["raw_payload"] = json.loads(json.dumps(payload))  # ensure JSON-serializable copy
    return NormalizedAsset(
        asset_id=asset_id,
        symbol=symbol,
        name=name if isinstance(name, str) else None,
        chain=chain,
        contract_address=(contract_address if isinstance(contract_address, str) else None),
        decimals=decimals,
        first_seen_at=observed_at,
        sources=[source],
        tags=tags,
    )


def _parse_ccxt_symbol(symbol: str) -> tuple[str, str]:
    """Parse CCXT symbol (e.g. 'BTC/EUR') into (base, quote). Fallback: (symbol, '')."""
    if not isinstance(symbol, str) or "/" not in symbol:
        return (str(symbol or "UNKNOWN").upper(), "")
    parts = symbol.strip().split("/", 1)
    return (parts[0].strip().upper(), parts[1].strip().upper())


def _derive_cex_asset_id(exchange: str, base: str) -> str:
    """Canonical asset_id for CEX ticker: cex:{exchange}:{base} (one per base per exchange)."""
    return f"cex:{exchange}:{base}"


def _extract_ccxt_snapshot_overrides(payload: Mapping[str, Any]) -> SnapshotOverrides:
    """Best-effort price and volume_24h_usd from payload (top-level last/quoteVolume or nested ticker)."""
    ticker = payload.get("ticker") if isinstance(payload.get("ticker"), dict) else {}
    last = payload.get("last") if payload.get("last") is not None else ticker.get("last")
    quote_volume = payload.get("quoteVolume")
    volume = ticker.get("volume")
    symbol = payload.get("symbol") or ""
    _, quote = _parse_ccxt_symbol(symbol)

    price: float | None = None
    if last is not None and isinstance(last, (int, float)):
        price = float(last)

    volume_24h_usd: float | None = None
    if quote_volume is not None and isinstance(quote_volume, (int, float)):
        try:
            volume_24h_usd = float(quote_volume)
        except (TypeError, ValueError):
            volume_24h_usd = None
    elif quote in ("USD", "USDT", "BUSD", "DAI") and last is not None and volume is not None:
        try:
            volume_24h_usd = float(volume) * float(last)
        except (TypeError, ValueError):
            volume_24h_usd = None

    return SnapshotOverrides(price=price, volume_24h_usd=volume_24h_usd)


def normalize_ccxt_ticker_payload(
    payload: Mapping[str, Any], *, source: str, observed_at: str
) -> tuple[NormalizedAsset, SnapshotOverrides]:
    """
    Normalize CCXT ticker payload (or replay with ccxt-shaped payload) into canonical asset
    and snapshot overrides (price, volume_24h_usd best-effort).
    """
    exchange = str(payload.get("exchange") or "unknown").lower()
    symbol = str(payload.get("symbol") or "")
    base, quote = _parse_ccxt_symbol(symbol)
    asset_id = _derive_cex_asset_id(exchange, base)

    ticker = payload.get("ticker") if isinstance(payload.get("ticker"), dict) else {}
    name = ticker.get("symbol") or (f"{base}/{quote}" if quote else base)

    tags: dict[str, Any] = {
        "p9": True,
        "ccxt": True,
        "exchange": exchange,
        "quote": quote or None,
        "raw_payload": json.loads(json.dumps(dict(payload))),
    }

    asset = NormalizedAsset(
        asset_id=asset_id,
        symbol=f"{base}/{quote}" if quote else base,
        name=name if isinstance(name, str) else None,
        chain="cex",
        contract_address=None,
        decimals=None,
        first_seen_at=observed_at,
        sources=[source],
        tags=tags,
    )
    overrides = _extract_ccxt_snapshot_overrides(payload)
    return (asset, overrides)


def persist_asset(con, a: NormalizedAsset) -> None:
    upsert_asset(
        con,
        asset_id=a.asset_id,
        symbol=a.symbol,
        name=a.name,
        chain=a.chain,
        contract_address=a.contract_address,
        decimals=a.decimals,
        first_seen_at=a.first_seen_at,
        sources=a.sources,
        tags=a.tags,
    )
