"""Private-plane consumer convergence onto WP-B normalized state (no second truth)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.market_data_private_state_runtime_convergence_v1.constants_v1 import (
    ACCOUNT_EQUITY_SIZING_AUTHORITY_NOT_ACQUIRED_BY_WP_C,
    EXECUTION_AUTHORITY_STATUS,
    MV2_DP_AUTHORITY_STATUS,
    PRETRADE_AUTHORITY_STATUS,
    PRIVATE_STATE_STRATEGY_AUTHORITY,
    WP_B_OWNER,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    PRIVATE_STATE_PLANE_EQUITY_SIZING_AUTHORITY,
    RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED,
)


class PrivateConvergenceError(RuntimeError):
    pass


def assert_execution_boundary_unchanged_v1() -> dict[str, Any]:
    return {
        "execution_authority_status": EXECUTION_AUTHORITY_STATUS,
        "mv2_dp_authority_status": MV2_DP_AUTHORITY_STATUS,
        "pretrade_authority_status": PRETRADE_AUTHORITY_STATUS,
        "wp_c_may_rerank": False,
        "wp_c_may_reselect": False,
        "wp_c_may_mint_execution_permit": False,
    }


def converged_balance_equity_handoff_v1(
    wp_b_balance_adapter: Mapping[str, Any],
) -> dict[str, Any]:
    if wp_b_balance_adapter.get("private_state_plane_equity_sizing_authority") is True:
        raise PrivateConvergenceError("WP_B_EQUITY_SIZING_AUTHORITY_FORBIDDEN")
    if wp_b_balance_adapter.get("running_account_equity_mint_allowed") is True:
        raise PrivateConvergenceError("WP_B_EQUITY_MINT_FORBIDDEN")
    if not ACCOUNT_EQUITY_SIZING_AUTHORITY_NOT_ACQUIRED_BY_WP_C:
        raise PrivateConvergenceError("WP_C_EQUITY_SIZING_ACQUIRED")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "canonical_adapter_owner": WP_B_OWNER,
        "consumer_id": "private_balance_equity",
        "competing_transport_truth": False,
        "account_equity_sizing_authority_not_acquired_by_wp_c": True,
        "private_state_plane_equity_sizing_authority": PRIVATE_STATE_PLANE_EQUITY_SIZING_AUTHORITY,
        "running_account_equity_mint_allowed": RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED,
        "payload": dict(wp_b_balance_adapter),
    }


def converged_fresh_pretrade_hint_handoff_v1(
    wp_b_hint: Mapping[str, Any],
    *,
    endpoint_path: str,
) -> dict[str, Any]:
    if wp_b_hint.get("cached_wp_b_may_substitute_fresh_get") is True:
        raise PrivateConvergenceError("CACHED_WP_B_MUST_NOT_SUBSTITUTE_FRESH_GET")
    if wp_b_hint.get("fresh_pretrade_substitute_forbidden") is not True:
        raise PrivateConvergenceError("FRESH_PRETRADE_SUBSTITUTE_NOT_FORBIDDEN")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "consumer_id": "fresh_pretrade_runtime_get",
        "endpoint_path": endpoint_path,
        "competing_transport_truth": False,
        "payload": dict(wp_b_hint),
    }


def converged_private_readmodel_handoff_v1(
    wp_b_operator_readmodel: Mapping[str, Any],
    *,
    trusted_current: bool,
    reconciliation_required: bool,
) -> dict[str, Any]:
    if reconciliation_required and trusted_current:
        raise PrivateConvergenceError("UNTRUSTED_STATE_MARKED_TRUSTED")
    if not trusted_current and wp_b_operator_readmodel.get("strategy_authority") != "NONE":
        raise PrivateConvergenceError("STRATEGY_AUTHORITY_LEAK")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "consumer_id": "private_positions_orders_fills",
        "private_state_strategy_authority": PRIVATE_STATE_STRATEGY_AUTHORITY,
        "trusted_current": trusted_current,
        "reconciliation_required": reconciliation_required,
        "competing_transport_truth": False,
        "payload": dict(wp_b_operator_readmodel),
    }


def converged_private_surfaces_v1(
    wp_b_surfaces: Mapping[str, Any],
    *,
    trusted_current: bool,
    reconciliation_required: bool,
) -> dict[str, Any]:
    balance_key = "balance_equity_observation"
    if balance_key not in wp_b_surfaces and "balance_equity" in wp_b_surfaces:
        balance_key = "balance_equity"
    return {
        "schema_name": "wp_c_converged_private_surfaces.v1",
        "balance_equity": converged_balance_equity_handoff_v1(wp_b_surfaces[balance_key]),
        "fresh_pretrade_hint": converged_fresh_pretrade_hint_handoff_v1(
            wp_b_surfaces["fresh_pretrade_hint"],
            endpoint_path=str(wp_b_surfaces["fresh_pretrade_hint"].get("endpoint_path") or ""),
        ),
        "operator_readmodel": converged_private_readmodel_handoff_v1(
            wp_b_surfaces["operator_readmodel"],
            trusted_current=trusted_current,
            reconciliation_required=reconciliation_required,
        ),
        "execution_boundary": assert_execution_boundary_unchanged_v1(),
    }


def assert_baseline_before_delta_trusted_v1(
    *,
    baseline_established: bool,
    ws_delta_applied: bool,
) -> None:
    if ws_delta_applied and not baseline_established:
        raise PrivateConvergenceError("WS_DELTA_BEFORE_REST_BASELINE")


def stale_gap_fail_closed_v1(
    *,
    trusted_current: bool,
    quality_state: Optional[str],
) -> None:
    if quality_state in ("stale", "gap", "missing") and trusted_current:
        raise PrivateConvergenceError("STALE_GAP_TREATED_AS_TRUSTED")
