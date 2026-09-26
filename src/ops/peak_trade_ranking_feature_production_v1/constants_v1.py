"""Authority-bounded constants for B05 ranking feature production."""

from __future__ import annotations

CAPABILITY_ID = "CAP21_FEATURE_PRODUCTION_V1"
PRODUCTION_VERSION = "peak_trade_ranking_feature_production.v1"
SCHEMA_VERSION = "peak_trade_ranking_feature_production_snapshot.v1"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_B05_CAP21_FEATURE_PRODUCTION_V1"
BOUND_ORIGIN_MAIN_SHA = "9c2edeb7d5133974c3c8b771eaa15f5df3871ec4"

CANONICAL_ECONOMIC_MD_PRODUCER = "src.ops.economic_md_input_producer_v1"
ECONOMIC_MD_CAPABILITY_ID = "CAPABILITY_2_2_ECONOMIC_MD_INPUT_PRODUCER_V1"

B05_IMPLEMENTED = True
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
RUNTIME_WIRING_ADDED = False
SELECTION_AUTHORITY_CREATED = False
BINDING_EFFECT = False
RANKING_ACTIVATION = False
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION = False
ECONOMIC_RANK_ACTIVATED = False
CAP23_SOLE_SELECTION_OWNER = True
CROSS_UNIVERSE_AUTHORITY = "NONE"
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MAX_POSITIONS_EFFECTIVE = 1
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

MARK_COUNT = 61
LOG_RETURN_COUNT = 60
PT1M_STEP_MS = 60_000
OBSERVATION_WINDOW_ID = "61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES"

FORBIDDEN_OUTPUT_FIELDS: tuple[str, ...] = (
    "rank_position",
    "balanced_movement_score",
    "ordered_ranking",
    "selected_future",
    "pairwise_order_witness",
)

CALL_GRAPH: tuple[str, ...] = (
    "load_economic_md_input_snapshot_v1",
    "build_input2_provenance_from_snapshot",
    "extract_contiguous_finalized_pt1m_marks_per_instrument",
    "compute_b03_ratified_raw_features_pure_v1",
    "populate_b04_raw_ranking_feature_dtos",
    "validate_raw_features_fail_closed",
    "persist_production_snapshot_digest",
)

FORBIDDEN_CALL_GRAPH_TARGETS: tuple[str, ...] = (
    "productive_futures_ranking_producer_v1",
    "single_selected_future_policy",
    "submit_order",
    "place_order",
    "activate_economic_rank",
)
