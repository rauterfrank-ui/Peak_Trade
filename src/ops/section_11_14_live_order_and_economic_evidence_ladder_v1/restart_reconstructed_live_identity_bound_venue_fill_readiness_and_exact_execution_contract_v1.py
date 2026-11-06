"""Prove LIVE_IDENTITY_BOUND_VENUE_FILL readiness and exact execution contract.

Readiness/contract authority only. Does not GET. Does not POST. Does not
wire-send. Does not submit. Does not mutate position. Does not restart.
Does not mutate LIVE_ENABLED or LIVE_ARMED. Does not bypass gates.
Does not treat historical BOUND_* identity or TEST_FIXTURE as a current
fill. Does not consume a future execution Owner-GO.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    BLOCKS_NEW_ENTRY,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    ENDPOINT_SUBMIT,
    ENDPOINT_TRADE_FILLS,
    LIVE_RECONCILIATION_PROVEN,
    ORDER_COUNT_LIMIT,
    OWNER_GO_EXECUTE,
    POSITION_COUNT_LIMIT,
    REQUIRED_ENVIRONMENT,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_EXPECTED_MGN_MODE,
    LEVERAGE_EXPECTED_POS_SIDE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_REQUIRED_VALUE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_RELPATH,
    HOST_JOIN_SYMBOL,
    PRODUCTIVE_HOOK_CALLER,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ,
    canary_venue_contract_count_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    CREDENTIAL_USE_ALLOWED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    ORDER_SUBMIT_ALLOWED,
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    PUBLIC_GET_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    exact_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1 import (
    CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION,
    reprove_productive_capture_call_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    FORBIDDEN_BOUND_FILL_KINDS,
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    require_future_bound_fill_identity_v1,
)

LIVE_IDENTITY_BOUND_VENUE_FILL_REQUIRED = True
LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER = (
    f"VENUE_FILL_OF_IDENTITY_BOUND_CANARY_POST_{ENDPOINT_SUBMIT}::run_canary_submit_transport_v1"
)
LIVE_FILL_READINESS_MATRIX_STATUS = "COMPLETE"
LIVE_FILL_READINESS = False
MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS = "BLOCKED"
LIVE_FILL_EXECUTION_AUTHORIZED = False
LIVE_FILL_EXECUTED = False
FUTURE_EXECUTION_OWNER_GO_REQUIRED = True
FUTURE_EXECUTION_OWNER_GO_SCOPE = (
    "EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_THEN_CONTEMPORANEOUS_"
    "PRE_RESTART_CAPTURE_NO_RESTART_NO_GATE_BYPASS"
)
FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_"
    "LIVE_IDENTITY_BOUND_VENUE_FILL_THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_V1"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_"
    "THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_REQUIRES_SEPARATE_OWNER_GO_V1"
)
CASE_ADJUDICATION = (
    "CASE_LIVE_IDENTITY_BOUND_VENUE_FILL_READINESS_MATRIX_COMPLETE_"
    "LIVE_FILL_READINESS_FALSE_ECONOMIC_CONTRACT_BLOCKED_NO_EXECUTION"
)
CANARY_EXECUTE_RELPATH = "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/runner_v1.py"
CANARY_EXECUTE_SYMBOL = "run_section_11_13_5_live_canary_minimum_exposure_v1"
CANARY_SUBMIT_TRANSPORT_RELPATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CANARY_SUBMIT_TRANSPORT_SYMBOL = "run_canary_submit_transport_v1"
FILL_OBSERVED_PRODUCER = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "fill_observed_adjudication_v1.py::adjudicate_live_fill_observed_v1"
)
GATE_NAMES: tuple[str, ...] = (
    "LIVE_ENABLED",
    "LIVE_ARMED",
    "CANARY_AUTHORIZED",
    "RUNTIME_EXECUTION_AUTHORIZED",
    "OWNER_EXECUTION_PERMIT",
    "SESSION_AUTH",
    "PRIVATE_GET_AUTH",
    "DESTINATION_HOST",
    "NETWORK_EGRESS_COMPATIBILITY",
    "INSTRUMENT_BINDING",
    "INSTRUMENT_STATE",
    "ACCOUNT_MODE",
    "POSITION_MODE",
    "MARGIN_MODE",
    "LEVERAGE",
    "PRICE_BAND",
    "MAX_AVAILABLE_MAX_SIZE",
    "AVAILABLE_MARGIN",
    "RISK_SIZING",
    "MAX_POSITIONS",
    "EXISTING_POSITION_STATE",
    "ORDER_QUANTITY",
    "ORDER_TYPE",
    "FEES",
    "SLIPPAGE",
    "STOP_EXIT_SAFETY",
    "KILL_SWITCH",
    "RECONCILIATION",
    "SUBMIT_TRANSPORT",
    "WIRE_SEND_GATE",
    "POST_ACTION_EVIDENCE",
    "FAILURE_SEMANTICS",
)
SIDE_EFFECT_NAMES: tuple[str, ...] = (
    "PUBLIC_GET",
    "PRIVATE_GET",
    "SESSION_AUTH",
    "WIRE_SEND",
    "ORDER_SUBMIT",
    "ORDER_ACK",
    "ORDER_FILL",
    "POSITION_MUTATION",
    "FEE_INCURRED",
    "CAPTURE_PERSIST",
    "RESTART",
    "CRASH",
    "EXIT_ORDER",
    "STOP_ORDER",
    "RECONCILIATION_ACTION",
)
CRITICAL_DISTINCTIONS: tuple[str, ...] = (
    "LIVE_FILL_READINESS",
    "LIVE_FILL_EXECUTION_AUTHORIZATION",
    "CONTEMPORANEOUS_CAPTURE_AUTHORIZATION",
    "RESTART_AUTHORIZATION",
    "GENERAL_LIVE_TRADING_AUTHORIZATION",
)


def _repo_root(repo_root: object | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[3]
    return Path(repo_root)


def _gate_row(
    *,
    name: str,
    state: object,
    source: str,
    freshness: str,
    required: bool,
    satisfied: bool,
    blocking: bool,
    mutation_required: bool,
) -> dict[str, Any]:
    if freshness == "NO_CURRENT_GET" and satisfied is True:
        raise Section1114OfflineSurfaceError("MISSING_FRESHNESS_MUST_BLOCK")
    return {
        "GATE": name,
        "STATE": state,
        "SOURCE": source,
        "FRESHNESS": freshness,
        "REQUIRED_FOR_MINIMAL_FILL": required,
        "SATISFIED": satisfied,
        "BLOCKING": blocking,
        "MUTATION_REQUIRED": mutation_required,
        "MUTATION_AUTHORIZED_BY_THIS_GO": False,
    }


def prove_historical_fill_is_not_current_v1(
    *,
    candidate: dict[str, object] | None = None,
) -> dict[str, Any]:
    identity = dict(candidate or {})
    match = exact_identity_match_v1(
        ord_id=identity.get("ordId", BOUND_ORDID),
        clordid=identity.get("clOrdId", BOUND_CLORDID),
        inst_id=identity.get("instId", BOUND_INSTID),
    )
    if match["ORDER_IDENTITY_MATCH"] is True:
        return {
            "DOCUMENT_CLASS": "SECTION_11_14_HISTORICAL_FILL_REJECTION_V1",
            "HISTORICAL_BOUND_FILL_IS_CURRENT_FILL": False,
            "HISTORICAL_BOUND_FILL_ADMISSIBLE_AS_CONTEMPORANEOUS_CAPTURE_INPUT": False,
            "REASON": "HISTORICAL_EVIDENCE_IS_NOT_CURRENT_TRUTH",
            "BOUND_ORDID": BOUND_ORDID,
            "BOUND_CLORDID": BOUND_CLORDID,
            "BOUND_INSTID": BOUND_INSTID,
            "BOUND_POS_SIDE": BOUND_POS_SIDE,
            "BOUND_FILL_SZ": BOUND_FILL_SZ,
            "identity_match": match,
        }
    raise Section1114OfflineSurfaceError("HISTORICAL_IDENTITY_MUST_REMAIN_RECOGNIZABLE")


def prove_fixture_is_not_live_fill_v1(*, input_class: object) -> dict[str, Any]:
    klass = str(input_class or "").strip()
    if klass == INPUT_CLASS_TEST_FIXTURE:
        return {
            "DOCUMENT_CLASS": "SECTION_11_14_FIXTURE_FILL_REJECTION_V1",
            "TEST_FIXTURE_IS_LIVE_FILL": False,
            "TEST_FIXTURE_ADMISSIBLE_AS_PRODUCTIVE_CONTEMPORANEOUS_CAPTURE_INPUT": False,
            "INPUT_CLASS": klass,
            "REASON": "TEST_FIXTURE_IS_NOT_PRODUCTIVE_PROVENANCE",
        }
    if klass == INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_FILL_INPUT_MUST_REMAIN_ABSENT")
    raise Section1114OfflineSurfaceError("INPUT_CLASS_REJECTED")


def prove_fill_producer_call_path_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    call_path = reprove_productive_capture_call_path_v1(
        repo_root=root,
        storage_root=storage_root,
    )
    if call_path["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    if call_path["callgraph"]["IRREVERSIBLE_EFFECT_BEFORE_CAPTURE_CALLER"] != (
        "LIVE_IDENTITY_BOUND_VENUE_FILL"
    ):
        raise Section1114OfflineSurfaceError("IRREVERSIBLE_PREDECESSOR_DRIFT")
    if call_path["entrypoints"]["CANARY_EXECUTE_INVOKES_CAPTURE"] is True:
        raise Section1114OfflineSurfaceError("CANARY_EXECUTE_MUST_NOT_INVOKE_CAPTURE")
    if call_path["entrypoints"]["CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE"] is True:
        raise Section1114OfflineSurfaceError("CANARY_SUBMIT_MUST_NOT_INVOKE_CAPTURE")
    if CANONICAL_BOUND_FILL_KIND in FORBIDDEN_BOUND_FILL_KINDS:
        raise Section1114OfflineSurfaceError("CANONICAL_BOUND_FILL_KIND_FORBIDDEN")
    qty = canary_venue_contract_count_v1()
    if qty != SUI_OPERATIVE_ORDER_SZ:
        raise Section1114OfflineSurfaceError("OPERATIVE_QTY_DRIFT")
    nodes = (
        {
            "id": "SELECTED_BOUND_INSTRUMENT",
            "symbol": "DEFAULT_INSTRUMENT_ID",
            "value": DEFAULT_INSTRUMENT_ID,
            "inst_type": DEFAULT_INST_TYPE,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "SIZING_RISK",
            "symbol": "canary_venue_contract_count_v1",
            "value": qty,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "PRETRADE_GATES",
            "symbol": "evaluate_canary_submit_gates_v1+order_plan_v1",
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
            "REQUIRES_CURRENT_GET": True,
        },
        {
            "id": "ORDER_PLAN",
            "symbol": "build_canary_order_plan path in run_canary_submit_transport_v1",
            "side": DEFAULT_SIDE,
            "order_type": DEFAULT_ORDER_TYPE,
            "td_mode": DEFAULT_TD_MODE,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "SUBMIT_BOUNDARY",
            "symbol": "refuse_submit_unless_gates_pass_v1",
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "WIRE_SEND",
            "symbol": CANARY_SUBMIT_TRANSPORT_SYMBOL,
            "path": CANARY_SUBMIT_TRANSPORT_RELPATH,
            "endpoint": ENDPOINT_SUBMIT,
            "method": "POST",
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "VENUE_ACK",
            "symbol": "synchronous POST /api/v5/trade/order response",
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
            "IS_NOT_BOUND_FILL": True,
        },
        {
            "id": "VENUE_FILL",
            "symbol": "venue-executed fill of the identity-bound order",
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
            "PEAK_TRADE_DOES_NOT_SYNTHESIZE_FILL": True,
        },
        {
            "id": "LIVE_IDENTITY_BOUND_VENUE_FILL",
            "symbol": CANONICAL_BOUND_FILL_KIND,
            "identity_fields": ("clOrdId", "ordId", "instId", "posSide", "fillSz"),
            "observation_endpoint": ENDPOINT_TRADE_FILLS,
            "historical_observation_producer": FILL_OBSERVED_PRODUCER,
            "historical_identity_admissible": False,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "PRE_RESTART_CAPTURE_CALLER",
            "symbol": PRODUCTIVE_HOOK_CALLER,
            "path": CALLER_RELPATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
            "INVOKED_FROM_CANARY_EXECUTE": False,
        },
        {
            "id": "CAPTURE_OWNER",
            "symbol": PRODUCTIVE_CAPTURE_OWNER,
            "hook": PRODUCTIVE_LIFECYCLE_HOOK,
            "path": HOOK_RELPATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
    )
    gaps = (
        {
            "GAP": "CANARY_EXECUTE_DOES_NOT_INVOKE_CAPTURE_HOST_JOIN",
            "HOST_JOIN": HOST_JOIN_SYMBOL,
            "HOST_JOIN_PATH": HOST_JOIN_RELPATH,
            "CLOSED_BY_INTERPRETATION": False,
        },
        {
            "GAP": "SUBMIT_TRANSPORT_RETURNS_AFTER_ACK_AND_DOES_NOT_OBSERVE_FILL",
            "ACK_IS_NOT_FILL": True,
            "CLOSED_BY_INTERPRETATION": False,
        },
        {
            "GAP": "LIVE_IDENTITY_BOUND_VENUE_FILL_IS_VENUE_EFFECT_NOT_PEAK_TRADE_SYNTHESIS",
            "CLOSED_BY_INTERPRETATION": False,
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER_CALL_PATH_V1",
        "LIVE_IDENTITY_BOUND_VENUE_FILL_REQUIRED": True,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER": LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN": True,
        "CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "CAPTURE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "CANARY_EXECUTE_SYMBOL": CANARY_EXECUTE_SYMBOL,
        "CANARY_EXECUTE_RELPATH": CANARY_EXECUTE_RELPATH,
        "CANARY_SUBMIT_TRANSPORT_SYMBOL": CANARY_SUBMIT_TRANSPORT_SYMBOL,
        "CANARY_SUBMIT_TRANSPORT_RELPATH": CANARY_SUBMIT_TRANSPORT_RELPATH,
        "SUBMIT_ENDPOINT": ENDPOINT_SUBMIT,
        "FILL_OBSERVATION_ENDPOINT": ENDPOINT_TRADE_FILLS,
        "FUTURE_BOUND_IDENTITY_PARAMETERIZATION": True,
        "IDENTITY_PRODUCER_SYMBOL": "require_future_bound_fill_identity_v1",
        "CANARY_EXECUTE_INVOKES_CAPTURE": False,
        "CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE": False,
        "HISTORICAL_BOUND_FILL_ADMISSIBLE": False,
        "TEST_FIXTURE_ADMISSIBLE": False,
        "nodes": list(nodes),
        "gaps": list(gaps),
        "predecessor_call_path": call_path,
        "historical_fill_rejection": prove_historical_fill_is_not_current_v1(),
        "fixture_rejection": prove_fixture_is_not_live_fill_v1(
            input_class=INPUT_CLASS_TEST_FIXTURE
        ),
    }


def census_live_fill_readiness_matrix_v1() -> dict[str, Any]:
    if LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if OWNER_GO == OWNER_GO_EXECUTE:
        raise Section1114OfflineSurfaceError("THIS_GO_MUST_NOT_BE_EXECUTE_TOKEN")
    rows = (
        _gate_row(
            name="LIVE_ENABLED",
            state=False,
            source="constants_v1.LIVE_ENABLED",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="LIVE_ARMED",
            state=False,
            source="constants_v1.LIVE_ARMED",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="CANARY_AUTHORIZED",
            state=False,
            source="constants_v1.CANARY_AUTHORIZED",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="RUNTIME_EXECUTION_AUTHORIZED",
            state=False,
            source="constants_v1.SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="OWNER_EXECUTION_PERMIT",
            state=OWNER_GO,
            source="this OWNER_GO is not OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="SESSION_AUTH",
            state="UNAUTHORIZED_NO_CURRENT_SESSION",
            source=f"CREDENTIAL_USE_ALLOWED={CREDENTIAL_USE_ALLOWED}; {REQUIRED_SECRETREF_URI}",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="PRIVATE_GET_AUTH",
            state=False,
            source=f"PRIVATE_GET_ALLOWED={PRIVATE_GET_ALLOWED}",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="DESTINATION_HOST",
            state=f"CODE_BOUND_{REUSED_BINDING_REST_HOST}_CURRENT_CONNECTIVITY_UNKNOWN",
            source="REUSED_BINDING_REST_HOST",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="NETWORK_EGRESS_COMPATIBILITY",
            state="UNKNOWN",
            source="no current network observation authorized",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="INSTRUMENT_BINDING",
            state=DEFAULT_INSTRUMENT_ID,
            source="DEFAULT_INSTRUMENT_ID",
            freshness="STANDING_CODE_BINDING",
            required=True,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="INSTRUMENT_STATE",
            state="UNKNOWN",
            source="instrument_state_observation_v1 requires current GET",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="ACCOUNT_MODE",
            state="UNKNOWN",
            source="account/config GET not authorized",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="POSITION_MODE",
            state=f"REQUIRED={POS_MODE_REQUIRED_VALUE}_CURRENT=UNKNOWN",
            source="pos_mode_observation_v1.POS_MODE_REQUIRED_VALUE",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="MARGIN_MODE",
            state=f"REQUIRED={DEFAULT_TD_MODE}_CURRENT=UNKNOWN",
            source="DEFAULT_TD_MODE + leverage_observation LEVERAGE_EXPECTED_MGN_MODE",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="LEVERAGE",
            state=(
                f"REQUIRED_MGN_MODE={LEVERAGE_EXPECTED_MGN_MODE};"
                f"REQUIRED_POS_SIDE={LEVERAGE_EXPECTED_POS_SIDE};VALUE=UNKNOWN"
            ),
            source="leverage_observation_v1",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="PRICE_BAND",
            state="UNKNOWN",
            source="price_band_observation_v1 requires current GET",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="MAX_AVAILABLE_MAX_SIZE",
            state="UNKNOWN",
            source="max_size_observation_v1 / max_available_observation_v1",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="AVAILABLE_MARGIN",
            state="UNKNOWN",
            source="available_margin observation on submit path requires current GET",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="RISK_SIZING",
            state=f"PLANNED_QTY={SUI_OPERATIVE_ORDER_SZ}_VENUE_ADMISSION_UNKNOWN",
            source="canary_venue_contract_count_v1; minSz/lotSz admission requires GET",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="MAX_POSITIONS",
            state=POSITION_COUNT_LIMIT,
            source="POSITION_COUNT_LIMIT",
            freshness="STANDING_CODE_BINDING",
            required=True,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="EXISTING_POSITION_STATE",
            state="UNKNOWN_MUST_BE_ZERO_TO_SUBMIT",
            source="evaluate_pre_submit_exchange_state_v1 OPEN_POSITION_PRESENT",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="ORDER_QUANTITY",
            state=SUI_OPERATIVE_ORDER_SZ,
            source="SUI_OPERATIVE_ORDER_SZ; venue minSz/lotSz unknown",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="ORDER_TYPE",
            state=DEFAULT_ORDER_TYPE,
            source="DEFAULT_ORDER_TYPE",
            freshness="STANDING_CODE_BINDING",
            required=True,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="FEES",
            state="UNKNOWN",
            source="no current trade-fee GET authorized",
            freshness="NO_CURRENT_GET",
            required=False,
            satisfied=False,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="SLIPPAGE",
            state="UNKNOWN",
            source="LIMIT px quantized from current ticker; ticker GET unauthorized",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="STOP_EXIT_SAFETY",
            state="SEPARATE_FLATTEN_PATH_NOT_PART_OF_ENTRY_FILL",
            source="flatten_execute is a distinct unauthorized path",
            freshness="STANDING_CODE_BINDING",
            required=False,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="KILL_SWITCH",
            state="UNKNOWN_NO_CURRENT_RUNTIME_OBSERVATION",
            source="lifecycle_v1 kill-switch contract is not a current observation",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="RECONCILIATION",
            state=LIVE_RECONCILIATION_PROVEN,
            source="canary constants LIVE_RECONCILIATION_PROVEN standing predicate",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
        _gate_row(
            name="SUBMIT_TRANSPORT",
            state=CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
            source="CANARY_SUBMIT_TRANSPORT_IMPLEMENTED; POST_ALLOWED=false",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="WIRE_SEND_GATE",
            state=False,
            source="allow_productive_wire_send default false; POST_ALLOWED=false",
            freshness="STANDING_CONSTANT",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=True,
        ),
        _gate_row(
            name="POST_ACTION_EVIDENCE",
            state="FILL_GET_NOT_ON_SUBMIT_RETURN_PATH",
            source=f"{ENDPOINT_TRADE_FILLS} is a later GET; this GO forbids GET",
            freshness="NO_CURRENT_GET",
            required=True,
            satisfied=False,
            blocking=True,
            mutation_required=False,
        ),
        _gate_row(
            name="FAILURE_SEMANTICS",
            state="FAIL_CLOSED_NO_RETRY_NO_SECOND_SUBMIT",
            source="RETRY_DEFAULT=false; SECOND_SUBMIT_DEFAULT=false; UNKNOWN_SUBMIT recon",
            freshness="STANDING_CODE_BINDING",
            required=True,
            satisfied=True,
            blocking=False,
            mutation_required=False,
        ),
    )
    names = tuple(row["GATE"] for row in rows)
    if names != GATE_NAMES:
        raise Section1114OfflineSurfaceError("READINESS_MATRIX_INCOMPLETE")
    if any(row["MUTATION_AUTHORIZED_BY_THIS_GO"] is True for row in rows):
        raise Section1114OfflineSurfaceError("GATE_MUTATION_MUST_REMAIN_UNAUTHORIZED")
    blocking = [row["GATE"] for row in rows if row["BLOCKING"] is True]
    if not blocking:
        raise Section1114OfflineSurfaceError("READINESS_MUST_REMAIN_BLOCKED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_FILL_READINESS_MATRIX_V1",
        "LIVE_FILL_READINESS_MATRIX_STATUS": LIVE_FILL_READINESS_MATRIX_STATUS,
        "LIVE_FILL_READINESS": False,
        "BLOCKING_GATE_COUNT": len(blocking),
        "BLOCKING_GATES": blocking,
        "THIS_GO_IS_NOT_GATE_BYPASS": True,
        "THIS_GO_IS_NOT_EXECUTE_TOKEN": True,
        "OWNER_GO_EXECUTE_TOKEN": OWNER_GO_EXECUTE,
        "AUTHORIZATION_SCOPE": AUTHORIZATION_SCOPE,
        "BLOCKS_NEW_ENTRY": BLOCKS_NEW_ENTRY,
        "ORDER_COUNT_LIMIT": ORDER_COUNT_LIMIT,
        "POSITION_COUNT_LIMIT": POSITION_COUNT_LIMIT,
        "REQUIRED_ENVIRONMENT": REQUIRED_ENVIRONMENT,
        "rows": list(rows),
    }


def bind_minimal_economic_action_contract_v1() -> dict[str, Any]:
    qty = canary_venue_contract_count_v1()
    contract = {
        "DOCUMENT_CLASS": "SECTION_11_14_MINIMAL_ECONOMIC_ACTION_CONTRACT_V1",
        "MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS": MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS,
        "VENUE": REUSED_BINDING_REST_HOST,
        "INSTRUMENT_ID": DEFAULT_INSTRUMENT_ID,
        "SIDE": DEFAULT_SIDE,
        "ORDER_TYPE": DEFAULT_ORDER_TYPE,
        "ORDER_QTY": qty,
        "PRICE_OR_PRICE_POLICY": "UNKNOWN",
        "TD_MODE": DEFAULT_TD_MODE,
        "POSITION_MODE": POS_MODE_REQUIRED_VALUE,
        "LEVERAGE": "UNKNOWN",
        "EXPECTED_MAX_NOTIONAL": "UNKNOWN",
        "EXPECTED_FEES": "UNKNOWN",
        "SLIPPAGE_BOUND": "UNKNOWN",
        "STOP_EXIT_POLICY": "SEPARATE_FLATTEN_PATH_NOT_PART_OF_THIS_FILL",
        "MAX_POSITION_COUNT": POSITION_COUNT_LIMIT,
        "EXPECTED_PRE_EXISTING_POSITION": "UNKNOWN",
        "POST_FILL_CAPTURE_EXPECTATION": (
            f"{HOST_JOIN_SYMBOL} after proven {CANONICAL_BOUND_FILL_KIND}; "
            "canary execute currently does not invoke the host join"
        ),
        "MAX_ORDERS": ORDER_COUNT_LIMIT,
        "MAX_WIRE_SEND_COUNT": 1,
        "UNKNOWN_FIELDS": (
            "PRICE_OR_PRICE_POLICY",
            "LEVERAGE",
            "EXPECTED_MAX_NOTIONAL",
            "EXPECTED_FEES",
            "SLIPPAGE_BOUND",
            "EXPECTED_PRE_EXISTING_POSITION",
        ),
        "BLOCKED_REASON": "MISSING_CURRENT_GET_FRESHNESS",
        "HISTORICAL_FILL_MAY_NOT_SUPPLY_THESE_VALUES": True,
        "ESTIMATION_FORBIDDEN": True,
        "EXECUTED": False,
        "AUTHORIZED_BY_THIS_GO": False,
    }
    unknown = tuple(contract["UNKNOWN_FIELDS"])
    if any(str(contract[name]) != "UNKNOWN" for name in unknown):
        raise Section1114OfflineSurfaceError("UNKNOWN_FIELD_MUST_REMAIN_UNKNOWN")
    return contract


def census_execution_side_effect_graph_v1() -> dict[str, Any]:
    rows = (
        {
            "EFFECT": "PUBLIC_GET",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "FAIL_CLOSED_BEFORE_SUBMIT",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "PRIVATE_GET",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "FAIL_CLOSED_BEFORE_SUBMIT",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "SESSION_AUTH",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "FAIL_CLOSED_NO_HANDLE",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "WIRE_SEND",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "FAIL_CLOSED_NO_WIRE_BACKEND_OR_GATE",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "ORDER_SUBMIT",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "FAIL_CLOSED_AT_REFUSE_SUBMIT",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "ORDER_ACK",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "UNKNOWN_SUBMIT_NO_BLIND_RETRY",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "ORDER_FILL",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "ACK_WITHOUT_FILL_IS_NOT_BOUND_FILL",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "POSITION_MUTATION",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "VENUE_FILL_IS_IRREVERSIBLE",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "FEE_INCURRED",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "MISSING_FEE_FAILS_LATER_LADDER_NOT_THIS_CONTRACT",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "CAPTURE_PERSIST",
            "REACHABLE": True,
            "REQUIRED": True,
            "EXPECTED": True,
            "FAILURE_MODE": "EXECUTE_DOES_NOT_INVOKE_HOST_JOIN",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "RESTART",
            "REACHABLE": True,
            "REQUIRED": False,
            "EXPECTED": False,
            "FAILURE_MODE": "NOT_AUTHORIZED_SEPARATE_GO_REQUIRED",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "CRASH",
            "REACHABLE": False,
            "REQUIRED": False,
            "EXPECTED": False,
            "FAILURE_MODE": "NO_CRASH_INJECTION_ON_PATH",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "EXIT_ORDER",
            "REACHABLE": True,
            "REQUIRED": False,
            "EXPECTED": False,
            "FAILURE_MODE": "FLATTEN_PATH_SEPARATE_UNAUTHORIZED",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "STOP_ORDER",
            "REACHABLE": True,
            "REQUIRED": False,
            "EXPECTED": False,
            "FAILURE_MODE": "FLATTEN_PATH_SEPARATE_UNAUTHORIZED",
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "EFFECT": "RECONCILIATION_ACTION",
            "REACHABLE": True,
            "REQUIRED": False,
            "EXPECTED": False,
            "FAILURE_MODE": "READ_ONLY_RECON_IS_NOT_SYNCHRONOUS_ACK",
            "CURRENTLY_AUTHORIZED": False,
        },
    )
    names = tuple(row["EFFECT"] for row in rows)
    if names != SIDE_EFFECT_NAMES:
        raise Section1114OfflineSurfaceError("SIDE_EFFECT_GRAPH_INCOMPLETE")
    if any(row["CURRENTLY_AUTHORIZED"] is True for row in rows):
        raise Section1114OfflineSurfaceError("NO_SIDE_EFFECT_AUTHORIZED_BY_THIS_GO")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_EXECUTION_SIDE_EFFECT_GRAPH_V1",
        "rows": list(rows),
        "ANY_SIDE_EFFECT_AUTHORIZED_BY_THIS_GO": False,
        "MAX_ECONOMIC_ACTIONS_IF_LATER_AUTHORIZED": 1,
    }


def bind_future_execution_owner_go_contract_v1() -> dict[str, Any]:
    if LIVE_FILL_READINESS is True:
        raise Section1114OfflineSurfaceError("READINESS_MUST_REMAIN_FALSE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_FUTURE_EXECUTION_OWNER_GO_CONTRACT_V1",
        "FUTURE_EXECUTION_OWNER_GO_REQUIRED": True,
        "FUTURE_EXECUTION_OWNER_GO_SCOPE": FUTURE_EXECUTION_OWNER_GO_SCOPE,
        "FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN": FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
        "CONSUMED_BY_THIS_GO": False,
        "FAIL_CLOSED": True,
        "READINESS_MUST_BE_REPROVEN_AT_CONSUMPTION": True,
        "bindings": {
            "WORKPACKAGE_VERSION": FUTURE_EXECUTION_OWNER_GO_SCOPE,
            "ORIGIN_MAIN_OR_PR_HEAD": "MUST_BIND_THEN_CURRENT_EXACT_HEAD",
            "INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "MAX_ORDERS": 1,
            "MAX_QUANTITY": SUI_OPERATIVE_ORDER_SZ,
            "MAX_NOTIONAL": "MUST_BIND_FRESH_PRETRADE_NOTIONAL_AT_CONSUMPTION",
            "SIDE": DEFAULT_SIDE,
            "ORDER_TYPE": DEFAULT_ORDER_TYPE,
            "MAX_WIRE_SEND_COUNT": 1,
            "MAX_POSITIONS": 1,
            "SECOND_POSITION": False,
            "RETRY_WITH_ECONOMIC_DUPLICATION": False,
            "GATE_BYPASS": False,
            "FAIL_CLOSED_ON_VENUE_AUTH_PRETRADE_DEVIATION": True,
            "CAPTURE_AFTER_ACTUAL_BOUND_FILL": True,
            "RESTART": "FORBIDDEN_UNLESS_SEPARATELY_AUTHORIZED",
        },
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "NEXT_SLICE_AUTHORIZED": False,
    }


def adjudicate_critical_distinctions_v1() -> dict[str, Any]:
    rows = (
        {
            "ID": "A",
            "NAME": "LIVE_FILL_READINESS",
            "VALUE": False,
            "EQUALS_EXECUTION_AUTHORIZATION": False,
        },
        {
            "ID": "B",
            "NAME": "LIVE_FILL_EXECUTION_AUTHORIZATION",
            "VALUE": False,
            "EQUALS_GENERAL_LIVE_TRADING": False,
        },
        {
            "ID": "C",
            "NAME": "CONTEMPORANEOUS_CAPTURE_AUTHORIZATION",
            "VALUE": False,
            "EQUALS_SUCCESSFUL_FILL": False,
        },
        {
            "ID": "D",
            "NAME": "RESTART_AUTHORIZATION",
            "VALUE": False,
            "EQUALS_SUCCESSFUL_CAPTURE": False,
        },
        {
            "ID": "E",
            "NAME": "GENERAL_LIVE_TRADING_AUTHORIZATION",
            "VALUE": False,
            "EQUALS_SINGLE_FILL": False,
        },
    )
    names = tuple(row["NAME"] for row in rows)
    if names != CRITICAL_DISTINCTIONS:
        raise Section1114OfflineSurfaceError("CRITICAL_DISTINCTION_INCOMPLETE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CRITICAL_DISTINCTION_V1",
        "SINGLE_AUTHORIZED_FILL_IS_NOT_GENERAL_LIVE_RELEASE": True,
        "SUCCESSFUL_FILL_IS_NOT_SUCCESSFUL_CAPTURE": True,
        "SUCCESSFUL_CAPTURE_IS_NOT_RESTART_RECONSTRUCTION": True,
        "RESTART_RECONSTRUCTION_IS_NOT_GENERAL_LIVE_RELEASE": True,
        "rows": list(rows),
    }


def prove_this_go_does_not_submit_or_mutate_v1() -> dict[str, Any]:
    if POST_ALLOWED is True or ORDER_SUBMIT_ALLOWED is True:
        raise Section1114OfflineSurfaceError("SUBMIT_MUST_REMAIN_FORBIDDEN")
    if PUBLIC_GET_ALLOWED is True or PRIVATE_GET_ALLOWED is True:
        raise Section1114OfflineSurfaceError("GET_MUST_REMAIN_FORBIDDEN")
    if CREDENTIAL_USE_ALLOWED is True:
        raise Section1114OfflineSurfaceError("CREDENTIAL_USE_MUST_REMAIN_FORBIDDEN")
    if CANARY_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("CANARY_MUST_REMAIN_UNAUTHORIZED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_READINESS_NON_EXECUTION_PROOF_V1",
        "LIVE_FILL_EXECUTION_AUTHORIZED": False,
        "LIVE_FILL_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "RESTART_EXECUTED": False,
        "GET_PERFORMED": False,
        "POST_USED": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
    }


def bind_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    producer = prove_fill_producer_call_path_v1(repo_root=root, storage_root=storage_root)
    matrix = census_live_fill_readiness_matrix_v1()
    economic = bind_minimal_economic_action_contract_v1()
    side_effects = census_execution_side_effect_graph_v1()
    future_go = bind_future_execution_owner_go_contract_v1()
    distinctions = adjudicate_critical_distinctions_v1()
    non_execution = prove_this_go_does_not_submit_or_mutate_v1()
    if matrix["LIVE_FILL_READINESS"] is True:
        raise Section1114OfflineSurfaceError("READINESS_MUST_REMAIN_FALSE")
    if economic["AUTHORIZED_BY_THIS_GO"] is True:
        raise Section1114OfflineSurfaceError("ECONOMIC_ACTION_MUST_REMAIN_UNAUTHORIZED")
    identity = require_future_bound_fill_identity_v1(
        bound_fill_identity={
            "clOrdId": "future-not-historical",
            "ordId": "future-not-historical",
            "instId": DEFAULT_INSTRUMENT_ID,
            "posSide": LEVERAGE_EXPECTED_POS_SIDE,
            "fillSz": SUI_OPERATIVE_ORDER_SZ,
        }
    )
    if identity["ordId"] == BOUND_ORDID:
        raise Section1114OfflineSurfaceError("FUTURE_IDENTITY_MUST_NOT_EQUAL_HISTORICAL")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_IDENTITY_BOUND_VENUE_FILL_READINESS_AND_EXACT_EXECUTION_CONTRACT_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_REQUIRED": True,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER": LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN": True,
        "LIVE_FILL_READINESS_MATRIX_STATUS": LIVE_FILL_READINESS_MATRIX_STATUS,
        "LIVE_FILL_READINESS": False,
        "BLOCKING_GATE_COUNT": matrix["BLOCKING_GATE_COUNT"],
        "BLOCKING_GATES": list(matrix["BLOCKING_GATES"]),
        "MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS": MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS,
        "VENUE": economic["VENUE"],
        "INSTRUMENT_ID": economic["INSTRUMENT_ID"],
        "SIDE": economic["SIDE"],
        "ORDER_TYPE": economic["ORDER_TYPE"],
        "ORDER_QTY": economic["ORDER_QTY"],
        "MAX_NOTIONAL": economic["EXPECTED_MAX_NOTIONAL"],
        "MAX_POSITIONS": economic["MAX_POSITION_COUNT"],
        "SESSION_AUTH_READY": False,
        "PRIVATE_GET_READY": False,
        "PRETRADE_READY": False,
        "RISK_READY": False,
        "TRANSPORT_READY": False,
        "WIRE_SEND_GATE_READY": False,
        "LIVE_FILL_EXECUTION_AUTHORIZED": False,
        "LIVE_FILL_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "RESTART_EXECUTED": False,
        "FUTURE_EXECUTION_OWNER_GO_REQUIRED": True,
        "FUTURE_EXECUTION_OWNER_GO_SCOPE": FUTURE_EXECUTION_OWNER_GO_SCOPE,
        "FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN": FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "NEXT_SLICE_AUTHORIZED": False,
        "producer": producer,
        "readiness_matrix": matrix,
        "economic_contract": economic,
        "side_effects": side_effects,
        "future_execution_go": future_go,
        "critical_distinctions": distinctions,
        "non_execution": non_execution,
        "call_path": producer["predecessor_call_path"],
    }
