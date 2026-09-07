"""Execute contemporaneous pre-restart observability prove-or-refute persist.

No GET. No POST. No restart execution. No productive handoff write.
No historical canary rewrite. No timestamp backfill.
"""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_observation_v1 import (
    COMPLETE_CAPTURE_SEAM,
    MINIMUM_SAFE_OBSERVATION_CLASS,
    OBSERVATION_CASE,
    OBSERVATION_STATUS,
    PROPOSED_NEXT_SLICE,
    bind_contemporaneous_pre_restart_observability_adjudication_v1,
    bind_non_synthetic_observation_protocol_v1,
    bind_restart_boundary_for_contemporaneous_classification_v1,
    execute_minimum_safe_read_back_observation_v1,
    inventory_durable_write_point_and_provenance_v1,
    inventory_productive_pre_restart_capture_trigger_and_producer_v1,
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


def execute_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1(
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
    trigger = inventory_productive_pre_restart_capture_trigger_and_producer_v1()
    write_point = inventory_durable_write_point_and_provenance_v1()
    boundary = bind_restart_boundary_for_contemporaneous_classification_v1()
    protocol = bind_non_synthetic_observation_protocol_v1()
    if trigger["AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT"] is True:
        raise Section1114OfflineSurfaceError("UNAUTHORIZED_SURFACE_CLAIM")
    if protocol["PRODUCTIVE_WRITE_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_WRITE_MUST_REMAIN_UNAUTHORIZED")
    read_back = execute_minimum_safe_read_back_observation_v1(storage_root=repo_root)
    adjudication = bind_contemporaneous_pre_restart_observability_adjudication_v1(
        read_back=read_back
    )
    restart = dict(adjudication["restart_adjudication"])
    if restart.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if adjudication["COMPLETE_CAPTURE_SEAM"] != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is True:
        raise Section1114OfflineSurfaceError("CONTEMPORANEOUS_OBSERVATION_MUST_REMAIN_UNOBSERVED")
    if read_back["READER_RESULT"] != "MISSING_HANDOFF":
        raise Section1114OfflineSurfaceError("PRODUCTIVE_DURABLE_HANDOFF_MUST_REMAIN_ABSENT")
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
        "FIRST_OWNER_PRODUCTIVELY_BOUND": True,
        "POS_SEMANTICS": "PROVEN",
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "CAPTURE_TRIGGER_STATUS": trigger["CAPTURE_TRIGGER_STATUS"],
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
        "READER_IMPLEMENTED": True,
        "SELECTED_PRODUCTIVE_READER": protocol["READ_BACK_READER"],
        "RESTART_CONSUMER_SELECTED": protocol["CONSUMER"],
        "RESTART_CONSUMER_BOUND": True,
        "PROVENANCE_VALIDATION": adjudication["PROVENANCE_VALIDATION"],
        "FRESHNESS_VALIDATION": adjudication["FRESHNESS_VALIDATION"],
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
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": True,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "OBSERVATION_STATUS": OBSERVATION_STATUS,
        "CASE_ADJUDICATION": OBSERVATION_CASE,
        "MINIMUM_SAFE_OBSERVATION_CLASS": MINIMUM_SAFE_OBSERVATION_CLASS,
        "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
        "READ_BACK_EXECUTED": True,
        "READ_BACK_RESULT": read_back["READER_RESULT"],
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT": False,
        "PRODUCTIVE_RUNTIME_CALLER_COUNT": 0,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "IMPLEMENTATION_AUTHORIZED": False,
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
        "trigger": trigger,
        "write_point": write_point,
        "restart_boundary": boundary,
        "observation_protocol": protocol,
        "read_back": {
            "MINIMUM_SAFE_OBSERVATION_CLASS": read_back["MINIMUM_SAFE_OBSERVATION_CLASS"],
            "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
            "READ_BACK_EXECUTED": True,
            "READER_RESULT": read_back["READER_RESULT"],
            "READER_REASON": read_back["READER_REASON"],
            "CONSUMER_ACCEPTED": read_back["CONSUMER_ACCEPTED"],
            "CONSUMER_REASON": read_back["CONSUMER_REASON"],
            "DURABLE_PATH": read_back["DURABLE_PATH"],
            "GET_PERFORMED": False,
            "VENUE_GET_FALLBACK": False,
            "EVIDENCE_PACK_FALLBACK": False,
        },
        "seam_predicate": {
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "MISSING_PREDICATES": list(adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]),
            "PREDICATES": dict(adjudication["COMPLETE_CAPTURE_SEAM_PREDICATES"]),
        },
        "observability_adjudication": {
            "OBSERVATION_STATUS": OBSERVATION_STATUS,
            "CASE_ADJUDICATION": OBSERVATION_CASE,
            "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "LIVE_RESTART_RECONSTRUCTED": False,
        },
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": origin_main_sha == EXPECTED_ORIGIN_MAIN_SHA,
            "OWNER_GO": OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1",
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
            "paths": [
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/constants_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/__init__.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_contemporaneous_pre_restart_observation_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_contemporaneous_pre_restart_observation_execute_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_reader_bind_execute_v1.py",
                "scripts/ops/run_section_11_14_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind_v1.py",
                "tests/ops/test_section_11_14_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1.py",
                "tests/ops/test_section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind_v1.py",
                "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_persist_v1.py",
                "docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1.md",
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
            "IMPLEMENTATION_AUTHORIZED": False,
            "NEXT_SLICE_AUTHORIZED": False,
            "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
        },
        "claims": dict(CLAIMS),
        "adjudication": restart,
        "binding": dict(adjudication["reader_binding"]),
        "pack": str(pack),
        "raw_exchanges": [],
    }
