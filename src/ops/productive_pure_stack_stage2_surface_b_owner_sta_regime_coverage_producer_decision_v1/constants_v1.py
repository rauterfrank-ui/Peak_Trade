"""Constants for Surface-B Owner/STA regime-coverage producer decision v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_START_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISION_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1=true"
)
OWNER = "ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1"
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decisions/v1"
)
DOCUMENT_TYPE = "OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISIONS_MANIFEST"
STATUS_SURFACE_OPEN = "OWNER_STA_DECISION_SURFACE_OPEN"

DECISION_ID = "DEC_REGIME_COVERAGE_PRODUCER"
DECISION_STATUS_OPEN = "OPEN"

BASELINE_ORIGIN_MAIN_SHA = "42e8527c929264c702d8f7d59a80fc38f850baff"
AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"

INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
CAMPAIGN_START_AUTHORIZED = False
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = False
RAW_INPUT_PACK_CREATED = False
CAMPAIGN_STARTED = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_CALIBRATION_AUTHORIZED = False
REGIME_COVERAGE_PRODUCER_AVAILABLE = False
REGIME_COVERAGE_STATUS = "SEMANTICALLY_UNRESOLVED"
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
O4_UNCHANGED = True
O4_PT1H_AS_PT1M_FORBIDDEN = True
EXISTING_PRODUCERS_ELEVATED = False
TRADING_LOGIC_CHANGED = False
ORDERS_TESTNET_LIVE_PAPER_EFFECTS = False
EXCHANGE_CREDENTIAL_EFFECTS = False

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISIONS_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "regime_coverage_producer_decisions_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_CYBERSECURITY_MIRROR_V1.md"
)
PARENT_TRIAD_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
)
PARENT_TRIAD_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json"
)
PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
PARENT_SURFACE_B_RATIFICATION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md"
)

ALLOWED_OWNER_VALUES: tuple[str, ...] = (
    "AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER",
    "EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER",
)

AUTHORIZE_OWNER_VALUE = "AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER"
REJECT_OWNER_VALUE = "EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER"

TAXONOMY_SINK_LABELS: tuple[str, ...] = (
    "low",
    "mid",
    "high",
    "unknown",
    "missing",
)

AUTHORIZE_DETAIL_FIELDS: tuple[str, ...] = (
    "canonical_producer_name",
    "canonical_producer_version",
    "versioned_producer_id",
    "taxonomy_binding",
    "threshold_authority_ref",
    "lookback_window_authority_ref",
    "time_basis",
    "PIT_no_lookahead_rules_ref",
    "candle_join_acceptance_ref",
    "mark_join_acceptance_ref",
    "instrument_binding_acceptance_ref",
    "determinism_contract_ref",
    "reproducibility_contract_ref",
    "producer_digest_contract_ref",
    "missing_label_semantics_ref",
    "unknown_label_semantics_ref",
)

FORBIDDEN_EXISTING_PRODUCER_TOKENS: tuple[str, ...] = (
    "analytics.regimes",
    "regime.detectors",
    "feature_regime_pipeline_v2",
    "ai.switch_layer",
    "research max-age regime map",
    "max-age regime map",
    "bull/bear evidence readmodel",
    "bull_bear_evidence_readmodel",
    "reporting regime buckets",
    "dashboard projection",
    "dashboard_projection",
    "dashboard_readmodel",
    "test fixture",
    "test_fixture",
    "fixture",
)

STA_OPEN_EXTERNAL_INPUTS: tuple[str, ...] = (
    "dedicated_surface_b_regime_recorder_under_sta",
    "ratified_taxonomy_mapping",
    "non_invented_coverage_counts",
    "producer_version_and_digest_contract",
    "provable_eth_usdt_swap_compatibility",
    "ratified_pt1m_candle_authority_join",
    "ratified_pt1m_mark_authority_join",
    "pit_no_lookahead_proof",
    "deterministic_reproducible_computation",
)

NULL_INSTANCE_KEYS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "seed",
    "partition_boundaries",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
    "regime_coverage_counts",
    "regime_coverage_instance",
)

REQUIRED_MANIFEST_TOP_KEYS: tuple[str, ...] = (
    "schema_version",
    "document_type",
    "capability_scope",
    "status",
    "baseline_origin_main_sha",
    "authority_surface",
    "decision_id",
    "decision_status",
    "owner_value",
    "allowed_owner_values",
    "authorize_detail_fields",
    "taxonomy_sink_labels",
    "sta_open_external_inputs",
    "forbidden_existing_producers",
    "reject_semantics",
    "authorize_semantics",
    "input_authority",
    "runtime_implemented",
    "campaign_start_authorized",
    "raw_input_pack_materialization_authorized",
    "raw_input_pack_created",
    "campaign_started",
    "productive_numeric_values_set",
    "regime_coverage_producer_available",
    "regime_coverage_status",
    "existing_producers_elevated",
    "dashboard_authority_effect",
    "notion_ssot",
    "repository_is_ssot",
    "open_null_instance_fields",
    "decisions",
)

FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = (
    "analytics.regimes",
    "regime.detectors",
    "feature_regime_pipeline_v2",
    "ai.switch_layer",
    "dashboard",
    "webui",
    "notion",
    "fixture",
    "demo",
    "bull_bear",
    "reporting regime",
    "coverage_count",
    "invented_threshold",
    "invented_lookback",
)
