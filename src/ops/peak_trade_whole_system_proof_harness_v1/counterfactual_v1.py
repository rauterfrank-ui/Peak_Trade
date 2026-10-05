"""Counterfactual repair closure (analysis only — no productive mutation)."""

from __future__ import annotations

from typing import Any


def build_counterfactual_repair_closure_v1() -> dict[str, Any]:
    blockers = [
        {
            "BLOCKER": "natural_enter_market_outcome",
            "PREVENTS": "traversal_to_PRE_EXTERNAL_without_enter",
            "COUNTERFACTUAL_REPAIR": "synthetic_enter_in_ghv_only",
            "PRODUCTIVE_MUTATION_AUTHORIZED": False,
            "EXPOSES_BEHIND": ["decision_layer", "mv2_dp_compose"],
        },
        {
            "BLOCKER": "live_public_GET_freshness",
            "PREVENTS": "runtime_proof_without_network",
            "COUNTERFACTUAL_REPAIR": "fixture_backed_get_in_tests",
            "PRODUCTIVE_MUTATION_AUTHORIZED": False,
            "CLASSIFICATION": "LIVE_ONLY_UNPROVEN",
        },
    ]
    return {
        "BLOCKER_CHAIN": blockers,
        "COMPLETE_BOUNDED_MUTATION_SET": [],
        "ANALYSIS_ONLY": True,
    }
