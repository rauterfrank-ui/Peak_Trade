"""Constants for CAPABILITY_11_3 private read-only venue integration and reconciliation."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_3_PRIVATE_READONLY_VENUE_INTEGRATION_AND_RECONCILIATION_V1"
PACKAGE_MARKER = "CAPABILITY_11_3_PRIVATE_READONLY_VENUE_INTEGRATION_AND_RECONCILIATION_V1=true"
OWNER = "ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1"
AUTHORITY_OWNER = OWNER
SCHEMA_VERSION = "capability_11_3_private_readonly_venue_integration_and_reconciliation.v1"
PRODUCER_VERSION = "capability_11_3_private_readonly_venue_integration_and_reconciliation.v1"
CONTRACT_VERSION = "v1"

PREDECESSOR_CAPABILITY_ID_11_1 = "CAPABILITY_11_1_EXECUTION_DOMAIN_AND_ORDER_LIFECYCLE_CONTRACTS_V1"
PREDECESSOR_OWNER_11_1 = "ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1"
PREDECESSOR_CAPABILITY_ID_11_2 = (
    "CAPABILITY_11_2_CREDENTIAL_AUTHORIZATION_AND_ACCOUNT_IDENTITY_BOUNDARY_V1"
)
PREDECESSOR_OWNER_11_2 = (
    "ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1"
)

# Hard safety bindings (contracts/scaffolding only; non-authorizing).
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
CAPABILITY_11_1_ANTI_CORRUPTION_RETAINED = True
CAPABILITY_11_1_JOURNALING_RETAINED = True

# Cap 11.2 contracts that must not be weakened.
CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED = True
CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED = True
CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED = True
CAPABILITY_11_2_NO_CREDENTIAL_LOAD_RETAINED = True
CAPABILITY_11_2_NO_AUTH_CONSUMPTION_RETAINED = True

# Reachability claims for Cap 11.3 (contracts only — no real private API).
TESTNET_EXECUTION_REACHABLE = False
LIVE_EXECUTION_REACHABLE = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE = False
REAL_CAPITAL_MOVEMENT_REACHABLE = False
PRIVATE_READONLY_NETWORK_REACHABLE = False
PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED = False
PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3 = False
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3 = False

# Private read-only surface claims.
PRIVATE_READONLY_PORT_DECLARED = True
PRIVATE_READONLY_SIDE_EFFECTS_ONLY = True
PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN = True
PRIVATE_READONLY_GET_ONLY = True
VENUE_ADAPTER_DECISION_AUTHORITY = False
VENUE_NATIVE_EVENT_NORMALIZED = True
ROUNDING_AND_PRECISION_EXPLICIT = True
MIN_SIZE_AND_NOTIONAL_VALIDATED = True
ORDER_TYPE_SUPPORT_EXPLICIT = True
RATE_LIMIT_BUDGET_EXPLICIT = True
ERROR_TAXONOMY_EXPLICIT = True

# Reconciliation hierarchy invariants (§11.5).
RECONCILIATION_BEFORE_ALPHA = True
RECONCILIATION_CONTINUOUS = True
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY = True
POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE = True
EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY = True
SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN = True

RECONCILIATION_LAYERS: tuple[str, ...] = (
    "credential_and_account_identity",
    "venue_instrument_and_contract_metadata",
    "open_orders",
    "recent_orders_and_trades",
    "positions",
    "balances_equity_and_available_margin",
    "local_portfolio_and_accounting",
    "risk_reservations",
    "pending_commands",
    "evidence_and_commit_cursors",
)

RECONCILIATION_OUTCOMES: tuple[str, ...] = (
    "MATCH",
    "SAFE_REBUILD",
    "SAFE_ADOPT_EXCHANGE_TRUTH",
    "CANCEL_UNKNOWN_ORDERS",
    "EXIT_ONLY",
    "REDUCE_ONLY",
    "CANCEL_ALL_AND_HALT",
    "HARD_STOP_OWNER_REVIEW",
)

PRIVATE_READONLY_GET_ENDPOINTS: tuple[str, ...] = (
    "accounts",
    "open_positions",
    "open_orders",
)

PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS: tuple[str, ...] = (
    "submit_order",
    "cancel_order",
    "amend_order",
    "withdraw",
    "transfer",
    "sendorder",
    "batchorder",
)

VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES: tuple[str, ...] = (
    "authentication_transport",
    "venue_native_instrument_translation",
    "request_signing",
    "endpoint_and_rate_limit_handling",
    "venue_event_normalization",
    "exchange_clock_synchronization",
    "idempotent_lookup_by_canonical_identifiers",
    "private_readonly_account_state_normalization",
)

VENUE_ADAPTER_FORBIDDEN_AUTHORITIES: tuple[str, ...] = (
    "decision",
    "alpha",
    "master_v2",
    "double_play",
    "portfolio_strategy",
    "risk_limit_policy",
    "safety_policy",
    "accounting_authority",
    "autonomous_limit_changes",
    "order_mutation",
)

PRIVATE_READONLY_PORT_OWNER = OWNER
VENUE_SESSION_CONTRACT_OWNER = OWNER
EXCHANGE_CLOCK_SYNC_OWNER = OWNER
PRIVATE_ACCOUNT_STATE_INGESTION_OWNER = OWNER
RECONCILIATION_HIERARCHY_OWNER = OWNER
VENUE_ADAPTER_ANTI_CORRUPTION_OWNER = OWNER

EVIDENCE_DIRNAME = "capability_11_3_private_readonly_venue_integration_and_reconciliation_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
