"""Constants for Cap 11.2 productive credential-load path binding."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_2_PRODUCTIVE_CREDENTIAL_LOAD_PATH_BINDING_V1"
PACKAGE_MARKER = "CAPABILITY_11_2_PRODUCTIVE_CREDENTIAL_LOAD_PATH_BINDING_V1=true"
OWNER = "ops.capability_11_2_productive_credential_load_path_binding_v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = (
    "CAPABILITY_11_2_CREDENTIAL_AUTHORIZATION_AND_ACCOUNT_IDENTITY_BOUNDARY_V1"
)
PREDECESSOR_OWNER = "ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1"
NEXT_CONSUMER_CAPABILITY_ID = (
    "CAPABILITY_11_3_PRIVATE_READONLY_VENUE_INTEGRATION_AND_RECONCILIATION_V1"
)

CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "not_activated"
RUNTIME_ACTIVATED = False

# Default fail-closed posture.
CREDENTIAL_LOAD_ALLOWED_DEFAULT = False
CREDENTIAL_LOAD_PERFORMED = False
CREDENTIAL_PLAINTEXT_LOADED = False
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
EXCHANGE_CREDENTIAL_USE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
NETWORK_SESSION_STARTED = False
CAPABILITY_11_3_STARTED = False
CAPABILITY_11_3_PRIVATE_READONLY_STARTED = False
CAPABILITY_11_13_STARTED = False
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False

LEAST_PRIVILEGE = True
WITHDRAWAL_PERMISSION = False
PLAINTEXT_SECRET_FORBIDDEN = True
SECRET_REFERENCE_ONLY = True
TESTNET_ONLY_SCOPE_REQUIRED = True

REQUIRED_PRECONDITIONS: tuple[str, ...] = (
    "testnet_only_scope",
    "venue_explicit",
    "account_identity_explicit",
    "instrument_scope_explicit",
    "least_privilege",
    "withdrawal_permission_false",
    "plaintext_secret_absent",
    "secret_reference_only",
    "exchange_credential_use_authorized",
    "testnet_authorized",
    "repository_sha_bound",
    "config_digest_bound",
    "account_identity_bound",
    "venue_bound",
    "cap_11_2_load_gate_prerequisites",
    "cap_11_3_not_started",
    "network_session_not_started",
    "no_plaintext_provider_access",
)

EVIDENCE_DIRNAME = "capability_11_2_productive_credential_load_path_binding_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
