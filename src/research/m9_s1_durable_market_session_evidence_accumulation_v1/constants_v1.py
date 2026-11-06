"""Constants for M9-S1 durable market session evidence accumulation v1."""

from __future__ import annotations

from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)
from src.research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
)

PACKAGE_MARKER = "M9_S1_DURABLE_MARKET_SESSION_EVIDENCE_ACCUMULATION_V1=true"

WORKPACKAGE_ID = "M9_S1_DURABLE_MARKET_SESSION_EVIDENCE_ACCUMULATION_V1"
SCHEMA_VERSION = "m9_s1_durable_market_session_evidence_accumulation/v1"
OBSERVATION_SCHEMA_VERSION = "m9_s1_market_session_observation/v1"
OBSERVATION_LEDGER_SCHEMA_VERSION = "m9_s1_market_session_observation_ledger/v1"
OWNER_REVIEW_SCHEMA_VERSION = "m9_s1_market_session_evidence_owner_review/v1"
REPLAY_ARTIFACT_SCHEMA_VERSION = "m9_s1_market_session_counterfactual_replay/v1"

NORMATIVE_SPEC = "docs/ops/specs/M9_S1_DURABLE_MARKET_SESSION_EVIDENCE_ACCUMULATION_NORMATIVE_V1.md"
DECISION_CONFIG = (
    "config/governance/m9_s1_durable_market_session_evidence_accumulation_v1_decision_v1.json"
)

DEFAULT_M9_S1_OBSERVATION_LEDGER_RELATIVE_PATH = (
    "docs/evidence/m9_s1_durable_market_session_evidence_accumulation_v1/"
    "market_session_observations.jsonl"
)
DEFAULT_OWNER_REVIEW_RELATIVE_PATH = (
    "docs/evidence/m9_s1_durable_market_session_evidence_accumulation_v1/"
    "owner_review_accumulation_report.json"
)

JOIN_LEDGER_RELATIVE_PATH = DEFAULT_JOIN_LEDGER_RELATIVE_PATH
PRODUCTIVE_LEDGER_RELATIVE_PATH = DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH

COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS: tuple[int, ...] = tuple(
    int(x) for x in OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS
)

NUMERIC_MAX_AGE_DECIDED = False
ENFORCEMENT_ENABLED = False
EXTERNAL_EFFECT_AUTHORIZED = False
PRODUCTIVE_PARAMETER_MUTATED = False
OBSERVATION_ONLY = True
COUNTERFACTUAL_ONLY = True

SELECTION_RESULT_UNRESOLVED = "UNRESOLVED_OWNER_DECISION"
SELECTION_READINESS_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
