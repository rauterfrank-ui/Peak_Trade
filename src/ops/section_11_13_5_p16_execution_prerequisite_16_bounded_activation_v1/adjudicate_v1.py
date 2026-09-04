"""Offline EXECUTION_PREREQUISITE_16 adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    BoundedActivationPermitV1,
    evaluate_bounded_activation_permit_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.constants_v1 import (
    BOUNDED_ACTIVATION_NARROWER_THAN_GLOBAL_LIVE_VALUE,
    BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
    BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
    BOUNDED_ACTIVATION_PURPOSE_VALUE,
    CASE_VALUE,
    CONFLICT_COUNT,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE,
    GLOBAL_LIVE_AUTHORIZED_REQUIRED_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P12_CLOSED,
    P13_CLOSED,
    P13_TEXT_REWRITTEN_VALUE,
    P16_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    P16_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    P16_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    P16_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    P16_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    P16_MECHANISM_IMPLEMENTED,
    P16_NAMED_CONTRACT_CLOSED,
    P16_RUNTIME_RESIDUAL,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN_VALUE,
    PREREQUISITE_16_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED_VALUE,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.lineage_v1 import (
    bounded_activation_lineage_v1,
    lineage_census_summary_v1,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "p16-offline-contract-decision"


class P16BoundedActivationAdjudicationError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_16 adjudication violation."""


def _positions() -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": TARGET_INSTRUMENT_ID, "pos": "1"}]}


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


def adjudicate_execution_prerequisite_16_bounded_activation_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P16BoundedActivationAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise P16BoundedActivationAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise P16BoundedActivationAdjudicationError("IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE")
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise P16BoundedActivationAdjudicationError("IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE")
    missing_ok, missing_reasons = evaluate_bounded_activation_permit_v1(
        permit=None,
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        evaluation_monotonic_ms=0,
    )
    if missing_ok or "BOUNDED_ACTIVATION_PERMIT_MISSING" not in missing_reasons:
        raise P16BoundedActivationAdjudicationError("MISSING_PERMIT_MUST_DENY")
    forbidden_permit = BoundedActivationPermitV1(
        kind=BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
        purpose=BOUNDED_ACTIVATION_PURPOSE_VALUE,
        owner_go=OWNER_GO,
        bound_origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        not_after_monotonic_ms=1_000_000,
    )
    forbidden_ok, forbidden_reasons = evaluate_bounded_activation_permit_v1(
        permit=forbidden_permit,
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        evaluation_monotonic_ms=0,
    )
    if forbidden_ok or "BOUNDED_ACTIVATION_OWNER_GO_FORBIDDEN" not in forbidden_reasons:
        raise P16BoundedActivationAdjudicationError("IMPLEMENTATION_GO_MUST_NOT_SATISFY_PERMIT")
    expired_permit = BoundedActivationPermitV1(
        kind=BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
        purpose=BOUNDED_ACTIVATION_PURPOSE_VALUE,
        owner_go=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
        bound_origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        not_after_monotonic_ms=0,
    )
    expired_ok, expired_reasons = evaluate_bounded_activation_permit_v1(
        permit=expired_permit,
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        evaluation_monotonic_ms=1,
    )
    if expired_ok or "BOUNDED_ACTIVATION_PERMIT_EXPIRED" not in expired_reasons:
        raise P16BoundedActivationAdjudicationError("EXPIRED_PERMIT_MUST_DENY")
    stale_permit = BoundedActivationPermitV1(
        kind=BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
        purpose=BOUNDED_ACTIVATION_PURPOSE_VALUE,
        owner_go=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
        bound_origin_main_sha="a" * 40,
        instrument_id=TARGET_INSTRUMENT_ID,
        not_after_monotonic_ms=1_000_000,
    )
    stale_ok, stale_reasons = evaluate_bounded_activation_permit_v1(
        permit=stale_permit,
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        evaluation_monotonic_ms=0,
    )
    if stale_ok or "BOUNDED_ACTIVATION_BOUND_SHA_STALE" not in stale_reasons:
        raise P16BoundedActivationAdjudicationError("STALE_PERMIT_MUST_DENY")
    substitute = evaluate_flatten_pre_send_gate_v1(_gate(live_authorized=True))
    if substitute.allowed is True:
        raise P16BoundedActivationAdjudicationError("LIVE_AUTHORIZED_TRUE_MUST_NOT_ALLOW")
    if "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_BOUNDED_PERMIT" not in substitute.reasons:
        raise P16BoundedActivationAdjudicationError("LIVE_AUTHORIZED_SUBSTITUTE_REASON_MISSING")
    missing_gate = evaluate_flatten_pre_send_gate_v1(_gate(bounded_activation_permit=None))
    if missing_gate.allowed is True:
        raise P16BoundedActivationAdjudicationError("MISSING_PERMIT_GATE_MUST_DENY")
    if "BOUNDED_ACTIVATION_PERMIT_MISSING" not in missing_gate.reasons:
        raise P16BoundedActivationAdjudicationError("MISSING_PERMIT_GATE_REASON_MISSING")
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise P16BoundedActivationAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    live_claim_pass = [
        item for item in reachable.audit_decisions if item[0] == "LIVE_AUTHORIZED_CLAIM"
    ]
    if not live_claim_pass or live_claim_pass[0][1] != "PASS":
        raise P16BoundedActivationAdjudicationError("LIVE_AUTHORIZED_FALSE_MUST_PASS_CLAIM_GATE")
    permit_pass = [
        item for item in reachable.audit_decisions if item[0] == "BOUNDED_ACTIVATION_PERMIT"
    ]
    if not permit_pass or permit_pass[0][1] != "PASS":
        raise P16BoundedActivationAdjudicationError("VALID_FIXTURE_PERMIT_MUST_PASS")
    transport = GatedProductiveFlattenTransportV1()
    if transport.network_session_authorized is not False:
        raise P16BoundedActivationAdjudicationError("NETWORK_SESSION_DEFAULT_NOT_FALSE")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    if window.get("EARLIEST_UNRESOLVED_DEPENDENCY") != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise P16BoundedActivationAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = bounded_activation_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P16BoundedActivationAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED": (
            EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED
        ),
        "P16_NAMED_WITHOUT_GLOBAL_LIVE_AUTHORIZED_CONTRACT_CLOSED": P16_NAMED_CONTRACT_CLOSED,
        "P16_BOUNDED_ACTIVATION_PERMIT_MECHANISM_IMPLEMENTED": P16_MECHANISM_IMPLEMENTED,
        "PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN": (
            PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN_VALUE
        ),
        "PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED": (
            PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED_VALUE
        ),
        "PREREQUISITE_16_FLATTEN_EXECUTE_AUTHORIZED": (
            PREREQUISITE_16_FLATTEN_EXECUTE_AUTHORIZED_VALUE
        ),
        "GLOBAL_LIVE_AUTHORIZED_REQUIRED": GLOBAL_LIVE_AUTHORIZED_REQUIRED_VALUE,
        "BOUNDED_ACTIVATION_NARROWER_THAN_GLOBAL_LIVE": (
            BOUNDED_ACTIVATION_NARROWER_THAN_GLOBAL_LIVE_VALUE
        ),
        "BOUNDED_ACTIVATION_PERMIT_KIND": BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
        "BOUNDED_ACTIVATION_PURPOSE": BOUNDED_ACTIVATION_PURPOSE_VALUE,
        "BOUNDED_ACTIVATION_OWNER_GO_CANONICAL": BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
        "STRUCTURAL_BOUNDED_PATH_ALLOWED_WITHOUT_LIVE_AUTHORIZED": True,
        "STRUCTURAL_ALLOW_IS_NOT_RUNTIME_ACTIVATION": True,
        "STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND": True,
        "OFFLINE_CONTRACT_PROOF_PERMIT_CLASS": (
            "OFFLINE_CONTRACT_REGRESSION_FIXTURE_NOT_PRODUCTIVE_RUNTIME_PERMIT"
        ),
        "FAIL_CLOSED_STATUS": "PASS",
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_CLOSED": P11_CLOSED,
        "P12_CLOSED": P12_CLOSED,
        "P13_CLOSED": P13_CLOSED,
        "P13_TEXT_REWRITTEN": P13_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "P16_RUNTIME_RESIDUAL": P16_RUNTIME_RESIDUAL,
        "P16_DOES_NOT_GRANT_EXECUTION_READINESS": P16_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "P16_DOES_NOT_AUTHORIZE_FLATTEN": P16_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "P16_DOES_NOT_SET_LIVE_AUTHORIZED": P16_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "P16_DOES_NOT_ISSUE_RUNTIME_PERMIT": P16_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "P16_DOES_NOT_AUTHORIZE_NETWORK_SESSION": P16_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "FAIL_CLOSED_IF_PREREQUISITE_16_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE": (
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
        "IMPLEMENTATION_GO_FORBIDDEN_AS_BOUNDED_PERMIT": True,
        "MISSING_PERMIT_DENIES": True,
        "EXPIRED_PERMIT_DENIES": True,
        "STALE_BOUND_PERMIT_DENIES": True,
        "GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES": True,
        "LINEAGE": lineage,
        "CENSUS": census,
        "WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY": window.get("EARLIEST_UNRESOLVED_DEPENDENCY"),
    }
