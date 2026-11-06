"""Mechanical caller-graph closure for o4_n_bars_learning → WP-A/WP-C → DDO host."""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.ops.market_data_private_state_runtime_convergence_v1.consumer_census_v1 import (
    census_entry_by_id_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    converged_o4_handoff_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    o4_n_bars_envelope_from_historical_facts_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_public_plane_convergence_v1 import (
    BINDING_ID as PRODUCTIVE_DDO_O4_CONVERGENCE_BINDING_ID,
    COMPETING_PRODUCTIVE_O4_TRUTH,
    PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL,
    maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1,
)

CONSUMER_ID: Final[str] = "o4_n_bars_learning"
CLOSURE_SCHEMA: Final[str] = "o4_n_bars_learning_caller_closure_v1"


def build_o4_n_bars_learning_caller_closure_v1() -> dict[str, Any]:
    census = census_entry_by_id_v1(CONSUMER_ID)
    return {
        "schema_name": CLOSURE_SCHEMA,
        "consumer_id": CONSUMER_ID,
        "census_canonical_fact_source": census.canonical_fact_source,
        "census_wp_c_handoff": census.wp_c_convergence_handoff,
        "productive_wallclock_binding": PRODUCTIVE_DDO_O4_CONVERGENCE_BINDING_ID,
        "productive_materializer": (
            "maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1"
        ),
        "wp_a_adapter": "o4_n_bars_envelope_from_historical_facts_v1",
        "wp_c_handoff": "converged_o4_handoff_v1",
        "productive_ddo_o4_source_is_wp_a_wp_c_canonical": (
            PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL
        ),
        "competing_productive_o4_truth": COMPETING_PRODUCTIVE_O4_TRUTH,
        "ddo_observation_only": True,
        "promotion_binding_changed": False,
    }


def verify_productive_convergence_trace_on_state_v1(state: Any) -> Mapping[str, Any]:
    trace = getattr(state, "last_ddo_o4_public_plane_convergence", None)
    if not isinstance(trace, Mapping) or trace.get("ok") is not True:
        raise ValueError("PRODUCTIVE_O4_CONVERGENCE_TRACE_MISSING")
    if trace.get("productive_ddo_o4_source_is_wp_a_wp_c_canonical") is not True:
        raise ValueError("PRODUCTIVE_DDO_O4_SOURCE_NOT_CANONICAL")
    if trace.get("competing_productive_o4_truth") is not False:
        raise ValueError("COMPETING_PRODUCTIVE_O4_TRUTH")
    return trace


def dry_run_handoff_chain_v1(*, pt1h_bars: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Offline proof that WP-A → WP-C handoff accepts canonical bar payloads."""
    wp_a = o4_n_bars_envelope_from_historical_facts_v1(pt1h_bars)
    wp_c = converged_o4_handoff_v1(wp_a)
    return {"wp_a": wp_a, "wp_c": wp_c}


__all__ = [
    "build_o4_n_bars_learning_caller_closure_v1",
    "dry_run_handoff_chain_v1",
    "maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1",
    "verify_productive_convergence_trace_on_state_v1",
]
