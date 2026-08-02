"""Constants for PHASE_9_2 public-MD session preflight (no network session)."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_LONG_RUNNING_STATEFUL_PUBLIC_MD_SIMULATION_EVIDENCE_V1"
TASK_ID = "PHASE_9_2_PUBLIC_MD_SESSION_PREFLIGHT_V1"
SCHEMA_VERSION = "phase_9_2_public_md_session_preflight.v1"
PRODUCER_VERSION = "phase_9_2_public_md_session_preflight.v1"
OWNER = "ops.phase_9_2_public_md_session_preflight_v1"
PACKAGE_MARKER = "PHASE_9_2_PUBLIC_MD_SESSION_PREFLIGHT_V1=true"

PREDECESSOR_CAPABILITY_ID = "PHASE_9_1_STRATEGY_REGISTRY_CLOSURE_V1"
ACTIVATION_CAPABILITY_ID = "CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1"

CORE_LOGIC_CHANGE = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
RUNTIME_START_ALLOWED = False
SIMULATED_EXECUTION_START_ALLOWED = False
LIVE_ORDERS = False
TESTNET_ORDERS = False
PAPER_EXCHANGE_ORDERS = False
EXCHANGE_CREDENTIAL_USE = False
REAL_CAPITAL_MOVEMENT = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"

CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_public_md_smoke_session_contract_v1.json"
CONFIG_SCHEMA_VERSION = "phase_9_2_public_md_smoke_session_contract.v1"

EVIDENCE_DIRNAME = "capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
EVIDENCE_SUBDIR = "preflight"
EVIDENCE_FILENAME = "phase_9_2_public_md_session_preflight_evidence_v1.json"
RESULT_FILENAME = "phase_9_2_public_md_session_preflight_result_v1.json"
READINESS_FILENAME = "phase_9_2_smoke_session_readiness_report_v1.json"
SMOKE_CONTRACT_FILENAME = "phase_9_2_public_md_smoke_session_contract_v1.json"
SESSION_LADDER_FILENAME = "phase_9_2_session_ladder_v1.json"
NETWORK_PROOF_FILENAME = "network_boundary_proof_v1.json"
PACING_PROOF_FILENAME = "pacing_rate_limit_proof_v1.json"
AUTH_PATH_FILENAME = "authorization_confirm_token_path_v1.json"
RESTART_PROOF_FILENAME = "state_restart_evidence_preflight_v1.json"
PARITY_PROOF_FILENAME = "parity_proof_v1.json"
PREREQUISITE_MATRIX_FILENAME = "prerequisite_matrix_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
CLAIM_MATRIX_FILENAME = "claim_matrix_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"

# Binding to productive Cap 7.2 / wallclock EEA public-MD contracts.
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"

SESSION_LADDER = (
    "SMOKE_SESSION",
    "ONE_HOUR_GOVERNED_SESSION",
    "RESTART_RECOVERY_SESSION",
    "RATE_LIMIT_RECONNECT_SESSION",
    "PROLONGED_NATURAL_MARKET_SESSION",
    "ADVERSE_STALE_DATA_SESSION",
    "MULTI_SESSION_CONTINUITY_CAMPAIGN",
)

# Smoke-only budgets (stricter than default wallclock; no zero-interval).
SMOKE_SESSION_ID = "phase_9_2_public_md_smoke_session_v1"
SMOKE_RUNTIME_SESSION_ID = "phase_9_2_smoke_runtime_session_v1"
SMOKE_CONFIRMATION_SESSION_ID = "phase_9_2_smoke_confirmation_session_v1"
SMOKE_DURATION_SECONDS = 180
SMOKE_POLL_INTERVAL_SECONDS = 2.0
SMOKE_HEARTBEAT_SECONDS = 5.0
SMOKE_HEARTBEAT_LOSS_SECONDS = 15.0
SMOKE_STALENESS_BUDGET_SECONDS = 5.0
SMOKE_MAX_GAP_SECONDS = 10.0
SMOKE_CONSECUTIVE_STALE_BUDGET = 3
SMOKE_RECONNECT_ATTEMPT_LIMIT = 3
SMOKE_RECONNECT_TIME_LIMIT_SECONDS = 60
SMOKE_PER_REQUEST_MAX_RETRIES = 2
SMOKE_SESSION_HTTP_429_BUDGET = 5
SMOKE_BACKOFF_INITIAL_SECONDS = 1.0
SMOKE_BACKOFF_MULTIPLIER = 2.0
SMOKE_BACKOFF_MAX_SECONDS = 30.0
SMOKE_RETRY_AFTER_MAX_SECONDS = 60.0
SMOKE_MINIMUM_INTERVAL_SECONDS = 2.0
SMOKE_MAX_REQUESTS_PER_SESSION = 120

REQUIRED_SESSION_METRICS = (
    "cycles",
    "distinct_observation_count",
    "duplicate_observation_count",
    "confirmation_phase_transitions",
    "candidate_count",
    "confirmed_count",
    "scope_transition_count",
    "entry_intent_count",
    "entry_fill_count",
    "reduce_intent_count",
    "reduce_fill_count",
    "exit_intent_count",
    "exit_fill_count",
    "total_fees",
    "total_slippage",
    "realized_pnl",
    "unrealized_pnl",
    "restart_count",
    "recovery_count",
    "reconciliation_results",
    "risk_veto_count",
    "safety_veto_count",
    "hold_count",
    "actionability_distribution",
    "state_divergence_count",
    "verifier_result",
)

CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
CONFIRM_TOKEN_ENV = "PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN"
PREREGISTRATION_OWNER = "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
AUTHORIZATION_CONSUMPTION_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1."
    "authorization_consumption_runtime_v1"
)
PUBLIC_MD_SHADOW_AUTH_OWNER = (
    "ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1."
    "authorization_consumption_v1"
)
EEA_TRANSPORT_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1"
EEA_NETWORK_GUARD_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1"
ACTIVATION_OWNER = "ops.single_future_stateful_no_order_runtime_activation_v1"
PACING_POLICY_OWNER = (
    "research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1."
    "public_md_rate_limit_policy_v1"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
