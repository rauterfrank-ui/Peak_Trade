"""Constants for CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
SCHEMA_VERSION = "productive_futures_ranking_snapshot.v1"
PRODUCER_VERSION = "productive_futures_ranking_producer.v1"
PACKAGE_MARKER = "PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1=true"
OWNER = "ops.productive_futures_ranking_producer_v1"
AUTHORITY_OWNER = OWNER
SINGLE_WRITER_IDENTITY = "productive_futures_ranking_snapshot_writer_v1"

RANKING_POLICY_ID = "productive_futures_universe_structural_ranking_v1"
RANKING_POLICY_VERSION = "v1"

# Provenance: Cap 2.1 governed universe instrument structural gates only.
# Explicitly excludes research cross-sectional formulas, dashboard heuristics,
# and Master V2 / Double Play trading scores.
RANKING_POLICY_PROVENANCE = (
    "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1 instrument fields "
    "+ CAPABILITY_2_2 owner requirements (data-quality eligibility, deterministic "
    "tie-break, Top-20 candidate context). No trading-alpha heuristic. "
    "No arbitrary market-signal weights. Equal structural gate components only."
)

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
    "deterministic_score_and_tie_break",
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
