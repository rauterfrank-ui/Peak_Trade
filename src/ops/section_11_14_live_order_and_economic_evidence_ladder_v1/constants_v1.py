"""Fail-closed constants for the offline §11.14 evidence-ladder surface."""

from __future__ import annotations

CAPABILITY_ID = "SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_14_offline_evidence_ladder.v1"
EVIDENCE_RECORD_SCHEMA_VERSION = "section_11_14_evidence_record.v1"
METRICS_SCHEMA_VERSION = "section_11_14_mandatory_live_metrics.v1"
OWNER = "ops.section_11_14_live_order_and_economic_evidence_ladder_v1"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_"
    "EXHAUSTIVE_OFFLINE_CENSUS_MAXIMUM_SAFE_LEVERAGE_V1"
)
PRIOR_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_PROOF_CRITERION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_BIND_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1"
)
HISTORICAL_FORENSIC_ACK_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_"
    "FORENSIC_ADJUDICATION_V1"
)
HISTORICAL_ORDER_PLAN_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_EXACT_LIVE_MUTATION_"
    "MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_PRIVATE_READ_ONLY_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_MAXIMUM_SAFE_LEVERAGE_CLOSE_ALL_NON_MUTATING_DEPENDENCIES_V1"
)
HISTORICAL_PATH_REACHABLE_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_CODE_EXISTS_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_OFFLINE_SURFACE_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_OFFLINE_EVIDENCE_LADDER_SURFACE_MAXIMUM_SAFE_LEVERAGE_V1"
)
WORKPACKAGE_ID = "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1"
THIS_SLICE = "11.14.LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS"
PREDECESSOR_SLICE = "11.14.LIVE_RESTART_RECONSTRUCTED_ADJUDICATION"
CURRENT_CANONICAL_SECTION = THIS_SLICE
LAST_CANONICALLY_CLOSED_STEP = "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS"
CANONICAL_EVIDENCE_RUN_ID = "20260904T195000Z"
HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO = PRIOR_OWNER_GO
HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID = "20260904T192000Z"
HISTORICAL_RESTART_RECONSTRUCTED_SHA = "4ad023a01708d897cd5a49bd06bff7bb02bbf590"
HISTORICAL_ACCOUNTING_RECONSTRUCTED_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_ACCOUNTING_RECONSTRUCTED_RUN_ID = "20260904T185000Z"
HISTORICAL_ACCOUNTING_RECONSTRUCTED_SHA = "78982a8b09f6e331a3c5e33a3aac70a2d190ca02"
HISTORICAL_POSITION_RECONCILED_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_POSITION_RECONCILED_MAXIMUM_SAFE_LEVERAGE_V2"
)
HISTORICAL_POSITION_RECONCILED_RUN_ID = "20260904T181817Z"
HISTORICAL_POSITION_RECONCILED_SHA = "2d46611a4485a5422279e75fc762dd2285f7cc15"
HISTORICAL_FEE_OBSERVED_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_FEE_OBSERVED_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_FEE_OBSERVED_RUN_ID = "20260904T173813Z"
HISTORICAL_FEE_OBSERVED_SHA = "de053526a5066526a1fd1ebaf5f5c4045a3ad4d5"
HISTORICAL_FILL_OBSERVED_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_FILL_OBSERVED_MAXIMUM_SAFE_LEVERAGE_V1"
)
HISTORICAL_FILL_OBSERVED_RUN_ID = "20260904T165859Z"
HISTORICAL_FILL_OBSERVED_SHA = "fead386cc6746524301a01b7b7489bea0621e4f3"
HISTORICAL_SUBMIT_ACK_OBSERVED_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_EXACT_SINGLE_LIVE_SUBMIT_POST_V1"
)
HISTORICAL_SUBMIT_ACK_OBSERVED_RUN_ID = "20260904T160450Z"
HISTORICAL_SUBMIT_ACK_OBSERVED_SHA = "d6d3fa2970aafc9517cff9c0b8c1685dabd9791b"
HISTORICAL_PROOF_CRITERION_RUN_ID = "20260904T151500Z"
HISTORICAL_PROOF_CRITERION_SHA = "61fbec920741b3c6631e15723092e3b262740c4e"
HISTORICAL_FORENSIC_ACK_RUN_ID = "20260904T144800Z"
HISTORICAL_FORENSIC_ACK_SHA = "6ead7a2cd7bded088f75ba48ca4c51fbde618945"
CANONICAL_BASE_SHA = "fec71a8f9cdd5fdb458ed361ebbf9f0117549c54"
EXPECTED_ORIGIN_MAIN_SHA = CANONICAL_BASE_SHA
IMPLEMENTATION_SHA = CANONICAL_BASE_SHA
HISTORICAL_ORDER_PLAN_SHA = "eca62c687d7fb42d0fa11c645d5f70bb26916c55"
HISTORICAL_ORDER_PLAN_RUN_ID = "20260904T140500Z"
HISTORICAL_PRIVATE_READ_ONLY_SHA = "6930807523ea7af3aff8cc653d335d5719d38d25"
HISTORICAL_PRIVATE_READ_ONLY_RUN_ID = "20260904T133200Z"
HISTORICAL_PATH_REACHABLE_SHA = "fa02c54468cc0320fe8c756bb4da08485fb84597"
HISTORICAL_PATH_REACHABLE_RUN_ID = "20260904T130000Z"
HISTORICAL_CODE_EXISTS_SHA = "b09cac11f0eaecfc5c6f5c97e8b23e808e186b9a"
HISTORICAL_CODE_EXISTS_RUN_ID = "20260904T123100Z"
HISTORICAL_OFFLINE_SURFACE_SHA = "a558c108617d40c12bd1d8c480a6e5d797ccb308"
HISTORICAL_OFFLINE_SURFACE_RUN_ID = "20260904T121000Z"
G12_STATUS_REQUIRED = "CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN"

CANONICAL_RUNBOOK_PATH = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_SECTION_HEADING = "## 11.14 Live order and economic evidence ladder"
CANONICAL_OFFLINE_SLICE_HEADING = "### 11.14 OFFLINE_EVIDENCE_LADDER_SURFACE"
CANONICAL_CODE_EXISTS_SLICE_HEADING = "### 11.14 LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION"
CANONICAL_PATH_REACHABLE_SLICE_HEADING = "### 11.14 LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION"
CANONICAL_PRIVATE_READ_ONLY_SLICE_HEADING = "### 11.14 LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION"
CANONICAL_ORDER_PLAN_OBSERVED_SLICE_HEADING = "### 11.14 LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION"
CANONICAL_SUBMIT_ACK_FORENSIC_SLICE_HEADING = (
    "### 11.14 LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION"
)
CANONICAL_SUBMIT_ACK_PROOF_CRITERION_SLICE_HEADING = (
    "### 11.14 LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION"
)
CANONICAL_SUBMIT_ACK_OBSERVED_ADJUDICATION_SLICE_HEADING = (
    "### 11.14 LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION"
)
CANONICAL_FILL_OBSERVED_ADJUDICATION_SLICE_HEADING = "### 11.14 LIVE_FILL_OBSERVED_ADJUDICATION"
CANONICAL_FEE_OBSERVED_ADJUDICATION_SLICE_HEADING = "### 11.14 LIVE_FEE_OBSERVED_ADJUDICATION"
CANONICAL_POSITION_RECONCILED_ADJUDICATION_SLICE_HEADING = (
    "### 11.14 LIVE_POSITION_RECONCILED_ADJUDICATION"
)
CANONICAL_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING = (
    "### 11.14 LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION"
)
CANONICAL_RESTART_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING = (
    "### 11.14 LIVE_RESTART_RECONSTRUCTED_ADJUDICATION"
)
CANONICAL_RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SLICE_HEADING = (
    "### 11.14 LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS"
)

LADDER_FIELDS: tuple[str, ...] = (
    "LIVE_EXECUTION_CODE_EXISTS",
    "LIVE_EXECUTION_PATH_REACHABLE",
    "LIVE_PRIVATE_READ_ONLY_PROVEN",
    "LIVE_ORDER_PLAN_OBSERVED",
    "LIVE_SUBMIT_ACK_OBSERVED",
    "LIVE_FILL_OBSERVED",
    "LIVE_FEE_OBSERVED",
    "LIVE_POSITION_RECONCILED",
    "LIVE_ACCOUNTING_RECONSTRUCTED",
    "LIVE_RESTART_RECONSTRUCTED",
    "LIVE_AUTONOMOUS_RECOVERY_OBSERVED",
    "LIVE_END_TO_END_EVIDENCE_PROVEN",
)
LADDER_FIELD_COUNT = 12

OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE: tuple[str, ...] = (
    "LIVE_RESTART_RECONSTRUCTED",
    "LIVE_AUTONOMOUS_RECOVERY_OBSERVED",
    "LIVE_END_TO_END_EVIDENCE_PROVEN",
)

LIVE_EXECUTION_CODE_EXISTS = True
LIVE_EXECUTION_PATH_REACHABLE = True
LIVE_PRIVATE_READ_ONLY_PROVEN = True
LIVE_ORDER_PLAN_OBSERVED = True
LIVE_SUBMIT_ACK_OBSERVED = True
LIVE_FILL_OBSERVED = True
LIVE_FEE_OBSERVED = True
LIVE_POSITION_RECONCILED = True
LIVE_ACCOUNTING_RECONSTRUCTED = True
LIVE_RESTART_RECONSTRUCTED = False
LIVE_AUTONOMOUS_RECOVERY_OBSERVED = False
LIVE_END_TO_END_EVIDENCE_PROVEN = False

LADDER_FIELD_DEFAULTS: dict[str, bool] = {
    "LIVE_EXECUTION_CODE_EXISTS": LIVE_EXECUTION_CODE_EXISTS,
    "LIVE_EXECUTION_PATH_REACHABLE": LIVE_EXECUTION_PATH_REACHABLE,
    "LIVE_PRIVATE_READ_ONLY_PROVEN": LIVE_PRIVATE_READ_ONLY_PROVEN,
    "LIVE_ORDER_PLAN_OBSERVED": LIVE_ORDER_PLAN_OBSERVED,
    "LIVE_SUBMIT_ACK_OBSERVED": LIVE_SUBMIT_ACK_OBSERVED,
    "LIVE_FILL_OBSERVED": LIVE_FILL_OBSERVED,
    "LIVE_FEE_OBSERVED": LIVE_FEE_OBSERVED,
    "LIVE_POSITION_RECONCILED": LIVE_POSITION_RECONCILED,
    "LIVE_ACCOUNTING_RECONSTRUCTED": LIVE_ACCOUNTING_RECONSTRUCTED,
    "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
    "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
    "LIVE_END_TO_END_EVIDENCE_PROVEN": LIVE_END_TO_END_EVIDENCE_PROVEN,
}

# Exact SSOT names from Master Runbook §11.14 (lines 60698-60719). Count=20.
# Prior pre-auth census reported 19; that count is not used.
MANDATORY_LIVE_METRICS: tuple[str, ...] = (
    "orders_planned",
    "orders_submitted",
    "orders_acknowledged",
    "orders_rejected",
    "orders_unknown",
    "partial_fills",
    "fills",
    "cancels",
    "amends",
    "duplicate_submit_prevented",
    "fees_paid",
    "funding_paid_or_received",
    "realized_pnl",
    "unrealized_pnl",
    "margin_utilization",
    "reconciliation_divergences",
    "autonomous_recoveries",
    "degradation_transitions",
    "kill_switch_events",
    "owner_interventions",
)
MANDATORY_LIVE_METRIC_COUNT = 20
PRIOR_CENSUS_REPORTED_METRIC_COUNT = 19
METRIC_COUNT_DISCREPANCY_VS_PRIOR_CENSUS = True

FORBIDDEN_LIVE_SOURCE_KINDS: tuple[str, ...] = (
    "FIXTURE",
    "SIMULATION",
    "SIMULATED",
    "TESTNET",
    "PAPER",
    "SHADOW",
    "DEMO",
)
ADMISSIBLE_OFFLINE_SOURCE_KINDS: tuple[str, ...] = (
    "CANONICAL_RUNBOOK",
    "REPOSITORY_IMPLEMENTATION",
    "PREDECESSOR_EVIDENCE",
    "GOVERNED_OFFLINE_CONTRACT",
    "GOVERNED_CURRENT_PRIVATE_GET",
    "GOVERNED_CURRENT_GATED_SUBMIT_PATH",
    "GOVERNED_CURRENT_LIVE_POST",
    "GOVERNED_PERSISTED_IDENTITY_BOUND_LIVE_ECONOMIC_PATH",
    "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF",
)

SECTION_11_14_AUTHORIZED = False
SECTION_11_14_COMPLETE = False
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED = False
SECTION_11_14_LIVE_EVIDENCE_COLLECTION_AUTHORIZED = False
SECTION_11_14_OFFLINE_SURFACE_BOUND = True
LIVE_AUTHORIZED = False
LIVE_ENABLED = False
LIVE_ARMED = False
SUBMIT_UNLOCKED = False
CANARY_AUTHORIZED = False
TESTNET_AUTHORIZED = False
POST_ALLOWED = False
ORDER_SUBMIT_ALLOWED = False
CANCEL_ALLOWED = False
AMEND_ALLOWED = False
FLATTEN_EXECUTE_ALLOWED = False
FUNDING_ALLOWED = False
CREDENTIAL_USE_ALLOWED = False
PUBLIC_GET_ALLOWED = False
PRIVATE_GET_ALLOWED = False
COLLECTOR_ACTIVATED = False
AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX = 1
RETRY_DEFAULT = False
SECOND_SUBMIT_DEFAULT = False
TIMEOUT_MUST_NOT_AUTO_POST = True
TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED = True
HISTORICAL_ORDER_PLAN_ARTIFACT_REUSE_FOR_POST = False
LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND = True
LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND = True
HISTORICAL_ACK_CASE_ADJUDICATION = "CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE"
HISTORICAL_POSITION_CASE_ADJUDICATION = "CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE"
HISTORICAL_ACCOUNTING_CASE_ADJUDICATION = "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE"
CASE_ADJUDICATION = "CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
LIVE_FILL_OBSERVED_PRODUCER_BOUND = True
LIVE_FILL_PROOF_CRITERION_BOUND = True
LIVE_FEE_OBSERVED_PRODUCER_BOUND = True
LIVE_FEE_PROOF_CRITERION_BOUND = True
LIVE_POSITION_RECONCILED_PRODUCER_BOUND = True
LIVE_POSITION_PROOF_CRITERION_BOUND = True
LIVE_ACCOUNTING_RECONSTRUCTED_PRODUCER_BOUND = True
LIVE_ACCOUNTING_PROOF_CRITERION_BOUND = True
LIVE_RESTART_RECONSTRUCTED_PRODUCER_BOUND = True
LIVE_RESTART_PROOF_CRITERION_BOUND = True
FULL_FILL_OBSERVED = True
PARTIAL_FILL_OBSERVED = False
NO_FILL_OBSERVED = False
HTTP_STATUS_CONTRIBUTES_TO_ACK = True
HTTP_STATUS_REQUIRED_FOR_ACK = 200
TOP_LEVEL_CODE_CONTRIBUTES_TO_ACK = True
TOP_LEVEL_CODE_REQUIRED_FOR_ACK = "0"
EXACTLY_ONE_DATA_ROW_REQUIRED_FOR_ACK = True
SCODE_0_REQUIRED_FOR_ACK = True
NONEMPTY_ORDID_REQUIRED_FOR_ACK = True
RETURNED_CLORDID_REQUIRED_FOR_ACK = True
RETURNED_CLORDID_MUST_EQUAL_SENT = True
READ_ONLY_RECON_IS_NOT_SYNCHRONOUS_ACK = True

REUSE_CLASSIFICATIONS: tuple[str, ...] = (
    "REUSABLE_AS_IDENTICAL_11_14_FACT",
    "SUPPORTING_CONTEXT_ONLY",
    "HISTORICAL_ONLY",
    "SEMANTICALLY_DIFFERENT",
    "REQUIRES_FRESH_OBSERVATION",
    "REQUIRES_OWNER_POLICY_DECISION",
    "CONTRADICTORY",
    "NOT_APPLICABLE",
    "CURRENT_AND_ADMISSIBLE",
    "CURRENT_BUT_INSUFFICIENT",
    "STALE_FOR_REACHABILITY",
)

EARLIEST_UNRESOLVED_DEPENDENCY = "LIVE_RESTART_RECONSTRUCTED"
NEXT_AUTHORITY_BOUNDARY = "LIVE_RESTART_RECONSTRUCTED"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
SESSION_LIVE_GATE_ACTIVATION_AUTHORIZED = False
STANDING_LIVE_GATES_MUST_REMAIN_FALSE = True
POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED = False
CANARY_TECHNICAL_EXECUTE_TOKEN = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
G12_DOES_NOT_AUTHORIZE_SECTION_11_14 = True
G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS = True
CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE = True
LIVE_RECONCILIATION_PROVEN_IS_NOT_LIVE_POSITION_RECONCILED = True
FIELD_NAME_SIMILARITY_IS_NOT_SEMANTIC_IDENTITY = True
HISTORICAL_EVIDENCE_IS_NOT_CURRENT_TRUTH = True
CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS = True
HISTORICAL_CODE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS = True
FIXTURE_TESTNET_SIM_IS_NOT_LIVE_EXECUTION_CODE_EXISTS = True
LIVE_EXECUTION_CODE_EXISTS_DOES_NOT_IMPLY_PATH_REACHABLE = True
LIVE_EXECUTION_CODE_EXISTS_DOES_NOT_IMPLY_AUTHORIZATION = True
LIVE_EXECUTION_PATH_REACHABLE_DOES_NOT_IMPLY_SUBMIT_AUTHORIZATION = True
LIVE_EXECUTION_PATH_REACHABLE_DOES_NOT_IMPLY_PRIVATE_READ_ONLY_PROVEN = True
LIVE_PRIVATE_READ_ONLY_PROVEN_DOES_NOT_IMPLY_ORDER_PLAN_OBSERVED = True
LIVE_PRIVATE_READ_ONLY_PROVEN_DOES_NOT_IMPLY_SUBMIT_AUTHORIZATION = True
HISTORICAL_PRIVATE_READ_ONLY_IS_NOT_CURRENT = True
SINGLE_REACHABILITY_GET_IS_NOT_PRIVATE_READ_ONLY_PROVEN = True
SECTION_11_13_2_TRADE_FALSE_IS_NOT_A_1114_CONJUNCT = True
BLOCKED_DRY_RUN_IS_NOT_LIVE_ORDER_PLAN_OBSERVED = True
HISTORICAL_GET_IS_NOT_CURRENT_REACHABLE = True
CREDENTIAL_PRESENCE_IS_NOT_AUTHENTICATION_SUCCESS = True
AUTHENTICATION_SUCCESS_IS_NOT_SUBMIT_AUTHORIZATION = True
VENUE_CONNECTIVITY_IS_NOT_LATER_LADDER_FIELD = True
NO_TESTNET_FIXTURE_OR_SIMULATED_RESULT_MAY_SATISFY_A_LIVE_EVIDENCE_FIELD = True
LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION = (
    "LIVE_EXECUTION_CODE_EXISTS is the first §11.14 Live proof-claim field. "
    "It is true iff current origin/main contains a complete, integrated, "
    "non-historical, non-fixture, non-testnet, non-simulated static call graph "
    "from the canonical Live canary execution decision/gate boundary through "
    "order-plan consumption, venue-native payload construction including "
    "client-order-id, fail-closed submit gates, the Live HTTP execution port, "
    "and UrllibLiveCanaryTransportV1.send. File presence alone, historical "
    "implementation, Cap 11.7-11.11 contracts-only constants, and §4.9 "
    "CURRENTLY_REACHABLE are each insufficient. True does not imply "
    "LIVE_EXECUTION_PATH_REACHABLE, authorization, credential availability, "
    "runtime observation, or any later ladder field."
)
LIVE_EXECUTION_PATH_REACHABLE_CANONICAL_DEFINITION = (
    "LIVE_EXECUTION_PATH_REACHABLE is the second §11.14 Live proof-claim field. "
    "It is true iff every bound PART_OF_REACHABILITY constituent is proven: "
    "the current productive Live canary static graph is complete and the "
    "entrypoint is integrated and selectable; fail-closed submit gates are "
    "evaluable; UrllibLiveCanaryTransportV1 is constructible; required SecretRef "
    "credential material is present without value disclosure; the production "
    "EEA host is currently connectable; a current authenticated private GET "
    "proves functional authentication and account/venue read access; and no "
    "static blocker prevents reaching the pre-submit boundary "
    "(refuse_submit_unless_gates_pass_v1). Submit-authorization gates "
    "(LIVE_ENABLED, LIVE_ARMED, SUBMIT_UNLOCKED, CANARY_AUTHORIZED, "
    "LIVE_AUTHORIZED, Owner execute-permit, SECTION_11_14_AUTHORIZED) are not "
    "constituents. File presence, LIVE_EXECUTION_CODE_EXISTS, §4.9 "
    "CURRENTLY_REACHABLE, historical GET success, credential presence alone, "
    "configured defaults, and fixture/testnet/sim sources are each insufficient. "
    "True does not promote LIVE_PRIVATE_READ_ONLY_PROVEN, LIVE_ORDER_PLAN_OBSERVED, "
    "any later ladder field, submit authorization, or POST."
)
LIVE_PRIVATE_READ_ONLY_PROVEN_CANONICAL_DEFINITION = (
    "LIVE_PRIVATE_READ_ONLY_PROVEN is the third §11.14 Live proof-claim field. "
    "It is true iff LIVE_EXECUTION_CODE_EXISTS and LIVE_EXECUTION_PATH_REACHABLE "
    "are already true and current authenticated private GET "
    "/api/v5/account/config and GET /api/v5/account/balance each return HTTP 200 "
    "and OKX code 0 with parseable account data, both methods are GET, no POST "
    "occurs, and no redirect is followed. A single reachability GET, historical "
    "§11.13.2 LIVE_PRIVATE_READ_ONLY_PROVEN, credential presence alone, "
    "fixture/testnet/sim sources, and the §11.13.2 TRADE=false owner attestation "
    "are each insufficient. True does not promote LIVE_ORDER_PLAN_OBSERVED, "
    "submit authorization, POST, Live-gate mutation, or any later ladder field."
)
LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION = (
    "LIVE_ORDER_PLAN_OBSERVED is the fourth §11.14 Live proof-claim field. "
    "It is true iff a current Live canary order-plan artifact is produced on "
    "the productive submit path after refuse_submit_unless_gates_pass_v1 from "
    "current venue-derived inputs. Static builder presence, a blocked dry-run, "
    "and §11.13.4 LIVE_DRY_RUN_ORDER_PLAN_PROVEN are each insufficient. True "
    "does not imply LIVE_SUBMIT_ACK_OBSERVED or POST authorization by itself."
)
LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION = (
    "LIVE_SUBMIT_ACK_OBSERVED is the fifth §11.14 Live proof-claim field. "
    "It is true iff LIVE_ORDER_PLAN_OBSERVED is already true and a current "
    "productive POST /api/v5/trade/order of a fresh plan (not a historical "
    "artifact) returns a synchronous parsed response with HTTP 200, no redirect, "
    "top-level code=0, exactly one data row, sCode=0, nonempty ordId, and a "
    "returned clOrdId that equals the sent clOrdId. Transport ok is not this "
    "field. CANARY_EXECUTED is not this field. UNKNOWN_SUBMIT is not ACK. A "
    "later read-only recon match by clOrdId may resolve order existence without "
    "reclassifying the original submit response as an observed ACK. Fixture, "
    "testnet, and simulated sources are forbidden. True does not imply "
    "LIVE_FILL_OBSERVED, POST authorization for a second submit, or §11.14 complete."
)
LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS = LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION
LIVE_SUBMIT_ACK_OBSERVED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "submit_ack_observed_adjudication_v1.py::adjudicate_live_submit_ack_observed_v1"
)
LIVE_FILL_OBSERVED_CANONICAL_DEFINITION = (
    "LIVE_FILL_OBSERVED is the sixth §11.14 Live proof-claim field. It is true "
    "iff LIVE_SUBMIT_ACK_OBSERVED is already true and a current governed private "
    "GET /api/v5/trade/fills on eea.okx.com, scoped to the exact acknowledged "
    "ordId, instId, and instType, returns HTTP 200, no redirect, top-level "
    "code=0, parseable JSON, and at least one data row whose ordId, clOrdId, "
    "and instId equal the bound Peak_Trade Live submit identity and whose "
    "fillSz is present and nonempty. That is at least one admissible executed "
    "fill bound to that identity. ACK, ordId existence, pending disappearance, "
    "position size, balance change, fee fields, and an order-state label are "
    "each insufficient. Historical fills, fixture, testnet, and simulated "
    "sources are forbidden. PARTIAL_FILL_OBSERVED and FULL_FILL_OBSERVED remain "
    "distinct. True does not imply LIVE_FEE_OBSERVED, LIVE_POSITION_RECONCILED, "
    "or §11.14 complete."
)
LIVE_FILL_OBSERVED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "fill_observed_adjudication_v1.py::adjudicate_live_fill_observed_v1"
)
LIVE_FEE_OBSERVED_CANONICAL_DEFINITION = (
    "LIVE_FEE_OBSERVED is the seventh §11.14 Live proof-claim field. It is true "
    "iff LIVE_FILL_OBSERVED is already true and a current governed private "
    "GET /api/v5/trade/fills on eea.okx.com, scoped to the exact acknowledged "
    "ordId, instId, and instType, returns HTTP 200, no redirect, top-level "
    "code=0, parseable JSON, and at least one data row whose ordId, clOrdId, "
    "and instId equal the bound Peak_Trade Live submit identity and whose "
    "venue-native fee field is present, nonempty, and Decimal-parseable and "
    "whose feeCcy is present and nonempty. That is an actual venue-reported "
    "fee bound to that identity. Fill quantity, fill price, fillPnl, "
    "order-state, ACK, position size, balance change, a static fee rate, "
    "fillPx times fillSz, historical fill evidence, fixture, testnet, and "
    "simulated sources are each insufficient. A missing, empty, unparseable, "
    "or schema-ambiguous fee fails closed and is not observed. True does not "
    "imply LIVE_POSITION_RECONCILED or §11.14 complete."
)
LIVE_FEE_OBSERVED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "fee_observed_adjudication_v1.py::adjudicate_live_fee_observed_v1"
)
LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION = (
    "LIVE_POSITION_RECONCILED is the eighth §11.14 Live proof-claim field. It is "
    "true iff LIVE_FEE_OBSERVED is already true and a current governed private "
    "GET /api/v5/account/positions on eea.okx.com, scoped to the bound instId and "
    "instType of the acknowledged Live submit, returns HTTP 200, no redirect, "
    "top-level code=0, parseable JSON, and exactly one data row whose instId "
    "equals the bound instrument and whose posSide equals the bound fill posSide "
    "and whose venue-native pos field is present, nonempty, and Decimal-parseable "
    "and whose Decimal pos equals the bound observed fillSz of the identity-bound "
    "Live fill. That is a current venue-reported position reconciled to that "
    "fill/fee path. Empty data is not zero and is not reconciled. A pos=0 row is "
    "not reconciled to a nonzero fillSz. Fill quantity alone, fee, ACK, "
    "order-state, balance change, LIVE_RECONCILIATION_PROVEN, historical position "
    "evidence, fixture, testnet, and simulated sources are each insufficient. A "
    "missing, empty, unparseable, schema-ambiguous, identity-mismatched, stale, "
    "or quantity-divergent pos fails closed and is not reconciled. True does not "
    "imply LIVE_ACCOUNTING_RECONSTRUCTED or §11.14 complete."
)
LIVE_POSITION_RECONCILED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "position_reconciled_adjudication_v1.py::adjudicate_live_position_reconciled_v1"
)
LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION = (
    "LIVE_ACCOUNTING_RECONSTRUCTED is the ninth §11.14 Live proof-claim field. It is "
    "true iff LIVE_POSITION_RECONCILED is already true and the identity-bound observed "
    "Live fill, fee, and position artifacts of the acknowledged Live submit reconstruct, "
    "using exact Decimal arithmetic and only venue-native fields actually present on that "
    "path, a closed realized-PnL identity reconstructed_realized_pnl[ccy] = fillPnl[feeCcy] "
    "+ fee[feeCcy] + fundingFee[position.ccy] + settledPnl[position.ccy] whose Decimal value "
    "equals the independently observed venue-native realizedPnl on the identity-bound "
    "position row, and whose feeCcy equals position.ccy, and whose fill.fee Decimal-equals "
    "position.fee, and whose fill.fillPnl Decimal-equals position.pnl, and whose fill.tradeId "
    "equals position.tradeId. Missing, empty, unparseable, or schema-ambiguous terms fail "
    "closed and are not replaced by zero. A present Decimal-parseable 0 is observed zero, "
    "not missing. Unrealized PnL, mark price, balance change, slippage inferred from fillPx "
    "versus fillMarkPx, Cap 7.1 ACCOUNTING_RECONSTRUCTION_MATCH, §11.17 "
    "LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN, historical unrelated accounting, fixture, "
    "testnet, and simulated sources are each insufficient. A nonzero residual without a "
    "canonical tolerance fails closed. True does not imply LIVE_RESTART_RECONSTRUCTED or "
    "§11.14 complete. A fresh private GET is not required when the identity-bound "
    "fill/fee/position evidence already contains the required terms."
)
LIVE_ACCOUNTING_RECONSTRUCTED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "accounting_reconstructed_adjudication_v1.py::adjudicate_live_accounting_reconstructed_v1"
)
LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION = (
    "LIVE_RESTART_RECONSTRUCTED is the tenth §11.14 Live proof-claim field. It is true "
    "iff LIVE_ACCOUNTING_RECONSTRUCTED is already true and persisted Live artifacts for "
    "the acknowledged Live submit contain a Peak_Trade durable pre-restart handoff state "
    "for that identity, distinct from the fill/fee/position venue-GET artifacts used for "
    "LIVE_ACCOUNTING_RECONSTRUCTED, from which an offline reconstruction using canonical "
    "restart semantics (reconstruct without re-submit and without silent reinitialization) "
    "yields a post-restart identity whose clOrdId, ordId, instId, posSide, and Decimal pos "
    "equal the bound Live submit/fill/position identity, and whose reconstructed pos is "
    "present, nonempty, Decimal-parseable, and is not zero when bound fillSz is nonzero. "
    "Accounting reconstruction, position reconciliation, fill/fee observation, ACK "
    "observation, Cap 11.5 and §11.12.6 fixtures, §11.12.9.14 TESTNET_RESTART_PROVEN, "
    "§11.17 LIVE_RESTART_PROVEN, historical implementation capability, and fixture/"
    "testnet/simulated sources are each insufficient. Absence of a durable Live "
    "pre-restart handoff or of a reconstructable post-restart identity fails closed and "
    "is not replaced by accounting closure. True does not imply "
    "LIVE_AUTONOMOUS_RECOVERY_OBSERVED, LIVE_END_TO_END_EVIDENCE_PROVEN, "
    "LIVE_RESTART_PROVEN, or §11.14 complete. A fresh process restart is not required "
    "when those persisted Live restart-handoff artifacts already exist; this field does "
    "not authorize restart execution."
)
LIVE_RESTART_RECONSTRUCTED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "restart_reconstructed_adjudication_v1.py::adjudicate_live_restart_reconstructed_v1"
)
STATIC_EXECUTION_GRAPH_FILENAME = "STATIC_EXECUTION_GRAPH.json"
COMPONENT_CLASSIFICATION_FILENAME = "COMPONENT_CLASSIFICATION.json"

EVIDENCE_DIRNAME = "section_11_14_live_order_and_economic_evidence_ladder_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
CLAIMS_FILENAME = "claims.json"
SUMMARY_FILENAME = "SUMMARY.json"
ADJUDICATION_FILENAME = "ADJUDICATION.json"
TRACEABILITY_FILENAME = "TRACEABILITY.json"
REUSE_MATRIX_FILENAME = "REUSE_VS_FRESH.json"
METRICS_SCHEMA_FILENAME = "MANDATORY_LIVE_METRICS_SCHEMA.json"
LADDER_STATE_FILENAME = "LADDER_STATE.json"
LINEAGE_FILENAME = "LINEAGE.json"
STATIC_FIELD_PROOF_FILENAME = "STATIC_FIELD_ADJUDICATION.json"
MUTATION_BOUNDARY_FILENAME = "MUTATION_BOUNDARY.json"
CONSTITUENT_MATRIX_FILENAME = "CONSTITUENT_MATRIX.json"
STATIC_REACHABILITY_GRAPH_FILENAME = "STATIC_REACHABILITY_GRAPH.json"
RUNTIME_DEPENDENCY_GRAPH_FILENAME = "RUNTIME_DEPENDENCY_GRAPH.json"
AUTHORITY_BOUNDARY_MAP_FILENAME = "AUTHORITY_BOUNDARY_MAP.json"
RUNTIME_GATE_CLASSIFICATION_FILENAME = "RUNTIME_GATE_CLASSIFICATION.json"
PRIVATE_GET_BINDING_FILENAME = "PRIVATE_GET_BINDING.json"
PRIVATE_GET_EVIDENCE_FILENAME = "PRIVATE_GET.sanitized.json"
PATH_REACHABLE_ADJUDICATION_FILENAME = "PATH_REACHABLE_ADJUDICATION.json"
PRIVATE_READ_ONLY_GET_BINDING_FILENAME = "PRIVATE_READ_ONLY_GET_BINDING.json"
PRIVATE_READ_ONLY_GET_EVIDENCE_FILENAME = "PRIVATE_READ_ONLY_GET.sanitized.json"
PRIVATE_READ_ONLY_ADJUDICATION_FILENAME = "PRIVATE_READ_ONLY_ADJUDICATION.json"
LATER_FIELD_CENSUS_FILENAME = "LATER_FIELD_CENSUS.json"
ORDER_PLAN_OBSERVED_ADJUDICATION_FILENAME = "ORDER_PLAN_OBSERVED_ADJUDICATION.json"
ORDER_PLAN_EVIDENCE_FILENAME = "ORDER_PLAN.sanitized.json"
GATE_STATE_FILENAME = "GATE_STATE.json"
PREFLIGHT_FILENAME = "PREFLIGHT.json"
SUBMIT_ACK_CONTRACT_FILENAME = "SUBMIT_ACK_CONTRACT.json"
SUBMIT_ACK_FAILURE_MATRIX_FILENAME = "SUBMIT_ACK_FAILURE_MATRIX.json"
SUBMIT_ACK_ADJUDICATION_FILENAME = "SUBMIT_ACK_ADJUDICATION.json"
SUBMIT_ACK_PROOF_CRITERION_FILENAME = "SUBMIT_ACK_PROOF_CRITERION.json"
EXACT_MUTATION_CONTRACT_FILENAME = "EXACT_MUTATION_CONTRACT.json"
POST_SUBMIT_RECON_FILENAME = "POST_SUBMIT_RECON.json"
FILL_OBSERVED_ADJUDICATION_FILENAME = "FILL_OBSERVED_ADJUDICATION.json"
FEE_OBSERVED_ADJUDICATION_FILENAME = "FEE_OBSERVED_ADJUDICATION.json"
POSITION_RECONCILED_ADJUDICATION_FILENAME = "POSITION_RECONCILED_ADJUDICATION.json"
ACCOUNTING_RECONSTRUCTED_ADJUDICATION_FILENAME = "ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json"
RESTART_RECONSTRUCTED_ADJUDICATION_FILENAME = "RESTART_RECONSTRUCTED_ADJUDICATION.json"

SP01_PATH = "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"
FLATTEN_EXECUTE_PATH = (
    "src/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/execute_v1.py"
)
CANARY_SUBMIT_TRANSPORT_PATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
SECTION_4_9_ANCHOR = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §4.9.4 SP-01"
