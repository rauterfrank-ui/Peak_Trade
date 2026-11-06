"""Prove or refute the productive capture owner and lifecycle hook.

Does not join a productive runtime caller. Does not write a handoff.
Does not GET. Does not POST. Does not execute a restart. Does not
synthesize contemporaneous Live observation. Does not backfill timestamps.
Does not mint a replacement owner or hook.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    PRODUCER_RELPATH,
    PRODUCER_SYMBOL,
    WRITER_RELPATH,
    WRITER_SYMBOL,
    census_productive_runtime_graph_v1,
    census_symbol_call_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    SELECTED_SEMANTIC_ID,
)

PRODUCTIVE_CAPTURE_OWNER = "NONE"
PRODUCTIVE_CAPTURE_OWNER_STATUS = "REFUTED"
PRODUCTIVE_LIFECYCLE_HOOK = "NONE"
PRODUCTIVE_LIFECYCLE_HOOK_STATUS = "REFUTED"
HOOK_ORDERING_PROVEN = False
BOUND_FILL_BEFORE_HOOK_PROVEN = False
HOOK_BEFORE_RESTART_PROVEN = False
AUTHORIZED_RUNTIME_SURFACE = "NONE"
AUTHORIZED_RUNTIME_SURFACE_PROVEN = False
BINDING_CASE = "CASE_B"
MINIMAL_FAIL_CLOSED_BINDING_ALLOWED = False
PRODUCTIVE_BINDING_IMPLEMENTED = False
EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH = True
NO_RETROACTIVE_SYNTHESIS_REQUIRED = True
NO_LIVE_ACTION_REQUIRED_FOR_BINDING = True
NO_WIRE_REQUIRED_FOR_BINDING = True
NO_NETWORK_MUTATION_REQUIRED = True
NO_CREDENTIAL_MUTATION_REQUIRED = True
CASE_ADJUDICATION = (
    "CASE_B_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING_CLOSED_"
    "MISSING_PREDICATES_NO_PRODUCTIVE_BINDING"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_"
    "LIFECYCLE_HOOK_REQUIRES_SEPARATE_OWNER_GO_V1"
)
REQUIRED_NEXT_AUTHORITY = (
    "OWNER_GO_TO_CREATE_UNIQUE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_"
    "THEN_SEPARATE_OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
)
MISSING_PREDICATES: tuple[str, ...] = (
    "PRODUCTIVE_CAPTURE_OWNER_UNIQUE",
    "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE",
    "HOOK_ORDERING_PROVEN",
    "BOUND_FILL_BEFORE_HOOK_PROVEN",
    "HOOK_BEFORE_RESTART_PROVEN",
    "AUTHORIZED_RUNTIME_SURFACE_PROVEN",
    "CAPTURE_WINDOW_TIMESTAMP_ORDERING",
    "FUTURE_BOUND_IDENTITY_PARAMETERIZATION",
    "PRODUCTIVE_S05_QTY_SOURCE",
    "FUTURE_LIVE_CAPTURE_AUTHORIZATION",
    "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL",
)
OWNER_CANDIDATE_CONFLICT = False


def _stage(
    *,
    stage_id: str,
    symbol: str,
    path: str,
    productive_callers: str,
    productive_callees: str,
    ownership: str,
    sync_async: str,
    state_transition: str,
    persistence_lifecycle: str,
    test_only_vs_productive: str,
    live_only_vs_reusable: str,
    is_bound_fill: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "STAGE_ID": stage_id,
        "SYMBOL": symbol,
        "PATH": path,
        "PRODUCTIVE_CALLERS": productive_callers,
        "PRODUCTIVE_CALLEES": productive_callees,
        "OWNERSHIP": ownership,
        "SYNC_ASYNC_BOUNDARY": sync_async,
        "STATE_TRANSITION": state_transition,
        "PERSISTENCE_SUPERVISOR_LIFECYCLE": persistence_lifecycle,
        "TEST_ONLY_VS_PRODUCTIVE": test_only_vs_productive,
        "LIVE_ONLY_VS_REUSABLE_RUNTIME": live_only_vs_reusable,
        "IS_CANONICAL_BOUND_FILL": is_bound_fill,
        "NOTES": notes,
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
    }


def census_productive_path_graph_v1(*, repo_root: Path) -> dict[str, Any]:
    graph = census_productive_runtime_graph_v1(repo_root=repo_root)
    writer = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=WRITER_SYMBOL,
        definition_relpath=WRITER_RELPATH,
    )
    producer = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=PRODUCER_SYMBOL,
        definition_relpath=PRODUCER_RELPATH,
    )
    stages = (
        _stage(
            stage_id="ORDER_INTENT",
            symbol="ExecutionOrchestrator.submit_intent",
            path="src/execution/orchestrator.py",
            productive_callers="simulated/paper pipeline callers; not Live canary",
            productive_callees="pipeline risk/route/adapter; simulated fill models",
            ownership="SIMULATED_EXECUTION_PIPELINE",
            sync_async="SYNC",
            state_transition="OrderIntent -> PipelineResult; not Live venue fill",
            persistence_lifecycle="ledger/events in simulated mode; no §11.14 handoff",
            test_only_vs_productive="REUSABLE_RUNTIME_NOT_LIVE_BOUND_FILL",
            live_only_vs_reusable="REUSABLE_SIMULATED",
            is_bound_fill=False,
            notes="ORDER_INTENT is not BOUND_FILL. Live canary has no OrderIntent object.",
        ),
        _stage(
            stage_id="ORDER_PLAN",
            symbol="build_minimum_valid_canary_order_plan_v1",
            path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py",
            productive_callers="run_canary_submit_transport_v1; execute_order_plan_observe_v1",
            productive_callees="venue-derived instrument/price quantization",
            ownership="LIVE_CANARY_ORDER_PLAN",
            sync_async="SYNC",
            state_transition="venue inputs -> canary order plan; no ordId; no pos",
            persistence_lifecycle="in-memory plan; §11.14 evidence via adjudicate_live_order_plan_observed_v1",
            test_only_vs_productive="PRODUCTIVE_LIVE_CANARY_WHEN_GATED",
            live_only_vs_reusable="LIVE_CANARY",
            is_bound_fill=False,
            notes="ORDER_PLAN is not BOUND_FILL.",
        ),
        _stage(
            stage_id="SUBMIT_REQUEST",
            symbol="refuse_submit_unless_gates_pass_v1",
            path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py",
            productive_callers="run_canary_submit_transport_v1",
            productive_callees="evaluate_canary_submit_gates_v1",
            ownership="LIVE_CANARY_SUBMIT_GATES",
            sync_async="SYNC",
            state_transition="PRE_SUBMIT_GATED; fail-closed unless gates pass",
            persistence_lifecycle="ephemeral gate evaluation; standing Live gates remain false",
            test_only_vs_productive="PRODUCTIVE_LIVE_CANARY_WHEN_GATED",
            live_only_vs_reusable="LIVE_CANARY",
            is_bound_fill=False,
            notes="SUBMIT_REQUEST is not BOUND_FILL. CURRENTLY LIVE_ENABLED=false POST_ALLOWED=false.",
        ),
        _stage(
            stage_id="WIRE_SEND",
            symbol="UrllibLiveCanaryTransportV1.send",
            path="src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py",
            productive_callers="LiveCanaryHttpClientV1.post_entry_order via run_canary_submit_transport_v1",
            productive_callees="HTTPS POST /api/v5/trade/order when authorized",
            ownership="LIVE_CANARY_TRANSPORT",
            sync_async="SYNC_HTTP",
            state_transition="signed request leaves process; unknown-submit window opens",
            persistence_lifecycle="ACK in memory; CONTEMPORANEOUS_PERSIST_RELIABLE=false",
            test_only_vs_productive="PRODUCTIVE_LIVE_CANARY_WHEN_AUTHORIZED",
            live_only_vs_reusable="LIVE_ONLY",
            is_bound_fill=False,
            notes="WIRE_SEND is not BOUND_FILL. Current POST_ALLOWED=false.",
        ),
        _stage(
            stage_id="VENUE_ACK",
            symbol="adjudicate_live_submit_ack_observed_v1",
            path="src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/submit_ack_observed_adjudication_v1.py",
            productive_callers="exact-single POST execute path; forensic §11.14 evidence",
            productive_callees="classify_submit_response_v1",
            ownership="SECTION_11_14_ACK_EVIDENCE",
            sync_async="SYNC_HTTP_RESPONSE",
            state_transition="ACKNOWLEDGED with ordId/clOrdId; posSide and pos absent",
            persistence_lifecycle="ACK payload process-local; not durable pre-restart handoff",
            test_only_vs_productive="PRODUCTIVE_LIVE_EVIDENCE_WHEN_POST_OCCURRED",
            live_only_vs_reusable="LIVE_ONLY",
            is_bound_fill=False,
            notes="ORDER_ACK != FILL. VENUE_ACK is not BOUND_FILL.",
        ),
        _stage(
            stage_id="FILL_EVENT",
            symbol="execute_fill_observed_gets_v1",
            path="src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/fill_observed_gets_v1.py",
            productive_callers="execute_live_fill_observed_v1 under a consumed historical GO",
            productive_callees="private GET /api/v5/trade/fills; adjudicate_live_fill_observed_v1",
            ownership="SECTION_11_14_FILL_EVIDENCE",
            sync_async="SYNC_HTTP_GET",
            state_transition="later identity-bound fill row; not in-process canary callback",
            persistence_lifecycle="evidence pack; not contemporaneous handoff writer",
            test_only_vs_productive="PRODUCTIVE_LIVE_EVIDENCE_GET_NOT_CAPTURE_HOOK",
            live_only_vs_reusable="LIVE_READ_ONLY_GET",
            is_bound_fill=False,
            notes="FILL_EVENT GET is not an in-process post-fill hook. FILL != POSITION_OBSERVATION.",
        ),
        _stage(
            stage_id="POSITION_OBSERVATION",
            symbol="execute_position_reconciled_gets_v1",
            path="src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/position_reconciled_gets_v1.py",
            productive_callers="execute_live_position_reconciled_v1 under a consumed historical GO",
            productive_callees="private GET /api/v5/account/positions; adjudicate_live_position_reconciled_v1",
            ownership="SECTION_11_14_POSITION_EVIDENCE",
            sync_async="SYNC_HTTP_GET",
            state_transition="venue-native pos reconciled to fillSz; not S05 handoff pos",
            persistence_lifecycle="evidence pack; venue-owned pos is not Peak_Trade handoff pos",
            test_only_vs_productive="PRODUCTIVE_LIVE_EVIDENCE_GET_NOT_CAPTURE_HOOK",
            live_only_vs_reusable="LIVE_READ_ONLY_GET",
            is_bound_fill=False,
            notes="POSITION_OBSERVATION != BOUND_FILL. Venue GET pos is not S05.",
        ),
        _stage(
            stage_id="BOUND_FILL",
            symbol="LIVE_FILL_OBSERVED_IDENTITY_BOUND_VENUE_FILL",
            path="src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/fill_observed_adjudication_v1.py::adjudicate_live_fill_observed_v1",
            productive_callers="none contemporaneous; proven by later fills GET",
            productive_callees="none to handoff writer",
            ownership="CANONICAL_LIVE_EVIDENCE_FIELD_NOT_RUNTIME_STATE_OWNER",
            sync_async="NOT_AN_IN_PROCESS_EVENT",
            state_transition="historical canary identity-bound venue fill is proven; not current runtime event",
            persistence_lifecycle="ladder field LIVE_FILL_OBSERVED=true; no BOUND_FILL_PROVEN runtime flag",
            test_only_vs_productive="PRODUCTIVE_LIVE_EVIDENCE_FIELD",
            live_only_vs_reusable="LIVE_ONLY",
            is_bound_fill=True,
            notes=(
                "Canonical bound fill requires venue ACK and wire-send. "
                "SIMULATED_FILL != PRODUCTIVE_BOUND_FILL. REPLAY_FILL != LIVE_BOUND_FILL."
            ),
        ),
        _stage(
            stage_id="PRE_RESTART_WINDOW",
            symbol="commit_handoff_after_bound_fill_before_restart_v1",
            path=WRITER_RELPATH,
            productive_callers="NONE; PRODUCTIVE_RUNTIME_CALLER_COUNT=0",
            productive_callees="emit_s05_handoff_pos_v1 (internal writer-to-producer only)",
            ownership="STORAGE_OWNER_NOT_PRODUCTIVE_CAPTURE_OWNER",
            sync_async="SYNC_WHEN_CALLED",
            state_transition="would persist five-field handoff if a productive caller existed",
            persistence_lifecycle="process-restart-readable record; host-crash unproven; unjoined",
            test_only_vs_productive="FORENSIC_OFFLINE_WRITER_UNJOINED",
            live_only_vs_reusable="CONTRACT_BOUND_NOT_RUNTIME_JOINED",
            is_bound_fill=False,
            notes="Window contract exists. No productive owner of BOUND_FILL_PROVEN and RESTART_NOT_YET_OCCURRED.",
        ),
        _stage(
            stage_id="RESTART_BOUNDARY",
            symbol="SupervisorLifecycle.restart",
            path="src/ops/canonical_local_launcher_and_process_supervision_v1/lifecycle_v1.py",
            productive_callers="local launcher/supervisor; not Live handoff path",
            productive_callees="stop then start; no handoff writer",
            ownership="PROCESS_SUPERVISION_NOT_LIVE_HANDOFF",
            sync_async="SYNC_PROCESS",
            state_transition="session STOPPED then STARTED; no pre-restart capture",
            persistence_lifecycle="session registry; not §11.14 durable handoff",
            test_only_vs_productive="PRODUCTIVE_SUPERVISOR_UNRELATED_TO_HANDOFF",
            live_only_vs_reusable="REUSABLE_SUPERVISOR",
            is_bound_fill=False,
            notes="Restart reader/consumer are bound but LIVE_RESTART_RECONSTRUCTED remains false.",
        ),
    )
    distinctions = {
        "ORDER_ACK_IS_NOT_FILL": True,
        "FILL_IS_NOT_POSITION_OBSERVATION": True,
        "POSITION_OBSERVATION_IS_NOT_BOUND_FILL": True,
        "SIMULATED_FILL_IS_NOT_PRODUCTIVE_BOUND_FILL": True,
        "REPLAY_FILL_IS_NOT_LIVE_BOUND_FILL": True,
        "ORDER_INTENT_IS_NOT_BOUND_FILL": True,
        "ORDER_PLAN_IS_NOT_BOUND_FILL": True,
        "WIRE_SEND_IS_NOT_BOUND_FILL": True,
        "VENUE_ACK_IS_NOT_BOUND_FILL": True,
    }
    # CASE_B required zero productive callers. The successor CREATE slice may
    # lawfully add exactly one productive writer caller. This census reports
    # current counts and does not freeze the CASE_B zero-caller invariant.
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_PATH_GRAPH_CENSUS_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "REQUIRED_EVENT_CHAIN": [
            "ORDER_INTENT",
            "ORDER_PLAN",
            "SUBMIT_REQUEST",
            "WIRE_SEND",
            "VENUE_ACK",
            "FILL_EVENT",
            "POSITION_OBSERVATION",
            "BOUND_FILL",
            "PRE_RESTART_WINDOW",
            "RESTART_BOUNDARY",
        ],
        "STAGE_COUNT": len(stages),
        "stages": list(stages),
        "distinctions": distinctions,
        "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT": writer["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT": producer["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": graph[
            "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"
        ],
        "writer_census": writer,
        "producer_census": producer,
        "prior_runtime_graph": graph,
    }


def census_productive_capture_owner_candidates_v1(*, repo_root: Path) -> dict[str, Any]:
    path_graph = census_productive_path_graph_v1(repo_root=repo_root)
    candidates = (
        {
            "CANDIDATE": FIRST_OWNER_ID,
            "PATH": WRITER_RELPATH
            + "::mint_section_11_14_live_durable_pre_restart_handoff_owner_v1",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Minted storage owner of durable records, not a runtime state owner.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": WRITER_SYMBOL,
            "PATH": WRITER_RELPATH,
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Writer exists and is unjoined; zero productive callers.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": PRODUCER_SYMBOL,
            "PATH": PRODUCER_RELPATH,
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Producer emits S05 only when the unjoined writer calls it.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "run_canary_submit_transport_v1",
            "PATH": "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Owns SUBMIT through ACK. Does not wait for fill. Does not call the writer.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "adjudicate_live_fill_observed_v1",
            "PATH": "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/fill_observed_adjudication_v1.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Later GET evidence collector. Can run after process end. Not contemporaneous.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "build_lifecycle_and_closeout_contract_v1",
            "PATH": "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/lifecycle_v1.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Documentary FILLED state. ACTIVATED=false. refuse_ungated_lifecycle_transition_v1.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "ExecutionOrchestrator.submit_intent",
            "PATH": "src/execution/orchestrator.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Simulated/paper pipeline. SIMULATED_FILL is not PRODUCTIVE_BOUND_FILL.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "SupervisorLifecycle.restart",
            "PATH": "src/ops/canonical_local_launcher_and_process_supervision_v1/lifecycle_v1.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "Process stop/start. Does not observe bound fill. Does not call the writer.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
        {
            "CANDIDATE": "LiveSessionOrchestrator.run_dryrun",
            "PATH": "src/execution/live/orchestrator.py",
            "OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED": False,
            "REASON": "DRYRUN snapshot-only. NO-LIVE. No broker. No fill.",
            "STATUS": "REFUTED_NOT_OWNER",
        },
    )
    owners = [
        row
        for row in candidates
        if row["OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED"] is True
    ]
    if owners:
        raise Section1114OfflineSurfaceError("NO_CANDIDATE_MAY_OWN_THE_WINDOW")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_OWNER_CENSUS_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "UNIQUE_OWNER_COUNT": 0,
        "OWNER_CANDIDATE_CONFLICT": OWNER_CANDIDATE_CONFLICT,
        "STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER": True,
        "candidates": list(candidates),
        "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT": path_graph[
            "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT"
        ],
        "PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT": path_graph[
            "PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT"
        ],
    }


def census_productive_lifecycle_hook_candidates_v1(*, repo_root: Path) -> dict[str, Any]:
    writer = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=WRITER_SYMBOL,
        definition_relpath=WRITER_RELPATH,
    )
    productive_writer_callers = [
        row for row in writer["rows"] if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    candidates = (
        {
            "SEARCH_CLASS": "post-bound-fill callback",
            "CANDIDATE": "NONE",
            "PATH": "NONE",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_ABSENT",
            "REASON": "Canary submit returns at ACK. Fill GET is a later slice, not a callback.",
        },
        {
            "SEARCH_CLASS": "state transition",
            "CANDIDATE": "refuse_ungated_lifecycle_transition_v1",
            "PATH": "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/lifecycle_v1.py",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_NOT_HOOK",
            "REASON": "Raises UNGATED_LIFECYCLE_TRANSITION_FORBIDDEN. ACTIVATED=false. FILLED is documentary.",
        },
        {
            "SEARCH_CLASS": "supervisor transition",
            "CANDIDATE": "SupervisorLifecycle.restart",
            "PATH": "src/ops/canonical_local_launcher_and_process_supervision_v1/lifecycle_v1.py",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_NOT_HOOK",
            "REASON": "Restart is the boundary itself. Does not capture before restart. Does not call writer.",
        },
        {
            "SEARCH_CLASS": "execution completion hook",
            "CANDIDATE": "ExecutionOrchestrator.submit_intent",
            "PATH": "src/execution/orchestrator.py",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_NOT_HOOK",
            "REASON": "Simulated pipeline completion is not a Live bound-fill hook.",
        },
        {
            "SEARCH_CLASS": "position reconciliation hook",
            "CANDIDATE": "adjudicate_live_position_reconciled_v1",
            "PATH": "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/position_reconciled_adjudication_v1.py",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_NOT_HOOK",
            "REASON": "Later GET. POSITION_OBSERVATION is not contemporaneous pre-restart capture.",
        },
        {
            "SEARCH_CLASS": "pre-restart shutdown hook",
            "CANDIDATE": "SupervisorLifecycle.stop",
            "PATH": "src/ops/canonical_local_launcher_and_process_supervision_v1/lifecycle_v1.py",
            "BOUND_FILL_ALREADY_PROVEN_BEFORE_HOOK": False,
            "HOOK_BEFORE_RESTART": False,
            "CALLS_WRITER": False,
            "STATUS": "REFUTED_NOT_HOOK",
            "REASON": "Graceful stop does not call the handoff writer and does not require bound fill.",
        },
    )
    # CASE_B required zero productive hook callers. Successor CREATE may add
    # exactly one. This historical census still does not mark a CASE_B hook
    # as proven.
    unique_hooks = [row for row in candidates if row["STATUS"] == "PROVEN_HOOK"]
    if unique_hooks:
        raise Section1114OfflineSurfaceError("NO_HOOK_MAY_BE_MARKED_PROVEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_LIFECYCLE_HOOK_CENSUS_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_STATUS": PRODUCTIVE_LIFECYCLE_HOOK_STATUS,
        "HOOK_ORDERING_PROVEN": HOOK_ORDERING_PROVEN,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": BOUND_FILL_BEFORE_HOOK_PROVEN,
        "HOOK_BEFORE_RESTART_PROVEN": HOOK_BEFORE_RESTART_PROVEN,
        "UNIQUE_HOOK_COUNT": 0,
        "PRODUCTIVE_WRITER_HOOK_CALLER_COUNT": len(productive_writer_callers),
        "candidates": list(candidates),
        "writer_census": writer,
    }


def bind_authorization_surface_matrix_v1() -> dict[str, Any]:
    rows = (
        {
            "SURFACE": "OFFLINE",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": True,
        },
        {
            "SURFACE": "REPLAY",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "SIMULATED",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "SHADOW",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "PAPER",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "TESTNET",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "LIVE_READ_ONLY",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "LIVE_ORDER",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "SURFACE": "OTHER",
            "SURFACE_PRESENT": True,
            "HOOK_REACHABLE": False,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": False,
            "CURRENTLY_AUTHORIZED": False,
        },
    )
    authorized_and_hookable = [
        row
        for row in rows
        if row["CURRENTLY_AUTHORIZED"] is True
        and row["HOOK_REACHABLE"] is True
        and row["BOUND_FILL_SEMANTICS_PRODUCTIVE"] is True
    ]
    if authorized_and_hookable:
        raise Section1114OfflineSurfaceError("NO_SURFACE_MAY_BE_AUTHORIZED_AND_HOOKABLE")
    live_authorized = [
        row
        for row in rows
        if row["SURFACE"] == "LIVE_ORDER" and row["CURRENTLY_AUTHORIZED"] is True
    ]
    if live_authorized:
        raise Section1114OfflineSurfaceError("LIVE_ORDER_MUST_REMAIN_UNAUTHORIZED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_AUTHORIZATION_SURFACE_MATRIX_V1",
        "AUTHORIZED_RUNTIME_SURFACE": AUTHORIZED_RUNTIME_SURFACE,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": AUTHORIZED_RUNTIME_SURFACE_PROVEN,
        "SUFFICIENT_SURFACE_COUNT": 0,
        "MINIMUM_SEMANTIC_CLASS_IF_LATER_AUTHORIZED": "LIVE_ORDER",
        "MINIMUM_SEMANTIC_CLASS_IS_NOT_CURRENTLY_AUTHORIZED": True,
        "CURRENT_LIVE_ENABLED": LIVE_ENABLED,
        "CURRENT_LIVE_ARMED": LIVE_ARMED,
        "CURRENT_CANARY_AUTHORIZED": CANARY_AUTHORIZED,
        "CURRENT_ORDER_SUBMIT_ALLOWED": ORDER_SUBMIT_ALLOWED,
        "CURRENT_POST_ALLOWED": POST_ALLOWED,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
        "rows": list(rows),
    }


def bind_productive_binding_adjudication_v1() -> dict[str, Any]:
    predicates = {
        "PRODUCTIVE_CAPTURE_OWNER_STATUS_PROVEN": False,
        "PRODUCTIVE_LIFECYCLE_HOOK_PROVEN": False,
        "HOOK_ORDERING_PROVEN": HOOK_ORDERING_PROVEN,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": BOUND_FILL_BEFORE_HOOK_PROVEN,
        "HOOK_BEFORE_RESTART_PROVEN": HOOK_BEFORE_RESTART_PROVEN,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": AUTHORIZED_RUNTIME_SURFACE_PROVEN,
        "EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH": EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH,
        "NO_RETROACTIVE_SYNTHESIS_REQUIRED": NO_RETROACTIVE_SYNTHESIS_REQUIRED,
        "NO_LIVE_ACTION_REQUIRED_FOR_BINDING": NO_LIVE_ACTION_REQUIRED_FOR_BINDING,
        "NO_WIRE_REQUIRED_FOR_BINDING": NO_WIRE_REQUIRED_FOR_BINDING,
        "NO_NETWORK_MUTATION_REQUIRED": NO_NETWORK_MUTATION_REQUIRED,
        "NO_CREDENTIAL_MUTATION_REQUIRED": NO_CREDENTIAL_MUTATION_REQUIRED,
    }
    case_a = all(
        predicates[name] is True
        for name in (
            "PRODUCTIVE_CAPTURE_OWNER_STATUS_PROVEN",
            "PRODUCTIVE_LIFECYCLE_HOOK_PROVEN",
            "HOOK_ORDERING_PROVEN",
            "BOUND_FILL_BEFORE_HOOK_PROVEN",
            "HOOK_BEFORE_RESTART_PROVEN",
            "AUTHORIZED_RUNTIME_SURFACE_PROVEN",
            "EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH",
            "NO_RETROACTIVE_SYNTHESIS_REQUIRED",
            "NO_LIVE_ACTION_REQUIRED_FOR_BINDING",
            "NO_WIRE_REQUIRED_FOR_BINDING",
            "NO_NETWORK_MUTATION_REQUIRED",
            "NO_CREDENTIAL_MUTATION_REQUIRED",
        )
    )
    if case_a is True:
        raise Section1114OfflineSurfaceError("CASE_A_MUST_REMAIN_UNREACHABLE")
    if MINIMAL_FAIL_CLOSED_BINDING_ALLOWED is True:
        raise Section1114OfflineSurfaceError("BINDING_MUST_REMAIN_FORBIDDEN")
    if PRODUCTIVE_BINDING_IMPLEMENTED is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_UNIMPLEMENTED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_BINDING_ADJUDICATION_V1",
        "BINDING_CASE": BINDING_CASE,
        "MINIMAL_FAIL_CLOSED_BINDING_ALLOWED": MINIMAL_FAIL_CLOSED_BINDING_ALLOWED,
        "PRODUCTIVE_BINDING_IMPLEMENTED": PRODUCTIVE_BINDING_IMPLEMENTED,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_STATUS": PRODUCTIVE_LIFECYCLE_HOOK_STATUS,
        "HOOK_ORDERING_PROVEN": HOOK_ORDERING_PROVEN,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": BOUND_FILL_BEFORE_HOOK_PROVEN,
        "HOOK_BEFORE_RESTART_PROVEN": HOOK_BEFORE_RESTART_PROVEN,
        "AUTHORIZED_RUNTIME_SURFACE": AUTHORIZED_RUNTIME_SURFACE,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": AUTHORIZED_RUNTIME_SURFACE_PROVEN,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER": True,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH": EXISTING_HANDOFF_WRITER_SEMANTICS_MATCH,
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "WHY_CAPTURE_IS_OR_IS_NOT_PRODUCTIVELY_BOUND": (
            "No unique productive component owns BOUND_FILL_PROVEN and "
            "RESTART_NOT_YET_OCCURRED. No lifecycle edge fires the existing "
            "writer after proven bound fill and before restart. LIVE_ORDER "
            "can produce a canonical bound fill but is not currently "
            "authorized. Binding the writer would invent a missing owner "
            "and hook. CASE_B: no productive binding."
        ),
        "predicates": predicates,
    }


def bind_productive_capture_owner_and_lifecycle_hook_binding_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    path_graph = census_productive_path_graph_v1(repo_root=repo_root)
    owner = census_productive_capture_owner_candidates_v1(repo_root=repo_root)
    hook = census_productive_lifecycle_hook_candidates_v1(repo_root=repo_root)
    surfaces = bind_authorization_surface_matrix_v1()
    decision = bind_productive_binding_adjudication_v1()
    reader_binding = bind_restart_reader_provenance_and_consumer_v1()
    if owner["UNIQUE_OWNER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("UNIQUE_OWNER_MUST_REMAIN_ZERO")
    if hook["UNIQUE_HOOK_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("UNIQUE_HOOK_MUST_REMAIN_ZERO")
    if decision["BINDING_CASE"] != BINDING_CASE:
        raise Section1114OfflineSurfaceError("BINDING_CASE_MUST_REMAIN_CASE_B")
    if decision["MINIMAL_FAIL_CLOSED_BINDING_ALLOWED"] is True:
        raise Section1114OfflineSurfaceError("BINDING_MUST_REMAIN_FORBIDDEN")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if NO_TIMESTAMP_BACKFILL is not True:
        raise Section1114OfflineSurfaceError("NO_TIMESTAMP_BACKFILL_MUST_REMAIN_TRUE")
    if NO_SYNTHETIC_PRE_RESTART_PROVENANCE is not True:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PROVENANCE_MUST_REMAIN_TRUE")
    missing = list(reader_binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "BINDING_CASE": BINDING_CASE,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_STATUS": PRODUCTIVE_LIFECYCLE_HOOK_STATUS,
        "HOOK_ORDERING_PROVEN": HOOK_ORDERING_PROVEN,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": BOUND_FILL_BEFORE_HOOK_PROVEN,
        "HOOK_BEFORE_RESTART_PROVEN": HOOK_BEFORE_RESTART_PROVEN,
        "AUTHORIZED_RUNTIME_SURFACE": AUTHORIZED_RUNTIME_SURFACE,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": AUTHORIZED_RUNTIME_SURFACE_PROVEN,
        "MINIMAL_FAIL_CLOSED_BINDING_ALLOWED": MINIMAL_FAIL_CLOSED_BINDING_ALLOWED,
        "PRODUCTIVE_BINDING_IMPLEMENTED": PRODUCTIVE_BINDING_IMPLEMENTED,
        "COMPLETE_CAPTURE_SEAM": reader_binding["COMPLETE_CAPTURE_SEAM"],
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "path_graph": path_graph,
        "owner_census": owner,
        "hook_census": hook,
        "authorization_surfaces": surfaces,
        "binding_decision": decision,
    }
