"""Constants for Phase 11 §11.12.7 kill-switch and emergency control proof."""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1"
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1=true"
OWNER = "ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_6_RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_V1"
)
PREDECESSOR_OWNER = "ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1"
NEXT_CONSUMER_CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1"
)
CAP_11_5_KILL_SWITCH_OWNER = (
    "ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1"
)

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False

# §11.12.7 scoped productive admissions (Owner-GO authorized for this residual only).
KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED = True
CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_ALLOWED = True
SECTION_11_12_6_PREDECESSOR_BINDING_REQUIRED = True

# Hard prohibitions preserved.
ORDER_SEND_DISABLED = True
ORDERS_AUTHORIZED = False
ORDER_PATH_STARTED = False
ORDER_SUBMIT_PERFORMED = False
MUTATING_EXCHANGE_CALLS = False
NETWORK_WRITES_AUTHORIZED = False
NETWORK_WRITE_PERFORMED = False
LIFECYCLE_NETWORK_EFFECT = "NONE"
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
TESTNET_ORDER_SUBMIT_PERFORMED = False
CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED = False
CAPABILITY_11_5_STARTED = False
KILL_SWITCH_CONTRACT_ACTIVATED = False
SECTION_11_12_8_STARTED = False
CAPABILITY_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
TESTNET_ORDER_LIFECYCLE_PROVEN = False
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN = False
TESTNET_RESTART_PROVEN = False
TESTNET_KILL_SWITCH_PROVEN = False

# §11.9 contract properties (fixture declarations; not activated / not Testnet-proven).
KILL_SWITCH_PERSISTED = True
KILL_SWITCH_FAIL_CLOSED = True
KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT = True
KILL_SWITCH_SURVIVES_RESTART = True
KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME = True
OWNER_AUTHORITY_REQUIRED_TO_CLEAR = True
CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA = True
EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA = True

LIFECYCLE_SOURCE_REQUIRED = "FIXTURE_ONLY"
EXECUTION_MODE_REQUIRED = "TESTNET"
PATH_CLASS = "KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF"
ALLOWED_SECTION_11_12_7_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS
FORBIDDEN_SECTION_11_12_8_PATHS: tuple[str, ...] = ("long_running_autonomous_campaign",)

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "section_11_12_6_predecessor_bound",
    "cap_11_5_kill_switch_and_emergency_control_contract_reused",
    "kill_switch_and_emergency_control_proof_allowed",
    "order_send_disabled",
    "orders_authorized_false",
    "network_writes_unauthorized",
    "network_effect_none",
    "cap_11_5_adapter_not_activated",
    "kill_switch_contract_not_activated",
    "section_11_12_8_not_started",
    "cap_11_13_not_started",
    "owner_go_kill_switch_emergency_control_authorized",
)

EVIDENCE_DIRNAME = "capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
