"""Offline CASE_A adjudication of the already-captured P08 GET. No GET. No POST."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    classify_target_position_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    qty_numeric_status_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    bind_captured_envelope_v1,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.constants_v1 import (
    ACTUAL_GET_COUNT,
    AUTHORIZED_ACCOUNT_UID,
    AUTHORIZED_CLASSIFIER_ID,
    AUTHORIZED_CLASSIFIER_REASON,
    AUTHORIZED_CLASSIFIER_STATE,
    AUTHORIZED_EMPTY_DATA_IS_ZERO,
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_GET_COUNT,
    AUTHORIZED_HOST,
    AUTHORIZED_QUERY_COMPLETENESS_PROVEN,
    AUTHORIZED_SIGNED_POS,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    G_POSMODE_SUBMIT_BODY_PROVEN,
    HTTP_STATUS,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OBSERVATION_CLASSIFIER_ID,
    OKX_CODE,
    ORIGINAL_WIRE_BODY_BYTES_AVAILABLE,
    OWNER_GO,
    P08_CANONICAL_CLOSE_DEFINITION,
    P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS,
    P08_CLOSED,
    P08_VERDICT,
    POSITION_OBSERVATION_CLASS,
    PRIOR_CAPTURE_OWNER_GO,
    QUERY,
    QUERY_COMPLETENESS_PROVEN_FALSE_DOES_NOT_INVALIDATE_OBSERVED_NONZERO_TARGET_ROW,
    RESULT_CLASS,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
    THIS_GO_GET_COUNT,
    THIS_GO_POST_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_position_observation_v1,
)


class P08NonzeroAdjudicationError(RuntimeError):
    """Fail-closed CASE_A adjudication violation."""


def reconstructed_captured_json_sha256_v1(payload: Mapping[str, Any]) -> str:
    text = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def adjudicate_captured_nonzero_position_v1(
    *,
    origin_main_sha: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08NonzeroAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    envelope = captured_envelope_v1() if payload is None else bind_captured_envelope_v1(payload)
    classified = classify_target_position_state_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if classified.state != AUTHORIZED_CLASSIFIER_STATE:
        raise P08NonzeroAdjudicationError(f"CLASSIFIER_STATE_MISMATCH:{classified.state}")
    if classified.signed_pos != AUTHORIZED_SIGNED_POS:
        raise P08NonzeroAdjudicationError(f"SIGNED_POS_MISMATCH:{classified.signed_pos}")
    if classified.reason != AUTHORIZED_CLASSIFIER_REASON:
        raise P08NonzeroAdjudicationError(f"CLASSIFIER_REASON_MISMATCH:{classified.reason}")
    if classified.query_completeness_proven != AUTHORIZED_QUERY_COMPLETENESS_PROVEN:
        raise P08NonzeroAdjudicationError("QUERY_COMPLETENESS_PROVEN_MISMATCH")
    if classified.empty_data_is_zero != AUTHORIZED_EMPTY_DATA_IS_ZERO:
        raise P08NonzeroAdjudicationError("EMPTY_DATA_IS_ZERO_MISMATCH")
    if classified.empty_data_is_zero:
        raise P08NonzeroAdjudicationError("EMPTY_DATA_MUST_NOT_BE_ZERO")

    qty_numeric = qty_numeric_status_v1(
        classifier_state=classified.state,
        signed_pos=classified.signed_pos,
    )
    window = {
        "classifier_state": classified.state,
        "classifier_reason": classified.reason,
        "signed_pos": classified.signed_pos,
        "TARGET_POSITION_QTY_NUMERIC": qty_numeric,
    }
    observation = classify_position_observation_v1(
        result_class=RESULT_CLASS,
        payload=envelope,
        window=window,
    )
    if observation.get("POSITION_OBSERVATION_CLASS") != CASE_A_TARGET_NONZERO:
        raise P08NonzeroAdjudicationError(
            f"NOT_CASE_A:{observation.get('POSITION_OBSERVATION_CLASS')}"
        )
    if observation.get("P08_CLOSED") is not True:
        raise P08NonzeroAdjudicationError("EXISTING_CONTRACT_REJECTS_NONZERO_ROW")
    if observation.get("TARGET_POSITION_NONZERO_PROVEN") is not True:
        raise P08NonzeroAdjudicationError("NONZERO_NOT_PROVEN")
    if observation.get("TARGET_POSITION_ZERO_PROVEN") is not False:
        raise P08NonzeroAdjudicationError("ZERO_PROVEN_CONFLICT")
    if qty_numeric != "PASS":
        raise P08NonzeroAdjudicationError(f"QTY_NUMERIC_NOT_PASS:{qty_numeric}")
    if observation.get("NEXT_AUTHORITY_BOUNDARY") != NEXT_AUTHORITY_BOUNDARY:
        raise P08NonzeroAdjudicationError("NEXT_AUTHORITY_BOUNDARY_DRIFT")

    prereq = adjudicate_prerequisite_08_window_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if prereq.get("EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN") is not True:
        raise P08NonzeroAdjudicationError("PREREQUISITE_08_NOT_PROVEN")
    if prereq.get("EARLIEST_UNRESOLVED_DEPENDENCY") != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise P08NonzeroAdjudicationError("EARLIEST_UNRESOLVED_DEPENDENCY_DRIFT")

    additional_runtime_fact_required = False
    if additional_runtime_fact_required:
        raise P08NonzeroAdjudicationError("ADDITIONAL_RUNTIME_FACT_REQUIRED")

    reconstructed_sha = reconstructed_captured_json_sha256_v1(envelope)
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_CAPTURE_OWNER_GO": PRIOR_CAPTURE_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_HOST": AUTHORIZED_HOST,
        "AUTHORIZED_ACCOUNT_UID": AUTHORIZED_ACCOUNT_UID,
        "AUTHORIZED_ENDPOINT": AUTHORIZED_ENDPOINT,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "HTTP_STATUS": HTTP_STATUS,
        "OKX_CODE": OKX_CODE,
        "QUERY": dict(QUERY),
        "RESULT_CLASS": RESULT_CLASS,
        "CLASSIFIER_ID": AUTHORIZED_CLASSIFIER_ID,
        "OBSERVATION_CLASSIFIER_ID": OBSERVATION_CLASSIFIER_ID,
        "classifier_state": classified.state,
        "classifier_reason": classified.reason,
        "signed_pos": classified.signed_pos,
        "query_completeness_proven": classified.query_completeness_proven,
        "empty_data_is_zero": classified.empty_data_is_zero,
        "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": True,
        "QUERY_COMPLETENESS_PROVEN_FALSE_DOES_NOT_INVALIDATE_OBSERVED_NONZERO_TARGET_ROW": (
            QUERY_COMPLETENESS_PROVEN_FALSE_DOES_NOT_INVALIDATE_OBSERVED_NONZERO_TARGET_ROW
        ),
        "TARGET_POSITION_QTY_NUMERIC": qty_numeric,
        "TARGET_POSITION_QTY_UNIT": "UNPROVEN",
        "POSITION_OBSERVATION_CLASS": observation["POSITION_OBSERVATION_CLASS"],
        "POSITION_RESPONSE_OBSERVED": observation["POSITION_RESPONSE_OBSERVED"],
        "TARGET_INSTRUMENT_ROW_OBSERVED": observation["TARGET_INSTRUMENT_ROW_OBSERVED"],
        "POSITION_STATE_OBSERVED": observation["POSITION_STATE_OBSERVED"],
        "TARGET_POSITION_ZERO_PROVEN": TARGET_POSITION_ZERO_PROVEN,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "P08_CLOSED": P08_CLOSED,
        "P08_VERDICT": P08_VERDICT,
        "P08_CANONICAL_CLOSE_DEFINITION": P08_CANONICAL_CLOSE_DEFINITION,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EXECUTION_PREREQUISITE_08_STATUS": prereq.get("EXECUTION_PREREQUISITE_08_STATUS"),
        "EXECUTION_PREREQUISITE_09_STATUS": prereq.get("EXECUTION_PREREQUISITE_09_STATUS"),
        "G_POSMODE_SUBMIT_BODY_PROVEN": G_POSMODE_SUBMIT_BODY_PROVEN,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "AUTHORIZED_GET_COUNT": AUTHORIZED_GET_COUNT,
        "ACTUAL_GET_COUNT": ACTUAL_GET_COUNT,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "THIS_GO_POST_COUNT": THIS_GO_POST_COUNT,
        "SECOND_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": ORIGINAL_WIRE_BODY_BYTES_AVAILABLE,
        "RECONSTRUCTED_CAPTURED_JSON_SHA256": reconstructed_sha,
        "BODY_SHA256_KIND": "RECONSTRUCTED_AUTHORIZED_FORENSIC_FIELDS_NOT_ORIGINAL_WIRE",
        "CAPTURED_ENVELOPE": envelope,
        "P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS": (
            P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS
        ),
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "ADDITIONAL_RUNTIME_FACT_REQUIRED": False,
        "POSITION_OBSERVATION_CLASS_EXPECTED": POSITION_OBSERVATION_CLASS,
    }
