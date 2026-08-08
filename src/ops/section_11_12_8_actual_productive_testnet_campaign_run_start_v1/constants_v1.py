"""Constants for §11.12.8 ACTUAL productive Testnet campaign RUN START.

Implements CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1.

This package wires the productive start path end-to-end. This OWNER_GO authorizes
IMPLEMENTATION + stubbed acceptance proof only. It does NOT itself start a real
productive Testnet campaign, load real credentials, open a real network session,
submit orders, or begin §11.13.
"""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    CAPABILITY_ID as HANDOFF_CAPABILITY_ID,
)

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1"
PACKAGE_MARKER = (
    "CAPABILITY_11_SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1=true"
)
OWNER = "ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1"
CONTRACT_VERSION = "v1"
PATH_CLASS = "SECTION_11_12_8_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START"
PRODUCTIVE_CONSUMER_ROLE = "ACTUAL_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER"
PRODUCTIVE_EXECUTOR_ROLE = "ACTUAL_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_EXECUTOR"

PREDECESSOR_CAPABILITY_ID = HANDOFF_CAPABILITY_ID
NEXT_CONSUMER_CAPABILITY_ID = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
)

# Exact future productive OWNER_GO contract (accepted by this consumer).
SCOPED_OWNER_GO_TOKEN = CAPABILITY_ID
SCOPED_OWNER_GO_SCOPE = "EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
SCOPED_OWNER_GO_AUTHORIZATION = "EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"

CORE_LOGIC_CHANGE = False
REFERENCE_ONLY = False
IMPLEMENTATION_ONLY = True  # this PR/GO: implement + stubbed gate; no real campaign start
NEW_WRAPPER_LAYER_CREATED = False
DEPRECATED_NON_EXTENDABLE = False

# Module-level package claims for THIS implementation era (no real side effects).
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED = False
PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED = False
NETWORK_SESSION_STARTED = False
NETWORK_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
LIVE_ORDER_EFFECT = "NONE"
LIVE_AUTHORIZED = False
SECTION_11_13_STARTED = False
CAPABILITY_11_13_STARTED = False
CREDENTIAL_PLAINTEXT_LOADED = False

# Persisted default for TESTNET_AUTHORIZED remains false; runtime may be ephemeral true.
TESTNET_AUTHORIZED_PERSISTED_DEFAULT = False

CANONICAL_RUNTIME_MODE = "TESTNET"
CANONICAL_VENUE = "OKX"
CANONICAL_INSTRUMENT_SCOPE: tuple[str, ...] = ("BTC-USDT-SWAP",)
CANONICAL_ALLOWED_ORDER_TYPES: tuple[str, ...] = ("LIMIT",)
CANONICAL_POSITION_COUNT_LIMIT = 1
CANONICAL_EMERGENCY_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS
CANONICAL_SECRET_REFERENCE = "secretref://vault/peak-trade/testnet-demo"
CANONICAL_ACCOUNT_IDENTITY = "acct-uid-testnet-demo"

# Private Testnet / demo allowlist (OKX EEA simulated). Live hosts hard-blocked.
TESTNET_REST_HOSTS: tuple[str, ...] = ("eea.okx.com",)
TESTNET_PRIVATE_REST_BASE = "https://eea.okx.com"
TESTNET_PRIVATE_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/config",
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/trade/orders-pending",
)
LIVE_FORBIDDEN_HOSTS: tuple[str, ...] = (
    "www.okx.com",
    "okx.com",
    "aws.okx.com",
)
SIMULATION_HEADER_NAME = "x-simulated-trading"
SIMULATION_HEADER_VALUE = "1"

# State machine stages.
STATE_IDLE = "IDLE"
STATE_GO_CONSUMED = "GO_CONSUMED"
STATE_AUTHORIZED = "AUTHORIZED"
STATE_ENABLED = "ENABLED"
STATE_ARMED = "ARMED"
STATE_CONFIRM_LATCHED = "CONFIRM_LATCHED"
STATE_CREDENTIAL_BOUND = "CREDENTIAL_BOUND"
STATE_PREFLIGHT_PASS = "PREFLIGHT_PASS"
STATE_NETWORK_SESSION_STARTED = "NETWORK_SESSION_STARTED"
STATE_CAMPAIGN_RUNNING = "CAMPAIGN_RUNNING"
STATE_COMPLETED = "COMPLETED"
STATE_ABORTED = "ABORTED"
STATE_SEALED = "SEALED"

STATE_SEQUENCE: tuple[str, ...] = (
    STATE_IDLE,
    STATE_GO_CONSUMED,
    STATE_AUTHORIZED,
    STATE_ENABLED,
    STATE_ARMED,
    STATE_CONFIRM_LATCHED,
    STATE_CREDENTIAL_BOUND,
    STATE_PREFLIGHT_PASS,
    STATE_NETWORK_SESSION_STARTED,
    STATE_CAMPAIGN_RUNNING,
    STATE_COMPLETED,
    STATE_ABORTED,
    STATE_SEALED,
)

DURABLE_STATE_SCHEMA = "section_11_12_8_actual_start_durable_state.v1"
DURABLE_STATE_FILENAME = "actual_start_durable_state_v1.json"

MODE_STUBBED_ACCEPTANCE = "STUBBED_ACCEPTANCE_GATE"
MODE_PRODUCTIVE_REAL = "PRODUCTIVE_REAL_NETWORK"  # not invoked by this implementation GO

CALL_CHAIN_LINKS: tuple[str, ...] = (
    "OWNER_GO",
    "validation",
    "authorization",
    "enabled",
    "armed",
    "confirm",
    "SecretRef",
    "account_testnet_binding",
    "risk_ks_emergency",
    "productive_consumer",
    "productive_executor",
    "network_session_entry",
    "first_permitted_TESTNET_effect",
    "campaign_running",
    "evidence",
    "completion_or_abort",
    "seal",
    "canonical_section_11_12_8_closeout",
)

BLOCKER_IDS: tuple[str, ...] = tuple(f"B{i:02d}" for i in range(1, 25))

EVIDENCE_DIRNAME = "capability_11_section_11_12_8_actual_productive_testnet_campaign_run_start_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
ACCEPTANCE_PROOF_FILENAME = "pre_merge_acceptance_gate_proof.json"
CALL_CHAIN_PROOF_FILENAME = "static_productive_call_chain_proof.json"
BLOCKER_MATRIX_FILENAME = "b01_b24_closure_matrix.json"

HIDDEN_CONFIRM_REUSE_OWNER = (
    "ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1"
)
RISK_GATE_REUSE_OWNER = "ops.gates.risk_gate"
KILL_SWITCH_REUSE_OWNER = "risk_layer.kill_switch.core.KillSwitch"
HANDOFF_PREDECESSOR_OWNER = (
    "ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1"
)

# Closeout fields remain false until REAL productive evidence exists.
TESTNET_ORDER_LIFECYCLE_PROVEN = False
TESTNET_RECONCILIATION_PROVEN = False
TESTNET_RESTART_PROVEN = False
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN = False
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN = False
TESTNET_KILL_SWITCH_PROVEN = False
TESTNET_AUTONOMOUS_RECOVERY_PROVEN = False
TESTNET_EVIDENCE_VERIFIED = False

NEXT_OPERATION_AFTER_STUBBED_BOUNDARY = "FIRST_PERMITTED_TESTNET_SIDE_EFFECT"
