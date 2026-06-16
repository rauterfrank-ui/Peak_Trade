"""Static + offline bounded Futures Testnet exchange impl descriptor contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_runtime_harness_exchange_impl_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    BoundedFuturesTestnetAdapterBinding,
    default_offline_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW
from src.ops.bounded_futures_testnet_exchange_impl_contract_v0 import (
    ARCHIVE_EXCHANGE_CLIENT_PRESENT,
    EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED,
    FUTURES_EXECUTE_AUTHORITY_ADDED,
    PACKAGE_MARKER,
    default_offline_exchange_impl_descriptor,
    validate_futures_testnet_exchange_impl_descriptor,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCHANGE_IMPL_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_exchange_impl_contract_v0.py"
)
RUNTIME_HARNESS_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_runtime_harness_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in EXCHANGE_IMPL_MODULE.read_text(encoding="utf-8")


def test_exchange_impl_not_authorized_and_no_network() -> None:
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED is False
    assert ARCHIVE_EXCHANGE_CLIENT_PRESENT is True
    assert FUTURES_EXECUTE_AUTHORITY_ADDED is False


def test_default_exchange_impl_descriptor_passes() -> None:
    descriptor = default_offline_exchange_impl_descriptor()
    result = validate_futures_testnet_exchange_impl_descriptor(descriptor)
    assert result["exchange_impl_pass"] is True
    assert result["fail_reasons"] == []


def test_unknown_instrument_fails() -> None:
    binding = default_offline_adapter_binding()
    bad_binding = BoundedFuturesTestnetAdapterBinding(
        adapter_id=binding.adapter_id,
        instrument="",
        market_type=binding.market_type,
        margin_mode=binding.margin_mode,
        max_leverage=binding.max_leverage,
        position_mode=binding.position_mode,
        network_host=binding.network_host,
        endpoint_allowlist=binding.endpoint_allowlist,
        reduce_only_supported=binding.reduce_only_supported,
        testnet_scoped=binding.testnet_scoped,
        order_side_semantics=binding.order_side_semantics,
    )
    descriptor = default_offline_exchange_impl_descriptor()
    bad = type(descriptor)(
        impl_id=descriptor.impl_id,
        adapter_binding=bad_binding,
        impl_kind=descriptor.impl_kind,
        network_calls_allowed=descriptor.network_calls_allowed,
        reduce_only_command_model=descriptor.reduce_only_command_model,
        close_only_command_model=descriptor.close_only_command_model,
        flatten_evidence_required=descriptor.flatten_evidence_required,
        funding_evidence_required=descriptor.funding_evidence_required,
        liquidation_evidence_required=descriptor.liquidation_evidence_required,
    )
    result = validate_futures_testnet_exchange_impl_descriptor(bad)
    assert result["exchange_impl_pass"] is False


def test_network_calls_allowed_on_descriptor_fails() -> None:
    descriptor = default_offline_exchange_impl_descriptor()
    bad = type(descriptor)(
        impl_id=descriptor.impl_id,
        adapter_binding=descriptor.adapter_binding,
        impl_kind=descriptor.impl_kind,
        network_calls_allowed=True,
        reduce_only_command_model=descriptor.reduce_only_command_model,
        close_only_command_model=descriptor.close_only_command_model,
        flatten_evidence_required=descriptor.flatten_evidence_required,
        funding_evidence_required=descriptor.funding_evidence_required,
        liquidation_evidence_required=descriptor.liquidation_evidence_required,
    )
    result = validate_futures_testnet_exchange_impl_descriptor(bad)
    assert result["exchange_impl_pass"] is False


def test_runtime_harness_module_crosslink() -> None:
    assert RUNTIME_HARNESS_MODULE.is_file()
    assert "bounded_futures_testnet_exchange_impl_contract_v0" in RUNTIME_HARNESS_MODULE.read_text(
        encoding="utf-8"
    )


def test_section5_pe10_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_exchange_impl_contract_v0" in section5
    assert "bounded_futures_testnet_runtime_harness_contract_v0" in section5
