"""Create productive capture-owner and lifecycle-hook tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_execute_v1 import (
    execute_live_handoff_create_productive_capture_owner_and_lifecycle_hook_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    AUTHORIZED_RUNTIME_SURFACE,
    BINDING_CASE,
    CANONICAL_BOUND_FILL_KIND,
    CASE_ADJUDICATION,
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    bind_authorization_surface_matrix_v1,
    bind_create_productive_capture_owner_and_lifecycle_hook_v1,
    census_create_caller_graph_v1,
    evaluate_productive_capture_gates_v1,
    require_future_bound_fill_identity_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_TEST_FIXTURE,
    build_test_fixture_field_provenance_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FUTURE_IDENTITY = {
    "clOrdId": "ptfutureboundfill000000000001",
    "ordId": "9990001112223334445",
    "instId": "ETH-USD_UM_XPERP-999999",
    "posSide": "net",
    "fillSz": "2",
}


def _hook_kwargs(storage_root: Path, **overrides: object) -> dict[str, object]:
    identity = dict(overrides.get("bound_fill_identity") or FUTURE_IDENTITY)
    payload: dict[str, object] = {
        "storage_root": storage_root,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": identity,
        "peak_trade_owned_resulting_current_position_qty": identity["fillSz"],
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T09:00:00Z",
        "capture_started_at": "2026-09-07T09:00:01Z",
        "attempt_identity": "test-create-capture-owner-v1",
        "input_class": INPUT_CLASS_TEST_FIXTURE,
        "lifecycle_id": "test-create-capture-owner-lifecycle-v1",
        "field_provenance": build_test_fixture_field_provenance_v1(
            bound_fill_identity=identity,
            lifecycle_id="test-create-capture-owner-lifecycle-v1",
        ),
    }
    payload.update(overrides)
    if "field_provenance" not in overrides:
        payload["field_provenance"] = build_test_fixture_field_provenance_v1(
            bound_fill_identity=dict(payload["bound_fill_identity"]),
            lifecycle_id=str(payload["lifecycle_id"]),
        )
    return payload


def test_exactly_one_productive_writer_caller_is_the_unique_hook() -> None:
    graph = census_create_caller_graph_v1(repo_root=REPO_ROOT)
    assert graph["WRITER_PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 1
    assert graph["PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 0
    assert graph["EXACTLY_ONE_PRODUCTIVE_WRITER_CALLER"] is True
    writer_rows = [
        row
        for row in graph["writer_census"]["rows"]
        if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    assert writer_rows[0]["FILE"] == HOOK_RELPATH


def test_unique_owner_and_hook_are_created() -> None:
    adjudication = bind_create_productive_capture_owner_and_lifecycle_hook_v1(repo_root=REPO_ROOT)
    assert adjudication["PRODUCTIVE_CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert adjudication["PRODUCTIVE_CAPTURE_OWNER_UNIQUE"] is True
    assert adjudication["PRODUCTIVE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK
    assert adjudication["PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE"] is True
    assert adjudication["HOOK_ORDERING_PROVEN"] is True
    assert adjudication["BOUND_FILL_BEFORE_HOOK_PROVEN"] is True
    assert adjudication["HOOK_BEFORE_RESTART_PROVEN"] is True
    assert adjudication["STRUCTURAL_RUNTIME_BINDING_PROVEN"] is True
    assert adjudication["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert adjudication["BINDING_CASE"] == BINDING_CASE
    assert adjudication["BINDING_CASE"] == "CASE_A_CREATED"
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert adjudication["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert LIVE_RESTART_RECONSTRUCTED is False


def test_live_order_hook_is_structurally_reachable_but_unauthorized() -> None:
    surfaces = bind_authorization_surface_matrix_v1()
    assert surfaces["AUTHORIZED_RUNTIME_SURFACE"] == AUTHORIZED_RUNTIME_SURFACE
    assert surfaces["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    assert surfaces["STRUCTURAL_RUNTIME_BINDING_PROVEN"] is True
    assert surfaces["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    live = next(row for row in surfaces["rows"] if row["SURFACE"] == "LIVE_ORDER")
    assert live["HOOK_REACHABLE"] is True
    assert live["BOUND_FILL_SEMANTICS_PRODUCTIVE"] is True
    assert live["CURRENTLY_AUTHORIZED"] is False
    offline = next(row for row in surfaces["rows"] if row["SURFACE"] == "OFFLINE")
    assert offline["CURRENTLY_AUTHORIZED"] is True
    assert offline["HOOK_REACHABLE"] is False
    assert LIVE_ENABLED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False


def test_future_identity_is_parameterized_and_not_historical_hardcode() -> None:
    identity = require_future_bound_fill_identity_v1(bound_fill_identity=FUTURE_IDENTITY)
    assert identity["instId"] == "ETH-USD_UM_XPERP-999999"
    assert identity["ordId"] == "9990001112223334445"
    with pytest.raises(Section1114OfflineSurfaceError, match="FUTURE_BOUND_IDENTITY_INCOMPLETE"):
        require_future_bound_fill_identity_v1(bound_fill_identity={"instId": "ETH-USD_UM_XPERP-1"})


def test_no_capture_before_bound_fill_proven() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="CAPTURE_BEFORE_BOUND_FILL_PROVEN"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=False,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="2",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )


@pytest.mark.parametrize(
    "kind",
    ["ORDER_ACK", "POSITION_OBSERVATION", "SIMULATED_FILL", "REPLAY_FILL"],
)
def test_ack_position_simulated_and_replay_are_rejected(kind: str) -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="BOUND_FILL_KIND_REJECTED"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=True,
            bound_fill_kind=kind,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="2",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )


def test_no_backfill_after_restart_and_missing_provenance_fail_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="NO_BACKFILL_AFTER_RESTART"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="2",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=True,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="RESTART_NOT_YET_OCCURRED_UNPROVEN"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="2",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=False,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="PRODUCTIVE_S05_QTY_MISSING"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )


def test_capture_after_bound_fill_before_restart_persists_parameterized_identity(
    tmp_path: Path,
) -> None:
    first = run_capture_hook_after_bound_fill_before_restart_v1(**_hook_kwargs(tmp_path))
    assert first["DURABLE_SUCCESS_ACK"] is True
    assert first["IDEMPOTENT_REPLAY"] is False
    assert first["identity"]["instId"] == FUTURE_IDENTITY["instId"]
    assert first["identity"]["ordId"] == FUTURE_IDENTITY["ordId"]
    assert first["writer_ack"]["record"]["pos"] == "2"
    assert first["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    second = run_capture_hook_after_bound_fill_before_restart_v1(**_hook_kwargs(tmp_path))
    assert second["IDEMPOTENT_REPLAY"] is True
    mismatched = dict(FUTURE_IDENTITY)
    mismatched["ordId"] = "8888888888888888888"
    with pytest.raises(Section1114OfflineSurfaceError):
        run_capture_hook_after_bound_fill_before_restart_v1(
            **_hook_kwargs(tmp_path, bound_fill_identity=mismatched)
        )


def test_qty_mismatch_and_timestamp_inversion_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        Section1114OfflineSurfaceError, match="POS_MUST_DECIMAL_EQUAL_BOUND_IDENTITY"
    ):
        run_capture_hook_after_bound_fill_before_restart_v1(
            **_hook_kwargs(tmp_path, peak_trade_owned_resulting_current_position_qty="1")
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="BOUND_FILL_AFTER_CAPTURE_START"):
        run_capture_hook_after_bound_fill_before_restart_v1(
            **_hook_kwargs(
                tmp_path,
                bound_fill_proven_at="2026-09-07T09:00:02Z",
                capture_started_at="2026-09-07T09:00:01Z",
            )
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="CAPTURE_START_NOT_BEFORE_RESTART"):
        evaluate_productive_capture_gates_v1(
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=FUTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="2",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T09:00:00Z",
            capture_started_at="2026-09-07T09:00:01Z",
            restart_boundary_at="2026-09-07T09:00:01Z",
            attempt_identity="x",
        )


def test_execute_is_offline_and_does_not_capture_or_authorize_live() -> None:
    result = execute_live_handoff_create_productive_capture_owner_and_lifecycle_hook_v1(
        owner_go=HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
        origin_main_sha=HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T090500Z-test",
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["BINDING_CASE"] == "CASE_A_CREATED"
    assert summary["PRODUCTIVE_CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert summary["PRODUCTIVE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK
    assert summary["STRUCTURAL_RUNTIME_BINDING_PROVEN"] is True
    assert summary["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert summary["CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER"] == 1
    assert summary["CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER"] == 0
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert summary["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert summary["HANDOFF_WRITTEN"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert result["raw_exchanges"] == []
    assert result["safety"]["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
