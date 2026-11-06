"""Authority inventory for Cap 5.2 — no parallel runtime/evidence authority."""

from __future__ import annotations

from typing import Any

from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    ACCOUNTING_OWNER,
    AUTHORITY_OWNER,
    CAP41_OWNER,
    CAP51_OWNER,
    CONFIG_TRUTH_OWNER,
    DASHBOARD_AUTHORITY_EFFECT,
    DASHBOARD_ROLE,
    DECISION_AUTHORITY_OWNER,
    DOUBLE_PLAY_PARITY_OWNER,
    PRODUCTIVE_BRIDGE_OWNER,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    PUBLIC_MD_CLIENT_OWNER,
    RANKING_OWNER,
    RECONCILIATION_OWNER,
    SELECTION_AUTHORITY_OWNER,
    SELECTION_RUNTIME_BINDING_OWNER,
    TYPED_VOLATILITY_PRESENCE_OWNER,
    UNIVERSE_OWNER,
    VERIFIER_OWNER,
)


def inventory_public_md_shadow_authority_surfaces_v1() -> dict[str, Any]:
    return {
        "public_md_shadow_evidence_authority": AUTHORITY_OWNER,
        "productive_runtime_host_reused": PRODUCTIVE_RUNTIME_HOST,
        "public_md_shadow_entrypoint": PRODUCTIVE_RUNTIME_ENTRYPOINT,
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
            "deterministic_offline_evidence": CAP51_OWNER,
            "public_md_client": PUBLIC_MD_CLIENT_OWNER,
            "verifier": VERIFIER_OWNER,
            "public_md_shadow_evidence": AUTHORITY_OWNER,
        },
        "legacy_or_parallel_surfaces": [
            {
                "path": "src/webui/market_dashboard_landscape_v2",
                "role": "DASHBOARD_READ_ONLY_CONSUMER",
                "productive_runtime_authority": False,
                "dashboard_authority_effect": False,
            }
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
