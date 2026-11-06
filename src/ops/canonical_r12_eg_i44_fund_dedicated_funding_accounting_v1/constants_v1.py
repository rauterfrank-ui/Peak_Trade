"""Constants for R12 EG-I44 dedicated funding accounting contract v1.

Read-only forensic overlay. Reconstructs G16/I44 structural funding
accounting semantics. Does not activate funding, close G16, or implement
IG-I44-FUNDING-IF-ACTIVATED.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R12_EG_I44_FUND_DEDICATED_FUNDING_ACCOUNTING_V1"
PACKAGE_MARKER = "CANONICAL_R12_EG_I44_FUND_DEDICATED_FUNDING_ACCOUNTING_V1=true"
CONTRACT_ID = "canonical_r12_eg_i44_fund_dedicated_funding_accounting"
CONTRACT_VERSION = "canonical_r12_eg_i44_fund_dedicated_funding_accounting/v1"
CONTRACT_OWNER = "ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_r12_eg_i44_fund_dedicated_funding_accounting_canonical_json_v1"
)

REMEDIATION_ID = "R12_EG_I44_FUND_DEDICATED_FUNDING_ACCOUNTING"
SOURCE_GAP_IDS = ("EG-I44-FUND", "IG-I44-FUNDING-IF-ACTIVATED", "G16")
DONE_CRITERION_STRUCTURAL = "EG_I44_FUND_STRUCTURAL_CONTRACT_CLOSED_G16_STILL_OPEN"
TARGET_DAG_DONE_CRITERION = "G16_CLOSED_OR_EXPLICITLY_OUT_OF_SCOPE"
TARGET_BINDING = "I44_GATED_FUTURE_CAPABILITY_KEEP_GAP_STRUCTURAL_CONTRACT_ONLY"

OD_I44_DECISION = "RATIFIED_A_GATED_FUTURE_CAPABILITY_KEEP_GAP"
BOUND_PRIMARY_TARGET_ROLE = "TRANSITIONAL_GATE"
I44_STATUS = "TRANSITIONAL_GATE_GATED_FUTURE_CAPABILITY_KEEP_GAP"
AUTHORITY_CLASS = "EVIDENCE_SCOPE_GATED_FUTURE_KEEP_MASTER_G16"
I44_OUT_OF_SCOPE_FOREVER = False

MASTER_G16_STATUS = "INSUFFICIENT_EVIDENCE"
MASTER_G16_INTENT = "DEDICATED_ACCOUNTING_EVIDENCE_IF_FUNDING_ENTERS_SCOPE"
COMPARISON_G16_ID = "G16_COMPATIBLE_EQUITY_SAMPLING_FREQUENCY"
COMPARISON_G16_OWNER = "src.meta.learning_loop.comparison_ssot_v1.comparison_gates_v1"
COMPARISON_G16_SEMANTICALLY_DISTINCT = True

CANONICAL_ACCOUNTING_OWNER = "ops.productive_futures_accounting_runtime_binding_v1"
CANONICAL_ACCOUNTING_KERNEL = "src.execution.paper.futures_accounting"
FUNDING_FIELD_OWNER = "src.execution.paper.futures_accounting.FuturesPosition.funding_pnl"
FUNDING_APPLICATION_OWNER = "NONE_PRODUCTIVE"
FUNDING_APPLICATION_KERNEL_HELPER = "src.execution.paper.futures_accounting.apply_funding_payment"
FUNDING_OBSERVATION_OWNER = "RESEARCH_AND_MARKET_CONTEXT_NON_AUTHORITY"
FUNDING_RECON_OWNER = "NONE_PRODUCTIVE"
ACCOUNTING_WRITER = "productive_futures_accounting_portfolio_writer_v1"

I17_SHADOW_FUNDING_HELPER = (
    "ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1._apply_funding"
)
I17_SHADOW_FUNDING_IS_G16_PROOF = False
BACKTEST_FUNDING_MODEL_OWNER = "src.backtest.funding_model_v1"
BACKTEST_FUNDING_MODEL_IS_G16_PROOF = False
RESEARCH_FUNDING_IS_PRODUCTIVE_PROOF = False
FIELD_PRESENT_DOES_NOT_PROVE_ACCOUNTING = True

FUNDING_ACCOUNTING_PROVEN = False
FUNDING_ECONOMICS_PROVEN = False
FUNDING_PNL_PROVEN = False
G16_CLOSED = False
FUNDING_IMPLEMENTATION_AUTHORIZED = False
FUNDING_ACCOUNTING_ACTIVATED = False
IG_I44_FUNDING_IF_ACTIVATED_IMPLEMENTED = False

ZERO_FUNDING_IMPLICIT_FALLBACK_FORBIDDEN = True
RESEARCH_TO_ACCOUNTING_BYPASS_FORBIDDEN = True
RESEARCH_TO_INTENT_BYPASS_FORBIDDEN = True
FUNDING_CLAIM_FAIL_CLOSED = True

SINGLE_FUTURE_LIVE_PROOF = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MULTI_FUTURE_RUNTIME_IMPLEMENTED = False
MAX_POSITIONS_EFFECTIVE = 1
SINGLE_SELECTED_FUTURE = True
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
G13_UNCHANGED = True
R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED = False
R6_RUNTIME_AUTHORIZED = False

CORE_LOGIC_CHANGE = False
RISK_LOGIC_CHANGE = False
ACCOUNTING_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
AUTHORITY_EFFECT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
TRADING_GRANT = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = False
ORDER_EFFECT = "NONE"

REQUIRED_OWNER_RELPATHS = (
    "src/execution/paper/futures_accounting.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py",
    "src/ops/productive_reconciliation_runtime_binding_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/constants_v1.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/meta/learning_loop/comparison_ssot_v1/comparison_gates_v1.py",
    "src/backtest/funding_model_v1.py",
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
)
