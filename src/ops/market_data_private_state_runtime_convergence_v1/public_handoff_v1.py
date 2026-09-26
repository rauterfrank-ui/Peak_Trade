"""Public-plane consumer convergence onto WP-A canonical facts (no transport truth)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.market_data_private_state_runtime_convergence_v1.constants_v1 import (
    CAP_2_3_SELECTION_OWNER,
    CAP_2_3_SELECTION_OWNER_STATUS,
    PUBLIC_MARKET_DATA_SELECTION_AUTHORITY,
    WP_A_OWNER,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import SELECTION_AUTHORITY
from src.ops.single_selected_future_policy_v1.constants_v1 import OWNER as CAP23_OWNER_CONST


class PublicConvergenceError(RuntimeError):
    pass


def forbid_direct_transport_as_consumer_truth_v1(
    *,
    consumer_id: str,
    transport_session_as_truth: bool,
) -> None:
    if transport_session_as_truth:
        raise PublicConvergenceError(f"DIRECT_TRANSPORT_CONSUMER_TRUTH_FORBIDDEN:{consumer_id}")


def assert_cap23_selection_owner_unchanged_v1() -> dict[str, Any]:
    if CAP_2_3_SELECTION_OWNER != CAP23_OWNER_CONST:
        raise PublicConvergenceError("CAP_2_3_SELECTION_OWNER_DRIFT")
    if SELECTION_AUTHORITY != "NONE":
        raise PublicConvergenceError("WP_A_SELECTION_AUTHORITY_NOT_NONE")
    return {
        "handoff": "cap23_selection_boundary",
        "cap_2_3_selection_owner": CAP_2_3_SELECTION_OWNER,
        "cap_2_3_selection_owner_status": CAP_2_3_SELECTION_OWNER_STATUS,
        "public_market_data_selection_authority": PUBLIC_MARKET_DATA_SELECTION_AUTHORITY,
        "wp_a_may_select": False,
    }


def converged_landscape_handoff_v1(
    wp_a_landscape: Mapping[str, Any],
    *,
    consumer_id: str = "landscape_dashboard",
) -> dict[str, Any]:
    forbid_direct_transport_as_consumer_truth_v1(
        consumer_id=consumer_id, transport_session_as_truth=False
    )
    if wp_a_landscape.get("dashboard_authority_effect") != "NONE":
        raise PublicConvergenceError("LANDSCAPE_AUTHORITY_EFFECT_NOT_NONE")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "canonical_adapter_owner": WP_A_OWNER,
        "consumer_id": consumer_id,
        "competing_transport_truth": False,
        "payload": dict(wp_a_landscape),
    }


def converged_ranking_b05_handoff_v1(
    wp_a_ranking: Mapping[str, Any],
    *,
    consumer_id: str = "ranking_b05_cap22",
) -> dict[str, Any]:
    forbid_direct_transport_as_consumer_truth_v1(
        consumer_id=consumer_id, transport_session_as_truth=False
    )
    if wp_a_ranking.get("ohlcv_substitution") is True:
        raise PublicConvergenceError("OHLCV_SUBSTITUTION_FORBIDDEN")
    cap23 = assert_cap23_selection_owner_unchanged_v1()
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "canonical_adapter_owner": WP_A_OWNER,
        "consumer_id": consumer_id,
        "competing_transport_truth": False,
        "ranking_safe": wp_a_ranking.get("ranking_safe"),
        "finalized_pt1m_mark_count": wp_a_ranking.get("finalized_pt1m_mark_count"),
        "required_count": wp_a_ranking.get("required_count"),
        "cap23_boundary": cap23,
        "payload": dict(wp_a_ranking),
    }


def converged_o4_handoff_v1(
    wp_a_o4: Mapping[str, Any],
    *,
    consumer_id: str = "o4_n_bars_learning",
) -> dict[str, Any]:
    if wp_a_o4.get("forward_fill") is True:
        raise PublicConvergenceError("O4_FORWARD_FILL_FORBIDDEN")
    if wp_a_o4.get("pt1m_semantic_migration") is True:
        raise PublicConvergenceError("O4_PT1M_MIGRATION_FORBIDDEN")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "consumer_id": consumer_id,
        "competing_transport_truth": False,
        "payload": dict(wp_a_o4),
    }


def converged_research_optimizer_handoff_v1(
    wp_a_research: Mapping[str, Any],
    *,
    consumer_id: str,
) -> dict[str, Any]:
    if wp_a_research.get("live_ws_required") is True:
        raise PublicConvergenceError("RESEARCH_LIVE_WS_REQUIRED_FORBIDDEN")
    if wp_a_research.get("promotion_authority") not in (None, "NONE"):
        raise PublicConvergenceError("RESEARCH_PROMOTION_AUTHORITY_FORBIDDEN")
    return {
        "convergence_owner": "ops.market_data_private_state_runtime_convergence_v1",
        "consumer_id": consumer_id,
        "competing_transport_truth": False,
        "payload": dict(wp_a_research),
    }


def converged_public_surfaces_v1(
    wp_a_surfaces: Mapping[str, Any],
) -> dict[str, Any]:
    """Single entry for all public converged consumer handoffs from WP-A publish."""
    return {
        "schema_name": "wp_c_converged_public_surfaces.v1",
        "landscape": converged_landscape_handoff_v1(wp_a_surfaces["landscape"]),
        "ranking_b05": converged_ranking_b05_handoff_v1(wp_a_surfaces["ranking_b05"]),
        "o4_n_bars": converged_o4_handoff_v1(wp_a_surfaces["o4_n_bars"]),
        "research_optimizer": converged_research_optimizer_handoff_v1(
            wp_a_surfaces["research_optimizer"],
            consumer_id="research_backtest",
        ),
        "cap23_boundary": assert_cap23_selection_owner_unchanged_v1(),
    }
