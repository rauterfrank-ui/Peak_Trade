"""Constants for Phase 11 §11.12.1 productive private-readonly API and account identity."""

from __future__ import annotations

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS,
    PRIVATE_READONLY_GET_ENDPOINTS,
)

CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_1_PRODUCTIVE_PRIVATE_READONLY_API_AND_ACCOUNT_IDENTITY_V1"
)
PACKAGE_MARKER = (
    "CAPABILITY_11_SECTION_11_12_1_PRODUCTIVE_PRIVATE_READONLY_API_AND_ACCOUNT_IDENTITY_V1=true"
)
OWNER = "ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_11_PRODUCTIVE_PRIVATE_READONLY_FETCH_REFERENCE_ONLY_V1"
PREDECESSOR_OWNER = "ops.capability_11_productive_private_readonly_fetch_reference_only_v1"
NEXT_CONSUMER_CAPABILITY_ID = "CAPABILITY_11_SECTION_11_12_2_ORDER_SERIALIZATION_DRY_RUN_V1"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False
REFERENCE_ONLY = False

# §11.12.1 scoped productive admissions (Owner-GO authorized for this residual only).
AUTHORIZATION_CONSUMPTION_ALLOWED = True
PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED = True
PRIVATE_READONLY_NETWORK_SESSION_ALLOWED = True
ACCOUNT_IDENTITY_FETCH_ALLOWED = True

# Hard prohibitions preserved.
ORDER_SEND_DISABLED = True
ORDERS_AUTHORIZED = False
ORDER_PATH_STARTED = False
MUTATING_EXCHANGE_CALLS = False
NETWORK_WRITES_AUTHORIZED = False
NETWORK_WRITE_PERFORMED = False
CAPABILITY_11_4_STARTED = False
CAPABILITY_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
LIVE_AUTHORIZED = False

# Package defaults before a governed execution (fail-closed until execute succeeds).
AUTHORIZATION_CONSUMED_DEFAULT = False
CREDENTIAL_CONSUMED_DEFAULT = False
NETWORK_SESSION_STARTED_DEFAULT = False
ACCOUNT_IDENTITY_FETCH_PERFORMED_DEFAULT = False
PRIVATE_READONLY_NETWORK_REACHABLE_DEFAULT = False

LEAST_PRIVILEGE = True
WITHDRAWAL_PERMISSION = False
PLAINTEXT_SECRET_FORBIDDEN = True
SECRET_REFERENCE_ONLY = True
TESTNET_ONLY_SCOPE_REQUIRED = True
PRIVATE_READONLY_GET_ONLY = True

# This residual fetches account-identity only (subset of Cap 11.3 GET allowlist).
ACCOUNT_IDENTITY_ENDPOINT = "accounts"
ACCOUNT_IDENTITY_HTTP_METHOD = "GET"
ACCOUNT_IDENTITY_PATH_CLASS = "PRIVATE_READONLY_ACCOUNT_IDENTITY"
ALLOWED_HTTP_METHODS: tuple[str, ...] = ("GET",)
SECTION_11_12_1_ALLOWED_ENDPOINTS: tuple[str, ...] = (ACCOUNT_IDENTITY_ENDPOINT,)

PRIVATE_READONLY_GET_ALLOWLIST: tuple[str, ...] = PRIVATE_READONLY_GET_ENDPOINTS
PRIVATE_READONLY_FORBIDDEN_MUTATIONS: tuple[str, ...] = PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS
FORBIDDEN_HTTP_METHODS: tuple[str, ...] = (
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "CONNECT",
    "TRACE",
)

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "least_privilege",
    "withdrawal_permission_false",
    "plaintext_secret_absent",
    "secret_reference_only",
    "credential_ref_id_bound",
    "fetch_reference_only_predecessor_bound",
    "owner_auth_artifact_bound",
    "credential_load_reference_only_bound",
    "cap_11_3_productive_private_readonly_path_bound",
    "get_only_allowlist_bound",
    "section_endpoint_accounts_only",
    "mutation_endpoints_absent",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "order_send_disabled",
    "orders_authorized_false",
    "network_writes_unauthorized",
    "cap_11_4_not_started",
    "cap_11_13_not_started",
    "owner_go_auth_consume_authorized",
    "owner_go_credential_consume_authorized",
    "owner_go_private_readonly_network_authorized",
    "owner_go_account_identity_fetch_authorized",
)

EVIDENCE_DIRNAME = (
    "capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1"
)
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
TRANSPORT_CLASS_GOVERNED_FIXTURE = "GOVERNED_FIXTURE_PRIVATE_READONLY_GET_V1"
