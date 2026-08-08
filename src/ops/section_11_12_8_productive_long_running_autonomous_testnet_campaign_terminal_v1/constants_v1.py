"""Constants for §11.12.8 terminal productive campaign consumer (implementation-only).

This is the SINGLE terminal consumer for Master Runbook §11.12.8.
It is NOT a PATH / EXECUTION / RUN / RUN_ACTIVATION wrapper layer.

Layers (must not be conflated):
  FIXTURE_PROOF = Cap 11 §11.12.8 fixture residual (preserved)
  WRAPPER_RESIDUALS = PATH/EXECUTION/RUN/RUN_ACTIVATION (non-extendable)
  TERMINAL_CONSUMER = this package (architecture terminal; no productive run in this GO)

This OWNER_GO: IMPLEMENTATION_ONLY.
  NO_PRODUCTIVE_RUN / NO_NETWORK_EFFECT / NO_CREDENTIAL_LOAD /
  NO_ORDER_EFFECT / NO_LIVE_EFFECT / NO_§11.13
"""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    CAPABILITY_ID as FIXTURE_CAPABILITY_ID,
    OWNER as FIXTURE_OWNER,
)

CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1"
)
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1=true"
OWNER = "ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1"
CONTRACT_VERSION = "v1"
TERMINAL_CONSUMER_CANONICAL_ROLE = "TERMINAL_PRODUCTIVE_CONSUMER_SECTION_11_12_8"
NEW_WRAPPER_LAYER_REQUIRED = False
NEW_WRAPPER_LAYER_CREATED = False

PREDECESSOR_CAPABILITY_ID = FIXTURE_CAPABILITY_ID
PREDECESSOR_OWNER = FIXTURE_OWNER
# Finite next step: separate Owner-GO for a productive campaign run — not another wrapper.
NEXT_CONSUMER_CAPABILITY_ID = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN"
)

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False
IMPLEMENTATION_ONLY = True

# Reuse owners (must not duplicate).
HIDDEN_CONFIRM_REUSE_OWNER = (
    "ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1"
)
HIDDEN_PTY_REUSE_OWNER = "ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1"
RISK_GATE_REUSE_OWNER = "ops.gates.risk_gate"
KILL_SWITCH_REUSE_OWNER = "risk_layer.kill_switch.core.KillSwitch"
CAP_11_1_PORT_DECLARATION_OWNER = (
    "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1"
)
CAP_11_4_ADAPTER_DECLARATION_OWNER = (
    "ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1"
)

# Terminal claims.
TERMINAL_CONSUMER_IMPLEMENTED = True
TERMINAL_CONSUMER_SURFACE_PRESENT = True
TESTNET_EXECUTION_PORT_CONSTRUCTIBLE = True
TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL = True
CREDENTIAL_LOAD_IMPLEMENTED = True
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_LOAD_PERFORMED = False

# Permanent fail-closed for THIS implementation OWNER_GO.
PRODUCTIVE_RUN_AUTHORIZED = False
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED = False
PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED = False
PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED = False
NETWORK_SESSION_STARTED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
AUTHORIZATION_CONSUMED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
ORDER_SEND_DISABLED = True
ORDERS_AUTHORIZED = False
ORDER_PATH_STARTED = False
ORDER_SUBMIT_PERFORMED = False
MUTATING_EXCHANGE_CALLS = False
NETWORK_WRITES_AUTHORIZED = False
NETWORK_WRITE_PERFORMED = False
NETWORK_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
LIVE_ORDER_EFFECT = "NONE"
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
TESTNET_ORDER_SUBMIT_PERFORMED = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CAPABILITY_11_13_STARTED = False
SECTION_11_13_STARTED = False
CAMPAIGN_SIDE_EFFECTS_AUTHORIZED = False
SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION = False

# Ephemeral enable/arm defaults (must be explicitly true for may_start).
CAMPAIGN_ENABLED_DEFAULT = False
CAMPAIGN_ARMED_DEFAULT = False

CANONICAL_RUNTIME_MODE = "TESTNET"
CANONICAL_VENUE = "OKX"
CANONICAL_INSTRUMENT_SCOPE: tuple[str, ...] = ("BTC-USDT-SWAP",)
CANONICAL_ALLOWED_ORDER_TYPES: tuple[str, ...] = ("LIMIT",)
CANONICAL_POSITION_COUNT_LIMIT = 1
CANONICAL_EMERGENCY_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS

MODE_PROVE_TERMINAL_ONLY = "PROVE_TERMINAL_ONLY"
MODE_GOVERNED_TERMINAL_GATE = "GOVERNED_SECTION_11_12_8_TERMINAL_GATE"
PATH_CLASS = "SECTION_11_12_8_PRODUCTIVE_TERMINAL_CONSUMER"

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "fixture_predecessor_bound",
    "testnet_only_scope",
    "live_path_blocked",
    "credential_scope_testnet",
    "secret_reference_only",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "instrument_scope_within_authority",
    "order_types_within_authority",
    "position_count_within_authority",
    "owner_go_bound",
    "confirm_token_digest_bound",
    "hidden_confirm_channel_bound",
    "campaign_enabled",
    "campaign_armed",
    "risk_gate_allows",
    "kill_switch_operational",
    "emergency_control_operational",
    "testnet_execution_port_constructible",
    "side_effects_unauthorized_in_this_implementation",
    "campaign_not_started",
    "cap_11_13_not_started",
    "network_effect_none",
    "order_effect_none",
    "credential_plaintext_not_loaded",
)

EVIDENCE_DIRNAME = (
    "capability_11_section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1"
)
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
