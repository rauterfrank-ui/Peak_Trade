"""Constants for Phase 11 productive credential-load reference-only."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_PRODUCTIVE_CREDENTIAL_LOAD_REFERENCE_ONLY_V1"
PACKAGE_MARKER = "CAPABILITY_11_PRODUCTIVE_CREDENTIAL_LOAD_REFERENCE_ONLY_V1=true"
OWNER = "ops.capability_11_productive_credential_load_reference_only_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = (
    "CAPABILITY_11_OWNER_AUTH_ARTIFACT_TESTNET_CREDENTIAL_SCOPE_PRIVATE_NETWORK_V1"
)
PREDECESSOR_OWNER = (
    "ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1"
)
NEXT_CONSUMER_CAPABILITY_ID = "CAPABILITY_11_PRODUCTIVE_PRIVATE_READONLY_FETCH_REFERENCE_ONLY_V1"

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False

# Default fail-closed posture (reference may describe intended object; never loads).
REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT = False
CREDENTIAL_LOAD_PERFORMED = False
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_CONSUMED = False
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
AUTHORIZATION_CONSUMED = False
NETWORK_SESSION_STARTED = False
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
REFERENCE_ONLY = True

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
    "owner_auth_artifact_bound",
    "cap_11_2_credential_load_path_bound",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "authorization_not_consumed",
    "credential_not_consumed",
    "network_session_not_started",
    "order_send_disabled",
    "orders_authorized_false",
    "cap_11_4_not_started",
    "cap_11_13_not_started",
    "no_plaintext_provider_access",
)

EVIDENCE_DIRNAME = "capability_11_productive_credential_load_reference_only_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
