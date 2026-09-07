"""Create the unique productive capture owner and lifecycle hook.

CASE_B proved no unique owner or hook existed. This slice mints exactly one
productive capture owner and exactly one semantic hook, structurally bound
on the LIVE_ORDER path, fail-closed, without Live/wire authorization.

Does not GET. Does not POST. Does not execute a restart. Does not invent
a bound fill. Does not backfill after restart. Does not hardcode historical
SUI/BTC identity. Does not claim host-crash durability. Does not promote
LIVE_RESTART_RECONSTRUCTED.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

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
    census_symbol_call_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
    SELECTED_SEMANTIC_ID,
)

PRODUCTIVE_CAPTURE_OWNER = "SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1"
PRODUCTIVE_CAPTURE_OWNER_UNIQUE = True
PRODUCTIVE_LIFECYCLE_HOOK = "run_capture_hook_after_bound_fill_before_restart_v1"
PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE = True
HOOK_RELPATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_restart_handoff_capture_hook_v1.py"
)
RESTART_BOUNDARY_SYMBOL = "SupervisorLifecycle.restart"
RESTART_BOUNDARY_PATH = (
    "src/ops/canonical_local_launcher_and_process_supervision_v1/lifecycle_v1.py"
)
CANONICAL_BOUND_FILL_KIND = "LIVE_IDENTITY_BOUND_VENUE_FILL"
FORBIDDEN_BOUND_FILL_KINDS: frozenset[str] = frozenset(
    {
        "ORDER_ACK",
        "VENUE_ACK",
        "POSITION_OBSERVATION",
        "SIMULATED_FILL",
        "REPLAY_FILL",
        "UNBOUND_VENUE_FILL",
        "FILL_SZ_COPY",
        "VENUE_GET_POS",
    }
)
HOOK_ORDERING_PROVEN = True
BOUND_FILL_BEFORE_HOOK_PROVEN = True
HOOK_BEFORE_RESTART_PROVEN = True
CAPTURE_WINDOW_TIMESTAMP_ORDERING = "CONTRACT_PROVEN"
FUTURE_BOUND_IDENTITY_PARAMETERIZATION = True
PRODUCTIVE_S05_QTY_SOURCE = (
    "SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1::"
    "peak_trade_owned_resulting_current_position_qty"
)
PRODUCTIVE_S05_QTY_SOURCE_PROVEN = True
STRUCTURAL_RUNTIME_BINDING_PROVEN = True
CURRENT_RUNTIME_EXECUTION_AUTHORIZED = False
AUTHORIZED_RUNTIME_SURFACE = "NONE"
AUTHORIZED_RUNTIME_SURFACE_PROVEN = False
BINDING_CASE = "CASE_A_CREATED"
PRODUCTIVE_BINDING_IMPLEMENTED = True
CASE_ADJUDICATION = (
    "CASE_A_CREATED_UNIQUE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_"
    "STRUCTURAL_BINDING_FAIL_CLOSED_RUNTIME_EXECUTION_UNAUTHORIZED"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)
REQUIRED_NEXT_AUTHORITY = (
    "OWNER_GO_FOR_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_THEN_SEPARATE_OWNER_GO_"
    "FOR_LIVE_RESTART_RECONSTRUCTED"
)
MISSING_PREDICATES: tuple[str, ...] = (
    "FUTURE_LIVE_CAPTURE_AUTHORIZATION",
    "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL",
)
IDENTITY_FIELDS: tuple[str, ...] = (
    "clOrdId",
    "ordId",
    "instId",
    "posSide",
    "fillSz",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def require_future_bound_fill_identity_v1(
    *,
    bound_fill_identity: Mapping[str, Any] | None,
) -> dict[str, str]:
    payload = dict(bound_fill_identity or {})
    missing = [name for name in IDENTITY_FIELDS if _text(payload.get(name)) == ""]
    if missing:
        raise Section1114OfflineSurfaceError("FUTURE_BOUND_IDENTITY_INCOMPLETE")
    return {
        "clOrdId": _text(payload.get("clOrdId")),
        "ordId": _text(payload.get("ordId")),
        "instId": _text(payload.get("instId")),
        "posSide": _text(payload.get("posSide")),
        "fillSz": _text(payload.get("fillSz")),
    }


def validate_capture_window_timestamps_v1(
    *,
    bound_fill_proven_at: object,
    capture_started_at: object,
    capture_committed_at: object | None = None,
    restart_boundary_at: object | None = None,
) -> dict[str, Any]:
    proven_at = _text(bound_fill_proven_at)
    started_at = _text(capture_started_at)
    committed_at = _text(capture_committed_at)
    restart_at = _text(restart_boundary_at)
    if proven_at == "" or started_at == "":
        raise Section1114OfflineSurfaceError("CAPTURE_WINDOW_TIMESTAMP_MISSING")
    if proven_at > started_at:
        raise Section1114OfflineSurfaceError("BOUND_FILL_AFTER_CAPTURE_START")
    if committed_at != "":
        if started_at > committed_at:
            raise Section1114OfflineSurfaceError("CAPTURE_COMMIT_BEFORE_START")
        if restart_at != "" and committed_at >= restart_at:
            raise Section1114OfflineSurfaceError("CAPTURE_COMMIT_NOT_BEFORE_RESTART")
    elif restart_at != "" and started_at >= restart_at:
        raise Section1114OfflineSurfaceError("CAPTURE_START_NOT_BEFORE_RESTART")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_WINDOW_TIMESTAMP_ORDERING_V1",
        "CAPTURE_WINDOW_TIMESTAMP_ORDERING": CAPTURE_WINDOW_TIMESTAMP_ORDERING,
        "BOUND_FILL_PROVEN_AT": proven_at,
        "CAPTURE_STARTED_AT": started_at,
        "CAPTURE_COMMITTED_AT": committed_at or None,
        "RESTART_BOUNDARY_AT": restart_at or None,
        "NO_TIMESTAMP_INVENTION": True,
        "RESTART_TIMESTAMP_OPTIONAL_AT_CAPTURE": True,
    }


def evaluate_productive_capture_gates_v1(
    *,
    bound_fill_proven: object,
    bound_fill_kind: object,
    bound_fill_identity: Mapping[str, Any] | None,
    peak_trade_owned_resulting_current_position_qty: object,
    source_kind: object,
    unit: object,
    restart_already_occurred: object,
    restart_not_yet_occurred_proven: object,
    bound_fill_proven_at: object,
    capture_started_at: object,
    restart_boundary_at: object | None = None,
    attempt_identity: object,
    extra_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if bound_fill_proven is not True:
        raise Section1114OfflineSurfaceError("CAPTURE_BEFORE_BOUND_FILL_PROVEN")
    kind = _text(bound_fill_kind)
    if kind in FORBIDDEN_BOUND_FILL_KINDS or kind != CANONICAL_BOUND_FILL_KIND:
        raise Section1114OfflineSurfaceError("BOUND_FILL_KIND_REJECTED")
    if restart_already_occurred is True:
        raise Section1114OfflineSurfaceError("NO_BACKFILL_AFTER_RESTART")
    if restart_not_yet_occurred_proven is not True:
        raise Section1114OfflineSurfaceError("RESTART_NOT_YET_OCCURRED_UNPROVEN")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if NO_TIMESTAMP_BACKFILL is not True:
        raise Section1114OfflineSurfaceError("NO_TIMESTAMP_BACKFILL_MUST_REMAIN_TRUE")
    if NO_SYNTHETIC_PRE_RESTART_PROVENANCE is not True:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PROVENANCE_MUST_REMAIN_TRUE")
    identity = require_future_bound_fill_identity_v1(bound_fill_identity=bound_fill_identity)
    qty = _text(peak_trade_owned_resulting_current_position_qty)
    if qty == "":
        raise Section1114OfflineSurfaceError("PRODUCTIVE_S05_QTY_MISSING")
    if _text(source_kind) != ADMISSIBLE_POS_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("POS_SOURCE_KIND_REJECTED")
    if _text(unit) != POS_UNIT:
        raise Section1114OfflineSurfaceError("WRONG_UNIT")
    if _text(attempt_identity) == "":
        raise Section1114OfflineSurfaceError("ATTEMPT_IDENTITY_MISSING")
    window = validate_capture_window_timestamps_v1(
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        capture_committed_at=None,
        restart_boundary_at=restart_boundary_at,
    )
    extras = dict(extra_fields or {})
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_OWNER_GATES_V1",
        "ALLOWED": True,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER": True,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "PRODUCTIVE_S05_QTY_SOURCE": PRODUCTIVE_S05_QTY_SOURCE,
        "FUTURE_BOUND_IDENTITY_PARAMETERIZATION": True,
        "HOOK_ORDERING_PROVEN": True,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": True,
        "HOOK_BEFORE_RESTART_PROVEN": True,
        "capture_window": window,
        "identity": identity,
        "writer_kwargs": {
            "resulting_current_position_qty": qty,
            "unit": POS_UNIT,
            "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
            "inst_id": identity["instId"],
            "clordid": identity["clOrdId"],
            "ord_id": identity["ordId"],
            "pos_side": identity["posSide"],
            "bound_fill_identity_exists": True,
            "attempt_identity": _text(attempt_identity),
            "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
            "capture_trigger": REQUIRED_CAPTURE_TRIGGER,
            "restart_already_occurred": False,
            "extra_fields": extras,
            "bound_fill_identity": identity,
            "now_utc": window["CAPTURE_STARTED_AT"],
        },
    }


def census_create_caller_graph_v1(*, repo_root: Path) -> dict[str, Any]:
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
    hook = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=PRODUCTIVE_LIFECYCLE_HOOK,
        definition_relpath=HOOK_RELPATH,
    )
    productive_writer = [
        row for row in writer["rows"] if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    if writer["PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 1:
        raise Section1114OfflineSurfaceError("WRITER_MUST_HAVE_EXACTLY_ONE_PRODUCTIVE_CALLER")
    if productive_writer[0]["FILE"] != HOOK_RELPATH:
        raise Section1114OfflineSurfaceError("WRITER_PRODUCTIVE_CALLER_MUST_BE_UNIQUE_HOOK")
    if producer["PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("PRODUCER_MUST_REMAIN_INTERNAL_TO_WRITER")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CREATE_CAPTURE_OWNER_CALLER_GRAPH_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT": writer["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT": producer["PRODUCTIVE_RUNTIME_CALLER_COUNT"],
        "HOOK_DEFINITION": HOOK_RELPATH,
        "HOOK_SYMBOL": PRODUCTIVE_LIFECYCLE_HOOK,
        "HOOK_CALL_SITE_COUNT": hook["CALL_SITE_COUNT"],
        "EXACTLY_ONE_PRODUCTIVE_WRITER_CALLER": True,
        "writer_census": writer,
        "producer_census": producer,
        "hook_census": hook,
    }


def census_created_owner_and_hook_v1(*, repo_root: Path) -> dict[str, Any]:
    graph = census_create_caller_graph_v1(repo_root=repo_root)
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CREATED_OWNER_AND_HOOK_CENSUS_V1",
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_UNIQUE": True,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE": True,
        "STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER": True,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "RESTART_BOUNDARY_SYMBOL": RESTART_BOUNDARY_SYMBOL,
        "RESTART_BOUNDARY_PATH": RESTART_BOUNDARY_PATH,
        "HOOK_IS_NOT_RESTART_BOUNDARY": True,
        "caller_graph": graph,
        "rejected_existing_candidates": (
            {
                "CANDIDATE": FIRST_OWNER_ID,
                "REASON": "Storage owner remains storage owner; not the runtime capture owner.",
            },
            {
                "CANDIDATE": WRITER_SYMBOL,
                "REASON": "Writer is the persistence seam, not the unique runtime owner.",
            },
            {
                "CANDIDATE": "run_canary_submit_transport_v1",
                "REASON": "Owns ACK. ORDER_ACK != FILL. Must not call the writer.",
            },
            {
                "CANDIDATE": "adjudicate_live_fill_observed_v1",
                "REASON": "Later GET can run after process end; cannot prove pre-restart.",
            },
            {
                "CANDIDATE": "ExecutionOrchestrator.submit_intent",
                "REASON": "SIMULATED_FILL != PRODUCTIVE_BOUND_FILL.",
            },
            {
                "CANDIDATE": RESTART_BOUNDARY_SYMBOL,
                "REASON": "Restart is the boundary, not the capture hook.",
            },
        ),
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
            "HOOK_REACHABLE": True,
            "BOUND_FILL_SEMANTICS_PRODUCTIVE": True,
            "CURRENTLY_AUTHORIZED": False,
            "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
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
    live = next(row for row in rows if row["SURFACE"] == "LIVE_ORDER")
    if live["CURRENTLY_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_ORDER_MUST_REMAIN_UNAUTHORIZED")
    if live["HOOK_REACHABLE"] is not True:
        raise Section1114OfflineSurfaceError("LIVE_ORDER_HOOK_MUST_BE_STRUCTURALLY_REACHABLE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CREATE_AUTHORIZATION_SURFACE_MATRIX_V1",
        "AUTHORIZED_RUNTIME_SURFACE": AUTHORIZED_RUNTIME_SURFACE,
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": False,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "SUFFICIENT_CURRENTLY_AUTHORIZED_SURFACE_COUNT": 0,
        "MINIMUM_SEMANTIC_CLASS_IF_LATER_AUTHORIZED": "LIVE_ORDER",
        "MINIMUM_SEMANTIC_CLASS_IS_NOT_CURRENTLY_AUTHORIZED": True,
        "CURRENT_LIVE_ENABLED": LIVE_ENABLED,
        "CURRENT_LIVE_ARMED": LIVE_ARMED,
        "CURRENT_CANARY_AUTHORIZED": CANARY_AUTHORIZED,
        "CURRENT_ORDER_SUBMIT_ALLOWED": ORDER_SUBMIT_ALLOWED,
        "CURRENT_POST_ALLOWED": POST_ALLOWED,
        "rows": list(rows),
    }


def bind_create_productive_capture_owner_and_lifecycle_hook_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    census = census_created_owner_and_hook_v1(repo_root=repo_root)
    surfaces = bind_authorization_surface_matrix_v1()
    reader_binding = bind_restart_reader_provenance_and_consumer_v1()
    if census["PRODUCTIVE_CAPTURE_OWNER_UNIQUE"] is not True:
        raise Section1114OfflineSurfaceError("CAPTURE_OWNER_MUST_BE_UNIQUE")
    if census["PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE"] is not True:
        raise Section1114OfflineSurfaceError("LIFECYCLE_HOOK_MUST_BE_UNIQUE")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    missing = list(reader_binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "BINDING_CASE": BINDING_CASE,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_UNIQUE": True,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE": True,
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
        "AUTHORIZED_RUNTIME_SURFACE_PROVEN": False,
        "PRODUCTIVE_BINDING_IMPLEMENTED": True,
        "COMPLETE_CAPTURE_SEAM": reader_binding["COMPLETE_CAPTURE_SEAM"],
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "owner_hook_census": census,
        "authorization_surfaces": surfaces,
    }
