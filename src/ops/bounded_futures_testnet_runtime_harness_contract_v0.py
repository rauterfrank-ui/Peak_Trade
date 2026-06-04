"""Repo-native bounded Futures Testnet runtime harness impl descriptor contract (v0).

Offline contract composing PE-9 harness readiness with PE-10 exchange impl descriptor.
No archive harness script, no scheduler/runtime start, no network, no orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_contract_v0 import ADAPTER_NETWORK_CALLS_ALLOWED
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW
from src.ops.bounded_futures_testnet_exchange_impl_contract_v0 import (
    ARCHIVE_EXCHANGE_CLIENT_PRESENT,
    BoundedFuturesTestnetExchangeImplDescriptor,
    EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED,
    FUTURES_EXECUTE_AUTHORITY_ADDED,
    default_offline_exchange_impl_descriptor,
    validate_futures_testnet_exchange_impl_descriptor,
)
from src.ops.bounded_futures_testnet_harness_contract_v0 import (
    HARNESS_EXECUTE_AUTHORIZED_NOW,
    BoundedFuturesTestnetHarnessConfig,
    default_offline_harness_config,
    evaluate_bounded_futures_testnet_harness_readiness,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_CONTRACT_V0=true"
RUNTIME_HARNESS_EXECUTE_ALLOWED = False
RUNTIME_HARNESS_NETWORK_ALLOWED = False
ARCHIVE_HARNESS_SCRIPT_REL_PATH = "scripts/ops/archive_futures_testnet_harness_v0.py"
ARCHIVE_HARNESS_SCRIPT_PRESENT = True
ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW = False


@dataclass(frozen=True)
class BoundedFuturesTestnetRuntimeHarnessImplDescriptor:
    impl_id: str
    exchange_impl_id: str
    harness_config: BoundedFuturesTestnetHarnessConfig
    exchange_impl: BoundedFuturesTestnetExchangeImplDescriptor
    archive_script_required: bool
    runtime_started_allowed: bool
    scheduler_started_allowed: bool


def default_offline_runtime_harness_impl_descriptor(
    *,
    evidence_dir: str = "",
) -> BoundedFuturesTestnetRuntimeHarnessImplDescriptor:
    exchange = default_offline_exchange_impl_descriptor()
    return BoundedFuturesTestnetRuntimeHarnessImplDescriptor(
        impl_id="offline_bounded_futures_testnet_runtime_harness_v0",
        exchange_impl_id=exchange.impl_id,
        harness_config=default_offline_harness_config(evidence_dir=evidence_dir),
        exchange_impl=exchange,
        archive_script_required=False,
        runtime_started_allowed=False,
        scheduler_started_allowed=False,
    )


def validate_futures_testnet_runtime_harness_impl_descriptor(
    descriptor: BoundedFuturesTestnetRuntimeHarnessImplDescriptor,
) -> dict[str, Any]:
    """Fail-closed runtime harness impl descriptor (offline)."""
    result: dict[str, Any] = {
        "runtime_harness_impl_pass": False,
        "pe9_harness_readiness_pass": False,
        "exchange_impl_pass": False,
        "archive_script_absent_pass": False,
        "runtime_scheduler_guard_pass": False,
        "fail_reasons": [],
    }

    if RUNTIME_HARNESS_EXECUTE_ALLOWED:
        result["fail_reasons"].append("RUNTIME_HARNESS_EXECUTE_ALLOWED must be false")
    if RUNTIME_HARNESS_NETWORK_ALLOWED:
        result["fail_reasons"].append("RUNTIME_HARNESS_NETWORK_ALLOWED must be false")
    if HARNESS_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("HARNESS_EXECUTE_AUTHORIZED_NOW must be false")
    if FUTURES_EXECUTE_AUTHORITY_ADDED:
        result["fail_reasons"].append("FUTURES_EXECUTE_AUTHORITY_ADDED must be false")
    if ADAPTER_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("ADAPTER_NETWORK_CALLS_ALLOWED must be false")
    if EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED must be false")
    if FUTURES_SESSION_AUTHORIZED_NOW:
        result["fail_reasons"].append("FUTURES_SESSION_AUTHORIZED_NOW must be false")

    if not descriptor.impl_id:
        result["fail_reasons"].append("impl_id required")
    if descriptor.exchange_impl_id != descriptor.exchange_impl.impl_id:
        result["fail_reasons"].append("exchange_impl_id must match exchange_impl.impl_id")
    if descriptor.archive_script_required:
        result["fail_reasons"].append("archive_script_required must be false in v0")
    if descriptor.runtime_started_allowed:
        result["fail_reasons"].append("runtime_started_allowed must be false")
    if descriptor.scheduler_started_allowed:
        result["fail_reasons"].append("scheduler_started_allowed must be false")
    if not ARCHIVE_HARNESS_SCRIPT_PRESENT:
        result["fail_reasons"].append("ARCHIVE_HARNESS_SCRIPT_PRESENT must be true")
    if ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW must be false")
    if ARCHIVE_EXCHANGE_CLIENT_PRESENT:
        result["fail_reasons"].append("ARCHIVE_EXCHANGE_CLIENT_PRESENT must be false")

    exchange_result = validate_futures_testnet_exchange_impl_descriptor(descriptor.exchange_impl)
    result["exchange_impl_pass"] = exchange_result["exchange_impl_pass"]
    result["fail_reasons"].extend(exchange_result["fail_reasons"])

    harness_result = evaluate_bounded_futures_testnet_harness_readiness(
        descriptor.harness_config,
        binding=descriptor.exchange_impl.adapter_binding,
    )
    result["pe9_harness_readiness_pass"] = harness_result["harness_contract_pass"]
    if not harness_result["harness_contract_pass"]:
        result["fail_reasons"].extend(harness_result["fail_reasons"])

    result["archive_script_present_pass"] = ARCHIVE_HARNESS_SCRIPT_PRESENT
    result["archive_script_absent_pass"] = not descriptor.archive_script_required
    result["runtime_scheduler_guard_pass"] = (
        not descriptor.runtime_started_allowed and not descriptor.scheduler_started_allowed
    )
    result["runtime_harness_impl_pass"] = not result["fail_reasons"]
    return result
