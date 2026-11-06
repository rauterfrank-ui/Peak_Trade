"""Bind the unique productive capture-hook caller and prove the offline call path.

Closes PRODUCTIVE_HOOK_CALLER=UNPROVEN_NO_PRODUCTIVE_HOOK_CALLER without
executing Live, GET, POST, wire send, restart, or contemporaneous productive
capture. COMPLETE_CAPTURE_SEAM remains UNPROVEN.
PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL remains false because the
bound seam predicate still requires empirical productive observation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_RELPATH,
    HOST_JOIN_SYMBOL,
    PRODUCTIVE_HOOK_CALLER,
    PRODUCTIVE_LIFECYCLE_EVENT,
    compose_live_order_pre_restart_capture_host_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    COMPLETE_CAPTURE_SEAM,
    COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND,
    REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND,
    bind_required_field_provenance_matrix_v1,
    census_productive_capture_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    census_create_caller_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    census_symbol_call_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)

PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN = True
PRODUCTIVE_CALL_PATH_OFFLINE_PROOF = True
PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL = False
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED = False
CASE_ADJUDICATION = (
    "CASE_PRODUCTIVE_HOOK_CALLER_BOUND_OFFLINE_CALL_PATH_PROVEN_"
    "COMPLETE_CAPTURE_SEAM_REMAINS_UNPROVEN"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)


def require_unique_productive_hook_caller_census_v1(
    *,
    productive_runtime_caller_count: object,
) -> None:
    count = int(productive_runtime_caller_count or 0)
    if count == 0:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")
    if count > 1:
        raise Section1114OfflineSurfaceError("MULTIPLE_PRODUCTIVE_HOOK_CALLERS_FORBIDDEN")


def require_production_graph_contains_unique_caller_v1(
    *,
    graph: Mapping[str, Any],
) -> None:
    caller_nodes = [
        row
        for row in list(graph.get("nodes") or [])
        if row.get("id") == "PRODUCTIVE_HOOK_CALLER" and row.get("symbol")
    ]
    if len(caller_nodes) != 1:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")
    if str(graph.get("PRODUCTIVE_HOOK_CALLER") or "").strip() != PRODUCTIVE_HOOK_CALLER:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")


def census_productive_hook_caller_v1(*, repo_root: Path) -> dict[str, Any]:
    hook = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=PRODUCTIVE_LIFECYCLE_HOOK,
        definition_relpath=HOOK_RELPATH,
    )
    caller = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=PRODUCTIVE_HOOK_CALLER,
        definition_relpath=CALLER_RELPATH,
    )
    host = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=HOST_JOIN_SYMBOL,
        definition_relpath=HOST_JOIN_RELPATH,
    )
    productive_hook = [
        row for row in hook["rows"] if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    require_unique_productive_hook_caller_census_v1(
        productive_runtime_caller_count=hook["PRODUCTIVE_RUNTIME_CALLER_COUNT"]
    )
    if productive_hook[0]["FILE"] != CALLER_RELPATH:
        raise Section1114OfflineSurfaceError("HOOK_PRODUCTIVE_CALLER_MUST_BE_UNIQUE_CALLER")
    productive_caller = [
        row for row in caller["rows"] if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    require_unique_productive_hook_caller_census_v1(
        productive_runtime_caller_count=caller["PRODUCTIVE_RUNTIME_CALLER_COUNT"]
    )
    if productive_caller[0]["FILE"] != HOST_JOIN_RELPATH:
        raise Section1114OfflineSurfaceError("CALLER_HOST_JOIN_MUST_BE_RUNNER")
    if host["PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("HOST_JOIN_MUST_NOT_HAVE_NESTED_PRODUCTIVE_CALLER")
    writer_graph = census_create_caller_graph_v1(repo_root=repo_root)
    if writer_graph["WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 1:
        raise Section1114OfflineSurfaceError("WRITER_MUST_HAVE_EXACTLY_ONE_PRODUCTIVE_CALLER")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_HOOK_CALLER_CENSUS_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_UNIQUE": True,
        "PRODUCTIVE_LIFECYCLE_EVENT": PRODUCTIVE_LIFECYCLE_EVENT,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "HOOK_PRODUCTIVE_RUNTIME_CALLER_COUNT": hook["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "CALLER_PRODUCTIVE_RUNTIME_CALLER_COUNT": caller["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "HOST_JOIN_PRODUCTIVE_RUNTIME_CALLER_COUNT": host["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "hook_census": hook,
        "caller_census": caller,
        "host_join_census": host,
        "writer_graph": {
            "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT": writer_graph[
                "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT"
            ],
            "EXACTLY_ONE_PRODUCTIVE_WRITER_CALLER": writer_graph[
                "EXACTLY_ONE_PRODUCTIVE_WRITER_CALLER"
            ],
        },
    }


def bind_productive_capture_hook_caller_and_offline_call_path_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    census = census_productive_hook_caller_v1(repo_root=repo_root)
    graph = compose_live_order_pre_restart_capture_host_graph_v1()
    dataflow = census_productive_capture_dataflow_v1(repo_root=repo_root)
    matrix = bind_required_field_provenance_matrix_v1()
    reader_binding = bind_restart_reader_provenance_and_consumer_v1()
    require_unique_productive_hook_caller_census_v1(
        productive_runtime_caller_count=census["HOOK_PRODUCTIVE_RUNTIME_CALLER_COUNT"]
    )
    require_unique_productive_hook_caller_census_v1(
        productive_runtime_caller_count=dataflow["HOOK_PRODUCTIVE_CALLER_COUNT"]
    )
    if dataflow["UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK"] != "PROVEN":
        raise Section1114OfflineSurfaceError("UPSTREAM_HOOK_JOIN_MUST_BE_PROVEN")
    require_production_graph_contains_unique_caller_v1(graph=graph)
    missing = list(reader_binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    if reader_binding["COMPLETE_CAPTURE_SEAM"] != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if LIVE_ENABLED is True or LIVE_ARMED is True or CANARY_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True or ORDER_SUBMIT_ALLOWED is True:
        raise Section1114OfflineSurfaceError("SUBMIT_MUST_REMAIN_FORBIDDEN")
    if CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_"
            "AND_OFFLINE_CALL_PATH_PROOF_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_SYMBOL": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_UNIQUE": True,
        "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN,
        "PRODUCTIVE_LIFECYCLE_EVENT": PRODUCTIVE_LIFECYCLE_EVENT,
        "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": PRODUCTIVE_CALL_PATH_OFFLINE_PROOF,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": (
            COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND
        ),
        "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND": REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": (
            PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "PROVEN_COMPLETE_FIELD_COUNT": matrix["PROVEN_COMPLETE_FIELD_COUNT"],
        "PROVEN_FAIL_CLOSED_FIELD_COUNT": matrix["PROVEN_FAIL_CLOSED_FIELD_COUNT"],
        "PARTIAL_CAPTURE_ALLOWED": matrix["PARTIAL_CAPTURE_ALLOWED"],
        "RETROACTIVE_SYNTHESIS_ALLOWED": matrix["RETROACTIVE_SYNTHESIS_ALLOWED"],
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "caller_census": census,
        "host_graph": graph,
        "dataflow": dataflow,
        "required_field_provenance_matrix": matrix,
        "reader_binding": {
            "COMPLETE_CAPTURE_SEAM": reader_binding["COMPLETE_CAPTURE_SEAM"],
            "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        },
    }
