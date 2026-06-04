"""Static + offline bounded Futures Testnet adapter binding contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_testnet_execute_harness_adapter_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    ADAPTER_NETWORK_CALLS_ALLOWED,
    BoundedFuturesTestnetAdapterBinding,
    DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
    FUTURES_TESTNET_ENDPOINT_ALLOWLIST,
    FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN,
    PACKAGE_MARKER,
    SPOT_KRAKEN_ENDPOINT_PREFIXES,
    default_offline_adapter_binding,
    validate_futures_testnet_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_contract_v0.py"
FUTURES_CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_contract_v0.py"
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_ADAPTER_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_BUNDLE_SUFFIX = (
    "futures_specific_bounded_testnet_readiness_charter_no_run_v0_20260604T125147Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in ADAPTER_MODULE.read_text(encoding="utf-8")


def test_futures_session_and_network_not_authorized() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert ADAPTER_NETWORK_CALLS_ALLOWED is False
    assert FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN is False


def test_default_binding_passes_offline_validation() -> None:
    binding = default_offline_adapter_binding()
    result = validate_futures_testnet_adapter_binding(binding)
    assert result["adapter_binding_pass"] is True
    assert result["fail_reasons"] == []


def test_spot_endpoint_in_endpoints_called_fails() -> None:
    binding = default_offline_adapter_binding()
    spot_ep = next(iter(SPOT_KRAKEN_ENDPOINT_PREFIXES))
    result = validate_futures_testnet_adapter_binding(binding, endpoints_called=[spot_ep])
    assert result["adapter_binding_pass"] is False
    assert result["spot_endpoint_isolation_pass"] is False


def test_live_kraken_host_fails() -> None:
    binding = default_offline_adapter_binding()
    bad = BoundedFuturesTestnetAdapterBinding(
        adapter_id=binding.adapter_id,
        instrument=binding.instrument,
        market_type=binding.market_type,
        margin_mode=binding.margin_mode,
        max_leverage=binding.max_leverage,
        position_mode=binding.position_mode,
        network_host="https://api.kraken.com",
        endpoint_allowlist=binding.endpoint_allowlist,
        reduce_only_supported=binding.reduce_only_supported,
        testnet_scoped=binding.testnet_scoped,
        order_side_semantics=binding.order_side_semantics,
    )
    result = validate_futures_testnet_adapter_binding(bad)
    assert result["adapter_binding_pass"] is False


def test_cross_margin_fails() -> None:
    binding = default_offline_adapter_binding()
    bad = BoundedFuturesTestnetAdapterBinding(
        adapter_id=binding.adapter_id,
        instrument=binding.instrument,
        market_type=binding.market_type,
        margin_mode="cross",
        max_leverage=binding.max_leverage,
        position_mode=binding.position_mode,
        network_host=binding.network_host,
        endpoint_allowlist=binding.endpoint_allowlist,
        reduce_only_supported=binding.reduce_only_supported,
        testnet_scoped=binding.testnet_scoped,
        order_side_semantics=binding.order_side_semantics,
    )
    result = validate_futures_testnet_adapter_binding(bad)
    assert result["adapter_binding_pass"] is False


def test_futures_contract_module_crosslink() -> None:
    assert FUTURES_CONTRACT_MODULE.is_file()
    assert "SPOT_KRAKEN_ENDPOINT_PREFIXES" in ADAPTER_MODULE.read_text(encoding="utf-8")


def test_section5_pe9_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_contract_v0" in section5
    assert "bounded_futures_testnet_harness_contract_v0" in section5


def test_endpoint_allowlist_non_empty_and_testnet_host() -> None:
    assert len(FUTURES_TESTNET_ENDPOINT_ALLOWLIST) >= 5
    assert DEFAULT_FUTURES_TESTNET_NETWORK_HOST.startswith("https://")
    assert "demo-futures" in DEFAULT_FUTURES_TESTNET_NETWORK_HOST


def test_charter_bundle_suffix_documented_in_test() -> None:
    assert CHARTER_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")
