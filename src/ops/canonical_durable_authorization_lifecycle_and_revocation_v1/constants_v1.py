"""Constants for CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1."""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1"
PACKAGE_MARKER = "CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1=true"
PRODUCER_FAMILY = "ops.canonical_durable_authorization_lifecycle_and_revocation_v1"
SCHEMA_VERSION = "v1"

AUTHORIZATION_SCHEMA = "authorization_artifact_v2"
AUTHORIZATION_SCHEMA_VERSION = "v2"
REVOCATION_SCHEMA = "authorization_revocation_v1"
REVOCATION_SCHEMA_VERSION = "v1"

TARGET_RUNTIME_CAPABILITY = (
    "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1"
)

LEGACY_FORMAL_AUTHORIZATION_CLASS = "LEGACY_FORMAL_AUTHORIZATION_V1"
LEGACY_FORMAL_SCHEMA_ID = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    ".formal_authorization_v1"
)

REASON_CONFIRM_TOKEN_EXPOSED = "CONFIRM_TOKEN_EXPOSED_OUTSIDE_SINGLE_OPERATOR_DELIVERY_CHANNEL"

CONFIG_RELPATH = "config/ops/canonical_durable_authorization_lifecycle_and_revocation_v1.toml"
CONTRACT_DOC_RELPATH = (
    "docs/ops/runbooks/CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1.md"
)
CLI_RELPATH = "scripts/ops/run_canonical_durable_authorization_lifecycle_and_revocation_v1.py"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
ECONOMIC_GATE_EFFECT_NONE = "NONE"

ORDERS_AUTHORIZED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
CREDENTIALS_AUTHORIZED = False
AUTO_PROMOTION_AUTHORIZED = False
PRIVATE_API = False
ORDER_ROUTING_REACHABLE = False

REVOCATION_CHECK_BEFORE_CONSUMPTION = True
REVOCATION_CHECK_FAIL_CLOSED = True
CONSUMPTION_ATOMIC = True
CONSUMPTION_SINGLE_USE = True
CONSUMPTION_REPLAY_BLOCKED = True
TOCTOU_BETWEEN_REVOCATION_CHECK_AND_CONSUMPTION_BLOCKED = True

REVOCATION_DIRNAME = "authorization_revocations_v1"
LIFECYCLE_LOCK_NAME = "authorization_lifecycle.lock"

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.orders",
    "src.broker",
    "src.live",
    "src.execution.live",
)

CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/__init__.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/constants_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/states_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/atomic_io_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/integrity_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/authorization_artifact_v2.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/legacy_formal_authorization_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/revocation_record_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/revocation_registry_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/authorization_writer_v2.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/lifecycle_lock_v1.py",
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/consumption_gate_v1.py",
)
