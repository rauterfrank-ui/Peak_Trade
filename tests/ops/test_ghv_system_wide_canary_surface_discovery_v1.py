"""System-wide GHV Canary surface discovery contracts (not Product Runtime proof)."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
    run_ghv_pre_external_continuation_harness_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
    FLIGHT_RECORD_FILENAME,
    GhvPreExternalRuntimeFlightRecorderSessionV1,
    append_flight_record_stage_v1,
    bind_ghv_pre_external_runtime_flight_recorder_session_v1,
    persist_continuation_snapshot_v1,
    reset_ghv_pre_external_runtime_flight_recorder_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1 import (
    CANARY_AUTHORITY,
    CANARY_CHANGES_DECISIONS,
    CANARY_CHANGES_RUNTIME_SEMANTICS,
    CANARY_CHANGES_RUNTIME_STATE,
    GHV_CANARY_ROOT,
    RECONCILIATION_FILENAME,
    GhvSystemWideCanarySessionV1,
    bind_ghv_system_wide_canary_session_v1,
    build_system_wide_canary_bundle_v1,
    discover_surfaces_from_flight_records_v1,
    persist_system_wide_canary_artifacts_v1,
    reconcile_modeled_vs_observed_v1,
    register_observed_surface_v1,
    reset_ghv_system_wide_canary_session_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from tests.ops.test_ghv_observe_shaped_venue_plan_object_identity_v1 import (
    _genuine_observe_shaped_s7_replay_v1,
)


def test_canary_authorities_none() -> None:
    assert CANARY_AUTHORITY == "NONE"
    assert CANARY_CHANGES_DECISIONS is False
    assert CANARY_CHANGES_RUNTIME_STATE is False
    assert CANARY_CHANGES_RUNTIME_SEMANTICS is False
    assert GHV_CANARY_ROOT == "GHV_SYNTHETIC_ENTER_SHORT_CYCLE_1"


def test_observed_surface_outside_modeled_graph() -> None:
    surf = register_observed_surface_v1(
        producer_symbol="unmodeled_runtime_adapter_xyz_v1",
        consumer_symbol="downstream_consumer",
        causal_relation="CONSUMES_TRACED_STATE",
        execution_domain="PRODUCT_RUNTIME",
        discovery_reason="test-only unmodeled surface",
    )
    reconciliation = reconcile_modeled_vs_observed_v1([surf], [])
    assert reconciliation["OBSERVED_BUT_NOT_MODELED_COUNT"] >= 1
    assert reconciliation["MODELED_TOTAL"] >= 18
    assert reconciliation["GLOBAL_RUNTIME_UNIVERSE_PROVEN_COMPLETE"] == "UNKNOWN_CURRENT"


def test_modeled_surface_not_observed_when_empty_records() -> None:
    reconciliation = reconcile_modeled_vs_observed_v1([], [])
    assert reconciliation["MODELED_BUT_NOT_OBSERVED_COUNT"] == reconciliation["MODELED_TOTAL"]


def test_flight_record_discovery_independent_of_modeled_edges(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root = tmp_path / "ev"
    evidence_root.mkdir()
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(
        GhvPreExternalRuntimeFlightRecorderSessionV1(
            enabled=True,
            product_evidence_root=evidence_root,
            run_id="r1",
            continuous_run_id="r1",
            cycle_index=1,
        )
    )
    canary_reset = bind_ghv_system_wide_canary_session_v1(
        GhvSystemWideCanarySessionV1(
            enabled=True,
            ghv_canary_trace_id=GhvSystemWideCanarySessionV1.new_trace_id(
                run_id="r1", cycle_index=1
            ),
            cycle_index=1,
        )
    )
    try:
        append_flight_record_stage_v1(
            stage="CUSTOM_UNMAPPED_STAGE",
            producer_symbol="custom_producer_not_in_modeled_graph_v1",
            consumer_symbol="custom_consumer_v1",
            parent_generation_id="gen_root",
            replay=replay,
        )
        rows = [
            json.loads(line)
            for line in (evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()
        ]
        assert rows[0].get("ghv_canary_trace_id", "").startswith("GHV_CANARY_TRACE_")
        surfaces, _events = discover_surfaces_from_flight_records_v1(rows)
        assert any("custom_producer" in s.get("symbol", "") for s in surfaces)
        bundle = build_system_wide_canary_bundle_v1(evidence_root=evidence_root)
        assert bundle["reconciliation"]["OBSERVED_BUT_NOT_MODELED_COUNT"] >= 1
    finally:
        reset_ghv_system_wide_canary_session_v1(canary_reset)
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_branch_and_harness_continuation_separation(tmp_path: Path) -> None:
    pairs, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    evidence_root = tmp_path / "ev2"
    evidence_root.mkdir()
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(
        GhvPreExternalRuntimeFlightRecorderSessionV1(
            enabled=True,
            product_evidence_root=evidence_root,
            run_id="r2",
            continuous_run_id="r2",
        )
    )
    try:
        parent = append_flight_record_stage_v1(
            stage="LIVE_29P_JOIN_OUTPUT",
            producer_symbol="join_current_productive_enter_live_29p_before_venue_plan_v1",
            consumer_symbol="venue_plan",
            parent_generation_id="gen_root",
            replay=replay,
        )
        persist_continuation_snapshot_v1(
            parent_generation_id=str(parent),
            post_live_29p_replay=replay,
            bound_instrument=bound,
            composed_epoch=EPOCH,
            session_id="s",
            run_id_suffix="r:s",
            synthetic_overlay_applied=False,
            live_29p_status="PASS",
            live_29p_first_blocker="",
        )
        snap = evidence_root / "ghv_pre_external_continuation_snapshot_v1"
        report = run_ghv_pre_external_continuation_harness_v1(
            snapshot_root=snap,
            output_dir=evidence_root,
        )
        assert report.get("system_wide_canary_reconciliation") is not None
        assert (evidence_root / RECONCILIATION_FILENAME).is_file()
        rec = json.loads((evidence_root / RECONCILIATION_FILENAME).read_text())
        assert rec["PRODUCT_OBSERVED_TOTAL"] >= 1
        assert rec["CONTINUATION_OBSERVED_TOTAL"] >= 1
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_canary_disabled_no_correlation_on_rows(tmp_path: Path) -> None:
    _, replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    evidence_root = tmp_path / "ev3"
    evidence_root.mkdir()
    fr_reset = bind_ghv_pre_external_runtime_flight_recorder_session_v1(
        GhvPreExternalRuntimeFlightRecorderSessionV1(
            enabled=True,
            product_evidence_root=evidence_root,
            run_id="r3",
            continuous_run_id="r3",
        )
    )
    try:
        append_flight_record_stage_v1(
            stage="S7_MV2_FINAL_OUTPUT",
            producer_symbol="p",
            consumer_symbol="c",
            parent_generation_id="gen_root",
            replay=replay,
        )
        row = json.loads((evidence_root / FLIGHT_RECORD_FILENAME).read_text().splitlines()[0])
        assert "ghv_canary_trace_id" not in row
    finally:
        reset_ghv_pre_external_runtime_flight_recorder_session_v1(fr_reset)


def test_persist_artifacts_no_secrets(tmp_path: Path) -> None:
    bundle = build_system_wide_canary_bundle_v1(evidence_root=tmp_path / "empty")
    paths = persist_system_wide_canary_artifacts_v1(
        evidence_root=tmp_path / "out",
        bundle=bundle,
    )
    assert paths["reconciliation"]
    text = (tmp_path / "out" / RECONCILIATION_FILENAME).read_text()
    assert "api_key" not in text.lower()
