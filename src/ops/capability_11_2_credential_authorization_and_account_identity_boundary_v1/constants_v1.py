"""Constants for CAPABILITY_11_2 credential/authorization/account-identity boundary."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_2_CREDENTIAL_AUTHORIZATION_AND_ACCOUNT_IDENTITY_BOUNDARY_V1"
PACKAGE_MARKER = "CAPABILITY_11_2_CREDENTIAL_AUTHORIZATION_AND_ACCOUNT_IDENTITY_BOUNDARY_V1=true"
OWNER = "ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1"
AUTHORITY_OWNER = OWNER
SCHEMA_VERSION = "capability_11_2_credential_authorization_and_account_identity_boundary.v1"
PRODUCER_VERSION = "capability_11_2_credential_authorization_and_account_identity_boundary.v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_11_1_EXECUTION_DOMAIN_AND_ORDER_LIFECYCLE_CONTRACTS_V1"
PREDECESSOR_OWNER = "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1"

# Hard safety bindings (boundary contracts/scaffolding only; non-authorizing).
CORE_LOGIC_CHANGE = False
CORE_LOGIC_CHANGE_ALLOWED = False
ACTIVATION_STATE = "not_activated"
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_TRADING_ALLOWED = False
TESTNET_ALLOWED = False
PAPER_EXCHANGE_ORDERS_ALLOWED = False
EXCHANGE_CREDENTIAL_USE_ALLOWED = False
REAL_CAPITAL_MOVEMENT_ALLOWED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
RULESET_MUTATION_ALLOWED = False
NOTION_MUTATION_ALLOWED = False

TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXCHANGE_CREDENTIAL_USE_AUTHORIZED = False
REAL_CAPITAL_MOVEMENT_AUTHORIZED = False
OWNER_GO_REQUIRED_FOR_EACH_ACTIVATION = True

LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_STARTED = False

VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
NUMERIC_MAX_AGE_EFFECT = "DIAGNOSTIC_ONLY"

# Cap 11.1 contracts that must not be weakened.
CAPABILITY_11_1_FAIL_CLOSED_RETAINED = True
CAPABILITY_11_1_IDEMPOTENCY_RETAINED = True
CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED = True
CAPABILITY_11_1_LIFECYCLE_RETAINED = True
CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED = True

# Reachability claims for Cap 11.2 (boundary only — no real credential use).
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
REAL_CAPITAL_MOVEMENT_REACHABLE = False
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2 = False

# Credential contract (§11.6).
LEAST_PRIVILEGE = True
WITHDRAWAL_PERMISSION = False
ACCOUNT_SCOPE_EXPLICIT = True
VENUE_SCOPE_EXPLICIT = True
INSTRUMENT_SCOPE_EXPLICIT = True
IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED = True
SECRET_REFERENCE_ONLY_IN_CONFIG = True
PLAINTEXT_SECRET_NEVER_PERSISTED = True
ROTATION_SUPPORTED = True
REVOCATION_DETECTED = True
CREDENTIAL_FAILURE_FAILS_CLOSED = True

# Plaintext / secret material (§11.3).
FORBIDDEN_TO_PERSIST = True
FORBIDDEN_IN_LOGS = True
FORBIDDEN_IN_PROCESS_ARGUMENTS = True
FORBIDDEN_IN_EVIDENCE = True

# Autonomy scope limits (§11.6).
AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED = True
AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION = False
AUTONOMOUS_CAPITAL_LIMIT_INCREASE = False
AUTONOMOUS_VENUE_ENABLEMENT = False
AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION = False

REQUIRED_AUTHORIZATION_BINDINGS: tuple[str, ...] = (
    "repository_sha",
    "config_digest",
    "runtime_mode",
    "venue",
    "account_identity",
    "instrument_or_active_set_scope",
    "maximum_notional",
    "maximum_leverage",
    "maximum_position_count",
    "maximum_session_duration",
    "loss_and_drawdown_limits",
    "allowed_order_types",
    "allowed_side_effects",
    "activation_epoch",
    "expiry",
)

CREDENTIAL_LOAD_PREREQUISITES: tuple[str, ...] = (
    "mode_validated",
    "authorization_validated",
    "repository_sha_validated",
    "config_digest_validated",
    "account_identity_validated",
    "venue_scope_validated",
)

CREDENTIAL_REFERENCE_METADATA_OWNER = OWNER
AUTHORIZATION_CONTRACT_OWNER = OWNER
ACCOUNT_IDENTITY_BOUNDARY_OWNER = OWNER

EVIDENCE_DIRNAME = "capability_11_2_credential_authorization_and_account_identity_boundary_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
