"""Option-2 Optimization scope and evidenced code references. AUTHORITY=NONE.

This module does not change trading logic and does not close the four open findings.
"""

from __future__ import annotations

from typing import Any

MEMBERSHIP_RATIFIED = False
GUARDIAN_RATIFIED = False

OPEN_FINDINGS: dict[str, str] = {
    "EXPERIMENT_EVIDENCE_MEMBERSHIP": "UNRESOLVED",
    "ENVELOPE_WORDING": "OPEN",
    "ZERO_TARGET_DRIFT": "OPEN",
    "F1_M9_TRADING_REACHABILITY": "NOT_PROVEN_OUT_OF_SCOPE",
}

UNIVERSE = "peak_trade.canonical_optimization_universe.v1"
LEARNING_INPUT = "peak_trade.canonical_optimization_universe_learning_input.v1"
EXPERIMENT_PLANE = "peak_trade.canonical_optimization_universe_experiment_plane.v1"
INGRESS = "peak_trade.governance.optimization_proposal_ingress.v1"
SURFACE_M9 = "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
SURFACE_F2 = "RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE_OPTIMIZATION_V1"
SURFACE_F5 = "F5_FRESH_FUTURES_INPUT_FRESHNESS_MAX_AGE_SHADOW_RESEARCH_V1"
M9_TARGET = "peak_trade.governance.productive_target.m9_volatility_numeric_max_age_seconds/v1"
PROVENANCE_ELIGIBILITY = "optimization_provenance_eligibility_v1"
FULL_CORE_ACK = "full_core_learning_input_ack_reference"
ADVANCED_SEARCH = "canonical_advanced_search_v1"
CHAMPION = "canonical_champion_challenger_v1"
COMPARISON = "canonical_comparison_ssot_v1"
EXPERIMENT_IDENTITY = "canonical_experiment_identity_v1"
EXPERIMENT_MEMORY = "canonical_experiment_memory_v1"
ROBUSTNESS = "canonical_robustness_suite_v1"
ENVELOPE = "peak_trade.canonical_optimizable_envelope.v1"
EXPERIMENT_EVIDENCE = "canonical_optimization_experiment_evidence_v1"
F1_M9 = "f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1"

_CLASSIFICATIONS: dict[str, tuple[str, ...]] = {
    "domain_functional_members": (UNIVERSE, LEARNING_INPUT, EXPERIMENT_PLANE, INGRESS),
    "external_interfaces_under_observation": (SURFACE_M9, SURFACE_F2, SURFACE_F5),
    "external_references_only": (
        M9_TARGET,
        PROVENANCE_ELIGIBILITY,
        FULL_CORE_ACK,
        ADVANCED_SEARCH,
        CHAMPION,
        COMPARISON,
        EXPERIMENT_IDENTITY,
        EXPERIMENT_MEMORY,
        ROBUSTNESS,
        ENVELOPE,
    ),
    "explicitly_out_of_scope": (F1_M9,),
    "unresolved": (EXPERIMENT_EVIDENCE,),
}


def build_optimization_scope_v1() -> dict[str, list[str]]:
    return {key: list(values) for key, values in _CLASSIFICATIONS.items()}


def optimization_nodes_v1() -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    for field, class_name in (
        ("domain_functional_members", "DOMAIN_FUNCTIONAL_MEMBER"),
        ("external_interfaces_under_observation", "EXTERNAL_INTERFACE_UNDER_OBSERVATION"),
        ("external_references_only", "EXTERNAL_REFERENCE_ONLY"),
        ("explicitly_out_of_scope", "EXPLICITLY_OUT_OF_SCOPE"),
        ("unresolved", "UNRESOLVED"),
    ):
        for object_id in _CLASSIFICATIONS[field]:
            nodes.append({"object_id": object_id, "scope_class": class_name})
    return nodes


def optimization_references_v1() -> list[dict[str, Any]]:
    """Direct code references already read on the authorized pin. No invented edges."""
    return [
        _ref(
            "opt-universe-calls-learning-input",
            UNIVERSE,
            LEARNING_INPUT,
            "CALLS",
            "src/experiments/canonical_optimization_universe_v1.py",
            299,
            "validate_canonical_optimization_universe_learning_input_v1",
        ),
        _ref(
            "opt-plane-calls-learning-input",
            EXPERIMENT_PLANE,
            LEARNING_INPUT,
            "CALLS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            168,
            "validate_canonical_optimization_universe_learning_input_v1",
        ),
        _ref(
            "opt-ingress-imports-plane",
            INGRESS,
            EXPERIMENT_PLANE,
            "IMPORTS",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            42,
            "canonical_optimization_universe_experiment_plane_v1",
        ),
        _ref(
            "opt-ingress-consumes-plane-schema",
            INGRESS,
            EXPERIMENT_PLANE,
            "CONSUMES",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            144,
            "EXPERIMENT_PLANE_SCHEMA_VERSION",
        ),
        _ref(
            "opt-ingress-imports-m9-surface",
            INGRESS,
            SURFACE_M9,
            "IMPORTS",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            28,
            "canonical_m9_volatility_numeric_max_age_optimizable_surface_v1",
        ),
        _ref(
            "opt-ingress-imports-f2-surface",
            INGRESS,
            SURFACE_F2,
            "IMPORTS",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            18,
            "canonical_f2_research_backtest_cost_grid_optimizable_surface_v1",
        ),
        _ref(
            "opt-ingress-imports-f5-surface",
            INGRESS,
            SURFACE_F5,
            "IMPORTS",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            23,
            "canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1",
        ),
        _ref(
            "opt-universe-calls-m9-zero",
            UNIVERSE,
            M9_TARGET,
            "CALLS",
            "src/experiments/canonical_optimization_universe_v1.py",
            58,
            "zero_authorized_productive_targets_v1",
        ),
        _ref(
            "opt-plane-calls-m9-zero",
            EXPERIMENT_PLANE,
            M9_TARGET,
            "CALLS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            85,
            "zero_authorized_productive_targets_v1",
        ),
        _ref(
            "opt-learning-imports-provenance",
            LEARNING_INPUT,
            PROVENANCE_ELIGIBILITY,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_learning_input_v1.py",
            20,
            "optimization_provenance_eligibility_v1",
        ),
        _ref(
            "opt-full-core-calls-learning-input",
            FULL_CORE_ACK,
            LEARNING_INPUT,
            "CALLS",
            "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_ddo_capture_to_offline_export_join_v1.py",
            282,
            "validate_canonical_optimization_universe_learning_input_v1",
        ),
        _ref(
            "opt-ingress-imports-experiment-evidence",
            INGRESS,
            EXPERIMENT_EVIDENCE,
            "IMPORTS",
            "src/governance/optimization_proposal_governance_ingress_v1.py",
            38,
            "canonical_optimization_experiment_evidence_v1",
        ),
        _ref(
            "opt-envelope-calls-m9-surface",
            ENVELOPE,
            SURFACE_M9,
            "CALLS",
            "src/experiments/canonical_optimizable_envelope_v1.py",
            120,
            "apply_volatility_numeric_max_age_surface_registry_v1",
        ),
        _ref(
            "opt-envelope-calls-f2-surface",
            ENVELOPE,
            SURFACE_F2,
            "CALLS",
            "src/experiments/canonical_optimizable_envelope_v1.py",
            123,
            "apply_research_backtest_cost_grid_surface_registry_v1",
        ),
        _ref(
            "opt-envelope-calls-f5-surface",
            ENVELOPE,
            SURFACE_F5,
            "CALLS",
            "src/experiments/canonical_optimizable_envelope_v1.py",
            126,
            "apply_f5_fresh_futures_input_freshness_surface_registry_v1",
        ),
        _ref(
            "opt-plane-imports-advanced-search",
            EXPERIMENT_PLANE,
            ADVANCED_SEARCH,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            16,
            "canonical_advanced_search_v1",
        ),
        _ref(
            "opt-plane-imports-champion",
            EXPERIMENT_PLANE,
            CHAMPION,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            26,
            "canonical_champion_challenger_v1",
        ),
        _ref(
            "opt-plane-imports-comparison",
            EXPERIMENT_PLANE,
            COMPARISON,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            31,
            "canonical_comparison_ssot_v1",
        ),
        _ref(
            "opt-plane-imports-experiment-identity",
            EXPERIMENT_PLANE,
            EXPERIMENT_IDENTITY,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            32,
            "canonical_experiment_identity_v1",
        ),
        _ref(
            "opt-plane-imports-experiment-memory",
            EXPERIMENT_PLANE,
            EXPERIMENT_MEMORY,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            36,
            "canonical_experiment_memory_v1",
        ),
        _ref(
            "opt-plane-imports-robustness",
            EXPERIMENT_PLANE,
            ROBUSTNESS,
            "IMPORTS",
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            50,
            "canonical_robustness_suite_v1",
        ),
    ]


def optimization_policies_v1() -> list[dict[str, str]]:
    return [
        _policy(
            "productive-authority-none",
            UNIVERSE,
            "OPTIMIZATION_PRODUCTIVE_AUTHORITY",
            "NONE",
            'OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"',
            "src/experiments/canonical_optimization_universe_v1.py",
        ),
        _policy(
            "envelope-defined-false",
            UNIVERSE,
            "OPTIMIZABLE_ENVELOPE_DEFINED",
            "False",
            "OPTIMIZABLE_ENVELOPE_DEFINED: Final[bool] = False",
            "src/experiments/canonical_optimization_universe_v1.py",
        ),
        _policy(
            "promotion-authority-none",
            INGRESS,
            "PROMOTION_AUTHORITY",
            "NONE",
            'PROMOTION_AUTHORITY: Final[str] = "NONE"',
            "src/governance/optimization_proposal_governance_ingress_v1.py",
        ),
        _policy(
            "apply-authority-none",
            INGRESS,
            "PRODUCTIVE_APPLY_AUTHORITY",
            "NONE",
            'PRODUCTIVE_APPLY_AUTHORITY: Final[str] = "NONE"',
            "src/governance/optimization_proposal_governance_ingress_v1.py",
        ),
        _policy(
            "proposal-only",
            EXPERIMENT_PLANE,
            "PROPOSAL_DISPOSITION",
            "PROPOSAL_ONLY",
            'PROPOSAL_DISPOSITION: Final[str] = "PROPOSAL_ONLY"',
            "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
        ),
    ]


def _policy(
    policy_id: str,
    subject: str,
    attribute: str,
    expected: str,
    snippet: str,
    path: str,
) -> dict[str, str]:
    return {
        "policy_id": policy_id,
        "subject_node": subject,
        "attribute": attribute,
        "expected": expected,
        "observed": expected if _snippet_present(path, snippet) else "ABSENT",
        "evidence_ref": f"{path}:{snippet}",
    }


def _snippet_present(path: str, snippet: str) -> bool:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return False
    return snippet in text


def _ref(
    edge_id: str,
    source: str,
    target: str,
    edge_type: str,
    path: str,
    line: int,
    symbol: str,
) -> dict[str, Any]:
    return {
        "edge_id": edge_id,
        "source_native_id": source,
        "target_native_id": target,
        "edge_type": edge_type,
        "path": path,
        "line": line,
        "symbol": symbol,
    }
