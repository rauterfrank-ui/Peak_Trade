"""Constants for PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1"
SCHEMA_VERSION = "phase_9_2_restart_recovery_session_contract.v1"
PRODUCER_VERSION = "phase_9_2_restart_recovery_session_contract_and_productive_harness.v1"
PACKAGE_MARKER = "PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1=true"
OWNER = "ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
AUTHORITY_OWNER = OWNER

CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_restart_recovery_session_contract_v1.json"
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
)
SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
RESTART_CAMPAIGN_ID = "phase_9_2_restart_recovery_campaign_v1"
DURABLE_STATE_LINEAGE_ID = "phase_9_2_restart_durable_state_lineage_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_restart_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

SEGMENT_ROLE_PRE = "PRE_RESTART"
SEGMENT_ROLE_POST = "POST_RESTART"
SEGMENT_ROLES = frozenset({SEGMENT_ROLE_PRE, SEGMENT_ROLE_POST})

CONTROLLED_RESTART_EXIT_CODE = 82
CONTROLLED_RESTART_REASON = "CONTROLLED_PRE_RESTART_SEGMENT_COMPLETE"

MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS = 30
REQUIRED_RECONCILIATION_BEFORE_ALPHA = True

LOCK_FILENAME = "session.lock"
AUTHORIZATION_LEDGER_FILENAME = "authorization_consumption_ledger_v1.jsonl"
PRE_TERMINAL_MANIFEST_FILENAME = "pre_restart_terminal_manifest_v1.json"
POST_TERMINAL_MANIFEST_FILENAME = "post_restart_terminal_manifest_v1.json"
CHECKPOINT_FILENAME = "phase_9_2_restart_checkpoint_v1.json"
STATE_ROOT_DIGESTS_FILENAME = "state_root_digests_v1.json"
TELEMETRY_FILENAME = "restart_segment_telemetry_v1.json"
BUNDLE_MANIFEST_FILENAME = "restart_bundle_manifest_v1.json"
VERIFIER_RESULT_FILENAME = "restart_bundle_verifier_result_v1.json"
EVIDENCE_CURSOR_FILENAME = "evidence_cursor_v1.json"
CAP64_COMMIT_FILENAME = "decision_path_commit_marker_v1.json"

OPEN_POSITION_RECOVERY_PROVEN = "OPEN_POSITION_RECOVERY_PROVEN"
OPEN_POSITION_NOT_OBSERVED = "OPEN_POSITION_NOT_OBSERVED"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
VOLATILITY_POLICY_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
EXECUTION_ECONOMICS_CHANGE = False

LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
RUNTIME_SESSION_ALLOWED = False

ORPHAN_LOCK_TAKEOVER_ALLOWED = False
SAME_SESSION_RESUME_ALLOWED = False
NEW_AUTHORIZATION_PER_SEGMENT_REQUIRED = True
FORCED_INTENT_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
COMPOSITION_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False

PREDECESSOR_CAP61 = "CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1"
PREDECESSOR_CAP62 = "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1"
PREDECESSOR_CAP64 = "CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1"
PREDECESSOR_CAP72 = "CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1"

NO_ORDER_BOUNDARY_ASSERTIONS = (
    "NO_LIVE_ORDERS",
    "NO_TESTNET_ORDERS",
    "NO_PAPER_EXCHANGE_ORDERS",
    "NO_EXCHANGE_CREDENTIAL_USE",
    "NO_REAL_CAPITAL_MOVEMENT",
    "NO_PRIVATE_ENDPOINT_ACCESS",
    "NO_AUTH_HEADER_TRANSMISSION",
)

REQUIRED_CONTRACT_FIELDS = (
    "schema_version",
    "capability_id",
    "restart_campaign_id",
    "durable_state_lineage_id",
    "segment_id",
    "segment_role",
    "predecessor_segment_id",
    "predecessor_terminal_manifest_digest",
    "expected_repository_sha",
    "expected_config_digest",
    "expected_instrument_identity",
    "expected_confirmation_session_id",
    "expected_runtime_state_digest",
    "expected_portfolio_digest",
    "expected_scope_digest",
    "expected_accounting_digest",
    "expected_evidence_cursor",
    "authorization_id",
    "authorization_digest",
    "runtime_session_id",
    "controlled_restart_reason",
    "minimum_pre_restart_distinct_observations",
    "required_reconciliation_before_alpha",
    "no_order_boundary_assertions",
)

REQUIRED_TELEMETRY_FIELDS = (
    "restart_campaign_id",
    "durable_state_lineage_id",
    "segment_id",
    "segment_role",
    "predecessor_segment_id",
    "pre_restart_terminal_manifest_digest",
    "state_root_digest_before_segment",
    "state_root_digest_after_segment",
    "confirmation_session_id_before",
    "confirmation_session_id_after",
    "observation_epoch_before",
    "observation_epoch_after",
    "reconciliation_completed_before_alpha",
    "duplicate_confirmation_prevented_count",
    "duplicate_fill_prevented_count",
    "evidence_cursor_before",
    "evidence_cursor_after",
    "portfolio_digest_before",
    "portfolio_digest_after",
    "scope_digest_before",
    "scope_digest_after",
    "accounting_digest_before",
    "accounting_digest_after",
    "controlled_restart_requested",
    "controlled_restart_completed",
    "open_position_present_at_restart",
    "open_position_recovered",
    "open_position_recovery_claim",
    "authorization_reused",
    "live_testnet_order_boundary_preserved",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
