"""Assemble the offline P10 TARGET_POSITION_QTY unit forensic persist pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.adjudicate_v1 import (
    adjudicate_target_position_qty_unit_v1,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.constants_v1 import (
    AUTHORIZED_ACCOUNT_UID,
    AUTHORIZED_HOST,
    AUTHORIZED_OPERATION,
    AUTHORIZED_SCOPE,
    CANONICAL_EVIDENCE_RUN_ID,
    CONFLICT_COUNT,
    CURRENT_UNIT_CONTRACT,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_DOES_NOT_GRANT_EXECUTION_READINESS,
    P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    QTY_UNIT_CENSUS_COMPLETE,
    QTY_UNIT_LINEAGE_COMPLETE,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_QTY_UNIT,
    THIS_GO_GET_COUNT,
    THIS_GO_POST_COUNT,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.persist_v1 import (
    persist_p10_qty_unit_adjudication_evidence_v1,
)


class P10QtyUnitAssembleError(RuntimeError):
    """Fail-closed assemble violation."""


def assemble_p10_qty_unit_adjudication_v1(
    *,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    run_id: str = CANONICAL_EVIDENCE_RUN_ID,
) -> dict[str, Any]:
    """Build and optionally persist the offline unit adjudication. No GET. No POST."""
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P10QtyUnitAssembleError("ORIGIN_MAIN_SHA_MISMATCH")
    verdict = adjudicate_target_position_qty_unit_v1(origin_main_sha=origin_main_sha)
    if verdict["TARGET_POSITION_QTY_UNIT"] != "UNPROVEN":
        raise P10QtyUnitAssembleError("UNIT_MUST_REMAIN_UNPROVEN")
    census = {
        "DOCUMENT_CLASS": "P10_TARGET_POSITION_QTY_UNIT_CENSUS_V1",
        "DOCUMENT_ROLE": "FORENSIC_CENSUS_AUTHORITY_NONE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "QTY_UNIT_CENSUS_COMPLETE": QTY_UNIT_CENSUS_COMPLETE,
        "SEAM_COUNT": verdict["CENSUS"]["SEAM_COUNT"],
        "EPISTEMIC_CLASS_COUNTS": verdict["CENSUS"]["EPISTEMIC_CLASS_COUNTS"],
        "TARGET_POSITION_QTY_PROVEN_UNITS_FOUND": verdict["CENSUS"][
            "TARGET_POSITION_QTY_PROVEN_UNITS_FOUND"
        ],
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "FORBIDDEN_PROMOTION_ALIASES": verdict["FORBIDDEN_PROMOTION_ALIASES"],
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "POST_PERFORMED": False,
        "GET_PERFORMED_THIS_PERSIST": False,
    }
    lineage = {
        "DOCUMENT_CLASS": "P10_TARGET_POSITION_QTY_UNIT_LINEAGE_V1",
        "DOCUMENT_ROLE": "FORENSIC_LINEAGE_AUTHORITY_NONE",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "QTY_UNIT_LINEAGE_COMPLETE": QTY_UNIT_LINEAGE_COMPLETE,
        "LINEAGE_FIELD_NAMES": verdict["CENSUS"]["LINEAGE_FIELD_NAMES"],
        "SEAMS": verdict["LINEAGE"],
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "POST_PERFORMED": False,
    }
    adjudication = {
        "DOCUMENT_CLASS": "P10_TARGET_POSITION_QTY_UNIT_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_WIRE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_POSITION_QTY_UNIT": verdict["TARGET_POSITION_QTY_UNIT"],
        "CURRENT_UNIT_CONTRACT": verdict["CURRENT_UNIT_CONTRACT"],
        "QTY_UNIT_CENSUS_COMPLETE": QTY_UNIT_CENSUS_COMPLETE,
        "QTY_UNIT_LINEAGE_COMPLETE": QTY_UNIT_LINEAGE_COMPLETE,
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "UNIT_CHAIN_VERDICT": verdict["UNIT_CHAIN_VERDICT"],
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY": verdict[
            "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY"
        ],
        "SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY": verdict[
            "SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY"
        ],
        "ONE_CONTRACT_EQUALS_ONE_SUI": verdict["ONE_CONTRACT_EQUALS_ONE_SUI"],
        "NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF": verdict[
            "NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF"
        ],
        "IMPLICIT_PASSTHROUGH_PRESENT": verdict["IMPLICIT_PASSTHROUGH_PRESENT"],
        "IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF": verdict["IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF"],
        "POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE": verdict[
            "POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE"
        ],
        "signed_pos": verdict["signed_pos"],
        "TARGET_POSITION_QTY_RAW": verdict["TARGET_POSITION_QTY_RAW"],
        "TARGET_POSITION_QTY_NUMERIC": verdict["TARGET_POSITION_QTY_NUMERIC"],
        "P08_CLOSED": P08_CLOSED,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "THIS_GO_GET_COUNT": THIS_GO_GET_COUNT,
        "THIS_GO_POST_COUNT": THIS_GO_POST_COUNT,
        "GET_PERFORMED_THIS_PERSIST": False,
        "SECOND_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "P10_DOES_NOT_GRANT_EXECUTION_READINESS": P10_DOES_NOT_GRANT_EXECUTION_READINESS,
        "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT": P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    summary = {
        "DOCUMENT_CLASS": "P10_TARGET_POSITION_QTY_UNIT_ADJUDICATION_PACKAGE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_CONSUMED": True,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "AUTHORIZED_SCOPE": AUTHORIZED_SCOPE,
        "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
        "HOST": AUTHORIZED_HOST,
        "AUTHORIZED_ACCOUNT_UID": AUTHORIZED_ACCOUNT_UID,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "CURRENT_UNIT_CONTRACT": CURRENT_UNIT_CONTRACT,
        "QTY_UNIT_CENSUS_COMPLETE": QTY_UNIT_CENSUS_COMPLETE,
        "QTY_UNIT_LINEAGE_COMPLETE": QTY_UNIT_LINEAGE_COMPLETE,
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": True,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
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
        "P10_DOES_NOT_GRANT_EXECUTION_READINESS": True,
        "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT": True,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
    }
    result: dict[str, Any] = {
        "verdict": verdict,
        "census": census,
        "lineage": lineage,
        "adjudication": adjudication,
        "summary": summary,
    }
    if evidence_root is not None:
        pack = Path(evidence_root) / run_id
        verified = persist_p10_qty_unit_adjudication_evidence_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            census=census,
            lineage=lineage,
            adjudication=adjudication,
            summary=summary,
        )
        result["EVIDENCE_PACK"] = str(pack)
        result["MANIFEST_VERIFY_RC"] = verified.get("MANIFEST_VERIFY_RC")
        result["EVIDENCE_DIRNAME"] = EVIDENCE_DIRNAME
    return result
