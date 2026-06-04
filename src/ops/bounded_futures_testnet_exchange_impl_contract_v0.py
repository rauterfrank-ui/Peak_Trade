"""Repo-native bounded Futures Testnet exchange impl descriptor contract (v0).

Offline contract for a futures testnet exchange *implementation stub* layered on PE-9
adapter binding. No network I/O, no credentials, no orders. Does not authorize execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    ADAPTER_NETWORK_CALLS_ALLOWED,
    BoundedFuturesTestnetAdapterBinding,
    FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN,
    default_offline_adapter_binding,
    validate_futures_testnet_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    FUTURES_SESSION_AUTHORIZED_NOW,
    REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_CONTRACT_V0=true"
EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED = False
ARCHIVE_EXCHANGE_CLIENT_PRESENT = False
FUTURES_EXECUTE_AUTHORITY_ADDED = False

ALLOWED_IMPL_KINDS: frozenset[str] = frozenset({"offline_contract_stub"})


@dataclass(frozen=True)
class BoundedFuturesTestnetExchangeImplDescriptor:
    impl_id: str
    adapter_binding: BoundedFuturesTestnetAdapterBinding
    impl_kind: str
    network_calls_allowed: bool
    reduce_only_command_model: str
    close_only_command_model: str
    flatten_evidence_required: bool
    funding_evidence_required: bool
    liquidation_evidence_required: bool


def default_offline_exchange_impl_descriptor() -> BoundedFuturesTestnetExchangeImplDescriptor:
    return BoundedFuturesTestnetExchangeImplDescriptor(
        impl_id="offline_bounded_futures_testnet_exchange_impl_v0",
        adapter_binding=default_offline_adapter_binding(),
        impl_kind="offline_contract_stub",
        network_calls_allowed=False,
        reduce_only_command_model="reduce_only_flag_required",
        close_only_command_model="cancel_or_close_bounded",
        flatten_evidence_required=True,
        funding_evidence_required=True,
        liquidation_evidence_required=True,
    )


def validate_futures_testnet_exchange_impl_descriptor(
    descriptor: BoundedFuturesTestnetExchangeImplDescriptor,
    *,
    endpoints_called: list[str] | None = None,
) -> dict[str, Any]:
    """Fail-closed exchange impl descriptor validation (offline)."""
    result: dict[str, Any] = {
        "exchange_impl_pass": False,
        "adapter_binding_pass": False,
        "instrument_endpoint_pass": False,
        "margin_leverage_command_model_pass": False,
        "evidence_field_contract_pass": False,
        "fail_reasons": [],
    }

    if EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED must be false")
    if FUTURES_EXECUTE_AUTHORITY_ADDED:
        result["fail_reasons"].append("FUTURES_EXECUTE_AUTHORITY_ADDED must be false")
    if FUTURES_SESSION_AUTHORIZED_NOW:
        result["fail_reasons"].append("FUTURES_SESSION_AUTHORIZED_NOW must be false")
    if descriptor.network_calls_allowed:
        result["fail_reasons"].append("descriptor.network_calls_allowed must be false")
    if not descriptor.impl_id:
        result["fail_reasons"].append("impl_id required")
    if descriptor.impl_kind not in ALLOWED_IMPL_KINDS:
        result["fail_reasons"].append(f"impl_kind must be one of {sorted(ALLOWED_IMPL_KINDS)}")
    if descriptor.reduce_only_command_model != "reduce_only_flag_required":
        result["fail_reasons"].append("reduce_only_command_model must be reduce_only_flag_required")
    if descriptor.close_only_command_model != "cancel_or_close_bounded":
        result["fail_reasons"].append("close_only_command_model must be cancel_or_close_bounded")
    if not descriptor.flatten_evidence_required:
        result["fail_reasons"].append("flatten_evidence_required must be true")
    if not descriptor.funding_evidence_required:
        result["fail_reasons"].append("funding_evidence_required must be true")
    if not descriptor.liquidation_evidence_required:
        result["fail_reasons"].append("liquidation_evidence_required must be true")

    binding = descriptor.adapter_binding
    if not binding.instrument or binding.instrument.strip() == "":
        result["fail_reasons"].append("unknown or empty futures instrument")
    if not binding.network_host:
        result["fail_reasons"].append("unknown or empty futures endpoint host")
    if not binding.testnet_scoped:
        result["fail_reasons"].append("adapter must be testnet_scoped")

    adapter_result = validate_futures_testnet_adapter_binding(
        binding, endpoints_called=endpoints_called
    )
    result["adapter_binding_pass"] = adapter_result["adapter_binding_pass"]
    result["fail_reasons"].extend(adapter_result["fail_reasons"])

    required_runtime_fields = (
        "position_flattened_by_end",
        "cancel_or_close_evidence_valid",
        "funding_risk_acknowledged",
        "liquidation_risk_acknowledged",
        "reduce_only_supported",
        "order_side_semantics",
    )
    missing = [f for f in required_runtime_fields if f not in REQUIRED_FUTURES_EVIDENCE_FIELD_NAMES]
    result["evidence_field_contract_pass"] = not missing
    if missing:
        result["fail_reasons"].append(f"missing futures evidence fields: {missing}")

    result["instrument_endpoint_pass"] = (
        bool(binding.instrument)
        and bool(binding.network_host)
        and adapter_result.get("futures_endpoint_allowlist_pass", False)
    )
    result["margin_leverage_command_model_pass"] = adapter_result.get("margin_leverage_pass", False)
    result["exchange_impl_pass"] = not result["fail_reasons"]
    result["futures_testnet_instrument_exchange_proven"] = (
        FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN
    )
    return result
