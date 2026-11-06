"""Constants for CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
SCHEMA_VERSION = "productive_futures_ranking_snapshot.v1"
PRODUCER_VERSION = "productive_futures_ranking_producer.v1"
PACKAGE_MARKER = "PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1=true"
OWNER = "ops.productive_futures_ranking_producer_v1"
AUTHORITY_OWNER = OWNER
SINGLE_WRITER_IDENTITY = "productive_futures_ranking_snapshot_writer_v1"

RANKING_POLICY_ID = "PEAK_TRADE_RANKING_MATRIX_POLICY_V1"
RANKING_POLICY_VERSION = "v1"

# Provenance: B03 Peak_Trade ranking matrix + B04/B05 economic features.
# Structural Cap 2.1 gates remain eligibility-only and are not summed into
# the economic attractiveness score. Venue-native id is final tie fallback only.
RANKING_POLICY_PROVENANCE = (
    "PEAK_TRADE_RANKING_MATRIX_POLICY_V1 equal-weight midrank-percentile "
    "composite over CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1 and "
    "CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1 from Cap-2.1-eligible S_STAR; "
    "B05 feature production + B04 contract; venue_native_id ASC final fallback only. "
    "No PROFILE_ONLY promotion. No Cap 2.3 selection authority."
)

ECONOMIC_RANK_ACTIVATED = True
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = True
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION = False
B06_IMPLEMENTED = True

TOP20_CANDIDATE_CONTEXT_LIMIT = 20
MAX_POSITIONS_EFFECTIVE = 1
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
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

# Universe snapshot input contract (Capability 2.1).
UNIVERSE_CAPABILITY_ID = "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1"
UNIVERSE_SCHEMA_VERSION = "governed_futures_universe_snapshot.v1"
UNIVERSE_PRODUCER_VERSION = "governed_futures_universe_producer.v1"
VENUE = "okx_eea"

DEFAULT_MAX_UNIVERSE_AGE_SECONDS = 86_400.0

SNAPSHOT_FILENAME = "productive_futures_ranking_snapshot_v1.json"
EVIDENCE_FILENAME = "productive_futures_ranking_evidence_v1.json"
WRITER_LOCK_FILENAME = "productive_futures_ranking_writer.lock"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".productive_futures_ranking_staging_"

SNAPSHOT_STATE_VALID = "VALID"
SNAPSHOT_STATE_NO_ELIGIBLE = "NO_ELIGIBLE_CANDIDATES"
SNAPSHOT_STATE_INVALID_INPUT = "INVALID_INPUT"
SNAPSHOT_STATE_STALE_INPUT = "STALE_INPUT"
SNAPSHOT_STATE_INTEGRITY_FAILURE = "INTEGRITY_FAILURE"

ELIGIBILITY_ELIGIBLE = "ELIGIBLE"
ELIGIBILITY_EXCLUDED = "EXCLUDED"

DATA_QUALITY_PASS = "PASS"

CALL_GRAPH = (
    "productive_ranking_entry_point",
    "load_governed_universe_snapshot",
    "validate_universe_bindings",
    "stale_and_integrity_checks",
    "structural_eligibility_classification",
    "consume_b05_feature_production_snapshot",
    "b03_economic_score_and_order",
    "top20_candidate_context",
    "atomic_persistence",
    "snapshot_verification",
    "restart_reload_proof",
    "evidence",
)

FORBIDDEN_CALL_GRAPH_TARGETS = frozenset(
    {
        "selected_future",
        "master_v2",
        "double_play",
        "execution",
        "dashboard_authority",
        "top_n_active_set",
        "live_orders",
    }
)

# Equal structural gate components — Cap 2.1 re-validation only (not alpha weights).
SCORE_COMPONENT_KEYS = (
    "universe_eligibility",
    "data_quality_pass",
    "mark_price_supported",
    "market_data_supported",
    "trading_status_live",
    "metadata_complete",
)

ACTIVE_TRADING_STATES = frozenset({"live"})
