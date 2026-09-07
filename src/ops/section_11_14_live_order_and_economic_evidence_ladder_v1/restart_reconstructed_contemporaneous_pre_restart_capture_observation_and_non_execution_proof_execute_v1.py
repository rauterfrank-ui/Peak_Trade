"""Execute contemporaneous PRE-RESTART observation non-execution persist.

No GET. No POST. No restart execution. No productive contemporaneous capture.
No Live/canary/testnet activation. Isolation from live execution remains false.
Observation is adjudicated NOT_EXECUTED. HOST_CRASH_DURABILITY remains UNPROVEN.
LIVE_RESTART_RECONSTRUCTED remains false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    PRODUCTIVE_HOOK_CALLER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO,
    HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_RUN_ID,
    HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA,
    LADDER_FIELD_DEFAULTS,
    LIVE_RESTART_RECONSTRUCTED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1 import (
    COMPLETE_CAPTURE_SEAM,
    NO_BACKFILL_CONTRACT_PROVEN,
    PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL,
    REQUIRED_FIELD_PROVENANCE_COMPLETE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1 import (
    AUTHORIZATION_MATRIX_STATUS,
    CAPTURE_POINT,
    CASE_ADJUDICATION,
    CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PROPOSED_NEXT_SLICE,
    bind_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)


def execute_live_handoff_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    if (
        str(owner_go or "").strip()
        != HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO
    ):
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if (
        str(origin_main_sha or "").strip()
        != HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA
    ):
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_RUN_ID)
    adjudication = bind_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1(
        repo_root=repo_root,
        storage_root=storage_root,
    )
    if adjudication["COMPLETE_CAPTURE_SEAM"] != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_REMAIN_PROVEN")
    if adjudication["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is not True:
        raise Section1114OfflineSurfaceError("NO_BACKFILL_CONTRACT_UNPROVEN")
    if adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if adjudication["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    if adjudication["CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION"] != "NOT_EXECUTED":
        raise Section1114OfflineSurfaceError("OBSERVATION_MUST_REMAIN_NOT_EXECUTED")
    if adjudication["LIVE_RESTART_RECONSTRUCTED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        **dict(LADDER_FIELD_DEFAULTS),
        "OWNER_GO": HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO,
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
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "PRODUCTIVE_CAPTURE_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": True,
        "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": True,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "CAPTURE_POINT": CAPTURE_POINT,
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE": "PROVEN",
        "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY": "PROVEN",
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_REPROVEN": "PROVEN",
        "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY_REPROVEN": "PROVEN",
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
        "CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE": True,
        "AUTHORIZATION_MATRIX_STATUS": AUTHORIZATION_MATRIX_STATUS,
        "NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CAPTURE_TIMESTAMP": None,
        "CAPTURE_ARTIFACT_ID": None,
        "CAPTURE_ARTIFACT_HASH": None,
        "CAPTURE_PROVENANCE_VALIDATED": False,
        "BACKFILL_USED": False,
        "RETROACTIVE_SYNTHESIS_USED": False,
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
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
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
        "entrypoints": dict(adjudication["entrypoints"]),
        "callgraph": dict(adjudication["callgraph"]),
        "timeline": dict(adjudication["timeline"]),
        "side_effects": dict(adjudication["side_effects"]),
        "gates": dict(adjudication["gates"]),
        "inputs": dict(adjudication["inputs"]),
        "isolation": dict(adjudication["isolation"]),
        "authorization_matrix": dict(adjudication["authorization_matrix"]),
        "observation_admissibility": dict(adjudication["observation_admissibility"]),
        "non_execution": dict(adjudication["non_execution"]),
        "host_graph": dict(adjudication["host_graph"]),
        "call_path": dict(adjudication["call_path"]),
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": (
                HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA
            ),
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": (
                origin_main_sha == HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA
            ),
            "OWNER_GO": HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": (
                "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_"
                "OBSERVATION_AND_NON_EXECUTION_PROOF_V1"
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
            "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": "NOT_EXECUTED",
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
            "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
            "COMPLETE_CAPTURE_SEAM": "PROVEN",
            "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": True,
            "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
            "LIVE_RESTART_RECONSTRUCTED": False,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
            "LIVE_SUBMIT_EXECUTED": False,
            "WIRE_SEND_EXECUTED": False,
            "RESTART_EXECUTED": False,
            "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        },
        "claims": dict(CLAIMS),
        "adjudication": dict(adjudication),
        "pack": str(pack),
        "raw_exchanges": [],
    }
