"""Authority inventory for Cap 5.1 — no parallel runtime/evidence authority."""

from __future__ import annotations

from typing import Any

from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    ACCOUNTING_OWNER,
    AUTHORITY_OWNER,
    CAP41_OWNER,
    CONFIG_TRUTH_OWNER,
    DASHBOARD_AUTHORITY_EFFECT,
    DASHBOARD_ROLE,
    DECISION_AUTHORITY_OWNER,
    DOUBLE_PLAY_PARITY_OWNER,
    PRODUCTIVE_BRIDGE_OWNER,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    RANKING_OWNER,
    RECONCILIATION_OWNER,
    SELECTION_AUTHORITY_OWNER,
    SELECTION_RUNTIME_BINDING_OWNER,
    TYPED_VOLATILITY_PRESENCE_OWNER,
    UNIVERSE_OWNER,
    VERIFIER_OWNER,
)


def inventory_offline_evidence_authority_surfaces_v1() -> dict[str, Any]:
    """Declare productive vs legacy/parallel authority surfaces for Cap 5.1."""
    return {
        "offline_evidence_authority": AUTHORITY_OWNER,
        "productive_runtime_host_reused": PRODUCTIVE_RUNTIME_HOST,
        "offline_evidence_entrypoint": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "second_canonical_runtime_host_created": False,
        "parallel_runtime_authority_created": False,
        "parallel_selection_authority_created": False,
        "parallel_accounting_authority_created": False,
        "parallel_evidence_authority_created": False,
        "authority_map": {
            "reconciliation": RECONCILIATION_OWNER,
            "universe": UNIVERSE_OWNER,
            "ranking": RANKING_OWNER,
            "selection": SELECTION_AUTHORITY_OWNER,
            "selection_runtime_binding": SELECTION_RUNTIME_BINDING_OWNER,
            "accounting": ACCOUNTING_OWNER,
            "decision": DECISION_AUTHORITY_OWNER,
            "bridge_host": PRODUCTIVE_BRIDGE_OWNER,
            "typed_volatility_presence": TYPED_VOLATILITY_PRESENCE_OWNER,
            "double_play_parity": DOUBLE_PLAY_PARITY_OWNER,
            "config_truth": CONFIG_TRUTH_OWNER,
            "pre_activation_closure": CAP41_OWNER,
            "verifier": VERIFIER_OWNER,
            "offline_evidence": AUTHORITY_OWNER,
        },
        "legacy_or_parallel_surfaces": [
            {
                "path": "src/webui/market_dashboard_landscape_v2",
                "role": "DASHBOARD_READ_ONLY_CONSUMER",
                "productive_runtime_authority": False,
                "dashboard_authority_effect": False,
            },
            {
                "path": (
                    "scripts/ops/"
                    "run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py"
                ),
                "role": "ANALYTICAL_BRIDGE_HELPER",
                "productive_runtime_authority": False,
                "notes": "Reused via Cap 4.1/2.4 host; not a second canonical host.",
            },
        ],
        "dashboard_authority_effect": DASHBOARD_AUTHORITY_EFFECT,
        "dashboard_role": DASHBOARD_ROLE,
        "allowlist_selection_authority": False,
        "direct_instrument_override_allowed": False,
        "legacy_parallel_authority_absent": True,
        "capability_owners_not_duplicated": True,
        "core_logic_changed": False,
        "master_v2_changed": False,
        "double_play_changed": False,
        "risk_changed": False,
        "safety_changed": False,
        "accounting_logic_changed": False,
        "selection_authority_unchanged": True,
    }
