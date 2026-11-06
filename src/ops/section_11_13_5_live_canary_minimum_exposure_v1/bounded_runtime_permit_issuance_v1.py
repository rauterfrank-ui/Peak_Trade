"""CASE_B issuance contract for BOUNDED_RUNTIME_PERMIT_ISSUANCE.

Closes the named residual as an offline issuance-contract persist. Does not
issue a runtime BoundedActivationPermitV1. Does not GET, POST, flatten, or
open a network session. Implementation Owner-GOs cannot satisfy issuance.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    BOUNDED_ACTIVATION_OWNER_GO_CANONICAL,
    evaluate_bounded_activation_permit_v1,
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    PASS_OFFLINE_CONTRACT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.remaining_execution_path_census_v1 import (
    CENSUS_IMPLEMENTATION_OWNER_GO,
    NAMED_REMAINING_AFTER_CENSUS,
    NAMED_REMAINING_AFTER_CENSUS_SET,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
)

BRPI_IMPLEMENTATION_OWNER_GO = CENSUS_IMPLEMENTATION_OWNER_GO
NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE = NAMED_REMAINING_AFTER_CENSUS
NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE_SET = NAMED_REMAINING_AFTER_CENSUS_SET

REASON_STPR_NOT_PASS = "STPR_NOT_PASS_OFFLINE_CONTRACT"
REASON_MISSING_STPR = "STPR_STATUS_MISSING"
REASON_MISSING_REMAINING = "REMAINING_AFTER_CENSUS_SET_MISSING"
REASON_REMAINING_MISMATCH = "REMAINING_AFTER_CENSUS_SET_MISMATCH"
REASON_STPR_REMAINING_DRIFT = "STPR_NAMED_REMAINING_MUST_STAY_FROZEN"
REASON_RUNTIME_ISSUANCE_CLAIM = "RUNTIME_PERMIT_ISSUANCE_CLAIMED"
REASON_FLATTEN_EXECUTE = "FLATTEN_EXECUTE_CLAIMED"
REASON_NETWORK_SESSION = "NETWORK_SESSION_CLAIMED"
REASON_POST = "POST_CLAIMED"
REASON_GET = "GET_CLAIMED"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE"
REASON_IMPLEMENTATION_GO_AS_EXECUTE = "IMPLEMENTATION_GO_FORBIDDEN_AS_FLATTEN_EXECUTE"
REASON_IMPLEMENTATION_GO_AS_PERMIT = "IMPLEMENTATION_GO_FORBIDDEN_AS_RUNTIME_PERMIT"
REASON_PERMIT_SCHEMA = "BOUNDED_ACTIVATION_PERMIT_SCHEMA_DENIED"


def _remaining_set(claimed: Iterable[str] | None) -> set[str] | None:
    if claimed is None:
        return None
    return {str(item).strip() for item in claimed if str(item).strip()}


def evaluate_bounded_runtime_permit_issuance_v1(
    *,
    stpr_status: str | None,
    claimed_remaining_after_census: Sequence[str] | None,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    live_authorized_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    permit_owner_go: str | None = None,
    origin_main_sha: str | None = None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    evaluation_monotonic_ms: int = 0,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never issues a runtime permit."""
    reasons: list[str] = []
    status = None if stpr_status is None else str(stpr_status).strip()
    if not status:
        reasons.append(REASON_MISSING_STPR)
    elif status != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_STPR_NOT_PASS)

    frozen_stpr = set(NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION)
    if frozen_stpr != {"BOUNDED_RUNTIME_PERMIT_ISSUANCE", "FLATTEN_EXECUTE", "NETWORK_SESSION"}:
        reasons.append(REASON_STPR_REMAINING_DRIFT)

    remaining = _remaining_set(claimed_remaining_after_census)
    if remaining is None:
        reasons.append(REASON_MISSING_REMAINING)
    elif remaining != NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE_SET:
        reasons.append(REASON_REMAINING_MISMATCH)

    if runtime_permit_issuance_claim is True:
        reasons.append(REASON_RUNTIME_ISSUANCE_CLAIM)
    if flatten_execute_authorized_claim is True:
        reasons.append(REASON_FLATTEN_EXECUTE)
    if network_session_authorized_claim is True:
        reasons.append(REASON_NETWORK_SESSION)
    if post_performed_claim is True:
        reasons.append(REASON_POST)
    if get_performed_claim is True:
        reasons.append(REASON_GET)
    if live_authorized_claim is True:
        reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)

    go = str(flatten_execute_owner_go or "").strip()
    if go:
        execute_ok, execute_reasons = evaluate_flatten_execute_authority_v1(
            token=None,
            purpose=None,
            owner_go=go,
        )
        if execute_ok or "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in execute_reasons:
            if go == BRPI_IMPLEMENTATION_OWNER_GO or go in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
                reasons.append(REASON_IMPLEMENTATION_GO_AS_EXECUTE)

    permit_go = str(permit_owner_go or "").strip()
    if permit_go and (
        permit_go == BRPI_IMPLEMENTATION_OWNER_GO
        or permit_go in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    ):
        reasons.append(REASON_IMPLEMENTATION_GO_AS_PERMIT)

    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha:
        fixture = offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=bound_sha,
            instrument_id=instrument_id,
        )
        if fixture.owner_go != BOUNDED_ACTIVATION_OWNER_GO_CANONICAL:
            reasons.append(REASON_PERMIT_SCHEMA)
        else:
            accepted, permit_reasons = evaluate_bounded_activation_permit_v1(
                permit=fixture,
                origin_main_sha=bound_sha,
                instrument_id=instrument_id,
                evaluation_monotonic_ms=evaluation_monotonic_ms,
            )
            if not accepted:
                reasons.append(REASON_PERMIT_SCHEMA)
                reasons.extend(permit_reasons)

    return (not reasons, tuple(reasons))


def bounded_runtime_permit_issuance_audit_v1(
    *,
    stpr_status: str | None,
    claimed_remaining_after_census: Sequence[str] | None,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    live_authorized_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    permit_owner_go: str | None = None,
    origin_main_sha: str | None = None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    evaluation_monotonic_ms: int = 0,
) -> dict[str, Any]:
    accepted, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=stpr_status,
        claimed_remaining_after_census=claimed_remaining_after_census,
        runtime_permit_issuance_claim=runtime_permit_issuance_claim,
        flatten_execute_authorized_claim=flatten_execute_authorized_claim,
        network_session_authorized_claim=network_session_authorized_claim,
        post_performed_claim=post_performed_claim,
        get_performed_claim=get_performed_claim,
        live_authorized_claim=live_authorized_claim,
        flatten_execute_owner_go=flatten_execute_owner_go,
        permit_owner_go=permit_owner_go,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        evaluation_monotonic_ms=evaluation_monotonic_ms,
    )
    return {
        "kind": "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
        "accepted": accepted,
        "reasons": list(reasons),
        "runtime_issued": False,
        "implementation_go_is_not_runtime_permit": True,
        "named_remaining_after_census": list(NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE),
    }


def assert_runtime_permit_not_issued_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN") is True:
        raise RuntimeError("RUNTIME_PERMIT_ISSUANCE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise RuntimeError("RUNTIME_PERMIT_BOOLEAN_TRUE_FORBIDDEN")
    if payload.get("RUNTIME_PERMIT_ISSUED") is True:
        raise RuntimeError("RUNTIME_PERMIT_ISSUED_CLAIMED")
