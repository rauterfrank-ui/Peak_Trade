"""Execute create-productive-capture-owner persist.

No GET. No POST. No restart execution. No productive handoff write during
this persist. No historical canary rewrite. No timestamp backfill.
CASE_A_CREATED: unique owner and hook structurally bound; runtime
execution remains unauthorized.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_RUN_ID,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    AUTHORIZED_RUNTIME_SURFACE,
    AUTHORIZED_RUNTIME_SURFACE_PROVEN,
    BINDING_CASE,
    BOUND_FILL_BEFORE_HOOK_PROVEN,
    CASE_ADJUDICATION,
    CAPTURE_WINDOW_TIMESTAMP_ORDERING,
    CURRENT_RUNTIME_EXECUTION_AUTHORIZED,
    FUTURE_BOUND_IDENTITY_PARAMETERIZATION,
    HOOK_BEFORE_RESTART_PROVEN,
    HOOK_ORDERING_PROVEN,
    MISSING_PREDICATES,
    PRODUCTIVE_BINDING_IMPLEMENTED,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_CAPTURE_OWNER_UNIQUE,
    PRODUCTIVE_LIFECYCLE_HOOK,
    PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE,
    PRODUCTIVE_S05_QTY_SOURCE,
    PRODUCTIVE_S05_QTY_SOURCE_PROVEN,
    PROPOSED_NEXT_SLICE,
    REQUIRED_NEXT_AUTHORITY,
    STRUCTURAL_RUNTIME_BINDING_PROVEN,
    bind_create_productive_capture_owner_and_lifecycle_hook_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    SELECTED_SEMANTIC_ID,
)


def execute_live_handoff_create_productive_capture_owner_and_lifecycle_hook_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_RUN_ID)
    adjudication = bind_create_productive_capture_owner_and_lifecycle_hook_v1(repo_root=repo_root)
    if adjudication["BINDING_CASE"] != BINDING_CASE:
        raise Section1114OfflineSurfaceError("BINDING_CASE_MUST_REMAIN_CASE_A_CREATED")
    if adjudication["PRODUCTIVE_BINDING_IMPLEMENTED"] is not True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_BE_IMPLEMENTED")
    if adjudication["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is True:
        raise Section1114OfflineSurfaceError("CONTEMPORANEOUS_OBSERVATION_MUST_REMAIN_UNOBSERVED")
    if adjudication["LIVE_RESTART_RECONSTRUCTED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if CURRENT_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    census = dict(adjudication["owner_hook_census"])
    graph = dict(census["caller_graph"])
    surfaces = dict(adjudication["authorization_surfaces"])
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
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
        "FIRST_OWNER_PRODUCTIVELY_BOUND": True,
        "POS_SEMANTICS": "PROVEN",
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "CAPTURE_TRIGGER_STATUS": "REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_BOUND",
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": True,
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": False,
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "STORAGE_OWNER_MINTED": True,
        "SELECTED_STORAGE_OWNER": FIRST_OWNER_ID,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "READER_BOUND": True,
        "RESTART_CONSUMER_BOUND": True,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": True,
        "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
        "HOST_CRASH_PROOF": "UNPROVEN",
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "POWER_LOSS_DURABILITY": "UNPROVEN",
        "DURABILITY_PROVEN_EFFECTIVE": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": list(
            adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
        ),
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": False,
        "OBSERVATION_STATUS": "STRUCTURAL_BINDING_CREATED_NOT_LIVE_OBSERVED",
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "BINDING_CASE": BINDING_CASE,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_UNIQUE": PRODUCTIVE_CAPTURE_OWNER_UNIQUE,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE": PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE,
        "HOOK_ORDERING_PROVEN": HOOK_ORDERING_PROVEN,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": BOUND_FILL_BEFORE_HOOK_PROVEN,
        "HOOK_BEFORE_RESTART_PROVEN": HOOK_BEFORE_RESTART_PROVEN,
        "CAPTURE_WINDOW_TIMESTAMP_ORDERING": CAPTURE_WINDOW_TIMESTAMP_ORDERING,
        "FUTURE_BOUND_IDENTITY_PARAMETERIZATION": FUTURE_BOUND_IDENTITY_PARAMETERIZATION,
        "PRODUCTIVE_S05_QTY_SOURCE": PRODUCTIVE_S05_QTY_SOURCE,
        "PRODUCTIVE_S05_QTY_SOURCE_PROVEN": PRODUCTIVE_S05_QTY_SOURCE_PROVEN,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": STRUCTURAL_RUNTIME_BINDING_PROVEN,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": AUTHORIZED_RUNTIME_SURFACE,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": AUTHORIZED_RUNTIME_SURFACE_PROVEN,
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER": graph[
            "PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT"
        ],
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER": graph[
            "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT"
        ],
        "PRODUCTIVE_BINDING_IMPLEMENTED": True,
        "PRODUCTIVE_BINDING_FAIL_CLOSED": True,
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT": False,
        "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
        "HANDOFF_WRITTEN": False,
        "RESTART_EXECUTED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "IMPLEMENTATION_AUTHORIZED": True,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "SECRET_VALUES_INCLUDED": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "RAW_EVIDENCE_MODIFIED": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "repo_root": str(repo_root),
    }
    pack = (
        repo_root
        / "evidence"
        / "ops"
        / ("section_11_14_live_order_and_economic_evidence_ladder_v1")
        / pack_run_id
    )
    return {
        "summary": summary,
        "caller_graph": graph,
        "owner_hook_census": census,
        "authorization_surfaces": surfaces,
        "seam_predicate": {
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "MISSING_PREDICATES": list(adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]),
        },
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": (
                origin_main_sha == HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA
            ),
            "OWNER_GO": HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": "SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1",
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
            "paths": [
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/constants_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/__init__.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_pos_producer_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_owner_and_writer_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_validators_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_future_authorized_contemporaneous_capture_window_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_productive_capture_owner_and_lifecycle_hook_binding_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_productive_capture_owner_and_lifecycle_hook_binding_execute_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_execute_v1.py",
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_restart_handoff_capture_hook_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_create_productive_capture_owner_and_lifecycle_hook_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1.py",
                "tests/ops/test_section_11_14_live_handoff_create_productive_capture_owner_and_lifecycle_hook_v1.py",
                "tests/ops/test_section_11_14_live_handoff_future_authorized_contemporaneous_capture_window_v1.py",
                "tests/ops/test_section_11_14_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1.py",
                "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_persist_v1.py",
                "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1.md",
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
                "docs/system_atlas/entities/catalog.yaml",
                "docs/system_atlas/relations/runtime.yaml",
            ],
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
            "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
            "PRODUCTIVE_BINDING_IMPLEMENTED": True,
            "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
            "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        },
        "claims": dict(CLAIMS),
        "adjudication": dict(adjudication),
        "pack": str(pack),
        "raw_exchanges": [],
    }
