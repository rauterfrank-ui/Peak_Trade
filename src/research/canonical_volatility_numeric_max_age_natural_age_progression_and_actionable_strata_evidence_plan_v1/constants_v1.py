"""Constants for natural age progression and actionable strata evidence plan v1."""

from __future__ import annotations

from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    WARMUP_REQUIRED_PRICE_COUNT,
)
from trading.master_v2.canonical_volatility_estimate_materializer_v1 import BAR_INTERVAL_SECONDS
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_"
    "AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_"
    "AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1"
)
CAPABILITY_VERSION = (
    "canonical_volatility_numeric_max_age_natural_age_progression_"
    "and_actionable_strata_evidence_plan/v1"
)
REVIEW_MODE_ID = CAPABILITY_ID
OWNER = (
    "research.canonical_volatility_numeric_max_age_natural_age_progression_"
    "and_actionable_strata_evidence_plan_v1"
)

# Derived research wiring — NOT a max-age policy recommendation.
PT1M_BAR_INTERVAL_SECONDS = int(BAR_INTERVAL_SECONDS)
PT60M_REQUIRED_PRICE_OBSERVATIONS = int(WARMUP_REQUIRED_PRICE_COUNT)
PT60M_HORIZON_SECONDS = PT1M_BAR_INTERVAL_SECONDS * max(PT60M_REQUIRED_PRICE_OBSERVATIONS - 1, 1)
RESEARCH_AGE_GRID_SECONDS: tuple[int, ...] = tuple(
    int(x) for x in RESEARCH_AGE_CANDIDATE_GRID_SECONDS
)
NATURAL_7200_TARGET_SECONDS = 7200
# Preregistration reachability requires natural age >= 7200; one PT1M step beyond.
RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS = 7201
# With PT1M cadence, 120 intervals → 7200s; require one additional distinct obs before recompute.
RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS = 121

RESEARCH_WIRING_LABEL = "RESEARCH_ESTIMATE_RECOMPUTE_WIRING_NOT_MAX_AGE_POLICY"
SOURCE_WINDOW_ORDINARY_SLIDE_DOES_NOT_RECOMPUTE = True

AGE_REFERENCE_CLOCK = "MARKET_EVENT_TIME"
AGE_FORMULA_VERSION = "reference_market_event_time_minus_volatility_as_of_event_time/v1"

# Hard non-goals / invariants
ESTIMATE_RECOMPUTE_TRIGGER_EXPLICIT = True
ESTIMATE_REUSE_EXPLICIT = True
ESTIMATE_REUSE_DOES_NOT_MUTATE_ESTIMATE = True
ESTIMATE_AS_OF_EVENT_TIME_IMMUTABLE_DURING_REUSE = True
AGE_DERIVED_FROM_EVENT_TIME_ONLY = True
RUNTIME_CYCLE_CANNOT_ADVANCE_AGE = True
DUPLICATE_OBSERVATION_CANNOT_ADVANCE_AGE = True
OUT_OF_ORDER_OBSERVATION_CANNOT_NEGATIVELY_ADVANCE_AGE = True
NO_SLEEP_BASED_AGE_SYNTHESIS = True
NO_TIMESTAMP_INJECTION = True
NO_POLICY_ENFORCEMENT = True
NUMERIC_MAX_AGE_SELECTED = False
NUMERIC_MAX_AGE_ENFORCING = False
ENFORCEMENT_APPLIED = False
THRESHOLD_SELECTED = False
ALPHA_MUTATION = False
STATE_MUTATION = False
MASTER_V2_LOGIC_CHANGED = False
DOUBLE_PLAY_LOGIC_CHANGED = False
BULL_BEAR_LOGIC_CHANGED = False
LIVE_AUTHORIZATION = False
HARD_STOP = True
BLOCKED_FOR_PARAMETER_DECISION = True
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = False
READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION = False

ALPHA_ONLY_COUNTERFACTUAL_BLOCK = True
EXIT_COUNTERFACTUAL_BLOCK = False
RISK_COUNTERFACTUAL_BLOCK = False
SAFETY_COUNTERFACTUAL_BLOCK = False
RECONCILIATION_COUNTERFACTUAL_BLOCK = False

COVERAGE_PLAN_SCHEMA = (
    "canonical_volatility_numeric_max_age_natural_age_progression_"
    "additional_evidence_coverage_plan/v1"
)
COVERAGE_PLAN_ARTIFACT_PATH = (
    "config/research/canonical_volatility_numeric_max_age_natural_age_progression_"
    "additional_evidence_coverage_plan_v1.json"
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "execution.live",
    "place_order",
    "submit_order",
    "broker_adapter",
)

SAFETY_RISK_EXIT_ACTION_KEYS: tuple[str, ...] = (
    "SAFETY_EXIT",
    "HARD_RISK_REDUCE",
    "POSITION_RECONCILIATION",
    "MANDATORY_ADVERSE_REDUCE",
    "PROFIT_EXIT",
    "TIME_EXIT",
    "INVALIDATION_EXIT",
)
