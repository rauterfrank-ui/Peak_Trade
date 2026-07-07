"""
Surface P offline-complete vs runtime-bridge-bound-not-activated contract v0.

Fail-closed semantic split: offline/backtest/scenario 4-way parity may be COMPLETE
while runtime bridge remains BOUND_NOT_ACTIVATED by policy. Does not grant runtime,
order, scheduler, or AI trade authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Tuple

from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    ORDER_EFFECT_NONE as AI_ORDER_EFFECT_NONE,
    RUNTIME_AUTHORITY_EFFECT_NONE as AI_RUNTIME_AUTHORITY_EFFECT_NONE,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)

SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_CONTRACT_LAYER_VERSION = "v0"
SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_CONTRACT_OWNER = (
    "trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0"
)
CONTRACT_SLICE_ID = (
    "SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_FAIL_CLOSED_CONTRACT_V0"
)
PACKAGE_MARKER = (
    "SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_FAIL_CLOSED_CONTRACT_V0=true"
)

SurfacePOfflineParityStatus = Literal["COMPLETE", "INCOMPLETE"]
SurfacePRuntimeBridgeBindingStatus = Literal["BOUND_NOT_ACTIVATED", "ACTIVATED", "UNBOUND"]
SurfacePRuntimeActivationStatus = Literal["NOT_ACTIVATED_POLICY_BLOCKED", "ACTIVATED"]
SurfacePOverallStatus = Literal[
    "PARTIAL_RUNTIME_ACTIVATION_PENDING",
    "PASS",
    "GAP_OFFLINE_INCOMPLETE",
]

_AUTHORITY_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"


@dataclass(frozen=True)
class SurfacePSemanticStatusV0:
    surface_p_offline_parity_status: SurfacePOfflineParityStatus
    surface_p_runtime_bridge_binding_status: SurfacePRuntimeBridgeBindingStatus
    surface_p_runtime_activation_status: SurfacePRuntimeActivationStatus
    surface_p_overall_status: SurfacePOverallStatus
    offline_economic_evidence_blocked_by_runtime_activation: bool
    runtime_authority_blocked_by_runtime_activation: bool
    ai_observability_boundary_documented: bool
    ai_layer_authority_effect: str
    ai_layer_order_effect: str
    ai_layer_runtime_effect: str
    runtime_authority_granted: bool
    order_authority_granted: bool
    scheduler_authority_granted: bool
    shadow_paper_testnet_live_authority_granted: bool
    offline_four_way_fixtures_complete: bool
    runtime_bridge_activated: bool
    fail_closed_reasons: Tuple[str, ...]


def _runtime_bridge_binding_status_v0() -> SurfacePRuntimeBridgeBindingStatus:
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED":
        return "BOUND_NOT_ACTIVATED"
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "ACTIVATED":
        return "ACTIVATED"
    return "UNBOUND"


def evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0(
    *,
    offline_four_way_fixtures_complete: bool | None = None,
) -> SurfacePSemanticStatusV0:
    """Evaluate fail-closed Surface P semantic split; never activates runtime bridge."""
    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    offline_complete = (
        offline_four_way_fixtures_complete
        if offline_four_way_fixtures_complete is not None
        else bar_assessment.fixtures_complete
    )
    runtime_bridge_binding = _runtime_bridge_binding_status_v0()
    runtime_bridge_activated = runtime_bridge_binding == "ACTIVATED"
    runtime_activation_status: SurfacePRuntimeActivationStatus = (
        "ACTIVATED" if runtime_bridge_activated else "NOT_ACTIVATED_POLICY_BLOCKED"
    )

    fail_reasons: list[str] = []
    if not offline_complete:
        fail_reasons.extend(bar_assessment.fail_closed_reasons or ("OFFLINE_FOUR_WAY_INCOMPLETE",))

    if offline_complete and runtime_bridge_binding == "BOUND_NOT_ACTIVATED":
        overall: SurfacePOverallStatus = "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    elif offline_complete and runtime_bridge_activated:
        overall = "PASS"
    else:
        overall = "GAP_OFFLINE_INCOMPLETE"

    return SurfacePSemanticStatusV0(
        surface_p_offline_parity_status="COMPLETE" if offline_complete else "INCOMPLETE",
        surface_p_runtime_bridge_binding_status=runtime_bridge_binding,
        surface_p_runtime_activation_status=runtime_activation_status,
        surface_p_overall_status=overall,
        offline_economic_evidence_blocked_by_runtime_activation=False,
        runtime_authority_blocked_by_runtime_activation=not runtime_bridge_activated,
        ai_observability_boundary_documented=AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
        ai_layer_authority_effect=_AUTHORITY_EFFECT_NONE,
        ai_layer_order_effect=AI_ORDER_EFFECT_NONE,
        ai_layer_runtime_effect=AI_RUNTIME_AUTHORITY_EFFECT_NONE,
        runtime_authority_granted=False,
        order_authority_granted=False,
        scheduler_authority_granted=False,
        shadow_paper_testnet_live_authority_granted=False,
        offline_four_way_fixtures_complete=offline_complete,
        runtime_bridge_activated=runtime_bridge_activated,
        fail_closed_reasons=tuple(fail_reasons),
    )


def surface_p_offline_parity_complete_runtime_activation_pending_v0(
    semantic: SurfacePSemanticStatusV0 | None = None,
) -> bool:
    """True when offline parity is complete and only runtime activation remains policy-blocked."""
    status = (
        semantic
        or evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    )
    return (
        status.surface_p_offline_parity_status == "COMPLETE"
        and status.surface_p_runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
        and status.surface_p_runtime_activation_status == "NOT_ACTIVATED_POLICY_BLOCKED"
        and status.surface_p_overall_status == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    )


def surface_p_semantic_status_to_dict_v0(
    semantic: SurfacePSemanticStatusV0,
) -> Mapping[str, object]:
    return {
        "surface_p_offline_parity_status": semantic.surface_p_offline_parity_status,
        "surface_p_runtime_bridge_binding_status": semantic.surface_p_runtime_bridge_binding_status,
        "surface_p_runtime_activation_status": semantic.surface_p_runtime_activation_status,
        "surface_p_overall_status": semantic.surface_p_overall_status,
        "offline_economic_evidence_blocked_by_runtime_activation": (
            semantic.offline_economic_evidence_blocked_by_runtime_activation
        ),
        "runtime_authority_blocked_by_runtime_activation": (
            semantic.runtime_authority_blocked_by_runtime_activation
        ),
        "ai_observability_boundary_documented": semantic.ai_observability_boundary_documented,
        "ai_layer_authority_effect": semantic.ai_layer_authority_effect,
        "ai_layer_order_effect": semantic.ai_layer_order_effect,
        "ai_layer_runtime_effect": semantic.ai_layer_runtime_effect,
        "runtime_authority_granted": semantic.runtime_authority_granted,
        "order_authority_granted": semantic.order_authority_granted,
        "scheduler_authority_granted": semantic.scheduler_authority_granted,
        "shadow_paper_testnet_live_authority_granted": semantic.shadow_paper_testnet_live_authority_granted,
        "offline_four_way_fixtures_complete": semantic.offline_four_way_fixtures_complete,
        "runtime_bridge_activated": semantic.runtime_bridge_activated,
        "runtime_reference_integration_status": RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
        "fail_closed_reasons": list(semantic.fail_closed_reasons),
    }
