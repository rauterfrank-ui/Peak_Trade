"""Route-C gated productive submit composition tests. Offline / no-wire."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    PRODUCTIVE_WIRE_REACHABLE,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.lineage_assembler_v1 import (
    assemble_canonical_lineage_snapshot_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    EvidenceFreshnessV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    HOST_GRAPH_ACTIVATION,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_host_composition_seam_v1 import (
    RouteCHostCompositionSeamError,
    RouteCHostCompositionSeamV1,
    bind_route_c_host_composition_seam_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    CREATE_PATH_ARCHITECTURALLY_COMPLETE,
    CREATE_PATH_CURRENTLY_AUTHORIZED,
    CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
    CURRENT_PRODUCTIVE_WIRE_REACHABLE,
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    ROUTE_C_FUTURE_EXECUTION_PERMIT_KIND,
    ROUTE_C_OWNER_GO,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.position_mode_submit_body_contract_v1 import (
    evaluate_position_mode_submit_body_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_v1 import (
    RouteCFutureExecutionPermitV1,
    RouteCSubmitCompositionInputV1,
    RouteCSubmitCompositionStatusV1,
    run_route_c_submit_composition_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_SIDE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ,
)
from tests.ops.test_canonical_offline_position_creation_path_wiring_v1 import (
    OTHER_INSTRUMENT,
    _assembly_input,
    _path_input,
    _typed_entry,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / (
    "src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1"
)
_FORBIDDEN_IMPORT_PREFIXES = ("requests", "httpx", "socket", "urllib", "aiohttp")
_FORBIDDEN_CALLS = frozenset({"post_entry_order", "urlopen", "urlretrieve"})


def _compose_input(
    upstream: object,
    **overrides: object,
) -> RouteCSubmitCompositionInputV1:
    assembled = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream))
    assert assembled.lineage is not None
    path_overrides = {key: overrides.pop(key) for key in ("path",) if key in overrides}
    if "path" in path_overrides:
        path = path_overrides["path"]
    else:
        path_kwargs = {key: overrides.pop(key) for key in ("owner_go",) if key in overrides}
        assembly_keys = {
            key: overrides.pop(key)
            for key in (
                "evidence",
                "intent",
                "mapper_action",
                "risk_chain",
                "safety_binding",
                "selection_instrument_id",
                "live_send_allowed",
            )
            if key in overrides
        }
        path = _path_input(
            upstream,
            owner_go=str(path_kwargs.get("owner_go") or ROUTE_C_OWNER_GO),
            **assembly_keys,
        )
    prewire = overrides.pop("prewire") if "prewire" in overrides else path.prewire
    authority = overrides.pop("authority") if "authority" in overrides else path.authority
    if prewire is not path.prewire or authority is not path.authority:
        path = replace(path, prewire=prewire, authority=authority)
    payload = {
        "path": path,
        "quantity_authority_source": "STEP_29P",
        "side_authority_source": "MAPPER_FROM_PLAN",
        "quantity_provenance_digest": assembled.lineage.risk_digest,
        "quantity_provenance_final": format(upstream.chain.final_quantity, "f"),
    }
    payload.update(overrides)
    return RouteCSubmitCompositionInputV1(**payload)  # type: ignore[arg-type]


def test_valid_lineage_reaches_submit_composer_candidate_only() -> None:
    upstream = _typed_entry("ENTER_LONG")
    result = run_route_c_submit_composition_v1(_compose_input(upstream))
    assert result.status is RouteCSubmitCompositionStatusV1.CANDIDATE
    assert result.submission_ready is False
    assert result.path is not None
    assert result.path.boundary.request_candidate is not None
    assert result.path.boundary.transport_record is not None
    assert result.gated_surface is not None
    assert result.gated_surface.method_bound is True
    assert result.http_invoked is False
    assert result.secret_materialized is False
    assert result.productive_wire_reachable is False
    assert "MISSING_FUTURE_EXECUTION_PERMIT" in result.reason_codes
    assert "POSITION_MODE_SUBMIT_BODY_SEMANTICS_UNPROVEN" in result.reason_codes
    candidate = result.path.boundary.request_candidate
    assert candidate.quantity == format(upstream.chain.final_quantity, "f")
    assert "posSide" not in candidate.venue_native_body
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert CURRENT_PRODUCTIVE_WIRE_REACHABLE is False


def test_no_http_and_no_secret_materialization() -> None:
    transport = OfflineRecordingTransportV1()
    result = run_route_c_submit_composition_v1(
        _compose_input(_typed_entry("ENTER_LONG")),
        transport=transport,
    )
    assert result.http_invoked is False
    assert result.secret_materialized is False
    assert (
        transport.network_call_performed is False
        if hasattr(transport, "network_call_performed")
        else True
    )
    assert transport.PRODUCTIVE_WIRE_REACHABLE is False
    assert transport.wire_send_enabled is False
    assert result.path is not None
    assert result.path.boundary.transport_record is not None
    assert result.path.boundary.transport_record.network_call_performed is False
    assert result.path.boundary.transport_record.secret_materialized is False


def test_step_29p_qty_and_provenance_preserved() -> None:
    upstream = _typed_entry("ENTER_SHORT")
    result = run_route_c_submit_composition_v1(_compose_input(upstream))
    assert result.status is RouteCSubmitCompositionStatusV1.CANDIDATE
    assert result.path is not None
    candidate = result.path.boundary.request_candidate
    assert candidate is not None
    expected = format(upstream.chain.final_quantity, "f")
    assert candidate.quantity == expected
    assert result.path.assembly.lineage is not None
    assert result.path.assembly.lineage.plan_quantity == expected
    assert candidate.side == "sell"


def test_canary_qty_default_rejected() -> None:
    result = run_route_c_submit_composition_v1(
        _compose_input(
            _typed_entry("ENTER_LONG"),
            quantity_authority_source="SUI_OPERATIVE_ORDER_SZ",
            quantity_provenance_final=SUI_OPERATIVE_ORDER_SZ,
        )
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "CANARY_QTY_DEFAULT_REJECTED" in result.reason_codes
    assert result.path is None


def test_canary_side_default_rejected() -> None:
    result = run_route_c_submit_composition_v1(
        _compose_input(
            _typed_entry("ENTER_LONG"),
            side_authority_source="DEFAULT_SIDE",
        )
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "CANARY_SIDE_DEFAULT_REJECTED" in result.reason_codes
    assert DEFAULT_SIDE == "BUY"
    assert result.path is None


def test_hold_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    hold_evidence = replace(upstream.evidence, decision_outcome="hold")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, evidence=hold_evidence, intent=None, mapper_action=None)
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "HOLD" in result.reason_codes


def test_exit_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    exit_evidence = replace(upstream.evidence, decision_outcome="exit")
    exit_intent = replace(upstream.intent, intent_action="EXIT")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, evidence=exit_evidence, intent=exit_intent)
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "EXIT" in result.reason_codes


def test_reduce_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    reduce_evidence = replace(upstream.evidence, decision_outcome="reduce")
    reduce_intent = replace(upstream.intent, intent_action="REDUCE")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, evidence=reduce_evidence, intent=reduce_intent)
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "REDUCE" in result.reason_codes


def test_inconsistent_instrument_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, selection_instrument_id=OTHER_INSTRUMENT)
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "INCONSISTENT_INSTRUMENT" in result.reason_codes


def test_inconsistent_quantity_provenance_rejected() -> None:
    result = run_route_c_submit_composition_v1(
        _compose_input(
            _typed_entry("ENTER_LONG"),
            quantity_provenance_digest="deadbeef" * 8,
        )
    )
    assert result.status in {
        RouteCSubmitCompositionStatusV1.DENY,
        RouteCSubmitCompositionStatusV1.CANDIDATE,
    }
    # Digest mismatch is checked after a valid path; wrong digest denies.
    if result.status is RouteCSubmitCompositionStatusV1.CANDIDATE:
        raise AssertionError("wrong provenance digest must not remain candidate")
    assert "INCONSISTENT_QUANTITY_PROVENANCE" in result.reason_codes


def test_missing_price_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    path = _path_input(upstream, owner_go=ROUTE_C_OWNER_GO)
    prewire = replace(path.prewire, limit_px="")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, path=replace(path, prewire=prewire))
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "MISSING_PRICE" in result.reason_codes


def test_stale_required_evidence_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    path = _path_input(upstream, owner_go=ROUTE_C_OWNER_GO)
    prewire = replace(path.prewire, freshness_status=EvidenceFreshnessV1.STALE)
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, path=replace(path, prewire=prewire))
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "PREWIRE_EVIDENCE_STALE" in result.reason_codes


def test_unresolved_position_mode_semantics_rejected() -> None:
    result = run_route_c_submit_composition_v1(_compose_input(_typed_entry("ENTER_LONG")))
    assert result.submission_ready is False
    assert result.position_mode_semantics == "UNPROVEN"
    assert result.position_mode_fail_closed is True
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert POSITION_MODE_FAIL_CLOSED is True
    assert "POSITION_MODE_SUBMIT_BODY_SEMANTICS_UNPROVEN" in result.reason_codes


def test_posside_net_manufactured_is_rejected() -> None:
    semantics, reasons, allowed = evaluate_position_mode_submit_body_v1(
        venue_native_body={"posSide": "net", "tdMode": "cross"},
        pos_mode="net",
    )
    assert semantics == "UNPROVEN"
    assert allowed is False
    assert "POSITION_MODE_SUBMIT_BODY_SEMANTICS_UNPROVEN" in reasons
    assert "POSSIDE_EMITTED_WHILE_SEMANTICS_UNPROVEN" in reasons
    assert "POSSIDE_NET_MANUFACTURED_FORBIDDEN" in reasons


def test_max_positions_violation_rejected() -> None:
    upstream = _typed_entry("ENTER_LONG")
    path = _path_input(upstream, owner_go=ROUTE_C_OWNER_GO)
    prewire = replace(path.prewire, position_observation_state="TARGET_POSITION_NONZERO_PROVEN")
    result = run_route_c_submit_composition_v1(
        _compose_input(upstream, path=replace(path, prewire=prewire))
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "MAX_POSITIONS_VIOLATION" in result.reason_codes


def test_missing_future_execution_permit_rejected() -> None:
    result = run_route_c_submit_composition_v1(_compose_input(_typed_entry("ENTER_LONG")))
    assert result.submission_ready is False
    assert "MISSING_FUTURE_EXECUTION_PERMIT" in result.reason_codes


def test_implementation_go_cannot_be_execution_permit() -> None:
    result = run_route_c_submit_composition_v1(
        _compose_input(
            _typed_entry("ENTER_LONG"),
            execution_permit=RouteCFutureExecutionPermitV1(
                owner_go=ROUTE_C_OWNER_GO,
                permit_id="permit-1",
                kind=ROUTE_C_FUTURE_EXECUTION_PERMIT_KIND,
            ),
        )
    )
    assert result.status is RouteCSubmitCompositionStatusV1.HALT
    assert "IMPLEMENTATION_GO_CANNOT_BE_EXECUTION_PERMIT" in result.reason_codes


def test_live_flags_block_without_monkeypatching_standing_constants() -> None:
    upstream = _typed_entry("ENTER_LONG")
    path = _path_input(upstream, owner_go=ROUTE_C_OWNER_GO)
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    live_enabled = run_route_c_submit_composition_v1(
        _compose_input(
            upstream, path=replace(path, authority=replace(path.authority, live_enabled=True))
        )
    )
    assert live_enabled.status is RouteCSubmitCompositionStatusV1.HALT
    assert "AUTHORITY_SNAPSHOT_UNLOCKED" in live_enabled.reason_codes
    live_armed = run_route_c_submit_composition_v1(
        _compose_input(
            upstream, path=replace(path, authority=replace(path.authority, live_armed=True))
        )
    )
    assert live_armed.status is RouteCSubmitCompositionStatusV1.HALT
    canary = run_route_c_submit_composition_v1(
        _compose_input(
            upstream,
            path=replace(path, authority=replace(path.authority, canary_authorized=True)),
        )
    )
    assert canary.status is RouteCSubmitCompositionStatusV1.HALT
    assert "CANARY_AUTHORIZED_BLOCKS" in canary.reason_codes
    submit = run_route_c_submit_composition_v1(
        _compose_input(
            upstream,
            path=replace(path, authority=replace(path.authority, submit_unlocked=True)),
        )
    )
    assert submit.status is RouteCSubmitCompositionStatusV1.HALT
    assert "SUBMIT_UNLOCKED_BLOCKS" in submit.reason_codes


def test_recording_transport_remains_non_wire() -> None:
    transport = OfflineRecordingTransportV1()
    result = run_route_c_submit_composition_v1(
        _compose_input(_typed_entry("ENTER_LONG")),
        transport=transport,
    )
    assert result.recording_is_live_transport is False
    assert transport.PRODUCTIVE_WIRE_REACHABLE is False
    assert transport.wire_send_enabled is False
    second = run_route_c_submit_composition_v1(
        _compose_input(_typed_entry("ENTER_LONG")),
        transport=transport,
    )
    assert second.path is not None
    assert second.path.boundary.transport_record is not None
    assert second.path.boundary.transport_record.duplicate_suppressed is True


def test_host_seam_does_not_activate_runtime() -> None:
    seam = bind_route_c_host_composition_seam_v1()
    assert seam.host_graph_activation is False
    assert HOST_GRAPH_ACTIVATION is False
    result = seam.compose(_compose_input(_typed_entry("ENTER_LONG")))
    assert result.host_graph_activated is False
    assert result.status is RouteCSubmitCompositionStatusV1.CANDIDATE
    try:
        RouteCHostCompositionSeamV1(host_graph_activation=True)
    except RouteCHostCompositionSeamError as exc:
        assert "HOST_GRAPH_ACTIVATION_FORBIDDEN" in str(exc)
    else:
        raise AssertionError("activated seam must fail closed")


def test_canary_plan_builder_forbidden() -> None:
    result = run_route_c_submit_composition_v1(
        _compose_input(_typed_entry("ENTER_LONG"), canary_plan_builder_invoked=True)
    )
    assert result.status is RouteCSubmitCompositionStatusV1.DENY
    assert "CANARY_PLAN_BUILDER_FORBIDDEN" in result.reason_codes


def test_architectural_complete_without_wire_or_authorization() -> None:
    assert CREATE_PATH_ARCHITECTURALLY_COMPLETE is True
    assert CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE is False
    assert CURRENT_PRODUCTIVE_WIRE_REACHABLE is False
    assert CREATE_PATH_CURRENTLY_AUTHORIZED is False
    assert PRODUCTIVE_WIRE_REACHABLE is False
    assert CANONICAL_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"


def test_package_has_no_network_imports_or_submit_calls() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                        hits.append(f"{path.name}:import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                    hits.append(f"{path.name}:from:{mod}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in _FORBIDDEN_CALLS:
                    hits.append(f"{path.name}:call:{node.func.attr}")
    assert hits == []
