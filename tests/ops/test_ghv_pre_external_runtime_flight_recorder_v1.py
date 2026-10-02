"""GHV PRE_EXTERNAL runtime flight recorder + continuation harness contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reapply_forensic_synthetic_safety_reprojection_on_replay_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
    run_ghv_pre_external_continuation_harness_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
    FLIGHT_RECORD_FILENAME,
    GhvPreExternalRuntimeFlightRecorderSessionV1,
    RECORDER_AUTHORITY,
    append_flight_record_stage_v1,
    bind_ghv_pre_external_runtime_flight_recorder_session_v1,
    persist_continuation_snapshot_v1,
    reset_ghv_pre_external_runtime_flight_recorder_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from tests.ops.test_ghv_observe_shaped_venue_plan_object_identity_v1 import (
    _genuine_observe_shaped_s7_replay_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _balance_payload,
    _injected,
    _instruments_payload,
)


def test_genuine_observe_shaped_replay_with_recorder_disabled_unchanged(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    traces: list[dict[str, object]] = []
    status, reasons, _ = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=_genuine_observe_shaped_s7_replay_v1(tmp_path)[0]["LANE_1"][1],
        mode=MODE_LIVE,
        composed_epoch=EPOCH,
        predicate_trace_collector=traces,
    )
    assert status is not CompositionStatusV1.PASS
    assert reasons
    assert traces


def test_synthetic_enter_short_overlay_and_pr7013_observable(tmp_path: Path) -> None:
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    session = GhvPreExternalRuntimeFlightRecorderSessionV1(
        enabled=True,
        product_evidence_root=evidence_root,
        run_id="run-test",
        continuous_run_id="run-test",
        repository_sha="abc",
        cycle_index=1,
    )
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(session)
    syn_reset = bind_synthetic_enter_forensic_session_v1(
        build_synthetic_enter_forensic_session_v1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=evidence_root,
            continuous_run_id="run-test",
        )
    )
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        assert overlay.applied is True
        live_29p = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=overlay.replay,
            bound_instrument=bound,
            injected=_injected(
                payload=_balance_payload(),
                instruments_payload=_instruments_payload(inst_id=str(bound.venue_native_id)),
            ),
            decision_epoch=EPOCH,
        )
        assert live_29p.replay is not None
        parent = append_flight_record_stage_v1(
            stage="LIVE_29P_JOIN_OUTPUT",
            producer_symbol="test",
            consumer_symbol="test",
            parent_generation_id="gen_root",
            replay=live_29p.replay,
        )
        assert parent is not None
        reapply_forensic_synthetic_safety_reprojection_on_replay_v1(
            live_29p.replay,
            parent_generation_id=parent,
        )
        persist_continuation_snapshot_v1(
            parent_generation_id=parent,
            post_live_29p_replay=live_29p.replay,
            bound_instrument=bound,
            composed_epoch=EPOCH,
            session_id="sess",
            run_id_suffix="run:suffix",
            synthetic_overlay_applied=True,
            live_29p_status=str(live_29p.status),
            live_29p_first_blocker=str(live_29p.first_blocker or ""),
        )
        lines = (evidence_root / FLIGHT_RECORD_FILENAME).read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 2
        pr7013_rows = [json.loads(line) for line in lines if "PR7013" in line]
        assert pr7013_rows
        assert pr7013_rows[-1]["helper_executed"] is True
        assert pr7013_rows[-1]["helper_preconditions_satisfied"] is True
    finally:
        reset_synthetic_enter_forensic_session_v1(syn_reset)
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_stale_object_generation_lineage_detectable(tmp_path: Path) -> None:
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root = tmp_path / "evidence2"
    evidence_root.mkdir()
    session = GhvPreExternalRuntimeFlightRecorderSessionV1(
        enabled=True,
        product_evidence_root=evidence_root,
        run_id="run2",
        continuous_run_id="run2",
    )
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(session)
    try:
        gen_a = append_flight_record_stage_v1(
            stage="S7_MV2_FINAL_OUTPUT",
            producer_symbol="a",
            consumer_symbol="b",
            parent_generation_id="gen_root",
            replay=observe_replay,
        )
        overlay = observe_replay
        gen_b = append_flight_record_stage_v1(
            stage="SYNTHETIC_OVERLAY_OUTPUT",
            producer_symbol="b",
            consumer_symbol="c",
            parent_generation_id=str(gen_a),
            replay=overlay,
        )
        assert gen_a != gen_b
        rows = [
            json.loads(line)
            for line in (evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()
        ]
        assert rows[1]["parent_generation_id"] == gen_a
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_continuation_harness_not_evaluable_without_get_capture(tmp_path: Path) -> None:
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    evidence_root = tmp_path / "evidence3"
    evidence_root.mkdir()
    session = GhvPreExternalRuntimeFlightRecorderSessionV1(
        enabled=True,
        product_evidence_root=evidence_root,
        run_id="run3",
        continuous_run_id="run3",
    )
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(session)
    try:
        parent = append_flight_record_stage_v1(
            stage="LIVE_29P_JOIN_OUTPUT",
            producer_symbol="test",
            consumer_symbol="test",
            parent_generation_id="gen_root",
            replay=observe_replay,
        )
        persist_continuation_snapshot_v1(
            parent_generation_id=str(parent),
            post_live_29p_replay=observe_replay,
            bound_instrument=bound,
            composed_epoch=EPOCH,
            session_id="sess",
            run_id_suffix="run:suffix",
            synthetic_overlay_applied=False,
            live_29p_status="PASS",
            live_29p_first_blocker="",
        )
        snap_root = evidence_root / "ghv_pre_external_continuation_snapshot_v1"
        report = run_ghv_pre_external_continuation_harness_v1(
            snapshot_root=snap_root,
            output_dir=tmp_path / "out",
        )
        assert "FRESH_PRETRADE_CONTRACT" in report["NOT_EVALUABLE"]
        assert report["ROOT_BLOCKERS"]
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_secret_serialization_fail_closed(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        GhvPreExternalRuntimeFlightRecorderError,
        _assert_no_secrets,
    )

    with pytest.raises(GhvPreExternalRuntimeFlightRecorderError):
        _assert_no_secrets({"api_key": "nope"})


def test_recorder_authority_none() -> None:
    assert RECORDER_AUTHORITY == "NONE"
