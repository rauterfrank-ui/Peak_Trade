"""Repo-native bounded Futures Testnet runtime harness contract (v0).

Offline contract for archive/runtime harness artifact readiness and exchange-impl binding.
Does not run harness, network, credentials, or orders. Execute remains unauthorized.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_exchange_impl_contract_v0 import (
    BoundedFuturesTestnetExchangeImplDescriptor,
    EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW,
    EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED,
    default_offline_exchange_impl_descriptor,
    validate_futures_testnet_exchange_impl_descriptor,
)
from src.ops.bounded_futures_testnet_harness_contract_v0 import (
    BoundedFuturesTestnetHarnessConfig,
    HARNESS_EXECUTE_AUTHORIZED_NOW,
    default_offline_harness_config,
    evaluate_bounded_futures_testnet_harness_readiness,
)

RUNTIME_HARNESS_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_CONTRACT_V0=true"
RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW = False
ARCHIVE_FUTURES_HARNESS_FILENAME = "bounded_futures_testnet_session_harness.py"
DEFAULT_HARNESS_TIER = "BOUNDED_FUTURES_TESTNET_SESSION_BOUNDED_V0"
REQUIRED_RUNTIME_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "SESSION_RESULT.json",
    "WALLCLOCK_EVIDENCE.json",
    "HEARTBEATS_REDACTED.jsonl",
)


@dataclass(frozen=True)
class BoundedFuturesTestnetRuntimeHarnessDescriptor:
    harness_tier: str
    archive_harness_filename: str
    evidence_dir_must_be_under_archive: bool
    exchange_impl: BoundedFuturesTestnetExchangeImplDescriptor
    harness_config: BoundedFuturesTestnetHarnessConfig
    runtime_script_present_in_repo: bool
    operator_go_token: str | None


def default_offline_runtime_harness_descriptor(
    *,
    evidence_dir: str = "",
) -> BoundedFuturesTestnetRuntimeHarnessDescriptor:
    return BoundedFuturesTestnetRuntimeHarnessDescriptor(
        harness_tier=DEFAULT_HARNESS_TIER,
        archive_harness_filename=ARCHIVE_FUTURES_HARNESS_FILENAME,
        evidence_dir_must_be_under_archive=True,
        exchange_impl=default_offline_exchange_impl_descriptor(),
        harness_config=default_offline_harness_config(evidence_dir=evidence_dir),
        runtime_script_present_in_repo=False,
        operator_go_token=None,
    )


def evaluate_bounded_futures_testnet_runtime_harness_readiness(
    descriptor: BoundedFuturesTestnetRuntimeHarnessDescriptor,
) -> dict[str, Any]:
    """Fail-closed runtime harness + exchange impl readiness (offline)."""
    result: dict[str, Any] = {
        "runtime_harness_contract_pass": False,
        "exchange_impl_contract_pass": False,
        "offline_harness_contract_pass": False,
        "runtime_harness_execute_authorized_now": RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW,
        "fail_reasons": [],
    }

    if RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW must be false")
    if HARNESS_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("HARNESS_EXECUTE_AUTHORIZED_NOW must be false")
    if EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW must be false")
    if EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED must be false")
    if descriptor.operator_go_token:
        result["fail_reasons"].append(
            "operator_go_token must not be set without separate execute GO"
        )
    if descriptor.harness_tier != DEFAULT_HARNESS_TIER:
        result["fail_reasons"].append(f"harness_tier must be {DEFAULT_HARNESS_TIER!r}")
    if descriptor.archive_harness_filename != ARCHIVE_FUTURES_HARNESS_FILENAME:
        result["fail_reasons"].append(
            f"archive_harness_filename must be {ARCHIVE_FUTURES_HARNESS_FILENAME!r}"
        )
    if descriptor.runtime_script_present_in_repo:
        result["fail_reasons"].append(
            "runtime_script_present_in_repo must be false until governed archive harness slice"
        )

    exchange_result = validate_futures_testnet_exchange_impl_descriptor(descriptor.exchange_impl)
    result["exchange_impl_contract_pass"] = exchange_result["exchange_impl_contract_pass"]
    result["fail_reasons"].extend(exchange_result["fail_reasons"])

    harness_result = evaluate_bounded_futures_testnet_harness_readiness(
        descriptor.harness_config,
        descriptor.exchange_impl.adapter_binding,
    )
    result["offline_harness_contract_pass"] = harness_result["harness_contract_pass"]
    result["fail_reasons"].extend(harness_result["fail_reasons"])

    if descriptor.evidence_dir_must_be_under_archive and descriptor.harness_config.evidence_dir:
        if "Peak_Trade_runtime_evidence_archive" not in descriptor.harness_config.evidence_dir:
            result["fail_reasons"].append("evidence_dir must be under Durable Archive Root")

    result["runtime_harness_contract_pass"] = not result["fail_reasons"]
    return result
