"""Identity and hard invariants for Operator-GO / Session-Preregistration v1."""

from __future__ import annotations

CAPABILITY_ID = "PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1"
PACKAGE_MARKER = (
    "PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1=true"
)
PRODUCER_FAMILY = "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
SCHEMA_VERSION = "v1"

PREREGISTRATION_SCHEMA_VERSION = "paper_shadow_observation_session_preregistration.v1"
OPERATOR_GO_SCHEMA_VERSION = "paper_shadow_observation_operator_go.v1"
AUTHORIZATION_ARTIFACT_SCHEMA_VERSION = "paper_shadow_observation_authorization_artifact.v1"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"

REQUIRED_MODE = "observation"
VENUE_OKX = "OKX"
MARKET_TYPE_FUTURES = "FUTURES"

# Bound by observation capability defaults (6h).
DEFAULT_MAX_SESSION_DURATION_SECONDS = 21600
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 7 * 24 * 3600

CONFIG_RELPATH = "config/ops/paper_shadow_observation_operator_go_session_preregistration_v1.toml"
CONTRACT_DOC_RELPATH = (
    "docs/ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_"
    "AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md"
)
CLI_RELPATH = (
    "scripts/ops/assess_paper_shadow_observation_operator_go_session_preregistration_v1.py"
)

OBSERVATION_PACKAGE_RELPATH = "src/ops/integrated_paper_shadow_observation_session_v1"
OBSERVATION_CAPABILITY_ID = "INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1"
OBSERVATION_CONFIG_RELPATH = "config/ops/integrated_paper_shadow_observation_session_v1.toml"

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.orders",
    "src.broker",
    "src.live",
    "src.execution.live",
)

AUTHORITY_FLAGS_ALWAYS_FALSE: tuple[str, ...] = (
    "ORDERS_AUTHORIZED",
    "TESTNET_AUTHORIZED",
    "LIVE_AUTHORIZED",
    "AUTO_PROMOTION_AUTHORIZED",
    "ECONOMIC_VALIDITY_PASS",
    "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED",
)

NO_AUTO_PROMOTION = True
WALLCLOCK_SESSION_EXECUTION_ALLOWED = False
NETWORK_ALLOWED = False
CREDENTIALS_ALLOWED = False
BROKER_WRITES_ALLOWED = False
ORDERS_ALLOWED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
SESSION_EXECUTED = False

# Discovery surface inventory (must all be present + symbol-complete).
CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/__init__.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/constants_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/preregistration_contract_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/operator_go_contract_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/confirm_token_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/state_machine_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_artifact_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_readiness_producer_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/verifier_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/consumption_revocation_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/discovery_v1.py",
)

REQUIRED_DISCOVERY_SYMBOLS: tuple[tuple[str, str], ...] = (
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/preregistration_contract_v1.py",
        "validate_preregistration_contract_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/operator_go_contract_v1.py",
        "validate_operator_go_contract_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_artifact_v1.py",
        "build_authorization_artifact_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_readiness_producer_v1.py",
        "produce_paper_shadow_observation_authorization_readiness_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/verifier_v1.py",
        "verify_paper_shadow_observation_authorization_bundle_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/discovery_v1.py",
        "discover_session_preregistration_and_operator_go_contract_present_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/confirm_token_v1.py",
        "verify_confirm_token_v1",
    ),
    (
        "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/state_machine_v1.py",
        "AuthorizationArmingState",
    ),
)
