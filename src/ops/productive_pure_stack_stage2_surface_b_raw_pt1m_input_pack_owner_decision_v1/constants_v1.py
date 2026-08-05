"""Constants for Surface-B raw PT1M input-pack Owner Decision v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START_AUTHORIZED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_RAW_PT1M_CANDLE_MARK_INPUT_PACK_AND_CAMPAIGN_INSTANCE_BINDING"
PACKAGE_MARKER = "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1=true"
OWNER = "ops.productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1"
SCHEMA_VERSION = "productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions/v1"
DOCUMENT_TYPE = "OWNER_AUTHORITY_DECISIONS_MANIFEST"
STATUS_STRUCTURE_OPEN = "OWNER_DECISION_STRUCTURE_RATIFIED_INSTANCE_FIELDS_OPEN"

BASELINE_ORIGIN_MAIN_SHA = "81315806a9501ab7872b9fc0c54bafa82eff5920"
AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"
SOURCE_ID = "sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1"
BAR_INTERVAL = "PT1M"

INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
CAMPAIGN_START_AUTHORIZED = False
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_CALIBRATION_AUTHORIZED = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
O4_UNCHANGED = True

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_DECISIONS_V1.json"
)
SCHEMA_REL = "docs/ops/schemas/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_decisions_v1.schema.json"

REQUIRED_INSTRUMENT_FIELDS: tuple[str, ...] = (
    "venue",
    "canonical_instrument_id",
    "venue_instrument_id",
    "contract_type",
    "market_type",
    "quote_currency",
    "settlement_currency",
)

PARTITION_SEGMENTS: tuple[str, ...] = (
    "train",
    "calibration",
    "validation",
    "holdout",
)

FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = (
    "fixture",
    "demo",
    "scenario_scalar",
    "dashboard",
    "webui",
    "notion",
    "cmc_volatility",
    "resultv1",
    "survivalresultv1",
    "suitabilityresultv1",
    "o4_pt1h_as_pt1m",
    "candle_close_as_mark",
    "trade_as_mark",
    "parallel_arithmetic_kernel",
    "parallel_survival_kernel",
)

REQUIRED_MANIFEST_TOP_KEYS: tuple[str, ...] = (
    "schema_version",
    "document_type",
    "capability_scope",
    "status",
    "baseline_origin_main_sha",
    "authority_surface",
    "input_authority",
    "runtime_implemented",
    "campaign_start_authorized",
    "raw_input_pack_materialization_authorized",
    "productive_numeric_values_set",
    "purge",
    "embargo",
    "fold_sizes",
    "campaign_instance",
    "decisions",
)

REQUIRED_INSTANCE_KEYS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "instrument_binding",
    "candle_authority",
    "mark_price_authority",
    "pack_provenance",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
    "regime_coverage",
)
