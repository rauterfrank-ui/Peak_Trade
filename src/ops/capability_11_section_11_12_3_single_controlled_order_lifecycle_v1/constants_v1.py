"""Constants for Phase 11 §11.12.3 single controlled order lifecycle."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_3_SINGLE_CONTROLLED_ORDER_LIFECYCLE_V1"
PACKAGE_MARKER = "CAPABILITY_11_SECTION_11_12_3_SINGLE_CONTROLLED_ORDER_LIFECYCLE_V1=true"
OWNER = "ops.capability_11_section_11_12_3_single_controlled_order_lifecycle_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_2_ORDER_SERIALIZATION_DRY_RUN_V1"
PREDECESSOR_OWNER = "ops.capability_11_section_11_12_2_order_serialization_dry_run_v1"
NEXT_CONSUMER_CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_4_ENTRY_PARTIAL_FILL_CANCEL_EXIT_LIFECYCLES_V1"
)
CAP_11_4_LIFECYCLE_OWNER = "ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False

# §11.12.3 scoped productive admissions (Owner-GO authorized for this residual only).
SINGLE_CONTROLLED_ORDER_LIFECYCLE_ALLOWED = True
CAP_11_4_SINGLE_CONTROLLED_LIFECYCLE_CONTRACT_REUSE_ALLOWED = True
SECTION_11_12_2_PREDECESSOR_BINDING_REQUIRED = True

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
CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED = False
CAPABILITY_11_4_STARTED = False
SECTION_11_12_4_STARTED = False
CAPABILITY_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
TESTNET_ORDER_LIFECYCLE_PROVEN = False

LIFECYCLE_SOURCE_REQUIRED = "FIXTURE_ONLY"
EXECUTION_MODE_REQUIRED = "TESTNET"
PATH_CLASS = "SINGLE_CONTROLLED_ORDER_LIFECYCLE"
LIFECYCLE_PATH_NAME = "single_controlled_order_lifecycle"
FORBIDDEN_SECTION_11_12_4_PATHS: tuple[str, ...] = (
    "entry_lifecycle",
    "partial_fill_lifecycle",
    "cancel_lifecycle",
    "exit_lifecycle",
)

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "section_11_12_2_predecessor_bound",
    "cap_11_4_single_controlled_lifecycle_contract_reused",
    "single_controlled_order_lifecycle_allowed",
    "order_send_disabled",
    "orders_authorized_false",
    "network_writes_unauthorized",
    "network_effect_none",
    "cap_11_4_adapter_not_activated",
    "section_11_12_4_not_started",
    "cap_11_13_not_started",
    "owner_go_single_controlled_order_lifecycle_authorized",
)

EVIDENCE_DIRNAME = "capability_11_section_11_12_3_single_controlled_order_lifecycle_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
