"""Constants for multi-session natural-age typed-vol + actionable-strata evidence v1."""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_"
    "MULTI_SESSION_NATURAL_AGE_TYPED_VOLATILITY_AND_ACTIONABLE_STRATA_EVIDENCE_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_"
    "MULTI_SESSION_NATURAL_AGE_TYPED_VOLATILITY_AND_ACTIONABLE_STRATA_EVIDENCE_V1"
)
REVIEW_MODE_ID = "MULTI_SESSION_NATURAL_AGE_TYPED_VOLATILITY_AND_ACTIONABLE_STRATA_EVIDENCE_V1"
CAPABILITY_VERSION = (
    "canonical_volatility_numeric_max_age_multi_session_natural_age_"
    "typed_volatility_and_actionable_strata_evidence/v1"
)

OWNER = (
    "research.canonical_volatility_numeric_max_age_multi_session_natural_age_"
    "typed_volatility_and_actionable_strata_evidence_v1"
)

# Hard strategy boundaries (observational capability only).
MASTER_V2_ORCHESTRATION_SEMANTICS_UNCHANGED = True
DOUBLE_PLAY_TRADING_LOGIC_UNCHANGED = True
BULL_BEAR_DIRECTIONAL_LOGIC_UNCHANGED = True
ENTRY_EXIT_POLICY_UNCHANGED = True
RISK_POLICY_UNCHANGED = True
SAFETY_POLICY_UNCHANGED = True
NO_POLICY_ENFORCEMENT = True
NUMERIC_MAX_AGE_SELECTED = False
POLICY_ENFORCEMENT_ADDED = False
HARD_STOP = True

# Scaffold removal invariants.
SYNTHETIC_VOLATILITY_VALUES_FORBIDDEN = True
STATIC_VOLATILITY_DEFAULT_FORBIDDEN = True
HARDCODED_AGE_DECISION_PROBE_FORBIDDEN = True
HARDCODED_3600_SECOND_BRANCH_FORBIDDEN = True
AGED_ESTIMATE_MUTATION_FORBIDDEN = True
FRESH_ESTIMATE_MUST_USE_CANONICAL_ESTIMATOR = True
MARKET_EVENT_TIME_IS_AGE_AUTHORITY = True
RUNTIME_CYCLE_IS_NOT_AGE_AUTHORITY = True
POLL_COUNT_IS_NOT_AGE_AUTHORITY = True

# Early-age density.
DISTINCT_MARKET_SAMPLE_SEMANTICS_PRESERVED = True
EARLY_AGE_DENSITY_DOES_NOT_FABRICATE_MARKET_TIME = True
NETWORK_PACING_BUDGET_PRESERVED = True
NO_ZERO_INTERVAL_BURSTS = True
ARTIFICIAL_AGE_FORBIDDEN = True

# Readiness defaults (session execution still separately GO'd).
READY_FOR_POLICY_SELECTION = False
READY_FOR_POLICY_IMPLEMENTATION = False
READY_FOR_POLICY_ENFORCEMENT = False
PRODUCTIVE_SESSION_EXECUTION_IN_DEFAULT_IMPORT = False

# Schemas.
SCHEMA_TYPED_VOL_COMPARISON = "canonical_volatility_numeric_max_age_typed_volatility_comparison/v1"
SCHEMA_FULL_ALPHA_COUNTERFACTUAL = (
    "canonical_volatility_numeric_max_age_full_alpha_counterfactual/v1"
)
SCHEMA_OPPORTUNITY_STRATA = "canonical_volatility_numeric_max_age_opportunity_strata/v1"
SCHEMA_CAMPAIGN_AGGREGATION = (
    "canonical_volatility_numeric_max_age_multi_session_campaign_aggregation/v1"
)
SCHEMA_READINESS = "canonical_volatility_numeric_max_age_multi_session_typed_vol_readiness/v1"

# Opportunity strata enums (versioned).
OPPORTUNITY_STRATA_V1: tuple[str, ...] = (
    "NO_ACTIONABLE_OPPORTUNITY",
    "LONG_DIRECTIONAL_OPPORTUNITY",
    "SHORT_DIRECTIONAL_OPPORTUNITY",
    "LONG_COMPOSITION_SELECTED",
    "SHORT_COMPOSITION_SELECTED",
    "LONG_ARMED",
    "SHORT_ARMED",
    "LONG_ENTRY_ELIGIBLE",
    "SHORT_ENTRY_ELIGIBLE",
    "ENTRY_BLOCKED_BY_NON_AGE_REASON",
    "ENTRY_BLOCKED_BY_AGE_ONLY",
    "OPEN_POSITION_EXIT_RELEVANT",
    "OPEN_POSITION_REDUCE_RELEVANT",
)

COUNTERFACTUAL_CLASSIFICATIONS_V1: tuple[str, ...] = (
    "NO_DECISION_CHANGE",
    "DIRECTIONAL_ASSESSMENT_CHANGE",
    "SURVIVAL_CHANGE",
    "SUITABILITY_CHANGE",
    "COMPOSITION_CHANGE",
    "SWITCH_STATE_CHANGE",
    "ENTRY_PERMISSION_CHANGE",
    "ENTRY_OUTCOME_CHANGE",
    "HOLD_REDUCE_EXIT_CHANGE",
    "NOT_COMPARABLE",
    "FRESH_ESTIMATE_UNAVAILABLE",
    "UNKNOWN",
)

EARLY_AGE_BUCKETS_SECONDS: tuple[tuple[int, int, str], ...] = (
    (0, 60, "0-60"),
    (61, 120, "61-120"),
    (121, 300, "121-300"),
)

# Forbidden scaffold fingerprints (must not reappear in productive writers).
FORBIDDEN_SCAFFOLD_SUBSTRINGS: tuple[str, ...] = (
    "old_vol = 0.12",
    "fresh_vol = 0.12 + (0.0001 * vol_count)",
    "age < 3600",
    'fresh_decision = "HOLD" if age < 3600 else "BLOCK_ALPHA_AGE_ONLY"',
)

REUSED_TYPED_ESTIMATE_FACTORY = "build_canonical_volatility_estimate_v1"
REUSED_TYPED_MATERIALIZER = "materialize_typed_canonical_volatility_estimate_v1"
REUSED_CMC_BINDER = "bind_typed_canonical_volatility_estimate_into_market_context_v1"
REUSED_LIFECYCLE_HOST = "NaturalAgeProgressionLifecycleHostV1"
REUSED_STRATA_PROJECTOR = "project_actionable_alpha_strata_v1"
REUSED_S03_INDEPENDENCE = "build_exit_risk_safety_independence_record_v1"

ARTIFACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_multi_session_natural_age_"
    "typed_volatility_and_actionable_strata_evidence_contract_v1.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_"
    "MULTI_SESSION_NATURAL_AGE_TYPED_VOLATILITY_AND_ACTIONABLE_STRATA_EVIDENCE_V1.md"
)

CAMPAIGN_AGGREGATION_FILENAME = "campaign_aggregation_v1.json"
S03_LEGACY_SESSION_REL = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_additional_evidence_campaign_v2_8312cd8d1b71c65b/sessions/S03"
)
# Frozen digests from preflight (must remain unchanged by this capability).
S03_FROZEN_FILE_DIGESTS: dict[str, str] = {
    "connectivity_events.jsonl": (
        "75792192a333d14eeb1ee4b4037d0e2c81f1d1d08f5d101495abf04c5fcf88e2"
    ),
    "counterfactual_decisions.jsonl": (
        "c3e7244c0e38e18418cd8212ddf4e8900bba83be7e6387bd6da0eab89b73e1f1"
    ),
    "decision_sensitivity.jsonl": (
        "e9bfb5d29d4dfed64b3e4f732d8fdc14fea4752568930146e127732a89c5a033"
    ),
    "exit_risk_safety_independence.jsonl": (
        "a2b47248921eb12c392341068f8ab7603b164f2af7f110db9348d9211a66d83f"
    ),
    "heartbeat.jsonl": "291a774c890bc2553c68e8b256e8df580c814112ced04b218253553a6673af40",
    "integrity_manifest.json": ("238f66a64b429c40ff26a2ce24073e8e788cbf6eb52b098c92d7a16c00056d7a"),
    "market_samples.jsonl": "dbe417fa1b5ebb4656271bbb1bd1a0c51f7b576fcd4bc2a8ae896308a7002ebc",
    "session_metadata.json": "5cff1155ec7447b229e1cb7e76d51abb892e21f6e97486982290ef68dbd6b8f1",
    "terminal_verdict.json": "99b753f2e945319f274033bd23aae938c37da9e3d2e421648e8202b42cf22a52",
    "volatility_drift_comparisons.jsonl": (
        "7064cc037052632f56603e7bd7ffc22679c65f7a8aa5b7e046d1ea3a998a7fd0"
    ),
    "volatility_records.jsonl": (
        "acd5e3b489d5698c66dba634be0baf9b64f753dcb0581549e30fe6cb5aba5a81"
    ),
}
