"""Execute pos producer-semantics contract persist. No GET. No POST. No writer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    bind_handoff_schema_version_v1,
    bind_new_pos_producer_contract_v1,
    bind_pos_account_mode_adjudication_v1,
    bind_pos_downstream_effect_after_producer_contract_v1,
    bind_pos_producer_semantics_and_contract_v1,
    bind_pos_sign_adjudication_v1,
    bind_pos_unit_adjudication_v1,
    bind_what_restart_reconstructs_v1,
)


def execute_live_handoff_pos_producer_semantics_and_contract_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    binding = bind_pos_producer_semantics_and_contract_v1()
    downstream = bind_pos_downstream_effect_after_producer_contract_v1()
    producer = bind_new_pos_producer_contract_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if binding["POS_SEMANTICS"] != "PROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_BE_PROVEN")
    if binding["SELECTED_SEMANTIC_UNIQUE"] is not True:
        raise Section1114OfflineSurfaceError("POS_SELECTED_SEMANTIC_MUST_BE_UNIQUE")
    if binding["NEW_PRODUCER_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    if binding["IMPLEMENTATION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    if downstream["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if downstream["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is not True:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_NOW_BE_ADJUDICABLE")
    if producer["PRODUCER_CONTRACT_COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError("PRODUCER_CONTRACT_MUST_BE_COMPLETE")
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
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": False,
        "POS_SEMANTICS": binding["POS_SEMANTICS"],
        "POS_SEMANTICS_STATUS": binding["POS_SEMANTICS_STATUS"],
        "POS_SEMANTICS_CANONICALLY_BOUND": binding["POS_SEMANTICS_CANONICALLY_BOUND"],
        "POS_CANONICAL_MEANING": binding["POS_CANONICAL_MEANING"],
        "POS_UNIT": binding["POS_UNIT"],
        "POS_SIGN_SEMANTICS": binding["POS_SIGN_SEMANTICS"],
        "POS_POS_SIDE_RELATION": binding["POS_POS_SIDE_RELATION"],
        "POS_POSITION_MODE_BINDING": binding["POS_POSITION_MODE_BINDING"],
        "POS_ACCOUNT_MODE_BINDING": binding["POS_ACCOUNT_MODE_BINDING"],
        "POS_TEMPORAL_MEANING": binding["POS_TEMPORAL_MEANING"],
        "SELECTED_SEMANTIC_ID": binding["SELECTED_SEMANTIC_ID"],
        "SELECTED_SEMANTIC_UNIQUE": binding["SELECTED_SEMANTIC_UNIQUE"],
        "REJECTED_SEMANTIC_CANDIDATE_COUNT": binding["REJECTED_SEMANTIC_CANDIDATE_COUNT"],
        "UNPROVEN_SEMANTIC_CANDIDATE_COUNT": binding["UNPROVEN_SEMANTIC_CANDIDATE_COUNT"],
        "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED": binding[
            "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED"
        ],
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "PRODUCER_ID": binding["PRODUCER_ID"],
        "PRODUCER_CONTRACT_COMPLETE": True,
        "SCHEMA_CHANGE_REQUIRED": False,
        "HANDOFF_SCHEMA_VERSION": binding["HANDOFF_SCHEMA_VERSION"],
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": True,
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
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
        "meaning_candidates": {"rows": binding["meaning_candidates"]},
        "what_restart_reconstructs": bind_what_restart_reconstructs_v1(),
        "unit_adjudication": bind_pos_unit_adjudication_v1(),
        "sign_adjudication": bind_pos_sign_adjudication_v1(),
        "account_mode_adjudication": bind_pos_account_mode_adjudication_v1(),
        "producer_contract": producer,
        "schema_version": bind_handoff_schema_version_v1(),
        "downstream": downstream,
        "claims": dict(CLAIMS),
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
