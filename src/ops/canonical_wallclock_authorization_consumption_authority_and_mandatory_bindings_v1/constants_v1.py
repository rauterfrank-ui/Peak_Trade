"""Constants for CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1."""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1"
PACKAGE_MARKER = (
    "CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1=true"
)
SCHEMA_VERSION = "v1"

CANONICAL_AUTHORIZATION_SCHEMA = "authorization_artifact_v2"
TARGET_RUNTIME_CAPABILITY = (
    "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1"
)
COMPLETION_CAPABILITY_ID = (
    "CANONICAL_WALLCLOCK_V2_AUTHORIZATION_CONSUMPTION_FAIL_CLOSED_COMPLETION_V1"
)

AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION = "LEGACY_PRODUCTIVE_AUTHORITY_RETIRED"
AUTHORIZATION_SCHEMA_REJECTED_LEGACY = "AUTHORIZATION_SCHEMA_REJECTED_LEGACY"

REQUIRED_SESSION_DURATION_SECONDS = 3600
EFFECTIVE_SESSION_CONFIG_DIGEST_KEY = "effective_session_config"
EFFECTIVE_SESSION_CONFIG_DIGEST_VERSION = "effective_session_config_digest_v1"

AUTHORIZED_VENUE = "OKX"
AUTHORIZED_NETWORK_SCOPE = "PUBLIC_MARKET_DATA_ONLY"
VENUE_FIELD = "venue"
NETWORK_SCOPE_FIELD = "network_scope"
CANONICAL_RUNBOOK_SHA256 = "a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a"

MANDATORY_SAFETY_BOUNDARIES: dict[str, bool] = {
    "wallclock_mode": True,
    "public_market_data_only": True,
    "analytical_simulated_execution": True,
    "external_paper_order_execution": False,
    "real_order_routing": False,
    "private_api": False,
    "forced_wiring_fixture_mode": False,
    "no_implicit_resume": True,
    "order_routing_reachable": False,
    "orders_created": False,
    "testnet_execution_occurred": False,
    "live_execution_occurred": False,
    "promotion_authority": False,
}

PRIVATE_API = False
ORDER_ROUTING_REACHABLE = False
ORDERS_AUTHORIZED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
VENUE_DEFAULT_FALLBACK = False

CONFIG_RELPATH = "config/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.toml"
CONTRACT_DOC_RELPATH = "docs/ops/runbooks/CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1.md"

CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/__init__.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/constants_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/mandatory_bindings_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/effective_session_config_digest_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/v1_quarantine_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/wallclock_v2_gatekeeper_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/call_graph_contract_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/evidence_sink_protocol_v1.py",
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/authority_inventory_v1.py",
)

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.orders",
    "src.broker",
    "src.live",
    "src.execution.live",
)
