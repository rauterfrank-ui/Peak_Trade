"""PL-TF-002 network evidence contract constants. No network. No credential load."""

from __future__ import annotations

CAPABILITY_ID = "PL_TF_002_NETWORK_EVIDENCE_CONTRACT_V1"
PACKAGE_MARKER = "PL_TF_002_NETWORK_EVIDENCE_CONTRACT_V1=true"
OWNER = "ops.pl_tf_002_network_evidence_contract_v1"
SCHEMA_VERSION = "pl_tf_002_network_evidence_contract.v1"
CONTRACT_VERSION = "v1"

RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NETWORK_EXECUTION_AUTHORIZED = False
CREDENTIAL_LOAD_AUTHORIZED = False
TREASURY_MUTATION_AUTHORIZED = False
EXTERNAL_EFFECT_AUTHORIZED = False
STEP_29P_AUTHORITY_CHANGED = False

# Verifier-package standing label (unchanged by verify_pl_tf_002_network_evidence_v1).
# Canonical navigation status after governed closure: treasury_phase_1 PL_TF_002_STATUS.
PL_TF_002_STATUS_STANDING = "FROZEN_PENDING_NETWORK_EVIDENCE"
VENUE_PERMISSION_UNKNOWN_STANDING = True
VENUE_PERMISSION_GET_PERFORMED_STANDING = False

# Future closure status (requires governed productive evidence + explicit status flip elsewhere).
PL_TF_002_STATUS_CLOSED = "CLOSED_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN"

NE_TF_001_TASK_ID = "NE-TF-001"
NE_TF_001_HTTP_METHOD = "GET"
NE_TF_001_ENDPOINT_PATH = "/api/v5/account/config"
NE_TF_001_RESPONSE_PERM_FIELD = "data[0].perm"
NE_TF_001_RESPONSE_UID_FIELD = "data[0].uid"
NE_TF_001_RESPONSE_CODE_FIELD = "code"

# Closed-world OKX perm comma-token vocabulary (perm field on account/config GET).
# Tokens read_only and trade: repo forensic/test captures (not endpoint-name inference).
OKX_PERM_TOKEN_READ: str = "read_only"
OKX_PERM_TOKEN_TRADE: str = "trade"
OKX_PERM_TOKEN_WITHDRAW: str = "withdraw"
OKX_PERM_KNOWN_TOKENS: frozenset[str] = frozenset(
    {OKX_PERM_TOKEN_READ, OKX_PERM_TOKEN_TRADE, OKX_PERM_TOKEN_WITHDRAW}
)

# PL-TF-002 trading-key treasury-separation target (distinct from §11.13.2 execute attestation).
PL_TF_002_REQUIRED_READ = True
PL_TF_002_REQUIRED_TRADE = False
PL_TF_002_REQUIRED_WITHDRAW = False

PRODUCTIVE_TRANSPORT_CLASSES: frozenset[str] = frozenset(
    {
        "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
        "LIVE_PRODUCTIVE_HTTP",
    }
)

FORBIDDEN_EVIDENCE_CLASS_MARKERS: tuple[str, ...] = (
    "INJECTED",
    "FIXTURE",
    "REPLAY",
    "HISTORICAL",
    "GOVERNED_FIXTURE",
    "INJECTED_TEST_DOUBLE",
    "PREFLIGHT_NO_NETWORK",
    "TRANSPORT_MISSING",
    "OFFLINE",
    "SYNTHETIC_CONTRACT_TEST",
)

FORBIDDEN_SECRET_FIELD_MARKERS: tuple[str, ...] = (
    "apikey",
    "api_key",
    "secret",
    "passphrase",
    "password",
    "authorization",
    "privatekey",
    "private_key",
    "signingmaterial",
    "signing_material",
    "bearer",
    "hmacsecret",
    "okxsecret",
)

# F1 productive venue GET bundle (Full-Core Fresh Pretrade item ids).
F1_REQUIRED_GET_ITEM_IDS: tuple[str, ...] = (
    "INSTRUMENT_STATE",
    "MAX_SIZE",
    "PRICE_BAND",
    "MAX_AVAILABLE",
    "LEVERAGE",
    "POS_MODE",
    "ACCOUNT_MODE",
    "MARGIN_MODE",
    "AVAILABLE_MARGIN",
)

DEFAULT_FRESHNESS_MAX_AGE_MS = 300_000
