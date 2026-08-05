"""Constants for Surface-B raw PT1M observation-input + exclusive-tip proof v1.

PACK_MATERIALIZATION=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
DOWNLOAD_OR_NETWORK_FETCH=STA_EXPLICITLY_AUTHORIZED_ONLY
DASHBOARD_AUTHORITY_EFFECT=NONE
INVENTED_VALUES=false
SILENT_DEFAULTS=false
PROPOSED_VALUES=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1=true"
)
OWNER = (
    "ops.productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_pt1m_observation_input_and_exclusive_tip_proof_v1"
)
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_pt1m_observation_input_and_exclusive_tip_proof_decisions/v1"
)
DOCUMENT_TYPE = "OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_DECISIONS_MANIFEST"
STATUS_PROOF_CONTRACT_READY_NUMERIC_UNRESOLVED = (
    "OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_"
    "CONTRACT_READY_NUMERIC_PROOFS_STILL_UNRESOLVED"
)

DECISION_ID = "DEC_RAW_INPUT_PACK_MATERIALIZATION"
DECISION_STATUS_RATIFIED = "RATIFIED"
OWNER_VALUE = "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION"
OWNER_GO = "OWNER_STA_SURFACE_B_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1"
OWNER_GO_BASE_SHA = "86d5eb3893647c8a77233569cccbd106245e5e09"
AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"

SCOPE = "STA_INPUT_PROOF_DOCS_MANIFEST_SCHEMA_VALIDATOR_EVIDENCE_ONLY"
BAR_INTERVAL = "PT1M"
BAR_INTERVAL_SECONDS = 60
CANDLE_EVENT_TIME_SEMANTICS = "PT1M_BUCKET_OPEN_EVENT_TIME"
MARK_EVENT_TIME_SEMANTICS = "PT1M_BUCKET_OPEN_EVENT_TIME"
EXCLUSIVE_TIP_FORMULA = "last_finalized_bar_open_event_time_epoch_s+60"
EXCLUSIVE_TIP_OFFSET_SECONDS = 60
DOWNLOAD_OR_NETWORK_FETCH_POLICY = "STA_EXPLICITLY_AUTHORIZED_ONLY"

CANDLE_AUTHORITY_SOURCE_REF = "venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1"
MARK_AUTHORITY_SOURCE_REF = (
    "venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1"
)

REQUIRED_INSTRUMENT_BINDING_V1: dict[str, str] = {
    "venue": "okx",
    "canonical_instrument_id": "inst-eth-usdt-perp",
    "venue_instrument_id": "ETH-USDT-SWAP",
    "contract_type": "perpetual",
    "market_type": "futures",
    "quote_currency": "USDT",
    "settlement_currency": "USDT",
}
INSTRUMENT_BINDING_FIELDS: tuple[str, ...] = tuple(REQUIRED_INSTRUMENT_BINDING_V1.keys())

AUTHORIZED_SOURCE_CLASSES: tuple[str, ...] = (
    "VENUE_NATIVE_OKX_PUBLIC_HISTORY_CANDLES_PT1M_CONFIRM_1",
    "VENUE_NATIVE_OKX_PUBLIC_HISTORY_MARK_PRICE_CANDLES_PT1M_CONFIRM_1",
)

FORBIDDEN_SOURCE_CLASSES: tuple[str, ...] = (
    "DASHBOARD_SOURCE",
    "OKX_ARCHIVE_AS_AUTHORITY",
    "FIXTURE_DEMO_SYNTHETIC_SOURCE",
    "O4_PT1H_AS_PT1M_AUTHORITY",
    "CANDLE_CLOSE_AS_MARK",
    "NOTION_AS_AUTHORITY",
)

FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = (
    "dashboard",
    "okx_archive",
    "fixture",
    "demo",
    "synthetic",
    "o4_pt1h",
    "candle_close_as_mark",
    "notion",
)

NUMERIC_PROOF_NULL_FIELDS: tuple[str, ...] = (
    "candle_row_count",
    "mark_row_count",
    "first_finalized_bucket_open_event_time_epoch_s",
    "last_finalized_bucket_open_event_time_epoch_s",
    "exclusive_tip_event_time_epoch_s",
    "observation_pack_digest",
    "raw_source_digest",
)

UNRESOLVED_FIELDS: tuple[str, ...] = (
    "candle_row_count",
    "mark_row_count",
    "first_finalized_bucket_open_event_time_epoch_s",
    "last_finalized_bucket_open_event_time_epoch_s",
    "exclusive_tip_event_time_epoch_s",
    "pt1m_alignment_concrete_epoch_proof",
    "candle_mark_join_concrete_proof",
    "contiguity_concrete_proof",
    "duplicate_free_concrete_proof",
    "observation_pack_digest",
    "raw_source_digest",
    "digest_bound_row_counts",
    "authorized_observation_window",
)

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_DECISIONS_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_pt1m_observation_input_and_exclusive_tip_proof_decisions_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF_CYBERSECURITY_MIRROR_V1.md"
)
PARENT_MATERIALIZATION_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1.md"
)
PARENT_MATERIALIZATION_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json"
)
PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
PARENT_TRIAD_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
)
PARENT_TRIAD_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json"
)

PROOF_CONTRACT_READY = True
STA_EXTERNAL_INPUT_FIELDS_READY = False
OWNER_PARTITION_SELECTION_READY = False
NUMERIC_PROOFS_RESOLVED = False

PACK_MATERIALIZATION = False
RAW_INPUT_PACK_CREATED = False
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = False
CAMPAIGN_START = False
INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
REGIME_COVERAGE_PRODUCER_AVAILABLE = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_THRESHOLDS_LOOKBACKS = False
TRADING_LOGIC_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
O4_UNCHANGED = True
O4_PT1H_AS_PT1M_FORBIDDEN = True
ORDERS_TESTNET_LIVE = False
INVENTED_VALUES = False
SILENT_DEFAULTS = False
PROPOSED_VALUES = False
DOWNLOAD_OR_NETWORK_FETCH = False
FILL_PARTITION_BOUNDARIES = False
OWNER_PARTITION_SELECTION = False
