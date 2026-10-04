"""CURRENT productive path owner references (read-only strings; no mutation imports)."""

from __future__ import annotations

# Resolved from src/ops/full_core_live_path_composition_root_v1/constants_v1.py (Phase 0)
CAP2_4_BINDING_OWNER = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
C1_OBSERVATION_OWNER = "distinct_market_observation_acceptor_v1"
DYNAMIC_DIRECTIONAL_SCOPE_OWNER = "canonical_scope_initialization_v1"
MV2_DOUBLE_PLAY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
CAPITAL_RISK_CRS_SIZING_OWNER = "capital_risk_admissibility_owner_v1"
INTENT_OWNER = "canonical_order_intent_owner_v1"
ADMISSION_OWNER = "evaluate_execution_admission_v1"
GOVERNED_CYCLE_OWNER = (
    "full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1"
)
VENUE_PLAN_OWNER = "full_core_live_path_composition_root_v1.current_productive_venue_plan_v1"
PRE_EXTERNAL_OWNER = "PRE_EXTERNAL_TERMINAL_BOUNDARY"

PTP_STAGE_ORDER: tuple[str, ...] = (
    "CAP2_4_BINDING",
    "C1_OBSERVATION",
    "DYNAMIC_DIRECTIONAL_SCOPE",
    "MV2_DOUBLE_PLAY",
    "CAPITAL_RISK_CRS_SIZING",
    "INTENT",
    "ADMISSION",
    "GOVERNED_CYCLE",
    "VENUE_PLAN",
    "PRE_EXTERNAL",
)

PTP_STAGE_OWNERS: dict[str, str] = {
    "CAP2_4_BINDING": CAP2_4_BINDING_OWNER,
    "C1_OBSERVATION": C1_OBSERVATION_OWNER,
    "DYNAMIC_DIRECTIONAL_SCOPE": DYNAMIC_DIRECTIONAL_SCOPE_OWNER,
    "MV2_DOUBLE_PLAY": MV2_DOUBLE_PLAY_OWNER,
    "CAPITAL_RISK_CRS_SIZING": CAPITAL_RISK_CRS_SIZING_OWNER,
    "INTENT": INTENT_OWNER,
    "ADMISSION": ADMISSION_OWNER,
    "GOVERNED_CYCLE": GOVERNED_CYCLE_OWNER,
    "VENUE_PLAN": VENUE_PLAN_OWNER,
    "PRE_EXTERNAL": PRE_EXTERNAL_OWNER,
}
