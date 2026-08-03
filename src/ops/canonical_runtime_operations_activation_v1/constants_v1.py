"""O8 activation constants (derived metadata; not SSOT)."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1"
SCHEMA_ID = "ops.canonical_runtime_operations_activation_contract_v1"
ACTIVATION_VERSION = "v1"
CANONICAL_OPERATOR_ENTRYPOINT = "scripts/ops/peak_trade_runtime.py"
ACTIVATION_CONTRACT_RELATIVE_PATH = (
    "config/ops/canonical_runtime_operations_activation_contract_v1.json"
)
CANONICAL_SUBCOMMANDS: tuple[str, ...] = (
    "preflight",
    "start",
    "status",
    "health",
    "logs",
    "stop",
    "restart",
    "recover",
    "verify",
)
REQUIRED_CONTRACT_KEYS: tuple[str, ...] = (
    "schema_id",
    "capability_id",
    "activation_version",
    "canonical_operator_entrypoint",
    "canonical_subcommands",
    "canonical_supervisor",
    "canonical_dashboard_path",
    "canonical_read_model",
    "canonical_ohlcv_path",
    "canonical_health_model",
    "legacy_path_policy",
    "rollback_policy",
    "core_logic_changed",
    "live_trading_authorized",
    "testnet_authorized",
    "paper_exchange_orders_authorized",
    "credentials_authorized",
    "dashboard_trading_authority",
    "read_model_authority_effect",
    "master_runbook_is_only_ssot",
    "second_ssot_allowed",
)
FORBIDDEN_TOKEN_BASENAMES: frozenset[str] = frozenset(
    {
        "confirm_token",
        "confirm_token.txt",
        "token",
        "token.txt",
        ".env",
        "credentials.json",
        "secrets.json",
        "authorization_token",
    }
)
SECRET_NAME_FRAGMENTS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "credential",
    "passphrase",
    "api_key",
    "apikey",
)
