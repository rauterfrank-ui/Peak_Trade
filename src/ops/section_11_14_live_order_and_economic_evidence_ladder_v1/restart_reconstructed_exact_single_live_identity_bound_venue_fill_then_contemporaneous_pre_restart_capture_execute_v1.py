"""Execute exact-single fill then PRE-RESTART capture persist.

No GET. No POST. No wire send. No submit. No position mutation. No restart.
No standing Live-gate mutation. No credential use. Historical fill and
TEST_FIXTURE remain inadmissible. The capture-hook code gap is proven and
the invocation-scoped repair seam is proven offline. Slice-level
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED remains false. This GO does
not authorize merge of the repair or subsequent Live execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ADJUDICATION_FILENAME,
    CANONICAL_EVIDENCE_RUN_ID,
    CAPTURE_SEAM_REPAIR_FILENAME,
    CLAIMS_FILENAME,
    CODE_GAP_FILENAME,
    CONTEMPORANEOUS_GATE_MATRIX_FILENAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    FILL_PRODUCER_CALL_PATH_FILENAME,
    FUTURE_OWNER_GO_CONTRACT_FILENAME,
    LADDER_FIELD_DEFAULTS,
    LIVE_FILL_READINESS_MATRIX_FILENAME,
    LIVE_RESTART_RECONSTRUCTED,
    MINIMAL_ECONOMIC_ACTION_CONTRACT_FILENAME,
    OWNER_GO,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    SUMMARY_FILENAME,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    persist_offline_surface_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1 import (
    COMPLETE_CAPTURE_SEAM,
    NO_BACKFILL_CONTRACT_PROVEN,
    PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL,
    REQUIRED_FIELD_PROVENANCE_COMPLETE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1 import (
    CASE_ADJUDICATION,
    CODE_GAP_ID,
    LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
    PROPOSED_NEXT_SLICE,
    TERMINAL_STATE,
    bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1,
)


AFTER_REPAIR_OWNER_GO_PROPOSED_TOKEN = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_"
    "LIVE_IDENTITY_BOUND_VENUE_FILL_THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_"
    "AFTER_CAPTURE_SEAM_REPAIR_V1"
)
AFTER_REPAIR_OWNER_GO_SCOPE = (
    "EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_THEN_CONTEMPORANEOUS_"
    "PRE_RESTART_CAPTURE_AFTER_CAPTURE_SEAM_REPAIR_NO_RESTART_NO_GATE_BYPASS"
)


def execute_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    adjudication = bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
        repo_root=repo_root,
        storage_root=storage_root,
    )
    if adjudication["TERMINAL_STATE"] != TERMINAL_STATE:
        raise Section1114OfflineSurfaceError("TERMINAL_STATE_DRIFT")
    if adjudication["LIVE_FILL_READINESS"] is True:
        raise Section1114OfflineSurfaceError("READINESS_MUST_REMAIN_FALSE")
    if adjudication["LIVE_SUBMIT_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("SUBMIT_MUST_NOT_BE_EXECUTED")
    if adjudication["WIRE_SEND_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("WIRE_SEND_MUST_NOT_BE_EXECUTED")
    if adjudication["POSITION_MUTATION_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("POSITION_MUTATION_MUST_NOT_BE_EXECUTED")
    if adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if adjudication["LIVE_RESTART_RECONSTRUCTED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    future_go = {
        "DOCUMENT_CLASS": "SECTION_11_14_FUTURE_OWNER_GO_CONTRACT_V1",
        "FUTURE_EXECUTION_OWNER_GO_REQUIRED": True,
        "FUTURE_EXECUTION_OWNER_GO_SCOPE": AFTER_REPAIR_OWNER_GO_SCOPE,
        "FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN": AFTER_REPAIR_OWNER_GO_PROPOSED_TOKEN,
        "CONSUMED_BY_THIS_GO": False,
        "FAIL_CLOSED": True,
        "NEXT_SLICE_AUTHORIZED": False,
        "REPAIR_MERGE_AUTHORIZED_BY_THIS_GO": False,
        "LIVE_SUBMIT_AUTHORIZED_BY_THIS_GO": False,
        "RESTART_AUTHORIZED_BY_THIS_GO": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
    }
    summary = {
        **dict(LADDER_FIELD_DEFAULTS),
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
        "COMPLETE_CAPTURE_SEAM": "PROVEN",
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": (
            PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL
        ),
        "NO_BACKFILL_CONTRACT_PROVEN": NO_BACKFILL_CONTRACT_PROVEN,
        "REQUIRED_FIELD_PROVENANCE_COMPLETE": REQUIRED_FIELD_PROVENANCE_COMPLETE,
        "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": True,
        "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND": True,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_REQUIRED": True,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER": LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
        "LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN": True,
        "LIVE_FILL_READINESS_MATRIX_STATUS": "COMPLETE",
        "LIVE_FILL_READINESS": False,
        "BLOCKING_GATE_COUNT": adjudication["BLOCKING_GATE_COUNT"],
        "BLOCKING_GATES": list(adjudication["BLOCKING_GATES"]),
        "MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS": "BLOCKED",
        "EXACT_ECONOMIC_ACTION_CONTRACT_STATUS": "BLOCKED",
        "VENUE": adjudication["VENUE"],
        "INSTRUMENT_ID": adjudication["INSTRUMENT_ID"],
        "SIDE": adjudication["SIDE"],
        "ORDER_TYPE": adjudication["ORDER_TYPE"],
        "ORDER_QTY": adjudication["ORDER_QTY"],
        "EXECUTION_LIMIT_PRICE": "UNKNOWN",
        "EXECUTION_MAX_NOTIONAL": "UNKNOWN",
        "MAX_POSITIONS": adjudication["EXECUTION_MAX_POSITIONS"],
        "CODE_CHANGE_REQUIRED": True,
        "CODE_GAP_ID": CODE_GAP_ID,
        "TERMINAL_STATE": TERMINAL_STATE,
        "LIVE_FILL_EXECUTION_AUTHORIZED": False,
        "LIVE_FILL_EXECUTED": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": "NOT_EXECUTED",
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_INJECTION_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "LIVE_ENABLED_MUTATED": False,
        "LIVE_ARMED_MUTATED": False,
        "HOST_CRASH_EXECUTED": False,
        "TESTNET_EXECUTED": False,
        "CANARY_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "IMPLEMENTATION_AUTHORIZED": True,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "SECRET_VALUES_INCLUDED": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "FUTURE_EXECUTION_OWNER_GO_REQUIRED": True,
        "FUTURE_EXECUTION_OWNER_GO_SCOPE": AFTER_REPAIR_OWNER_GO_SCOPE,
        "FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN": AFTER_REPAIR_OWNER_GO_PROPOSED_TOKEN,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "NEXT_SLICE_AUTHORIZED": False,
        "REPAIR_MERGE_AUTHORIZED": False,
        "repo_root": str(repo_root),
    }
    pack = (
        repo_root
        / "evidence"
        / "ops"
        / "section_11_14_live_order_and_economic_evidence_ladder_v1"
        / pack_run_id
    )
    return {
        "summary": summary,
        "producer": dict(adjudication["producer"]),
        "readiness_matrix": dict(adjudication["readiness_matrix"]),
        "economic_contract": dict(adjudication["economic_contract"]),
        "code_gap": dict(adjudication["code_gap"]),
        "future_execution_go": future_go,
        "non_execution": dict(adjudication["non_execution"]),
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": origin_main_sha == EXPECTED_ORIGIN_MAIN_SHA,
            "OWNER_GO": OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": (
                "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_"
                "VENUE_FILL_THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_V1"
            ),
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
        },
        "safety": {
            "LIVE_ENABLED": False,
            "LIVE_ARMED": False,
            "CANARY_AUTHORIZED": False,
            "GET_PERFORMED": False,
            "POST_USED": False,
            "WIRE_SEND": False,
            "LIVE_ACTION": "NONE",
            "CREDENTIAL_USE": False,
            "IMPLEMENTATION_AUTHORIZED": True,
            "NEXT_SLICE_AUTHORIZED": False,
            "LIVE_FILL_READINESS": False,
            "LIVE_FILL_EXECUTION_AUTHORIZED": False,
            "LIVE_FILL_EXECUTED": False,
            "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": "NOT_EXECUTED",
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
            "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
            "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
            "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": True,
            "LIVE_RESTART_RECONSTRUCTED": False,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
            "LIVE_SUBMIT_EXECUTED": False,
            "WIRE_SEND_EXECUTED": False,
            "RESTART_EXECUTED": False,
            "OWNER_GO_IS_NOT_GATE_BYPASS": True,
            "TERMINAL_STATE": TERMINAL_STATE,
            "CODE_CHANGE_REQUIRED": True,
            "REPAIR_MERGE_AUTHORIZED": False,
        },
        "claims": dict(CLAIMS),
        "adjudication": dict(adjudication),
        "pack": str(pack),
        "raw_exchanges": [],
    }


def documents_for_exact_single_bound_fill_then_pre_restart_capture_pack_v1(
    *,
    result: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        SUMMARY_FILENAME: dict(result["summary"]),
        CLAIMS_FILENAME: dict(result["claims"]),
        ADJUDICATION_FILENAME: dict(result["adjudication"]),
        "SAFETY.json": dict(result["safety"]),
        "BASELINE.json": dict(result["baseline"]),
        "CHANGED_PATH_CENSUS.json": dict(result["changed_path_census"]),
        FILL_PRODUCER_CALL_PATH_FILENAME: dict(result["producer"]),
        LIVE_FILL_READINESS_MATRIX_FILENAME: dict(result["readiness_matrix"]),
        CONTEMPORANEOUS_GATE_MATRIX_FILENAME: dict(result["readiness_matrix"]),
        MINIMAL_ECONOMIC_ACTION_CONTRACT_FILENAME: dict(result["economic_contract"]),
        CODE_GAP_FILENAME: dict(result["code_gap"]),
        CAPTURE_SEAM_REPAIR_FILENAME: dict(result["code_gap"]["semantics"]),
        FUTURE_OWNER_GO_CONTRACT_FILENAME: dict(result["future_execution_go"]),
        "NON_EXECUTION.json": dict(result["non_execution"]),
    }


def persist_exact_single_bound_fill_then_pre_restart_capture_pack_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    result = execute_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=run_id,
    )
    pack = Path(str(result["pack"]))
    verified = persist_offline_surface_pack_v1(
        pack=pack,
        origin_main_sha=origin_main_sha,
        documents=documents_for_exact_single_bound_fill_then_pre_restart_capture_pack_v1(
            result=result
        ),
    )
    result["manifest"] = dict(verified)
    return result
