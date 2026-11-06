"""Stable provenance IDs and digests for bridge hardening v2."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _canonical_json(
    payload: Mapping[str, Any] | list[Any] | str | int | float | bool | None,
) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(material: str | bytes) -> str:
    if isinstance(material, str):
        material = material.encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def digest_mapping(payload: Mapping[str, Any]) -> str:
    return sha256_hex(_canonical_json(dict(payload)))


def make_scoped_id(prefix: str, *parts: Any) -> str:
    body = sha256_hex("|".join(str(p) for p in parts))[:24]
    return f"{prefix}_{body}"


def portfolio_state_hash(snapshot: Mapping[str, Any]) -> str:
    state = snapshot.get("state") if isinstance(snapshot, Mapping) else None
    if not isinstance(state, Mapping):
        state = snapshot
    return digest_mapping(dict(state))


def build_config_bundle_digest(
    *,
    feature_config_version: str,
    regime_config_version: str,
    price_basis_contract_version: str,
    fee_rate_bps: str,
    slippage_bps: str,
    initial_equity: str,
    feature_window_min: int,
) -> str:
    return digest_mapping(
        {
            "feature_config_version": feature_config_version,
            "regime_config_version": regime_config_version,
            "price_basis_contract_version": price_basis_contract_version,
            "fee_rate_bps": fee_rate_bps,
            "slippage_bps": slippage_bps,
            "initial_equity": initial_equity,
            "feature_window_min": int(feature_window_min),
        }
    )
