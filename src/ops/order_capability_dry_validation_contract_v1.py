"""Order-Capability dry-validation contract (v1).

Pure offline validation for accepted operator inputs and pre-execute blockers.
Does not authorize orders, network, live, preflight lift, or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.bounded_testnet_order_cap_contract_v0 import default_bounded_normal_v0_spec

PACKAGE_MARKER = "ORDER_CAPABILITY_DRY_VALIDATION_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_dry_validation_result.v1"
DEFAULT_VENUE_HOST = "demo-futures.kraken.com"
DEFAULT_ORDER_TYPE = "limit"
DEFAULT_MAX_SESSION_DURATION_SECONDS = 60
ALLOWED_ORDER_TYPES = frozenset({DEFAULT_ORDER_TYPE})
FORBIDDEN_LIVE_VENUE_MARKERS = frozenset(
    {
        "futures.kraken.com",
        "api.kraken.com",
        "www.kraken.com",
    }
)


@dataclass(frozen=True)
class OrderCapabilityDryValidationInputs:
    instrument: str
    venue: str
    max_loss_cap_eur: float
    max_notional_eur: float
    order_type: str
    session_duration_seconds: int
    abort_ack_confirmed: bool
    max_notional_confirmed: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def venue_is_demo_testnet_only(venue: str) -> bool:
    normalized = _normalize(venue)
    if DEFAULT_VENUE_HOST not in normalized:
        return False
    for marker in FORBIDDEN_LIVE_VENUE_MARKERS:
        if marker in normalized and DEFAULT_VENUE_HOST not in normalized:
            return False
    return True


def validate_order_capability_dry_validation_inputs(
    inputs: OrderCapabilityDryValidationInputs,
) -> list[str]:
    """Return fail-closed reasons; empty list means input checks pass."""
    reasons: list[str] = []
    if inputs.instrument != DEFAULT_INSTRUMENT:
        reasons.append(f"instrument must be {DEFAULT_INSTRUMENT!r}")
    if not venue_is_demo_testnet_only(inputs.venue):
        reasons.append("venue must be demo/testnet-only and include demo-futures.kraken.com")
    if inputs.max_loss_cap_eur <= 0:
        reasons.append("max_loss_cap_eur must be > 0")
    if inputs.max_notional_eur <= 0:
        reasons.append("max_notional_eur must be > 0")
    if inputs.max_loss_cap_eur > inputs.max_notional_eur:
        reasons.append("max_loss_cap_eur must be <= max_notional_eur")
    if inputs.order_type not in ALLOWED_ORDER_TYPES:
        reasons.append(f"order_type must be one of {sorted(ALLOWED_ORDER_TYPES)!r}")
    if inputs.session_duration_seconds <= 0:
        reasons.append("session_duration_seconds must be > 0")
    if inputs.session_duration_seconds > DEFAULT_MAX_SESSION_DURATION_SECONDS:
        reasons.append(
            f"session_duration_seconds must be <= {DEFAULT_MAX_SESSION_DURATION_SECONDS}"
        )
    if not inputs.abort_ack_confirmed:
        reasons.append("abort_ack_confirmed must be true")
    if not inputs.max_notional_confirmed:
        reasons.append("max_notional_confirmed must be true")
    return reasons


def _safety_flags() -> dict[str, bool]:
    return {
        "no_order": True,
        "no_cancel": True,
        "no_trade": True,
        "no_position_mutation": True,
        "no_network": True,
        "no_secret_read": True,
        "no_live": True,
        "no_authority_change": True,
        "preflight_remains_blocked": True,
        "dry_validation_authorized": False,
        "order_capability_execute_authorized": False,
        "live_authorized": False,
        "order_submission_executed": False,
        "cancel_executed": False,
        "trade_position_mutation_executed": False,
        "network_api_called": False,
    }


def evaluate_order_capability_dry_validation(
    inputs: OrderCapabilityDryValidationInputs,
) -> dict[str, Any]:
    fail_reasons = validate_order_capability_dry_validation_inputs(inputs)
    verdict = "PASS" if not fail_reasons else "FAIL_CLOSED"
    return {
        "verdict": verdict,
        "execute_ready": False,
        "fail_reasons": fail_reasons,
        "input_status": {
            "instrument": inputs.instrument,
            "venue": inputs.venue,
            "max_loss_cap_eur": inputs.max_loss_cap_eur,
            "max_notional_eur": inputs.max_notional_eur,
            "order_type": inputs.order_type,
            "session_duration_seconds": inputs.session_duration_seconds,
        },
        "blocker_status": {
            "abort_ack_confirmed": inputs.abort_ack_confirmed,
            "max_notional_confirmed": inputs.max_notional_confirmed,
            "required_q7_abort_ack_before_execute": True,
            "required_max_notional_confirm_before_execute": True,
        },
        "safety_flags": _safety_flags(),
    }


def build_dry_validation_result(
    inputs: OrderCapabilityDryValidationInputs,
    *,
    adapter_version: str = "cli_order_capability_dry_validation_flow_v1",
) -> dict[str, Any]:
    evaluation = evaluate_order_capability_dry_validation(inputs)
    spec = default_bounded_normal_v0_spec()
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter_version": adapter_version,
        **evaluation,
        "contract_marker": PACKAGE_MARKER,
        "pe7_reference_max_notional_eur": spec.max_notional_eur,
        "pe7_reference_max_position_hold_seconds": spec.max_position_hold_seconds,
    }
