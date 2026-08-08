"""Constants for §11.12.8 productive campaign RUN CONSUMER (implementation-only).

This package is the missing executable consumer surface after the terminal
consumer. It does NOT reinterpret the terminal as a productive runner.

This OWNER_GO: IMPLEMENTATION_ONLY_FOR_MISSING_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER
  NO_PRODUCTIVE_RUN_EXECUTION / NO_NETWORK_EFFECT / NO_CREDENTIAL_LOAD /
  NO_ORDER_EFFECT / NO_LIVE_EFFECT / NO_§11.13

Productive campaign execution requires a later separate Owner-GO.
"""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    CAPABILITY_ID as TERMINAL_CAPABILITY_ID,
    OWNER as TERMINAL_OWNER,
    TERMINAL_CONSUMER_CANONICAL_ROLE as TERMINAL_ROLE,
)

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1"
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1=true"
OWNER = "ops.section_11_12_8_productive_campaign_run_consumer_v1"
CONTRACT_VERSION = "v1"
PATH_CLASS = "SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER"
RUN_CONSUMER_CANONICAL_ROLE = "PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER"

PREDECESSOR_CAPABILITY_ID = TERMINAL_CAPABILITY_ID
PREDECESSOR_OWNER = TERMINAL_OWNER
TERMINAL_PREDECESSOR_ROLE = TERMINAL_ROLE
# Finite next step: separate Owner-GO for productive run activation/execution.
NEXT_CONSUMER_CAPABILITY_ID = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_ACTIVATION"
)

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False
IMPLEMENTATION_ONLY = True
NEW_WRAPPER_LAYER_CREATED = False

# Consumer surface claims.
PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED = True
PRODUCTIVE_RUN_CONSUMER_PRESENT = True
PRODUCTIVE_RUN_CONSUMER_ABSENT = False
PRODUCTIVE_RUN_EXECUTION_AUTHORIZED = False
PRODUCTIVE_RUN_EXECUTION_AUTHORIZED_IN_THIS_IMPLEMENTATION = False

# Permanent fail-closed for THIS implementation OWNER_GO.
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
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_LOAD_PERFORMED = False

# Ephemeral enable/arm defaults (must be explicitly true for structural may_arm).
CAMPAIGN_ENABLED_DEFAULT = False
CAMPAIGN_ARMED_DEFAULT = False

CANONICAL_RUNTIME_MODE = "TESTNET"
CANONICAL_VENUE = "OKX"
CANONICAL_INSTRUMENT_SCOPE: tuple[str, ...] = ("BTC-USDT-SWAP",)
CANONICAL_ALLOWED_ORDER_TYPES: tuple[str, ...] = ("LIMIT",)
CANONICAL_POSITION_COUNT_LIMIT = 1
CANONICAL_EMERGENCY_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS

MODE_PROVE_RUN_CONSUMER_ONLY = "PROVE_RUN_CONSUMER_ONLY"
MODE_GOVERNED_RUN_CONSUMER_GATE = "GOVERNED_SECTION_11_12_8_RUN_CONSUMER_GATE"

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "terminal_predecessor_bound",
    "terminal_role_unchanged",
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
    "execution_unauthorized_in_this_implementation",
    "campaign_not_started",
    "cap_11_13_not_started",
    "network_effect_none",
    "order_effect_none",
    "credential_plaintext_not_loaded",
)

EVIDENCE_DIRNAME = "capability_11_section_11_12_8_productive_campaign_run_consumer_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
