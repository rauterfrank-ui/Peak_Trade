"""Static + offline OKX Europe X-Perp venue binding contract (v0).

Package E / INV-033 offline production instrument binding. No network, credentials, orders, runtime.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    DEMO_REFERENCE_INSTRUMENT_ID,
    ENVIRONMENT_PRODUCTION_METADATA_OFFLINE,
    LeverageSemantics,
    OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
    OkxEuropeXperpInstrumentBinding,
    PACKAGE_MARKER,
    PRODUCTION_EXPIRY_DATE,
    PRODUCTION_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_TYPE,
    PRODUCTION_RULE_TYPE,
    PROMOTION_ALLOWED,
    REGULATORY_MAX_RETAIL_LEVERAGE,
    RUNTIME_EXECUTED,
    VALIDATE_ONLY_MODE,
    VENUE_BINDING_NETWORK_CALLS_ALLOWED,
    VENUE_BINDING_ORDERS_ALLOWED,
    VENUE_OKX_EUROPE,
    VENUE_REPORTED_LEVERAGE_CAPABILITY,
    default_okx_europe_xperp_production_binding,
    effective_operational_leverage_cap,
    evaluate_okx_europe_xperp_binding,
    offline_adapter_capability_descriptor,
    venue_capability_exceeds_retail_limit,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

REPO_ROOT = Path(__file__).resolve().parents[2]
VENUE_BINDING_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_venue_binding_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OKX_EEA_XPERP_BINDING_CONTRACT_GUARD_V0=true"


def _binding(**overrides: object) -> OkxEuropeXperpInstrumentBinding:
    base = default_okx_europe_xperp_production_binding()
    if not overrides:
        return base
    return replace(base, **overrides)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert PACKAGE_MARKER in VENUE_BINDING_MODULE.read_text(encoding="utf-8")


def test_okx_europe_adapter_lifecycle_contract_version_binding() -> None:
    assert OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION == "okx_europe_adapter_lifecycle.v0"
    assert "OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION" in VENUE_BINDING_MODULE.read_text(
        encoding="utf-8"
    )


def test_global_inert_flags_remain_false() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert VENUE_BINDING_NETWORK_CALLS_ALLOWED is False
    assert VENUE_BINDING_ORDERS_ALLOWED is False
    assert PROMOTION_ALLOWED is False
    assert RUNTIME_EXECUTED is False


def test_default_production_xperp_binding_passes() -> None:
    binding = default_okx_europe_xperp_production_binding()
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["venue_binding_pass"] is True
    assert result["fail_reasons"] == []
    assert binding.instrument_id == PRODUCTION_INSTRUMENT_ID
    assert binding.instrument_type == PRODUCTION_INSTRUMENT_TYPE
    assert binding.rule_type == PRODUCTION_RULE_TYPE
    assert binding.has_fixed_expiry is True
    assert binding.has_funding_mechanism is True
    assert binding.is_classic_perpetual_swap is False


def test_funding_plus_fixed_expiry_accepted() -> None:
    binding = default_okx_europe_xperp_production_binding()
    assert binding.expiry_date == PRODUCTION_EXPIRY_DATE
    assert binding.has_funding_mechanism is True
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["xperp_semantics_pass"] is True


def test_static_validate_only_zero_order_attempts() -> None:
    binding = default_okx_europe_xperp_production_binding()
    assert binding.validate_only_mode == VALIDATE_ONLY_MODE
    assert binding.order_attempt_count == 0
    assert binding.network_call_count == 0
    assert binding.private_api_call_count == 0
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["static_validate_only_pass"] is True


def test_semantic_demo_reference_without_exact_match() -> None:
    binding = default_okx_europe_xperp_production_binding()
    assert binding.demo_instrument_id == DEMO_REFERENCE_INSTRUMENT_ID
    assert binding.demo_exact_match is False
    assert binding.demo_semantic_family_match is True
    assert binding.demo_metadata_parity is False
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["production_demo_separation_pass"] is True


def test_venue_capability_50_does_not_raise_retail_limit_10() -> None:
    leverage = LeverageSemantics(
        venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
        regulatory_retail_leverage_limit=REGULATORY_MAX_RETAIL_LEVERAGE,
        runtime_leverage=None,
        runtime_leverage_authorized=False,
    )
    assert venue_capability_exceeds_retail_limit(leverage) is True
    assert effective_operational_leverage_cap(leverage) == REGULATORY_MAX_RETAIL_LEVERAGE
    assert effective_operational_leverage_cap(leverage) != VENUE_REPORTED_LEVERAGE_CAPABILITY


def test_offline_adapter_capability_descriptor_inert() -> None:
    binding = default_okx_europe_xperp_production_binding()
    descriptor = offline_adapter_capability_descriptor(binding)
    assert descriptor["adapter_kind"] == "offline_capability_descriptor_only"
    assert descriptor["network_calls_allowed"] is False
    assert descriptor["orders_allowed"] is False
    assert descriptor["effective_operational_leverage_cap"] == REGULATORY_MAX_RETAIL_LEVERAGE
    assert descriptor["venue_binding_pass"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("instrument_id", DEMO_REFERENCE_INSTRUMENT_ID),
        ("demo_instrument_id", PRODUCTION_INSTRUMENT_ID),
        ("demo_exact_match", True),
        ("instrument_type", "SWAP"),
        ("rule_type", ""),
        ("rule_type", "normal"),
        ("expiry_date", ""),
        ("has_fixed_expiry", False),
        ("is_classic_perpetual_swap", True),
        ("instrument_id", "BTC-USD_UM_XPERP-310404"),
        ("instrument_id", "ETH/EUR"),
        ("source_manifest_verified", False),
        ("order_attempt_count", 1),
        ("network_call_count", 1),
        ("private_api_call_count", 1),
        ("runtime_executed", True),
        ("promotion_allowed", True),
        ("environment", "demo"),
        ("venue", "kraken"),
    ],
)
def test_negative_binding_variants_fail(field: str, value: object) -> None:
    binding = _binding(**{field: value})
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["venue_binding_pass"] is False
    assert result["fail_reasons"]


def test_runtime_leverage_set_fails() -> None:
    binding = _binding(
        leverage=LeverageSemantics(
            venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
            regulatory_retail_leverage_limit=REGULATORY_MAX_RETAIL_LEVERAGE,
            runtime_leverage=5.0,
            runtime_leverage_authorized=False,
        )
    )
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["venue_binding_pass"] is False


def test_runtime_leverage_authorized_fails() -> None:
    binding = _binding(
        leverage=LeverageSemantics(
            venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
            regulatory_retail_leverage_limit=REGULATORY_MAX_RETAIL_LEVERAGE,
            runtime_leverage=None,
            runtime_leverage_authorized=True,
        )
    )
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["venue_binding_pass"] is False


def test_retail_limit_cannot_be_set_to_venue_capability() -> None:
    binding = _binding(
        leverage=LeverageSemantics(
            venue_reported_leverage_capability=VENUE_REPORTED_LEVERAGE_CAPABILITY,
            regulatory_retail_leverage_limit=VENUE_REPORTED_LEVERAGE_CAPABILITY,
            runtime_leverage=None,
            runtime_leverage_authorized=False,
        )
    )
    result = evaluate_okx_europe_xperp_binding(binding)
    assert result["venue_binding_pass"] is False
    assert any("regulatory_retail_leverage_limit" in r for r in result["fail_reasons"])


def test_environment_must_be_production_metadata_offline() -> None:
    binding = _binding(environment=ENVIRONMENT_PRODUCTION_METADATA_OFFLINE)
    assert evaluate_okx_europe_xperp_binding(binding)["venue_binding_pass"] is True
    bad = _binding(environment="production_runtime")
    assert evaluate_okx_europe_xperp_binding(bad)["venue_binding_pass"] is False
