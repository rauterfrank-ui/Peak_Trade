"""Assemble the offline P08 CASE_A nonzero adjudication persist/close pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.adjudicate_v1 import (
    adjudicate_captured_nonzero_position_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    CAPTURED_GET_METADATA,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.constants_v1 import (
    ACTUAL_GET_COUNT,
    AUTHORIZED_ACCOUNT_UID,
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_GET_COUNT,
    AUTHORIZED_HOST,
    AUTHORIZED_OPERATION,
    AUTHORIZED_SCOPE,
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    G_POSMODE_SUBMIT_BODY_PROVEN,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS,
    P08_CLOSED,
    P08_VERDICT,
    POSITION_OBSERVATION_CLASS,
    PREDECESSOR_SLICE,
    PRIOR_CAPTURE_OWNER_GO,
    SECRETREF_URI,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
    THIS_GO_GET_COUNT,
    THIS_GO_POST_COUNT,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.persist_v1 import (
    persist_p08_nonzero_adjudication_evidence_v1,
)


class P08NonzeroAssembleError(RuntimeError):
    """Fail-closed assemble violation."""


def assemble_p08_nonzero_adjudication_v1(
    *,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    run_id: str = CANONICAL_EVIDENCE_RUN_ID,
) -> dict[str, Any]:
    """Build and optionally persist the offline CASE_A adjudication. No GET. No POST."""
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08NonzeroAssembleError("ORIGIN_MAIN_SHA_MISMATCH")
    verdict = adjudicate_captured_nonzero_position_v1(origin_main_sha=origin_main_sha)
    envelope = verdict["CAPTURED_ENVELOPE"]
    snapshot = {
        "DOCUMENT_CLASS": "P08_NONZERO_POSITION_CAPTURED_GET_SNAPSHOT_V1",
        "DOCUMENT_ROLE": "BOUND_AUTHORIZED_FORENSIC_INPUT_NOT_ORIGINAL_WIRE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "PRIOR_CAPTURE_OWNER_GO": PRIOR_CAPTURE_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "HOST": AUTHORIZED_HOST,
        "AUTHORIZED_ACCOUNT_UID": AUTHORIZED_ACCOUNT_UID,
        "AUTHORIZED_ENDPOINT": AUTHORIZED_ENDPOINT,
        "ENDPOINT": "/api/v5/account/positions",
        "METHOD": "GET",
        "QUERY_PARAMETERS": {},
        "INSTID_FILTER_USED": False,
        "SECRETREF_URI": SECRETREF_URI,
        "REQUEST_TIMESTAMP": CAPTURED_GET_METADATA["REQUEST_TIMESTAMP"],
        "RESPONSE_TIMESTAMP": CAPTURED_GET_METADATA["RESPONSE_TIMESTAMP"],
        "HTTP_STATUS": CAPTURED_GET_METADATA["HTTP_STATUS"],
        "OKX_CODE": CAPTURED_GET_METADATA["OKX_CODE"],
        "OKX_MSG": CAPTURED_GET_METADATA["OKX_MSG"],
        "RAW_DATA_COUNT": CAPTURED_GET_METADATA["RAW_DATA_COUNT"],
        "TARGET_INSTRUMENT_MATCH_COUNT": CAPTURED_GET_METADATA["TARGET_INSTRUMENT_MATCH_COUNT"],
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CAPTURED_FIELD_SET": CAPTURED_GET_METADATA["CAPTURED_FIELD_SET"],
        "REDACTED_PAYLOAD": envelope,
        "TARGET_MATCHING_ROW": envelope["data"][0],
        "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
        "RECONSTRUCTED_CAPTURED_JSON_SHA256": verdict["RECONSTRUCTED_CAPTURED_JSON_SHA256"],
        "BODY_SHA256_KIND": verdict["BODY_SHA256_KIND"],
        "AUTHORIZED_GET_COUNT": AUTHORIZED_GET_COUNT,
        "ACTUAL_GET_COUNT": ACTUAL_GET_COUNT,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "THIS_GO_POST_COUNT": THIS_GO_POST_COUNT,
        "SECOND_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "GET_PERFORMED_THIS_PERSIST": False,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
    }
    adjudication = {
        "DOCUMENT_CLASS": "P08_NONZERO_POSITION_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_WIRE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "PRIOR_CAPTURE_OWNER_GO": PRIOR_CAPTURE_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "CLASSIFIER_ID": verdict["CLASSIFIER_ID"],
        "OBSERVATION_CLASSIFIER_ID": verdict["OBSERVATION_CLASSIFIER_ID"],
        "RESULT_CLASS": verdict["RESULT_CLASS"],
        "classifier_state": verdict["classifier_state"],
        "classifier_reason": verdict["classifier_reason"],
        "signed_pos": verdict["signed_pos"],
        "query_completeness_proven": verdict["query_completeness_proven"],
        "empty_data_is_zero": verdict["empty_data_is_zero"],
        "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": True,
        "QUERY_COMPLETENESS_PROVEN_FALSE_DOES_NOT_INVALIDATE_OBSERVED_NONZERO_TARGET_ROW": (
            verdict[
                "QUERY_COMPLETENESS_PROVEN_FALSE_DOES_NOT_INVALIDATE_OBSERVED_NONZERO_TARGET_ROW"
            ]
        ),
        "TARGET_POSITION_QTY_NUMERIC": verdict["TARGET_POSITION_QTY_NUMERIC"],
        "TARGET_POSITION_QTY_UNIT": verdict["TARGET_POSITION_QTY_UNIT"],
        "POSITION_OBSERVATION_CLASS": verdict["POSITION_OBSERVATION_CLASS"],
        "TARGET_INSTRUMENT_ROW_OBSERVED": verdict["TARGET_INSTRUMENT_ROW_OBSERVED"],
        "POSITION_STATE_OBSERVED": verdict["POSITION_STATE_OBSERVED"],
        "TARGET_POSITION_ZERO_PROVEN": TARGET_POSITION_ZERO_PROVEN,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "P08_CLOSED": P08_CLOSED,
        "P08_VERDICT": P08_VERDICT,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EXECUTION_PREREQUISITE_08_STATUS": verdict["EXECUTION_PREREQUISITE_08_STATUS"],
        "EXECUTION_PREREQUISITE_09_STATUS": verdict["EXECUTION_PREREQUISITE_09_STATUS"],
        "G_POSMODE_SUBMIT_BODY_PROVEN": G_POSMODE_SUBMIT_BODY_PROVEN,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "ADDITIONAL_RUNTIME_FACT_REQUIRED": False,
        "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
        "RECONSTRUCTED_CAPTURED_JSON_SHA256": verdict["RECONSTRUCTED_CAPTURED_JSON_SHA256"],
        "BODY_SHA256_KIND": verdict["BODY_SHA256_KIND"],
        "AUTHORIZED_GET_COUNT": AUTHORIZED_GET_COUNT,
        "ACTUAL_GET_COUNT": ACTUAL_GET_COUNT,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "SECOND_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS": (
            P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS
        ),
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    summary = {
        "DOCUMENT_CLASS": "P08_NONZERO_POSITION_ADJUDICATION_PACKAGE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_CONSUMED": True,
        "PRIOR_CAPTURE_OWNER_GO": PRIOR_CAPTURE_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "AUTHORIZED_SCOPE": AUTHORIZED_SCOPE,
        "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
        "HOST": AUTHORIZED_HOST,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "POSITION_OBSERVATION_CLASS": POSITION_OBSERVATION_CLASS,
        "P08_VERDICT": P08_VERDICT,
        "P08_CLOSED": True,
        "TARGET_POSITION_NONZERO_PROVEN": True,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "EMPTY_DATA_IS_ZERO": False,
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "AUTHORIZED_GET_COUNT": AUTHORIZED_GET_COUNT,
        "ACTUAL_GET_COUNT": ACTUAL_GET_COUNT,
        "GET_REQUEST_COUNT": THIS_GO_GET_COUNT,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "HTTP_EXCHANGE_COUNT": 0,
        "POST_COUNT": THIS_GO_POST_COUNT,
        "WRITE_REQUEST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "SECOND_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "CORE_CHANGED": False,
        "NEW_AUTHORITY_CREATED": False,
        "MERGE_AUTHORIZED": False,
        "P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS": True,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
    }
    result: dict[str, Any] = {
        "verdict": verdict,
        "snapshot": snapshot,
        "adjudication": adjudication,
        "summary": summary,
    }
    if evidence_root is not None:
        pack = Path(evidence_root) / run_id
        verified = persist_p08_nonzero_adjudication_evidence_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            snapshot=snapshot,
            adjudication=adjudication,
            summary=summary,
        )
        result["EVIDENCE_PACK"] = str(pack)
        result["MANIFEST_VERIFY_RC"] = verified.get("MANIFEST_VERIFY_RC")
        result["EVIDENCE_DIRNAME"] = EVIDENCE_DIRNAME
    return result
