"""Bounded Futures Testnet venue binding contract (v0).

Offline OKX Europe X-Perp production instrument binding for Package E / INV-033.
No network I/O, credentials, private API, orders, runtime, or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_VENUE_BINDING_CONTRACT_V0=true"
VENUE_BINDING_NETWORK_CALLS_ALLOWED = False
VENUE_BINDING_ORDERS_ALLOWED = False
PROMOTION_ALLOWED = False
RUNTIME_EXECUTED = False

VENUE_OKX_EUROPE = "okx_europe"
ENVIRONMENT_PRODUCTION_METADATA_OFFLINE = "production_metadata_offline_binding"
VALIDATE_ONLY_MODE = "static_schema_binding_only"

REGULATORY_ENTITY_OKX_EUROPE_MARKETS = "OKX Europe Markets Limited"
API_HOST_OKX_EEA = "https://eea.okx.com"

PRODUCTION_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
PRODUCTION_INSTRUMENT_TYPE = "FUTURES"
PRODUCTION_RULE_TYPE = "xperp"
PRODUCTION_UNDERLYING = "ETH"
PRODUCTION_SETTLEMENT_ASSET = "USD"
PRODUCTION_CONTRACT_SIZE_ETH = 0.1
PRODUCTION_TICK_SIZE = 0.01
PRODUCTION_LOT_SIZE = 1.0
PRODUCTION_MIN_ORDER_SIZE = 1.0
PRODUCTION_EXPIRY_DATE = "2031-04-04"

DEMO_REFERENCE_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310328"
DEMO_REFERENCE_INSTRUMENT_TYPE = "FUTURES"
DEMO_REFERENCE_RULE_TYPE = "xperp"
DEMO_REFERENCE_EXPIRY_DATE = "2031-03-28"

VENUE_REPORTED_LEVERAGE_CAPABILITY = 50.0
REGULATORY_MAX_RETAIL_LEVERAGE = 10.0

QUALIFICATION_EVIDENCE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/package_e_e2_inv033_okx_europe_demo_eth_instrument_qualification_"
    "bounded_read_only_no_account_no_runtime_v0_20260626T204649Z"
)
GAP_CLOSURE_EVIDENCE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/package_e_e2_inv033_okx_europe_product_demo_evidence_gap_closure_"
    "bounded_read_only_no_account_no_credentials_no_runtime_v0_20260626T205436Z"
)

OKX_EEA_PUBLIC_ENDPOINT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "/api/v5/public/time",
        "/api/v5/public/instruments",
        "/api/v5/market/ticker",
        "/api/v5/market/tickers",
    }
)

_BITCOIN_INSTRUMENT_FRAGMENTS = frozenset({"BTC", "XBT"})
_SPOT_INSTRUMENT_MARKERS = frozenset({"SPOT"})


@dataclass(frozen=True)
class LeverageSemantics:
    """Separated leverage semantics — venue capability must not raise retail limit."""

    venue_reported_leverage_capability: float
    regulatory_retail_leverage_limit: float
    runtime_leverage: float | None
    runtime_leverage_authorized: bool


@dataclass(frozen=True)
class OkxEuropeXperpInstrumentBinding:
    venue: str
    regulatory_entity: str
    environment: str
    api_host: str
    instrument_id: str
    instrument_type: str
    rule_type: str
    underlying: str
    settlement_asset: str
    contract_size: float
    tick_size: float
    lot_size: float
    minimum_order_size: float
    expiry_date: str
    has_fixed_expiry: bool
    has_funding_mechanism: bool
    is_classic_perpetual_swap: bool
    leverage: LeverageSemantics
    demo_instrument_id: str
    demo_exact_match: bool
    demo_semantic_family_match: bool
    demo_metadata_parity: bool
    source_evidence_bundle: str
    gap_closure_evidence_bundle: str
    source_manifest_verified: bool
    validate_only_mode: str
    order_attempt_count: int
    network_call_count: int
    private_api_call_count: int
    runtime_executed: bool
    promotion_allowed: bool


def default_okx_europe_xperp_production_binding(
    *,
    source_manifest_verified: bool = True,
) -> OkxEuropeXperpInstrumentBinding:
    """Canonical offline production-metadata binding from qualification evidence."""
    return OkxEuropeXperpInstrumentBinding(
        venue=VENUE_OKX_EUROPE,
        regulatory_entity=REGULATORY_ENTITY_OKX_EUROPE_MARKETS,
        environment=ENVIRONMENT_PRODUCTION_METADATA_OFFLINE,
        api_host=API_HOST_OKX_EEA,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        instrument_type=PRODUCTION_INSTRUMENT_TYPE,
        rule_type=PRODUCTION_RULE_TYPE,
        underlying=PRODUCTION_UNDERLYING,
        settlement_asset=PRODUCTION_SETTLEMENT_ASSET,
        contract_size=PRODUCTION_CONTRACT_SIZE_ETH,
        tick_size=PRODUCTION_TICK_SIZE,
        lot_size=PRODUCTION_LOT_SIZE,
        minimum_order_size=PRODUCTION_MIN_ORDER_SIZE,
        expiry_date=PRODUCTION_EXPIRY_DATE,
        has_fixed_expiry=True,
        has_funding_mechanism=True,
        is_classic_perpetual_swap=False,
        leverage=LeverageSemantics(
            venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
            regulatory_retail_leverage_limit=REGULATORY_MAX_RETAIL_LEVERAGE,
            runtime_leverage=None,
            runtime_leverage_authorized=False,
        ),
        demo_instrument_id=DEMO_REFERENCE_INSTRUMENT_ID,
        demo_exact_match=False,
        demo_semantic_family_match=True,
        demo_metadata_parity=False,
        source_evidence_bundle=QUALIFICATION_EVIDENCE_BUNDLE,
        gap_closure_evidence_bundle=GAP_CLOSURE_EVIDENCE_BUNDLE,
        source_manifest_verified=source_manifest_verified,
        validate_only_mode=VALIDATE_ONLY_MODE,
        order_attempt_count=0,
        network_call_count=0,
        private_api_call_count=0,
        runtime_executed=False,
        promotion_allowed=False,
    )


def venue_capability_exceeds_retail_limit(leverage: LeverageSemantics) -> bool:
    """True when venue-reported capability exceeds the regulatory retail ceiling."""
    return leverage.venue_reported_leverage_capability > leverage.regulatory_retail_leverage_limit


def effective_operational_leverage_cap(leverage: LeverageSemantics) -> float:
    """Fail-closed operative cap: min(regulatory retail, venue capability) when runtime unset."""
    if leverage.runtime_leverage_authorized and leverage.runtime_leverage is not None:
        return min(
            leverage.runtime_leverage,
            leverage.regulatory_retail_leverage_limit,
            leverage.venue_reported_leverage_capability,
        )
    return min(
        leverage.regulatory_retail_leverage_limit,
        leverage.venue_reported_leverage_capability,
    )


def _parse_expiry_date(expiry: str) -> date | None:
    try:
        parts = expiry.split("-")
        if len(parts) != 3:
            return None
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (TypeError, ValueError):
        return None


def _instrument_contains_bitcoin_direction(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    return any(fragment in upper for fragment in _BITCOIN_INSTRUMENT_FRAGMENTS)


def evaluate_okx_europe_xperp_binding(
    binding: OkxEuropeXperpInstrumentBinding,
) -> dict[str, Any]:
    """Fail-closed offline binding evaluation."""
    result: dict[str, Any] = {
        "venue_binding_pass": False,
        "production_demo_separation_pass": False,
        "leverage_semantics_pass": False,
        "static_validate_only_pass": False,
        "xperp_semantics_pass": False,
        "evidence_binding_pass": False,
        "offline_inert_pass": False,
        "fail_reasons": [],
    }
    fail = result["fail_reasons"]

    if binding.venue != VENUE_OKX_EUROPE:
        fail.append(f"venue must be {VENUE_OKX_EUROPE!r}")
    if binding.environment != ENVIRONMENT_PRODUCTION_METADATA_OFFLINE:
        fail.append(f"environment must be {ENVIRONMENT_PRODUCTION_METADATA_OFFLINE!r}")
    if binding.instrument_id != PRODUCTION_INSTRUMENT_ID:
        fail.append(f"instrument_id must be {PRODUCTION_INSTRUMENT_ID!r}")
    if binding.instrument_type != PRODUCTION_INSTRUMENT_TYPE:
        fail.append(f"instrument_type must be {PRODUCTION_INSTRUMENT_TYPE!r}")
    if binding.instrument_type == "SWAP":
        fail.append("SWAP instrument_type forbidden for X-Perp binding")
    if not binding.rule_type:
        fail.append("rule_type required")
    elif binding.rule_type != PRODUCTION_RULE_TYPE:
        fail.append(f"rule_type must be {PRODUCTION_RULE_TYPE!r}")
    if binding.underlying != PRODUCTION_UNDERLYING:
        fail.append(f"underlying must be {PRODUCTION_UNDERLYING!r}")
    if binding.settlement_asset != PRODUCTION_SETTLEMENT_ASSET:
        fail.append(f"settlement_asset must be {PRODUCTION_SETTLEMENT_ASSET!r}")
    if not binding.has_fixed_expiry:
        fail.append("has_fixed_expiry must be true")
    if _parse_expiry_date(binding.expiry_date) is None:
        fail.append("expiry_date must be present and parseable")
    if binding.is_classic_perpetual_swap:
        fail.append("is_classic_perpetual_swap must be false")
    if _instrument_contains_bitcoin_direction(binding.instrument_id):
        fail.append("bitcoin-direction instrument forbidden")
    if binding.instrument_type in _SPOT_INSTRUMENT_MARKERS:
        fail.append("spot instrument forbidden")

    if binding.demo_exact_match is not False:
        fail.append("demo_exact_match must be false")
    if binding.demo_semantic_family_match is not True:
        fail.append("demo_semantic_family_match must be true")
    if binding.demo_metadata_parity is not False:
        fail.append("demo_metadata_parity must be false")
    if binding.instrument_id == binding.demo_instrument_id:
        fail.append("production instrument_id must not equal demo_instrument_id")
    if binding.demo_instrument_id == PRODUCTION_INSTRUMENT_ID:
        fail.append("demo_instrument_id must not be used as production binding")

    lev = binding.leverage
    if lev.regulatory_retail_leverage_limit != REGULATORY_MAX_RETAIL_LEVERAGE:
        fail.append(f"regulatory_retail_leverage_limit must be {REGULATORY_MAX_RETAIL_LEVERAGE!r}")
    if lev.runtime_leverage is not None:
        fail.append("runtime_leverage must be unset for offline binding")
    if lev.runtime_leverage_authorized:
        fail.append("runtime_leverage_authorized must be false")

    if binding.validate_only_mode != VALIDATE_ONLY_MODE:
        fail.append(f"validate_only_mode must be {VALIDATE_ONLY_MODE!r}")
    if binding.order_attempt_count != 0:
        fail.append("order_attempt_count must be 0")
    if binding.network_call_count != 0:
        fail.append("network_call_count must be 0")
    if binding.private_api_call_count != 0:
        fail.append("private_api_call_count must be 0")
    if binding.runtime_executed:
        fail.append("runtime_executed must be false")
    if binding.promotion_allowed:
        fail.append("promotion_allowed must be false")
    if not binding.source_manifest_verified:
        fail.append("source_manifest_verified must be true")
    if not binding.source_evidence_bundle:
        fail.append("source_evidence_bundle required")
    if not binding.gap_closure_evidence_bundle:
        fail.append("gap_closure_evidence_bundle required")

    result["production_demo_separation_pass"] = not any(
        "demo" in r or "production instrument_id" in r for r in fail
    )
    result["leverage_semantics_pass"] = not any("leverage" in r for r in fail)
    result["static_validate_only_pass"] = not any(
        r for r in fail if "validate_only" in r or "order_attempt" in r or "network_call" in r
    )
    result["xperp_semantics_pass"] = not any(
        r for r in fail if "SWAP" in r or "perpetual" in r or "rule_type" in r or "expiry" in r
    )
    result["evidence_binding_pass"] = not any("evidence" in r or "manifest" in r for r in fail)
    result["offline_inert_pass"] = not any(
        r for r in fail if "runtime" in r or "promotion" in r or "private_api" in r
    )
    result["venue_binding_pass"] = not fail
    return result


def offline_adapter_capability_descriptor(
    binding: OkxEuropeXperpInstrumentBinding,
) -> dict[str, Any]:
    """Inert adapter capability metadata for later network adapter implementation."""
    evaluation = evaluate_okx_europe_xperp_binding(binding)
    return {
        "adapter_kind": "offline_capability_descriptor_only",
        "venue": binding.venue,
        "api_host": binding.api_host,
        "instrument_id": binding.instrument_id,
        "instrument_type": binding.instrument_type,
        "rule_type": binding.rule_type,
        "public_endpoint_allowlist": sorted(OKX_EEA_PUBLIC_ENDPOINT_ALLOWLIST),
        "network_calls_allowed": VENUE_BINDING_NETWORK_CALLS_ALLOWED,
        "orders_allowed": VENUE_BINDING_ORDERS_ALLOWED,
        "validate_only_mode": binding.validate_only_mode,
        "effective_operational_leverage_cap": effective_operational_leverage_cap(binding.leverage),
        "venue_binding_pass": evaluation["venue_binding_pass"],
        "futures_session_authorized_now": FUTURES_SESSION_AUTHORIZED_NOW,
    }


def assert_venue_binding_inert() -> None:
    if FUTURES_SESSION_AUTHORIZED_NOW:
        raise RuntimeError("FUTURES_SESSION_AUTHORIZED_NOW must remain false")
    if VENUE_BINDING_NETWORK_CALLS_ALLOWED:
        raise RuntimeError("VENUE_BINDING_NETWORK_CALLS_ALLOWED must remain false")
    if VENUE_BINDING_ORDERS_ALLOWED:
        raise RuntimeError("VENUE_BINDING_ORDERS_ALLOWED must remain false")
