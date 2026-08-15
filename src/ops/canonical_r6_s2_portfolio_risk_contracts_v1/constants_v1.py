"""Constants for R6 S2 portfolio-risk contracts v1.

Read-only forensic overlay. Reconstructs structural portfolio-risk
semantics and authority boundaries. Does not implement Multi-Future
runtime, change G13, invent N>1 numerics, or claim live proof.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1"
PACKAGE_MARKER = "CANONICAL_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1=true"
CONTRACT_ID = "canonical_r6_s2_portfolio_risk_contracts"
CONTRACT_VERSION = "canonical_r6_s2_portfolio_risk_contracts/v1"
CONTRACT_OWNER = "ops.canonical_r6_s2_portfolio_risk_contracts_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_r6_s2_portfolio_risk_contracts_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_r6_s2_portfolio_risk_contracts_canonical_json_v1"

REMEDIATION_ID = "R6_S2_PORTFOLIO_RISK_CONTRACTS"
SOURCE_GAP_IDS = ("I37", "I74", "I85", "I12", "I29", "RB-G13", "PHASE_8", "CLUSTER_E", "CLUSTER_F")
DONE_CRITERION = "S2_STRUCTURAL_PORTFOLIO_RISK_CONTRACTS_BOUND_WITHOUT_RUNTIME"
TARGET_BINDING = "S2_PORTFOLIO_RISK_CONTRACTS_FAIL_CLOSED_SINGLE_FUTURE"

CANONICAL_AUTHORITY_CHAIN = (
    "strategy_selection",
    "scope_capital",
    "risk",
    "safety",
    "intent",
    "execution",
)

CANONICAL_SINGLE_INSTRUMENT_RISK_OWNER = "src.governance.capital_risk_sizing_v1"
CANONICAL_SINGLE_INSTRUMENT_RISK_GATE = "src.ops.gates.risk_gate"
CANONICAL_SAFETY_OWNER = "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
FUTURE_PORTFOLIO_RISK_OWNER = "canonical_risk_chain_extended_by_i85_contracts_not_a_second_engine"
COMPONENT_RISK_OWNER = "canonical_risk_chain_per_instrument_context_consuming_i37_methods"

I37_ROLE = "GOVERNED_SUPPORTING_VAR_CVAR_METHOD_LIBRARY"
I37_AUTHORITY_EFFECT = "NONE"
I74_ROLE = "CANONICAL_REQUIREMENT_ROADMAP_NON_RUNTIME"
I74_AUTHORITY_EFFECT = "NONE"
I85_ROLE = "CANONICAL_PORTFOLIO_COMPONENT_VAR_CONTRACT_IDENTITY_G13_GATED"
I85_AUTHORITY_EFFECT = "NONE"
I12_ROLE = "CANONICAL_AUTO_LIQUIDATION_NOT_IMPLEMENTED_R7"
I29_ROLE = "CANONICAL_KILL_SWITCH_SINGLE_FUTURE_SCOPE"

I37_I74_DUAL_VAR_AUTHORITY_FORBIDDEN = True
I85_PARALLEL_PORTFOLIO_OWNER_FORBIDDEN = True
SRC_PORTFOLIO_IS_RESEARCH_HELPER = True
RISK_LAYER_MANAGER_IS_AUTHORITY = False
RISK_ENFORCER_IS_AUTHORITY = False
LEGACY_POSITION_SIZER_IS_AUTHORITY = False
ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN = True
NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN = True
ALLOCATION_TO_ORDER_BYPASS_FORBIDDEN = True
PORTFOLIO_AGGREGATION_IS_DERIVED_UNLESS_EXPLICIT = True

NUMERIC_POLICY_STATUS = "DEFERRED_UNRATIFIED"
N_GREATER_THAN_ONE_RATIFIED = False
PORTFOLIO_VAR_LIMIT_RATIFIED = False
COMPONENT_VAR_LIMIT_RATIFIED = False
CORRELATION_THRESHOLD_RATIFIED = False
CONCENTRATION_PERCENTAGE_RATIFIED = False
PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED = False
GROSS_NET_EXPOSURE_LIMIT_RATIFIED = False

CAP23_OWNER = "ops.single_selected_future_policy_v1"
CAP24_OWNER = "ops.single_selected_future_runtime_binding_v1"
CAP22_OWNER = "ops.productive_futures_ranking_producer_v1"
CAP31_OWNER = "ops.productive_futures_accounting_runtime_binding_v1"
CAP11_RECON_OWNER = "ops.productive_reconciliation_runtime_binding_v1"
CAP72_OWNER = "ops.single_future_stateful_no_order_runtime_activation_v1"
ACCOUNTING_WRITER = "productive_futures_accounting_portfolio_writer_v1"
SELECTION_WRITER = "single_selected_future_selection_writer_v1"
RECON_WRITER = "productive_portfolio_position_state_writer_v1"
CAPITAL_RISK_SIZING_OWNER = "src.governance.capital_risk_sizing_v1"

SINGLE_FUTURE_LIVE_PROOF_MEANING = (
    "CAP_11_13_LIVE_CANARY_THEN_LIVE_ORDER_ECONOMIC_LADDER_NOT_I17_NOT_TESTNET_NOT_SHADOW"
)
SINGLE_FUTURE_LIVE_PROOF = False
I17_IS_NOT_LIVE_PROOF = True
TESTNET_IS_NOT_LIVE_PROOF = True
SHADOW_IS_NOT_LIVE_PROOF = True
GET_ONLY_LIVE_IS_NOT_LIVE_ORDER_PROOF = True

MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MULTI_FUTURE_RUNTIME_IMPLEMENTED = False
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
SINGLE_SELECTED_FUTURE = True
TOP_N_ACTIVE_SET_AUTHORITY = False
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
G13_UNCHANGED = True
NO_SILENT_G13_BYPASS = True
NO_AUTOMATIC_STAGE_PROGRESSION = True
UQ5_RATIFIED = True
U_MF_S1_RATIFIED = True
R6_S1_CLOSED = True

CORE_LOGIC_CHANGE = False
RISK_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False

LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = False
ORDER_EFFECT = "NONE"
R6_RUNTIME_AUTHORIZED = False
S3_RUNTIME_IMPLEMENTATION_AUTHORIZED = False
S5_AUTHORIZATION_GRANTED = False
S6_AUTONOMOUS_GRANTED = False

REQUIRED_OWNER_RELPATHS = (
    "src/governance/capital_risk_sizing_v1.py",
    "src/ops/gates/risk_gate.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_selected_future_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/constants_v1.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_reconciliation_runtime_binding_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/constants_v1.py",
    "src/risk/var.py",
    "src/risk/component_var.py",
    "src/risk/portfolio_var.py",
    "src/risk/covariance.py",
    "src/risk/enforcement.py",
    "src/risk/portfolio.py",
    "src/risk/risk_layer_manager.py",
    "src/portfolio/manager.py",
    "docs/risk/roadmaps/PORTFOLIO_VAR_ROADMAP.md",
    "docs/risk/roadmaps/COMPONENT_VAR_ROADMAP_PATCHED.md",
    "docs/risk/roadmaps/RISK_LAYER_ROADMAP.md",
    "docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md",
)

REUSE_CANDIDATES = (
    "src.governance.capital_risk_sizing_v1",
    "src.ops.gates.risk_gate",
    "src.risk.var",
    "src.risk.component_var",
    "src.risk.covariance",
    "src.risk.portfolio",
    "src.risk.portfolio_var",
    "src.risk.enforcement",
)

NON_AUTHORITY_HELPERS = (
    "src.risk.risk_layer_manager.RiskLayerManager",
    "src.risk.enforcement.RiskEnforcer",
    "src.risk.position_sizer",
    "src.portfolio.PortfolioManager",
    "src.portfolio.equal_weight",
    "src.portfolio.vol_target",
    "docs.risk.roadmaps",
)
