"""Authority inventory — Cap 6.2 inserts persistence wiring only."""

from __future__ import annotations

from typing import Any

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CANONICAL_SCOPE_SNAPSHOT_OWNER,
    CONFIRMATION_BINDING_OWNER,
    CORE_LOGIC_CHANGE,
    PRODUCTIVE_DECISION_OWNER,
    PRODUCTIVE_HOST,
    RUNTIME_SCOPE_STATE_OWNER,
    SCOPE_BOUNDARY_OWNER,
    SCOPE_TRANSITION_OWNER,
)


def inventory_dynamic_scope_binding_authority_surfaces_v1() -> dict[str, Any]:
    return {
        "dynamic_scope_binding_authority": AUTHORITY_OWNER,
        "productive_host": PRODUCTIVE_HOST,
        "decision_authority": PRODUCTIVE_DECISION_OWNER,
        "runtime_scope_state_owner": RUNTIME_SCOPE_STATE_OWNER,
        "canonical_scope_snapshot_owner": CANONICAL_SCOPE_SNAPSHOT_OWNER,
        "scope_transition_owner": SCOPE_TRANSITION_OWNER,
        "scope_boundary_owner": SCOPE_BOUNDARY_OWNER,
        "confirmation_binding_owner": CONFIRMATION_BINDING_OWNER,
        "parallel_master_v2_persistence_domain_created": False,
        "parallel_double_play_persistence_domain_created": False,
        "parallel_scope_domain_model_created": False,
        "serialization_adapter_has_decision_authority": False,
        "forced_intent_allowed": False,
        "master_v2_bypass_allowed": False,
        "double_play_bypass_allowed": False,
        "composition_bypass_allowed": False,
        "risk_bypass_allowed": False,
        "safety_bypass_allowed": False,
        "direct_fill_injection_allowed": False,
        "core_logic_changed": CORE_LOGIC_CHANGE,
        "productive_scope_authority": RUNTIME_SCOPE_STATE_OWNER,
    }
