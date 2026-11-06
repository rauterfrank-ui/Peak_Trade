"""Constants for Phase 9.2 Step-7 multi-session continuity campaign binding.

This package binds campaign harness + per-session evidence + campaign bundle
verifier surfaces. It never starts a network session and never mints/consumes
authorization or confirm tokens.
"""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_"
    "BINDING_AND_VERIFIER_IMPLEMENTATION_V1"
)
TARGET_CAMPAIGN_CAPABILITY_ID = "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_V1"
SCHEMA_VERSION = "phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_"
    "BINDING_AND_VERIFIER_IMPLEMENTATION_V1=true"
)
OWNER = "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_V1"
SESSION_LADDER_STEP = "MULTI_SESSION_CONTINUITY_CAMPAIGN"
SESSION_SCOPE = "PHASE_9_2_MULTI_SESSION_CONTINUITY_CAMPAIGN"
CAMPAIGN_ID = "phase_9_2_multi_session_continuity_campaign_v1"
TARGET_SESSION_ID_PREFIX = "phase_9_2_public_md_multi_session_continuity_session_v1"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.json"
)
CAMPAIGN_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_multi_session_continuity_campaign_contract_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_"
    "CONTINUITY_CAMPAIGN_BINDING_AND_VERIFIER_IMPLEMENTATION_V1.md"
)
BINDING_MANIFEST_FILENAME = "repeated_multi_session_continuity_campaign_binding_manifest_v1.json"

# Multi-session requirement expressed without inventing a governance count:
# campaign must contain strictly more than one governed session.
MULTI_SESSION_REQUIREMENT_OPERATOR = ">"
MULTI_SESSION_REQUIREMENT_OPERAND = 1
MULTI_SESSION_REQUIREMENT_EXPRESSION = ">1"

# Canonical reuse owners (no parallel semantics).
STEP3_RESTART_OWNER = (
    "ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1"
)
STEP4_RECONNECT_OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
)
STEP6_STALE_ADVERSE_OWNER = (
    "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1."
    "governed_injected_stale_data_fault_v1"
)
CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)

CAMPAIGN_HARNESS_OWNER = f"{OWNER}.campaign_harness_v1"
CAMPAIGN_BUNDLE_OWNER = f"{OWNER}.campaign_bundle_v1"
CAMPAIGN_VERIFIER_OWNER = f"{OWNER}.campaign_verifier_v1"
PER_SESSION_EVIDENCE_CONTRACT_OWNER = f"{OWNER}.per_session_evidence_contract_v1"
CAMPAIGN_STATE_CONTRACT_OWNER = f"{OWNER}.campaign_state_contract_v1"

SESSION_EVIDENCE_SCHEMA_VERSION = "phase_9_2_multi_session_continuity_session_evidence.v1"
CAMPAIGN_BUNDLE_SCHEMA_VERSION = "phase_9_2_multi_session_continuity_campaign_bundle.v1"
CAMPAIGN_STATE_SCHEMA_VERSION = "phase_9_2_multi_session_continuity_campaign_state.v1"

# Permanent constants — never flip in this binding capability.
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
AUTHORIZATION_REUSE_FORBIDDEN = True
CONFIRM_TOKEN_REUSE_FORBIDDEN = True
READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION = True

PHASE_9_2_STEP_6_STATUS = "CLOSED_PASS"
PHASE_9_2_STEP_7_STATUS = "OPEN"
PHASE_9_2_SESSION_LADDER_COMPLETE = False
MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
CAMPAIGN_EXECUTED = False
NETWORK_SESSION_STARTED = False
STEP7_STARTED = False
NEXT_OPEN_PHASE_9_2_STEP = "7_MULTI_SESSION_CONTINUITY_CAMPAIGN"

STEP7_CAMPAIGN_OWNER_PRESENT = True
STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT = True
STEP7_CAMPAIGN_HARNESS_BOUND = True
STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT = True
STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT = True
STEP7_CAMPAIGN_VERIFIER_PRESENT = True
STEP7_BINDING_IMPLEMENTED = True

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True
FORCED_INTENT_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False
NO_PARALLEL_RESTART_MODEL = True
NO_PARALLEL_RECONNECT_MODEL = True
NO_PARALLEL_STALE_MODEL = True
NO_PARALLEL_CAMPAIGN_AUTHORITY = True

PER_SESSION_REQUIRED_FIELDS = (
    "session_id",
    "repository_sha",
    "config_digest",
    "authorization_id",
    "authorization_digest",
    "confirm_token_fingerprint",
    "session_result",
    "restart_recovery_result",
    "reconnect_result",
    "stale_adverse_result",
    "state_root_before",
    "state_root_after",
    "verifier_result",
    "claims",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def multi_session_requirement_satisfied_v1(session_count: int) -> bool:
    """True iff campaign contains strictly more than one governed session."""
    return int(session_count) > int(MULTI_SESSION_REQUIREMENT_OPERAND)
