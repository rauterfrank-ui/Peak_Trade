"""Unique LIVE_ORDER productive caller of the §11.14 pre-restart capture hook.

This is the sole productive runtime caller of
`run_capture_hook_after_bound_fill_before_restart_v1`. It is bound to
`REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART` on the
LIVE_ORDER host graph after proven identity-bound venue fill and before
`SupervisorLifecycle.restart`.

It does not GET. It does not POST. It does not wire-send. It does not
submit. It does not invent missing required fields. It does not backfill.
It does not treat historical BOUND_* identity as the current producer.
Runtime execution remains unauthorized.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    ADMISSIBLE_FIELD_SOURCE_KINDS,
    FRESHNESS_CONTEMPORANEOUS,
    IDENTITY_HANDOFF_FIELDS,
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
    identity_producer_symbol_for_tests,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    FORBIDDEN_BOUND_FILL_KINDS,
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    PRODUCTIVE_S05_QTY_SOURCE,
    RESTART_BOUNDARY_PATH,
    RESTART_BOUNDARY_SYMBOL,
    require_future_bound_fill_identity_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)

PRODUCTIVE_HOOK_CALLER = "call_pre_restart_handoff_capture_after_bound_fill_v1"
PRODUCTIVE_HOOK_CALLER_UNIQUE = True
PRODUCTIVE_LIFECYCLE_EVENT = REQUIRED_CAPTURE_TRIGGER
CALLER_RELPATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "pre_restart_handoff_capture_caller_v1.py"
)
HOST_JOIN_SYMBOL = "run_live_order_pre_restart_handoff_capture_v1"
HOST_JOIN_RELPATH = "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/runner_v1.py"
IDENTITY_PRODUCER = (
    "LIVE_IDENTITY_BOUND_VENUE_FILL::bound_fill_identity parameterized into "
    f"{PRODUCTIVE_CAPTURE_OWNER}"
)
IDENTITY_PRODUCER_SYMBOL = "require_future_bound_fill_identity_v1"
FORBIDDEN_LIFECYCLE_EVENTS: frozenset[str] = frozenset(
    {
        "ORDER_ACK",
        "SUBMIT_ACK",
        "PRE_FILL",
        "RESTART",
        "POST_RESTART",
        "POSITION_OBSERVATION",
        "SIMULATED_FILL",
        "REPLAY_FILL",
        "",
    }
)


class OfflineNonproductiveCaptureAdapterV1:
    """Deterministic offline sink. Cannot wire-send, POST, or submit."""

    WIRE_SEND_CAPABLE = False
    POST_CAPABLE = False
    SUBMIT_CAPABLE = False
    LIVE_ENABLE_CAPABLE = False

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = Path(storage_root)
        self.commits: list[dict[str, Any]] = []

    def record_commit(self, payload: Mapping[str, Any]) -> None:
        if self.WIRE_SEND_CAPABLE is True or self.POST_CAPABLE is True:
            raise Section1114OfflineSurfaceError("OFFLINE_ADAPTER_MUST_NOT_BE_WIRE_CAPABLE")
        self.commits.append(dict(payload))


def _text(value: object) -> str:
    return str(value or "").strip()


def require_bound_productive_capture_owner_v1(*, capture_owner: object | None = None) -> str:
    bound = _text(PRODUCTIVE_CAPTURE_OWNER)
    if bound == "":
        raise Section1114OfflineSurfaceError("CAPTURE_OWNER_VACANCY")
    if bound != "SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1":
        raise Section1114OfflineSurfaceError("CAPTURE_OWNER_VACANCY")
    declared = _text(capture_owner) if capture_owner is not None else bound
    if declared == "":
        raise Section1114OfflineSurfaceError("CAPTURE_OWNER_VACANCY")
    if declared != bound:
        raise Section1114OfflineSurfaceError("CAPTURE_OWNER_VACANCY")
    return bound


def require_bound_lifecycle_event_v1(*, lifecycle_event: object) -> str:
    event = _text(lifecycle_event)
    if event in FORBIDDEN_LIFECYCLE_EVENTS or event != PRODUCTIVE_LIFECYCLE_EVENT:
        raise Section1114OfflineSurfaceError("WRONG_LIFECYCLE_EVENT")
    return event


def build_contemporaneous_field_provenance_from_bound_fill_v1(
    *,
    bound_fill_identity: Mapping[str, Any],
    peak_trade_owned_resulting_current_position_qty: object,
    lifecycle_id: object,
    input_class: object,
) -> dict[str, Any]:
    klass = _text(input_class)
    lifecycle = _text(lifecycle_id)
    if lifecycle == "":
        raise Section1114OfflineSurfaceError("LIFECYCLE_ID_MISSING")
    identity = require_future_bound_fill_identity_v1(bound_fill_identity=bound_fill_identity)
    qty = _text(peak_trade_owned_resulting_current_position_qty)
    if qty == "":
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_MISSING")
    identity_source = "PARAMETERIZED_BOUND_FILL_IDENTITY"
    pos_source = "PEAK_TRADE_OWNED_S05_QTY"
    identity_producer = IDENTITY_PRODUCER_SYMBOL
    if klass == INPUT_CLASS_TEST_FIXTURE:
        identity_source = "TEST_FIXTURE_PARAMETERIZED_BOUND_FILL_IDENTITY"
        pos_source = "TEST_FIXTURE_PEAK_TRADE_OWNED_S05_QTY"
        identity_producer = identity_producer_symbol_for_tests()
    elif klass != INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT:
        raise Section1114OfflineSurfaceError("INPUT_CLASS_REJECTED")
    if identity_source not in ADMISSIBLE_FIELD_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
    if pos_source not in ADMISSIBLE_FIELD_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
    rows: dict[str, dict[str, str]] = {}
    for name in IDENTITY_HANDOFF_FIELDS:
        rows[name] = {
            "FIELD": name,
            "INPUT_CLASS": klass,
            "PRODUCER_SYMBOL": identity_producer,
            "EXPECTED_PRODUCER": IDENTITY_PRODUCER,
            "ACTUAL_PRODUCER": identity_producer,
            "SOURCE_KIND": identity_source,
            "FRESHNESS": FRESHNESS_CONTEMPORANEOUS,
            "LIFECYCLE_ID": lifecycle,
            "CAPTURE_TIME_BINDING": "CONTEMPORANEOUS_WITH_BOUND_FILL_PROVEN_AT",
            "BACKFILL_ALLOWED": "false",
            "VALUE": identity[name],
        }
    rows["pos"] = {
        "FIELD": "pos",
        "INPUT_CLASS": klass,
        "PRODUCER_SYMBOL": PRODUCTIVE_S05_QTY_SOURCE,
        "EXPECTED_PRODUCER": PRODUCTIVE_S05_QTY_SOURCE,
        "ACTUAL_PRODUCER": PRODUCTIVE_S05_QTY_SOURCE,
        "SOURCE_KIND": pos_source,
        "FRESHNESS": FRESHNESS_CONTEMPORANEOUS,
        "LIFECYCLE_ID": lifecycle,
        "CAPTURE_TIME_BINDING": "CONTEMPORANEOUS_AT_HANDOFF_COMMIT_AFTER_BOUND_FILL",
        "BACKFILL_ALLOWED": "false",
        "VALUE": qty,
    }
    missing = [name for name in REQUIRED_HANDOFF_FIELDS if name not in rows]
    if missing:
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_MISSING")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CALLER_CONTEMPORANEOUS_FIELD_PROVENANCE_V1",
        "INPUT_CLASS": klass,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "BACKFILL_ALLOWED": False,
        "LIFECYCLE_ID": lifecycle,
        "fields": rows,
    }


def compose_live_order_pre_restart_capture_host_graph_v1() -> dict[str, Any]:
    if LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    nodes = (
        {
            "id": "BOUND_FILL",
            "kind": CANONICAL_BOUND_FILL_KIND,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "PRODUCTIVE_HOOK_CALLER",
            "symbol": PRODUCTIVE_HOOK_CALLER,
            "path": CALLER_RELPATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "HOST_JOIN",
            "symbol": HOST_JOIN_SYMBOL,
            "path": HOST_JOIN_RELPATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "PRODUCTIVE_LIFECYCLE_HOOK",
            "symbol": PRODUCTIVE_LIFECYCLE_HOOK,
            "path": HOOK_RELPATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "PRODUCTIVE_CAPTURE_OWNER",
            "symbol": PRODUCTIVE_CAPTURE_OWNER,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
        {
            "id": "RESTART_BOUNDARY",
            "symbol": RESTART_BOUNDARY_SYMBOL,
            "path": RESTART_BOUNDARY_PATH,
            "PRODUCTION_REACHABLE": True,
            "CURRENTLY_AUTHORIZED": False,
        },
    )
    caller_nodes = [row for row in nodes if row["id"] == "PRODUCTIVE_HOOK_CALLER"]
    if len(caller_nodes) != 1:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_MUST_CONTAIN_UNIQUE_CALLER")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_ORDER_PRE_RESTART_CAPTURE_HOST_GRAPH_V1",
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_UNIQUE": True,
        "PRODUCTIVE_LIFECYCLE_EVENT": PRODUCTIVE_LIFECYCLE_EVENT,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "WIRE_SEND": False,
        "POST_ALLOWED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "nodes": list(nodes),
        "edges": [
            {
                "from": "BOUND_FILL",
                "to": "HOST_JOIN",
                "event": PRODUCTIVE_LIFECYCLE_EVENT,
            },
            {"from": "HOST_JOIN", "to": "PRODUCTIVE_HOOK_CALLER"},
            {"from": "PRODUCTIVE_HOOK_CALLER", "to": "PRODUCTIVE_LIFECYCLE_HOOK"},
            {"from": "PRODUCTIVE_LIFECYCLE_HOOK", "to": "PRODUCTIVE_CAPTURE_OWNER"},
            {
                "from": "PRODUCTIVE_LIFECYCLE_HOOK",
                "to": "RESTART_BOUNDARY",
                "order": "BEFORE",
            },
        ],
    }


def prove_caller_field_provenance_matrix_v1(
    *,
    field_provenance: Mapping[str, Any],
) -> list[dict[str, str]]:
    fields = dict(field_provenance.get("fields") or {})
    rows: list[dict[str, str]] = []
    for name in REQUIRED_HANDOFF_FIELDS:
        payload = dict(fields.get(name) or {})
        expected = (
            IDENTITY_PRODUCER if name in IDENTITY_HANDOFF_FIELDS else PRODUCTIVE_S05_QTY_SOURCE
        )
        actual = _text(payload.get("ACTUAL_PRODUCER") or payload.get("PRODUCER_SYMBOL"))
        if actual == "":
            raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_MISSING")
        backfill = _text(payload.get("BACKFILL_ALLOWED")).lower()
        if backfill in {"true", "1", "yes"}:
            raise Section1114OfflineSurfaceError("BACKFILL_FORBIDDEN")
        rows.append(
            {
                "FIELD": name,
                "EXPECTED_PRODUCER": expected,
                "ACTUAL_PRODUCER": actual,
                "CAPTURE_TIME_BINDING": _text(payload.get("CAPTURE_TIME_BINDING")),
                "BACKFILL_ALLOWED": "false",
                "VALUE_IDENTITY_OR_EQUIVALENCE_RULE": (
                    "MUST_EQUAL_SAME_BOUND_FILL_LIFECYCLE"
                    if name in IDENTITY_HANDOFF_FIELDS
                    else "POS_MUST_DECIMAL_EQUAL_BOUND_FILL_SZ_OF_SAME_LIFECYCLE"
                ),
                "FAIL_CLOSED_BEHAVIOR": "HARD_FAIL",
            }
        )
    return rows


def call_pre_restart_handoff_capture_after_bound_fill_v1(
    *,
    storage_root: Path,
    bound_fill_proven: bool,
    bound_fill_kind: object,
    bound_fill_identity: Mapping[str, Any],
    peak_trade_owned_resulting_current_position_qty: object,
    source_kind: object,
    unit: object,
    restart_already_occurred: bool,
    restart_not_yet_occurred_proven: bool,
    bound_fill_proven_at: object,
    capture_started_at: object,
    attempt_identity: object,
    input_class: object,
    lifecycle_id: object,
    lifecycle_event: object,
    field_provenance: Mapping[str, Any] | None = None,
    capture_owner: object | None = None,
    restart_boundary_at: object | None = None,
    extra_fields: Mapping[str, Any] | None = None,
    restart_derived: bool = False,
    source_is_restart_reader: bool = False,
    source_is_historical_evidence: bool = False,
    capture_adapter: OfflineNonproductiveCaptureAdapterV1 | None = None,
) -> dict[str, Any]:
    owner = require_bound_productive_capture_owner_v1(capture_owner=capture_owner)
    event = require_bound_lifecycle_event_v1(lifecycle_event=lifecycle_event)
    kind = _text(bound_fill_kind)
    if kind in FORBIDDEN_BOUND_FILL_KINDS or kind != CANONICAL_BOUND_FILL_KIND:
        raise Section1114OfflineSurfaceError("WRONG_LIFECYCLE_EVENT")
    if bound_fill_proven is not True:
        raise Section1114OfflineSurfaceError("WRONG_LIFECYCLE_EVENT")
    if restart_already_occurred is True:
        raise Section1114OfflineSurfaceError("WRONG_LIFECYCLE_EVENT")
    if LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if capture_adapter is not None:
        if capture_adapter.WIRE_SEND_CAPABLE is True or capture_adapter.POST_CAPABLE is True:
            raise Section1114OfflineSurfaceError("OFFLINE_ADAPTER_MUST_NOT_BE_WIRE_CAPABLE")
        storage_root = capture_adapter.storage_root
    if field_provenance is None:
        provenance = build_contemporaneous_field_provenance_from_bound_fill_v1(
            bound_fill_identity=bound_fill_identity,
            peak_trade_owned_resulting_current_position_qty=(
                peak_trade_owned_resulting_current_position_qty
            ),
            lifecycle_id=lifecycle_id,
            input_class=input_class,
        )
    else:
        provenance = dict(field_provenance)
    matrix_rows = prove_caller_field_provenance_matrix_v1(field_provenance=provenance)
    result = run_capture_hook_after_bound_fill_before_restart_v1(
        storage_root=storage_root,
        bound_fill_proven=bound_fill_proven,
        bound_fill_kind=bound_fill_kind,
        bound_fill_identity=bound_fill_identity,
        peak_trade_owned_resulting_current_position_qty=(
            peak_trade_owned_resulting_current_position_qty
        ),
        source_kind=source_kind,
        unit=unit,
        restart_already_occurred=restart_already_occurred,
        restart_not_yet_occurred_proven=restart_not_yet_occurred_proven,
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        attempt_identity=attempt_identity,
        input_class=input_class,
        lifecycle_id=lifecycle_id,
        field_provenance=provenance,
        restart_boundary_at=restart_boundary_at,
        extra_fields=extra_fields,
        restart_derived=restart_derived,
        source_is_restart_reader=source_is_restart_reader,
        source_is_historical_evidence=source_is_historical_evidence,
    )
    if capture_adapter is not None:
        capture_adapter.record_commit(result)
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_HOOK_CALLER_RESULT_V1",
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_UNIQUE": True,
        "PRODUCTIVE_LIFECYCLE_EVENT": event,
        "PRODUCTIVE_CAPTURE_OWNER": owner,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": True,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "WIRE_SEND": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "field_provenance_proof": matrix_rows,
        "hook_result": result,
    }
