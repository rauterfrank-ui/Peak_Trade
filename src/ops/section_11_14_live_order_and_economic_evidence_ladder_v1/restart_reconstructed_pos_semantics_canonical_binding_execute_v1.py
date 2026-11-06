"""Execute pos-semantics canonical binding persist. No GET. No POST. No writer join."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_OWNER_GO,
    HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    bind_okx_pos_versus_handoff_pos_v1,
    bind_pos_downstream_effect_v1,
    bind_pos_semantics_canonical_binding_v1,
    bind_pos_sign_proof_v1,
    bind_pos_temporal_provenance_v1,
    bind_pos_unit_proof_v1,
    bind_required_new_producer_contract_v1,
)


def execute_live_handoff_pos_semantics_canonical_binding_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    allowed_owner_gos = {OWNER_GO, HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_OWNER_GO}
    if str(owner_go or "").strip() not in allowed_owner_gos:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    allowed_shas = {EXPECTED_ORIGIN_MAIN_SHA, HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_SHA}
    if str(origin_main_sha or "").strip() not in allowed_shas:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    binding = bind_pos_semantics_canonical_binding_v1()
    downstream = bind_pos_downstream_effect_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if binding["POS_SEMANTICS"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_REMAIN_UNPROVEN")
    if binding["POS_ACCEPTABLE_PRODUCER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("POS_ACCEPTABLE_PRODUCER_MUST_REMAIN_ZERO")
    if binding["IMPLEMENTATION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    if downstream["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is True:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNADJUDICABLE")
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
        "FIRST_OWNER_PRODUCTIVELY_BOUND": False,
        "POS_SEMANTICS": binding["POS_SEMANTICS"],
        "POS_SEMANTICS_STATUS": binding["POS_SEMANTICS_STATUS"],
        "POS_CANONICAL_MEANING": binding["POS_CANONICAL_MEANING"],
        "POS_UNIT": binding["POS_UNIT"],
        "POS_SIGN_SEMANTICS": binding["POS_SIGN_SEMANTICS"],
        "POS_POS_SIDE_RELATION": binding["POS_POS_SIDE_RELATION"],
        "POS_INSTRUMENT_BINDING": binding["POS_INSTRUMENT_BINDING"],
        "POS_POSITION_MODE_BINDING": binding["POS_POSITION_MODE_BINDING"],
        "POS_ACCOUNT_MODE_BINDING": binding["POS_ACCOUNT_MODE_BINDING"],
        "POS_ACCEPTABLE_PRODUCER_COUNT": binding["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "POS_ACCEPTABLE_PRODUCERS": binding["POS_ACCEPTABLE_PRODUCERS"],
        "POS_REJECTED_PRODUCER_COUNT": binding["POS_REJECTED_PRODUCER_COUNT"],
        "POS_UNPROVEN_PRODUCER_COUNT": binding["POS_UNPROVEN_PRODUCER_COUNT"],
        "POS_UNPROVEN_PRODUCERS": binding["POS_UNPROVEN_PRODUCERS"],
        "POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY": binding[
            "POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY"
        ],
        "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED": binding[
            "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED"
        ],
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "POWER_LOSS_DURABILITY": "UNPROVEN",
        "DURABILITY_PROVEN_EFFECTIVE": False,
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "ARCHITECTURE_ADJUDICATION_COMPLETE": True,
        "IMPLEMENTATION_AUTHORIZED": False,
        "PROPOSED_NEXT_SLICE": binding["PROPOSED_NEXT_SLICE"],
        "SEQUENCE_AUTO_EXECUTED": False,
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
        "binding": binding,
        "candidate_matrix": {"rows": binding["candidates"]},
        "unit_proof": bind_pos_unit_proof_v1(),
        "sign_proof": bind_pos_sign_proof_v1(),
        "temporal_provenance": bind_pos_temporal_provenance_v1(),
        "okx_versus_handoff": bind_okx_pos_versus_handoff_pos_v1(),
        "required_new_producer": bind_required_new_producer_contract_v1(),
        "downstream": downstream,
        "claims": dict(CLAIMS),
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
