"""Assemble the offline P08 authority-boundary adjudication pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.authority_boundary_v1 import (
    adjudicate_minimum_higher_authority_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.closure_condition_v1 import (
    prove_p08_closure_condition_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    AUTHORIZED_HOST,
    AUTHORIZED_OPERATION,
    AUTHORIZED_SCOPE,
    CANONICAL_EVIDENCE_RUN_ID,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    CURRENT_EXECUTION_READINESS,
    EMPTY_DATA_IS_ZERO,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    FUTURE_EXECUTION_GO_DRAFT_STATUS,
    GET_NOT_REQUIRED_REASON,
    G_POSMODE_SUBMIT_BODY_PROVEN,
    MINIMUM_HIGHER_AUTHORITY,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P08_NEXT_AUTHORITY_RESULT,
    P08_READ_ONLY_CLOSURE_RESULT,
    POSITION_OBSERVATION_CLASS,
    PREDECESSOR_SLICE,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.future_go_draft_v1 import (
    build_future_execution_go_draft_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.mechanism_census_v1 import (
    census_state_appearance_mechanisms_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.persist_v1 import (
    persist_p08_authority_boundary_evidence_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.readiness_v1 import (
    adjudicate_current_execution_readiness_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.safety_v1 import (
    prove_safety_invariants_v1,
)


class P08AuthorityBoundaryAssembleError(RuntimeError):
    """Fail-closed assemble violation."""


def assemble_p08_authority_boundary_v1(
    *,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    run_id: str = CANONICAL_EVIDENCE_RUN_ID,
) -> dict[str, Any]:
    """Build and optionally persist the offline adjudication. No GET. No POST."""
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08AuthorityBoundaryAssembleError("ORIGIN_MAIN_SHA_MISMATCH")
    empty_envelope = {"code": "0", "msg": "", "data": []}
    closure = prove_p08_closure_condition_v1(positions_payload=empty_envelope)
    census = census_state_appearance_mechanisms_v1()
    readiness = adjudicate_current_execution_readiness_v1()
    authority = adjudicate_minimum_higher_authority_v1(census=census, readiness=readiness)
    future_go = build_future_execution_go_draft_v1()
    safety = prove_safety_invariants_v1()
    blockers = {
        "CURRENT_BLOCKERS": list(readiness.get("CURRENT_BLOCKERS") or []),
        "OPEN_CONTRADICTIONS": list(readiness.get("OPEN_CONTRADICTIONS") or []),
        "FIRST_PARTY_CREATE_BLOCKERS": [
            "G_POSMODE_SUBMIT_BODY_UNPROVEN",
            "LIVE_ENABLED_FALSE",
            "LIVE_ARMED_FALSE",
            "SUBMIT_UNLOCKED_FALSE",
            "CANARY_AUTHORIZED_FALSE",
            "HISTORICAL_VENUE_CAPACITY_PROVEN_ZERO",
        ],
        "EXTERNAL_APPEARANCE_REMAINING": [
            "OWNER_VENUE_MANUAL_TARGET_POSITION_ABSENT",
            "NO_UNCONSUMED_P08_OBSERVATION_GET_GO",
        ],
        "GET_NOT_REQUIRED_REASON": GET_NOT_REQUIRED_REASON,
    }
    if authority.get("P08_NEXT_AUTHORITY_RESULT") != P08_NEXT_AUTHORITY_RESULT:
        raise P08AuthorityBoundaryAssembleError("AUTHORITY_RESULT_DRIFT")
    if int(census.get("VIABLE_MECHANISM_COUNT") or 0) != 1:
        raise P08AuthorityBoundaryAssembleError("VIABLE_COUNT_DRIFT")
    adjudication = {
        "DOCUMENT_CLASS": "P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "P08_CLOSURE_CONDITION_STATUS": closure.get("P08_CLOSURE_CONDITION_STATUS"),
        "P08_NEXT_AUTHORITY_RESULT": P08_NEXT_AUTHORITY_RESULT,
        "MINIMUM_HIGHER_AUTHORITY": MINIMUM_HIGHER_AUTHORITY,
        "STATE_APPEARANCE_MECHANISM_COUNT": census.get("STATE_APPEARANCE_MECHANISM_COUNT"),
        "VIABLE_MECHANISM_COUNT": census.get("VIABLE_MECHANISM_COUNT"),
        "CURRENT_EXECUTION_READINESS": CURRENT_EXECUTION_READINESS,
        "CURRENT_BLOCKERS": blockers["CURRENT_BLOCKERS"],
        "OPEN_CONTRADICTIONS": "NONE",
        "FUTURE_EXECUTION_GO_DRAFT_STATUS": FUTURE_EXECUTION_GO_DRAFT_STATUS,
        "P08_CLOSED": P08_CLOSED,
        "TARGET_POSITION_ZERO_PROVEN": TARGET_POSITION_ZERO_PROVEN,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "G_POSMODE_SUBMIT_BODY_PROVEN": G_POSMODE_SUBMIT_BODY_PROVEN,
        "POSITION_OBSERVATION_CLASS": POSITION_OBSERVATION_CLASS,
        "P08_READ_ONLY_CLOSURE_RESULT": P08_READ_ONLY_CLOSURE_RESULT,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EARLIEST_UNRESOLVED_DEPENDENCY": CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
    }
    summary = {
        "DOCUMENT_CLASS": "P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_PACKAGE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_CONSUMED": True,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "AUTHORIZED_SCOPE": AUTHORIZED_SCOPE,
        "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
        "HOST": AUTHORIZED_HOST,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "P08_NEXT_AUTHORITY_RESULT": P08_NEXT_AUTHORITY_RESULT,
        "MINIMUM_HIGHER_AUTHORITY": MINIMUM_HIGHER_AUTHORITY,
        "STATE_APPEARANCE_MECHANISM_COUNT": census.get("STATE_APPEARANCE_MECHANISM_COUNT"),
        "VIABLE_MECHANISM_COUNT": census.get("VIABLE_MECHANISM_COUNT"),
        "FUTURE_EXECUTION_GO_DRAFT_STATUS": FUTURE_EXECUTION_GO_DRAFT_STATUS,
        "GET_REQUEST_COUNT": 0,
        "HTTP_EXCHANGE_COUNT": 0,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": 0,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "P08_CLOSED": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "CORE_CHANGED": False,
        "NEW_AUTHORITY_CREATED": False,
        "MERGE_AUTHORIZED": False,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
    }
    result: dict[str, Any] = {
        "closure": closure,
        "census": census,
        "readiness": readiness,
        "authority": authority,
        "future_go": future_go,
        "safety": safety,
        "blockers": blockers,
        "adjudication": adjudication,
        "summary": summary,
    }
    if evidence_root is not None:
        pack = Path(evidence_root) / run_id
        verified = persist_p08_authority_boundary_evidence_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            closure=closure,
            census=census,
            readiness=readiness,
            authority=authority,
            future_go=future_go,
            safety=safety,
            blockers=blockers,
            adjudication=adjudication,
            summary=summary,
        )
        result["EVIDENCE_PACK"] = str(pack)
        result["MANIFEST_VERIFY_RC"] = verified.get("MANIFEST_VERIFY_RC")
        result["EVIDENCE_DIRNAME"] = EVIDENCE_DIRNAME
    return result
