"""Constants for B07 Future Profile Snapshot V1."""

from __future__ import annotations

CAPABILITY_ID = "B07_FUTURE_PROFILE_SNAPSHOT_V1"
SCHEMA_VERSION = "future_profile_snapshot.v1"
PROFILE_VERSION = "future_profile_snapshot/v1"
PRODUCER_VERSION = "future_profile_snapshot_producer.v1"
OWNER_GO_THIS_SLICE = "OWNER_GO_B07_FUTURE_PROFILE_SNAPSHOT_V1"

AUTHORITY_ELIGIBILITY_SAFETY = "ELIGIBILITY_SAFETY"
AUTHORITY_RANKING_INPUT = "RANKING_INPUT"
AUTHORITY_PROFILE_ONLY = "PROFILE_ONLY"
AUTHORITY_UNCLASSIFIED = "UNCLASSIFIED"

AVAILABLE = "AVAILABLE"
MISSING = "MISSING"
INVALID = "INVALID"
NOT_APPLICABLE = "NOT_APPLICABLE"

GROUP_IDENTITY_CONTRACT = "IDENTITY_CONTRACT"
GROUP_MARKET_STATE = "MARKET_STATE"
GROUP_ACTIVITY_DEPTH = "ACTIVITY_DEPTH"
GROUP_MOVEMENT_ECONOMIC_FEATURES = "MOVEMENT_ECONOMIC_FEATURES"
GROUP_PRODUCT_MECHANICS = "PRODUCT_MECHANICS"
GROUP_PROVENANCE_DATA_QUALITY = "PROVENANCE_DATA_QUALITY"
GROUP_RANKING_CONTEXT = "RANKING_CONTEXT"

FIELD_AUTHORITY_CLASSES = frozenset(
    {
        AUTHORITY_ELIGIBILITY_SAFETY,
        AUTHORITY_RANKING_INPUT,
        AUTHORITY_PROFILE_ONLY,
        AUTHORITY_UNCLASSIFIED,
    }
)

FIELD_AVAILABILITY_STATES = frozenset({AVAILABLE, MISSING, INVALID, NOT_APPLICABLE})

CALL_GRAPH = (
    "future_profile_snapshot_entry_point",
    "consume_cap21_universe_snapshot",
    "consume_economic_md_snapshot_optional",
    "consume_b05_feature_production_snapshot_optional",
    "consume_b06_ranking_snapshot_optional",
    "compose_observability_fields",
    "canonical_profile_serialization",
)

FORBIDDEN_CALL_GRAPH_TARGETS = frozenset(
    {
        "produce_single_selected_future_v1",
        "run_single_selected_future_policy_v1",
        "single_selected_future_runtime_binding",
        "master_v2",
        "double_play",
        "execution",
        "order_intent",
        "wire_send",
        "live_orders",
    }
)
