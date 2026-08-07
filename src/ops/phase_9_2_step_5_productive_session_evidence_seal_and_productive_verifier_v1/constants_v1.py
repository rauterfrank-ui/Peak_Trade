"""Constants for Step-5 productive session evidence seal + productive verifier."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_5_PRODUCTIVE_SESSION_EVIDENCE_SEAL_AND_PRODUCTIVE_VERIFIER_V1"
SCHEMA_VERSION = "phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier.v1"
SEAL_SCHEMA = "phase_9_2_step_5_productive_session_evidence_seal.v1"
PRODUCTIVE_VERIFIER_SCHEMA = "phase_9_2_step_5_productive_session_verifier.v1"
OWNER = "ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1"

OFFLINE_VERIFIER_DOMAIN = "IMPLEMENTATION_PROOF"
PRODUCTIVE_VERIFIER_DOMAIN = "AUTHORIZED_PRODUCTIVE_SESSION"
OFFLINE_VERIFIER_EXPECTED_FALSE_FOR_PRODUCTIVE_SESSION = True
PRODUCTIVE_SESSION_INVALIDATED_BY_OFFLINE_VERIFIER = False

CANONICAL_SESSION_RELATIVE_PATH = (
    "evidence/ops/phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1/session_20260806T213801Z"
)

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_5_productive_session_evidence_seal_"
    "and_productive_verifier_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_5_PRODUCTIVE_SESSION_"
    "EVIDENCE_SEAL_AND_PRODUCTIVE_VERIFIER_V1.md"
)

SESSION_CONTRACT_SECONDS_EXPECTED = 7200
MIN_REQUEST_INTERVAL_SECONDS_REQUIRED = 2.0
EXPECTED_PUBLIC_MD_REQUEST_COUNT = 3391
EXPECTED_HEARTBEAT_COUNT = 1130

OPERATOR_PUBLIC_RESULT_NAME = "operator_public_result.json"
TERMINAL_MANIFEST_RELATIVE = "evidence/session_terminal_manifest_v1.json"
EXECUTOR_SUMMARY_RELATIVE = "evidence/executor_summary.json"
EVENTS_RELATIVE = "evidence/session_events.jsonl"
PROGRESS_NAME = "progress.json"
AUTH_LEDGER_RELATIVE = "persistence/step5_authorization_consumption_ledger_v1.jsonl"
LOCKS_DIR_RELATIVE = "persistence/locks"
CONFIRM_TOKEN_PUBLIC_RELATIVE = "issuance/confirm_token_public.json"
GRANT_PUBLIC_RELATIVE = "issuance/grant_public.json"

OFFLINE_IMPLEMENTATION_VERIFIER_OWNER = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1.evidence_v1."
    "verify_session_manifest_v1"
)

NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
RUNTIME_START_ALLOWED = False
PROCESS_START_ALLOWED = False
CORE_LOGIC_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True
DASHBOARD_FILES_CHANGED = False
PRESENTATION_LAYER_CHANGED = False

PHASE_9_2_STEP_3_STATUS = "OPEN"
PHASE_9_2_STEP_4_STATUS = "OPEN"
PHASE_9_2_STEP_5_STATUS = "CLOSED_PASS"
PHASE_9_2_STEP_6_STATUS = "OPEN"
PHASE_9_2_STEP_7_STATUS = "OPEN"
NEXT_OPEN_PHASE_9_2_STEP = "3_RESTART_RECOVERY_PRODUCTIVE_REAL_NETWORK_SESSION"
NEXT_RECOMMENDED_CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_V1"
)
NEXT_RECOMMENDED_CAPABILITY_TITLE = (
    "Phase 9.2 Step-3 governed productive real-network restart/recovery session"
)
REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED = False

FORBIDDEN_PLAINTEXT_TOKEN_MARKERS = (
    "PTCONFIRMv1_",
    "confirm_token_plaintext",
    "CONFIRM_TOKEN_PLAINTEXT=",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
