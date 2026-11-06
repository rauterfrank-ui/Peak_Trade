"""Mutation / submit boundary for §11.13.4 dry-run order plan (hard no-submit)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    FORBIDDEN_ORDER_API_METHODS,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    LIVE_RECONCILIATION_PROVEN,
    METHOD_ALLOWLIST,
    SUBMIT_FORBIDDEN,
)


class LiveDryRunOrderPlanMutationBoundaryError(RuntimeError):
    """Fail-closed mutation/submit boundary violation."""


def assert_get_only_method_v1(method: str) -> str:
    m = str(method or "").strip().upper()
    if m in FORBIDDEN_HTTP_METHODS or m not in METHOD_ALLOWLIST:
        raise LiveDryRunOrderPlanMutationBoundaryError(
            f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}"
        )
    return m


def assert_endpoint_not_mutation_v1(endpoint: str) -> str:
    ep = str(endpoint or "").strip()
    lowered = ep.lower()
    for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
        if marker not in lowered:
            continue
        if marker.rstrip("?") in {"/trade/order", "/api/v5/trade/order"} and (
            "/trade/orders-" in lowered or lowered.endswith("/trade/orders-pending")
        ):
            continue
        raise LiveDryRunOrderPlanMutationBoundaryError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
    return ep


def refuse_order_submit_v1(*, claimed_action: str) -> None:
    raise LiveDryRunOrderPlanMutationBoundaryError(
        f"ORDER_SUBMIT_HARD_BLOCKED_IN_LIVE_DRY_RUN:{claimed_action}"
    )


def refuse_order_api_method_v1(*, method_name: str) -> None:
    name = str(method_name or "").strip().lower()
    if name in FORBIDDEN_ORDER_API_METHODS or "order" in name and "pending" not in name:
        raise LiveDryRunOrderPlanMutationBoundaryError(
            f"ORDER_API_METHOD_HARD_BLOCKED:{method_name}"
        )
    raise LiveDryRunOrderPlanMutationBoundaryError(f"ORDER_API_METHOD_HARD_BLOCKED:{method_name}")


def assert_standing_gates_block_execute_v1(
    *,
    blocks_new_entry: bool,
    live_reconciliation_proven: bool,
    live_authorized: bool = LIVE_AUTHORIZED,
) -> list[str]:
    reasons: list[str] = []
    if live_authorized is not False or LIVE_AUTHORIZED is not False:
        reasons.append("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if LIVE_ENABLED or LIVE_ARMED or LIVE_ORDER_AUTHORIZED:
        reasons.append("LIVE_TRADING_GATES_MUST_REMAIN_FALSE")
    if live_reconciliation_proven is not False or LIVE_RECONCILIATION_PROVEN is not False:
        # Proven false is required for current unresolved divergence semantics.
        pass
    if live_reconciliation_proven is False:
        reasons.append("LIVE_RECONCILIATION_PROVEN=false")
    if blocks_new_entry:
        reasons.append("BLOCKS_NEW_ENTRY=true")
    if SUBMIT_FORBIDDEN:
        reasons.append("DRY_RUN_SUBMIT_FORBIDDEN=true")
    return reasons


def build_mutation_boundary_attestation_v1(
    *,
    blocks_new_entry: bool,
    live_reconciliation_proven: bool,
    write_request_count: int,
    order_request_count: int,
    cancel_request_count: int,
    amend_request_count: int,
    withdraw_request_count: int,
    transfer_request_count: int,
    methods_used: list[str],
) -> dict[str, Any]:
    block_reasons = assert_standing_gates_block_execute_v1(
        blocks_new_entry=blocks_new_entry,
        live_reconciliation_proven=live_reconciliation_proven,
    )
    if any(
        int(x) != 0
        for x in (
            write_request_count,
            order_request_count,
            cancel_request_count,
            amend_request_count,
            withdraw_request_count,
            transfer_request_count,
        )
    ):
        raise LiveDryRunOrderPlanMutationBoundaryError("NONZERO_MUTATION_COUNTER")
    if any(str(m).upper() != "GET" for m in methods_used):
        raise LiveDryRunOrderPlanMutationBoundaryError("NON_GET_METHOD_OBSERVED")
    return {
        "SUBMIT_REACHABLE": False,
        "ORDER_SUBMIT_PERFORMED": False,
        "ACCOUNT_MUTATION_PERFORMED": False,
        "LIVE_AUTHORIZED": False,
        "LIVE_ORDER_AUTHORIZED": False,
        "BLOCKS_NEW_ENTRY": bool(blocks_new_entry),
        "LIVE_RECONCILIATION_PROVEN": bool(live_reconciliation_proven),
        "EXECUTION_BLOCK_REASONS": block_reasons,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "DRY_RUN_MARKER": True,
        "NO_DEMO_SIMULATION": True,
    }


def assert_plan_cannot_reach_submit_v1(plan: Mapping[str, Any]) -> None:
    if plan.get("submitted") is True:
        raise LiveDryRunOrderPlanMutationBoundaryError("PLAN_MARKED_SUBMITTED_FORBIDDEN")
    if plan.get("submit") is True:
        raise LiveDryRunOrderPlanMutationBoundaryError("PLAN_SUBMIT_FLAG_TRUE_FORBIDDEN")
    if str(plan.get("lifecycle_state", "")).upper() in {
        "SUBMIT_PENDING",
        "SUBMITTED",
        "ACKED",
        "FILLED",
    }:
        raise LiveDryRunOrderPlanMutationBoundaryError("PLAN_LIFECYCLE_PAST_PRE_SUBMIT")
    venue_payload = plan.get("venue_native_dry_run_payload") or {}
    if isinstance(venue_payload, Mapping):
        if venue_payload.get("submit") is True:
            raise LiveDryRunOrderPlanMutationBoundaryError("VENUE_PAYLOAD_SUBMIT_TRUE")
        if venue_payload.get("dry_run") is not True:
            raise LiveDryRunOrderPlanMutationBoundaryError("VENUE_PAYLOAD_DRY_RUN_REQUIRED")
