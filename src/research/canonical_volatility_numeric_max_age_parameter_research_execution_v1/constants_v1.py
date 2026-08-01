"""Constants for non-enforcing numeric max-age parameter research execution v1."""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1=true"
)

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1"
CAPABILITY_VERSION = "canonical_volatility_numeric_max_age_parameter_research_execution/v1"
RESEARCH_EXECUTION_OWNER = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1"
)

SCHEMA_VERSION = "canonical_volatility_numeric_max_age_parameter_research_execution/v1"
CANDIDATE_DOMAIN_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_candidate_domain/v1"
HYPOTHESIS_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_hypothesis_contract/v1"
SPLIT_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_split_and_embargo_contract/v1"
ROBUSTNESS_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_robustness_execution_contract/v1"
MANIFEST_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_research_execution_manifest/v1"
INPUT_EVIDENCE_MANIFEST_SCHEMA_VERSION = (
    "canonical_volatility_numeric_max_age_input_evidence_manifest/v1"
)
CONCLUSION_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_research_conclusion/v1"
INTEGRITY_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_research_integrity_manifest/v1"

EXPECTED_PREREGISTRATION_DIGEST = "965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537"

# Operator-bound research arguments only (not config / policy / productive defaults).
# Source authority: EXPLICIT_OPERATOR_OR_CALLER_SUPPLIED_CANDIDATE_ARGUMENTS_ONLY
# from CanonicalVolatilityMaxAgeResearchDesignContractV1.
OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS: tuple[int, ...] = (
    60,
    120,
    300,
    600,
    900,
    1800,
    3600,
    7200,
)
BASELINE_CANDIDATE_ID = "UNRESOLVED_MAX_AGE_NON_ENFORCING"
AGE_REFERENCE_CLOCK = "MARKET_EVENT_TIME"
AGE_UNIT = "SECONDS"
AGE_FORMULA = "reference_market_event_time_minus_volatility_as_of_event_time"

RESEARCH_QUESTION = (
    "Welcher, falls überhaupt ein solcher existiert, robuste Bereich für die "
    "maximal zulässige Event-Time-Alterung eines kanonischen "
    "VolatilityEstimate reduziert stale-estimate exposure, ohne belastbare "
    "Entscheidungsqualität, Coverage oder Regime-Robustheit unvertretbar zu "
    "verschlechtern?"
)
NULL_HYPOTHESIS_H0 = (
    "Innerhalb des preregistrierten Candidate-Domains existiert kein "
    "robuster numerischer Maximum-Age-Bereich, der gegenüber der "
    "unresolved/non-enforcing Baseline über Walk-Forward-, Holdout-, "
    "Regime- und Stress-Auswertungen hinweg einen stabilen Nettonutzen zeigt."
)
ALTERNATIVE_HYPOTHESIS_H1 = (
    "Mindestens ein zusammenhängender Candidate-Bereich zeigt gegenüber der "
    "unresolved/non-enforcing Baseline einen reproduzierbaren und robusten "
    "Nettonutzen, ohne die preregistrierten Rejection Criteria zu verletzen."
)

# Deterministic embargo derivation horizons (seconds), bound before evaluation.
LOOKBACK_BARS = 60
BAR_INTERVAL_SECONDS = 60
LOOKBACK_HORIZON_SECONDS = LOOKBACK_BARS * BAR_INTERVAL_SECONDS  # 3600
HOLDING_HORIZON_SECONDS = LOOKBACK_HORIZON_SECONDS
SURVIVAL_HORIZON_SECONDS = LOOKBACK_HORIZON_SECONDS
LABEL_HORIZON_SECONDS = LOOKBACK_HORIZON_SECONDS
EMBARGO_SECONDS = max(
    LOOKBACK_HORIZON_SECONDS,
    HOLDING_HORIZON_SECONDS,
    SURVIVAL_HORIZON_SECONDS,
    LABEL_HORIZON_SECONDS,
)

WALK_FORWARD_FOLDS = 3
HOLDOUT_FRACTION = 0.20
TRAIN_FRACTION_WITHIN_NON_HOLDOUT = 0.70
BOOTSTRAP_REPETITIONS = 200
BOOTSTRAP_BLOCK_SECONDS = EMBARGO_SECONDS
BOOTSTRAP_SEED = 0xC0FFEE01
NEIGHBORHOOD_PERTURBATION_FACTORS: tuple[float, ...] = (0.9, 1.1)

MINIMUM_SESSION_COUNT = 2
MINIMUM_REGIME_COUNT = 2
MINIMUM_EVIDENCE_COUNT = 8
MAX_STALE_REJECTION_RATE = 0.85
MAX_COVERAGE_REDUCTION_VS_BASELINE = 0.50
MAX_NEIGHBORHOOD_SENSITIVITY = 0.35
MAX_WALK_FORWARD_INSTABILITY = 0.40

DEFAULT_INPUT_LEDGER_RELATIVE_PATH = (
    "docs/evidence/canonical_volatility_numeric_max_age_research_evidence_ledger_v1/"
    "research_evidence_ledger.jsonl"
)
DEFAULT_OUTPUT_EVIDENCE_RELATIVE_ROOT = (
    "docs/evidence/canonical_volatility_numeric_max_age_parameter_research_execution_v1"
)

# Hard safety flags — research evidence only, never trading authority.
NUMERIC_MAX_AGE_DECIDED = False
THRESHOLD_STATUS = "UNRESOLVED_MAX_AGE"
NUMERIC_THRESHOLD_SELECTED = False
PARAMETER_PROMOTED = False
ENFORCEMENT_APPLIED = False
ENFORCEMENT_DURING_RESEARCH = False
COUNTERFACTUAL_ONLY = True
ALPHA_DECISION_MUTATION_ALLOWED = False
ALPHA_MUTATION_OCCURRED = False
PRODUCTIVE_TRADING_BEHAVIOR_CHANGED = False
LIVE_TESTNET_ORDER_ACTIVATION_OCCURRED = False
LIVE_AUTHORIZATION = False
HARD_STOP = True
READY_FOR_THRESHOLD_SELECTION = False
READY_FOR_PARAMETER_PROMOTION = False
READY_FOR_ENFORCEMENT = False

AUTHORITY_SCOPE = "RESEARCH_EVIDENCE_ONLY"
NON_AUTHORITY_SCOPE = (
    "NOT_TRADING_AUTHORITY;"
    "NOT_ALPHA_AUTHORITY;"
    "NOT_POLICY_DEFAULT;"
    "NOT_CONFIG_DEFAULT;"
    "NOT_ORDER_AUTHORITY;"
    "NOT_LIVE_AUTHORITY"
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "trading.execution",
    "src.execution",
    "trading.live",
    "src.live",
    "exchange_order",
    "place_order",
    "submit_order",
    "broker_adapter",
)

RESEARCH_CONCLUSION_NO_ROBUST = "NO_ROBUST_NUMERIC_MAX_AGE_ESTABLISHED"
RESEARCH_CONCLUSION_REGION_PENDING = "ROBUST_CANDIDATE_REGION_IDENTIFIED_PENDING_OWNER_RATIFICATION"
RESEARCH_CONCLUSION_INSUFFICIENT = "INSUFFICIENT_RESEARCH_EVIDENCE"

CLI_REL_PATH = (
    "scripts/ops/run_canonical_volatility_numeric_max_age_parameter_research_execution_v1.py"
)
SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1.md"
)
