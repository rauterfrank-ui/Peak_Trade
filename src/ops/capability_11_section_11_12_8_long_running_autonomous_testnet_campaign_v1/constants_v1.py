"""Constants for Phase 11 §11.12.8 long-running autonomous Testnet campaign."""

from __future__ import annotations

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS as CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS,
    TESTNET_CLOSURE_EVIDENCE_FIELDS as CAP_11_6_TESTNET_CLOSURE_EVIDENCE_FIELDS,
)

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1"
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_8_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_V1=true"
OWNER = "ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_7_KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_V1"
)
PREDECESSOR_OWNER = "ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1"
NEXT_CONSUMER_CAPABILITY_ID = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_TESTNET_CAMPAIGN_OR_CAPABILITY_11_13"
)
CAP_11_6_CAMPAIGN_EVIDENCE_OWNER = "ops.capability_11_6_long_running_autonomous_testnet_evidence_v1"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False

# §11.12.8 scoped admissions (Owner-GO authorizes implementation residual only).
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED = True
CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_ALLOWED = True
SECTION_11_12_7_PREDECESSOR_BINDING_REQUIRED = True
KILL_SWITCH_BINDING_REQUIRED = True

# Hard prohibitions preserved — this OWNER_GO does NOT authorize productive campaign.
ORDER_SEND_DISABLED = True
ORDERS_AUTHORIZED = False
ORDER_PATH_STARTED = False
ORDER_SUBMIT_PERFORMED = False
MUTATING_EXCHANGE_CALLS = False
NETWORK_WRITES_AUTHORIZED = False
NETWORK_WRITE_PERFORMED = False
LIFECYCLE_NETWORK_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
TESTNET_ORDER_SUBMIT_PERFORMED = False
TESTNET_CAMPAIGN_STARTED = False
TESTNET_CAMPAIGN_COMPLETED = False
LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED = False
CAPABILITY_11_6_STARTED = False
CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED = False
CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED = False
CAPABILITY_11_5_STARTED = False
KILL_SWITCH_CONTRACT_ACTIVATED = False
CAPABILITY_11_13_STARTED = False
SECTION_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_SESSION_STARTED = False
TESTNET_ORDER_LIFECYCLE_PROVEN = False
TESTNET_RECONCILIATION_PROVEN = False
TESTNET_RESTART_PROVEN = False
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN = False
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN = False
TESTNET_KILL_SWITCH_PROVEN = False
TESTNET_AUTONOMOUS_RECOVERY_PROVEN = False
TESTNET_EVIDENCE_VERIFIED = False

# Kill-switch binding retained from closed §11.12.7 (not activated / not proven).
KILL_SWITCH_BINDING_STATUS = "BOUND"
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
PATH_CLASS = "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE"
ALLOWED_SECTION_11_12_8_PATHS: tuple[str, ...] = CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS
FORBIDDEN_CAPABILITY_11_13_PATHS: tuple[str, ...] = (
    "live_activation",
    "live_canary",
    "live_shadow",
)
TESTNET_CLOSURE_EVIDENCE_FIELDS: tuple[str, ...] = CAP_11_6_TESTNET_CLOSURE_EVIDENCE_FIELDS

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "section_11_12_7_predecessor_bound",
    "kill_switch_binding_bound",
    "cap_11_6_long_running_campaign_evidence_contract_reused",
    "long_running_autonomous_testnet_campaign_evidence_allowed",
    "order_send_disabled",
    "orders_authorized_false",
    "network_writes_unauthorized",
    "network_effect_none",
    "testnet_campaign_not_started",
    "testnet_campaign_not_completed",
    "campaign_not_activated",
    "cap_11_6_adapter_not_activated",
    "kill_switch_contract_not_activated",
    "cap_11_13_not_started",
    "owner_go_long_running_campaign_evidence_authorized",
)

EVIDENCE_DIRNAME = "capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
