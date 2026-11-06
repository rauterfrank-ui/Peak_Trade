"""Canonical P08 TARGET_POSITION_NONZERO_PROVEN closure-condition proof.

Binds the observation that would satisfy Prerequisite 08 to existing
producers, tests, and evidence. Never GETs. Never POSTs. Never closes P08
from empty, absent, zero, historical, or fixture payloads.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    RESULT_CLASS_200_OKX_0,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_position_observation_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    ABSENT_TARGET_ROW_IS_ZERO,
    AUTHORIZED_HOST,
    EMPTY_DATA_IS_ZERO,
    P08_AUTHORIZED_RESOLUTION_PATH,
    P08_CANONICAL_ENDPOINT,
    P08_CANONICAL_PRODUCER,
    P08_DEFINITION,
    P08_REQUIRED_PROPOSITION,
    TARGET_INSTRUMENT_ID,
    TARGET_INST_TYPE,
)


class P08ClosureConditionError(RuntimeError):
    """Fail-closed closure-condition proof violation."""


FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "HTTP_STATUS_NOT_200",
    "OKX_CODE_NOT_0",
    "TRANSPORT_OR_CLIENT_FAIL",
    "FILTERED_INSTID_GET_IS_NOT_08_RESOLUTION_PATH",
    "EMPTY_DATA_IS_NOT_ZERO",
    "ABSENT_TARGET_ROW_IS_NOT_ZERO",
    "ZERO_ROW_DOES_NOT_CLOSE_P08",
    "AMBIGUOUS_TARGET_POSITION_ROWS",
    "NON_TARGET_INSTRUMENT_ROW",
    "HISTORICAL_EMPTY_ENVELOPE_IS_NOT_CURRENT_08_PROOF",
    "FIXTURE_NONZERO_IS_NOT_PRODUCTIVE_08_PROOF",
    "IDENTIFIER_CHANNEL_IS_NOT_CANONICAL_P08_AUTHORITY",
    "POS_UNPARSEABLE_OR_MISSING",
    "QUERY_COMPLETENESS_NOT_PROVEN_BY_HTTP_OK",
)


def prove_p08_closure_condition_v1(
    *,
    positions_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the bound closure condition. Not a GET and not P08 closed."""
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if classified.state == TARGET_POSITION_NONZERO_PROVEN:
        raise P08ClosureConditionError("FORBIDDEN_PRODUCTIVE_NONZERO_CLAIM_ON_OFFLINE_PROOF")
    observation = classify_position_observation_v1(
        result_class=RESULT_CLASS_200_OKX_0
        if positions_payload is not None
        else "TRANSPORT_OR_CLIENT_FAIL",
        payload=positions_payload,
        window={
            "classifier_state": classified.state,
            "classifier_reason": classified.reason,
            "TARGET_POSITION_QTY_NUMERIC": "",
        }
        if positions_payload is not None
        else None,
    )
    if observation.get("P08_CLOSED") is True:
        raise P08ClosureConditionError("FORBIDDEN_P08_CLOSED_CLAIM")
    if observation.get("TARGET_POSITION_NONZERO_PROVEN") is True:
        raise P08ClosureConditionError("FORBIDDEN_NONZERO_PROVEN_CLAIM")
    return {
        "P08_CLOSURE_CONDITION_STATUS": "PROVEN",
        "P08_REQUIRED_PROPOSITION": P08_REQUIRED_PROPOSITION,
        "P08_CANONICAL_DEFINITION": P08_DEFINITION,
        "AUTHORITATIVE_PRODUCER": P08_CANONICAL_PRODUCER,
        "AUTHORITATIVE_ENDPOINT": P08_CANONICAL_ENDPOINT,
        "AUTHORITATIVE_HOST": AUTHORIZED_HOST,
        "AUTHORIZED_RESOLUTION_PATH": P08_AUTHORIZED_RESOLUTION_PATH,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_INST_TYPE": TARGET_INST_TYPE,
        "TARGET_INSTRUMENT_IDENTITY_REQUIREMENT": (
            "EXACTLY_ONE_ROW_WITH_INSTID_EQUAL_TO_BOUND_TARGET"
        ),
        "QUANTITY_NONZERO_SEMANTICS": (
            "UNIQUE_TARGET_ROW_POS_OR_POSSIZE_PARSEABLE_AND_SIGNED_NONZERO"
        ),
        "ADDITIONAL_FIELD_PREDICATES_REQUIRED": False,
        "UNFILTERED_ACCOUNT_POSITIONS_TARGET_ROW_SUFFICIENT": True,
        "FILTERED_INSTID_GET_SUFFICIENT": False,
        "IDENTIFIER_CHANNEL_SUFFICIENT": False,
        "ROW_MAY_ARISE_BY_EXTERNAL_OR_PREEXISTING_OR_PEAK_TRADE_CREATE": True,
        "ROW_MUST_BE_GENERATED_BY_PEAK_TRADE": False,
        "ACCOUNT_REQUIREMENT": "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY_ON_EEA_OKX",
        "POSITION_MODE_REQUIREMENT_FOR_OBSERVATION": "NONE_OBSERVATION_IS_SOURCE_IRRELEVANT",
        "FRESHNESS_REQUIREMENT": (
            "THIS_WINDOW_UNFILTERED_GET_ONLY;FLATTEN_PRE_SEND_MAX_AGE_MS=5000;"
            "HISTORICAL_EMPTY_IS_NOT_CURRENT_08_PROOF"
        ),
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "ABSENT_TARGET_ROW_IS_ZERO": ABSENT_TARGET_ROW_IS_ZERO,
        "ZERO_ROW_CLOSES_P08": False,
        "FAIL_CLOSED_CONDITIONS": list(FAIL_CLOSED_CONDITIONS),
        "classifier_state": classified.state,
        "classifier_reason": classified.reason,
        "POSITION_OBSERVATION_CLASS": observation.get("POSITION_OBSERVATION_CLASS"),
        "P08_CLOSED": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "TARGET_POSITION_ZERO_PROVEN": classified.state == TARGET_POSITION_ZERO_PROVEN,
        "TARGET_POSITION_NOT_OBSERVED": classified.state == TARGET_POSITION_NOT_OBSERVED,
        "CASE_A_IS_THE_ONLY_P08_CLOSE": CASE_A_TARGET_NONZERO,
        "CASE_B_DOES_NOT_CLOSE_P08": CASE_B_TARGET_ZERO,
        "CASE_C_DOES_NOT_CLOSE_P08": CASE_C_EMPTY_DATA_NOT_ZERO,
    }
