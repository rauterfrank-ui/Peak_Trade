"""Constants for §11.12.8 productive campaign RUN ACTIVATION + executable handoff.

OWNER_GO: CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1
SCOPE: IMPLEMENTATION_ONLY_WITH_END_TO_END_DRY_ACTIVATION_PROOF

This package closes the complete statically discoverable non-executable/missing
blocker set for the §11.12.8 activation path. It does NOT authorize a productive
Testnet campaign run, network session, orders, credential plaintext load, or §11.13.
"""

from __future__ import annotations

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    EMERGENCY_COMMANDS as CAP_11_5_EMERGENCY_COMMANDS,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (
    CAPABILITY_ID as RUN_CONSUMER_CAPABILITY_ID,
    OWNER as RUN_CONSUMER_OWNER,
    RUN_CONSUMER_CANONICAL_ROLE,
)

CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1"
)
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1=true"
OWNER = "ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1"
CONTRACT_VERSION = "v1"
PATH_CLASS = "SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF"
ACTIVATION_EXECUTOR_CANONICAL_ROLE = (
    "PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF"
)

SCOPED_OWNER_GO_TOKEN = (
    "CAPABILITY_11_SECTION_11_12_8_PRODUCTIVE_CAMPAIGN_RUN_ACTIVATION_AND_EXECUTABLE_HANDOFF_V1"
)
SCOPED_OWNER_GO_SCOPE = "IMPLEMENTATION_ONLY_WITH_END_TO_END_DRY_ACTIVATION_PROOF"

PREDECESSOR_CAPABILITY_ID = RUN_CONSUMER_CAPABILITY_ID
PREDECESSOR_OWNER = RUN_CONSUMER_OWNER
RUN_CONSUMER_ROLE = RUN_CONSUMER_CANONICAL_ROLE
NEXT_CONSUMER_CAPABILITY_ID = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START"
)

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "implementation_only_dry_activation_proof"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False
IMPLEMENTATION_ONLY = True
NEW_WRAPPER_LAYER_CREATED = False
DEPRECATED_NON_EXTENDABLE = False

# Defaults remain fail-closed.
CAMPAIGN_ENABLED_DEFAULT = False
CAMPAIGN_ARMED_DEFAULT = False
AUTHORIZATION_STATE_DEFAULT = "UNAUTHORIZED"

# Permanent safety claims for this OWNER_GO.
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED = False
PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED = False
PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED = False
NETWORK_SESSION_STARTED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = True  # scoped OWNER_GO may be consumed for dry proof
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
TESTNET_AUTHORIZED = False  # productive Testnet campaign run remains unauthorized
CAPABILITY_11_13_STARTED = False
SECTION_11_13_STARTED = False
CAMPAIGN_SIDE_EFFECTS_AUTHORIZED = False
SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION = False
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_LOAD_PERFORMED = False

CANONICAL_RUNTIME_MODE = "TESTNET"
CANONICAL_VENUE = "OKX"
CANONICAL_INSTRUMENT_SCOPE: tuple[str, ...] = ("BTC-USDT-SWAP",)
CANONICAL_ALLOWED_ORDER_TYPES: tuple[str, ...] = ("LIMIT",)
CANONICAL_POSITION_COUNT_LIMIT = 1
CANONICAL_EMERGENCY_COMMANDS: tuple[str, ...] = CAP_11_5_EMERGENCY_COMMANDS
CANONICAL_SECRET_REFERENCE = "secretref://vault/peak-trade/testnet-demo"
CANONICAL_ACCOUNT_IDENTITY = "acct-uid-testnet-demo"

MODE_DRY_ACTIVATION_PROOF = "END_TO_END_DRY_ACTIVATION_PROOF"
MODE_ABORT_DRY_ACTIVATION = "ABORT_DRY_ACTIVATION"
MODE_COMPLETE_DRY_ACTIVATION = "COMPLETE_DRY_ACTIVATION"

AUTHORIZATION_STATE_UNAUTHORIZED = "UNAUTHORIZED"
AUTHORIZATION_STATE_AUTHORIZED = "AUTHORIZED"

DURABLE_STATE_SCHEMA = "section_11_12_8_campaign_durable_state.v1"
DURABLE_STATE_FILENAME = "campaign_durable_state_v1.json"

COMPLETE_BLOCKER_IDS: tuple[str, ...] = (
    "1_scoped_OWNER_GO_consumer",
    "2_non_deprecated_activation_executor",
    "3_authorization_state_transition",
    "4_durable_campaign_enabled_state",
    "5_durable_campaign_armed_state",
    "8_SecretRef_only_credential_path",
    "9_productive_testnet_account_binding",
    "18_PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1_authorization_handoff",
    "19_network_session_entry_boundary",
    "22_execution_evidence_production",
    "23_evidence_sealing",
    "24_campaign_completion_abort_handling",
)

PRESERVED_EXECUTABLE_CONTROLS: tuple[str, ...] = (
    "6_hidden_confirm_channel",
    "7_confirm_token_digest_binding",
    "10_config_digest_binding",
    "11_venue_binding",
    "12_instrument_authority_binding",
    "13_order_type_authority_binding",
    "14_max_position_authority_binding",
    "15_risk_gate_productive_invocation",
    "16_KillSwitch_productive_invocation",
    "17_emergency_control_productive_invocation",
    "20_testnet_only_enforcement",
    "21_live_path_hard_block",
    "25_section_11_13_isolation",
)

EVIDENCE_DIRNAME = (
    "capability_11_section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1"
)
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
DRY_PROOF_FILENAME = "end_to_end_dry_activation_proof.json"
