"""Assemble productive flatten POST and reconciliation evidence pack."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.adjudicate_v1 import (
    adjudicate_productive_flatten_post_and_reconciliation_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
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
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_v1 import (
    persist_productive_flatten_post_evidence_v1,
)


class ProductiveFlattenPostAssembleError(RuntimeError):
    """Fail-closed assemble violation."""


def assemble_productive_flatten_post_and_reconciliation_v1(
    *,
    origin_main_sha: str,
    runtime_facts: Mapping[str, Any],
    evidence_root: Path | None = None,
    persist: bool = True,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveFlattenPostAssembleError("ORIGIN_MAIN_SHA_MISMATCH")
    verdict = adjudicate_productive_flatten_post_and_reconciliation_v1(
        origin_main_sha=origin_main_sha,
        runtime_facts=runtime_facts,
    )
    permit_audit = dict(runtime_facts.get("PERMIT_AUDIT") or {})
    census = {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_CENSUS_V1",
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
        "POST_PERFORMED": verdict["POST_PERFORMED"],
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "LIVE_FLATTEN_PROVABILITY_PROVEN": verdict["LIVE_FLATTEN_PROVABILITY_PROVEN"],
        "G09_STATUS": verdict["G09_STATUS"],
        "G10_STATUS": verdict["G10_STATUS"],
        "G11_STATUS": verdict["G11_STATUS"],
        "G12_STATUS": verdict["G12_STATUS"],
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    lineage = {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_LINEAGE_V1",
        "DOCUMENT_ROLE": "FORENSIC_LINEAGE_AUTHORITY_NONE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "LINEAGE_FIELD_NAMES": verdict["CENSUS"]["LINEAGE_FIELD_NAMES"],
        "SEAMS": verdict["LINEAGE"],
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "POST_PERFORMED": verdict["POST_PERFORMED"],
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
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
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PACKAGE_V1",
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
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "PRIVATE_GET_USED": verdict["PRIVATE_GET_USED"],
        "POSITION_GET_USED": verdict["POSITION_GET_USED"],
        "PUBLIC_GET_USED": verdict["PUBLIC_GET_USED"],
        "POST_ATTEMPTED": verdict["POST_ATTEMPTED"],
        "POST_USED": verdict["POST_USED"],
        "POST_PERFORMED": verdict["POST_PERFORMED"],
        "POST_RESULT": verdict["POST_RESULT"],
        "POST_COUNT": verdict["THIS_GO_POST_COUNT"],
        "ORDER_SUBMIT_USED": verdict["ORDER_SUBMIT_USED"],
        "ORDER_ID_REDACTED": verdict["ORDER_ID_REDACTED"],
        "PERMIT_VALIDATION_RESULT": verdict["PERMIT_VALIDATION_RESULT"],
        "PERMIT_CONSUMED": verdict["PERMIT_CONSUMED"],
        "PERMIT_ISSUED": verdict["PERMIT_ISSUED"],
        "PERMIT_ID_OR_HASH": verdict["PERMIT_ID_OR_HASH"],
        "PRE_WIRE_POSITION_RESULT": verdict["PRE_WIRE_POSITION_RESULT"],
        "PRE_WIRE_POSITION_FRESHNESS": verdict["PRE_WIRE_POSITION_FRESHNESS"],
        "POSITION_OBSERVATION_CLASS": verdict["POSITION_OBSERVATION_CLASS"],
        "POST_POSITION_OBSERVATION_CLASS": verdict["POST_POSITION_OBSERVATION_CLASS"],
        "RECONCILIATION_ATTEMPTED": verdict["RECONCILIATION_ATTEMPTED"],
        "RECONCILIATION_RESULT": verdict["RECONCILIATION_RESULT"],
        "TARGET_POSITION_ZERO_PROVEN": verdict["TARGET_POSITION_ZERO_PROVEN"],
        "LIVE_FLATTEN_PROVABILITY_PROVEN": verdict["LIVE_FLATTEN_PROVABILITY_PROVEN"],
        "RETRY_USED": False,
        "RETRY_AUTHORITY_PROVEN": False,
        "FUNDING_USED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "EMPTY_DATA_IS_ZERO": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "EXECUTION_READY": False,
        "G09_STATUS": verdict["G09_STATUS"],
        "G10_STATUS": verdict["G10_STATUS"],
        "G11_STATUS": verdict["G11_STATUS"],
        "G12_STATUS": verdict["G12_STATUS"],
        "G13_STATUS": verdict["G13_STATUS"],
        "G14_STATUS": verdict["G14_STATUS"],
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
        "FAIL_CLOSED_REASON": verdict["FAIL_CLOSED_REASON"],
        "GET_REQUEST_COUNT": int(runtime_facts.get("GET_REQUEST_COUNT") or 0),
        "WRITE_REQUEST_COUNT": int(runtime_facts.get("WRITE_REQUEST_COUNT") or 0),
        "CANONICAL_OWNER_GO_TOKEN_FOUND": runtime_facts.get("CANONICAL_OWNER_GO_TOKEN_FOUND"),
        "CANONICAL_OWNER_GO_TOKEN": runtime_facts.get("CANONICAL_OWNER_GO_TOKEN"),
    }
    observations_sanitized = {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_OBSERVATIONS_V1",
        "DOCUMENT_ROLE": "SANITIZED_RAW_RUNTIME_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "HOST": AUTHORIZED_HOST,
        "OBSERVATIONS": runtime_facts.get("OBSERVATIONS"),
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    runtime_permit = {
        "DOCUMENT_CLASS": "RUNTIME_BOUNDED_ACTIVATION_PERMIT_V1",
        "DOCUMENT_ROLE": "AUTHORITY_CAPABILITY_ARTIFACT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        **permit_audit,
        "PERMIT_CONSUMED": verdict["PERMIT_CONSUMED"],
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    post_action_sanitized = {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_POST_ACTION_V1",
        "DOCUMENT_ROLE": "SANITIZED_POST_ACTION_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "GATE_RECEIPT": runtime_facts.get("GATE_RECEIPT"),
        "SUBMIT_RESULT": runtime_facts.get("SUBMIT_RESULT"),
        "POST_ACTION_VERDICT": runtime_facts.get("POST_ACTION_VERDICT"),
        "ORDER_ID_REDACTED": runtime_facts.get("ORDER_ID_REDACTED"),
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    claims = {
        **CLAIMS,
        "GET_PERFORMED_THIS_PERSIST": verdict["GET_PERFORMED_THIS_PERSIST"],
        "PRIVATE_AUTH_USED": verdict["PRIVATE_AUTH_USED"],
        "POST_PERFORMED": verdict["POST_PERFORMED"],
        "POST_USED": verdict["POST_USED"],
        "LIVE_FLATTEN_PROVABILITY_PROVEN": verdict["LIVE_FLATTEN_PROVABILITY_PROVEN"],
        "TARGET_POSITION_ZERO_PROVEN": verdict["TARGET_POSITION_ZERO_PROVEN"],
        "G09_STATUS": verdict["G09_STATUS"],
        "G10_STATUS": verdict["G10_STATUS"],
        "G11_STATUS": verdict["G11_STATUS"],
        "G12_STATUS": verdict["G12_STATUS"],
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    result: dict[str, Any] = {
        "verdict": verdict,
        "census": census,
        "lineage": lineage,
        "adjudication": adjudication,
        "summary": summary,
        "OBSERVATIONS": observations_sanitized,
        "RUNTIME_PERMIT": runtime_permit,
        "POST_ACTION": post_action_sanitized,
    }
    if persist and evidence_root is not None:
        stamp = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pack = Path(evidence_root) / stamp
        verified = persist_productive_flatten_post_evidence_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            census=census,
            lineage=lineage,
            adjudication=adjudication,
            summary=summary,
            observations_sanitized=observations_sanitized,
            runtime_permit=runtime_permit,
            post_action_sanitized=post_action_sanitized,
            claims=claims,
        )
        result["EVIDENCE_PACK"] = str(pack)
        result["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
        result["RUN_ID"] = stamp
    return result
