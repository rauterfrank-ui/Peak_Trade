"""Execute future-authorized contemporaneous capture-window persist.

No GET. No POST. No restart execution. No productive handoff write.
No historical canary rewrite. No timestamp backfill. No runtime join.
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    CASE_ADJUDICATION,
    COMPLETE_CAPTURE_SEAM,
    MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE,
    MISSING_PREDICATES,
    PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE,
    PRODUCTIVE_BINDING_IMPLEMENTED,
    PRODUCTIVE_CAPTURE_HOOK,
    PRODUCTIVE_CAPTURE_HOOK_STATUS,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_CAPTURE_OWNER_STATUS,
    PROPOSED_NEXT_SLICE,
    REQUIRED_NEXT_AUTHORITY,
    bind_future_authorized_contemporaneous_capture_window_v1,
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


def execute_live_handoff_future_authorized_contemporaneous_capture_window_v1(
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
    adjudication = bind_future_authorized_contemporaneous_capture_window_v1(repo_root=repo_root)
    if adjudication["PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_FORBIDDEN")
    if adjudication["PRODUCTIVE_BINDING_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_UNIMPLEMENTED")
    if adjudication["COMPLETE_CAPTURE_SEAM"] != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is True:
        raise Section1114OfflineSurfaceError("CONTEMPORANEOUS_OBSERVATION_MUST_REMAIN_UNOBSERVED")
    if adjudication["LIVE_RESTART_RECONSTRUCTED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_FORBIDDEN")
    if PRODUCTIVE_BINDING_IMPLEMENTED is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_UNIMPLEMENTED")
    graph = dict(adjudication["runtime_graph"])
    bound_fill = dict(adjudication["bound_fill"])
    window = dict(adjudication["capture_window"])
    minimum = dict(adjudication["minimum_future_window"])
    decision = dict(adjudication["binding_decision"])
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
        "OBSERVATION_STATUS": "CLOSED_REFUTED",
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "BOUND_FILL_CANONICAL_SYMBOL": bound_fill["BOUND_FILL_CANONICAL_SYMBOL"],
        "BOUND_FILL_IS_PRODUCTIVE_RUNTIME_EVENT": True,
        "BOUND_FILL_REQUIRES_VENUE_ACK": True,
        "BOUND_FILL_REQUIRES_WIRE_SEND": True,
        "BOUND_FILL_CAN_EXIST_OFFLINE": False,
        "BOUND_FILL_CAN_EXIST_IN_SHADOW": False,
        "BOUND_FILL_CAN_EXIST_IN_TESTNET": False,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "PRODUCTIVE_CAPTURE_HOOK": PRODUCTIVE_CAPTURE_HOOK,
        "PRODUCTIVE_CAPTURE_HOOK_STATUS": PRODUCTIVE_CAPTURE_HOOK_STATUS,
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER": graph[
            "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_emit_s05_handoff_pos_v1"
        ],
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER": graph[
            "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_commit_handoff_after_bound_fill_before_restart_v1"
        ],
        "CAPTURE_WINDOW_ORDERING": window["CAPTURE_WINDOW_ORDERING"],
        "MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE": MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE,
        "MINIMUM_REQUIRED_RUNTIME": minimum["MINIMUM_REQUIRED_RUNTIME"],
        "MINIMUM_REQUIRED_OWNER_AUTHORITY": minimum["MINIMUM_REQUIRED_OWNER_AUTHORITY"],
        "LIVE_ENABLED_REQUIRED": True,
        "LIVE_ARMED_REQUIRED": True,
        "CANARY_AUTHORIZED_REQUIRED": True,
        "ORDER_SUBMIT_GO_REQUIRED": True,
        "WIRE_SEND_REQUIRED": True,
        "VENUE_FILL_REQUIRED": True,
        "PRIVATE_GET_REQUIRED": True,
        "NETWORK_AUTH_REQUIRED": True,
        "CREDENTIAL_ACCESS_REQUIRED": True,
        "PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE": False,
        "PRODUCTIVE_BINDING_IMPLEMENTED": False,
        "PRODUCTIVE_BINDING_FAIL_CLOSED": False,
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
        "runtime_graph": graph,
        "bound_fill": bound_fill,
        "capture_window": window,
        "authorization_surfaces": dict(adjudication["authorization_surfaces"]),
        "minimum_future_window": minimum,
        "binding_decision": decision,
        "seam_predicate": {
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "MISSING_PREDICATES": list(adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]),
        },
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": origin_main_sha == EXPECTED_ORIGIN_MAIN_SHA,
            "OWNER_GO": OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": "SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1",
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
            "paths": [
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/constants_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/__init__.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_contemporaneous_pre_restart_observation_execute_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_future_authorized_contemporaneous_capture_window_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_future_authorized_contemporaneous_capture_window_execute_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_future_authorized_contemporaneous_capture_window_v1.py",
                "tests/ops/test_section_11_14_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1.py",
                "tests/ops/test_section_11_14_live_handoff_future_authorized_contemporaneous_capture_window_v1.py",
                "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_persist_v1.py",
                "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1.md",
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
            "PRODUCTIVE_BINDING_IMPLEMENTED": False,
        },
        "claims": dict(CLAIMS),
        "adjudication": dict(adjudication),
        "pack": str(pack),
        "raw_exchanges": [],
    }
