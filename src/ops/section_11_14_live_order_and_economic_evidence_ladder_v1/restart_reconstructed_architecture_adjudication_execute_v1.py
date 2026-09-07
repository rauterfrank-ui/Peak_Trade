"""Execute architecture adjudication persist. No GET. No POST. No writer join."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_and_capture_architecture_adjudication_v1 import (
    bind_capture_seam_graph_census_v1,
    bind_durability_contract_adjudication_v1,
    bind_owner_and_capture_architecture_adjudication_v1,
    bind_owner_contract_adjudication_v1,
    bind_pos_semantics_adjudication_v1,
    bind_proposed_slice_sequence_v1,
    bind_restart_admission_predicate_v1,
    bind_step_29p_handoff_relation_v1,
    bind_writer_reader_contract_adjudication_v1,
)


def execute_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    architecture = bind_owner_and_capture_architecture_adjudication_v1()
    owner = bind_owner_contract_adjudication_v1()
    pos = bind_pos_semantics_adjudication_v1()
    seams = bind_capture_seam_graph_census_v1()
    durability = bind_durability_contract_adjudication_v1()
    writer_reader = bind_writer_reader_contract_adjudication_v1()
    admission = bind_restart_admission_predicate_v1()
    step_29p = bind_step_29p_handoff_relation_v1()
    sequence = bind_proposed_slice_sequence_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if architecture["ADMISSION_TRUE"] is True:
        raise Section1114OfflineSurfaceError("ADMISSION_TRUE_MUST_REMAIN_FALSE")
    if architecture["IMPLEMENTATION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO,
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
        "PROPOSED_FIRST_OWNER_ID": architecture["PROPOSED_FIRST_OWNER_ID"],
        "PROPOSED_FIRST_OWNER_ADJUDICATION": architecture["PROPOSED_FIRST_OWNER_ADJUDICATION"],
        "FIRST_OWNER_CONTRACT_DECLARED": architecture["FIRST_OWNER_CONTRACT_DECLARED"],
        "FIRST_OWNER_PRODUCTIVELY_BOUND": architecture["FIRST_OWNER_PRODUCTIVELY_BOUND"],
        "POS_SEMANTICS": architecture["POS_SEMANTICS"],
        "POS_ACCEPTABLE_PRODUCER_COUNT": architecture["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": architecture[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT"
        ],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": architecture[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM"
        ],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": architecture[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN"
        ],
        "COMPLETE_CAPTURE_SEAM": architecture["COMPLETE_CAPTURE_SEAM"],
        "HOST_CRASH_DURABILITY": architecture["HOST_CRASH_DURABILITY"],
        "POWER_LOSS_DURABILITY": architecture["POWER_LOSS_DURABILITY"],
        "DURABILITY_PROVEN_EFFECTIVE": architecture["DURABILITY_PROVEN_EFFECTIVE"],
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "STEP_29P_EQUITY_DIMENSION_BINDING_STATUS": architecture[
            "STEP_29P_EQUITY_DIMENSION_BINDING_STATUS"
        ],
        "STEP_29P_HANDOFF_RELATION": architecture["STEP_29P_HANDOFF_RELATION"],
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "ARCHITECTURE_ADJUDICATION_COMPLETE": True,
        "IMPLEMENTATION_AUTHORIZED": False,
        "MINIMAL_SAFE_ARCHITECTURE": architecture["MINIMAL_SAFE_ARCHITECTURE"],
        "PROPOSED_NEXT_SLICE": architecture["PROPOSED_NEXT_SLICE"],
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
        "architecture": architecture,
        "owner": owner,
        "pos": pos,
        "seams": seams,
        "durability": durability,
        "writer_reader": writer_reader,
        "admission": admission,
        "step_29p": step_29p,
        "sequence": sequence,
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
