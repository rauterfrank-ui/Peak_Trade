"""CAPABILITY_O4 constants — public-MD / OHLCV transport reconciliation."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_O4_CANONICAL_PUBLIC_MD_AND_OHLCV_TRANSPORT_RECONCILIATION_V1"
SCHEMA_VERSION = "o4_canonical_public_md_and_ohlcv_transport_reconciliation_v1"
PACKAGE_MARKER = "CANONICAL_PUBLIC_MD_AND_OHLCV_TRANSPORT_RECONCILIATION_V1=true"

# Authority classifications for inventory rows.
CLASS_AUTHORITATIVE = "AUTHORITATIVE"
CLASS_DERIVED = "DERIVED"
CLASS_LEGACY = "LEGACY"
CLASS_FORBIDDEN = "FORBIDDEN"

# Canonical ownership targets (exactly one each).
CANONICAL_NORMALIZED_EVENT_PATH = (
    "NormalizedPublicMarketDataV1+ObservationIdentityV1+DistinctMarketObservationAcceptorV1"
)
AUTHORITATIVE_BAR_PRODUCER = "CanonicalPublicMdBarProducerV1"
DASHBOARD_OHLCV_CLASSIFICATION = CLASS_DERIVED
DASHBOARD_TRANSPORT = "HTTP_JSON_POLL"

# Bar quality / finalization states (shared contract).
BAR_STATE_IN_PROGRESS = "IN_PROGRESS_BAR"
BAR_STATE_FINALIZED = "FINALIZED_BAR"
BAR_STATE_CORRECTED = "CORRECTED_BAR"
BAR_STATE_MISSING = "MISSING_BAR"
BAR_STATE_STALE = "STALE_BAR"

BAR_STATES = frozenset(
    {
        BAR_STATE_IN_PROGRESS,
        BAR_STATE_FINALIZED,
        BAR_STATE_CORRECTED,
        BAR_STATE_MISSING,
        BAR_STATE_STALE,
    }
)

# Shared interval IDs (canonical set for productive public-MD OHLCV).
INTERVAL_PT1H = "PT1H"
INTERVAL_1H = "1H"  # alias accepted only as input synonym for PT1H
SUPPORTED_INTERVALS = frozenset({INTERVAL_PT1H})

# Authority envelope required fields.
AUTHORITY_ENVELOPE_FIELDS = (
    "canonical_instrument_id",
    "venue_instrument_id",
    "venue",
    "interval",
    "bar_open_time",
    "bar_close_time",
    "event_time",
    "receive_time",
    "first_observation_identity",
    "last_observation_identity",
    "session_id",
    "repository_sha",
    "config_digest",
    "transport_lag",
    "quality_state",
    "finalization_state",
    "revision",
)

SAFETY_INVARIANTS = {
    "CORE_LOGIC_CHANGE_ALLOWED": False,
    "MASTER_V2_CHANGE_ALLOWED": False,
    "DOUBLE_PLAY_CHANGE_ALLOWED": False,
    "BULL_BEAR_CHANGE_ALLOWED": False,
    "DYNAMIC_SCOPE_CHANGE_ALLOWED": False,
    "RISK_AUTHORITY_CHANGE_ALLOWED": False,
    "SAFETY_AUTHORITY_CHANGE_ALLOWED": False,
    "DASHBOARD_REDESIGN_ALLOWED": False,
    "NETWORK_SESSION_ALLOWED": False,
    "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
    "CONFIRM_TOKEN_MINT_ALLOWED": False,
    "ORDERS_ALLOWED": False,
    "EXCHANGE_CREDENTIAL_USE_ALLOWED": False,
    "LIVE_TRADING_ALLOWED": False,
    "TESTNET_ALLOWED": False,
    "REAL_CAPITAL_MOVEMENT_ALLOWED": False,
    "NO_PARALLEL_NORMALIZED_EVENT_SSOT": True,
    "NO_SILENT_GAP_FILL": True,
    "NO_DASHBOARD_AUTHORITATIVE_INDEPENDENT_RECOMPUTATION": True,
    "FINALIZED_IMMUTABLE_EXCEPT_CORRECTION": True,
    "DUPLICATE_DOES_NOT_ADVANCE_AUTHORITATIVE_STATE": True,
    "OUT_OF_ORDER_MUST_BE_CLASSIFIED": True,
}

# Deferred scopes (explicit non-claims).
DEFERRED_TO_O5 = (
    "DURABLE_READ_MODEL_BINDING_CLOSURE",
    "EXPECTED_MISSING_SOURCE_SEMANTICS",
    "DASHBOARD_BACKEND_FRONTEND_LIFECYCLE",
    "DASHBOARD_SUPERVISOR_BINDING",
    "REALTIME_METRICS_UX",
    "STALE_AND_DISCONNECTED_DASHBOARD_CHROME",
    "INSTRUMENT_AND_INTERVAL_UI_REBUILD",
)
DEFERRED_TO_O8 = (
    "LEGACY_HOST_DEAUTHORIZATION",
    "OLD_LAUNCH_PATH_REMOVAL",
)
