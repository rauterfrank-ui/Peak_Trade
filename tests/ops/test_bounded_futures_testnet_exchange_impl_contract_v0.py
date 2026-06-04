"""Static + offline bounded Futures Testnet exchange impl contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_runtime_harness_exchange_impl_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.exchange.bounded_futures_testnet_exchange_impl_contract_v0 import (
    EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW,
    EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED,
    BoundedFuturesTestnetExchangeImplDescriptor,
    BoundedFuturesTestnetExchangeImplStub,
    PACKAGE_MARKER,
    default_offline_exchange_impl_descriptor,
    validate_futures_testnet_exchange_impl_descriptor,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCHANGE_IMPL_MODULE = (
    REPO_ROOT / "src" / "exchange" / "bounded_futures_testnet_exchange_impl_contract_v0.py"
)
ADAPTER_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_contract_v0.py"
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_REFRESH_SUFFIX = (
    "futures_specific_bounded_testnet_readiness_charter_refresh_no_run_v0_20260604T132452Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in EXCHANGE_IMPL_MODULE.read_text(encoding="utf-8")


def test_exchange_impl_not_authorized() -> None:
    assert EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED is False
    assert EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW is False
    assert FUTURES_SESSION_AUTHORIZED_NOW is False


def test_default_descriptor_passes() -> None:
    descriptor = default_offline_exchange_impl_descriptor()
    result = validate_futures_testnet_exchange_impl_descriptor(descriptor)
    assert result["exchange_impl_contract_pass"] is True
    assert result["fail_reasons"] == []


def test_network_calls_allowed_fails() -> None:
    base = default_offline_exchange_impl_descriptor()
    bad = BoundedFuturesTestnetExchangeImplDescriptor(
        impl_module=base.impl_module,
        impl_class=base.impl_class,
        adapter_binding=base.adapter_binding,
        network_calls_allowed=True,
        execute_authorized=False,
        testnet_scoped=True,
        supports_reduce_only=True,
        supports_position_read=True,
        supports_margin_read=True,
    )
    result = validate_futures_testnet_exchange_impl_descriptor(bad)
    assert result["exchange_impl_contract_pass"] is False


def test_stub_place_order_fail_closed() -> None:
    stub = BoundedFuturesTestnetExchangeImplStub(default_offline_exchange_impl_descriptor())
    with pytest.raises(RuntimeError, match="not authorized"):
        stub.place_order_fail_closed()


def test_no_requests_import_in_exchange_impl_module() -> None:
    text = EXCHANGE_IMPL_MODULE.read_text(encoding="utf-8")
    assert "import requests" not in text
    assert "urllib" not in text


def test_section5_pe10_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_exchange_impl_contract_v0" in section5
    assert ADAPTER_MODULE.is_file()


def test_charter_refresh_suffix_documented() -> None:
    assert CHARTER_REFRESH_SUFFIX in Path(__file__).read_text(encoding="utf-8")
