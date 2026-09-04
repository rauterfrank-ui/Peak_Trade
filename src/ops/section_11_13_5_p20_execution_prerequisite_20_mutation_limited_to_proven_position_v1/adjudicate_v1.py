"""Offline EXECUTION_PREREQUISITE_20 adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.mutation_limited_to_proven_position_v1 import (
    REASON_INSTRUMENT_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MUTATION_BODY_MISSING,
    REASON_NO_PROVEN_POSITION,
    REASON_OVERSIZE,
    REASON_PARTIAL,
    REASON_SIDE_MISMATCH,
    REASON_ZERO_POSITION,
    evaluate_mutation_limited_to_proven_position_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.constants_v1 import (
    CASE_VALUE,
    CONFLICT_COUNT,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE,
    FLATTEN_QTY_RULE_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    MUTATION_OBJECT_VALUE,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P12_CLOSED,
    P13_CLOSED,
    P16_CLOSED,
    P16_TEXT_REWRITTEN_VALUE,
    P20_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    P20_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    P20_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    P20_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    P20_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    P20_MECHANISM_IMPLEMENTED,
    P20_NAMED_CONTRACT_CLOSED,
    P20_RUNTIME_RESIDUAL,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PREREQUISITE_20_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED_VALUE,
    PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN_VALUE,
    PRIVATE_AUTH_USED,
    PROVEN_POSITION_CLASSIFIER_VALUE,
    PROVEN_POSITION_STATE_VALUE,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.lineage_v1 import (
    lineage_census_summary_v1,
    mutation_limited_to_proven_position_lineage_v1,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "p20-offline-contract-decision"
WRONG_INSTRUMENT_ID = "BTC-USD_UM_XPERP-000000"


class P20MutationLimitedToProvenPositionAdjudicationError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_20 adjudication violation."""


def _positions(*, pos: str = "1", inst_id: str = TARGET_INSTRUMENT_ID) -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": inst_id, "pos": pos}]}


def _empty() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _pending() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="0.8209",
        ask="0.8210",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        tick_sz="0.0001",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _gate(**overrides: Any) -> FlattenPreSendGateInputV1:
    permit = overrides.pop(
        "bounded_activation_permit",
        offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            instrument_id=TARGET_INSTRUMENT_ID,
        ),
    )
    payload: dict[str, Any] = {
        "live_authorized": False,
        "live_enabled": True,
        "live_armed": True,
        "flatten_live_wire_enabled": True,
        "allow_productive_wire_send": True,
        "flatten_execute_token": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "flatten_execute_purpose": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "flatten_execute_owner_go": FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "positions_payload": _positions(),
        "pending_orders_payload": _pending(),
        "price_input": _price(),
        "owner_go": "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "flatten_execute_bound_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "instrument_id": TARGET_INSTRUMENT_ID,
        "one_shot_no_retry": True,
        "duplicate_post_protection": True,
        "flatten_pre_send_decision_id": DECISION_ID,
        "position_observation_freshness_evidence": PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id=DECISION_ID,
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        "monotonic_ms_clock": (lambda: 0),
        "bounded_activation_permit": permit,
    }
    payload.update(overrides)
    return FlattenPreSendGateInputV1(**payload)


def _matching_body() -> dict[str, Any]:
    return {
        "clOrdId": "pt20offline0000000000000001",
        "instId": TARGET_INSTRUMENT_ID,
        "side": "SELL",
        "ordType": "limit",
        "sz": "1",
        "tdMode": "cross",
        "px": "0.8209",
        "reduceOnly": True,
    }


def adjudicate_execution_prerequisite_20_mutation_limited_to_proven_position_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P20MutationLimitedToProvenPositionAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise P20MutationLimitedToProvenPositionAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE"
        )
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE"
        )
    missing_ok, missing_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_empty(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body=_matching_body(),
    )
    if missing_ok or REASON_NO_PROVEN_POSITION not in missing_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("NO_PROVEN_POSITION_MUST_DENY")
    zero_ok, zero_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(pos="0"),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body=_matching_body(),
    )
    if zero_ok or REASON_ZERO_POSITION not in zero_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("ZERO_POSITION_MUST_DENY")
    none_ok, none_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body=None,
    )
    if none_ok or REASON_MUTATION_BODY_MISSING not in none_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("MISSING_MUTATION_BODY_MUST_DENY")
    wrong_inst_ok, wrong_inst_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body={**_matching_body(), "instId": WRONG_INSTRUMENT_ID},
    )
    if wrong_inst_ok or REASON_INSTRUMENT_MISMATCH not in wrong_inst_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("WRONG_INSTRUMENT_MUST_DENY")
    partial_ok, partial_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body={**_matching_body(), "sz": "0.5"},
    )
    if partial_ok or REASON_PARTIAL not in partial_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("PARTIAL_FLATTEN_MUST_DENY")
    oversize_ok, oversize_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body={**_matching_body(), "sz": "2"},
    )
    if oversize_ok or REASON_OVERSIZE not in oversize_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("OVERSIZE_FLATTEN_MUST_DENY")
    side_ok, side_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body={**_matching_body(), "side": "BUY"},
    )
    if side_ok or REASON_SIDE_MISMATCH not in side_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError("SIDE_MISMATCH_MUST_DENY")
    substitute_ok, substitute_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_empty(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body=None,
        live_authorized_claim=True,
    )
    if (
        substitute_ok
        or REASON_NO_PROVEN_POSITION not in substitute_reasons
        or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in substitute_reasons
    ):
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY"
        )
    matching_ok, matching_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload=_positions(),
        instrument_id=TARGET_INSTRUMENT_ID,
        mutation_body=_matching_body(),
    )
    if matching_ok is not True or matching_reasons:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            f"MATCHING_MUTATION_MUST_PASS:{matching_reasons}"
        )
    empty_gate = evaluate_flatten_pre_send_gate_v1(_gate(positions_payload=_empty()))
    if empty_gate.allowed is True:
        raise P20MutationLimitedToProvenPositionAdjudicationError("EMPTY_POSITION_GATE_MUST_DENY")
    p20_empty = [
        item
        for item in empty_gate.audit_decisions
        if item[0] == "MUTATION_LIMITED_TO_PROVEN_POSITION"
    ]
    if not p20_empty or not str(p20_empty[0][1]).startswith("DENY:"):
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "EMPTY_POSITION_P20_GATE_MUST_DENY"
        )
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    p20_pass = [
        item
        for item in reachable.audit_decisions
        if item[0] == "MUTATION_LIMITED_TO_PROVEN_POSITION"
    ]
    if not p20_pass or p20_pass[0][1] != "PASS":
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "MATCHING_FIXTURE_P20_GATE_MUST_PASS"
        )
    transport = GatedProductiveFlattenTransportV1()
    if transport.network_session_authorized is not False:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "NETWORK_SESSION_DEFAULT_NOT_FALSE"
        )
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    if window.get("EARLIEST_UNRESOLVED_DEPENDENCY") != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise P20MutationLimitedToProvenPositionAdjudicationError(
            "WINDOW_EARLIEST_DEPENDENCY_DRIFT"
        )
    lineage = mutation_limited_to_proven_position_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P20MutationLimitedToProvenPositionAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION": (
            EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION
        ),
        "P20_NAMED_MUTATION_LIMITED_TO_PROVEN_POSITION_CONTRACT_CLOSED": P20_NAMED_CONTRACT_CLOSED,
        "P20_MUTATION_SCOPE_GATE_IMPLEMENTED": P20_MECHANISM_IMPLEMENTED,
        "PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN": (
            PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN_VALUE
        ),
        "PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED": (
            PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED_VALUE
        ),
        "PREREQUISITE_20_FLATTEN_EXECUTE_AUTHORIZED": (
            PREREQUISITE_20_FLATTEN_EXECUTE_AUTHORIZED_VALUE
        ),
        "PROVEN_POSITION_CLASSIFIER": PROVEN_POSITION_CLASSIFIER_VALUE,
        "PROVEN_POSITION_STATE": PROVEN_POSITION_STATE_VALUE,
        "MUTATION_OBJECT": MUTATION_OBJECT_VALUE,
        "FLATTEN_QTY_RULE": FLATTEN_QTY_RULE_VALUE,
        "OFFLINE_CONTRACT_PROOF_POSITION_CLASS": (
            "OFFLINE_CONTRACT_REGRESSION_FIXTURE_NOT_SEND_TIME_POSITION"
        ),
        "STRUCTURAL_ALLOW_IS_NOT_RUNTIME_MUTATION": True,
        "STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND": True,
        "FAIL_CLOSED_STATUS": "PASS",
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_CLOSED": P11_CLOSED,
        "P12_CLOSED": P12_CLOSED,
        "P13_CLOSED": P13_CLOSED,
        "P16_CLOSED": P16_CLOSED,
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "P20_RUNTIME_RESIDUAL": P20_RUNTIME_RESIDUAL,
        "P20_DOES_NOT_GRANT_EXECUTION_READINESS": P20_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "P20_DOES_NOT_AUTHORIZE_FLATTEN": P20_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "P20_DOES_NOT_SET_LIVE_AUTHORIZED": P20_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "P20_DOES_NOT_ISSUE_RUNTIME_PERMIT": P20_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "P20_DOES_NOT_AUTHORIZE_NETWORK_SESSION": P20_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "FAIL_CLOSED_IF_PREREQUISITE_20_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE
        ),
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "NETWORK_SESSION_AUTHORIZED_DEFAULT": False,
        "IMPLEMENTATION_GO_FORBIDDEN_AS_FLATTEN_EXECUTE": True,
        "NO_PROVEN_POSITION_DENIES": True,
        "ZERO_POSITION_DENIES": True,
        "MISSING_MUTATION_BODY_DENIES": True,
        "WRONG_INSTRUMENT_DENIES": True,
        "PARTIAL_FLATTEN_DENIES": True,
        "OVERSIZE_FLATTEN_DENIES": True,
        "SIDE_MISMATCH_DENIES": True,
        "GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES": True,
        "LINEAGE": lineage,
        "CENSUS": census,
        "WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY": window.get("EARLIEST_UNRESOLVED_DEPENDENCY"),
    }
