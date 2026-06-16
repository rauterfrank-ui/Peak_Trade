"""Repo-native bounded Testnet order-cap contract (v0).

Offline contract evaluator for bounded-normal-testnet-v0 session evidence.
Does not authorize Testnet execute; RUN_TESTNET_SESSION_ALLOWED_NOW remains false.
Entrypoint CLI wiring is a separate follow-up slice.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any

from src.ops.wallclock_session_evidence_v0 import bounds_from_planned_duration

PACKAGE_MARKER = "BOUNDED_TESTNET_ORDER_CAP_CONTRACT_V0=true"
CLI_WIRING_COMPLETE_MARKER = "REPO_NATIVE_BOUNDED_ORDER_CAP_CLI_WIRING_COMPLETE=true"
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


def add_bounded_order_cap_cli_arguments(parser: argparse.ArgumentParser) -> None:
    """Register repo-native bounded order-cap CLI flags (defaults: bounded-normal-v0 charter)."""
    defaults = default_bounded_normal_v0_spec()
    parser.add_argument(
        "--session-class",
        type=str,
        default=defaults.session_class,
        help=f"Bounded session class (default: {defaults.session_class})",
    )
    parser.add_argument(
        "--order-policy",
        type=str,
        default=defaults.order_policy,
        help=f"Bounded order policy (default: {defaults.order_policy})",
    )
    parser.add_argument(
        "--max-real-orders",
        type=int,
        default=defaults.max_real_orders,
        help=f"Max real orders created (default: {defaults.max_real_orders})",
    )
    parser.add_argument(
        "--max-order-attempts",
        type=int,
        default=defaults.max_order_attempts,
        help=f"Max order attempts (default: {defaults.max_order_attempts})",
    )
    parser.add_argument(
        "--max-cancel-attempts",
        type=int,
        default=defaults.max_cancel_attempts,
        help=f"Max cancel/close attempts (default: {defaults.max_cancel_attempts})",
    )
    parser.add_argument(
        "--max-order-notional-eur",
        type=float,
        default=defaults.max_notional_eur,
        help=f"Max order notional EUR (default: {defaults.max_notional_eur})",
    )
    parser.add_argument(
        "--max-position-hold-seconds",
        type=int,
        default=defaults.max_position_hold_seconds,
        help=f"Max position hold seconds (default: {defaults.max_position_hold_seconds})",
    )
    parser.add_argument(
        "--require-position-flat-by-end",
        action=argparse.BooleanOptionalAction,
        default=defaults.position_must_be_flattened,
        help="Require position flattened by session end (default: true)",
    )


def bounded_cap_spec_from_namespace(args: argparse.Namespace) -> BoundedTestnetOrderCapSpec:
    return BoundedTestnetOrderCapSpec(
        session_class=str(args.session_class),
        order_policy=str(args.order_policy),
        max_real_orders=int(args.max_real_orders),
        max_order_attempts=int(args.max_order_attempts),
        max_cancel_attempts=int(args.max_cancel_attempts),
        max_notional_eur=float(args.max_order_notional_eur),
        max_position_hold_seconds=int(args.max_position_hold_seconds),
        position_must_be_flattened=bool(args.require_position_flat_by_end),
    )


def validate_bounded_cap_cli_namespace(args: argparse.Namespace) -> list[str]:
    """Fail-closed validation for bounded cap CLI values (offline, no I/O)."""
    reasons: list[str] = []
    spec = bounded_cap_spec_from_namespace(args)
    if spec.session_class == DEFAULT_SESSION_CLASS:
        for name, value in (
            ("max_real_orders", spec.max_real_orders),
            ("max_order_attempts", spec.max_order_attempts),
            ("max_cancel_attempts", spec.max_cancel_attempts),
            ("max_position_hold_seconds", spec.max_position_hold_seconds),
        ):
            if value <= 0:
                reasons.append(f"{name} must be positive for {DEFAULT_SESSION_CLASS}")
        if spec.max_notional_eur <= 0:
            reasons.append("max_order_notional_eur must be positive")
    duration = getattr(args, "duration", None)
    if duration is not None and duration <= 0:
        reasons.append("--duration must be a positive integer (minutes)")
    return reasons


def planned_duration_seconds_from_args(args: argparse.Namespace) -> int | None:
    duration = getattr(args, "duration", None)
    if duration is None:
        return None
    return int(duration) * 60


def build_entrypoint_bounded_cap_config_evidence(
    spec: BoundedTestnetOrderCapSpec,
    *,
    planned_duration_seconds: int | None = None,
) -> dict[str, Any]:
    """Pre-session bounded cap + wall-clock config evidence (no runtime counters)."""
    evidence: dict[str, Any] = {
        "evidence_source": EVIDENCE_SOURCE_REPO_NATIVE,
        "session_class": spec.session_class,
        "order_policy": spec.order_policy,
        "max_real_orders": spec.max_real_orders,
        "max_order_attempts": spec.max_order_attempts,
        "max_cancel_attempts": spec.max_cancel_attempts,
        "max_order_notional_eur": spec.max_notional_eur,
        "max_position_hold_seconds": spec.max_position_hold_seconds,
        "position_must_be_flattened_by_end": spec.position_must_be_flattened,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "cancel_or_close_attempted": False,
        "cancel_or_close_evidence_valid": False,
        "order_notional_eur": 0.0,
        "order_notional_within_cap": True,
        "position_flattened_by_end": False,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "bounded_order_cap_config_emitted": True,
    }
    if planned_duration_seconds is not None:
        evidence.update(bounds_from_planned_duration(planned_duration_seconds))
        evidence["planned_duration_seconds"] = planned_duration_seconds
    return evidence


def emit_entrypoint_bounded_cap_config_json(evidence: dict[str, Any]) -> str:
    return json.dumps(evidence, sort_keys=True)


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
