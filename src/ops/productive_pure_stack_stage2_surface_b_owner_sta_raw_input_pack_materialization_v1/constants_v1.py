"""Constants for Surface-B Owner/STA raw input-pack materialization execution v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CAMPAIGN_START=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_TESTNET_LIVE=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_V1=true"
)
OWNER = "ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1"
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization/v1"
)
DOCUMENT_TYPE = "OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_EXECUTION_MANIFEST"

OWNER_GO = "OWNER_STA_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION_V1"
OWNER_GO_BASE_SHA = "24da36c1b4ded14a376d9f73555a0cba28b41204"
SCOPE = "RAW_INPUT_PACK_MATERIALIZATION_ONLY"
STATUS = "OWNER_STA_RAW_INPUT_PACK_MATERIALIZED_OBSERVATION_DIGEST_COMPUTED_REMAINING_NULL"
DECISION_ID = "DEC_RAW_INPUT_PACK_MATERIALIZATION"
DECISION_STATUS = "RATIFIED"
OWNER_VALUE = "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION"

AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"

PACK_MATERIALIZATION = True
RAW_INPUT_PACK_CREATED = True
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = True
CAMPAIGN_START = False
CAMPAIGN_START_AUTHORIZED = False
CAMPAIGN_STARTED = False
INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
REGIME_COVERAGE_PRODUCER_AVAILABLE = False
REGIME_COVERAGE_STATUS = "SEMANTICALLY_UNRESOLVED"
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_THRESHOLDS_LOOKBACKS = False
TRADING_LOGIC_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
ORDERS_TESTNET_LIVE = False
INVENTED_VALUES = False
SILENT_DEFAULTS = False
PROPOSED_VALUES = False
USE_RECORDED_INSTANCE_VALUES = True
CAMPAIGN_ID_EXPLICIT_LEAVE_NULL = True
REGIME_COVERAGE_LEAVE_NULL_UNTIL_STA_PRODUCER_PROOF = True

DATASET_ID = "surface_b_eth_usdt_swap_pt1m_okx_public_tip1785934680_v1"
SCENARIO_ID = "surface_b_regime_coverage_structural_partition_v1"
SEED = 5745001
EVENT_TIME_EPOCH_S = 1_785_934_680
RAW_SOURCE_DIGEST = "9ea3edd6b0b7051a647ff3e6dd64da524b0bbb3ca6850a699c37936ad9541a57"
OBSERVATION_PACK_DIGEST = "268b2e67b350bfa0cf2310a75b1d2710a45dca277b182205dfe12692131a0676"
CONFIG_DIGEST = "577a327df1a7bcfc8be394cca6db370f7d33675c92c80432d7d069dae5c6c419"
REPOSITORY_SHA = OWNER_GO_BASE_SHA
INGESTION_TIMESTAMP = "2026-08-05T12:58:48Z"
FINALIZATION_TIMESTAMP = "2026-08-05T12:58:49Z"
BAR_COUNT = 299
FIRST_BAR_OPEN_EVENT_TIME_EPOCH_S = 1_785_916_740
LAST_BAR_OPEN_EVENT_TIME_EPOCH_S = 1_785_934_620
OBSERVATION_PACK_CANONICAL_JSON_SHA256 = (
    "af3ef5f70315e80f1b0e48769b02fbe1b479456526946405e972ef38908f6ff4"
)

INSTRUMENT_BINDING: dict[str, str] = {
    "venue": "okx",
    "canonical_instrument_id": "inst-eth-usdt-perp",
    "venue_instrument_id": "ETH-USDT-SWAP",
    "contract_type": "perpetual",
    "market_type": "futures",
    "quote_currency": "USDT",
    "settlement_currency": "USDT",
}

PARTITION_BOUNDARIES_EVENT_TIME_EPOCH_S: tuple[int, ...] = (
    1_785_916_740,
    1_785_921_240,
    1_785_925_740,
    1_785_930_240,
    1_785_934_680,
)
FOLD_IDS: tuple[str, ...] = ("train", "calibration", "validation", "holdout")
BOOTSTRAP_SEEDS: tuple[int, ...] = (574_500_101, 574_500_102, 574_500_103, 574_500_104)

REMAINING_NULL_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "regime_coverage_counts",
    "regime_coverage_instance",
)

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_EXECUTION_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_input_pack_materialization_execution_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_CYBERSECURITY_MIRROR_EXECUTION_V1.md"
)
ARTIFACTS_REL = (
    "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
    "raw_input_pack_materialization_v1"
)
OBSERVATION_PACK_REL = f"{ARTIFACTS_REL}/observation_pack.json"
MATERIALIZATION_PROOF_REL = f"{ARTIFACTS_REL}/materialization_proof.json"
OBSERVATION_PACK_DIGEST_TXT_REL = f"{ARTIFACTS_REL}/observation_pack_digest.txt"

PARENT_MATERIALIZATION_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISION_V1.md"
)
PARENT_MATERIALIZATION_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "RAW_INPUT_PACK_MATERIALIZATION_DECISIONS_V1.json"
)
PARENT_OKX_TIP_PROOF_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF_V1.md"
)
CANDLE_RAW_REL = (
    "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
    "okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/candle_raw_http_response.json"
)
MARK_RAW_REL = (
    "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
    "okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/mark_raw_http_response.json"
)
SEALED_TIP_PROOF_ARTIFACT_REL = (
    "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
    "okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/numeric_tip_proof.json"
)

HTTP_RESPONSE_METADATA_REL = (
    "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
    "okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1/http_response_metadata.json"
)
