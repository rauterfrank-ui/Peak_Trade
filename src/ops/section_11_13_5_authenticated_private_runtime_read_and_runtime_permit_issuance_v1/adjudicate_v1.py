"""Adjudicate authenticated private runtime read and runtime permit issuance."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    APT_CLOSED,
    CENSUS_CLOSED,
    CENSUS_RUNTIME_RESIDUAL,
    CENSUS_TEXT_REWRITTEN_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
    NAMED_REMAINING_HIGHER_AUTHORITY,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    NEXT_WORKPACKAGE,
    OWNER_GO,
    P08_CLOSED,
    P16_CLOSED,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    STPR_CLOSED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_COUNT,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.contract_v1 import (
    AuthenticatedPrivateRuntimeReadContractError,
    assert_live_authorized_cannot_substitute_v1,
    assert_productive_boundary_not_crossed_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.gap_adjudication_v1 import (
    adjudicate_gaps_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.lineage_v1 import (
    authenticated_private_runtime_read_lineage_v1,
    lineage_summary_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)


class AuthenticatedPrivateRuntimeReadAdjudicationError(RuntimeError):
    """Fail-closed adjudication violation."""


def adjudicate_authenticated_private_runtime_read_and_permit_issuance_v1(
    *,
    origin_main_sha: str,
    runtime_facts: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise AuthenticatedPrivateRuntimeReadAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_live_authorized_cannot_substitute_v1(
        live_authorized_claim=bool(runtime_facts.get("LIVE_AUTHORIZED"))
    )
    assert_productive_boundary_not_crossed_v1(runtime_facts)
    if LIVE_AUTHORIZED is True or LIVE_ENABLED is True or LIVE_ARMED is True:
        raise AuthenticatedPrivateRuntimeReadContractError("STANDING_LIVE_FLAG_TRUE")
    if runtime_facts.get("POST_PERFORMED") is True:
        raise AuthenticatedPrivateRuntimeReadAdjudicationError("POST_PERFORMED")
    if runtime_facts.get("NETWORK_SESSION_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadAdjudicationError("FLATTEN_SESSION_AUTHORIZED")

    gaps = adjudicate_gaps_v1(runtime_facts=runtime_facts)
    lineage = authenticated_private_runtime_read_lineage_v1(runtime_facts=runtime_facts)
    census = lineage_summary_v1(runtime_facts=runtime_facts)
    permit_audit = dict(runtime_facts.get("PERMIT_AUDIT") or {})
    observation = dict(runtime_facts.get("OBSERVATION") or {})
    freshness = dict(runtime_facts.get("FRESHNESS") or {})
    issued = permit_audit.get("issued") is True
    get_performed = runtime_facts.get("GET_PERFORMED_THIS_PERSIST") is True
    return {
        "DOCUMENT_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_PERMIT_ISSUANCE_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_WIRE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "P08_CLOSED": P08_CLOSED,
        "P16_CLOSED": P16_CLOSED,
        "STPR_CLOSED": STPR_CLOSED,
        "APT_CLOSED": APT_CLOSED,
        "CENSUS_CLOSED": CENSUS_CLOSED,
        "CENSUS_TEXT_REWRITTEN": CENSUS_TEXT_REWRITTEN_VALUE,
        "AUTHENTICATED_PRIVATE_RUNTIME_READ": (
            "PASS_RUNTIME" if get_performed else "FAIL_CLOSED_GET_NOT_PERFORMED"
        ),
        "RUNTIME_PERMIT_ISSUANCE": "PASS_RUNTIME_ISSUED" if issued else "FAIL_CLOSED",
        "RUNTIME_PERMIT_ISSUED": issued,
        "PERMIT_ISSUANCE_ATTEMPTED": True,
        "PERMIT_ISSUANCE_RESULT": "PASS" if issued else "FAIL_CLOSED",
        "PERMIT_ID_OR_HASH": permit_audit.get("permit_identity_sha256"),
        "PERMIT_DENY_REASONS": list(permit_audit.get("reasons") or []),
        "GET_PERFORMED_THIS_PERSIST": get_performed,
        "PRIVATE_AUTH_USED": runtime_facts.get("PRIVATE_AUTH_USED") is True,
        "CREDENTIAL_USE_PROVEN": runtime_facts.get("CREDENTIAL_USE_PROVEN") is True,
        "NETWORK_PROVEN": runtime_facts.get("NETWORK_PROVEN") is True,
        "PRIVATE_GET_PROVEN": get_performed,
        "POSITION_GET_USED": get_performed,
        "PUBLIC_GET_USED": False,
        "POST_PERFORMED": False,
        "POST_PROVEN": False,
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "PRODUCTIVE_FLATTEN_POST_AUTHORIZED": False,
        "PRODUCTIVE_RECONCILIATION_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "EMPTY_DATA_IS_ZERO": False,
        "POSITION_OBSERVATION_CLASS": observation.get("POSITION_OBSERVATION_CLASS"),
        "POSITION_OBSERVATION_FRESHNESS_ALLOWED": freshness.get("allowed"),
        "POSITION_OBSERVATION_FRESHNESS_AGE_MS": freshness.get("age_ms"),
        "POSITION_OBSERVATION_FRESHNESS_REJECT_REASON": freshness.get("reject_reason") or None,
        "G05_STATUS": gaps["G05_STATUS"],
        "G06_STATUS": gaps["G06_STATUS"],
        "G07_STATUS": gaps["G07_STATUS"],
        "G08_STATUS": gaps["G08_STATUS"],
        "GAPS": gaps["GAPS"],
        "REMAINING_GAP_COUNT": gaps["REMAINING_GAP_COUNT"],
        "REMAINING_RUNTIME_GAPS": gaps["REMAINING_RUNTIME_GAPS"],
        "REMAINING_EXTERNAL_STATE_GAPS": gaps["REMAINING_EXTERNAL_STATE_GAPS"],
        "REMAINING_OWNER_DECISIONS": gaps["REMAINING_OWNER_DECISIONS"],
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "NEXT_WORKPACKAGE": NEXT_WORKPACKAGE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "CENSUS_RUNTIME_RESIDUAL": CENSUS_RUNTIME_RESIDUAL,
        "NAMED_REMAINING_HIGHER_AUTHORITY": list(NAMED_REMAINING_HIGHER_AUTHORITY),
        "WORKPACKAGE_COUNT": WORKPACKAGE_COUNT,
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT": MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
        "CENSUS": census,
        "LINEAGE": list(lineage),
        "FAIL_CLOSED_STATUS": "PASS" if get_performed else "FAIL_CLOSED",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "EXECUTION_READY": False,
        "THIS_GO_GET_COUNT": int(runtime_facts.get("GET_REQUEST_COUNT") or 0),
        "THIS_GO_POST_COUNT": 0,
        "HTTP_STATUS": runtime_facts.get("HTTP_STATUS"),
        "OKX_CODE": runtime_facts.get("OKX_CODE"),
        "RESULT_CLASS": runtime_facts.get("RESULT_CLASS"),
        "GET_ERROR": runtime_facts.get("GET_ERROR"),
        "PARSE_ERROR": runtime_facts.get("PARSE_ERROR"),
    }
