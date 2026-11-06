"""Contemporaneous exact-single fill then PRE-RESTART capture adjudication.

This slice re-proves the productive fill producer, re-adjudicates Live-fill
readiness gates from current standing constants, and proves the capture-hook
code gap plus the bounded invocation-scoped repair seam. It does not GET.
It does not POST. It does not wire-send. It does not mutate standing Live
gates. It does not restart. Historical BOUND_* identity and TEST_FIXTURE
remain inadmissible as contemporaneous capture input.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    OWNER_GO_EXECUTE,
    POSITION_COUNT_LIMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    PRODUCTIVE_HOOK_CALLER,
    build_contemporaneous_field_provenance_from_bound_fill_v1,
    call_pre_restart_handoff_capture_after_bound_fill_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
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
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1 import (
    FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
    GATE_NAMES,
    LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
    prove_fill_producer_call_path_v1,
    prove_fixture_is_not_live_fill_v1,
    prove_historical_fill_is_not_current_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
)

LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN = True
CAPTURE_CALLER = PRODUCTIVE_HOOK_CALLER
CAPTURE_CALLER_ACCEPTS_HISTORICAL_FILL = False
CAPTURE_CALLER_ACCEPTS_FIXTURE_FILL = False
CAPTURE_CALLER_ACCEPTS_SYNTHETIC_FILL = False
CODE_CHANGE_REQUIRED = True
CODE_GAP_ID = "PRODUCTIVE_CAPTURE_HOOK_DEFAULT_REFUSES_PRODUCTIVE_BOUND_FILL_INPUT"
TERMINAL_STATE = "CODE_GAP_FOUND"
CASE_ADJUDICATION = (
    "CASE_CODE_GAP_FOUND_PRODUCTIVE_CAPTURE_DEFAULT_UNAUTHORIZED_"
    "INVOCATION_SCOPED_SEAM_REPAIRED_NO_LIVE_SUBMIT"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_"
    "THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_AFTER_CAPTURE_SEAM_REPAIR_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)
REQUIRED_BLOCKING_GATE_NAMES: tuple[str, ...] = (
    "LIVE_ENABLED",
    "LIVE_ARMED",
    "CANARY_AUTHORIZED",
    "RUNTIME_EXECUTION_AUTHORIZED",
    "OWNER_EXECUTION_PERMIT",
    "SESSION_AUTH",
    "PRIVATE_GET_AUTH",
    "DESTINATION_HOST",
    "NETWORK_EGRESS_COMPATIBILITY",
    "INSTRUMENT_STATE",
    "ACCOUNT_MODE",
    "POSITION_MODE",
    "MARGIN_MODE",
    "LEVERAGE",
    "PRICE_BAND",
    "MAX_AVAILABLE_MAX_SIZE",
    "AVAILABLE_MARGIN",
    "RISK_SIZING",
    "EXISTING_POSITION_STATE",
    "ORDER_QUANTITY",
    "SLIPPAGE",
    "KILL_SWITCH",
    "SUBMIT_TRANSPORT",
    "WIRE_SEND_GATE",
    "POST_ACTION_EVIDENCE",
)
_SEAM_IDENTITY = {
    "clOrdId": "ptprodidentityclordidseam000001",
    "ordId": "1888000777666555444",
    "instId": "ETH-USD_UM_XPERP-SEAM",
    "posSide": "net",
    "fillSz": "1",
}


def _repo_root(repo_root: object | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[3]
    return Path(repo_root)


def _gate(
    *,
    name: str,
    status: str,
    evidence_class: str,
    evidence: str,
    required: bool,
) -> dict[str, Any]:
    if status not in {"PASS", "BLOCKED", "UNKNOWN"}:
        raise Section1114OfflineSurfaceError("GATE_STATUS_TAXONOMY_DRIFT")
    blocking = required is True and status != "PASS"
    return {
        "GATE": name,
        "GATE_STATUS": status,
        "EVIDENCE_CLASS": evidence_class,
        "EVIDENCE": evidence,
        "REQUIRED_FOR_MINIMAL_FILL": required,
        "BLOCKING": blocking,
        "SATISFIED": status == "PASS",
    }


def census_contemporaneous_live_fill_readiness_matrix_v1() -> dict[str, Any]:
    qty = canary_venue_contract_count_v1()
    owner_permit_pass = OWNER_GO == FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN
    rows = (
        _gate(
            name="LIVE_ENABLED",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="section_11_14 constants_v1.LIVE_ENABLED; mutation not authorized",
            required=True,
        ),
        _gate(
            name="LIVE_ARMED",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="section_11_14 constants_v1.LIVE_ARMED; mutation not authorized",
            required=True,
        ),
        _gate(
            name="CANARY_AUTHORIZED",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="section_11_14 constants_v1.CANARY_AUTHORIZED",
            required=True,
        ),
        _gate(
            name="RUNTIME_EXECUTION_AUTHORIZED",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED standing false",
            required=True,
        ),
        _gate(
            name="OWNER_EXECUTION_PERMIT",
            status="PASS" if owner_permit_pass else "BLOCKED",
            evidence_class="OWNER_GO_TOKEN_MATCH",
            evidence=OWNER_GO,
            required=True,
        ),
        _gate(
            name="SESSION_AUTH",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT_NO_CURRENT_SESSION",
            evidence="CREDENTIAL_USE_ALLOWED=false; no current session authorized",
            required=True,
        ),
        _gate(
            name="PRIVATE_GET_AUTH",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="PRIVATE_GET_ALLOWED=false",
            required=True,
        ),
        _gate(
            name="DESTINATION_HOST",
            status="UNKNOWN",
            evidence_class="CODE_BOUND_CONNECTIVITY_UNKNOWN",
            evidence=f"REUSED_BINDING_REST_HOST={REUSED_BINDING_REST_HOST}",
            required=True,
        ),
        _gate(
            name="NETWORK_EGRESS_COMPATIBILITY",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_NETWORK_OBSERVATION",
            evidence="network observation not authorized by this GO without GET/POST",
            required=True,
        ),
        _gate(
            name="INSTRUMENT_BINDING",
            status="PASS",
            evidence_class="STANDING_CODE_BINDING",
            evidence=DEFAULT_INSTRUMENT_ID,
            required=True,
        ),
        _gate(
            name="INSTRUMENT_STATE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="instrument_state_observation_v1 requires current GET",
            required=True,
        ),
        _gate(
            name="ACCOUNT_MODE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="account/config GET not authorized",
            required=True,
        ),
        _gate(
            name="POSITION_MODE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="pos_mode_observation_v1 CURRENT=UNKNOWN",
            required=True,
        ),
        _gate(
            name="MARGIN_MODE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="REQUIRED=cross CURRENT=UNKNOWN",
            required=True,
        ),
        _gate(
            name="LEVERAGE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="leverage_observation_v1 VALUE=UNKNOWN",
            required=True,
        ),
        _gate(
            name="PRICE_BAND",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="price_band_observation_v1 requires current GET",
            required=True,
        ),
        _gate(
            name="MAX_AVAILABLE_MAX_SIZE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="max_size/max_available observation requires current GET",
            required=True,
        ),
        _gate(
            name="AVAILABLE_MARGIN",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="available_margin observation requires current GET",
            required=True,
        ),
        _gate(
            name="RISK_SIZING",
            status="UNKNOWN",
            evidence_class="PLANNED_QTY_VENUE_ADMISSION_UNKNOWN",
            evidence=f"PLANNED_QTY={qty}; minSz/lotSz admission requires GET",
            required=True,
        ),
        _gate(
            name="MAX_POSITIONS",
            status="PASS",
            evidence_class="STANDING_CODE_BINDING",
            evidence=str(POSITION_COUNT_LIMIT),
            required=True,
        ),
        _gate(
            name="EXISTING_POSITION_STATE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="OPEN_POSITION_PRESENT unknown; must be zero to submit",
            required=True,
        ),
        _gate(
            name="ORDER_QUANTITY",
            status="UNKNOWN",
            evidence_class="CODE_BOUND_VENUE_ADMISSION_UNKNOWN",
            evidence=f"SUI_OPERATIVE_ORDER_SZ={SUI_OPERATIVE_ORDER_SZ}",
            required=True,
        ),
        _gate(
            name="ORDER_TYPE",
            status="PASS",
            evidence_class="STANDING_CODE_BINDING",
            evidence=DEFAULT_ORDER_TYPE,
            required=True,
        ),
        _gate(
            name="FEES",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="trade-fee GET not authorized",
            required=False,
        ),
        _gate(
            name="SLIPPAGE",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_GET",
            evidence="LIMIT px quantized from current ticker; ticker GET unauthorized",
            required=True,
        ),
        _gate(
            name="STOP_EXIT_SAFETY",
            status="PASS",
            evidence_class="STANDING_CODE_BINDING",
            evidence="flatten_execute is a distinct unauthorized path",
            required=False,
        ),
        _gate(
            name="KILL_SWITCH",
            status="UNKNOWN",
            evidence_class="NO_CURRENT_RUNTIME_OBSERVATION",
            evidence="lifecycle_v1 kill-switch contract is not a current observation",
            required=True,
        ),
        _gate(
            name="RECONCILIATION",
            status="PASS",
            evidence_class="STANDING_CONSTANT",
            evidence="LIVE_RECONCILIATION_PROVEN standing predicate",
            required=True,
        ),
        _gate(
            name="SUBMIT_TRANSPORT",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence=(
                f"CANARY_SUBMIT_TRANSPORT_IMPLEMENTED={CANARY_SUBMIT_TRANSPORT_IMPLEMENTED}; "
                f"POST_ALLOWED={POST_ALLOWED}"
            ),
            required=True,
        ),
        _gate(
            name="WIRE_SEND_GATE",
            status="BLOCKED",
            evidence_class="STANDING_CONSTANT",
            evidence="allow_productive_wire_send default false; POST_ALLOWED=false",
            required=True,
        ),
        _gate(
            name="POST_ACTION_EVIDENCE",
            status="BLOCKED",
            evidence_class="NO_CURRENT_GET",
            evidence="/api/v5/trade/fills is a later GET; PRIVATE_GET_ALLOWED=false",
            required=True,
        ),
        _gate(
            name="FAILURE_SEMANTICS",
            status="PASS",
            evidence_class="STANDING_CODE_BINDING",
            evidence="RETRY_DEFAULT=false; SECOND_SUBMIT_DEFAULT=false",
            required=True,
        ),
    )
    names = tuple(str(row["GATE"]) for row in rows)
    if names != GATE_NAMES:
        raise Section1114OfflineSurfaceError("GATE_NAME_CENSUS_DRIFT")
    if LIVE_ENABLED is True or LIVE_ARMED is True or CANARY_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("STANDING_LIVE_GATE_TRUE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if POST_ALLOWED is True or PRIVATE_GET_ALLOWED is True or CREDENTIAL_USE_ALLOWED is True:
        raise Section1114OfflineSurfaceError("STANDING_MUTATION_GATE_TRUE")
    blocking = [str(row["GATE"]) for row in rows if row["BLOCKING"] is True]
    required_blocking = [name for name in REQUIRED_BLOCKING_GATE_NAMES if name in blocking]
    missing_required = [
        name for name in REQUIRED_BLOCKING_GATE_NAMES if name not in {row["GATE"] for row in rows}
    ]
    if missing_required:
        raise Section1114OfflineSurfaceError("REQUIRED_GATE_CENSUS_DRIFT")
    live_fill_readiness = len(required_blocking) == 0
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CONTEMPORANEOUS_LIVE_FILL_READINESS_MATRIX_V1",
        "LIVE_FILL_READINESS_MATRIX_STATUS": "COMPLETE",
        "LIVE_FILL_READINESS": live_fill_readiness,
        "BLOCKING_GATE_COUNT": len(required_blocking),
        "BLOCKING_GATES": required_blocking,
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "HISTORICAL_MATRIX_IS_NOT_CONTEMPORANEOUS_PASS": True,
        "rows": list(rows),
    }


def bind_minimal_economic_action_contract_v1() -> dict[str, Any]:
    qty = canary_venue_contract_count_v1()
    if qty != SUI_OPERATIVE_ORDER_SZ:
        raise Section1114OfflineSurfaceError("OPERATIVE_QTY_DRIFT")
    if DEFAULT_INSTRUMENT_ID != "SUI-USD_UM_XPERP-310404":
        raise Section1114OfflineSurfaceError("INSTRUMENT_BINDING_DRIFT")
    if DEFAULT_SIDE != "BUY" or DEFAULT_ORDER_TYPE != "LIMIT":
        raise Section1114OfflineSurfaceError("ORDER_PLAN_BINDING_DRIFT")
    unknown_fields = (
        "PRICE_OR_PRICE_POLICY",
        "LEVERAGE",
        "EXPECTED_MAX_NOTIONAL",
        "EXPECTED_FEES",
        "SLIPPAGE_BOUND",
        "EXPECTED_PRE_EXISTING_POSITION",
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_MINIMAL_ECONOMIC_ACTION_CONTRACT_V1",
        "MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS": "BLOCKED",
        "EXACT_ECONOMIC_ACTION_CONTRACT_STATUS": "BLOCKED",
        "BLOCKED_REASON": "MISSING_CURRENT_GET_FRESHNESS",
        "ESTIMATION_FORBIDDEN": True,
        "AUTHORIZED_BY_THIS_GO": False,
        "EXECUTED": False,
        "VENUE": REUSED_BINDING_REST_HOST,
        "INSTRUMENT_ID": DEFAULT_INSTRUMENT_ID,
        "SIDE": DEFAULT_SIDE,
        "ORDER_TYPE": DEFAULT_ORDER_TYPE,
        "ORDER_QTY": qty,
        "TD_MODE": DEFAULT_TD_MODE,
        "MAX_POSITION_COUNT": POSITION_COUNT_LIMIT,
        "MAX_ORDERS": 1,
        "MAX_WIRE_SEND_COUNT": 1,
        "PRICE_OR_PRICE_POLICY": "UNKNOWN",
        "EXECUTION_LIMIT_PRICE": "UNKNOWN",
        "LEVERAGE": "UNKNOWN",
        "EXPECTED_MAX_NOTIONAL": "UNKNOWN",
        "EXECUTION_MAX_NOTIONAL": "UNKNOWN",
        "EXPECTED_FEES": "UNKNOWN",
        "SLIPPAGE_BOUND": "UNKNOWN",
        "EXPECTED_PRE_EXISTING_POSITION": "UNKNOWN",
        "UNKNOWN_FIELDS": list(unknown_fields),
        "CANARY_TECHNICAL_EXECUTE_TOKEN": OWNER_GO_EXECUTE,
        "WORKPACKAGE_OWNER_GO": OWNER_GO,
    }


def prove_capture_caller_semantics_v1(*, storage_root: Path) -> dict[str, Any]:
    fixture_rejection = prove_fixture_is_not_live_fill_v1(input_class=INPUT_CLASS_TEST_FIXTURE)
    historical_rejection = prove_historical_fill_is_not_current_v1()
    lifecycle_id = "code-gap-default-unauthorized-lifecycle"
    provenance = build_contemporaneous_field_provenance_from_bound_fill_v1(
        bound_fill_identity=_SEAM_IDENTITY,
        peak_trade_owned_resulting_current_position_qty="1",
        lifecycle_id=lifecycle_id,
        input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    )
    hook_kwargs: dict[str, Any] = {
        "storage_root": storage_root,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": dict(_SEAM_IDENTITY),
        "peak_trade_owned_resulting_current_position_qty": "1",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T18:45:00Z",
        "capture_started_at": "2026-09-07T18:45:01Z",
        "attempt_identity": "code-gap-default-unauthorized-attempt",
        "input_class": INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        "lifecycle_id": lifecycle_id,
        "field_provenance": provenance,
    }
    default_error = ""
    try:
        run_capture_hook_after_bound_fill_before_restart_v1(**hook_kwargs)
    except Section1114OfflineSurfaceError as exc:
        default_error = str(exc)
    else:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_INPUT_MUST_REMAIN_UNAUTHORIZED")
    if "RUNTIME_EXECUTION_UNAUTHORIZED" not in default_error:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_INPUT_MUST_REMAIN_UNAUTHORIZED")

    fixture_error = ""
    fixture_kwargs = dict(hook_kwargs)
    fixture_kwargs["input_class"] = INPUT_CLASS_TEST_FIXTURE
    fixture_kwargs["runtime_execution_authorized"] = True
    fixture_kwargs["field_provenance"] = build_contemporaneous_field_provenance_from_bound_fill_v1(
        bound_fill_identity=_SEAM_IDENTITY,
        peak_trade_owned_resulting_current_position_qty="1",
        lifecycle_id="code-gap-fixture-rejected-lifecycle",
        input_class=INPUT_CLASS_TEST_FIXTURE,
    )
    fixture_kwargs["lifecycle_id"] = "code-gap-fixture-rejected-lifecycle"
    try:
        run_capture_hook_after_bound_fill_before_restart_v1(**fixture_kwargs)
    except Section1114OfflineSurfaceError as exc:
        fixture_error = str(exc)
    else:
        raise Section1114OfflineSurfaceError("FIXTURE_MUST_REMAIN_NON_PRODUCTIVE")
    if "FIXTURE_FILL_NOT_PRODUCTIVE" not in fixture_error:
        raise Section1114OfflineSurfaceError("FIXTURE_MUST_REMAIN_NON_PRODUCTIVE")

    historical_error = ""
    historical_kwargs = dict(hook_kwargs)
    historical_kwargs["runtime_execution_authorized"] = True
    historical_kwargs["source_is_historical_evidence"] = True
    try:
        run_capture_hook_after_bound_fill_before_restart_v1(**historical_kwargs)
    except Section1114OfflineSurfaceError as exc:
        historical_error = str(exc)
    else:
        raise Section1114OfflineSurfaceError("HISTORICAL_FILL_MUST_REMAIN_REJECTED")
    if "HISTORICAL_EVIDENCE_IS_NOT_CURRENT_RUNTIME" not in historical_error:
        raise Section1114OfflineSurfaceError("HISTORICAL_FILL_MUST_REMAIN_REJECTED")

    with tempfile.TemporaryDirectory(prefix="pt-11-14-offline-seam-") as tmp:
        seam_root = Path(tmp)
        seam_result = call_pre_restart_handoff_capture_after_bound_fill_v1(
            storage_root=seam_root,
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=dict(_SEAM_IDENTITY),
            peak_trade_owned_resulting_current_position_qty="1",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T18:45:00Z",
            capture_started_at="2026-09-07T18:45:01Z",
            attempt_identity="code-gap-authorized-offline-seam-attempt",
            input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
            lifecycle_id="code-gap-authorized-offline-seam-lifecycle",
            lifecycle_event=REQUIRED_CAPTURE_TRIGGER,
            field_provenance=build_contemporaneous_field_provenance_from_bound_fill_v1(
                bound_fill_identity=_SEAM_IDENTITY,
                peak_trade_owned_resulting_current_position_qty="1",
                lifecycle_id="code-gap-authorized-offline-seam-lifecycle",
                input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
            ),
            runtime_execution_authorized=True,
        )
    if seam_result.get("CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED") is not True:
        raise Section1114OfflineSurfaceError("AUTHORIZED_OFFLINE_SEAM_MUST_COMMIT")
    if seam_result.get("LIVE_ENABLED") is True or seam_result.get("WIRE_SEND") is True:
        raise Section1114OfflineSurfaceError("SEAM_MUST_NOT_WIRE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_CALLER_SEMANTICS_V1",
        "CAPTURE_CALLER": CAPTURE_CALLER,
        "CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "CAPTURE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "CAPTURE_CALLER_ACCEPTS_HISTORICAL_FILL": False,
        "CAPTURE_CALLER_ACCEPTS_FIXTURE_FILL": False,
        "CAPTURE_CALLER_ACCEPTS_SYNTHETIC_FILL": False,
        "DEFAULT_PRODUCTIVE_INPUT_ERROR": default_error,
        "AUTHORIZED_FIXTURE_ERROR": fixture_error,
        "AUTHORIZED_HISTORICAL_ERROR": historical_error,
        "INVOCATION_SCOPED_SEAM_PROVEN": True,
        "INVOCATION_SCOPED_SEAM_IS_NOT_LIVE_CAPTURE": True,
        "STANDING_RUNTIME_EXECUTION_AUTHORIZED": False,
        "fixture_rejection": fixture_rejection,
        "historical_rejection": historical_rejection,
    }


def prove_code_gap_and_repair_v1(*, storage_root: Path) -> dict[str, Any]:
    semantics = prove_capture_caller_semantics_v1(storage_root=storage_root)
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CODE_GAP_AND_REPAIR_V1",
        "CODE_CHANGE_REQUIRED": True,
        "CODE_GAP_ID": CODE_GAP_ID,
        "CODE_GAP_PROOF": (
            "run_capture_hook_after_bound_fill_before_restart_v1 default refuses "
            "PRODUCTIVE_BOUND_FILL_INPUT with RUNTIME_EXECUTION_UNAUTHORIZED. "
            "Standing SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED remains false. "
            "This GO is not a gate bypass and does not mutate standing Live flags."
        ),
        "REPAIR": (
            "invocation-scoped runtime_execution_authorized default false; "
            "productive input allowed only when the flag is true; fixture and "
            "historical evidence remain rejected"
        ),
        "REPAIR_LIVE_EXECUTED": False,
        "REPAIR_DOES_NOT_AUTHORIZE_SUBMIT": True,
        "REPAIR_DOES_NOT_AUTHORIZE_MERGE": True,
        "semantics": semantics,
    }


def bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    store = storage_root or (root / "durable_state")
    producer = prove_fill_producer_call_path_v1(repo_root=root, storage_root=store)
    if (
        producer["LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER"]
        != LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER
    ):
        raise Section1114OfflineSurfaceError("FILL_PRODUCER_DRIFT")
    matrix = census_contemporaneous_live_fill_readiness_matrix_v1()
    economic = bind_minimal_economic_action_contract_v1()
    gap = prove_code_gap_and_repair_v1(storage_root=store)
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if matrix["LIVE_FILL_READINESS"] is True:
        raise Section1114OfflineSurfaceError("READINESS_MUST_REMAIN_FALSE")
    if economic["EXACT_ECONOMIC_ACTION_CONTRACT_STATUS"] != "BLOCKED":
        raise Section1114OfflineSurfaceError("ECONOMIC_CONTRACT_MUST_REMAIN_BLOCKED")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_"
            "THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "TERMINAL_STATE": TERMINAL_STATE,
        "OWNER_GO_SCOPE_MATCH": OWNER_GO == FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER": LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN": True,
        "CAPTURE_CALLER": CAPTURE_CALLER,
        "CAPTURE_CALLER_ACCEPTS_HISTORICAL_FILL": False,
        "CAPTURE_CALLER_ACCEPTS_FIXTURE_FILL": False,
        "CAPTURE_CALLER_ACCEPTS_SYNTHETIC_FILL": False,
        "CODE_CHANGE_REQUIRED": True,
        "LIVE_FILL_READINESS_MATRIX_STATUS": "COMPLETE",
        "LIVE_FILL_READINESS": False,
        "BLOCKING_GATE_COUNT": matrix["BLOCKING_GATE_COUNT"],
        "BLOCKING_GATES": list(matrix["BLOCKING_GATES"]),
        "EXACT_ECONOMIC_ACTION_CONTRACT_STATUS": "BLOCKED",
        "VENUE": economic["VENUE"],
        "INSTRUMENT_ID": economic["INSTRUMENT_ID"],
        "SIDE": economic["SIDE"],
        "ORDER_TYPE": economic["ORDER_TYPE"],
        "ORDER_QTY": economic["ORDER_QTY"],
        "EXECUTION_LIMIT_PRICE": "UNKNOWN",
        "EXECUTION_MAX_NOTIONAL": "UNKNOWN",
        "EXECUTION_MAX_POSITIONS": POSITION_COUNT_LIMIT,
        "LIVE_FILL_EXECUTION_AUTHORIZED": False,
        "LIVE_FILL_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "RESTART_EXECUTED": False,
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "NEXT_SLICE_AUTHORIZED": False,
        "producer": producer,
        "readiness_matrix": matrix,
        "economic_contract": economic,
        "code_gap": gap,
        "non_execution": {
            "DOCUMENT_CLASS": "SECTION_11_14_NON_EXECUTION_V1",
            "LIVE_SUBMIT_EXECUTED": False,
            "WIRE_SEND_EXECUTED": False,
            "POSITION_MUTATION_EXECUTED": False,
            "GET_PERFORMED": False,
            "POST_USED": False,
            "RESTART_EXECUTED": False,
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        },
    }
