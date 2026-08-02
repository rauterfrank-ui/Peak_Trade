"""Legacy / parallel instrument authority inventory for Cap 2.4 closure."""

from __future__ import annotations

from typing import Any


def inventory_instrument_authority_surfaces_v1() -> dict[str, Any]:
    """Classify productive vs research instrument inputs (fail-closed inventory)."""
    return {
        "productive_selection_authority_owner": ("CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"),
        "productive_selection_consumer": ("ops.single_selected_future_runtime_binding_v1"),
        "productive_runtime_host": (
            "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        ),
        "surfaces": [
            {
                "surface": "persisted_single_selected_future_selection_v1",
                "role": "SOLE_PRODUCTIVE_SELECTION_AUTHORITY",
                "owner": "ops.single_selected_future_policy_v1",
                "authority_effect": True,
            },
            {
                "surface": "single_selected_future_runtime_binding_v1",
                "role": "SOLE_PRODUCTIVE_SELECTION_CONSUMER",
                "owner": "ops.single_selected_future_runtime_binding_v1",
                "authority_effect": True,
            },
            {
                "surface": "governed_futures_universe_snapshot_v1",
                "role": "INSTRUMENT_GOVERNANCE_VALIDATION",
                "owner": "ops.governed_futures_universe_producer_v1",
                "authority_effect": False,
            },
            {
                "surface": "productive_futures_ranking_snapshot_v1",
                "role": "RANKING_REFERENCE_VALIDATION",
                "owner": "ops.productive_futures_ranking_producer_v1",
                "authority_effect": False,
            },
            {
                "surface": "venue_safety_allowlist",
                "role": "SAFETY_ADMIT_DENY_ONLY",
                "owner": "ops.single_selected_future_runtime_binding_v1",
                "authority_effect": False,
                "selection_authority": False,
            },
            {
                "surface": "dashboard_selected_future_display",
                "role": "READ_ONLY_CONSUMER",
                "owner": "webui/dashboard",
                "authority_effect": False,
            },
            {
                "surface": "bounded_futures_testnet_venue_binding_PRODUCTION_INSTRUMENT_ID",
                "role": "LEGACY_HARDCODED_DEFAULT_NOT_PRODUCTIVE_AUTHORITY",
                "owner": "ops.bounded_futures_testnet_venue_binding_v0",
                "authority_effect": False,
                "productive_rejected": True,
            },
            {
                "surface": "direct_runtime_instrument_override",
                "role": "RESEARCH_TEST_ONLY",
                "owner": "explicit_research_entrypoint",
                "authority_effect": False,
                "productive_rejected": True,
            },
            {
                "surface": "okx_futures_shadow_no_order_entrypoint_v0",
                "role": "LEGACY_NO_ORDER_RESEARCH_PATH",
                "owner": "ops.okx_futures_shadow_no_order_entrypoint_v0",
                "authority_effect": False,
                "productive_selected_future_authority": False,
            },
        ],
        "ALLOWLIST_SELECTION_AUTHORITY": False,
        "DASHBOARD_AUTHORITY_EFFECT": False,
        "DIRECT_INSTRUMENT_OVERRIDE_ALLOWED": False,
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": True,
        "SELECTION_CONSUMER_COUNT": 1,
    }
