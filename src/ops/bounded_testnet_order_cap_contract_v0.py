"""Repo-native bounded Testnet order-cap contract (v0).

Offline contract evaluator for bounded-normal-testnet-v0 session evidence.
Does not authorize Testnet execute; RUN_TESTNET_SESSION_ALLOWED_NOW remains false.
Entrypoint CLI wiring is a separate follow-up slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PACKAGE_MARKER = "BOUNDED_TESTNET_ORDER_CAP_CONTRACT_V0=true"
DEFAULT_SESSION_CLASS = "bounded-normal-testnet-v0"
DEFAULT_ORDER_POLICY = "normal-testnet-bounded"
EVIDENCE_SOURCE_REPO_NATIVE = "repo_native_session"
EVIDENCE_SOURCE_ARCHIVE_HARNESS = "archive_normal_testnet_harness"

REQUIRED_BOUNDED_ORDER_CAP_CLI_FLAGS: tuple[str, ...] = (
    "--max-real-orders",
    "--max-order-attempts",
    "--max-cancel-attempts",
    "--max-order-notional-eur",
    "--max-position-hold-seconds",
    "--session-class",
    "--order-policy",
)

REQUIRED_EVIDENCE_FIELD_NAMES: tuple[str, ...] = (
    "session_class",
    "order_policy",
    "order_attempt_count",
    "real_orders_created_count",
    "cancel_or_close_attempt_count",
    "order_notional_eur",
    "order_notional_within_cap",
    "position_flattened_by_end",
    "cancel_or_close_evidence_valid",
    "risk_killswitch_scope_active",
    "risk_killswitch_scope_pass",
)


@dataclass(frozen=True)
class BoundedTestnetOrderCapSpec:
    session_class: str
    order_policy: str
    max_real_orders: int
    max_order_attempts: int
    max_cancel_attempts: int
    max_notional_eur: float
    max_position_hold_seconds: int
    position_must_be_flattened: bool


def default_bounded_normal_v0_spec() -> BoundedTestnetOrderCapSpec:
    return BoundedTestnetOrderCapSpec(
        session_class=DEFAULT_SESSION_CLASS,
        order_policy=DEFAULT_ORDER_POLICY,
        max_real_orders=1,
        max_order_attempts=1,
        max_cancel_attempts=1,
        max_notional_eur=10.0,
        max_position_hold_seconds=60,
        position_must_be_flattened=True,
    )


def evaluate_bounded_order_cap_evidence(
    evidence: dict[str, Any],
    spec: BoundedTestnetOrderCapSpec | None = None,
) -> dict[str, Any]:
    """Fail-closed bounded order-cap evaluation (offline, no I/O)."""
    spec = spec or default_bounded_normal_v0_spec()
    result: dict[str, Any] = {
        "bounded_order_cap_pass": False,
        "order_attempt_cap_pass": False,
        "real_order_cap_pass": False,
        "cancel_close_cap_pass": False,
        "notional_cap_pass": False,
        "position_flatten_pass": False,
        "risk_killswitch_scope_pass": False,
        "fail_reasons": [],
    }

    for field in REQUIRED_EVIDENCE_FIELD_NAMES:
        if field not in evidence:
            result["fail_reasons"].append(f"missing required field: {field}")

    session_class = evidence.get("session_class")
    if session_class != spec.session_class:
        result["fail_reasons"].append(
            f"session_class must be {spec.session_class!r} (got {session_class!r})"
        )

    order_policy = evidence.get("order_policy")
    if order_policy != spec.order_policy:
        result["fail_reasons"].append(
            f"order_policy must be {spec.order_policy!r} (got {order_policy!r})"
        )

    order_attempts = evidence.get("order_attempt_count")
    if order_attempts is not None and order_attempts > spec.max_order_attempts:
        result["fail_reasons"].append("order_attempt_count exceeds cap")

    real_orders = evidence.get("real_orders_created_count")
    if real_orders is not None and real_orders > spec.max_real_orders:
        result["fail_reasons"].append("real_orders_created_count exceeds cap")

    cancel_attempts = evidence.get("cancel_or_close_attempt_count")
    if cancel_attempts is not None and cancel_attempts > spec.max_cancel_attempts:
        result["fail_reasons"].append("cancel_or_close_attempt_count exceeds cap")

    notional = evidence.get("order_notional_eur")
    if notional is not None and notional > spec.max_notional_eur:
        result["fail_reasons"].append("order_notional_eur exceeds cap")

    if real_orders and int(real_orders) > 0:
        if not evidence.get("cancel_or_close_attempted"):
            result["fail_reasons"].append("cancel_or_close required when real order created")
        if not evidence.get("cancel_or_close_evidence_valid"):
            result["fail_reasons"].append("cancel_or_close_evidence_valid required")

    if spec.position_must_be_flattened and not evidence.get("position_flattened_by_end"):
        result["fail_reasons"].append("position_flattened_by_end required")

    if not evidence.get("order_notional_within_cap"):
        result["fail_reasons"].append("order_notional_within_cap must be true")

    if not evidence.get("risk_killswitch_scope_active"):
        result["fail_reasons"].append("risk_killswitch_scope_active must be true")

    if not evidence.get("risk_killswitch_scope_pass"):
        result["fail_reasons"].append("risk_killswitch_scope_pass must be true")

    if evidence.get("scheduler_started"):
        result["fail_reasons"].append("scheduler_started must be false")
    if evidence.get("runtime_started"):
        result["fail_reasons"].append("runtime_started must be false")
    if evidence.get("live_env_present"):
        result["fail_reasons"].append("live_env_present must be false")

    result["order_attempt_cap_pass"] = (
        order_attempts is not None and order_attempts <= spec.max_order_attempts
    )
    result["real_order_cap_pass"] = real_orders is not None and real_orders <= spec.max_real_orders
    result["cancel_close_cap_pass"] = (
        cancel_attempts is not None and cancel_attempts <= spec.max_cancel_attempts
    )
    result["notional_cap_pass"] = (
        notional is not None
        and notional <= spec.max_notional_eur
        and evidence.get("order_notional_within_cap") is True
    )
    result["position_flatten_pass"] = evidence.get("position_flattened_by_end") is True
    result["risk_killswitch_scope_pass"] = evidence.get("risk_killswitch_scope_pass") is True

    result["bounded_order_cap_pass"] = not result["fail_reasons"]
    return result
