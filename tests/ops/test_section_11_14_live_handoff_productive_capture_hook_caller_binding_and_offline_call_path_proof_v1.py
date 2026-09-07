"""Productive capture-hook caller binding and offline call-path tests.

All inputs are TEST_FIXTURE. These tests do not execute productive Live
capture, submit, wire send, or restart.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_SYMBOL,
    OfflineNonproductiveCaptureAdapterV1,
    PRODUCTIVE_HOOK_CALLER,
    PRODUCTIVE_LIFECYCLE_EVENT,
    compose_live_order_pre_restart_capture_host_graph_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_live_order_pre_restart_handoff_capture_v1,
    run_section_11_13_5_live_canary_minimum_exposure_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_TEST_FIXTURE,
    build_test_fixture_field_provenance_v1,
    census_productive_capture_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_hook_caller_binding_and_offline_call_path_proof_execute_v1 import (
    execute_live_handoff_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1 import (
    CASE_ADJUDICATION,
    PRODUCTIVE_CALL_PATH_OFFLINE_PROOF,
    PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN,
    bind_productive_capture_hook_caller_and_offline_call_path_v1,
    census_productive_hook_caller_v1,
    require_production_graph_contains_unique_caller_v1,
    require_unique_productive_hook_caller_census_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_FIXTURE_IDENTITY = {
    "clOrdId": "pttestfixtureclordid000000001",
    "ordId": "1110002223334445556",
    "instId": "ETH-USD_UM_XPERP-FIXTURE",
    "posSide": "net",
    "fillSz": "3",
}
LIFECYCLE_ID = "test-fixture-productive-hook-caller-lifecycle-v1"


def _caller_kwargs(tmp_path: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "storage_root": tmp_path,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": dict(TEST_FIXTURE_IDENTITY),
        "peak_trade_owned_resulting_current_position_qty": "3",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T13:00:00Z",
        "capture_started_at": "2026-09-07T13:00:01Z",
        "attempt_identity": "test-fixture-caller-attempt-v1",
        "input_class": INPUT_CLASS_TEST_FIXTURE,
        "lifecycle_id": LIFECYCLE_ID,
        "lifecycle_event": REQUIRED_CAPTURE_TRIGGER,
    }
    payload.update(overrides)
    return payload


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF"
    )
    assert OWNER_GO.endswith(
        "PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF_V1"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "97c015c352467413e292785f2349120e38b43e73"
    assert PRODUCTIVE_HOOK_CALLER == "call_pre_restart_handoff_capture_after_bound_fill_v1"
    assert PRODUCTIVE_LIFECYCLE_EVENT == REQUIRED_CAPTURE_TRIGGER
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False


def test_production_preflight_graph_contains_unique_caller() -> None:
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="preflight",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert result.ok is True
    graph = result.payload["pre_restart_capture_host_graph"]
    require_production_graph_contains_unique_caller_v1(graph=graph)
    assert graph["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert graph["HOST_JOIN_SYMBOL"] == HOST_JOIN_SYMBOL
    lifecycle = result.payload["lifecycle_contract"]["pre_restart_handoff_capture"]
    assert lifecycle["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert lifecycle["LIFECYCLE_EVENT"] == REQUIRED_CAPTURE_TRIGGER
    assert result.payload["submit_gate"]["SUBMIT_ALLOWED"] is False
    assert result.payload["claims"]["NETWORK_EFFECT"] != "WIRE_SEND"


def test_offline_call_path_uses_production_host_join_and_nonproductive_adapter(
    tmp_path: Path,
) -> None:
    adapter = OfflineNonproductiveCaptureAdapterV1(tmp_path)
    result = run_live_order_pre_restart_handoff_capture_v1(
        **_caller_kwargs(tmp_path, capture_adapter=adapter)
    )
    assert result["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert result["HOST_JOIN_SYMBOL"] == HOST_JOIN_SYMBOL
    assert result["PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN"] is True
    assert result["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert result["WIRE_SEND"] is False
    assert result["hook_result"]["TEST_FIXTURE"] is True
    assert result["hook_result"]["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert adapter.WIRE_SEND_CAPABLE is False
    assert adapter.POST_CAPABLE is False
    assert len(adapter.commits) == 1
    for row in result["field_provenance_proof"]:
        assert row["BACKFILL_ALLOWED"] == "false"
        assert row["ACTUAL_PRODUCER"] != ""
        assert row["EXPECTED_PRODUCER"] != ""


def test_owner_vacancy_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="CAPTURE_OWNER_VACANCY"):
        run_live_order_pre_restart_handoff_capture_v1(**_caller_kwargs(tmp_path, capture_owner=""))
    with pytest.raises(Section1114OfflineSurfaceError, match="CAPTURE_OWNER_VACANCY"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, capture_owner="OTHER_OWNER")
        )


def test_missing_required_field_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="REQUIRED_FIELD_MISSING"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, peak_trade_owned_resulting_current_position_qty="")
        )


def test_non_contemporaneous_provenance_fail_closed(tmp_path: Path) -> None:
    provenance = build_test_fixture_field_provenance_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
    )
    fields = dict(provenance["fields"])
    fields["clOrdId"] = dict(fields["clOrdId"])
    fields["clOrdId"]["FRESHNESS"] = "STALE_CACHE"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="STALE_OR_INVALID_PROVENANCE"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, field_provenance=provenance)
        )


def test_required_field_backfill_fail_closed(tmp_path: Path) -> None:
    provenance = build_test_fixture_field_provenance_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
    )
    fields = dict(provenance["fields"])
    fields["pos"] = dict(fields["pos"])
    fields["pos"]["BACKFILL_ALLOWED"] = "true"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="BACKFILL_FORBIDDEN"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, field_provenance=provenance)
        )


def test_wrong_lifecycle_event_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_LIFECYCLE_EVENT"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, lifecycle_event="ORDER_ACK")
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_LIFECYCLE_EVENT"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, bound_fill_proven=False)
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_LIFECYCLE_EVENT"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, restart_already_occurred=True)
        )


def test_multiple_productive_callers_fail_closed() -> None:
    with pytest.raises(
        Section1114OfflineSurfaceError, match="MULTIPLE_PRODUCTIVE_HOOK_CALLERS_FORBIDDEN"
    ):
        require_unique_productive_hook_caller_census_v1(productive_runtime_caller_count=2)


def test_production_graph_without_caller_fail_closed() -> None:
    with pytest.raises(
        Section1114OfflineSurfaceError, match="PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER"
    ):
        require_production_graph_contains_unique_caller_v1(
            graph={"nodes": [], "PRODUCTIVE_HOOK_CALLER": ""}
        )
    with pytest.raises(
        Section1114OfflineSurfaceError, match="PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER"
    ):
        require_unique_productive_hook_caller_census_v1(productive_runtime_caller_count=0)


def test_offline_adapter_cannot_wire_send(tmp_path: Path) -> None:
    class _WireCapableAdapter:
        WIRE_SEND_CAPABLE = True
        POST_CAPABLE = False
        storage_root = tmp_path

    with pytest.raises(
        Section1114OfflineSurfaceError, match="OFFLINE_ADAPTER_MUST_NOT_BE_WIRE_CAPABLE"
    ):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, capture_adapter=_WireCapableAdapter())
        )
    adapter = OfflineNonproductiveCaptureAdapterV1(tmp_path)
    assert adapter.WIRE_SEND_CAPABLE is False
    assert adapter.SUBMIT_CAPABLE is False
    assert adapter.LIVE_ENABLE_CAPABLE is False


def test_live_gates_remain_false_and_preflight_cannot_execute() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    graph = compose_live_order_pre_restart_capture_host_graph_v1()
    assert graph["LIVE_ENABLED"] is False
    assert graph["LIVE_ARMED"] is False
    assert graph["WIRE_SEND"] is False
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="preflight",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        live_enabled=False,
        live_armed=False,
    )
    assert result.payload["submit_gate"]["SUBMIT_ALLOWED"] is False


def test_census_and_bind_prove_unique_productive_caller_without_complete_seam() -> None:
    census = census_productive_hook_caller_v1(repo_root=REPO_ROOT)
    assert census["HOOK_PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 1
    assert census["CALLER_PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 1
    assert census["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    dataflow = census_productive_capture_dataflow_v1(repo_root=REPO_ROOT)
    assert dataflow["HOOK_PRODUCTIVE_CALLER_COUNT"] == 1
    assert dataflow["UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK"] == "PROVEN"
    adjudication = bind_productive_capture_hook_caller_and_offline_call_path_v1(repo_root=REPO_ROOT)
    assert adjudication["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert adjudication["PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN"] is True
    assert adjudication["PRODUCTIVE_CALL_PATH_OFFLINE_PROOF"] is True
    assert adjudication["PRODUCTIVE_LIFECYCLE_EVENT"] == REQUIRED_CAPTURE_TRIGGER
    assert adjudication["PRODUCTIVE_CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert adjudication["PRODUCTIVE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert adjudication["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is False
    assert adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert adjudication["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert adjudication["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    productive_hook = [
        row
        for row in census["hook_census"]["rows"]
        if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    assert productive_hook[0]["FILE"] == CALLER_RELPATH
    assert PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN is True
    assert PRODUCTIVE_CALL_PATH_OFFLINE_PROOF is True


def test_execute_is_offline_and_does_not_claim_productive_capture() -> None:
    result = (
        execute_live_handoff_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            run_id="20260907T130000Z-test",
        )
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert summary["PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN"] is True
    assert summary["PRODUCTIVE_CALL_PATH_OFFLINE_PROOF"] is True
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is False
    assert summary["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert summary["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert summary["HANDOFF_WRITTEN"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    assert result["safety"]["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
