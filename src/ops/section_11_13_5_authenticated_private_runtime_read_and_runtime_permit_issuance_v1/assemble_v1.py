"""Assemble authenticated private runtime read and permit issuance evidence pack."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.adjudicate_v1 import (
    adjudicate_authenticated_private_runtime_read_and_permit_issuance_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    AUTHORIZED_ACCOUNT_UID,
    AUTHORIZED_HOST,
    AUTHORIZED_OPERATION,
    AUTHORIZED_SCOPE,
    CENSUS_RUNTIME_RESIDUAL,
    EARLIEST_UNRESOLVED_DEPENDENCY,
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
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_COUNT,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.persist_v1 import (
    persist_authenticated_private_runtime_read_evidence_v1,
)


class AuthenticatedPrivateRuntimeReadAssembleError(RuntimeError):
    """Fail-closed assemble violation."""


def assemble_authenticated_private_runtime_read_and_permit_issuance_v1(
    *,
    origin_main_sha: str,
    runtime_facts: Mapping[str, Any],
    evidence_root: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise AuthenticatedPrivateRuntimeReadAssembleError("ORIGIN_MAIN_SHA_MISMATCH")
    verdict = adjudicate_authenticated_private_runtime_read_and_permit_issuance_v1(
        origin_main_sha=origin_main_sha,
        runtime_facts=runtime_facts,
    )
    if verdict["POST_PERFORMED"] is True:
        raise AuthenticatedPrivateRuntimeReadAssembleError("POST_MUST_REMAIN_FALSE")
    if verdict["FLATTEN_EXECUTE_AUTHORIZED"] is True:
        raise AuthenticatedPrivateRuntimeReadAssembleError(
            "FLATTEN_EXECUTE_MUST_REMAIN_UNAUTHORIZED"
        )
    if verdict["NETWORK_SESSION_AUTHORIZED"] is True:
        raise AuthenticatedPrivateRuntimeReadAssembleError(
            "FLATTEN_NETWORK_SESSION_MUST_REMAIN_UNAUTHORIZED"
        )
    permit_audit = dict(runtime_facts.get("PERMIT_AUDIT") or {})
    census = {
        "DOCUMENT_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_PERMIT_ISSUANCE_CENSUS_V1",
        "DOCUMENT_ROLE": "FORENSIC_CENSUS_AUTHORITY_NONE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "SEAM_COUNT": verdict["CENSUS"]["SEAM_COUNT"],
        "EPISTEMIC_CLASS_COUNTS": verdict["CENSUS"]["EPISTEMIC_CLASS_COUNTS"],
        "PROVEN_SEAMS": verdict["CENSUS"]["PROVEN_SEAMS"],
        "NOT_PROMOTED_SEAMS": verdict["CENSUS"]["NOT_PROMOTED_SEAMS"],
        "NAMED_REMAINING_HIGHER_AUTHORITY": list(NAMED_REMAINING_HIGHER_AUTHORITY),
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "POST_PERFORMED": False,
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "RUNTIME_PERMIT_ISSUED": verdict["RUNTIME_PERMIT_ISSUED"],
        "NETWORK_SESSION_AUTHORIZED": False,
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "NETWORK_PROVEN": verdict["NETWORK_PROVEN"],
        "CREDENTIAL_USE_PROVEN": verdict["CREDENTIAL_USE_PROVEN"],
        "G05_STATUS": verdict["G05_STATUS"],
        "G06_STATUS": verdict["G06_STATUS"],
    }
    lineage = {
        "DOCUMENT_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_PERMIT_ISSUANCE_LINEAGE_V1",
        "DOCUMENT_ROLE": "FORENSIC_LINEAGE_AUTHORITY_NONE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "LINEAGE_FIELD_NAMES": verdict["CENSUS"]["LINEAGE_FIELD_NAMES"],
        "SEAMS": verdict["LINEAGE"],
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "POST_PERFORMED": False,
    }
    adjudication = {
        **verdict,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
    }
    summary = {
        "DOCUMENT_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_PERMIT_ISSUANCE_PACKAGE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_CONSUMED": bool(runtime_facts.get("OWNER_GO_CONSUMED")),
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "AUTHORIZED_SCOPE": AUTHORIZED_SCOPE,
        "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
        "HOST": AUTHORIZED_HOST,
        "AUTHORIZED_ACCOUNT_UID": AUTHORIZED_ACCOUNT_UID,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "AUTHENTICATED_PRIVATE_RUNTIME_READ": verdict["AUTHENTICATED_PRIVATE_RUNTIME_READ"],
        "RUNTIME_PERMIT_ISSUANCE": verdict["RUNTIME_PERMIT_ISSUANCE"],
        "RUNTIME_PERMIT_ISSUED": verdict["RUNTIME_PERMIT_ISSUED"],
        "PERMIT_ISSUANCE_ATTEMPTED": True,
        "PERMIT_ISSUANCE_RESULT": verdict["PERMIT_ISSUANCE_RESULT"],
        "PERMIT_ID_OR_HASH": verdict["PERMIT_ID_OR_HASH"],
        "G05_STATUS": verdict["G05_STATUS"],
        "G06_STATUS": verdict["G06_STATUS"],
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "CREDENTIAL_USE_PROVEN": verdict["CREDENTIAL_USE_PROVEN"],
        "NETWORK_PROVEN": verdict["NETWORK_PROVEN"],
        "PRIVATE_GET_PROVEN": verdict["PRIVATE_GET_PROVEN"],
        "POSITION_GET_USED": verdict["POSITION_GET_USED"],
        "PUBLIC_GET_USED": False,
        "POST_PERFORMED": False,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": int(runtime_facts.get("WRITE_REQUEST_COUNT") or 0),
        "GET_REQUEST_COUNT": int(runtime_facts.get("GET_REQUEST_COUNT") or 0),
        "HTTP_EXCHANGE_COUNT": int(runtime_facts.get("HTTP_EXCHANGE_COUNT") or 0),
        "HTTP_STATUS": runtime_facts.get("HTTP_STATUS"),
        "OKX_CODE": runtime_facts.get("OKX_CODE"),
        "RESULT_CLASS": runtime_facts.get("RESULT_CLASS"),
        "POSITION_OBSERVATION_CLASS": verdict["POSITION_OBSERVATION_CLASS"],
        "POSITION_OBSERVATION_FRESHNESS_ALLOWED": verdict["POSITION_OBSERVATION_FRESHNESS_ALLOWED"],
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "PRODUCTIVE_FLATTEN_POST_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "EXECUTION_READY": False,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "NEXT_WORKPACKAGE": NEXT_WORKPACKAGE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "CENSUS_RUNTIME_RESIDUAL": CENSUS_RUNTIME_RESIDUAL,
        "REMAINING_GAP_COUNT": verdict["REMAINING_GAP_COUNT"],
        "REMAINING_RUNTIME_GAPS": verdict["REMAINING_RUNTIME_GAPS"],
        "REMAINING_EXTERNAL_STATE_GAPS": verdict["REMAINING_EXTERNAL_STATE_GAPS"],
        "REMAINING_OWNER_DECISIONS": verdict["REMAINING_OWNER_DECISIONS"],
        "WORKPACKAGE_COUNT": WORKPACKAGE_COUNT,
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT": MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
        "GET_ERROR": runtime_facts.get("GET_ERROR"),
        "PARSE_ERROR": runtime_facts.get("PARSE_ERROR"),
    }
    get_sanitized = {
        "DOCUMENT_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ_GET_ACCOUNT_POSITIONS_V1",
        "DOCUMENT_ROLE": "SANITIZED_RAW_RUNTIME_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "ENDPOINT": runtime_facts.get("ENDPOINT"),
        "METHOD": "GET",
        "HOST": AUTHORIZED_HOST,
        "REQUEST_TIME_UTC": runtime_facts.get("REQUEST_TIME_UTC"),
        "RESPONSE_TIME_UTC": runtime_facts.get("RESPONSE_TIME_UTC"),
        "HTTP_STATUS": runtime_facts.get("HTTP_STATUS"),
        "OKX_CODE": runtime_facts.get("OKX_CODE"),
        "OKX_MESSAGE": runtime_facts.get("SANITIZED_OKX_MESSAGE"),
        "BODY_SHA256": runtime_facts.get("BODY_SHA256"),
        "BODY_BYTES": runtime_facts.get("BODY_BYTES"),
        "DATA_ROW_COUNT": runtime_facts.get("DATA_ROW_COUNT"),
        "RAW_DATA_SHAPE": runtime_facts.get("RAW_DATA_SHAPE"),
        "REDACTED_PAYLOAD": runtime_facts.get("REDACTED_PAYLOAD"),
        "RESULT_CLASS": runtime_facts.get("RESULT_CLASS"),
        "OBSERVATION_IDENTITY": runtime_facts.get("OBSERVATION_IDENTITY"),
        "LOCAL_RESPONSE_RECEIVED_AT": runtime_facts.get("LOCAL_RESPONSE_RECEIVED_AT"),
        "SECRET_VALUES_INCLUDED": False,
        "POST_PERFORMED": False,
    }
    runtime_permit = {
        "DOCUMENT_CLASS": "RUNTIME_BOUNDED_ACTIVATION_PERMIT_V1",
        "DOCUMENT_ROLE": "AUTHORITY_CAPABILITY_ARTIFACT_NOT_FLATTEN_EXECUTE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        **permit_audit,
        "POST_NOT_IMPLIED": True,
        "FLATTEN_EXECUTE_NOT_IMPLIED": True,
        "LIVE_AUTHORIZED_NOT_IMPLIED": True,
        "POST_PERFORMED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "FLATTEN_EXECUTE_AUTHORIZED": False,
    }
    claims = {
        **CLAIMS,
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "RUNTIME_PERMIT_ISSUED": verdict["RUNTIME_PERMIT_ISSUED"],
        "PERMIT_ISSUANCE_RESULT": verdict["PERMIT_ISSUANCE_RESULT"],
        "G05_STATUS": verdict["G05_STATUS"],
        "G06_STATUS": verdict["G06_STATUS"],
        "POST_PERFORMED": False,
        "POST_ALLOWED": False,
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
    }
    result: dict[str, Any] = {
        "verdict": verdict,
        "census": census,
        "lineage": lineage,
        "adjudication": adjudication,
        "summary": summary,
        "GET_ACCOUNT_POSITIONS": get_sanitized,
        "RUNTIME_PERMIT": runtime_permit,
    }
    if evidence_root is not None:
        stamp = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pack = Path(evidence_root) / stamp
        verified = persist_authenticated_private_runtime_read_evidence_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            census=census,
            lineage=lineage,
            adjudication=adjudication,
            summary=summary,
            get_sanitized=get_sanitized,
            runtime_permit=runtime_permit,
            claims=claims,
        )
        result["EVIDENCE_PACK"] = str(pack)
        result["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
        result["RUN_ID"] = stamp
    return result
