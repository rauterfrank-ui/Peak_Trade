"""Constants for LONG_RUNNING_TESTNET_PROVEN prep/eval capability (pre-run only)."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1"
PACKAGE_MARKER = "CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1=true"
OWNER = "ops.capability_11_long_running_testnet_proven_prep_eval_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "capability_11_long_running_testnet_proven_prep_eval.v1"

# Reuse execute surface; do not reopen §11.12.8.
REUSED_EXECUTE_SURFACE = (
    "ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1"
    "+ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1"
)
SECTION_11_12_8_CLOSED = True
SECTION_11_12_8_REOPENED = False
CAP_11_12_TESTNET_PROGRAM_CLOSED = True

# Owner-ratified execute authorization for this claim path (merge ≠ execute).
CANONICAL_EXECUTE_OWNER_GO_SCOPE = "EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
MERGE_AUTHORIZATION_IS_NOT_EXECUTE_AUTHORIZATION = True
PRODUCTIVE_CAMPAIGN_STARTED_BY_THIS_PACKAGE = False
NETWORK_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
LIVE_ORDER_EFFECT = "NONE"
LIVE_AUTHORIZED = False
SECTION_11_13_STARTED = False
PRE_LIVE_CYBERSECURITY_GATE = "NOT_PASSED"
LONG_RUNNING_TESTNET_PROVEN = False
LONG_RUNNING_TESTNET_PROVEN_DEFAULT = False
LONG_RUNNING_PATH_READY = True
CORE_LOGIC_CHANGE = False

# Master §11.12.8.1 bounds reused for LONG_RUNNING claim evaluation.
CAMPAIGN_DURATION_BOUND_SECONDS = 3600
CAMPAIGN_MAX_CYCLES = 120
CYCLE_CADENCE_SECONDS = 60
BOUND_PRIORITY = "FIRST_REACHED_WINS"

# Owner-ratified PASS minima (evaluation only; not claimed true by this prep PR).
PASS_MINIMA_BOUND_REACHED = True
PASS_MINIMA_SEALED_EVIDENCE = True
PASS_MINIMA_FINAL_FLAT = True
PASS_MINIMA_NO_LIVE_EFFECT = True
PASS_MINIMA_ORDER_ACK_COUNT_GTE_1 = True
PASS_MINIMA_CLEAN_CANCEL_OR_RECONCILE_SAME_RUN = True
PASS_MINIMA_TRANSPORT_ONLY_403_REFUSED = True

FORBIDDEN_HISTORICAL_EVIDENCE_ROOTS: tuple[str, ...] = (
    "evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z",
    "evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z",
)

EVIDENCE_DIRNAME = "capability_11_long_running_testnet_proven_prep_eval_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
