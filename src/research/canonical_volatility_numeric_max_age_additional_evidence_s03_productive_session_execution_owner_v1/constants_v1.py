"""Constants for Additional-Evidence S03 productive session execution owner v1.

Capability only: defines the sole typed execution owner for S03 under Auth-v2.
Does not consume production authorization, start a real session, open network,
or write production evidence during capability merge.
"""

from __future__ import annotations

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_VERSION,
    REQUIRED_DURATION_SECONDS,
    REQUIRED_INSTRUMENT,
    REQUIRED_NETWORK_SCOPE,
    REQUIRED_SESSION_SCOPE,
    REQUIRED_VENUE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    BOUND_RUNBOOK_DIGEST,
    DEFAULT_CODE_BASELINE_SHA,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    PUBLIC_MD_ENDPOINT_ALLOWLIST,
    PUBLIC_MD_METHOD_ALLOWLIST,
    BOUND_PUBLIC_MD_HOST_V1,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_PRODUCTIVE_SESSION_EXECUTION_OWNER_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_PRODUCTIVE_SESSION_EXECUTION_OWNER_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID
OWNER = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_"
    "s03_productive_session_execution_owner_v1"
)
CANONICAL_EXECUTION_OWNER_SYMBOL = "run_additional_evidence_s03_productive_session_v1"

CLI_MODE = "additional-evidence-s03-session-run"
EXISTING_CLI_OWNER = (
    "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)
EXISTING_S01_S02_RUNNER_CLI_MODE = "productive-preregistered-session-run"

# Bound S03 identity (exact).
BOUND_CAMPAIGN_ID = "cv_maxage_additional_evidence_campaign_v2_8312cd8d1b71c65b"
BOUND_SESSION_LABEL = "S03"
BOUND_SESSION_ID = "cv_maxage_additional_evidence_campaign_v2_8312cd8d1b71c65b_s03_4c31d7dc5a08"
BOUND_PREREGISTRATION_ID = BOUND_SESSION_ID
BOUND_PREREGISTRATION_DIGEST = "e06aee85ad609e41e701d06f640838779c6ca30d237ea933a1cd3af56fb3b4bb"
BOUND_CONTRACT_DIGEST = "402247b1222c42abb891d30fd27520719d49c920381b126518039250b6f41b42"
BOUND_RUNBOOK_DIGEST_V1 = BOUND_RUNBOOK_DIGEST
BOUND_AUTHORIZATION_VERSION = AUTHORIZATION_VERSION
BOUND_VENUE = REQUIRED_VENUE
BOUND_INSTRUMENT = REQUIRED_INSTRUMENT
BOUND_NETWORK_SCOPE = REQUIRED_NETWORK_SCOPE
BOUND_SESSION_SCOPE = REQUIRED_SESSION_SCOPE
BOUND_DURATION_SECONDS = REQUIRED_DURATION_SECONDS  # 10860
BOUND_CODE_BASELINE_SHA = DEFAULT_CODE_BASELINE_SHA

EVIDENCE_CAMPAIGN_ROOT_REL = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    f"campaigns/{BOUND_CAMPAIGN_ID}"
)
S03_SESSIONS_REL = f"{EVIDENCE_CAMPAIGN_ROOT_REL}/sessions/S03"
S03_LOCK_FILENAME = "session.lock"
S03_METADATA_FILENAME = "session_metadata.json"
S03_HEARTBEAT_FILENAME = "heartbeat.jsonl"
S03_CONNECTIVITY_FILENAME = "connectivity_events.jsonl"
S03_MARKET_SAMPLES_FILENAME = "market_samples.jsonl"
S03_VOLATILITY_FILENAME = "volatility_records.jsonl"
S03_DRIFT_FILENAME = "volatility_drift_comparisons.jsonl"
S03_DECISION_SENSITIVITY_FILENAME = "decision_sensitivity.jsonl"
S03_EXIT_RISK_SAFETY_FILENAME = "exit_risk_safety_independence.jsonl"
S03_COUNTERFACTUAL_FILENAME = "counterfactual_decisions.jsonl"
S03_TERMINAL_VERDICT_FILENAME = "terminal_verdict.json"
S03_INTEGRITY_MANIFEST_FILENAME = "integrity_manifest.json"

# Exhausted campaign evidence that must remain byte-identical.
EXISTING_EXHAUSTED_CAMPAIGN_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe"
S01_SESSION_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s01_8a97f48c839c"
S02_SESSION_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s02_c02312c99747"

# Reused public-MD allowlists from preregistered runner.
REUSED_PUBLIC_MD_HOST = BOUND_PUBLIC_MD_HOST_V1
REUSED_PUBLIC_MD_ENDPOINT_ALLOWLIST = PUBLIC_MD_ENDPOINT_ALLOWLIST
REUSED_PUBLIC_MD_METHOD_ALLOWLIST = PUBLIC_MD_METHOD_ALLOWLIST

# Side-effect probe markers (aligned with Auth-v2 ordering vocabulary).
SIDE_EFFECT_AUTHORIZATION_CONSUMED = "AUTHORIZATION_CONSUMED"
SIDE_EFFECT_SESSION_LOCK = "SESSION_LOCK"
SIDE_EFFECT_EVIDENCE_CREATION = "EVIDENCE_CREATION"
SIDE_EFFECT_NETWORK = "NETWORK"
SIDE_EFFECT_RUNTIME_INITIALIZATION = "RUNTIME_INITIALIZATION"

FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME: tuple[str, ...] = (
    SIDE_EFFECT_SESSION_LOCK,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_RUNTIME_INITIALIZATION,
)

# Architecture invariants.
NO_SECOND_EXECUTION_AUTHORITY = True
NO_SECOND_DECISION_AUTHORITY = True
AUTH_V2_IS_SOLE_SESSION_AUTHORITY = True
CONSUME_BEFORE_SIDE_EFFECTS = True
SESSION_LOCK_BEFORE_NETWORK = True
ONE_ACTIVE_SESSION_PER_SCOPE = True
MONOTONIC_DURATION_AUTHORITY = True
WALLCLOCK_ONLY_FOR_AUDIT = True
PUBLIC_MARKET_DATA_ONLY = True
COUNTERFACTUAL_RUNTIME_IS_NON_AUTHORITY = True
ARTIFICIAL_DELAY_FOR_AGE_CREATION = False
SYNTHETIC_TIMESTAMP_AGING = False
MARKET_TIME_FABRICATION = False
DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME = True
RUNTIME_CYCLE_CANNOT_ADVANCE_MARKET_TIME = True
PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY = False
REAL_NETWORK_IN_THIS_CAPABILITY = False
AUTHORIZATION_CONSUMPTION_IN_THIS_CAPABILITY = False
NUMERIC_MAX_AGE_SELECTED = False
POLICY_ENFORCEMENT_ADDED = False
HARD_STOP = True
READY_FOR_S03_AUTHORIZATION_CONSUMPTION_AND_EXECUTION = False

# Observational exit/risk/safety independence (does not redefine Master-V2 logic).
EXIT_PRECEDENCE_OBSERVED: tuple[str, ...] = (
    "SAFETY_EXIT",
    "HARD_RISK_REDUCE",
    "POSITION_RECONCILIATION",
    "MANDATORY_ADVERSE_REDUCE",
    "PROFIT_EXIT",
    "TIME_EXIT",
    "INVALIDATION_EXIT",
    "HOLD_REVERSAL_HANDLING",
)
REVERSAL_REDUCE_FIRST_SEQUENCE: tuple[str, ...] = (
    "REDUCE_OR_REVERSAL_PREPARATION_EXIT",
    "FLAT",
    "OPPOSITE_SIDE_ARMED",
    "ENTER_OPPOSITE",
)

SCHEMA_SESSION_METADATA = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_session_metadata/v1"
)
SCHEMA_HEARTBEAT = "canonical_volatility_numeric_max_age_additional_evidence_s03_heartbeat/v1"
SCHEMA_CONNECTIVITY = "canonical_volatility_numeric_max_age_additional_evidence_s03_connectivity/v1"
SCHEMA_MARKET_SAMPLE = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_market_sample/v1"
)
SCHEMA_VOLATILITY = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_volatility_record/v1"
)
SCHEMA_DRIFT = "canonical_volatility_numeric_max_age_additional_evidence_s03_volatility_drift/v1"
SCHEMA_DECISION_SENSITIVITY = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_decision_sensitivity/v1"
)
SCHEMA_EXIT_RISK_SAFETY = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_exit_risk_safety_independence/v1"
)
SCHEMA_COUNTERFACTUAL = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_counterfactual/v1"
)
SCHEMA_TERMINAL_VERDICT = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_terminal_verdict/v1"
)
SCHEMA_INTEGRITY_MANIFEST = (
    "canonical_volatility_numeric_max_age_additional_evidence_s03_integrity_manifest/v1"
)
SCHEMA_SESSION_LOCK = "canonical_volatility_numeric_max_age_additional_evidence_s03_session_lock/v1"

SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_PRODUCTIVE_SESSION_EXECUTION_OWNER_V1.md"
)
CONTRACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "s03_productive_session_execution_owner_contract_v1.json"
)
PACKAGE_RELATIVE_DIR = (
    "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
    "s03_productive_session_execution_owner_v1"
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "execution.live",
    "place_order",
    "submit_order",
    "broker_adapter",
)

CONFIRM_TOKEN_PLAINTEXT_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "confirm_token",
        "token_plaintext",
        "raw_token",
        "go_token",
        "operator_confirm_token_plaintext",
    }
)
