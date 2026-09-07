"""Execute required-field capture-seam and owner-vacancy persist. No GET. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_v1 import (
    bind_section_11_14_live_handoff_owner_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    bind_section_11_14_live_handoff_owner_vacancy_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_derivation_refusal_v1 import (
    bind_pos_derivation_adjudication_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_census_v1 import (
    bind_pos_producer_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    bind_live_order_timeline_capture_v1,
    bind_required_field_contract_v1,
)


def execute_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    allowed_owner_gos = {OWNER_GO, HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO}
    allowed_shas = {EXPECTED_ORIGIN_MAIN_SHA, HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA}
    if str(owner_go or "").strip() not in allowed_owner_gos:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() not in allowed_shas:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    field_contract = bind_required_field_contract_v1()
    timeline = bind_live_order_timeline_capture_v1()
    producers = bind_pos_producer_census_v1()
    derivations = bind_pos_derivation_adjudication_v1()
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    owner_bind = bind_section_11_14_live_handoff_owner_contract_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "POS_SEMANTICS": field_contract["POS_SEMANTICS"],
        "POS_TYPE": field_contract["POS_TYPE"],
        "POS_SOURCE_AUTHORITY": field_contract["POS_SOURCE_AUTHORITY"],
        "POS_CAPTURE_TIME_REQUIREMENT": field_contract["POS_CAPTURE_TIME_REQUIREMENT"],
        "POS_PEAK_TRADE_OWNERSHIP_REQUIRED": field_contract["POS_PEAK_TRADE_OWNERSHIP_REQUIRED"],
        "POS_PRODUCER_CANDIDATE_COUNT": producers["POS_PRODUCER_CANDIDATE_COUNT"],
        "POS_ACCEPTABLE_PRODUCER_COUNT": producers["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "POS_REJECTED_PRODUCER_COUNT": producers["POS_REJECTED_PRODUCER_COUNT"],
        "POS_UNPROVEN_PRODUCER_COUNT": producers["POS_UNPROVEN_PRODUCER_COUNT"],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": timeline[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT"
        ],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": timeline[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM"
        ],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": timeline[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN"
        ],
        "COMPLETE_CAPTURE_SEAM": timeline["COMPLETE_CAPTURE_SEAM"],
        "OWNER_VACANCY_CONTRACT_STATUS": vacancy["OWNER_VACANCY_CONTRACT_STATUS"],
        "PROPOSED_FIRST_OWNER_ID": vacancy["PROPOSED_FIRST_OWNER_ID"],
        "NEW_OWNER_REQUIRED": vacancy["NEW_OWNER_REQUIRED"],
        "PRODUCTIVE_WRITER_PRESENT": False,
        "PRODUCTIVE_READER_PRESENT": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "PRODUCTIVE_WRITER_JOIN_CREATED": False,
        "PRODUCTIVE_READER_JOIN_CREATED": False,
        "LATER_WRITER_CLAIMED_POSSIBLE": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
        "repo_root": str(repo_root),
    }
    pack = (
        Path(repo_root)
        / "evidence"
        / "ops"
        / "section_11_14_live_order_and_economic_evidence_ladder_v1"
        / pack_run_id
    )
    return {
        "pack": str(pack),
        "summary": summary,
        "field_contract": field_contract,
        "timeline": timeline,
        "pos_producer_census": producers,
        "pos_derivation": derivations,
        "owner_vacancy": vacancy,
        "owner_bind": owner_bind,
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
