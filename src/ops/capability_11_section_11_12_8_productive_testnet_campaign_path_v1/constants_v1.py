"""Constants for §11.12.8 productive Testnet campaign PATH (implementation only).

Distinct layers (must not be conflated):
  FIXTURE_PROOF = Cap 11 §11.12.8 fixture-only campaign evidence (predecessor)
  PRODUCTIVE_TESTNET_CAPABILITY = this path package (gates present; no execution)
  PRODUCTIVE_TESTNET_EXECUTION = later separate Owner-GO campaign run (out of scope)
"""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    ALLOWED_SECTION_11_12_8_PATHS as FIXTURE_ALLOWED_PATHS,
    CAPABILITY_ID as FIXTURE_CAPABILITY_ID,
    KILL_SWITCH_BINDING_STATUS as FIXTURE_KILL_SWITCH_BINDING_STATUS,
    OWNER as FIXTURE_OWNER,
)

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_PATH_V1"
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_TESTNET_CAMPAIGN_PATH_V1=true"
OWNER = "ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1"
CONTRACT_VERSION = "v1"

# Historical wrapper residual — do not extend with further PATH/EXEC/RUN layers.
NON_EXTENDABLE_WRAPPER_RESIDUAL = True
DEPRECATED_AS_NON_CANONICAL_WRAPPER = True
WRAPPER_LOOP_TERMINATION_POINT = "TERMINAL_PRODUCTIVE_CONSUMER_SECTION_11_12_8"
TERMINAL_CONSUMER_CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_TERMINAL_V1"
)

PREDECESSOR_CAPABILITY_ID = FIXTURE_CAPABILITY_ID
PREDECESSOR_OWNER = FIXTURE_OWNER
NEXT_CONSUMER_CAPABILITY_ID = "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_TESTNET_CAMPAIGN_EXECUTION"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False

# Layer separation claims.
FIXTURE_PROOF_PRESERVED = True
PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED = True
PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED = False
PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT = True
PRODUCTIVE_TESTNET_CAMPAIGN_PATH_ABSENT = False

# Permanent fail-closed — this OWNER_GO authorizes path implementation only.
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
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
TESTNET_ORDER_SUBMIT_PERFORMED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CAPABILITY_11_13_STARTED = False
SECTION_11_13_STARTED = False
KILL_SWITCH_CONTRACT_ACTIVATED = False

# Defaults for ephemeral enable/arm (must be explicitly true for may_start).
CAMPAIGN_ENABLED_DEFAULT = False
CAMPAIGN_ARMED_DEFAULT = False

# Canonical authority reuse (no expansion beyond bound §11.12.x / Cap 11.4/11.5).
CANONICAL_RUNTIME_MODE = "TESTNET"
CANONICAL_VENUE = "OKX"
CANONICAL_INSTRUMENT_SCOPE: tuple[str, ...] = ("BTC-USDT-SWAP",)
CANONICAL_ALLOWED_ORDER_TYPES: tuple[str, ...] = ("LIMIT",)
CANONICAL_POSITION_COUNT_LIMIT = 1
CANONICAL_EMERGENCY_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS
FIXTURE_ALLOWED_CAMPAIGN_EVIDENCE_PATHS: tuple[str, ...] = FIXTURE_ALLOWED_PATHS
KILL_SWITCH_BINDING_STATUS_REQUIRED = FIXTURE_KILL_SWITCH_BINDING_STATUS

KILL_SWITCH_PERSISTED = True
KILL_SWITCH_FAIL_CLOSED = True
KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT = True
KILL_SWITCH_SURVIVES_RESTART = True
KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME = True
OWNER_AUTHORITY_REQUIRED_TO_CLEAR = True
CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA = True
EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA = True

PATH_CLASS = "PRODUCTIVE_TESTNET_CAMPAIGN_PATH"
MODE_PROVE_PATH_ONLY = "PROVE_PATH_ONLY"
MODE_GOVERNED_START_GATE = "GOVERNED_PRODUCTIVE_CAMPAIGN_START_GATE"

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
    "PEAK_TRADE_11_12_8_CONFIRM_TOKEN",
    "PEAK_TRADE_PRODUCTIVE_11_12_8_CONFIRM_TOKEN",
)

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "fixture_predecessor_bound",
    "testnet_only_scope",
    "live_path_blocked",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_within_authority",
    "order_types_within_authority",
    "position_count_within_authority",
    "credential_scope_testnet",
    "secret_reference_only",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "owner_authorization_bound",
    "confirm_token_digest_bound",
    "campaign_enabled",
    "campaign_armed",
    "kill_switch_operational",
    "emergency_control_operational",
    "order_send_disabled_default",
    "orders_unauthorized_default",
    "network_writes_unauthorized",
    "network_effect_none",
    "campaign_not_started",
    "execution_not_authorized",
    "cap_11_13_not_started",
)

EVIDENCE_DIRNAME = "capability_11_section_11_12_8_productive_testnet_campaign_path_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
