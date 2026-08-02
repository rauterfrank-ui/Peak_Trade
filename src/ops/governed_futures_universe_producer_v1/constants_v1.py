"""Constants for CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1"
SCHEMA_VERSION = "governed_futures_universe_snapshot.v1"
PRODUCER_VERSION = "governed_futures_universe_producer.v1"
PACKAGE_MARKER = "GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1=true"
OWNER = "ops.governed_futures_universe_producer_v1"
AUTHORITY_OWNER = OWNER
SINGLE_WRITER_IDENTITY = "governed_futures_universe_snapshot_writer_v1"

VENUE = "okx_eea"
VENUE_ALLOWED = frozenset({"okx_eea"})
FUTURES_ONLY = True
SPOT_EXCLUDED = True
BTC_EXCLUDED = True
MAX_POSITIONS_EFFECTIVE = 1
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
RANKING_AUTHORITY_ADDED = False
SELECTION_AUTHORITY_ADDED = False
ALPHA_AUTHORITY_ADDED = False
EXECUTION_AUTHORITY_ADDED = False
DASHBOARD_AUTHORITY = False
CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED"
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_TRADING_SESSION_ALLOWED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
ALPHA_ALLOWED_DEFAULT = False

DEFAULT_MAX_SOURCE_AGE_SECONDS = 86_400.0

SNAPSHOT_FILENAME = "governed_futures_universe_snapshot_v1.json"
EVIDENCE_FILENAME = "governed_futures_universe_evidence_v1.json"
WRITER_LOCK_FILENAME = "governed_futures_universe_writer.lock"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".governed_futures_universe_staging_"

CALL_GRAPH = (
    "productive_universe_entry_point",
    "okx_eea_instrument_discovery",
    "raw_metadata_validation",
    "futures_only_filter",
    "btc_exclusion",
    "canonical_instrument_normalization",
    "eligibility_data_quality_classification",
    "deterministic_universe_snapshot",
    "atomic_persistence",
    "snapshot_verification",
    "evidence",
)

FORBIDDEN_CALL_GRAPH_TARGETS = frozenset(
    {
        "ranking",
        "selected_future",
        "master_v2",
        "double_play",
        "execution",
        "dashboard_authority",
    }
)

ACTIVE_TRADING_STATES = frozenset({"live"})
SUPPORTED_INST_TYPES = frozenset({"SWAP", "FUTURES"})
SUPPORTED_CT_TYPES = frozenset({"linear"})
FORBIDDEN_BASE_ASSETS = frozenset({"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB", "BITCOIN"})
FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin", "wbtc", "tbtc", "rbtc", "btcb"})

UNIVERSE_STATUS_ELIGIBLE = "ELIGIBLE_UNIVERSE_READY"
UNIVERSE_STATUS_EMPTY = "NO_ELIGIBLE_INSTRUMENTS"
