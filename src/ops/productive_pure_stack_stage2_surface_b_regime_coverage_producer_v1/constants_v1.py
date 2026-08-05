"""Constants for dedicated Surface-B regime-coverage producer v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED
DASHBOARD_AUTHORITY_EFFECT=NONE
NO_INVENTED_THRESHOLDS=true
NO_INVENTED_LOOKBACKS=true
NO_INVENTED_COVERAGE_COUNTS=true
"""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_REGIME_COVERAGE_PRODUCER_V1"
PACKAGE_MARKER = "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_REGIME_COVERAGE_PRODUCER_V1=true"
OWNER = "ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1"

CANONICAL_PRODUCER_NAME = "surface_b_regime_coverage_producer_v1"
CANONICAL_PRODUCER_VERSION = "v1"
VERSIONED_PRODUCER_ID = "productive_pure_stack_stage2_surface_b_regime_coverage_producer/v1"

AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"
TIME_BASIS = "EVENT_TIME_PT1M_FINALIZED_BAR_CLOSE_UTC"
PT1M_SECONDS = 60

TAXONOMY_BINDING = "TAXONOMY_SINK_EXCLUSIVE:low|mid|high|unknown|missing"
TAXONOMY_SINK_LABELS: tuple[str, ...] = (
    "low",
    "mid",
    "high",
    "unknown",
    "missing",
)

THRESHOLD_AUTHORITY_REF = "OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1"
LOOKBACK_WINDOW_AUTHORITY_REF = "OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1"

PIT_NO_LOOKAHEAD_RULES_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/pit_rules_v1.py"
)
CANDLE_JOIN_ACCEPTANCE_REF = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority"
)
MARK_JOIN_ACCEPTANCE_REF = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority"
)
INSTRUMENT_BINDING_ACCEPTANCE_REF = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#instrument_binding"
)
DETERMINISM_CONTRACT_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "determinism_contract_v1.py"
)
REPRODUCIBILITY_CONTRACT_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "reproducibility_contract_v1.py"
)
PRODUCER_DIGEST_CONTRACT_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "digest_contract_v1.py"
)
MISSING_LABEL_SEMANTICS_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "label_semantics_v1.py#missing"
)
UNKNOWN_LABEL_SEMANTICS_REF = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "label_semantics_v1.py#unknown"
)

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
)
PRODUCER_SPEC_REL = "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_REGIME_COVERAGE_PRODUCER_V1.md"

INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
RAW_INPUT_PACK_CREATED = False
CAMPAIGN_STARTED = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
REGIME_COVERAGE_PRODUCER_AVAILABLE = False
REGIME_COVERAGE_STATUS = "SEMANTICALLY_UNRESOLVED"
DASHBOARD_AUTHORITY_EFFECT = "NONE"
EXISTING_PRODUCERS_ELEVATED = False
TRADING_LOGIC_CHANGED = False
ORDERS_TESTNET_LIVE_PAPER_EFFECTS = False
EXCHANGE_CREDENTIAL_EFFECTS = False
PRODUCTIVE_EMISSION = False
INVENT_THRESHOLDS = False
INVENT_LOOKBACKS = False
INVENT_COVERAGE_COUNTS = False
CLASSIFY_LOW_MID_HIGH_WITHOUT_OWNER_THRESHOLDS = False

FORBIDDEN_EXISTING_PRODUCER_TOKENS: tuple[str, ...] = (
    "analytics.regimes",
    "regime.detectors",
    "feature_regime_pipeline_v2",
    "ai.switch_layer",
    "research max-age regime map",
    "bull/bear evidence readmodel",
    "reporting regime buckets",
    "Dashboard projections",
    "Test fixtures",
)

AUTHORIZE_DETAIL_FIELD_VALUES: dict[str, str] = {
    "canonical_producer_name": CANONICAL_PRODUCER_NAME,
    "canonical_producer_version": CANONICAL_PRODUCER_VERSION,
    "versioned_producer_id": VERSIONED_PRODUCER_ID,
    "taxonomy_binding": TAXONOMY_BINDING,
    "threshold_authority_ref": THRESHOLD_AUTHORITY_REF,
    "lookback_window_authority_ref": LOOKBACK_WINDOW_AUTHORITY_REF,
    "time_basis": TIME_BASIS,
    "PIT_no_lookahead_rules_ref": PIT_NO_LOOKAHEAD_RULES_REF,
    "candle_join_acceptance_ref": CANDLE_JOIN_ACCEPTANCE_REF,
    "mark_join_acceptance_ref": MARK_JOIN_ACCEPTANCE_REF,
    "instrument_binding_acceptance_ref": INSTRUMENT_BINDING_ACCEPTANCE_REF,
    "determinism_contract_ref": DETERMINISM_CONTRACT_REF,
    "reproducibility_contract_ref": REPRODUCIBILITY_CONTRACT_REF,
    "producer_digest_contract_ref": PRODUCER_DIGEST_CONTRACT_REF,
    "missing_label_semantics_ref": MISSING_LABEL_SEMANTICS_REF,
    "unknown_label_semantics_ref": UNKNOWN_LABEL_SEMANTICS_REF,
}
