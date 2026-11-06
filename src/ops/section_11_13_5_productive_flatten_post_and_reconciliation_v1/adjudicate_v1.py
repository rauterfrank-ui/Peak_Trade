"""Adjudicate productive flatten POST and reconciliation."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    APRPI_CLOSED,
    CENSUS_CLOSED,
    CENSUS_RUNTIME_RESIDUAL,
    CENSUS_TEXT_REWRITTEN,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO_VALUE,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
    NAMED_REMAINING_HIGHER_AUTHORITY,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    NEXT_WORKPACKAGE,
    OWNER_GO,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    RETRY_ALLOWED_VALUE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_COUNT,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.contract_v1 import (
    ProductiveFlattenPostContractError,
    assert_live_authorized_cannot_substitute_v1,
    assert_no_retry_v1,
    assert_payload_not_live_unlock_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.gap_adjudication_v1 import (
    adjudicate_gaps_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.lineage_v1 import (
    lineage_summary_v1,
    productive_flatten_post_lineage_v1,
)


class ProductiveFlattenPostAdjudicationError(RuntimeError):
    """Fail-closed productive flatten adjudication violation."""


def adjudicate_productive_flatten_post_and_reconciliation_v1(
    *,
    origin_main_sha: str,
    runtime_facts: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveFlattenPostAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_live_authorized_cannot_substitute_v1(
        live_authorized_claim=bool(runtime_facts.get("LIVE_AUTHORIZED"))
    )
    assert_payload_not_live_unlock_v1(runtime_facts)
    assert_no_retry_v1(retry_used=bool(runtime_facts.get("RETRY_USED")))
    if LIVE_AUTHORIZED is True or LIVE_ENABLED is True or LIVE_ARMED is True:
        raise ProductiveFlattenPostContractError("STANDING_LIVE_FLAG_TRUE")
    if runtime_facts.get("RETRY_USED") is True:
        raise ProductiveFlattenPostAdjudicationError("RETRY_USED")
    if runtime_facts.get("FUNDING_USED") is True:
        raise ProductiveFlattenPostAdjudicationError("FUNDING_USED")

    gaps = adjudicate_gaps_v1(runtime_facts=runtime_facts)
    lineage = productive_flatten_post_lineage_v1(runtime_facts=runtime_facts)
    census = lineage_summary_v1(runtime_facts=runtime_facts)
    permit_audit = dict(runtime_facts.get("PERMIT_AUDIT") or {})
    observation = dict(runtime_facts.get("OBSERVATION") or {})
    post_observation = dict(runtime_facts.get("POST_OBSERVATION") or {})
    freshness = dict(runtime_facts.get("FRESHNESS") or {})
    post_used = runtime_facts.get("POST_USED") is True
    recon = runtime_facts.get("RECONCILIATION_ATTEMPTED") is True
    zero = runtime_facts.get("TARGET_POSITION_ZERO_PROVEN") is True
    proven = runtime_facts.get("LIVE_FLATTEN_PROVABILITY_PROVEN") is True
    return {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_WIRE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "APRPI_CLOSED": APRPI_CLOSED,
        "CENSUS_CLOSED": CENSUS_CLOSED,
        "CENSUS_TEXT_REWRITTEN": CENSUS_TEXT_REWRITTEN,
        "GET_PERFORMED_THIS_PERSIST": runtime_facts.get("GET_PERFORMED_THIS_PERSIST") is True,
        "PRIVATE_AUTH_USED": runtime_facts.get("PRIVATE_AUTH_USED") is True,
        "PRIVATE_GET_USED": runtime_facts.get("PRIVATE_GET_USED") is True,
        "POSITION_GET_USED": runtime_facts.get("POSITION_GET_USED") is True,
        "PUBLIC_GET_USED": runtime_facts.get("PUBLIC_GET_USED") is True,
        "POST_ATTEMPTED": runtime_facts.get("POST_ATTEMPTED") is True,
        "POST_USED": post_used,
        "POST_PERFORMED": post_used,
        "POST_RESULT": runtime_facts.get("POST_RESULT"),
        "ORDER_SUBMIT_USED": runtime_facts.get("ORDER_SUBMIT_USED") is True,
        "ORDER_ID_REDACTED": runtime_facts.get("ORDER_ID_REDACTED"),
        "PERMIT_VALIDATION_RESULT": runtime_facts.get("PERMIT_VALIDATION_RESULT"),
        "PERMIT_CONSUMED": runtime_facts.get("PERMIT_CONSUMED") is True,
        "PERMIT_ISSUED": permit_audit.get("issued") is True,
        "PERMIT_ID_OR_HASH": permit_audit.get("permit_identity_sha256"),
        "PRE_WIRE_POSITION_RESULT": runtime_facts.get("PRE_WIRE_POSITION_RESULT"),
        "PRE_WIRE_POSITION_FRESHNESS": runtime_facts.get("PRE_WIRE_POSITION_FRESHNESS") is True,
        "POSITION_OBSERVATION_CLASS": observation.get("POSITION_OBSERVATION_CLASS"),
        "POST_POSITION_OBSERVATION_CLASS": post_observation.get("POSITION_OBSERVATION_CLASS"),
        "POSITION_OBSERVATION_FRESHNESS_ALLOWED": freshness.get("allowed"),
        "RECONCILIATION_ATTEMPTED": recon,
        "RECONCILIATION_RESULT": (
            "PASS_RUNTIME" if recon else "NOT_ATTEMPTED_BECAUSE_POST_NOT_USED"
        ),
        "TARGET_POSITION_ZERO_PROVEN": zero,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": proven,
        "RETRY_USED": False,
        "RETRY_AUTHORITY_PROVEN": False,
        "RETRY_ALLOWED": RETRY_ALLOWED_VALUE,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO_VALUE,
        "FUNDING_USED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "STANDING_LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "NETWORK_SESSION_INSTANCE_AUTHORIZED": (
            runtime_facts.get("NETWORK_SESSION_INSTANCE_AUTHORIZED") is True
        ),
        "FLATTEN_EXECUTE_INVOCATION_USED": (
            runtime_facts.get("FLATTEN_EXECUTE_INVOCATION_USED") is True
        ),
        "FAIL_CLOSED_REASON": runtime_facts.get("FAIL_CLOSED_REASON"),
        "G09_STATUS": gaps["G09_STATUS"],
        "G10_STATUS": gaps["G10_STATUS"],
        "G11_STATUS": gaps["G11_STATUS"],
        "G12_STATUS": gaps["G12_STATUS"],
        "G13_STATUS": gaps["G13_STATUS"],
        "G14_STATUS": gaps["G14_STATUS"],
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
        "FAIL_CLOSED_STATUS": "PASS"
        if runtime_facts.get("GET_PERFORMED_THIS_PERSIST")
        else "FAIL_CLOSED",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "EXECUTION_READY": False,
        "THIS_GO_GET_COUNT": int(runtime_facts.get("GET_REQUEST_COUNT") or 0),
        "THIS_GO_POST_COUNT": int(runtime_facts.get("POST_COUNT") or 0),
        "VENUE_ACCEPTED_IS_NOT_FILL_PROVEN": True,
        "FILL_IS_NOT_POSITION_ZERO_PROVEN": True,
        "POSITION_ZERO_IS_NOT_FULL_RECONCILIATION_ALONE": True,
    }
