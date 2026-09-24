"""Constants for F1/M9 prospective candidate-selection campaign execution owner v1."""

from __future__ import annotations

from typing import Final

WORKPACKAGE_ID: Final[str] = "F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_OWNER_MAX_BUILD_V1"
EXECUTION_OWNER_ID: Final[str] = "f1_m9_prospective_candidate_selection_campaign_execution_v1"
SCHEMA_VERSION: Final[str] = "f1_m9_prospective_candidate_selection_campaign_execution/v1"
RUNTIME_AUTHORIZATION_SCHEMA_VERSION: Final[str] = (
    "f1_m9_prospective_campaign_execution_runtime_authorization/v1"
)
SEALED_EVIDENCE_SCHEMA_VERSION: Final[str] = "f1_m9_prospective_campaign_sealed_evidence_bundle/v1"

NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1_decision_v1.json"
)

CAMPAIGN_ID: Final[str] = "cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032"
PREREGISTRATION_ID: Final[str] = (
    "F1_M9_PROSPECTIVE_VOLATILITY_NUMERIC_MAX_AGE_CANDIDATE_SELECTION_CAMPAIGN_PREREGISTRATION_V1"
)
PREREGISTRATION_CONFIG: Final[str] = (
    "config/research/f1_m9_prospective_volatility_numeric_max_age_candidate_selection_"
    "campaign_preregistration_v1.json"
)
PREREGISTRATION_DIGEST: Final[str] = (
    "44971151bc41b124bfa3642d38cba0bc43919160fec2e2d74df4f9e135101b0c"
)
SELECTION_POLICY_ID: Final[str] = (
    "f1_m9_volatility_numeric_max_age_productive_candidate_selection_policy_v1"
)
SELECTION_POLICY_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_candidate_selection_policy_v1.json"
)
SELECTION_POLICY_DIGEST: Final[str] = (
    "2bab88a8289fb0322ea2e9d1f0133d05543f9a899d2ba7602a4509c4a184d2a1"
)
SELECTION_RULE_ID: Final[str] = "F1_M9_ROBUST_REGION_UNIQUE_SURVIVOR_POINT_V1"

SURFACE_ID: Final[str] = "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
SOURCE_PARAMETER_ID: Final[str] = "max_age_seconds"
TARGET_PARAMETER_ID: Final[str] = "numeric_max_age_seconds"

DURABLE_CAMPAIGN_ROOT_REL: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    f"campaigns/{CAMPAIGN_ID}"
)

REAL_MD_SUPPLIER_MODULE: Final[str] = (
    "research.canonical_volatility_numeric_max_age_preregistered_productive_session_"
    "runner_v1.public_md_source_v1"
)
REAL_MD_SUPPLIER_ID: Final[str] = "CANONICAL_VOLATILITY_PREREGISTERED_PUBLIC_MD_SOURCE_V1"

HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID: Final[str] = (
    "cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f"
)

STATUS_EXECUTION_PROOF_PASS: Final[str] = "F1_M9_CAMPAIGN_EXECUTION_PROOF_PASS"
STATUS_EXECUTION_DENIED: Final[str] = "DENIED_FAIL_CLOSED"
STATUS_AUTHORIZED_PATH_READY: Final[str] = "F1_M9_AUTHORIZED_CAMPAIGN_EXECUTION_PATH_READY"

NEXT_TRUE_BLOCKER: Final[str] = "F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_REQUIRES_OWNER_GO"

CAMPAIGN_ARTIFACT_NAMES: Final[tuple[str, ...]] = (
    "campaign_manifest.json",
    "runtime_execution_authorization_ref.json",
    "source_provenance.json",
    "session_evidence.json",
    "candidate_grid_evaluation.json",
    "oos_evidence.json",
    "robustness_evidence.json",
    "economic_evidence.json",
    "failure_evidence.json",
    "contamination_adjudication.json",
    "campaign_completeness.json",
    "selection_result.json",
    "MANIFEST.sha256",
)

EVIDENCE_SOURCE_REAL: Final[str] = "REAL_PUBLIC_MARKET_DATA"
EVIDENCE_SOURCE_FIXTURE: Final[str] = "FIXTURE_OR_SYNTHETIC"
EVIDENCE_SOURCE_HISTORICAL: Final[str] = "HISTORICAL_COUNTERFACTUAL"

REQUIREMENT_VERDICT_PASS: Final[str] = "PASS"
REQUIREMENT_VERDICT_FAIL: Final[str] = "FAIL"
REQUIREMENT_VERDICT_INCOMPLETE: Final[str] = "INCOMPLETE"

RESUME_STATE_RESUME_AUTHORIZED: Final[str] = "RESUME_AUTHORIZED"
RESUME_STATE_ALREADY_COMPLETE: Final[str] = "ALREADY_COMPLETE"
RESUME_STATE_FAIL_CLOSED: Final[str] = "FAIL_CLOSED"
