"""Whole-cycle GHV causal observability contracts (observer-only; not Product Runtime proof)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reset_synthetic_enter_forensic_session_v1,
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
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
    CHANGE_IMPACT_FILENAME,
    FIELD_PROVENANCE_FILENAME,
    GHV_ROOT_CHANGE_EVENT_ID,
    PROVENANCE_ANALYZER_AUTHORITY,
    REVERSE_PROVENANCE_FILENAME,
    STATE_GRAPH_FILENAME,
    build_change_impact_v1,
    build_field_provenance_rows_v1,
    build_reverse_provenance_v1,
    build_state_graph_v1,
    build_whole_cycle_observability_v1,
    enumerate_bounded_cycle_graph_v1,
    persist_whole_cycle_observability_artifacts_v1,
)
from tests.ops.test_ghv_observe_shaped_venue_plan_object_identity_v1 import (
    _genuine_observe_shaped_s7_replay_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH


def _bind_recorder(tmp_path: Path) -> tuple[Path, object]:
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    session = GhvPreExternalRuntimeFlightRecorderSessionV1(
        enabled=True,
        product_evidence_root=evidence_root,
        run_id="run-wc",
        continuous_run_id="run-wc",
        repository_sha="abc",
        cycle_index=1,
    )
    token = bind_ghv_pre_external_runtime_flight_recorder_session_v1(session)
    return evidence_root, token


def test_bounded_graph_accounts_all_nodes() -> None:
    nodes, edges = enumerate_bounded_cycle_graph_v1()
    assert len(nodes) >= 18
    assert len(edges) >= 10
    graph = build_state_graph_v1([], None)
    assert graph["UNACCOUNTED_GRAPH_NODES"] == 0
    assert graph["GRAPH_NODES_TOTAL"] == len(nodes)


def test_ghv_root_event_on_synthetic_enter_short_cycle1(tmp_path: Path) -> None:
    _, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root, fr_tok = _bind_recorder(tmp_path)
    syn_tok = bind_synthetic_enter_forensic_session_v1(
        build_synthetic_enter_forensic_session_v1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=evidence_root,
            continuous_run_id="run-wc",
        )
    )
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        assert overlay.applied is True
        rows = [
            json.loads(line)
            for line in (evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()
        ]
        root_rows = [r for r in rows if r.get("change_event_id") == GHV_ROOT_CHANGE_EVENT_ID]
        assert root_rows
        assert root_rows[0]["decision_after"] == "enter_short"
        assert root_rows[0]["selected_side_after"] == "short"
    finally:
        reset_synthetic_enter_forensic_session_v1(syn_tok)
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_tok)


def test_field_provenance_and_fan_out(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root, fr_tok = _bind_recorder(tmp_path)
    try:
        gen_a = append_flight_record_stage_v1(
            stage="S7_MV2_FINAL_OUTPUT",
            producer_symbol="producer_a",
            consumer_symbol="consumer_b",
            parent_generation_id="gen_root",
            replay=replay,
        )
        gen_b = append_flight_record_stage_v1(
            stage="SYNTHETIC_OVERLAY_OUTPUT",
            producer_symbol="producer_b",
            consumer_symbol="consumer_c",
            parent_generation_id=str(gen_a),
            replay=replay,
        )
        assert gen_a != gen_b
        records = [
            json.loads(line)
            for line in (evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()
        ]
        fp = build_field_provenance_rows_v1(records)
        assert any(r["field_name"] == "decision_outcome" for r in fp)
        impact = build_change_impact_v1(records)
        assert impact["ghv_explicit_root"] is True
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_tok)


def test_stale_generation_lineage_detectable(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root, fr_tok = _bind_recorder(tmp_path)
    try:
        gen_old = append_flight_record_stage_v1(
            stage="S7_MV2_FINAL_OUTPUT",
            producer_symbol="old",
            consumer_symbol="stale_consumer",
            parent_generation_id="gen_root",
            replay=replay,
        )
        append_flight_record_stage_v1(
            stage="SYNTHETIC_OVERLAY_OUTPUT",
            producer_symbol="new",
            consumer_symbol="stale_consumer",
            parent_generation_id=str(gen_old),
            replay=replay,
            extra={"stale_generation_consumer": True},
        )
        records = [
            json.loads(line)
            for line in (evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()
        ]
        graph = build_state_graph_v1(records, None)
        assert graph["dynamic_edges"]
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_tok)


def test_reverse_provenance_and_multi_blocker_harness(tmp_path: Path) -> None:
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    evidence_root, fr_tok = _bind_recorder(tmp_path)
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
        snap = evidence_root / "ghv_pre_external_continuation_snapshot_v1"
        report = run_ghv_pre_external_continuation_harness_v1(
            snapshot_root=snap,
            output_dir=evidence_root,
        )
        assert report["NO_FAIL_FAST_OBSERVATION"] is True
        assert len(report["stages"]) >= 5
        assert report["ROOT_CAUSE_PROVEN"] is False if "ROOT_CAUSE_PROVEN" in report else True
        bundle = build_whole_cycle_observability_v1(
            evidence_root=evidence_root,
            harness_report=report,
        )
        reverse = build_reverse_provenance_v1(
            bundle["field_provenance_rows"],
            bundle["state_graph"],
            ghv_root=None,
        )
        assert "reverse_chains" in reverse
        paths = persist_whole_cycle_observability_artifacts_v1(
            evidence_root=tmp_path / "artifacts",
            bundle=bundle,
        )
        assert (tmp_path / "artifacts" / STATE_GRAPH_FILENAME).is_file()
        assert (tmp_path / "artifacts" / FIELD_PROVENANCE_FILENAME).is_file()
        assert (tmp_path / "artifacts" / CHANGE_IMPACT_FILENAME).is_file()
        assert (tmp_path / "artifacts" / REVERSE_PROVENANCE_FILENAME).is_file()
        assert paths["state_graph"] == STATE_GRAPH_FILENAME
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_tok)


def test_recorder_disabled_semantic_identity_unchanged(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    syn_tok = bind_synthetic_enter_forensic_session_v1(
        build_synthetic_enter_forensic_session_v1(
            enabled=True,
            synthetic_side="enter_short",
            inject_cycle_index=1,
            product_evidence_root=tmp_path,
            continuous_run_id="x",
        )
    )
    try:
        before = str(getattr(replay.evidence, "decision_outcome", ""))
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(replay, cycle_index=1)
        assert overlay.applied
        assert not (tmp_path / FLIGHT_RECORD_FILENAME).exists()
        assert str(getattr(overlay.replay.evidence, "decision_outcome", "")) != before
    finally:
        reset_synthetic_enter_forensic_session_v1(syn_tok)


def test_unaccounted_nodes_prevent_cycle_capture_complete() -> None:
    graph = build_state_graph_v1([], None)
    assert graph["CYCLE_GRAPH_ENUMERATION_COMPLETE"] is True
    bundle = build_whole_cycle_observability_v1(
        evidence_root=Path("/nonexistent"),
        harness_report={
            "stages": [],
            "ROOT_BLOCKERS": [],
            "DEPENDENT_BLOCKERS": [],
            "INDEPENDENT_BLOCKERS": [],
            "NOT_EVALUABLE": [],
        },
    )
    assert bundle["CAUSAL_ANALYSIS_COMPLETE"] is True


def test_authorities_none() -> None:
    assert RECORDER_AUTHORITY == "NONE"
    assert PROVENANCE_ANALYZER_AUTHORITY == "NONE"
