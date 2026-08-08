"""Constants for Phase 11 Owner Auth Artifact (Testnet + credential + private network)."""

from __future__ import annotations

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS,
    PRIVATE_READONLY_GET_ENDPOINTS,
)

CAPABILITY_ID = "CAPABILITY_11_OWNER_AUTH_ARTIFACT_TESTNET_CREDENTIAL_SCOPE_PRIVATE_NETWORK_V1"
PACKAGE_MARKER = (
    "CAPABILITY_11_OWNER_AUTH_ARTIFACT_TESTNET_CREDENTIAL_SCOPE_PRIVATE_NETWORK_V1=true"
)
OWNER = "ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_11_3_PRODUCTIVE_PRIVATE_READONLY_PATH_BINDING_V1"
PREDECESSOR_OWNER = "ops.capability_11_3_productive_private_readonly_path_binding_v1"
NEXT_CONSUMER_CAPABILITY_ID = "CAPABILITY_11_PRODUCTIVE_CREDENTIAL_LOAD_REFERENCE_ONLY_V1"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False

# Default fail-closed posture (artifact may describe future admission; runtime stays closed).
OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT = False
OWNER_AUTH_ARTIFACT_ISSUED = False
AUTHORIZATION_CONSUMED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
NETWORK_SESSION_STARTED = False
CREDENTIAL_LOAD_PERFORMED = False
CREDENTIAL_PLAINTEXT_LOADED = False
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
ORDER_SEND_DISABLED = True
ORDERS_AUTHORIZED = False
ORDER_PATH_STARTED = False
MUTATING_EXCHANGE_CALLS = False
CAPABILITY_11_4_STARTED = False
CAPABILITY_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False

# Package-level runtime authorization remains false until a later consuming step.
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXCHANGE_CREDENTIAL_USE_AUTHORIZED = False

LEAST_PRIVILEGE = True
WITHDRAWAL_PERMISSION = False
PLAINTEXT_SECRET_FORBIDDEN = True
SECRET_REFERENCE_ONLY = True
TESTNET_ONLY_SCOPE_REQUIRED = True

NETWORK_SCOPE_REQUIRED = "PRIVATE_READONLY_GET_ONLY"
PRIVATE_READONLY_GET_ALLOWLIST: tuple[str, ...] = PRIVATE_READONLY_GET_ENDPOINTS
PRIVATE_READONLY_FORBIDDEN_MUTATIONS: tuple[str, ...] = PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS
ALLOWED_SIDE_EFFECTS_REQUIRED: tuple[str, ...] = ("private_readonly_get",)
# Cap 11.2 binding forbids empty tuples; "NONE" is the order-send-disabled sentinel.
ALLOWED_ORDER_TYPES_REQUIRED: tuple[str, ...] = ("NONE",)

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "least_privilege",
    "withdrawal_permission_false",
    "plaintext_secret_absent",
    "secret_reference_only",
    "artifact_testnet_authorized",
    "artifact_exchange_credential_use_authorized",
    "artifact_network_session_authorized_private_readonly",
    "order_send_disabled",
    "orders_authorized_false",
    "allowed_order_types_none_only",
    "allowed_side_effects_private_readonly_get_only",
    "network_scope_private_readonly_get_only",
    "get_only_allowlist_bound",
    "mutation_endpoints_absent",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "cap_11_2_credential_load_path_bound",
    "cap_11_3_productive_private_readonly_path_bound",
    "authorization_not_consumed",
    "network_session_not_started",
    "cap_11_4_not_started",
    "cap_11_13_not_started",
    "no_plaintext_provider_access",
)

EVIDENCE_DIRNAME = "capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
