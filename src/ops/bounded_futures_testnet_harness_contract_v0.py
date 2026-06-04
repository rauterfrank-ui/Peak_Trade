"""Repo-native bounded Futures Testnet harness contract (v0).

Offline contract for futures-specific bounded testnet execute harness readiness.
Validates adapter binding + evidence template against bounded_futures_testnet_contract_v0.
Does not authorize harness execute, network, credentials, or orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    ADAPTER_NETWORK_CALLS_ALLOWED,
    BoundedFuturesTestnetAdapterBinding,
    FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN,
    PACKAGE_MARKER as ADAPTER_PACKAGE_MARKER,
    default_offline_adapter_binding,
    validate_futures_testnet_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_ORDER_POLICY,
    DEFAULT_SESSION_CLASS,
    EVIDENCE_SOURCE_FUTURES_HARNESS,
    FUTURES_SESSION_AUTHORIZED_NOW,
    default_bounded_futures_normal_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
)

HARNESS_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_HARNESS_CONTRACT_V0=true"
HARNESS_EXECUTE_AUTHORIZED_NOW = False
FUTURES_EXECUTE_AUTHORITY_ADDED = False


@dataclass(frozen=True)
class BoundedFuturesTestnetHarnessConfig:
    session_class: str
    order_policy: str
    evidence_source: str
    evidence_dir: str
    planned_duration_seconds: int
    max_order_attempts: int
    max_real_orders: int
    max_cancel_attempts: int
    max_notional_eur: float
    max_position_hold_seconds: int
    operator_go_token: str | None


def default_offline_harness_config(*, evidence_dir: str = "") -> BoundedFuturesTestnetHarnessConfig:
    spec = default_bounded_futures_normal_v0_spec()
    return BoundedFuturesTestnetHarnessConfig(
        session_class=DEFAULT_SESSION_CLASS,
        order_policy=DEFAULT_ORDER_POLICY,
        evidence_source=EVIDENCE_SOURCE_FUTURES_HARNESS,
        evidence_dir=evidence_dir,
        planned_duration_seconds=300,
        max_order_attempts=spec.max_order_attempts,
        max_real_orders=spec.max_real_orders,
        max_cancel_attempts=spec.max_cancel_attempts,
        max_notional_eur=spec.max_notional_eur,
        max_position_hold_seconds=spec.max_position_hold_seconds,
        operator_go_token=None,
    )


def build_offline_harness_evidence_template(
    binding: BoundedFuturesTestnetAdapterBinding,
    config: BoundedFuturesTestnetHarnessConfig,
) -> dict[str, Any]:
    """Skeleton evidence dict for contract evaluation (zero-order planning template)."""
    return {
        "session_class": config.session_class,
        "order_policy": config.order_policy,
        "instrument": binding.instrument,
        "market_type": binding.market_type,
        "margin_mode": binding.margin_mode,
        "max_leverage": binding.max_leverage,
        "leverage_within_cap": binding.max_leverage
        <= default_bounded_futures_normal_v0_spec().max_leverage,
        "position_mode": binding.position_mode,
        "order_side_semantics": binding.order_side_semantics,
        "reduce_only_supported": binding.reduce_only_supported,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "order_notional_eur": 0.0,
        "order_notional_within_cap": True,
        "position_flattened_by_end": True,
        "cancel_or_close_evidence_valid": True,
        "futures_endpoint_isolation_pass": True,
        "spot_endpoint_isolation_pass": True,
        "funding_risk_acknowledged": True,
        "liquidation_risk_acknowledged": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "master_v2_double_play_authority_used": False,
        "endpoints_called": [],
        "network_host": binding.network_host,
        "evidence_source": config.evidence_source,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "futures_session_authorized_now": False,
        "harness_execute_authorized_now": False,
        "futures_testnet_instrument_exchange_proven": FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN,
    }


def evaluate_bounded_futures_testnet_harness_readiness(
    config: BoundedFuturesTestnetHarnessConfig,
    binding: BoundedFuturesTestnetAdapterBinding | None = None,
) -> dict[str, Any]:
    """Fail-closed harness readiness (offline). Execute remains unauthorized."""
    binding = binding or default_offline_adapter_binding()
    result: dict[str, Any] = {
        "harness_contract_pass": False,
        "adapter_binding_pass": False,
        "evidence_template_pass": False,
        "harness_execute_authorized_now": HARNESS_EXECUTE_AUTHORIZED_NOW,
        "futures_session_authorized_now": FUTURES_SESSION_AUTHORIZED_NOW,
        "futures_testnet_instrument_exchange_proven": FUTURES_TESTNET_INSTRUMENT_EXCHANGE_PROVEN,
        "fail_reasons": [],
    }

    if HARNESS_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("HARNESS_EXECUTE_AUTHORIZED_NOW must be false")
    if FUTURES_EXECUTE_AUTHORITY_ADDED:
        result["fail_reasons"].append("FUTURES_EXECUTE_AUTHORITY_ADDED must be false")
    if ADAPTER_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("ADAPTER_NETWORK_CALLS_ALLOWED must be false")
    if config.operator_go_token:
        result["fail_reasons"].append(
            "operator_go_token must not be set without separate execute GO"
        )

    spec = default_bounded_futures_normal_v0_spec()
    if config.session_class != spec.session_class:
        result["fail_reasons"].append(f"session_class must be {spec.session_class!r}")
    if config.order_policy != spec.order_policy:
        result["fail_reasons"].append(f"order_policy must be {spec.order_policy!r}")
    if config.evidence_source != EVIDENCE_SOURCE_FUTURES_HARNESS:
        result["fail_reasons"].append(
            f"evidence_source must be {EVIDENCE_SOURCE_FUTURES_HARNESS!r}"
        )
    if config.max_real_orders > spec.max_real_orders:
        result["fail_reasons"].append("max_real_orders exceeds spec cap")
    if config.max_order_attempts > spec.max_order_attempts:
        result["fail_reasons"].append("max_order_attempts exceeds spec cap")
    if config.max_cancel_attempts > spec.max_cancel_attempts:
        result["fail_reasons"].append("max_cancel_attempts exceeds spec cap")
    if config.max_notional_eur > spec.max_notional_eur:
        result["fail_reasons"].append("max_notional_eur exceeds spec cap")

    adapter_result = validate_futures_testnet_adapter_binding(binding)
    result["adapter_binding_pass"] = adapter_result["adapter_binding_pass"]
    result["fail_reasons"].extend(adapter_result["fail_reasons"])

    template = build_offline_harness_evidence_template(binding, config)
    evidence_result = evaluate_bounded_futures_testnet_evidence(template)
    result["evidence_template_pass"] = evidence_result["bounded_futures_testnet_pass"]
    if not evidence_result["bounded_futures_testnet_pass"]:
        result["fail_reasons"].extend(evidence_result["fail_reasons"])

    result["harness_contract_pass"] = not result["fail_reasons"]
    return result
