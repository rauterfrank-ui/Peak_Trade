"""Repo-native bounded Futures Testnet adapter binding contract (v0).

Offline contract for futures testnet adapter surface: instrument, endpoint allowlist,
margin/leverage, and spot isolation. No network I/O, no credentials, no orders.
Does not authorize Futures Testnet execute; FUTURES_SESSION_AUTHORIZED_NOW remains false.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    DEFAULT_MARGIN_MODE,
    DEFAULT_MARKET_TYPE,
    DEFAULT_MAX_LEVERAGE,
    DEFAULT_POSITION_MODE,
    FUTURES_SESSION_AUTHORIZED_NOW,
    SPOT_KRAKEN_ENDPOINT_PREFIXES,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_CONTRACT_V0=true"
ADAPTER_NETWORK_CALLS_ALLOWED = False
FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN = False

# Contract-default testnet futures host (planning placeholder; not live spot Kraken).
DEFAULT_FUTURES_TESTNET_NETWORK_HOST = "https://demo-futures.kraken.com"

# Futures REST paths — separate from spot SPOT_KRAKEN_ENDPOINT_PREFIXES.
FUTURES_TESTNET_ENDPOINT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "/derivatives/api/v3/tickers",
        "/derivatives/api/v3/instruments",
        "/derivatives/api/v3/accounts",
        "/derivatives/api/v3/openpositions",
        "/derivatives/api/v3/openorders",
        "/derivatives/api/v3/sendorder",
        "/derivatives/api/v3/cancelorder",
        "/derivatives/api/v3/cancelallorders",
    }
)

LIVE_FUTURES_HOST_PREFIXES: frozenset[str] = frozenset(
    {
        "https://futures.kraken.com",
        "https://api.kraken.com",
    }
)


@dataclass(frozen=True)
class BoundedFuturesTestnetAdapterBinding:
    adapter_id: str
    instrument: str
    market_type: str
    margin_mode: str
    max_leverage: float
    position_mode: str
    network_host: str
    endpoint_allowlist: frozenset[str]
    reduce_only_supported: bool
    testnet_scoped: bool
    order_side_semantics: str


def default_offline_adapter_binding() -> BoundedFuturesTestnetAdapterBinding:
    """Contract-default binding for offline planning; exchange proof remains false."""
    return BoundedFuturesTestnetAdapterBinding(
        adapter_id="offline_bounded_futures_testnet_adapter_v0",
        instrument=DEFAULT_INSTRUMENT,
        market_type=DEFAULT_MARKET_TYPE,
        margin_mode=DEFAULT_MARGIN_MODE,
        max_leverage=DEFAULT_MAX_LEVERAGE,
        position_mode=DEFAULT_POSITION_MODE,
        network_host=DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
        endpoint_allowlist=FUTURES_TESTNET_ENDPOINT_ALLOWLIST,
        reduce_only_supported=True,
        testnet_scoped=True,
        order_side_semantics="long",
    )


def validate_futures_testnet_adapter_binding(
    binding: BoundedFuturesTestnetAdapterBinding,
    *,
    endpoints_called: list[str] | None = None,
) -> dict[str, Any]:
    """Fail-closed adapter binding validation (offline, no I/O)."""
    result: dict[str, Any] = {
        "adapter_binding_pass": False,
        "futures_endpoint_allowlist_pass": False,
        "spot_endpoint_isolation_pass": False,
        "margin_leverage_pass": False,
        "instrument_binding_pass": False,
        "fail_reasons": [],
    }

    if not binding.adapter_id:
        result["fail_reasons"].append("adapter_id required")
    if binding.market_type != DEFAULT_MARKET_TYPE:
        result["fail_reasons"].append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not binding.instrument:
        result["fail_reasons"].append("instrument required")
    if binding.margin_mode != DEFAULT_MARGIN_MODE:
        result["fail_reasons"].append(f"margin_mode must be {DEFAULT_MARGIN_MODE!r}")
    if binding.margin_mode == "cross":
        result["fail_reasons"].append("cross margin not allowed unless explicitly governed")
    if binding.max_leverage > DEFAULT_MAX_LEVERAGE:
        result["fail_reasons"].append("max_leverage exceeds contract cap")
    if binding.position_mode != DEFAULT_POSITION_MODE:
        result["fail_reasons"].append(f"position_mode must be {DEFAULT_POSITION_MODE!r}")
    if binding.order_side_semantics not in ("long", "short", "long_or_short_bounded"):
        result["fail_reasons"].append("order_side_semantics must be long/short bounded")
    if not binding.reduce_only_supported:
        result["fail_reasons"].append("reduce_only_supported must be true")
    if not binding.testnet_scoped:
        result["fail_reasons"].append("testnet_scoped must be true")

    host = binding.network_host.strip().rstrip("/")
    if any(host.startswith(prefix) for prefix in LIVE_FUTURES_HOST_PREFIXES):
        result["fail_reasons"].append(
            "live or spot Kraken host not allowed for bounded futures testnet"
        )
    if host == "https://api.kraken.com":
        result["fail_reasons"].append("spot kraken.com host forbidden for futures bounded adapter")

    if not binding.endpoint_allowlist:
        result["fail_reasons"].append("endpoint_allowlist must be non-empty")
    elif not binding.endpoint_allowlist.issubset(FUTURES_TESTNET_ENDPOINT_ALLOWLIST):
        result["fail_reasons"].append("endpoint_allowlist contains paths outside futures allowlist")

    endpoints = endpoints_called or []
    for ep in endpoints:
        if ep in SPOT_KRAKEN_ENDPOINT_PREFIXES:
            result["fail_reasons"].append(f"spot endpoint not allowed: {ep}")
        if ep not in FUTURES_TESTNET_ENDPOINT_ALLOWLIST:
            result["fail_reasons"].append(f"endpoint not on futures testnet allowlist: {ep}")

    result["instrument_binding_pass"] = bool(binding.instrument)
    result["spot_endpoint_isolation_pass"] = not any(
        "spot endpoint" in r for r in result["fail_reasons"]
    )
    result["futures_endpoint_allowlist_pass"] = (
        binding.endpoint_allowlist.issubset(FUTURES_TESTNET_ENDPOINT_ALLOWLIST)
        and result["spot_endpoint_isolation_pass"]
        and not any("endpoint not on" in r for r in result["fail_reasons"])
        and not any("endpoint_allowlist contains" in r for r in result["fail_reasons"])
    )
    result["margin_leverage_pass"] = (
        binding.margin_mode == DEFAULT_MARGIN_MODE and binding.max_leverage <= DEFAULT_MAX_LEVERAGE
    )
    result["adapter_binding_pass"] = not result["fail_reasons"]
    return result


def assert_futures_session_not_authorized() -> None:
    """Defense-in-depth: module must not flip session authorization."""
    if FUTURES_SESSION_AUTHORIZED_NOW:
        raise RuntimeError("FUTURES_SESSION_AUTHORIZED_NOW must remain false")
