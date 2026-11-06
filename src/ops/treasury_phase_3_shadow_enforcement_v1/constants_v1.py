"""Treasury Phase-3 shadow/read-only enforcement. No mutation. No capital owner."""

from __future__ import annotations

CAPABILITY_ID = "TREASURY_PHASE_3_SHADOW_ENFORCEMENT_V1"
PACKAGE_MARKER = "TREASURY_PHASE_3_SHADOW_ENFORCEMENT_V1=true"
OWNER = "ops.treasury_phase_3_shadow_enforcement_v1"
SCHEMA_VERSION = "treasury_phase_3_shadow_enforcement.v1"
CONTRACT_VERSION = "v1"
JOIN_SEAM_ID = "TREASURY_PHASE_3_SHADOW_READ_ONLY_ENFORCEMENT_V1"

TREASURY_PHASE_3_STATUS = "SHADOW_ENFORCEMENT_BOUND"
TREASURY_SEPARATION_GATE_WIRED = True
TREASURY_MUTATION_REACHABLE = False
TREASURY_RISK_ADMISSIBLE_MINT = False
TREASURY_PRODUCTIVE_CAPITAL_OWNER = False
CREDENTIAL_EXPANSION = False
EXTERNAL_EFFECT_AUTHORIZED = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NETWORK_ALLOWED = False

PHASE_2_RECONCILIATION_OWNER = "ops.treasury_phase_2_read_only_reconciliation_v1"
SEPARATION_GATE_OWNER = "ops.treasury_separation_gate"

SHADOW_HTTP_SURFACE_11_13_2 = "section_11_13_2_live_private_read_only_v1"
SHADOW_HTTP_SURFACE_11_13_3 = "section_11_13_3_live_shadow_with_exchange_reconciliation_v1"
SHADOW_HTTP_SURFACE_11_13_4 = "section_11_13_4_live_dry_run_order_plan_v1"
ALLOWED_SHADOW_HTTP_SURFACES: tuple[str, ...] = (
    SHADOW_HTTP_SURFACE_11_13_2,
    SHADOW_HTTP_SURFACE_11_13_3,
    SHADOW_HTTP_SURFACE_11_13_4,
)

SECOND_CAPITAL_AUTHORITY_ADDED = False
STEP_29P_AUTHORITY_UNCHANGED = True
PRODUCTIVE_AUTHORITY_GRAPH_CHANGED = False

FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "construct_live_execution_port_v1",
    "post_entry_order",
    "join_capital_admission_into_admission_inputs_v1",
    "evaluate_step_29p_capital_risk_admissibility_v1",
    "join_treasury_capital_admission_into_account_equity_orchestration_v1",
)
