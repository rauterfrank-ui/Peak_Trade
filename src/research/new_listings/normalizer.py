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
