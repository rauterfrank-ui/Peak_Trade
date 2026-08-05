"""Constants for Surface-B Owner/STA raw input-pack materialization decision v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_START_AUTHORIZED=false
PACK_MATERIALIZATION=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1=true"
)
OWNER = "ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1"
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decisions/v1"
)
DOCUMENT_TYPE = "OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_MANIFEST"
STATUS_SURFACE_OPEN = "OWNER_STA_DECISION_SURFACE_OPEN"
STATUS_OWNER_VALUE_RECORDED = "OWNER_STA_OWNER_VALUE_RECORDED_AUTHORIZE_DETAIL_FIELDS_STILL_OPEN"
STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED = (
    "OWNER_STA_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED_INSTANCE_FIELDS_STILL_OPEN"
)
STATUS_PROVABLE_INSTANCE_FIELDS_CLOSED = (
    "OWNER_STA_PROVABLE_INSTANCE_FIELDS_CLOSED_NON_PROVABLE_INSTANCE_FIELDS_STILL_OPEN"
)
STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY = (
    "OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY_FIELDS_STILL_NULL"
)

DECISION_ID = "DEC_RAW_INPUT_PACK_MATERIALIZATION"
DECISION_STATUS_OPEN = "OPEN"
DECISION_STATUS_RATIFIED = "RATIFIED"

BASELINE_ORIGIN_MAIN_SHA = "56721ad0666fac5627d2dedbf33a22b59cd5996e"
OWNER_GO_BASE_SHA_PROVABLE_INSTANCE_FIELDS_CLOSED = "ac8b1e67baf361156c6f666a2c4cddbe49362400"
OWNER_GO_BASE_SHA = "6e4abc160c1b2b048a41e92d50003a33c30bb355"
DECISION_PACKET_ID = (
    "OWNER_STA_SURFACE_B_RAW_INPUT_PACK_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_V1"
)
DECISION_PACKET_DOCUMENT_TYPE = "OWNER_STA_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET"
DECISION_PACKET_STATUS = "PACKET_READY_FIELDS_STILL_NULL"
DECISION_PACKET_FIELD_STATUS = "OPEN_FILLABLE"
INPUT_CLASS_OWNER_VALUE = "OWNER_VALUE"
INPUT_CLASS_STA_EXTERNAL_INPUT = "STA_EXTERNAL_INPUT"
AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"

INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
CAMPAIGN_START_AUTHORIZED = False
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = False
RAW_INPUT_PACK_CREATED = False
CAMPAIGN_STARTED = False
PACK_MATERIALIZATION = False
PRODUCER_REIMPLEMENTATION = False
CONSUMER_WIRING = False
PT1M_ADAPTER = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_CALIBRATION_AUTHORIZED = False
PRODUCTIVE_THRESHOLDS_LOOKBACKS = False
REGIME_COVERAGE_PRODUCER_AVAILABLE = False
REGIME_COVERAGE_STATUS = "SEMANTICALLY_UNRESOLVED"
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
O4_UNCHANGED = True
O4_PT1H_AS_PT1M_FORBIDDEN = True
TRADING_LOGIC_CHANGED = False
ORDERS_TESTNET_LIVE_PAPER_EFFECTS = False
EXCHANGE_CREDENTIAL_EFFECTS = False
AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED = True
AUTHORIZE_DETAIL_FIELDS_COMPLETE = False
PROVABLE_INSTANCE_FIELDS_CLOSED = True
NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY = True
NON_PROVABLE_INSTANCE_VALUES_STILL_NULL = True
REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS = True
SILENT_DEFAULTS = False
PROPOSED_VALUES = False
INVENTED_VALUES = False

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_input_pack_materialization_decisions_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_CYBERSECURITY_MIRROR_V1.md"
)
PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
PARENT_TRIAD_DECISION_REL = "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
PARENT_REGIME_COVERAGE_DECISION_REL = "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
PARENT_STA_OPEN_INPUTS_CLOSEOUT_REL = "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1.md"
PARENT_SURFACE_B_RATIFICATION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md"
)

ALLOWED_OWNER_VALUES: tuple[str, ...] = (
    "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION",
    "EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION",
)

AUTHORIZE_OWNER_VALUE = "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION"
REJECT_OWNER_VALUE = "EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION"
RECORDED_OWNER_VALUE = AUTHORIZE_OWNER_VALUE

AUTHORIZE_DETAIL_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "instrument_binding_ref",
    "candle_authority_source_ref",
    "mark_price_authority_source_ref",
    "observation_pack_digest",
    "raw_source_digest",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
    "regime_coverage_binding_ref",
)

AUTHORIZE_DETAIL_PROVABLE_FIELDS: tuple[str, ...] = (
    "instrument_binding_ref",
    "candle_authority_source_ref",
    "mark_price_authority_source_ref",
    "regime_coverage_binding_ref",
)

AUTHORIZE_DETAIL_INSTANCE_NULL_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "observation_pack_digest",
    "raw_source_digest",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
)

AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES: dict[str, str] = {
    "instrument_binding_ref": (
        "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding"
    ),
    "candle_authority_source_ref": (
        "venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1"
    ),
    "mark_price_authority_source_ref": (
        "venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1"
    ),
    "regime_coverage_binding_ref": (
        "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
    ),
}

PROVABLE_INSTANCE_FIELDS: tuple[str, ...] = ("instrument_binding",)

PROVABLE_INSTANCE_FIELD_VALUES: dict[str, dict[str, str]] = {
    "instrument_binding": {
        "venue": "okx",
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "venue_instrument_id": "ETH-USDT-SWAP",
        "contract_type": "perpetual",
        "market_type": "futures",
        "quote_currency": "USDT",
        "settlement_currency": "USDT",
    },
}

CLOSED_STA_EXTERNAL_INPUTS: tuple[str, ...] = (
    "venue_native_candle_source_identity",
    "venue_native_mark_source_identity",
)

STA_OPEN_EXTERNAL_INPUTS: tuple[str, ...] = (
    "non_invented_campaign_instance_identity",
    "immutable_pack_provenance_digests",
    "deterministic_campaign_seed",
    "exclusive_tip_event_time_epoch_s",
    "partition_fold_bootstrap_structure",
    "regime_coverage_materialization_readiness",
)

REQUIRE_EXPLICIT_OWNER_VALUES_FOR: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "observation_pack_digest",
    "raw_source_digest",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
    "regime_coverage_counts",
    "regime_coverage_instance",
)

NULL_INSTANCE_KEYS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "instrument_binding",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
    "regime_coverage_counts",
    "regime_coverage_instance",
    "observation_pack_digest",
    "raw_source_digest",
)

REMAINING_NULL_INSTANCE_KEYS: tuple[str, ...] = tuple(
    k for k in NULL_INSTANCE_KEYS if k not in PROVABLE_INSTANCE_FIELDS
)

NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "observation_pack_digest",
    "raw_source_digest",
    "seed",
    "event_time_epoch_s",
    "partition_boundaries",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
    "regime_coverage_counts",
    "regime_coverage_instance",
)

NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_OWNER_VALUE_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "seed",
    "partition_boundaries",
    "partition_boundaries_event_time_epoch_s",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
)

NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_STA_EXTERNAL_INPUT_FIELDS: tuple[str, ...] = (
    "observation_pack_digest",
    "raw_source_digest",
    "event_time_epoch_s",
    "regime_coverage_counts",
    "regime_coverage_instance",
)

NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELD_SPECS: dict[str, dict[str, object]] = {
    "campaign_id": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "non_invented_campaign_instance_identity",
        "allowed_format": "NON_EMPTY_ASCII_SLUG_STRING",
    },
    "dataset_id": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "non_invented_campaign_instance_identity",
        "allowed_format": "NON_EMPTY_ASCII_DATASET_ID_STRING",
    },
    "scenario_id": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "non_invented_campaign_instance_identity",
        "allowed_format": "NON_EMPTY_ASCII_SCENARIO_ID_STRING",
    },
    "observation_pack_digest": {
        "input_class": INPUT_CLASS_STA_EXTERNAL_INPUT,
        "related_sta_open_input": "immutable_pack_provenance_digests",
        "allowed_format": "SHA256_HEX_64",
    },
    "raw_source_digest": {
        "input_class": INPUT_CLASS_STA_EXTERNAL_INPUT,
        "related_sta_open_input": "immutable_pack_provenance_digests",
        "allowed_format": "SHA256_HEX_64",
    },
    "seed": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "deterministic_campaign_seed",
        "allowed_format": "DETERMINISTIC_NON_NEGATIVE_INTEGER_OR_EXPLICIT_SEED_STRING",
    },
    "event_time_epoch_s": {
        "input_class": INPUT_CLASS_STA_EXTERNAL_INPUT,
        "related_sta_open_input": "exclusive_tip_event_time_epoch_s",
        "allowed_format": "UNIX_EPOCH_SECONDS_INTEGER",
    },
    "partition_boundaries": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "ORDERED_LIST_OF_EVENT_TIME_BOUNDARIES",
    },
    "partition_boundaries_event_time_epoch_s": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "ORDERED_LIST_OF_UNIX_EPOCH_SECONDS_INTEGERS",
    },
    "fold_ids": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "ORDERED_LIST_OF_NON_EMPTY_FOLD_ID_STRINGS",
    },
    "bootstrap_seeds": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "ORDERED_LIST_OF_DETERMINISTIC_SEEDS",
    },
    "purge": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "EXPLICIT_OWNER_NUMERIC_OR_EXPLICIT_NULL_RATIFICATION",
    },
    "embargo": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "EXPLICIT_OWNER_NUMERIC_OR_EXPLICIT_NULL_RATIFICATION",
    },
    "fold_sizes": {
        "input_class": INPUT_CLASS_OWNER_VALUE,
        "related_sta_open_input": "partition_fold_bootstrap_structure",
        "allowed_format": "EXPLICIT_OWNER_LIST_OF_POSITIVE_INTEGERS_OR_EXPLICIT_NULL_RATIFICATION",
    },
    "regime_coverage_counts": {
        "input_class": INPUT_CLASS_STA_EXTERNAL_INPUT,
        "related_sta_open_input": "regime_coverage_materialization_readiness",
        "allowed_format": "OBSERVATION_DERIVED_COUNT_OBJECT_FROM_AUTHORIZED_PRODUCER_ONLY",
    },
    "regime_coverage_instance": {
        "input_class": INPUT_CLASS_STA_EXTERNAL_INPUT,
        "related_sta_open_input": "regime_coverage_materialization_readiness",
        "allowed_format": "PRODUCER_BOUND_REGIME_COVERAGE_INSTANCE_OBJECT",
    },
}

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
    "owner_go_base_sha",
    "allowed_owner_values",
    "authorize_detail_fields",
    "sta_open_external_inputs",
    "closed_sta_external_inputs",
    "require_explicit_owner_values_for",
    "parent_authority_refs",
    "forbidden_sources",
    "reject_semantics",
    "authorize_semantics",
    "input_authority",
    "runtime_implemented",
    "campaign_start_authorized",
    "raw_input_pack_materialization_authorized",
    "raw_input_pack_created",
    "campaign_started",
    "pack_materialization",
    "producer_reimplementation",
    "consumer_wiring",
    "pt1m_adapter",
    "productive_numeric_values_set",
    "productive_thresholds_lookbacks",
    "regime_coverage_producer_available",
    "regime_coverage_status",
    "dashboard_authority_effect",
    "notion_ssot",
    "repository_is_ssot",
    "open_null_instance_fields",
    "decisions",
)

FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = (
    "fixture",
    "demo",
    "scenario_scalar",
    "dashboard_readmodel",
    "webui",
    "notion",
    "cmc_volatility",
    "o4_pt1h_as_pt1m_authority",
    "candle_close_as_mark",
    "trade_as_mark",
)

PARENT_AUTHORITY_REF_VALUES: dict[str, str] = {
    "raw_pt1m_pack_owner_decision": PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL,
    "triad_authority_decision": PARENT_TRIAD_DECISION_REL,
    "regime_coverage_producer_decision": PARENT_REGIME_COVERAGE_DECISION_REL,
    "sta_open_inputs_closeout": PARENT_STA_OPEN_INPUTS_CLOSEOUT_REL,
    "surface_b_ratification": PARENT_SURFACE_B_RATIFICATION_REL,
}
