"""Authority inventory — Cap 6.1 inserts wiring only; no parallel decision authority."""

from __future__ import annotations

from typing import Any

from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    C1_OWNER,
    C2_OWNER,
    C3_OWNER,
    CORE_LOGIC_CHANGE,
    PRODUCTIVE_DECISION_OWNER,
    PRODUCTIVE_HOST,
)


def inventory_confirmation_binding_authority_surfaces_v1() -> dict[str, Any]:
    return {
        "confirmation_binding_authority": AUTHORITY_OWNER,
        "productive_host": PRODUCTIVE_HOST,
        "decision_authority": PRODUCTIVE_DECISION_OWNER,
        "c1_owner": C1_OWNER,
        "c2_owner": C2_OWNER,
        "c3_owner": C3_OWNER,
        "parallel_master_v2_persistence_domain_created": False,
        "parallel_double_play_persistence_domain_created": False,
        "serialization_adapter_has_decision_authority": False,
        "forced_intent_allowed": False,
        "master_v2_bypass_allowed": False,
        "double_play_bypass_allowed": False,
        "composition_bypass_allowed": False,
        "risk_bypass_allowed": False,
        "safety_bypass_allowed": False,
        "direct_fill_injection_allowed": False,
        "core_logic_changed": CORE_LOGIC_CHANGE,
        "legacy_directional_confirmation_state_authority": False,
        "productive_confirmation_authority": "C3_side_carrier_using_C1_C2",
    }
